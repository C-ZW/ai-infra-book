# 第 15 章：密碼學工程實戰破口

後端工程師在寫加密或簽章功能時，很少是因為 `AES-256` 或 `SHA-256` 本身的數學強度被攻破而出事。真實世界裡的密碼學漏洞，幾乎都爆在演算法外圍的工程細節上：解密失敗時噴出的錯誤訊息不小心告訴客戶端「填充格式對不對」、容器重啟讓 `96-bit` Nonce 計數器歸零重用、直接拿 `===` 比對 Webhook 簽章字串，或是圖方便用 `Math.random()` 產生重設密碼連結。

一旦這些工程邊界失守，攻擊者根本不需要去窮舉 `2^256` 的金鑰空間。只要發幾千次 HTTP 請求，或是攔到兩筆共用同一個 Nonce 的密文，就能在完全不知道金鑰的前提下還原明文、偽造認證標籤，甚至直接接管商戶帳號。本章就從區塊與狀態機的底層合約切入，拆解五類最常見的密碼學工程破口與防禦寫法。

---

## 從你已知的出發

為什麼明明用了工業級的 `AES-256-CBC` 加密 Cookie，也用了 `AES-256-GCM` 保護敏感資料，攻擊者手上一把金鑰都沒有，卻還是能逐字解開 Cookie 內容，甚至自己捏造出一張能通過 GCM 驗證的管理員憑證？

因為密碼學演算法不是只要「金鑰夠長」就萬無一失，每一個原語背後都有一條絕對不能踩破的使用鐵律。以 `AES-CBC` 來說，解密端會先拿前一個密文區塊做 XOR，接著檢查尾端的 PKCS#7 填充位元組；只要你的 API 對「填充格式錯誤」回傳 `500`、對「JSON 解析或權限錯誤」回傳 `401`，這個微小的狀態碼差異就成了替攻擊者逐一核對明文的免費算命仙（Padding Oracle）。

而 `AES-GCM` 雖然補上了認證標籤，但它的整個數學安全都建立在「同一把金鑰下，`96-bit` Nonce 永遠不能重複」這條不變量上；只要容器重啟或寫死 IV 讓 Nonce 撞號一次，兩筆密文一做 XOR 就會當場吐出明文差值與內部驗證金鑰。

延續第 4 章看過的 `RS256` JWT 信任根破口（`2048-bit` RSA、有效期 `900 s`、JWKS 快取 TTL `300 s`），這章我們繼續往下挖，直接檢視支撐 Cookie、Webhook 與隨機權杖的底層密碼學實作。

---

## 機制與推導

### 攻擊者目標與實質影響

攻擊者挑應用層的密碼學實作下手，目的就是跳過「硬解金鑰」這堵高牆，用幾千次網路請求或幾筆公開輸出，直接換取系統最高權限：

在加密資料上，目標是**無金鑰解密與密文偽造**。利用 AES-CBC Padding Oracle，攻擊者不必知道金鑰就能一塊一塊解開 NexusPay 的加密 Session Cookie；更狠的是還能反過來利用它構造出任意指定內容的合法密文（CBC-R），直接把自己變成商戶管理員。

要是碰到 AES-GCM 在同一把金鑰下重用了 `96-bit` Nonce，後果更是**機密性與完整性的雙重崩潰**。重用 Nonce 不但會直接洩漏兩段明文重疊處的差值 `P1 ⊕ P2`，還會暴露底層的 GHASH 驗證金鑰 `H`。

把兩個認證標籤做 XOR 消掉遮罩後，會得到關於 `H` 的有限體多項式方程，在單區塊等長且無 AAD 時能直接算出唯一解，多區塊時也能解出少數候選根並篩出真值。拿到 `H` 之後，攻擊者就能在該重用 Nonce 與已知金鑰流範圍內，隨意竄改密文並算出 100% 合法的認證標籤。

在簽章與隨機數上，目標則是**偽造 Webhook 與預測未來權杖**。如果後端用非恆定時間的字串比對來驗 HMAC，微秒級的時間差就會把簽章內容洩漏出去，讓攻擊者偽造「結算成功」的回呼入帳。如果拿 `Math.random()` 去產生交易流水號與重設密碼連結，攻擊者只要看幾筆公開流水號就能反推 V8 引擎的內部狀態，精準算出下一位使用者的密碼重設 Token，直接串起第 6 章的跨租戶存取與第 12 章的帳本提領漏洞。

---

### AES-CBC Padding Oracle：從 1-bit 錯誤訊息到完整明文解密

AES 是區塊加密演算法（Block Cipher），每個區塊的大小固定是 `128 bits`（`16 bytes`）。在 CBC（Cipher Block Chaining）模式下，要解開第 `i` 個密文區塊 `C_i`，流程長這樣：

```text
  C_{i-1} (16 bytes)               C_i (16 bytes)
         |                                |
         |                                v
         |                       +-----------------+
         |                       |   AES_Decrypt   | <-- Key K
         |                       +--------+--------+
         |                                |
         |                                v
         |                       I_i = D_K(C_i)  (Intermediate State)
         |                                |
         +-------------> (XOR) <----------+
                           |
                           v
                 P_i = I_i ^ C_{i-1}
                           |
                           v
            +------------------------------+
            | PKCS#7 Padding Check:        |
            | last byte k in 0x01..0x10,   |
            | and last k bytes all == k    |
            +--------------+---------------+
                           |
            +--------------+--------------+
            | Invalid Padding             | Valid Padding
            v                             v
      HTTP 500 /                    HTTP 401 /
      "Bad Decrypt"                 "Invalid Session"
```

因為明文的總長度不一定剛好是 `16 bytes` 的整數倍，加密時函式庫會照 PKCS#7 規範把最後一塊補滿。假設距離 16 的倍數還差 `k` 個位元組（`k = 16 - (明文長度 mod 16)`，所以 `1 ≤ k ≤ 16`），就在尾巴填入 `k` 個數值剛好等於 `k` 的位元組（十六進位從 `0x01` 到 `0x10`）。比如差 1 byte 就補一個 `0x01`；差 2 bytes 就補 `0x02 0x02`；如果原本長度就剛好是 16 的倍數，則會額外多補一整塊 16 個 `0x10`。

漏洞就出在解密時的順序：**後端一定是先算完 `I_i ^ C_{i-1}`、先檢查 PKCS#7 填充合不合法，通過之後才會把明文拿去跑 `JSON.parse()` 或檢查 Session 權限**。只要伺服器在「填充不合法」（例如噴 `500 Bad Decrypt`）跟「填充合法但業務內容不對」（例如回 `401 Invalid Session`）時表現出任何一點不同，攻擊者手上就多了一個每次能問出 1-bit 真假的 **Padding Oracle**。

有了這個 Oracle，假設攻擊者想解開 `C_i`，他根本不用管原本的前一個區塊 `C_{i-1}` 是什麼，而是自己捏造一個可控的假區塊 `C'_{i-1}`，接在 `C_i` 前面送給伺服器解密：

