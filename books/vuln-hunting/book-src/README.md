# 邊界失守：從後端系統到獨立漏洞挖掘與資安工程

本書面向具備多年後端系統開發經驗的工程師，從「安全不變量違背」出發，貫穿虛構多租戶即時結算與 API 閘道平台 **NexusPay**，系統化建立獨立漏洞挖掘與資安工程（AppSec / Product Security / Vulnerability Research）能力。

## 閱讀與實作路線

1. **一鍵啟動本地靶機**：進入 `books/vuln-hunting/labs/`，執行 `./setup.sh up` 啟動核心環境（Nginx `:8080`、Node.js 22 API `:3000`、PostgreSQL 16 `:5432`、Redis 7 `:6379`）；Part IV–V 原生二進位與 Fuzzing 實驗執行 `./setup.sh up-bin && ./setup.sh shell-bin`（完整索引見附錄 A）。
2. **結構設計**：每章固定包含六節——「從你已知的出發」、「機制與推導（首節即交代攻擊者目標與實質影響）」、「故障模式與防禦」、「動手做（含難度、預估時間、參考解答與 PortSwigger / pwn.college 檢查點）」、「自我檢核」與「延伸閱讀」。
3. **版本狀態（2026-11）**：
   - 全書 **37 章正文**（`ch01`–`ch37`）＋ **4 份附錄（附錄 A–D）** 全數完稿，通過 Tier-1 契約與圖表檢查，以及兩輪跨模型審查（`codex gpt-6.2-sol low` 與 `medium`）裁決與修復。
