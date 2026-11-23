# 外部事實與時效基準（Source Evidence — ch18-cloud-iam-and-lateral-movement）

本文件記錄《邊界失守》[第 18 章：雲端 IAM、中繼資料服務與橫向移動] 涉及之 2025/2026 時效性標準、工具版本與外部事實參照（依據 `_meta/landscape-2026-11.md`），供寫作與 Tier-2 審核校驗使用。

## 本章特定事實與審查要點

本章詳細分析 AWS IMDSv1 與 IMDSv2 會話 Token 差異，以及雲端 IAM 權限圖評估與最小權限架構。

## 關聯標準與事實摘錄（Landscape 2026-11）

- **OWASP Top 10:2025**（2025 年底釋出、2026 年初正式定版）：A01 仍為 Broken Access Control（已併入 SSRF）、A02 Security Misconfiguration、A03 Software Supply Chain Failures、A10 新增 Mishandling of Exceptional Conditions。
  - 來源：OWASP Top 10 專案頁（https://owasp.org/Top10/）

- **真實目標與協調揭露基準**：HackerOne、Bugcrowd、Intigriti、GitHub Security Advisories（GHSA）與 MITRE CNA 協調揭露流程。⚠️ 平台獎金中位數與政策隨時調整，書中引用時標註日期。
  - 來源：MITRE CVE / CNA 指引與各大漏洞賞金平台