第一步，**先攻破最後一個位元組（索引 15）**。我們把 `C'_{i-1}[0..14]` 固定住（比如全部填 `0x00`），然後讓最後一個位元組 `C'_{i-1}[15]` 從 `0x00` 一路試到 `0xff`（最多試 `256` 次）。只要伺服器突然不再報 Padding Error（改回 `401`），就代表解密出來的最後一個位元組湊出了合法的 PKCS#7 填充！

絕大多數時候，這代表解出來的最後一個位元組變成了 `0x01`。唯一需要小心的小插曲是：萬一前面未改動的倒數第二個位元組 `P'_i[14] = I_i[14] ^ C'_{i-1}[14]` 剛好等於 `0x02`（或剛好構成某段長度 `k ∈ {2..16}` 的合法填充前綴），那當我們試到另一個候選值 `g_2 = I_i[15] ^ 0x02` 時，尾巴兩個位元組就會湊成合法的 `0x02 0x02` 而同樣通過檢查。

因為前 15 個位元組固定時，倒數第二個位元組最多只會指定一種較長的填充長度，所以最多只會多出這一個混淆候選值。要排除它非常簡單：只要在命中時，順手把倒數第二個位元組翻轉一個 bit（`C'_{i-1}[14] ^= 0x01`）再多送 1 次確認請求，任何長度 `k ≥ 2` 的填充都會當場被破壞；如果翻轉後依然通過檢查，那就 100% 確定最後一個位元組真的是 `0x01`。

一旦確定 `I_i[15] ^ C'_{i-1}[15] = 0x01`，移項一下就能立刻算出未知的中間狀態與真實明文：
- 中間狀態：`I_i[15] = C'_{i-1}[15] ^ 0x01`
- 真實明文：`P_i[15] = I_i[15] ^ C_{i-1}[15]`

第二步，**往前推進到倒數第二個位元組（索引 14）**。現在我們已經知道 `I_i[15]` 的真值了，於是把假區塊的最後一格改成 `C'_{i-1}[15] = I_i[15] ^ 0x02`，強迫解密結果的最後一格固定變成 `0x02`。接著同樣拿 `C'_{i-1}[14]` 從 `0x00` 試到 `0xff`；只要 Oracle 回報填充合法，就代表倒數第二格也湊成了 `0x02`！於是立刻算出 `I_i[14] = C'_{i-1}[14] ^ 0x02`，真實明文就是 `P_i[14] = I_i[14] ^ C_{i-1}[14]`。

第三步，**一路往左推完 16 bytes**。照這個節奏一路推到索引 `0`，整塊 `16-byte` 明文就一字不漏地解出來了。

我們來算一下需要打多少次請求：每個位元組的主要試探最壞要試 `256` 次；如果正確值均勻分布在 `1..256` 且一猜中就停，單一位元組的期望查詢次數是 `(1 + 256) / 2 = 128.5` 次（工程估算常記為約 `128` 次）。

所以解開一個 `16-byte` 區塊，最壞主要查詢數是 **`16 × 256 = 4,096` 次**（加上最後一格排除歧義的 `1` 到 `2` 次確認請求為 `4,097` 到 `4,098` 次），主要試探的平均查詢數則約為 **`16 × 128 = 2,048` 次**（精確離散期望值為 `16 × 128.5 = 2,056` 次；加計確認請求後的總期望約為 `2,057.002` 次）。

#### Worked Example 1：AES-CBC Padding Oracle 逐位元組實算

假設 NexusPay 舊版的加密 Cookie 用的是 `AES-256-CBC`，攻擊者從瀏覽器抓到兩塊連續的 16-byte 密文 `C_{i-1}` 與 `C_i`。下面我們把真實的中間狀態 `I_i = D_K(C_i)` 攤開來，一步步算給你看攻擊者是怎麼隔空摸出明文的：

```text
已知攔截密文區塊 (16 bytes):
  C_{i-1} = 3a 7f 12 9c 44 01 b8 e2 7d 55 90 a1 c3 4e 6f 18
  [索引]     0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15

目標明文真值 (驗證用，攻擊前未知):
  P_i     = {"role":"user"}\x01
          = 7b 22 72 6f 6c 65 22 3a 22 75 73 65 72 22 7d 01
  I_i     = 41 5d 60 f3 28 64 9a d8 5f 20 e3 c4 b1 6c 12 19

--- 步驟 1：破解 byte[15] (目標填充 0x01) ---
構造 C'_{i-1} = 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 XX
遍歷 XX = 0x00 .. 0xff (共 256 種可能):
  當 XX = 0x18 時:
    解密末位元組 = I_i[15] ^ 0x18 = 0x19 ^ 0x18 = 0x01  --> Oracle 回傳 Padding Valid (HTTP 401)
  (註：需檢查邊界案例，若改動 C'_{i-1}[14] 為 0x01 後依然 Valid，確認填充長度為 1 而非 0x02 0x02)

反推 I_i[15] 與 P_i[15]:
  I_i[15] = 0x18 ^ 0x01 = 0x19
  P_i[15] = I_i[15] ^ C_{i-1}[15] = 0x19 ^ 0x18 = 0x01 (確認最後 1 byte 為 PKCS#7 填充 0x01)

--- 步驟 2：破解 byte[14] (目標填充 0x02 0x02) ---
固定 C'_{i-1}[15] = I_i[15] ^ 0x02 = 0x19 ^ 0x02 = 0x1b
構造 C'_{i-1} = 00 00 00 00 00 00 00 00 00 00 00 00 00 00 YY 1b
遍歷 YY = 0x00 .. 0xff:
  當 YY = 0x10 時:
    解密末兩位元組 = (I_i[14] ^ 0x10, I_i[15] ^ 0x1b)
                   = (0x12 ^ 0x10, 0x19 ^ 0x1b) = (0x02, 0x02) --> Oracle 回傳 Padding Valid

反推 I_i[14] 與 P_i[14]:
  I_i[14] = 0x10 ^ 0x02 = 0x12
  P_i[14] = I_i[14] ^ C_{i-1}[14] = 0x12 ^ 0x6f = 0x7d (ASCII '}')

--- 查詢次數總結 (16-byte 區塊主要試探) ---
  最壞情況: 16 bytes * 256 次/byte = 4,096 次請求 (另加 byte[15] 確認請求至多 1~2 次)
  平均情況: 約 16 bytes * 128 次/byte = 2,048 次請求 (精確離散期望值 16 * 128.5 = 2,056 次)
  若密文共 4 個需解密區塊 (64 bytes)，平均僅需約 4 * 2,048 = 8,192 次 (精確期望 8,224 次) HTTP 請求即可全數解密。
```

