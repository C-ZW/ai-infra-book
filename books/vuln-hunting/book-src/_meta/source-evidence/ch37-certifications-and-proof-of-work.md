# 外部事實與時效基準（Source Evidence — ch37-certifications-and-proof-of-work）

本文件記錄《邊界失守》[第 37 章：資安證照 ROI 評析與可驗證的能力證明體系] 涉及之 2025/2026 時效性標準、工具版本與外部事實參照（依據 `_meta/landscape-2026-11.md`），供寫作與 Tier-2 審核校驗使用。

## 本章特定事實與審查要點

本章資安證照評析（OSCP/OSEP/CRTP）與 Proof of Work（CVE/GHSA/開源 Fuzzer）對齊實戰操作型能力認證現況。

## 關聯標準與事實摘錄（Landscape 2026-11）

- **CVSS v4.0 + EPSS + CISA KEV**：FIRST 於 2023-11 發布 CVSS v4.0，引入 Attack Requirements（AT）並拆分 Vulnerable / Subsequent System 影響；截至 2026 年業界處於 v3.1 與 v4.0 並存過渡期（NVD 因 CVE 暴增改採優先富化策略），實務漏洞優先序普遍結合 **CVSS v4.0 + EPSS（Exploit Prediction Scoring System）+ CISA KEV**。⚠️ NVD 富化覆蓋率持續變動。
  - 來源：FIRST CVSS v4.0 規範（https://www.first.org/cvss/v4.0/specification-document）、NIST NVD（https://nvd.nist.gov/）

- **Web / API 實驗基準**：PortSwigger Web Security Academy（免費且涵蓋 HTTP Smuggling、Race Condition、OAuth 等現代議題）。
  - 來源：PortSwigger Research（https://portswigger.net/research）

- **Binary / Systems 實驗基準**：pwn.college（亞利桑那州立大學開源系統安全實戰平台）。
  - 來源：pwn.college（https://pwn.college/）

- **真實目標與協調揭露基準**：HackerOne、Bugcrowd、Intigriti、GitHub Security Advisories（GHSA）與 MITRE CNA 協調揭露流程。⚠️ 平台獎金中位數與政策隨時調整，書中引用時標註日期。
  - 來源：MITRE CVE / CNA 指引與各大漏洞賞金平台
