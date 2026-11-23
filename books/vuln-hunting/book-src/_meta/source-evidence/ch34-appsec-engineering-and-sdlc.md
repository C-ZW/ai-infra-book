# 外部事實與時效基準（Source Evidence — ch34-appsec-engineering-and-sdlc）

本文件記錄《邊界失守》[第 34 章：企業級 AppSec 工程與 SDLC 防線設計] 涉及之 2025/2026 時效性標準、工具版本與外部事實參照（依據 `_meta/landscape-2026-11.md`），供寫作與 Tier-2 審核校驗使用。

## 本章特定事實與審查要點

本章 AppSec 工程體系結合 CVSS v4.0 + EPSS + CISA KEV 二維排序、SCA 可達性分析與 CodeQL/Semgrep CI/CD 閘門。

## 關聯標準與事實摘錄（Landscape 2026-11）

- **OWASP Top 10:2025**（2025 年底釋出、2026 年初正式定版）：A01 仍為 Broken Access Control（已併入 SSRF）、A02 Security Misconfiguration、A03 Software Supply Chain Failures、A10 新增 Mishandling of Exceptional Conditions。
  - 來源：OWASP Top 10 專案頁（https://owasp.org/Top10/）

- **CVSS v4.0 + EPSS + CISA KEV**：FIRST 於 2023-11 發布 CVSS v4.0，引入 Attack Requirements（AT）並拆分 Vulnerable / Subsequent System 影響；截至 2026 年業界處於 v3.1 與 v4.0 並存過渡期（NVD 因 CVE 暴增改採優先富化策略），實務漏洞優先序普遍結合 **CVSS v4.0 + EPSS（Exploit Prediction Scoring System）+ CISA KEV**。⚠️ NVD 富化覆蓋率持續變動。
  - 來源：FIRST CVSS v4.0 規範（https://www.first.org/cvss/v4.0/specification-document）、NIST NVD（https://nvd.nist.gov/）

- **靜態與變體分析**：**CodeQL**（跨檔案語意資料流與變體分析主力）、**Semgrep**（輕量語法樹規則與 CI/pre-commit 防線）。
  - 來源：GitHub Security Lab 與 Semgrep 官方文件
