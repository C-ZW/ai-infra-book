# 外部事實與時效基準（Source Evidence — ch14-waf-and-defense-bypass）

本文件記錄《邊界失守》[第 14 章 防禦對抗與繞過技術（WAF、代理正規化與 Rate Limiting）] 涉及之 2025/2026 時效性標準、工具版本與外部事實參照（依據 `_meta/landscape-2026-11.md`），供寫作與 Tier-2 審核校驗使用。

## 本章特定事實與審查要點

本章分析 WAF 分塊編碼、Multipart 變異與 Unicode 規範化繞過，對照 OWASP ModSecurity Core Rule Set 最新防禦實踐。

## 關聯標準與事實摘錄（Landscape 2026-11）

- **OWASP Top 10:2025**（2025 年底釋出、2026 年初正式定版）：A01 仍為 Broken Access Control（已併入 SSRF）、A02 Security Misconfiguration、A03 Software Supply Chain Failures、A10 新增 Mishandling of Exceptional Conditions。
  - 來源：OWASP Top 10 專案頁（https://owasp.org/Top10/）

- **Web / API 實驗基準**：PortSwigger Web Security Academy（免費且涵蓋 HTTP Smuggling、Race Condition、OAuth 等現代議題）。
  - 來源：PortSwigger Research（https://portswigger.net/research）