更可怕的是，這招還能倒著用，把「解密 Oracle」變成「加密 Oracle」（也就是 **CBC-R**）。攻擊者想偽造什麼明文 `P_target_n`，就先隨便挑一塊最後的密文 `C_n`，用 Padding Oracle 算出它的中間狀態 `I_n`，然後把前一塊密文直接設成 `C_{n-1} = I_n ^ P_target_n`。這樣伺服器在解 `C_{n-1} || C_n` 時，算完 `I_n ^ C_{n-1}` 就會乖乖吐出攻擊者指定的 `P_target_n`，一路往前推回 IV 就能憑空捏造出整串合法的加密 Cookie。

---

### AES-GCM Nonce 重用：CTR 流密碼重疊與 GHASH 金鑰 `H` 洩漏

為了徹底解決 CBC 沒有完整性保護跟 Padding Oracle 的毛病，現代後端幾乎都改用認證加密（AEAD，Authenticated Encryption with Associated Data），其中的主力就是 `AES-256-GCM`。照 NIST SP 800-38D 規範，AES-GCM 的區塊大小一樣是 `128 bits`（`16 bytes`），而標準的 Nonce（或稱 IV）長度則是 `96 bits`（`12 bytes`）。

要看懂 GCM 為什麼怕 Nonce 重用，得先看懂它內部的兩條運算流水線：

第一條是負責加密的**計數器模式（CTR）**。系統會把 `96-bit` Nonce `N` 後面補上一個 32-bit 的初始計數器 `0x00000001`，拼成 `128-bit` 的 `J_0 = N || 0x00000001`。接著要加密第 `j` 個明文區塊 `P_j`（`j = 1, 2, ..., m`）時，就把 `J_0` 的最後 32 位元加 `j` 次（記為 `inc_32^j(J_0)`）送進 AES 加密產生金鑰流，再跟明文做 XOR：`C_j = P_j ⊕ E_K(inc_32^j(J_0))`（最後一塊如果不滿 16 bytes 就只取對應長度的金鑰流）。

第二條是負責防竄改的**多項式認證標籤（GHASH）**。系統先拿全零區塊加密算出認證金鑰 `H = E_K(0^128)`。接著把各自補零對齊到 128-bit 的附加驗證資料 `AAD`、所有密文區塊 `C_1..C_m`，還有以位元數（bit length）表示的長度區塊 `L = bitlen(AAD) || bitlen(C)`（兩個 64-bit 無號整數拼成 128 bits），全部當成有限體 `GF(2^128)` 上的多項式係數，算出 `GHASH_H(AAD, C)`，最後再跟 `E_K(J_0)` 做 XOR 產生 `128-bit` 的認證標籤 Tag `T`。

拿沒有 AAD 的單區塊密文來說，公式非常乾淨：
`T = (C_1 · H^2) ⊕ (L · H) ⊕ E_K(J_0)`（這裡的乘法跟加法都是在有限體 `GF(2^128)` 底下算的）。

只要每次加密的 `(K, N)` 組合都不一樣，這套設計固若金湯。但工程師常在三個地方踩雷：一是為了省事把 Nonce 寫死成全零或固定常數；二是把遞增計數器存在記憶體裡，結果容器一重啟或橫向擴容成多個 Pod，大家又從 `1` 開始算。

三是用隨機數產生 `96-bit` Nonce，卻在單一金鑰下呼叫超過安全上限（NIST SP 800-38D 規定，為了把碰撞機率壓在 `2^{-32}` 以下，單把金鑰搭配隨機 `96-bit` Nonce 的總加密次數不得超過 `2^32` 次；由生日界線可知 `2^32` 次獨立抽樣的碰撞機率上界約為 `2^{-33}`）。

只要同一組 `(K, N)` 被拿去加密了兩筆不同的資料，災難就會瞬間爆發（密碼學上稱為 **Forbidden Attack**）：

首先是**機密性當場歸零**。因為 `K` 跟 `N` 一樣，初始計數器 `J_0` 就一模一樣，後面產生的整條金鑰流 `S_j = E_K(inc_32^j(J_0))` 也完全一模一樣。攻擊者只要把攔到的兩段密文拿來做 XOR，金鑰流就會自己消掉：`C1 ⊕ C2 = (P1 ⊕ S) ⊕ (P2 ⊕ S) = P1 ⊕ P2`。只要其中一段明文是已知的（或是像 JSON 欄位名 `{"role":"` 這種固定格式），另一段明文就會直接顯形。

更致命的是**認證標籤也一起崩潰**。因為兩筆資料共用同一個 `J_0`，保護標籤的最後那層遮罩 `E_K(J_0)` 也完全相同！把兩個標籤拿來做 XOR（`T1 ⊕ T2`），最難猜的 `E_K(J_0)` 當場對消；如果兩筆資料的 `AAD` 長度與密文長度也一樣，連 `L · H` 那一項也會一起消掉。

這時整個式子只剩下未知數 `H` 與已知密文差值組成的 `GF(2^128)` 多項式方程 `f(H) = 0`。解出 `H` 之後，攻擊者連 AES 金鑰 `K` 長什麼樣都不用知道，就能在這個重用的 Nonce `N` 底下隨便改密文、隨便改 AAD，並自己算出能 100% 騙過伺服器的合法 Tag `T'`。

#### Worked Example 2：AES-GCM `96-bit` Nonce 重用實算（還原 `P1 ⊕ P2` 與 GHASH 金鑰 `H`）

我們直接拿真實的 `AES-128-GCM` 數值來算一遍（`AES-256-GCM` 的 `128-bit` 區塊與 `96-bit` Nonce 推導過程完全一模一樣）：

