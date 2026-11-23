# 外部事實與時效基準（Source Evidence — ch28-static-and-variant-analysis）

本文件記錄《邊界失守》[第 28 章：靜態分析、變體分析與自動化規則工程] 涉及之 2025/2026 時效性標準、工具版本與外部事實參照（依據 `_meta/landscape-2026-11.md`），供寫作與 Tier-2 審核校驗使用。

## 本章特定事實與審查要點

本章跨檔案語義資料流分析以 CodeQL 全域 TaintTracking 與 Semgrep 語法樹比對為具體工程實作基準。

## 關聯標準與事實摘錄（Landscape 2026-11）

- **MITRE CWE Top 25（2025 版，沿用至 2026）**：基於近 40,000 筆 CVE 統計；前三名為 CWE-79（XSS）、CWE-89（SQLi）、CWE-352（CSRF），CWE-862（Missing Authorization）躍升至第 4；記憶體安全（CWE-787 Out-of-bounds Write）與命令注入（CWE-78）與 CISA KEV 高度重疊。⚠️ 2026 年度榜單預計年底更新。
  - 來源：MITRE CWE Top 25（https://cwe.mitre.org/top25/）與 CISA Secure by Design 指引（https://www.cisa.gov/）

- **靜態與變體分析**：**CodeQL**（跨檔案語意資料流與變體分析主力）、**Semgrep**（輕量語法樹規則與 CI/pre-commit 防線）。
  - 來源：GitHub Security Lab 與 Semgrep 官方文件
