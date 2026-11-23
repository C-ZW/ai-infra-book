# 第 35 章：完整實戰演練：NexusPay 端到端紅藍對抗復盤

前面三十四章，我們把漏洞拆在四個獨立的技術層面：邊緣代理與 HTTP 協定分歧、應用層授權與併發狀態機、雲端控制平面與 AI Agent 隔離，以及原生 FFI 二進位模組與核心邊界。到了第 34 章，我們也把這些單點防禦收束成企業級的 AppSec Paved Road。

但真實世界的資安事件，從來不會乖乖停在單一章節的邊界裡。攻擊者只要在第一層找到一個看似低危的路由解析分歧或 SSRF，就能串起第二層的授權盲點、摸走第三層的雲端短期憑證，最後在第四層的原生解析器引爆整台機器崩潰。

本章不再引入新的攻擊手法，而是直接拿貫穿全書的 **NexusPay** 四層架構當作唯一靶標。我們會從黑箱偵察與跨層威脅建模出發，完整復盤一場六階段的端到端紅藍對抗演練，並把紅隊打穿的破口，轉化為藍隊「`24 小時` 緊急止血、`7 天` 根因修復、長期架構防線」的工程落地與 CI 自動化安全回歸測試。

> **授權與演練邊界**：本章所有攻擊路徑分析與概念驗證（PoC）皆限定於本地建置的 NexusPay 隔離靶機，聚焦於狀態機不變量驗證、架構威脅建模與防禦回歸測試，不提供武器化入侵腳本。

---

## 從你已知的出發

為什麼很多團隊每季做完滲透測試、修完報告上列出的十幾個中低危漏洞，隔月線上帳本還是被雙花掏空，甚至連 Kubernetes 叢集的雲端密鑰都被整碗端走？

因為多數紅藍演練都犯了「單點視角」的毛病。紅隊挖到一個路徑解析差異或 `libnexus-parse` 崩潰點就急著交差，沒往下追它能不能串接雲端憑證或打穿帳本不變量，結果嚴重度被低估；藍隊看到 FFI 崩潰就只補長度檢查、看到併發雙花就只把 Nginx 限流調緊，卻放任上游代理分歧與資料庫交易隔離這兩個真正的病根繼續躺在線上。

端到端紅藍對抗的價值，就是強迫雙方攤開同一張「跨層信任邊界與不變量地圖」：紅隊負責證明小破口如何串成致命攻擊鏈，藍隊則負責用最低的工程代價切斷關鍵跳板，並把驗證邏輯直接鎖進 CI 回歸測試。

---

## 機制與推導

### 攻擊者目標與實質影響

在 NexusPay 這種多租戶即時結算平台上，攻擊者花力氣串聯跨層漏洞，不是為了看伺服器噴一段 Stack Trace，而是為了打破系統最核心的三條業務與架構不變量：

第一是**財務帳本守恆**（Ledger Conservation）。每個測試帳戶的初始餘額固定是 `10,000` 分（`$100.00`），單次提領上限也是 `10,000` 分。不管外面湧進多極端的併發請求，已結算的提領總額加上剩餘餘額，絕對不能超過初始入金，而且帳本餘額永遠不能變成負數或重複入帳。

第二是**多租戶與密鑰隔離**（Tenant & Secret Isolation）。租戶 A 的請求絕對不能讀寫租戶 B 的帳務資料；跑在 Kubernetes 裡的應用層 Pod，也絕對不能透過非預期的出站連線去摸到雲端 IAM 高權限憑證或 KMS 解密權限。

第三是**執行時期記憶體與可用性**（Runtime Safety & Availability）。負責解析外部二進位報表的 N-API 模組 `libnexus-parse`（合法 payload 上限為 `65,536 bytes`），遇到任何畸形封包都必須安全回傳錯誤碼。

它絕不能發生越界讀寫（OOB）或行程崩潰，否則會拖垮同一個行程裡的 Node.js Worker，在 `2,000 req/s` 的尖峰流量下引發連鎖雪崩。