```text
環境參數:
  Key   K = 00112233445566778899aabbccddeeff (128-bit)
  Nonce N = a1b2c3d4e5f60718293a4b5c         (96-bit / 12 bytes, 重複使用!)
  AAD     = "" (0 bytes)
  (系統真實 GHASH 金鑰 H = E_K(0^128) = fde4fbae4a09e020eff722969f83832b)

加密兩筆 16-byte 權限結構:
  P1 = {"role":"guest"}  -> C1 = 3d95d2cedaf3e65bc00bd5dc2d6c070d
                            T1 = 0e66f962def7f575ce5294ef582ba037
  P2 = {"role":"admin"}  -> C2 = 3d95d2cedaf3e65bc00dc4d43776070d
                            T2 = fb498f3b8d4126c959b8f4c43e822e13

--- 1. 機密性破壞：消去金鑰流 ---
  C1 ^ C2 = 0000000000000000000611081a1a0000
  已知前綴為 {"role":" (9 bytes) 且結尾為 "} (2 bytes)，差值位於 bytes [9..13]:
  "guest" (67 75 65 73 74) ^ 06 11 08 1a 1a = 61 64 6d 69 6e ("admin")

--- 2. 完整性破壞：在 GF(2^128) 上消去 E_K(J_0) 並還原 H ---
  對 16-byte 單區塊且 AAD 為空的情況:
    T1 = (C1 · H^2) ^ (L · H) ^ E_K(J_0)
    T2 = (C2 · H^2) ^ (L · H) ^ E_K(J_0)
  兩式 XOR 後，(L · H) 與 E_K(J_0) 完全對消:
    T1 ^ T2 = (C1 ^ C2) · H^2
    dT      = 0e66f962def7f575ce5294ef582ba037 ^ fb498f3b8d4126c959b8f4c43e822e13
            = f52f765953b6d3bc97ea602b66a98e24
    dC      = 0000000000000000000611081a1a0000
  在 GF(2^128) (不可約多項式 x^128 + x^7 + x^2 + x + 1) 中求反元素與平方根:
    H^2 = dT · (dC)^(-1)
    H   = (H^2)^(2^127) = fde4fbae4a09e020eff722969f83832b  (與真值 100% 吻合!)

--- 3. 任意偽造密文與合法 Tag ---
  攻擊者欲將 P1 竄改為 P_forged = {"role":"super"}:
    Keystream S1 = C1 ^ P1
    C_forged     = P_forged ^ S1 = 3d95d2cedaf3e65bc01fd5c93b6a070d
    T_forged     = T1 ^ ((C_forged ^ C1) · H^2) = 3767b53ddde9970dab72cdd9fcf4a70e
  伺服器以 AESGCM(K).decrypt(N, C_forged || T_forged, AAD) 驗證:
    結果: 通過 Tag 驗證，成功解密出 b'{"role":"super"}'！
```

如果攔到的兩筆密文超過一個區塊，或是帶有不同長度的 `AAD`，那 `T1 ⊕ T2` 就會變成一個最高次項為 `d` 次的多項式方程 `f(H) = 0`。這時只要在 `GF(2^128)` 上跑 Cantor-Zassenhaus 多項式因式分解，就能把 `H` 縮小到最多 `d` 個候選解；接著再拿第三筆重用的密文交叉比對，或是送去給伺服器的驗證端試一下（Tag Oracle），馬上就能揪出唯一正確的那把 `H`。

---

### Timing Side-Channel：非恆定時間 HMAC 比對與早期返回

再來看 Webhook 驗簽。HMAC-SHA256 本身幾乎不可能被暴力碰撞，但很多工程師算完正確簽章後，最後一步卻這樣寫：

```typescript
const expected = crypto.createHmac('sha256', webhookSecret).update(rawBody).digest('hex');
if (req.headers['x-nexus-sig'] !== expected) {
  return res.status(401).json({ error: 'invalid signature' });
}
```

問題就出在那個 `!==` 上。不管是 JavaScript 的 `===`、C 語言的 `memcmp` 還是一般語言的字串比對，為了追求速度，底層都是**從左到右逐位元組（或逐字組）比對，一發現不一樣就立刻提早返回（Early Exit）**。如果第 1 個字元就錯了，迴圈跑 1 步就收工；如果前 10 個字元都猜對，迴圈就會多跑 10 步才在第 11 個位置失敗。

在能夠精準分辨前綴匹配長度的理想側通道模型下，這個提早返回的特性，會把原本要猜 `2^256` 次（64 個十六進位字元就是 `16^64`）的天文數字，直接砍成「一個字元一個字元慢慢猜」的線性搜尋：總共只要猜 `32 bytes × 256 = 8,192` 個候選值（如果按 64 個 hex 字元逐字分辨，更是只有 `64 × 16 = 1,024` 個候選值；實際發出的總請求數就是候選數乘上每個候選需要的統計取樣次數）。

當然，在真實世界裡，多跑一圈位元組迴圈的時間差只有幾奈秒到幾十奈秒，隔著公網幾十毫秒的網路抖動是很難直接量出來的。但在下面三種場景裡，時序側通道（Timing Side-Channel）依然是能打穿防線的真威脅：

第一是**同機房、同 VPC 的內部微服務或 Sidecar 通訊**。內網延遲非常穩定，抖動只有幾十微秒，攻擊者只要對每個候選值打上千次請求，取中位數或第 10 百分位數濾掉 GC 跟長尾雜訊，就能把單步迴圈的微小時間差揪出來。

第二是**框架或後端邏輯不小心把時間差放大了**。比如比對前先做了複雜的 UTF-8 正規化，或是每比對一個區塊就觸發記憶體配置與紀錄，直接把奈秒級的差異放大到微秒級。

第三是**遇到短 Token 或截斷簽章**。像是 6 位數 OTP 或只取前 8 碼的短簽章，因為字元數極少，取樣驗證的成本就會大幅降低。

---

### 弱 PRNG 與 V8 `Math.random()`（`xorshift128+`）狀態預測

當系統需要產生密碼重設連結、Session ID、OAuth `state` 或一次性驗證碼時，如果不小心用了 `Math.random()`（或是 C 的 `rand()`、Python 的 `random` 模組），最嚴重的問題不是「亂數不夠亂可能會撞號」，而是**它的內部狀態可以被完整倒推出來**。

Node.js 與 Chrome 底層的 V8 引擎，是用 `xorshift128+` 演算法來實作 `Math.random()` 的。它的整個內部狀態只有兩個 64-bit 無號整數 `(state0, state1)`，加起來才區區 `128 bits`。每次你呼叫 `Math.random()`，它裡面只做了幾次單純的位元移位（Shift）跟 XOR：

```text
s1 = state0
s0 = state1
state0 = s0
s1 ^= (s1 << 23)        // 64-bit unsigned shift
s1 ^= (s1 >> 17)
s1 ^= s0
s1 ^= (s0 >> 26)
state1 = s1
// 取出 64-bit 狀態輸出的高 52/53 bits 填入 IEEE 754 binary64 (52-bit 顯式小數欄位 / 53-bit 有效位數) 回傳 [0, 1)
```

致命傷在於：**整個狀態更新過程，完完全全是 `GF(2)` 上的線性運算（只有移位跟 XOR）**。而且每次呼叫 `Math.random()`，它都會把當下 128-bit 狀態裡的高 `52` 到 `53 bits` 直接包進回傳的 IEEE 754 雙精度浮點數裡送給你。

因為單次輸出只露出高 52 bits，前兩筆輸出各自留了低位沒曝光，只看前三筆輸出時方程式的秩（Rank）最多只有 117，還湊不滿 128 個未知位元。

但只要攻擊者從任何公開的地方，拿到同一個 Node.js 行程連續吐出的 **4 到 5 個** `Math.random()` 輸出（比如系統拿 `Math.random().toString(36).slice(2)` 去產生公開的 `X-Request-Id` 放在 HTTP 回應標頭裡，而且中間沒有夾雜其他未知呼叫，讓收集到的高位約束在 `GF(2)` 或位元向量方程組上達到滿秩 `128`），就能把這 128 個未知 bit 列成線性方程組丟進 Z3 求解器。

