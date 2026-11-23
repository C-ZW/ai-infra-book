# 外部事實與時效基準（Source Evidence — ch13-deserialization-and-nodejs-runtime）

本文件記錄《邊界失守》[第 13 章 反序列化、原型鏈汙染與 Node.js 執行時期漏洞] 涉及之 2025/2026 時效性標準、工具版本與外部事實參照（依據 `_meta/landscape-2026-11.md`），供寫作與 Tier-2 審核校驗使用。

## 本章特定事實與審查要點

本章 Node.js 原型鏈汙染與 V8 執行時期記憶體隔離參照 Chromium V8 Sandbox（Ubercage 1 TB 連續虛擬位址空間與指標壓縮）現況。

## 關聯標準與事實摘錄（Landscape 2026-11）

- **V8 Sandbox（Ubercage）**：在現代 Chromium 與 V8 執行時期已成生產級隔離邊界。保留 1 TB 連續虛擬位址空間，沙箱內指標壓縮為相對於基底的 32 位元偏移，並將程式碼指標移出 JS 物件改以間接表索引，迫使攻擊者必須額外尋找沙箱逃逸原語。⚠️ 實作細節隨 V8 版本持續收緊。
  - 來源：V8 官方部落格（https://v8.dev/blog/sandbox）

- **Web / API 實驗基準**：PortSwigger Web Security Academy（免費且涵蓋 HTTP Smuggling、Race Condition、OAuth 等現代議題）。
  - 來源：PortSwigger Research（https://portswigger.net/research）
