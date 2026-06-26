# OAuth2、OIDC 與 OAuth 2.1：grant 類型與現況

你想在自己的 App 裡加一個「列出使用者最近的相簿照片」的功能，而照片存在某個你不擁有的服務上。最直白的做法呼之欲出：請使用者把那個服務的帳號密碼填進你的表單，你拿著去登入、抓照片。這個念頭出現的那一秒，整個 OAuth 的故事就有了動機——因為它是**錯的**，而且錯得很徹底。

使用者把密碼交給你，等於把那個帳號的**全部**權力交給你：不只讀照片，還能改密碼、刪相簿、讀私訊、轉走錢。你只想要一個很窄的能力（讀照片），卻被迫索取了整把鑰匙。更糟的是，你現在得**保管**這把明文密碼——你的資料庫一旦外洩，賠上的是使用者在別處的帳號。而使用者想收回授權，唯一的辦法是改密碼，連帶把所有其他正當拿著這組密碼的 App 一起踢掉。這裡每一個問題都不是實作疏失，而是「拿密碼當授權憑證」這個模型的**結構性缺陷**：密碼是一個全有全無、無法限縮、無法選擇性撤銷、必須長期保管的東西，而授權需要的恰恰相反——範圍可框、時效可控、可單獨撤回、不必任何人代為保管祕密。

OAuth 2.0 就是為了把「授權」這件事從「密碼」裡拆出來而生的。它要回答一個很具體的問題：**怎麼讓一個第三方 App 代表使用者去存取某個資源，卻從頭到尾不讓它碰到使用者的密碼。** 把這個問題講透，再看它衍生出的身分層（OIDC）與十年後的整併（OAuth 2.1），這一章就完整了。

## 四個角色，與那張代客泊車的票

OAuth 的整個劇本，是四個角色之間的一段協商。把名字記清楚，後面才不會亂：

- **resource owner**：使用者本人，那些照片的擁有者。
- **client**：想存取照片的第三方 App。
- **authorization server**：發 token、也是使用者真正輸入密碼的地方（通常就是照片服務的帳號系統）。
- **resource server**：實際持有照片、收到請求時要驗 token 的 API。

關鍵的洞見藏在一個生活化的比喻裡：**代客泊車的票（valet key）**。有些車的鑰匙分兩種——車主的全功能鑰匙，和一把交給泊車員的限制版，後者只能發動引擎、開車門，開不了後車廂、跑不了超過幾公里。OAuth 發給 client 的 **access token**，就是這把 valet key：它代表「持有者被授權做某些事」，但能做的事被框在一個很窄的範圍裡，而且會過期、能被單獨作廢。client 拿著它去敲 resource server 的門，resource server 驗票放行——全程沒有人需要把車主的全功能鑰匙（密碼）交出去。

於是前面那一串結構性缺陷被逐一拆解：token 只帶**它需要的那點權限**（scope），不是整把鑰匙；token 有 **expiry**，洩漏了也只在短窗口內有效；撤銷一個 token **不影響**其他 token，使用者可以單獨踢掉某個 App；client 保管的是一個隨時可換、權限受限的 token，而非那個能毀掉使用者一切的密碼。OAuth 沒有發明什麼新的密碼學，它只是把「授權」重新塑造成一個**可限縮、可過期、可單獨撤銷、不含長期祕密**的憑證——這正是密碼做不到的四件事。

## authorization code flow：為什麼要繞這麼一大圈

知道了要發 valet key，下一個問題是怎麼把它安全地交到 client 手上。這裡是 OAuth 最容易被嫌「為什麼這麼麻煩」、卻每一步都有血淚的地方。

主流的做法叫 **authorization code grant**。先看它的步驟，再逐一解釋每一步在防什麼：

```
1. client 把使用者的瀏覽器導向 authorization server，
   帶上 client_id、要求的 scope、redirect_uri、state
2. 使用者在 authorization server 上登入、看到「某 App 想存取你的照片」、點同意
3. authorization server 把瀏覽器導回 client 的 redirect_uri，
   url 上帶一個一次性的 authorization code
4. client 的「後端」拿這個 code，連同自己的憑證，
   直接（server-to-server）打 authorization server 的 token endpoint
5. authorization server 驗過後，回傳 access token（與可選的 refresh token）
6. client 拿 access token 去 resource server 存取照片
```