不到一秒鐘，內部的 `(state0, state1)` 就會被算得一清二楚——往回推可以算出剛剛發給別人的 Token，往後推則能精準算出下一秒系統即將產生的管理員密碼重設連結。

---

### 金鑰管理與輪換破口

就算你乖乖用了 `AES-256-GCM`、`HMAC-SHA256` 跟 `crypto.randomBytes()`，如果在金鑰的生命週期管理上偷懶，整道防線還是會瞬間瓦解。

最常見的是**直接拿弱密碼當金鑰，或是所有功能共用同一把主金鑰**。例如程式裡寫了 `process.env.SESSION_SECRET || 'dev-secret'`，上線時忘了設環境變數就直接用 `'dev-secret'`；或是把人類設的短密碼沒有經過 Argon2id / scrypt 這類帶隨機鹽值與高運算成本的 KDF 做金鑰拉伸（Key Stretching），就直接塞進 AES。

又或者，系統雖然有一把高強度的主金鑰，卻沒有用 HKDF（搭配明確的 `info` 用途標籤）派生出不同用途的子金鑰，而是拿同一串位元組既簽 Webhook HMAC、又加密 Session Cookie、還拿去簽第 4 章的 JWT。這叫缺乏**用途隔離**（Domain Separation），只要其中一個小端點出包洩漏了金鑰特徵，全站所有防線就跟著一起陪葬。

另一個工程痛點是**金鑰輪換（Key Rotation）沒設版本號與緩衝期**。回想一下 NexusPay 的基準設定：`RS256` JWT 的有效期是 `900 s`，而驗證端對 JWKS 公鑰清單的快取 TTL 是 `300 s`。如果你在簽發憑證或加密封包時沒有帶上 `kid`（Key ID）或版本號，在換金鑰的過渡期裡，驗證端根本不知道該拿哪一把金鑰來解，只能把所有有效金鑰抓出來盲試一輪。

標準的無痛輪換流程，必須嚴格照著時間軸走：**先在 JWKS 掛上新公鑰，等過了 `> 300 s` 確定所有節點的快取都拿到新公鑰後，才把簽發端切換成新私鑰；接著再等 `> 900 s`，確定舊私鑰簽出去的 Token 全部自然過期之後，才能把舊公鑰從清單上撤掉**。

---

## 故障模式與防禦

我們把前面拆解的五種密碼學破口與修補標準，整理成這張工程對照表：

| 故障模式 | 為什麼會被打穿 | 真正能鎖死邊界的防禦設計 |
|---|---|---|
| 只用 `AES-CBC` 沒加認證 | 密文可被任意改動，而且「填充錯誤」跟「業務錯誤」的不同回應會形成 1-bit Padding Oracle | 全面改用 AEAD（`AES-256-GCM` 或 `ChaCha20-Poly1305`）；若受限於舊系統必須用 CBC，務必採 **Encrypt-then-MAC**，在解密前先用恆定時間驗完 MAC |
| `AES-GCM` Nonce 重用或歸零 | 寫死 IV、容器重啟讓計數器歸零，或同一把金鑰隨機產生 Nonce 超過 `2^32` 次 | 單把金鑰每次都用 CSPRNG 產生 `96-bit` 隨機 Nonce，並控制總調用次數遠低於 `2^32`；高吞吐量系統改用 HKDF 搭配每筆請求的 `128-bit` Salt 派生一次性子金鑰 |
| 用 `===` 或 `memcmp` 比對簽章 | 比對失敗就提早返回，讓執行時間洩漏出猜對了幾個前綴字元 | 一律改用 `crypto.timingSafeEqual(a, b)`；為避免長度不同直接拋出例外，比對前須先固定轉成等長 Buffer 或做雙重 HMAC（Double-HMAC）盲化 |
| 用 `Math.random()` 產生安全憑證 | V8 的 `xorshift128+` 內部狀態才 128 bits 且是純線性運算，前 3 筆輸出秩最多 117，看連續 4–5 筆輸出湊滿秩 128 就能完全算穿 | 凡是跟安全有關的隨機數，一律呼叫作業系統級的 CSPRNG（如 `crypto.randomBytes(32)` 或 `crypto.randomUUID()`） |
| 金鑰寫死預設值或沒有版本號 | 環境變數漏設就退回預設弱金鑰；密文沒帶 `kid` 導致金鑰外洩時不敢換、換了全站斷線 | 服務啟動時強制檢查金鑰存在性與長度（拒收預設字串，由 KMS/CSPRNG 給足熵值）；所有密文封套都帶上 `keyVersion` / `kid` 並用 `AAD` 綁定租戶上下文 |

### 防禦實作基準：NexusPay 加密 Cookie 與 Webhook 驗簽

下面我們直接用 TypeScript 寫出 NexusPay 處理加密 Cookie 與 Webhook 驗簽的標準範本。看程式碼時，請特別留意裡面解決了兩個實務上超容易踩坑的細節：

第一個細節是 **用 GCM 的 AAD（附加驗證資料）鎖死租戶與版本號**。我們在加密 Cookie 時，把 `tenantId` 跟 `keyVersion` 寫進 AAD 裡；到了解封（`unsealSessionCookie`）的時候，**必須先檢查封套上的版本號有沒有低於系統允許的最低版本 `minAcceptedVersion`，接著再拿「當前請求已經認證通過的目標租戶 ID」去重新組出 AAD 丟進 GCM 驗證**。

這樣一來，就算攻擊者把租戶 A 的合法加密 Cookie 偷搬到租戶 B 的請求裡用，或是拿已經退役的舊版金鑰密文來重放，在 GCM 驗 Tag 那一關就會直接炸開（至於同租戶、同版本內的重放攻擊，則要在 payload 裡加上 `exp` 過期時間與單次 `jti` 來擋）。

第二個細節是 **`timingSafeEqual` 的長度陷阱與雙重 HMAC 盲化**。Node.js 的 `crypto.timingSafeEqual(bufA, bufB)` 有個硬限制：只要傳進去的兩個 Buffer 長度差了一個 byte，它就會直接拋出 `RangeError` 例外——如果不小心沒接好，這個例外本身又變成洩漏長度的側通道。

最穩的做法是：先用正規表達式確認傳進來的簽章是不是合法的 64 字元 hex 格式並轉成 `32 bytes` Buffer（格式不對就拿全零的 `32 bytes` Buffer 代打，最後再跟格式檢查結果做 AND），接著用現場隨機產生的 `32-byte` 盲化金鑰對兩邊再算一次 HMAC（Double-HMAC），把兩邊都壓成固定 `32 bytes` 的隨機摘要後再交給 `timingSafeEqual`。這樣既不會拋出長度例外，也徹底抹掉了原本秘密 MAC 的前綴特徵。

