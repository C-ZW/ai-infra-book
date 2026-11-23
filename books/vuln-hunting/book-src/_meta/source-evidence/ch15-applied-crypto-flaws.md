# 外部事實與時效基準（Source Evidence — ch15-applied-crypto-flaws）

本文件記錄《邊界失守》[第 15 章 應用層密碼學破口與金鑰生命週期] 涉及之 2025/2026 時效性標準、工具版本與外部事實參照（依據 `_meta/landscape-2026-11.md`），供寫作與 Tier-2 審核校驗使用。

## 本章特定事實與審查要點

本章密碼學破口涵蓋 PKCS#7 Padding Oracle、ECB 模式區塊重組與金鑰管理生命週期，對齊 NIST SP 800-38A 標準。

## 關聯標準與事實摘錄（Landscape 2026-11）

- **MITRE CWE Top 25（2025 版，沿用至 2026）**：基於近 40,000 筆 CVE 統計；前三名為 CWE-79（XSS）、CWE-89（SQLi）、CWE-352（CSRF），CWE-862（Missing Authorization）躍升至第 4；記憶體安全（CWE-787 Out-of-bounds Write）與命令注入（CWE-78）與 CISA KEV 高度重疊。⚠️ 2026 年度榜單預計年底更新。
  - 來源：MITRE CWE Top 25（https://cwe.mitre.org/top25/）與 CISA Secure by Design 指引（https://www.cisa.gov/）

- **Web / API 實驗基準**：PortSwigger Web Security Academy（免費且涵蓋 HTTP Smuggling、Race Condition、OAuth 等現代議題）。
  - 來源：PortSwigger Research（https://portswigger.net/research）
