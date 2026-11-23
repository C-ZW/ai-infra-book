# 外部事實與時效基準（Source Evidence — ch11-ssrf-parsers-and-cache）

本文件記錄《邊界失守》[第 11 章：SSRF、URL Parser 混淆與 Web Cache Poisoning / Deception] 涉及之 2025/2026 時效性標準、工具版本與外部事實參照（依據 `_meta/landscape-2026-11.md`），供寫作與 Tier-2 審核校驗使用。

## 本章特定事實與審查要點

本章聚焦 OWASP Top 10:2025 A01 整合之 SSRF、RFC 3986 與 WHATWG URL 解析分歧，以及 Web Cache Poisoning 實務邊界。

## 關聯標準與事實摘錄（Landscape 2026-11）

- **OWASP Top 10:2025**（2025 年底釋出、2026 年初正式定版）：A01 仍為 Broken Access Control（已併入 SSRF）、A02 Security Misconfiguration、A03 Software Supply Chain Failures、A10 新增 Mishandling of Exceptional Conditions。
  - 來源：OWASP Top 10 專案頁（https://owasp.org/Top10/）

- **OWASP API Security Top 10:2023**：截至 2026 年底仍為最新正式版（API1 BOLA、API2 Broken Authentication、API3 BOPLA、API4 Unrestricted Resource Consumption、API5 BFLA、API6 Sensitive Business Flows、API7 SSRF、API8 Security Misconfiguration、API9 Improper Inventory Management、API10 Unsafe Consumption of APIs）。⚠️ 需留意 2027 年是否釋出新版。
  - 來源：OWASP API Security Project（https://owasp.org/API-Security/）

- **Web / API 實驗基準**：PortSwigger Web Security Academy（免費且涵蓋 HTTP Smuggling、Race Condition、OAuth 等現代議題）。
  - 來源：PortSwigger Research（https://portswigger.net/research）