單看一個弱點，可能只是局部的資訊洩漏或中低風險。但只要跨越四層邊界串成完整利用鏈，一旦打穿財務帳本或拿走雲端憑證，就會對業務造成實質重創。按照第 33 章的 CVSS v4.0 與 SLA 基準，這種跨層破口會直接定級為嚴重（Critical）等級，或是因為具備高可利用性與主動攻擊威脅，必須立刻排入 `24 小時` 緊急 SLA 處置。

---

### 全系統概念攻擊路徑與威脅建模（Web → Cloud → FFI）

動手打靶之前，紅藍雙方得先把 NexusPay 的架構圖攤開來對齊。下面這張圖整合了第 1 章的四層信任邊界，標出三條最具代表性的跨層突破路線（Chain A、Chain B、Chain C）：

```
+-------------------------------------------------------------------------+
| 外部網路 (Untrusted Internet / Attacker)                                |
+------------------------------------+------------------------------------+
                                     |
        [Chain A: H2 Single-Packet]  |  [Chain B: Parser Diff / SSRF]
        20 reqs / < 1 ms jitter      |  [Chain C: Malformed TLV > 64 KiB]
                                     v
+-------------------------------------------------------------------------+
| Layer 1: 邊緣與協定層 (Nginx proxy_read_timeout 30s / WAF)              |
+------------------+-----------------------------------+------------------+
                   |                                   |
                   v                                   v
+-----------------------------------+ +-----------------------------------+
| Layer 2: 應用與狀態機層           | | Layer 3: 雲端與編排層             |
| Node.js (keepAliveTimeout = 5s)   | | K8s Pod / ServiceAccount / RBAC   |
| - JWT RS256 (900s), JWKS (300s)   | | - Webhook Egress -> IMDS / IAM    |
| - GraphQL (深度 8, Batch 20)      | | - AI Agent Tool-Use / RAG 邊界    |
| - PostgreSQL 16 (餘額 10,000 分)  | +-----------------+-----------------+
| - Redis 7 (Session / 分散式鎖)    |                   |
+------------------+----------------+                   |
                   |                                    |
                   | [N-API FFI 呼叫: 8B Header + Payload]
                   v                                    |
+-----------------------------------+                   |
| Layer 4: 原生二進位與執行時期層   |                   |
| libnexus-parse (Rust / C FFI)     |                   |
| - 合法 payload 上限 65,536 bytes  |<------------------+
| - 越界長度檢查缺失 -> Crash / OOB |   (橫向取得內部密鑰或觸發 Worker 中斷)
+-----------------------------------+
```

我們順著資料流，看看這三條攻擊鏈是怎麼一關接一關穿過去的：

先看 **Chain A**（邊緣併發直穿帳本雙花）。攻擊者利用 HTTP/2 多工的單封包攻擊（Single-Packet Attack），把 `20` 筆提領請求的最後一個位元組塞進同一個 TCP 封包，在 `< 1 ms` 的時間差內同時砸進 Node.js API Gateway。

如果後端資料庫只用預設的 `READ COMMITTED` 隔離等級，又沒加 `SELECT ... FOR UPDATE` 列鎖或原子條件更新，這 `20` 筆請求就會在極短的讀取視窗裡同時讀到 `10,000` 分初始餘額，讓好幾筆請求一起過關，當場把帳本領爆。

再看 **Chain B**（代理分歧與 SSRF 橫向奪取雲端憑證）。當外層 Nginx 與後端 Node.js 對路徑正規化或 `Transfer-Encoding` 的切法不同（見第 3 章），或是商戶設定 Webhook 的功能忘了擋掉鏈路本地位址與內網網段（見第 11 章），攻擊者就能穿過大門去打內部管理介面或雲端中繼資料服務（IMDS）。

只要拿到綁在 Pod 身上的短期 IAM 憑證，攻擊者就能一路橫向摸進內部密鑰庫與其他微服務（見第 18 章）。

最後是 **Chain C**（API 輸入直擊原生 FFI 邊界崩潰）。商戶對帳系統會把上傳的二進位報表交給底層的 `libnexus-parse` 解析；它的 TLV 檔頭固定為 `8 bytes`（`magic: 2B`、`type: 2B`、`len: 4B` 無號整數），合法 payload 上限為 `65,536 bytes`（`64 KiB`）。