最反直覺的是第 3、4 步那個「分兩段」：為什麼不在第 3 步就直接把 access token 回傳，非要先給一個 `code`、再換一次？答案是**信任邊界的切割**。第 3 步走的是瀏覽器重定向——token 如果這時出現在 URL 上，它會留在瀏覽器歷史、可能被 `Referer` 標頭帶到下一個網站、被中間的代理記進 log。而 access token 是長效力的真鑰匙，不該在這種容易外洩的通道上裸奔。`code` 則是**一次性、短命（典型幾十秒到幾分鐘）、且本身不能拿去存取任何資源**的東西——它只是一張「待兌換券」。真正的兌換（第 4 步）走的是 client 後端對 authorization server 的**直接 TLS 連線**，access token 從頭到尾不經過瀏覽器這個髒通道。把「在不安全通道上傳遞的東西」和「真正有力量的東西」分成兩個，是這個 flow 的設計骨架。

第 1 步那個 **`state`** 參數也不是裝飾。它是一個 client 自己產生的隨機值，原封不動在第 3 步被帶回來；client 比對「回來的 state 跟我送出去的是不是同一個」，藉此確認「這個 callback 是回應我剛剛發起的那次授權」，而不是攻擊者偽造的一個 callback 把使用者誘騙到一段別人發起的授權上——這就是擋 CSRF 的那道閂。省掉 `state`，攻擊者就能讓使用者的帳號被綁到攻擊者控制的授權結果上。

## code 被攔截怎麼辦：PKCE 的那道數學閂

分兩段把 access token 護住了，但 `code` 自己在第 3 步還是走了瀏覽器重定向這條髒通道。在某些環境裡，這個 `code` 會被偷——而一旦被偷，攻擊者就能搶在合法 client 之前去第 4 步把它換成 access token。這不是假想。

最經典的攻擊場景在行動裝置上。原生 App 接收 redirect 常靠註冊一個 custom URI scheme（像 `myapp://callback`）。問題是作業系統允許**多個 App 註冊同一個 scheme**——一個惡意 App 偷偷也宣稱自己處理 `myapp://`，當授權結果帶著 `code` 回傳時，OS 可能把它交給了那個惡意 App。code 落到攻擊者手上，flow 就被劫持了。公開 client（行動 App、SPA）還有個雪上加霜的前提：它們**藏不住祕密**——程式碼可被反編譯、JavaScript 攤在瀏覽器裡，所以不能靠「client 後端有一把只有它知道的 secret」來在第 4 步證明自己的身分。光偷到 code 就夠了。

**PKCE（Proof Key for Code Exchange，RFC 7636，唸作「pixy」）** 就是補這個洞的。它的巧思是讓 client **臨時生成一對證據**，把「發起授權的人」和「來兌換 code 的人」用密碼學綁成同一個：

```
1. client 隨機產一個高熵字串 code_verifier（43–128 字元，
   字元集為 RFC 3986 的 unreserved：A-Z a-z 0-9 - . _ ~）
2. client 算出 code_challenge = BASE64URL( SHA256( ASCII(code_verifier) ) )
3. 發起授權時，只送 code_challenge（與 method=S256）上去，verifier 留在本地
4. authorization server 把這個 challenge 跟發出的 code 綁在一起記著
5. 第 4 步兌換 code 時，client 補送原始的 code_verifier
6. authorization server 重算 SHA256→base64url，比對是否等於先前存的 challenge；
   不符就拒發 token
```

關鍵在第 6 步那個不可逆。SHA-256 是單向的——攻擊者就算在重定向時攔到了 `code`，甚至也看到了當初送上去的 `code_challenge`，他**算不回** `code_verifier`（那需要逆轉雜湊）。而兌換 code 必須附上正確的 `code_verifier`，這個 verifier 只活在合法 client 的記憶體裡、從沒走過瀏覽器那條髒通道。於是「偷到 code」不再等於「能換到 token」——少了那把只有原 client 握有的 verifier，authorization server 在第 6 步就把攻擊者擋下了。