```typescript
import crypto from 'node:crypto';

interface EncryptedEnvelope {
  v: number;       // 金鑰版本 (keyVersion)
  iv: string;      // 12-byte (96-bit) base64url Nonce
  tag: string;     // 16-byte (128-bit) GCM Auth Tag
  ct: string;      // 密文
}

// 1A. 以 AES-256-GCM 加密，並透過 AAD 綁定租戶與版本上下文
export function sealSessionCookie(
  masterKeys: Record<number, Buffer>,
  activeVersion: number,
  tenantId: string,
  payload: object
): string {
  const key = masterKeys[activeVersion];
  if (!key || key.length !== 32) {
    throw new Error('Invalid 256-bit master key');
  }

  // 每次加密皆向 OS CSPRNG 取得全新 96-bit Nonce
  const iv = crypto.randomBytes(12);
  const aad = Buffer.from(`v=${activeVersion};tenant=${tenantId}`, 'utf8');

  const cipher = crypto.createCipheriv('aes-256-gcm', key, iv);
  cipher.setAAD(aad);

  const plaintext = Buffer.from(JSON.stringify(payload), 'utf8');
  const ct = Buffer.concat([cipher.update(plaintext), cipher.final()]);
  const tag = cipher.getAuthTag(); // 固定 16 bytes

  const envelope: EncryptedEnvelope = {
    v: activeVersion,
    iv: iv.toString('base64url'),
    tag: tag.toString('base64url'),
    ct: ct.toString('base64url'),
  };
  return Buffer.from(JSON.stringify(envelope), 'utf8').toString('base64url');
}

// 1B. 解封並強制檢查最低允許金鑰版本與可信租戶 AAD
export function unsealSessionCookie(
  masterKeys: Record<number, Buffer>,
  minAcceptedVersion: number,
  expectedTenantId: string,
  token: string
): unknown {
  const env = JSON.parse(Buffer.from(token, 'base64url').toString('utf8')) as EncryptedEnvelope;
  if (typeof env.v !== 'number' || env.v < minAcceptedVersion) {
    throw new Error('Rejected retired or invalid key version');
  }
  const key = masterKeys[env.v];
  const iv = Buffer.from(env.iv, 'base64url');
  const tag = Buffer.from(env.tag, 'base64url');
  const ct = Buffer.from(env.ct, 'base64url');
  if (!key || key.length !== 32 || iv.length !== 12 || tag.length !== 16) {
    throw new Error('Malformed envelope parameters');
  }

  // 以呼叫端提供的可信 expectedTenantId 重建 AAD，防止跨租戶密文搬移
  const aad = Buffer.from(`v=${env.v};tenant=${expectedTenantId}`, 'utf8');
  const decipher = crypto.createDecipheriv('aes-256-gcm', key, iv);
  decipher.setAAD(aad);
  decipher.setAuthTag(tag);

  const pt = Buffer.concat([decipher.update(ct), decipher.final()]);
  return JSON.parse(pt.toString('utf8'));
}

// 2. 恆定時間 Webhook 簽章驗證 (固定 32-byte 摘要 + Double-HMAC 盲化)
export function verifyWebhookSignature(
  webhookSecret: Buffer,
  rawBody: Buffer,
  providedHexSig: string
): boolean {
  const expectedMac = crypto
    .createHmac('sha256', webhookSecret)
    .update(rawBody)
    .digest();

  // 驗證公開的 64-char hex 格式並轉為 32-byte Buffer
  const isHexFormat = typeof providedHexSig === 'string' && /^[0-9a-f]{64}$/i.test(providedHexSig);
  const providedBuf = isHexFormat
    ? Buffer.from(providedHexSig, 'hex')
    : Buffer.alloc(32);

  // Double-HMAC：以隨機盲化金鑰將雙方映射為等長 32-byte 摘要後再交由 timingSafeEqual 比對
  const blindKey = crypto.randomBytes(32);
  const hExpected = crypto.createHmac('sha256', blindKey).update(expectedMac).digest();
  const hProvided = crypto.createHmac('sha256', blindKey).update(providedBuf).digest();

  return crypto.timingSafeEqual(hExpected, hProvided) && isHexFormat;
}
```

---

## 動手做

- **難度**：進階
- **預估時間**：60 分鐘

### 任務目標

1. **本地 Lab 1 — 寫一支 AES-CBC Padding Oracle 自動解密器**：
   - 在本機用 Python 建一個模擬 NexusPay 舊版加密 Cookie 的 Padding Oracle 函式（解密後檢查 PKCS#7 填充，填充對就回 `True`，填充錯就回 `False`）。
   - 寫出攻擊腳本，在完全不碰金鑰變數的前提下，把一整段多區塊密文逐位元組解開，並印出實際查詢次數，看看是不是真的落在理論平均值（每區塊約 `2,048` 次）附近。
2. **本地 Lab 2 — 實測 AES-GCM `96-bit` Nonce 重用與 Tag 偽造**：
   - 用 Python `cryptography` 套件的 `AESGCM`，拿同一把金鑰跟同一個 `96-bit` Nonce 加密兩段等長的 JSON 明文，先驗證 `C1 ⊕ C2 = P1 ⊕ P2`。
   - 接著寫幾行 `GF(2^128)` 有限體乘法與求反元素，從 `(C1, T1)` 跟 `(C2, T2)` 算出內部的 GHASH 驗證金鑰 `H`，再把明文偷換成管理員權限的 `{"role":"super"}`，算出偽造密文與偽造 Tag，最後丟進 `AESGCM.decrypt()` 驗證它真的能一舉過關！
3. **外部靶場檢查點（Cryptopals Set 2–3 經典題目）**：
   - **Set 2 Challenge 10 / 11 / 12**（手寫 CBC 與 ECB/CBC 偵測）：試著只用 ECB 原語自己兜出 CBC 加解密，體會為什麼 ECB 沒用 IV、遇到重複的 `16-byte` 明文永遠會吐出相同的密文區塊。
   - **Set 2 Challenge 13**（ECB Cut-and-Paste 剪貼攻擊）：體驗怎麼靠調整帳號長度，把 `role=admin` 剛好擠到獨立的一個 `16-byte` 區塊，再像剪貼積木一樣拼出管理員密文；順便對照本章為什麼一再強調要用 AEAD 的 Tag 與 AAD 鎖死上下文。
   - **Set 3 Challenge 17**（The CBC Padding Oracle）：親手處理我們在正文講過的「最後一個位元組歧義問題」——當倒數第二格剛好是 `0x02` 時，為什麼猜末位元組會有兩個值（分別湊出 `0x01` 與 `0x02 0x02`）都能通過檢查？驗證看看把 `C'_{i-1}[14] ^= 0x01` 翻轉一下是不是就能瞬間抓出真正的 `0x01`。
   - **Set 3 Challenge 22 / 23**（MT19937 PRNG 狀態複製）：練習從輸出反推 Mersenne Twister 的內部狀態，再回來對比 V8 `xorshift128+` 只有 `128 bits` 線性狀態時為什麼更容易被算穿。