如果 N-API 橋接層或 C/Rust 入口沒嚴格核對 `len` 與實際緩衝區長度，或在算 `8 + len` 配置空間時沒做防溢位檢查，一顆特製的畸形封包就能直接引發記憶體越界或行程崩潰，讓整顆 Node.js Worker 在 `2,000 req/s` 的高壓流量下骨牌式重啟。

---

### 六階段端到端紅藍對抗時間軸（Worked Example）

光畫架構圖還不夠，真正的紅藍復盤必須看時間軸與告警訊號。假設我們在週三上午啟動一場六小時的無預警對抗演練，紅隊從公網黑箱開始推進，藍隊則盯著 SIEM 與 Prometheus 監控面板。

下面這份演練紀錄，完整對照了紅隊在六個階段的實質推進、碰到的 NexusPay 基準常數，以及藍隊在「修補前」與「修補後」截然不同的告警反應：

```text
=== NexusPay 六階段端到端紅藍對抗時間軸（基準演練紀錄） ===
標的基線：Gateway 尖峰 2,000 req/s | Nginx 30s / Node 5s | 測試戶餘額 10,000 分 ($100.00)
          JWT RS256 900s / JWKS 300s | GraphQL 深度 8 / Batch 20 | TLV 上限 65,536 bytes

[Stage 1] T+00:00 — 黑箱偵察與邊界測繪 (Reconnaissance)
  - 紅隊動作：比對 OpenAPI 公開文件與前端靜態 JS Bundle 路由，量測 Nginx (30s) 與 Node.js (5s)
              連線保持行為，確認支援 HTTP/2 多工且 GraphQL Batch 上限為 20。
  - 修補前告警：無告警（探測流量完全混入正常 2,000 req/s 背景流量）。
  - 修補後告警：[LOW] WAF 偵測非常規路由探測比例升高，觸發來源指紋標記。

[Stage 2] T+01:15 — 邊緣分歧與授權邊界突破 (Edge & Auth Bypass)
  - 紅隊動作：利用路徑正規化差異繞過外部代理對 /internal/reconcile 的前綴阻斷，
              並測試僅檢查 JWT 簽章 (RS256, 900s) 卻漏查租戶歸屬的對帳端點 (BOLA)。
  - 修補前告警：無告警（後端只記了一筆 HTTP 200，根本沒比對代理層與應用層看到的路徑差異）。
  - 修補後告警：[HIGH] 統一授權中介層攔截未宣告 @Policy 路由與跨租戶存取嘗試，回傳 403 並發送 SIEM 告警。

[Stage 3] T+02:30 — 單封包併發突破帳本不變量 (State-Machine Breach)
  - 紅隊動作：針對 POST /v1/withdrawals 發起 HTTP/2 單封包併發測試，將 20 個請求
              （每筆提領 5,000 分）的最後 1 位元組同步送達，伺服器端到達抖動 < 1 ms。
  - 實質結果（修補前）：4 筆併發同時通過讀取階段（當時讀到的餘額都是 10,000 分），
              總計領出 20,000 分 ($200.00)，當場打破 10,000 分帳本守恆不變量。
  - 修補前告警：無即時告警（直到隔天凌晨跑財務對帳報表，才發現帳上出現 -10,000 分赤字）。
  - 修補後告警：[CRITICAL] DB 條件更新受影響列數為 0 且冪等鍵衝突達閾值，多餘請求被安全拒絕；
              即時觸發帳本併發競爭異常告警。

[Stage 4] T+04:00 — 應用層 SSRF 至雲端短期憑證橫向 (Cloud Lateral Movement)
  - 紅隊動作：利用商戶 Webhook 網址驗證缺失，發起鏈路本地位址探測（IMDSv1 未關閉環境），
              讀取 Pod 綁定的短期 IAM 憑證，確認該憑證對內部密鑰庫擁有非預期的 List/Read 權限。
  - 修補前告警：無告警（出站請求被當成普通的商戶 Webhook 通知放行）。
  - 修補後告警：[CRITICAL] 安全 HTTP Client 在 DNS 解析階段攔截私有與鏈路本地 IP (169.254.169.254)，
              同時 K8s NetworkPolicy 記錄非預期 Egress 阻斷事件。

[Stage 5] T+05:20 — 原生 FFI 邊界畸形封包驗證 (Native FFI Fault)
  - 紅隊動作：向報表匯入端點傳送畸形 TLV 封包（8 bytes 檔頭中的 len 欄位設為 0x0001_0008 =
              65,544 bytes，超出 65,536 bytes 合法上限，且原生層缺乏邊界保護）。
  - 實質結果（修補前）：libnexus-parse 觸發未受控記憶體異常，導致 Node.js Worker 當場終止。
  - 修補前告警：只看到通用的 HTTP 502 Bad Gateway 與 Pod OOM/CrashLoopBackOff 紀錄，完全看不出是誰打的。
  - 修補後告警：[HIGH] N-API 入口閘門與 Rust 解析器直接回傳 Err(PayloadTooLarge)，Pod 零重啟，
              事件附帶完整 TLV 檔頭摘要寫入安全稽核日誌。

[Stage 6] T+06:00 — 藍隊止血與修補里程碑 (Remediation Milestones)
  - T+00h ~ T+24h（嚴重 SLA 24 小時）：緊急啟用提領 API 序列化鎖、封鎖 Webhook 內網出站、
    於 Node.js 入口強制截斷 > 65,536 bytes 的 TLV 負載，先把所有外部攻擊路堵死。
  - T+24h ~ T+7d （高危 SLA 7 天） ：完成 DB 原子條件扣款與冪等鍵重構、全面強制 IMDSv2、
    修補 libnexus-parse 邊界並把崩潰樣本加進 cargo-fuzz CI 回歸測試，全數測試案例轉綠通過。
```

