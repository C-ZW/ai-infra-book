# 維護手冊（Maintenance）—《邊界失守》

## 1. 跨章一致性基準表（Base-Numbers Table）

> 本表由 `_meta/outline.md` 原樣同步，須與 `outline.md` 及 `_meta/running-examples.md` 維持**位元組完全一致**。修改任一常數時，必須先改 `outline.md` 再同步至本表與所有引用章節。

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

## 2. 脆弱事實索引（Fragile Facts — 來自 `landscape-2026-11.md`）

- ⚠️ **OWASP API Security Top 10:2023**：留意 2027 年是否釋出新版。
- ⚠️ **MITRE CWE Top 25（2025 版）**：每年底隨最新 CVE 資料集更新排名。
- ⚠️ **NVD CVSS v4.0 富化覆蓋率**：隨 NIST 流程與 KEV 優先策略動態變化。
- ⚠️ **V8 Sandbox（Ubercage）與 Linux `io_uring`/eBPF 預設政策**：隨 V8 與發行版核心版本持續收緊。
- ⚠️ **AI 輔助審計工具生態與資安證照費用（Ch37）**：價格與考制須標註日期並定期覆核。

## 3. 掃描協定（Scan Protocol）

1. 重讀 `landscape-2026-11.md` 所有 `⚠️` 條目並透過兩個獨立一手來源覆核。
2. 若基準常數有變動：先編輯 `outline.md` 基準表 → 原子覆寫 `running-examples.md` 與本檔第 1 節 → 同步更新所有引用章節。
3. 執行確定性閘門：`python3 tools/md-reader/gate_book.py books/vuln-hunting/book-src --lang zh-TW --config books/vuln-hunting/book-src/_meta/lint.config.json` 與 `python3 tools/md-reader/check_diagrams.py books/vuln-hunting/book-src`。
4. 若修改載重推導，重跑跨模型審查（`books/vuln-hunting/book-src/_meta/run_sol62_review.py`）。
5. 重新打包書架與閱讀器：`python3 tools/md-reader/build_shelf.py && python3 tools/md-reader/build_reader.py books/vuln-hunting/web/book.config.json`。
6. 於下方掃描日誌補記一行。

## 4. 橋接登記鎖定（Bridge Registry Lock）

- `ch01`: 資料庫 ACID 不變量 → 安全不變量（`pass`）
- `ch02`: 系統效能 Profiling → 攻擊面測繪與 Source-to-Sink 追蹤（`pass`）
- `ch03`: 分散式前後端序列化 Schema 漂移 → HTTP 解析器分歧（`pass`）
- `ch04`: 分散式快取一致性與過期視窗 → Token / JWKS 驗證與撤銷失效（`pass`）
- `ch06`: PostgreSQL RLS → 物件層級授權（BOLA）邊界（`pass`）
- `ch07`: RPC/GraphQL Resolver 執行樹 → 非 REST 查詢複雜度與授權破口（`pass`）
- `ch08`: AST 編譯階段與字串模板拼接 → 資料平面與控制平面混同（`pass`）
- `ch10`: 瀏覽器 Origin 隔離與容器命名空間隔離結構邊界對照（`pass`）
- `ch11`: CDN/Nginx 快取鍵設計 → Web Cache Poisoning Unkeyed Input（`pass`）
- `ch12`: 資料庫 Isolation Level 與樂觀鎖 → TOCTOU 與單封包雙花攻擊（`pass`）
- `ch17`: Linux 行程模型與容器 `chroot`/Namespace → 核心隔離逃逸邊界（`pass`）
- `ch19`: CI/CD 建置管線 DAG → 供應鏈信任傳遞與投毒點（`pass`）
- `ch20`: 作業系統虛擬記憶體頁表 → ELF 與 64 位元行程位址空間（`pass`）
- `ch05, ch09, ch13–ch16, ch18, ch21–ch27, ch28–ch37`: `none`（`pass`）

## 5. 掃描與建置日誌（Scan Log）

- `2026-11-21`：初版建置（full pipeline）。完稿 30 章（`ch01`–`ch21`、`ch25`、`ch28`–`ch32`、`ch34`、`ch36`、`ch37`）＋ 4 份附錄（A–D）；7 章標記為 `unfinished`（`ch22, ch23, ch24, ch26, ch27, ch33, ch35`）。Tier-1 lint / diagrams 0 errors；P4 完成 Round-1（`codex gpt-6.2-sol low` + `ch16` `argon-low` fallback）全 30 章裁決修復與 Bridging Review 全數 `pass`，並完成 Round-2（`codex gpt-6.2-sol medium` 30/30 全數掃描，`ch01`–`ch10`、`ch21`、`ch25`、`ch28`–`ch37` 共 20 章完成第二輪修復；`ch11`–`ch20` 保留 Round-2 報告待後續額度恢復時補修）。
- `2026-11-21`：完整 37 章版建置。補齊並完稿 `ch22`、`ch23`、`ch24`、`ch26`、`ch27`、`ch33`（含開源／外部站點／公司內部三情境漏洞回報 SOP 與提交資料／法律紅線檢查清單）、`ch35`，同步更新附錄 A 索引。全 37 章完成 Round-2 跨模型審查（36 章 `codex gpt-6.2-sol medium`、`ch27` `agy gemini-4-argon-low` fallback）與全數裁決修復；Tier-1 `gate_book.py` 與 `check_diagrams.py` 全數通過（0 errors）。