用 RFC 7636 附錄 B 的真實例子手算一遍，把抽象的東西落地。verifier 取 `dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk`（43 字元），對它的 ASCII 位元組做 SHA-256，得到一串 32 位元組的雜湊，再做 base64url 編碼（去掉 padding 的 `=`），結果是 `E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM`。送出去的就是後者這個 challenge，留在身邊的是前者這個 verifier；server 收到 verifier 時把它再跑一次 `SHA256→base64url`，得到的若不是分毫不差的 `E9Mel...w-cM`，就一律拒絕。`method` 還有一個 `plain`（challenge 直接等於 verifier、不做雜湊），但那等於沒有保護——能攔到 challenge 就等於拿到 verifier，所以除非 client 真的連 SHA-256 都跑不動，否則一律用 `S256`。

PKCE 最初是為「藏不住 secret 的公開 client」設計的補丁。但它的價值後來被認為對機密 client 也成立——多一道與 code 綁定的證明，沒有壞處——這個認知，正是後面 OAuth 2.1 把它升格成「對所有 client 強制」的伏筆。

## OAuth 不告訴你「使用者是誰」：OIDC 補上的那一塊

到這裡，client 已經能安全地拿到一個 access token、代表使用者去存取照片了。但有件事 OAuth **從頭到尾沒做**，而且很多人沒意識到它沒做：**OAuth 不告訴你使用者是誰。**

這不是疏漏，是定義。access token 是一張「持有者可以對某資源做某些事」的票，它證明的是**授權**——可以做什麼。它**不**證明「來兌換這張票的人是誰」。把這件事想清楚會冒冷汗：如果你把「拿到了某使用者的 access token」當成「該使用者在我這裡登入成功了」，你就踩進一個經典的混淆攻擊面。一個惡意 App 完全可以拿著它從**別處**騙來、或自己正當取得的 access token，丟給你的「用 OAuth 登入」端點；你拿這個 token 去問資源服務「這個 token 屬於誰」，得到一個使用者身分，就**以那個人的身分**把人放進來了——但那個 token 根本不是為你的 App 簽發的，持有它的也不是本人。access token 對「受眾是誰」沒有約束力，你卻拿它當了登入憑證。

**OIDC（OpenID Connect Core 1.0）** 就是疊在 OAuth 2.0 之上、專門補上「認證」這一層的。它的做法乾淨利落：在授權請求裡多加一個 `openid` scope，authorization server（這個角色在 OIDC 語境下改稱 **OpenID Provider, OP**）除了照舊發 access token，**另外**發一個東西——**ID Token**。

ID Token 是一個簽章過的 JWT（結構與簽章機制見〈JWT 與簽章〉），它和 access token 的職責是兩回事，這個分工是 OIDC 的核心：

- **access token** 是給 **resource server** 看的，回答「持有者能做什麼」。它對 client 通常是**不透明**的——client 不該去拆它、解讀它，只該原封不動帶去資源端。
- **ID Token** 是給 **client** 看的，回答「使用者是誰、何時、用什麼方式完成了認證」。它就是 client 的認證結果。

一句話釘死兩者的分工：**OAuth 給你 access token（去做事的授權憑證）、OIDC 給你 ID Token（你是誰的認證結果）。** 把 access token 拿去推身分是誤用，把 ID Token 拿去存取資源也是誤用——它們是兩張面額、用途都不同的票。

## 驗一個 ID Token，到底在驗什麼

拿到 ID Token，client 不能只看一眼簽章對不對就放人。簽章只證明「這個 JWT 沒被竄改、確實由 OP 簽的」，但「沒被竄改」不等於「這是發給**我**、回應**我這次**請求的」。一個成熟的 ID Token 驗證，至少要逐一核對幾個 claim，每一個都在堵一種具體的攻擊：