仔細看這張時間軸，你會發現成熟紅藍演練最核心的衡量指標：**不是紅隊總共挖出幾個洞，而是每一個突破點在修補前後，藍隊能不能「即時看見」並「從結構上擋死」。**

在修補之前，紅隊從 Stage 1 一路打到 Stage 4，藍隊的監控面板竟然一片綠燈；直到 Stage 5 打崩了 Worker 才跳出一個找不到兇手的 `502` 告警，帳本少掉的 `$100.00` 甚至要等隔天財務對帳才發現。而在修補之後，紅隊在 Stage 2 到 Stage 5 的每一次試探，都會當場撞上結構化防線並留下精確的上下文告警，系統不變量從頭到尾紋絲不動。

---

### 紅隊事後報告怎麼寫才不會被當耳邊風？

很多技術很強的工程師，打完紅隊演練寫出來的報告卻常常被管理層或研發團隊擱置。原因很簡單：整份報告塞滿了幾十頁的 HTTP 請求截圖與工具輸出，卻沒有清楚回答「這對業務有多痛」以及「到底該改哪一行架構」。

一份能真正推動修補的紅隊報告，必須拆成兩個層次來寫：

第一個層次是寫給技術主管與風險決策者看的**高階摘要**（Executive Summary），用一頁篇幅說清楚兩件事：哪條業務不變量被打破（如 `10,000` 分帳本在 `< 1 ms` 併發下可被超額提領），以及跨層串聯後的風險定級。

按第 33 章方法，只要結合 CVSS v4.0 向量、EPSS `≥ 0.1` 或實質可利用性，就能直接排入 `24 小時` 嚴重 SLA 並附上建議止血順序。

第二個層次則是寫給後端與基礎設施團隊看的**技術根因分析**（Technical Root Cause），關鍵是指出整條攻擊鏈裡**最早失守的那一道信任邊界**。

舉例來說，Chain A 表面像是「HTTP/2 單封包併發太快」，但真正根因是「資料庫扣款把讀取與寫入拆成兩個非原子步驟，且沒鎖冪等鍵」。只有指對根因，藍隊才不會把工時浪費在調 WAF 限流上。