### 參考解答

下面這支完整的 Python 腳本（跑之前先裝好套件：`pip install cryptography`）把 Lab 1 的 Padding Oracle 自動解密跟 Lab 2 的 GCM Nonce 重用偽造一次跑通：

```python
#!/usr/bin/env python3
import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import padding as sym_padding

# =====================================================================
# Lab 1: AES-CBC Padding Oracle 逐位元組解密實戰
# =====================================================================
SECRET_CBC_KEY = os.urandom(32)


def cbc_encrypt(plaintext: bytes) -> bytes:
    iv = os.urandom(16)
    padder = sym_padding.PKCS7(128).padder()
    padded = padder.update(plaintext) + padder.finalize()
    enc = Cipher(algorithms.AES(SECRET_CBC_KEY), modes.CBC(iv)).encryptor()
    return iv + enc.update(padded) + enc.finalize()


def padding_oracle(ciphertext: bytes) -> bool:
    """模擬錯誤設計的伺服器：僅回傳 PKCS#7 填充是否合法 (1-bit Oracle)。"""
    iv, ct = ciphertext[:16], ciphertext[16:]
    dec = Cipher(algorithms.AES(SECRET_CBC_KEY), modes.CBC(iv)).decryptor()
    raw = dec.update(ct) + dec.finalize()
    unpadder = sym_padding.PKCS7(128).unpadder()
    try:
        unpadder.update(raw) + unpadder.finalize()
        return True
    except ValueError:
        return False


def exploit_cbc_padding_oracle(ciphertext: bytes) -> tuple[bytes, int]:
    blocks = [ciphertext[i : i + 16] for i in range(0, len(ciphertext), 16)]
    recovered_plaintext = bytearray()
    queries = 0

    for blk_idx in range(1, len(blocks)):
        c_prev = blocks[blk_idx - 1]
        c_curr = blocks[blk_idx]
        intermediate = bytearray(16)

        for pos in range(15, -1, -1):
            pad_val = 16 - pos
            prefix = bytearray(16)
            for k in range(pos + 1, 16):
                prefix[k] = intermediate[k] ^ pad_val

            found = False
            for guess in range(256):
                prefix[pos] = guess
                queries += 1
                if padding_oracle(bytes(prefix) + c_curr):
                    # 排除 pos == 15 時原始明文恰好以 0x02 0x02 等長填充結尾的誤判
                    if pos == 15:
                        verify_buf = bytearray(prefix)
                        verify_buf[14] ^= 0x01
                        queries += 1
                        if not padding_oracle(bytes(verify_buf) + c_curr):
                            continue
                    intermediate[pos] = guess ^ pad_val
                    found = True
                    break
            assert found, f"Failed at block {blk_idx}, pos {pos}"

        plain_block = bytes(a ^ b for a, b in zip(intermediate, c_prev))
        recovered_plaintext.extend(plain_block)

    # 去除最終 PKCS#7 填充
    pad_len = recovered_plaintext[-1]
    return bytes(recovered_plaintext[:-pad_len]), queries


# =====================================================================
# Lab 2: AES-GCM 96-bit Nonce 重用 -> 還原 H 並偽造 Tag
# =====================================================================
GF_R = 0xE1000000000000000000000000000000


def gf_mul(x: int, y: int) -> int:
    z, v = 0, y
    for i in range(128):
        if (x >> (127 - i)) & 1:
            z ^= v
        lsb = v & 1
        v >>= 1
        if lsb:
            v ^= GF_R
    return z


def gf_pow(x: int, e: int) -> int:
    res = 1 << 127  # GF(2^128) GCM 位元序中的單位元 1
    base = x
    while e > 0:
        if e & 1:
            res = gf_mul(res, base)
        base = gf_mul(base, base)
        e >>= 1
    return res


def gf_inv(x: int) -> int:
    return gf_pow(x, (1 << 128) - 2)


def run_labs() -> None:
    # 驗證 Lab 1
    secret_msg = b'{"tenant":"nexus","role":"merchant_admin"}'
    ct = cbc_encrypt(secret_msg)
    decrypted, total_q = exploit_cbc_padding_oracle(ct)
    num_blocks = (len(ct) // 16) - 1
    print(f"[Lab 1] 解密結果: {decrypted.decode()}")
    print(f"[Lab 1] 區塊數: {num_blocks}, 總查詢數: {total_q} (平均每塊 {total_q / num_blocks:.1f} 次)")
    assert decrypted == secret_msg

    # 驗證 Lab 2
    gcm_key = bytes.fromhex("00112233445566778899aabbccddeeff")
    reused_nonce = bytes.fromhex("a1b2c3d4e5f60718293a4b5c")
    p1 = b'{"role":"guest"}'
    p2 = b'{"role":"admin"}'

    aesgcm = AESGCM(gcm_key)
    out1 = aesgcm.encrypt(reused_nonce, p1, b"")
    out2 = aesgcm.encrypt(reused_nonce, p2, b"")
    c1, t1 = out1[:16], out1[16:]
    c2, t2 = out2[:16], out2[16:]

    dc = int.from_bytes(bytes(a ^ b for a, b in zip(c1, c2)), "big")
    dt = int.from_bytes(bytes(a ^ b for a, b in zip(t1, t2)), "big")
    h2 = gf_mul(dt, gf_inv(dc))
    h_rec = gf_pow(h2, 1 << 127)
    print(f"[Lab 2] 還原 GHASH 金鑰 H: {h_rec.to_bytes(16, 'big').hex()}")

    # 偽造 {"role":"super"} 的密文與 Tag
    p_forged = b'{"role":"super"}'
    keystream = bytes(a ^ b for a, b in zip(c1, p1))
    c_forged = bytes(a ^ b for a, b in zip(p_forged, keystream))
    dc_forge = int.from_bytes(bytes(a ^ b for a, b in zip(c_forged, c1)), "big")
    t_forged_int = int.from_bytes(t1, "big") ^ gf_mul(dc_forge, h2)
    t_forged = t_forged_int.to_bytes(16, "big")

    verified_plain = aesgcm.decrypt(reused_nonce, c_forged + t_forged, b"")
    print(f"[Lab 2] 伺服器驗證偽造封包成功，解密明文: {verified_plain.decode()}")
    assert verified_plain == p_forged


if __name__ == "__main__":
    run_labs()
```

跑完這支腳本，你會看到 Lab 1 每解開一個區塊的平均查詢次數穩穩落在理論期望值（主要試探期望 `2,056` 次，約 `2,048` 次／區塊，加上末位元組確認請求的總期望約 `2,057` 次）附近，完全沒讀金鑰就把整串 JSON 還原出來；而 Lab 2 只靠兩筆撞了 Nonce 的 `(C1, T1)` 與 `(C2, T2)` 就直接解出 `H = fde4fbae4a09e020eff722969f83832b`，並成功把 `{"role":"super"}` 偽造成能通過 `AESGCM.decrypt()` 驗證的合法密文。