- **`iss`（issuer）**：簽發者必須是你信任的那個 OP。漏驗，等於接受任何人簽的 token。
- **`aud`（audience）**：受眾必須包含**你自己的** `client_id`。這是堵前面那個混淆攻擊的關鍵——一個簽給「別的 App」的合法 ID Token，`aud` 不是你，就該被你拒絕。OAuth 的 access token 之所以不能拿來登入，正是因為它的受眾不是 client——它就算帶 `aud`，綁的也是 resource server，client 既不是它的預期接收者、也不負責驗它；而 ID Token 把 `aud` 硬綁成你的 `client_id`，你才驗得出「這張身分票是專門簽給我的」。
- **`exp`（expiry）**：過期的不收。
- **`nonce`**：如果你在發起授權時送了一個隨機 `nonce`，ID Token 裡必須回帶同一個值。它對認證流程的作用，類比 `state` 對授權流程，但綁的層次不同：`state` 活在授權通道、綁的是 callback 與發起者（擋 CSRF），`nonce` 被簽進 ID Token 本身、綁的是這張身分票到「我剛剛發起的那一次登入」——擋的是把一張別處取得的、本身合法的 ID Token 重放進來假冒登入。
- **簽章**：用 OP 公布的公鑰驗（規格要求 OP **必須**支援 `RS256`，見 OIDC Core §15.1；公鑰怎麼透過 JWKS 端點動態取得、怎麼隨 `kid` 輪替，見〈JWT 與簽章〉）。

這裡有一個容易被略過、卻很能說明 OIDC 設計細膩之處的 claim：**`at_hash`**。當 OP 在發 ID Token 的同時也發了 access token，它可以在 ID Token 裡放一個 `at_hash`——那是 access token 值經雜湊、取左半、再 base64url 編碼的結果。client 收到後，把自己拿到的 access token 同樣雜湊一遍、比對 `at_hash`，就能確認「我手上這個（不透明、無法自己驗的）access token，和這張（我驗得過簽章的）ID Token 是**同一次簽發、配成一對的**」。這道檢查擋的是一種偷天換日：攻擊者把 flow 裡的 access token 抽換成另一個。沒有 `at_hash`，client 沒辦法察覺；有了它，access token 雖然自己不可驗，卻被一個可驗的 ID Token「背書」綁定了。同理還有對 authorization code 做的 `c_hash`。這些 hash claim 只需要擋竄改、不需擋暴力反推，所以規格說 128 位元抗碰撞就夠——它們是完整性檢查，不是機密保護。

## 不需要使用者在場的時候：client credentials

到目前為止的故事都圍著「代表某個**使用者**去存取資源」打轉。但有一大類場景根本沒有使用者：一個後端排程半夜去呼叫另一個內部 API、一個服務去拉另一個服務的資料。這裡沒有人會坐在瀏覽器前點「同意」，也沒有什麼 redirect 可言。

OAuth 為此留了一條完全不同的路：**client credentials grant**。client 用**自己的**憑證（一組 client id + secret，或更穩的私鑰）直接打 token endpoint，換來一個代表「**它自己**」的 access token——不是代表任何使用者。整個瀏覽器重定向、使用者同意、PKCE 那一大套全部省掉，因為它們存在的理由（保護「使用者把權限委派給 App」這個動作）在這裡不存在。這條路提醒我們：OAuth 的 grant 類型不是一堆可隨意挑選的同義做法，而是**對應不同的信任前提**——有沒有使用者在場、client 藏不藏得住 secret、憑證在哪個通道上傳遞——每一種 grant 都是某一組前提下的最佳解。看懂這點，就不會問「我到底該用哪個 grant」這種問題，而是先問「我的信任前提是什麼」，grant 自己就浮出來了。

## OAuth 2.1：把十年的傷疤寫進規格

OAuth 2.0 的原始規格 RFC 6749 是 2012 年的東西。它定義了好幾種 grant，其中有些在當年看似合理、後來被真實世界的攻擊一一證明是壞主意。這十多年的教訓散落在一堆後續的安全 BCP（best current practice）文件裡——直到 **RFC 9700（OAuth 2.0 Security Best Current Practice，2025 年 1 月發布）** 把這些要求正式收編成一份權威文件。**OAuth 2.1**（`draft-ietf-oauth-v2-1`）則是把 RFC 6749 加上這些累積的安全共識，**整併成一份更精簡、預設就更安全**的文件的努力。它做的四件最該記住的事：

