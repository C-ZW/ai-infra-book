# 全書基準數字表（Base-Numbers Table）

> 本檔由 `_meta/outline.md` 之基準數字表原樣生成，供 Tier-2 跨模型驗證器作為單一事實基準。**禁止手動編輯本檔**；任何修改須先改 `outline.md` 再同步覆寫。

| 基準常數 | 數值與單位 | 所屬概念（NexusPay / 系統模型） | 引用章節 |
|---|---|---|---|
| NexusPay 閘道請求逾時 | `30 s`（Nginx `proxy_read_timeout`），Node.js `keepAliveTimeout = 5 s` | 反向代理與後端連線生命週期邊界 | Ch01, Ch03, Ch11, Ch12, Ch14 |
| NexusPay 帳戶餘額與併發規格 | 單戶測試餘額 `10,000`（整數分，即 `$100.00`）；單次提領上限 `10,000`；併發尖峰 `2,000 req/s` | 多租戶帳本不變量與競爭條件雙花分析 | Ch01, Ch06, Ch08, Ch12, Ch35 |
| JWT Access Token 規格 | RS256（2048-bit RSA），有效期 `900 s`（15 分鐘）；JWKS 快取 TTL `300 s` | 身分驗證與金鑰輪換邊界 | Ch04, Ch05, Ch06, Ch15 |
| GraphQL 查詢深度與批次上限 | 預設巢狀深度上限 `8` 層；單次 Batch 請求上限 `20` 個操作 | 非 REST API 資源耗盡與授權繞過邊界 | Ch07, Ch14 |
| 單封包併發視窗（HTTP/2） | 同連線最後 1 位元組同步送達 `20` 個請求，伺服器端到達抖動 `< 1 ms` | Single-Packet Attack 與 TOCTOU 視窗量化 | Ch03, Ch12, Ch35 |
| 64 位元 x86_64 堆疊與堆積對齊 | 指標寬度 `8 bytes`；Stack / `ptmalloc2` chunk 最小對齊 `16 bytes`；最小可用 chunk 大小 `32 bytes`（`0x20`） | 二進位記憶體佈局與堆積利用 | Ch20, Ch22, Ch23, Ch24, Ch25 |
| Linux x86_64 ASLR 熵位元數 | 使用者空間 `mmap` / 堆積典型隨機化 `28 bits`（頁大小 `4 KiB = 4,096 bytes`，`12 bits` 頁內偏移固定） | 記憶體隨機化暴力猜測成本與資訊洩漏必要性 | Ch20, Ch22, Ch23, Ch27 |
| `ptmalloc2` tcache 容量與 Safe-Linking | 每條 tcache bin 上限 `7` 個 chunk（涵蓋 `0x20`–`0x410` 共 `64` bins）；Safe-Linking 掩碼為 `(pos >> 12) ^ ptr` | glibc 現代堆積緩解與繞過推導 | Ch23, Ch24, Ch25 |
| `libnexus-parse` TLV 封包規格 | 檔頭固定 `8 bytes`（`magic: 2B`、`type: 2B`、`len: 4B` uint32）；合法 payload 上限 `65,536 bytes`（`64 KiB`） | Rust/C FFI 解析邊界、逆向與 Fuzzing 目標 | Ch20, Ch21, Ch25, Ch28, Ch29, Ch30 |
| V8 Sandbox（Ubercage）位址空間 | 保留 `1 TiB` 連續虛擬位址空間；內部壓縮指標為 `32 bits` 相對偏移 | 現代執行時期記憶體隔離邊界 | Ch13, Ch26 |
| Linux 核心除錯與 SLUB 基準 | x86_64 頁大小 `4 KiB`；SLUB 常見物件快取級距 `kmalloc-32` 至 `kmalloc-4096`（2 的冪次對齊） | 核心堆積噴灑與隔離邊界 | Ch17, Ch27 |
| AES-GCM 規格與 Nonce 限制 | 區塊大小 `128 bits`（`16 bytes`）；標準 Nonce `96 bits`（`12 bytes`）；同金鑰下 Nonce 重用立即洩漏 GHASH 驗證金鑰 `H` | 實務密碼學破口與認證加密邊界 | Ch04, Ch15 |
| AFL++ 覆蓋率位圖規格 | 預設邊緣覆蓋率 map 大小 `65,536 bytes`（`64 KiB`）；單核 Persistent Mode 基準吞吐 `5,000 exec/s` | 灰箱 Fuzzing 覆蓋率收斂與效能瓶頸 | Ch29, Ch30, Ch31 |
| 漏洞修復與分流門檻 | 高危 SLA `7 天`、嚴重 SLA `24 小時`；CVSS v4.0 搭配 EPSS `≥ 0.1` 或列入 CISA KEV 視為立即處置 | 漏洞揭露、嚴重度評定與 AppSec 治理 | Ch33, Ch34, Ch35, Ch36 |