---

## 故障模式與防禦

### 藍隊分階段修補計畫（24 小時 / 7 天 / 長期架構）

面對橫跨四層邊界的複合式破口，藍隊不可能在一天之內把整套微服務重寫一遍，但也絕對不能放任雙花跟 SSRF 漏洞在線上繼續裸奔七天。最務實的工程做法，是嚴格切開三個時間維度，對齊全書基準的嚴重（`24 小時`）與高危（`7 天`）SLA：

| 修補階段 | 時間視窗 | 核心目標 | NexusPay 具體工程行動 |
|---|---|---|---|
| **第一階段：緊急止血** | `24 小時` 內 | 先切斷外部利用鏈，保住資金與密鑰，允許暫時犧牲一點非核心彈性 | 1. 提領 API 暫時掛上 Redis 分散式互斥鎖，限制單一帳戶同時只能跑 1 筆提領。<br>2. 邊緣 WAF 與 Nginx 強制拒收帶有雙重編碼或路徑跳躍字元的內部前綴請求。<br>3. 雲端層立刻掛上 Egress NetworkPolicy，阻斷應用 Pod 連往 `169.254.169.254`。<br>4. Node.js 呼叫 `libnexus-parse` 前，強制檢查整個封包不超過 `65,544 bytes`（`8 bytes` 檔頭加上 `65,536 bytes` payload 上限），並核對宣告長度與實際緩衝區大小一致。 |
| **第二階段：根因修復** | `7 天` 內 | 修好底層邏輯與組態缺陷，拔掉「只靠外圍擋」的脆弱假設 | 1. 帳本扣款改成 PostgreSQL 單條原子條件更新（`WHERE balance >= $1`），並綁定 `idempotency_key` 唯一約束。<br>2. 應用層全面換上第 34 章預設拒絕的 `@Policy` 授權中介層，並補上代理路徑對齊測試。<br>3. 雲端強制升級 IMDSv2（設為 `HttpPutResponseHopLimit = 1`），並把 Pod 的 IAM Role 砍到最小權限。<br>4. Rust/C FFI 原生層改用 `try_from` 與 `checked_add` 親自檢查 `8 bytes` 檔頭與 `65,536 bytes` 上限，不再依賴上層把關。 |
| **第三階段：長期架構防線** | 季度演進 | 靠 Paved Road 與 CI 自動化閘門，讓同類漏洞在未來的 PR 裡根本寫不出來 | 1. 封裝強制綁定租戶上下文的 `TenantDbClient`，以及內建 DNS/IP 雙重檢查的安全 HTTP Client。<br>2. 把紅隊這 3 條攻擊鏈的驗證條件，全部寫成 CI 必跑的自動化安全回歸測試。<br>3. 把 `libnexus-parse` 接上 `cargo-fuzz` 持續模糊測試（採用 ClusterFuzzLite 模式），每次發 PR 自動重跑回歸語料庫。 |

這裡要特別提醒一個藍隊最常踩的坑：**把「`24 小時` 緊急止血」直接當成「結案」**。

很多團隊在第一天加上 Redis 分散式鎖擋住併發提領之後，覺得線上沒再出事，就把修資料庫的工單無限期延後了。結果兩個月後 Redis 發生一次主從切換或網路抖動導致鎖短暫失效，底層沒設防的資料庫當場又被雙花打穿。記住，`24 小時` 止血只是幫你買到 `7 天` 根因修復的安全時間窗，兩步都走完才算真正修好。

---

### 自動化安全回歸測試與偵測工程

修好漏洞後的最後一哩路，是確保三個月後某位新來的工程師在重構結算服務時，不會順手把你辛苦建好的防線給拆了。最可靠的做法，就是把紅隊打破不變量的條件，直接改寫成確定性的整合測試鎖進 CI 管線。

下面示範兩段對應 Chain A 與 Chain C 的安全回歸測試（用 TypeScript 與 Jest 撰寫，專門驗證系統不變量與邊界錯誤處理，不含任何惡意攻擊載荷）：

