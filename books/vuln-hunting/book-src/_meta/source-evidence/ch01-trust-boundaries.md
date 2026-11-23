# 外部事實與時效基準（Source Evidence — ch01-trust-boundaries）

本文件記錄《邊界失守》[第 1 章：信任邊界、攻擊面與漏洞的形式化模型] 涉及之 2025/2026 時效性標準、工具版本與外部事實參照（依據 `_meta/landscape-2026-11.md`），供寫作與 Tier-2 審核校驗使用。

## 本章特定事實與審查要點

本章形式化漏洞模型（狀態機不變量違背）與 NexusPay 四層架構邊界，對齊 OWASP Top 10:2025 與 MITRE CWE Top 25 基礎分類。

## 關聯標準與事實摘錄（Landscape 2026-11）

- **OWASP Top 10:2025**（2025 年底釋出、2026 年初正式定版）：A01 仍為 Broken Access Control（已併入 SSRF）、A02 Security Misconfiguration、A03 Software Supply Chain Failures、A10 新增 Mishandling of Exceptional Conditions。
  - 來源：OWASP Top 10 專案頁（https://owasp.org/Top10/）

- **MITRE CWE Top 25（2025 版，沿用至 2026）**：基於近 40,000 筆 CVE 統計；前三名為 CWE-79（XSS）、CWE-89（SQLi）、CWE-352（CSRF），CWE-862（Missing Authorization）躍升至第 4；記憶體安全（CWE-787 Out-of-bounds Write）與命令注入（CWE-78）與 CISA KEV 高度重疊。⚠️ 2026 年度榜單預計年底更新。
  - 來源：MITRE CWE Top 25（https://cwe.mitre.org/top25/）與 CISA Secure by Design 指引（https://www.cisa.gov/）

- **Web / API 實驗基準**：PortSwigger Web Security Academy（免費且涵蓋 HTTP Smuggling、Race Condition、OAuth 等現代議題）。
  - 來源：PortSwigger Research（https://portswigger.net/research）