---

## 自我檢核

- **難度**：入門至進階
- **預估時間**：20 分鐘

1. 在 AES-CBC Padding Oracle 攻擊裡，如果目標是一段包含 `5` 個密文區塊（不含最前面的 IV，共 `80 bytes`）的加密憑證，只算主要試探的話，理論上最壞跟平均各要打多少次 Oracle 查詢？另外，若攻擊者想利用 **CBC-R** 將最後一塊明文 `P_5` 偽造成任意指定的 `16-byte` 目標明文 `P_target`，在已經透過 Oracle 解出 `C_5` 中間狀態 `I_5 = D_K(C_5)` 的前提下，應該如何構造前一個密文區塊 `C'_4`？
2. 某個跑在 Kubernetes 上的微服務，在 Pod 啟動時把 `AES-256-GCM` 的 `96-bit` Nonce 計數器設為 `1`，之後每加密一筆資料就加 `1`。當這支服務橫向擴容成 `4` 個 Pod、或是某個 Pod 重啟時，為什麼會釀成嚴重的資安事故？若改用作業系統 CSPRNG 隨機產生 `96-bit` Nonce，根據 NIST SP 800-38D 規範，同一把金鑰下的總加密次數上限是多少？超過時該如何設計金鑰派生架構？
3. 為什麼直接寫 `crypto.timingSafeEqual(Buffer.from(userSig), Buffer.from(expectedSig))` 還是可能出事？在實務上該怎麼結合格式檢查與雙重 HMAC（Double-HMAC）來做安全比對？
4. 有工程師覺得 `Math.random()` 直接拿來當重設密碼 Token 太容易看出規律，於是把它套了一層 `SHA-256` 雜湊（寫成 `sha256(Math.random().toString())`）。請問這樣修補安全嗎？另外，當 NexusPay（`RS256` JWT 有效期 `900 s`、JWKS 快取 TTL `300 s`）要執行簽章金鑰輪換時，新公鑰上架、切換簽發私鑰與撤除舊公鑰之間分別至少要間隔多少秒，才不會發生驗簽斷線或舊鑰留存過久？

### 參考解答

1. 只算主要試探時，解開 `5` 個 `16-byte` 區塊在最壞情況下需要 `5 × 16 × 256 = 20,480` 次查詢；在均勻分布假設下，主要試探的精確離散期望值是 `5 × 16 × 128.5 = 10,280` 次（工程上用每字節 `128` 次估算則是 `5 × 2,048 = 10,240` 次；加計第 15 位元組排除歧義的確認請求後，總期望約為 `5 × 2,057.002 = 10,285` 次）。若要用 CBC-R 將最後一塊明文偽造成 `P_target`，因為 CBC 解密公式為 `P'_5 = D_K(C_5) ⊕ C'_4 = I_5 ⊕ C'_4`，攻擊者只需直接令 **`C'_4 = I_5 ⊕ P_target`**，伺服器解開 `C'_4 || C_5` 時就會在最後一塊精準吐出 `P_target`。
2. 只要這 `4` 個 Pod 與重啟後的 Pod 共用同一把 AES-GCM 金鑰，且 `96-bit` Nonce 都從 `1` 開始遞增，不同 Pod 就會拿**同一組 `(K, N)`** 加密不同明文。攻擊者把兩筆撞號密文做 XOR 就能消去金鑰流算出 `P1 ⊕ P2`，並透過 Forbidden Attack 在 `GF(2^128)` 上解出 GHASH 金鑰 `H` 偽造任意認證標籤。若改用 CSPRNG 隨機產生 `96-bit` Nonce，NIST SP 800-38D 規定單一金鑰的總調用上限為 **`2^32` 次**（將碰撞機率壓在 `2^{-32}` 以下）；高吞吐量系統應為每筆請求或每個 Pod 產生 `128-bit` 隨機 Salt，先用 HKDF 派生出獨立子金鑰再加密。
3. 當使用者傳進來的 `userSig` 與 `expectedSig` 位元組長度不同時，`crypto.timingSafeEqual` 會直接拋出 `RangeError` 例外，不僅可能讓請求崩潰，也直接洩漏了簽章的真實長度。面對固定 `32 bytes` 的 Webhook HMAC-SHA256，應先驗證輸入是否為 64 字元 hex 字串並解碼成 `32 bytes` Buffer（格式不符就拿 `32 bytes` 全零 Buffer 代打，最後回傳時再與格式檢查結果做邏輯 AND），接著用現場隨機產生的 `32-byte` 盲化金鑰分別對兩邊再算一次 HMAC-SHA256，把雙方都映射成固定 `32 bytes` 摘要後再交給 `timingSafeEqual`。
4. **套 `SHA-256` 完全不安全**。單向雜湊不會增加亂數的熵（Entropy）；攻擊者只要從公開處（如請求流水號）收集連續 4 到 5 筆未雜湊的 `Math.random()` 輸出，使 `GF(2)` 線性約束達到滿秩 `128`，就能用 Z3 還原 V8 `xorshift128+` 的 `128-bit` 內部狀態 `(state0, state1)`，推算出重設密碼當下的浮點數再自己套一次 `SHA-256`。至於 NexusPay 的 JWT 金鑰輪換：新公鑰掛上 JWKS 後，必須先等 **`> 300 s`**（超過 JWKS 快取 TTL）確保所有節點都拿到新公鑰，才能把簽發端切換成新私鑰；切換後還必須再等 **`> 900 s`**（超過舊 JWT 有效期）確保舊私鑰簽出的 Token 全數自然過期，才能將舊公鑰從 JWKS 撤除。

---

## 延伸閱讀

- **NIST SP 800-38D**：*Recommendation for Block Cipher Modes of Operation: Galois/Counter Mode (GCM) and GMAC*（官方標準，定義了 `128-bit` 區塊、`96-bit` Nonce 與單一金鑰的加密次數上限）。
- **Antoine Joux (2006)**：*Authentication Failures in NIST version of GCM*（Forbidden Attack 的原始論文，完整推導了 Nonce 重用時怎麼在 `GF(2^128)` 上解出驗證金鑰 `H`）。
- **The Cryptopals Crypto Challenges (Set 2 & Set 3)**：動手寫程式練熟 ECB/CBC 判別、CBC Padding Oracle 與 PRNG 狀態複製的最佳實戰題庫（https://cryptopals.com/）。
- **V8 官方部落格**：*There's Math.random(), and then there's Math.random()*（講解 V8 引擎改用 `xorshift128+` 的來龍去脈與為什麼它不能拿來做資安用途）。
- **Node.js `crypto` 官方文件**：查閱 `crypto.timingSafeEqual` 與 `crypto.createCipheriv` 在處理 AEAD AAD 與認證標籤時的詳細規範。