```typescript
// 1. Chain A 回歸測試：驗證單次 20 筆併發提領下，帳本依然死守守恆不變量
describe('Security Regression: Ledger Concurrency Invariant', () => {
  it('enforces total debits <= 10,000 cents under 20 parallel requests', async () => {
    const accountId = await seedTestAccount({ initialBalanceCents: 10_000 });
    const withdrawAmount = 5_000;

    // 模擬單封包時間窗內同時湧入 20 筆提領請求（各自帶入獨立冪等鍵）
    const requests = Array.from({ length: 20 }, (_, i) =>
      ledgerService.withdraw({
        accountId,
        amountCents: withdrawAmount,
        idempotencyKey: `reg-test-${i}`,
      })
    );

    const results = await Promise.allSettled(requests);
    const succeeded = results.filter(
      (r) => r.status === 'fulfilled' && r.value.approved === true
    );
    const finalBalance = await ledgerRepo.getBalanceCents(accountId);

    // 核心安全斷言：最多只能成功 2 筆，且扣款總額加上剩餘餘額必須剛好等於 10,000 分
    expect(succeeded.length).toBeLessThanOrEqual(2);
    expect(finalBalance).toBeGreaterThanOrEqual(0);
    expect(succeeded.length * withdrawAmount + finalBalance).toBe(10_000);
  });
});

// 2. Chain C 回歸測試：驗證 libnexus-parse 收到超過 65,536 bytes 的 TLV 封包時會安全拒絕
describe('Security Regression: libnexus-parse Boundary Enforcement', () => {
  it('rejects TLV header declaring payload > 65,536 bytes without process crash', () => {
    const header = Buffer.alloc(8);
    header.writeUInt16BE(0x4e50, 0); // magic: "NP"
    header.writeUInt16BE(0x0001, 2); // type: settlement_report
    header.writeUInt32BE(65_544, 4); // len: 超出合法上限 65,536 bytes

    const oversizedFrame = Buffer.concat([header, Buffer.alloc(64)]);

    expect(() => nativeParser.parseTlv(oversizedFrame)).toThrow(/PayloadTooLarge|InvalidLength/);
  });
});
```

除了在 CI 裡跑回歸測試，線上的**偵測工程**（Detection Engineering）也要同步跟上。藍隊可以把前面六階段時間軸裡的關鍵攔截點，轉成結構化的告警規則：

- 當資料庫條件更新在短時間內對同一個帳戶密集出現 `affected_rows = 0`，就代表有人正在試探併發雙花時間窗。
- 當安全 HTTP Client 的 DNS 檢查攔到 `169.254.0.0/16` 或 `10.0.0.0/8` 這類私有位址時，馬上發出高優先級的出站 SSRF 告警。
- 當 `libnexus-parse` 回傳 `PayloadTooLarge` 或檔頭格式錯誤的比例突然飆高，就能第一時間抓到正在對二進位端點做 Fuzzing 探測的來源。

---

## 動手做

- **難度**：挑戰
- **預估時間**：90 分鐘

這是全書 NexusPay 實戰演練的總驗收（Capstone）。請在本地隔離的 NexusPay 綜合靶場環境中（啟動指令見附錄 A），打開計時器，獨立完成下面三項任務並記錄你的推導過程：

1. **全系統威脅建模與跨層路徑盤點**：先不要看前面的提示，對著啟動後的 NexusPay 四層架構，自己畫出至少 3 條跨層風險路徑（必須涵蓋邊緣／併發狀態機、應用／雲端控制平面，以及 `libnexus-parse` FFI 邊界）。請清楚寫出每條路徑打破了哪一條系統不變量，並標註相關的基準常數（如 `10,000` 分、`20` 筆併發、`65,536 bytes`）。
2. **藍隊分階段修補設計**：針對你找出的 3 條路徑，分別開出 `24 小時` 緊急止血措施、`7 天` 根因修復方案，以及一條能從源頭消滅這類漏洞的 Paved Road 架構護欄。
3. **自動化安全回歸測試驗證**：挑上面至少 2 條路徑，親手寫出非破壞性的自動化安全回歸測試（像是併發不變量測試、SSRF 阻斷測試或 TLV 邊界拒絕測試）。先在還沒修補的環境跑一次，親眼確認測試會紅燈失敗；接著套用你的修補方案再跑一次，確認所有測試全數轉綠通過。