1. **PKCE 對所有用 authorization code flow 的 client 強制必要**——不再只限公開 client。前面說過，多一道與 code 綁定的證明對機密 client 也只有好處，於是乾脆全面要求。
2. **移除 implicit grant**。這是 OAuth 2.0 裡讓 access token 直接從瀏覽器的 URL fragment 回傳的捷徑——它把長效力的真鑰匙丟在最容易外洩的地方（瀏覽器歷史、log、`Referer`），在 token 洩漏與重放面前不堪一擊。SPA 一律改走 authorization code + PKCE。
3. **移除 ROPC（Resource Owner Password Credentials）grant**。這個 grant 讓 client 直接收下使用者的帳號密碼再去換 token——它**徹底違背 OAuth 一開始的初衷**（不讓 client 碰密碼）。它的存在本身就是個諷刺，2.1 把它拿掉。
4. **redirect URI 必須 exact string matching**。不再允許前綴比對或萬用字元——那種寬鬆比對是「開放重定向 + code 竊取」的經典破口（攻擊者構造一個落在「允許前綴」內、卻指向自己的 URI，把 code 騙走）。要求逐字元完全相符，就堵死了這個構造空間。

除了這四項，2.1 還把一些 BCP 寫進核心，例如 bearer token 不准出現在 URL query string、公開 client 的 refresh token 必須做輪替（rotation）或 sender-constraining 等。

這裡有一個**最容易說錯、值得當心的措辭問題**：OAuth 2.1 在 2026-06 **仍然是 IETF 的 Internet-Draft，還沒成為 RFC**。最新一版是 **draft-15（2026-03-02 發布，Standards Track，預定 2026-09-03 到期）**。坊間「OAuth 2.1 來了」之類的標題很容易讓人以為它已是定稿標準——但以 IETF datatracker 為準，它仍在 draft 階段。這個區別在實務上其實不太影響你該怎麼做：上面那四項安全做法，無論 2.1 是不是 RFC，**你今天就該全部照做**（它們本來就是 RFC 9700 已經背書的 BCP，PKCE、移除 implicit/ROPC、exact redirect matching 都不是要等誰拍板的選配）。但在文件、簡報、跟同事溝通時，把它說成「OAuth 2.1 **標準**」或「**RFC**」就是不準確——它是「凝聚了當前安全共識的進行中草案」，而那些安全共識本身已經是現行最佳實踐。

## 為什麼是這個形狀

退一步看，OAuth/OIDC 這一整套看似繁複的機器，每一個零件都能回溯到開頭那個最樸素的錯誤——把密碼當授權憑證。

正因為不該把整把鑰匙交出去，才有了範圍受限、會過期、可單獨撤銷的 **access token**（valet key）。正因為 access token 這把真鑰匙不該走瀏覽器那條髒通道，才有了「先發一次性 `code`、再到後端換 token」的**兩段式 flow**。正因為連 `code` 走重定向都可能被攔、而公開 client 又藏不住 secret，才有了用單向雜湊把「發起者」和「兌換者」綁成同一人的 **PKCE**。正因為 OAuth 只管授權、不管「你是誰」，才有了疊在它上面、用一張綁定受眾的 ID Token 回答身分的 **OIDC**。正因為十多年來每一種偷懶的捷徑都被攻擊驗證過代價，才有了把 implicit、ROPC、寬鬆 redirect 一律掃掉的 **OAuth 2.1**。

它不是一套憑空複雜的協定，而是「讓第三方代表使用者去做事、卻不交出密碼」這個需求，在一次次真實攻擊的打磨下，被逼出來的形狀。當你下次看到登入頁面跳轉到某個你信任的服務、同意之後又跳回來、而你的密碼從沒離開過那個服務——你看到的，就是這整條推理鏈在替你工作。

## 延伸閱讀

- The OAuth 2.0 Authorization Framework — RFC 6749: https://www.rfc-editor.org/rfc/rfc6749
- The OAuth 2.1 Authorization Framework — draft-ietf-oauth-v2-1（IETF datatracker，2026-06 仍為 draft-15）: https://datatracker.ietf.org/doc/draft-ietf-oauth-v2-1/
- Proof Key for Code Exchange by OAuth Public Clients — RFC 7636: https://www.rfc-editor.org/rfc/rfc7636
- Best Current Practice for OAuth 2.0 Security — RFC 9700: https://www.rfc-editor.org/rfc/rfc9700
- OpenID Connect Core 1.0: https://openid.net/specs/openid-connect-core-1_0.html
- OAuth 2.0 Token Introspection — RFC 7662: https://www.rfc-editor.org/rfc/rfc7662
- OAuth 2.1 official overview（oauth.net）: https://oauth.net/2.1/