### 參考解答

你可以用下面這三個驗收標準，來核對自己的演練成果（細節可依你本地靶場的分支版本微調）：

1. **威脅建模與路徑核對**：
   - **Web 與併發路徑**：檢查提領端點在同時收到 `20` 筆併發請求（模擬 `< 1 ms` 時間窗）時，是不是因為「先讀、再查、後寫」沒有包成原子操作，導致總提領金額突破 `10,000` 分。
   - **Cloud 與 SSRF 路徑**：檢查 Webhook 或報表匯入功能在發起連線前，有沒有驗證 DNS 解析後的真實 IP。只要沒擋掉 `169.254.169.254` 與內網網段，就會構成雲端憑證橫向洩漏風險。
   - **FFI 與 TLV 路徑**：檢查 `libnexus-parse` 收到 `len > 65,536 bytes` 或是 `len` 與實際緩衝區長度不合的 `8 bytes` 檔頭時，能不能平穩回傳結構化錯誤，而不是當場把行程撞死。
2. **修補驗證檢核點**：
   - `24 小時` 止血方案必須能立刻切斷外部攻擊路徑（例如掛上 Egress NetworkPolicy 擋掉 IMDS、在入口截斷超長封包、加上分散式鎖限流），而且不能拖垮正常商戶 `2,000 req/s` 的線上流量。
   - `7 天` 根因修復必須把安全檢查下沉到資源擁有者本身（PostgreSQL 單條原子更新、全面強制 IMDSv2 搭配最小 IAM 權限、Rust 側用 `checked_add` 鎖死邊界）。
3. **回歸測試驗收**：
   - 執行 `npm test -- --testPathPattern=security-regression` 時，所有安全斷言在修補前都要精準報錯（如 `succeeded.length * withdrawAmount + finalBalance === 10_000`、連往私有 IP 拋出 `SsrfBlockedError`、畸形 TLV 拋出 `PayloadTooLarge`）。
   - 套用修補後則要 100% 自動通過，且測試前後 Node.js 與 Rust Worker 的行程 PID 必須維持不變（代表零崩潰重啟）。

---

## 自我檢核

- **難度**：進階
- **預估時間**：30 分鐘

先別看下面的解答，試著用本章的紅藍對抗視角，回答這四個實戰覆盤常遇到的問題：

1. **告警盲區診斷**：在某次演練中，紅隊利用路徑正規化差異繞過 Nginx 的 `/internal/` 封鎖，成功打進後端 Node.js 服務並拿走跨租戶對帳單。事後藍隊查 Log，發現後端只有一筆平淡無奇的 `HTTP 200 OK`，完全沒觸發任何警報。請問藍隊在架構與觀測性上漏了哪兩件事？
2. **止血與根因的取捨**：假設線上提領 API 正在被併發雙花攻擊，藍隊值班工程師提議：「我們直接在 PostgreSQL 把整個資料庫的全域交易隔離等級改成 `SERIALIZABLE`，這樣 5 分鐘就能修好，連 `24 小時` 止血跟 `7 天` 拆階段都省了！」在 `2,000 req/s` 的尖峰流量下，這樣做會釀成什麼災難？正確的分階段做法是什麼？
3. **跨層串聯定級**：紅隊找到兩個單獨看起來不起眼的問題：(A) 某報表預覽 API 可讓伺服器對任意網址發送不帶認證的 `GET` 請求，只回傳 HTTP 狀態碼（Blind SSRF）；(B) 內網有台舊的密鑰代理服務，只要收到 `GET /rotate?debug=1` 就會把金鑰印在公開錯誤佇列裡。若報告把 A 和 B 分開寫成兩個「低危漏洞」，會出什麼問題？應該怎麼寫？
4. **回歸測試的設計邊界**：為什麼我們在寫 CI 自動化安全回歸測試時，要直接測試「`20` 筆併發下最終扣款總額加上餘額必等於 `10,000` 分」這個業務不變量，而不是去寫一個檢查「程式碼裡有沒有呼叫 `redis.lock()`」的靜態字串測試？

### 參考解答

1. **告警盲區診斷**：
   - 第一，後端缺乏**預設拒絕的統一授權中介層**（如第 34 章的 `@Policy` 宣告與租戶上下文比對），誤以為只要掛在 `/internal/` 底下就會由外層 Nginx 擋好，犯了「只在邊緣設防、內層完全不驗」的毛病。
   - 第二，缺乏**跨層路徑與權限拒絕遙測**。當請求走進敏感路由或嘗試存取非本租戶的資源時，後端中介層必須親自攔截並丟出帶有請求上下文的 `403` 結構化稽核告警，而不是依賴外層代理的攔截紀錄。
2. **止血與根因的取捨**：
   - 如果不改應用程式的重試與鎖定範圍，直接在 `2,000 req/s` 的高併發環境把全域隔離等級切到 `SERIALIZABLE`，大量的讀寫交易會因為序列化衝突（Serialization Failure）而瘋狂拋錯中斷，甚至塞爆資料庫連線池，直接演變成全站自我阻斷服務（DoS）。
   - 正確做法是：在 `24 小時` 內先對提領端點針對「單一帳戶粒度」加上分散式互斥鎖或限流來止血；接著在 `7 天` 內，把扣款 SQL 改寫成單條帶條件的原子更新（`UPDATE accounts SET balance = balance - $1 WHERE id = $2 AND balance >= $1`）搭配唯一冪等鍵，這樣既能鎖死資金守恆，又不會拖垮全站吞吐量。
3. **跨層串聯定級**：
   - 把 A 和 B 拆開報成兩個低危漏洞，會讓開發團隊把它們丟進底層 Backlog 排到半年後才修，完全沒意識到攻擊者只要拿 A 的 Blind SSRF 去打 B 的內網介面，馬上就能偷走整套系統的金鑰。
   - 在紅隊報告的高階摘要與根因分析裡，必須把「A 串接 B 奪取金鑰」畫成同一條跨層攻擊鏈，直接依最終破壞力（金鑰外洩）定級為嚴重漏洞（啟動 `24 小時` SLA），並在修補建議中同時要求切斷 A 的內網出站能力與修復 B 的未授權介面。
4. **回歸測試的設計邊界**：
   - 檢查有沒有呼叫 `redis.lock()` 只在測「實作細節」，一旦未來團隊把 Redis 鎖重構成資料庫原子更新，測試就會誤報失敗；反過來，如果有人雖然呼叫了 `redis.lock()`，卻把鎖的 Key 寫錯或放在扣款交易外面，靜態檢查會亮綠燈，雙花漏洞卻照樣復活。
   - 直接對「扣款總額 ＋ 剩餘餘額 === `10,000` 分」這個安全不變量下斷言，才能不管底層實作怎麼重構，永遠在 CI 裡替帳本守住最後一道底線。

---

## 延伸閱讀

- **NIST SP 800-61 Revision 3**（Incident Response Recommendations and Considerations for Cybersecurity Risk Management）：現代企業事件回應生命週期與復盤標準框架（https://csrc.nist.gov/pubs/sp/800/61/r3/final）。
- **OWASP Threat Modeling Cheat Sheet**：跨層架構信任邊界繪製與系統化威脅識別指南（https://cheatsheetseries.owasp.org/cheatsheets/Threat_Modeling_Cheat_Sheet.html）。
- **PortSwigger Web Security Academy — Race Conditions & HTTP Request Smuggling**：單封包攻擊（Single-Packet Attack）與前端／後端解析分歧的線上互動實驗（https://portswigger.net/web-security）。
- **Google OSS-Fuzz — Ideal Integration & Regression Testing**：如何將修補後的漏洞測試樣本固化為持續 Fuzzing 與自動化回歸閘門（https://google.github.io/oss-fuzz/getting-started/new-project-guide/）。
