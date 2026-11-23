# 外部事實與時效基準（Source Evidence — ch19-supply-chain-and-cicd）

本文件記錄《邊界失守》[第 19 章：軟體供應鏈與 CI/CD 管線攻防] 涉及之 2025/2026 時效性標準、工具版本與外部事實參照（依據 `_meta/landscape-2026-11.md`），供寫作與 Tier-2 審核校驗使用。

## 本章特定事實與審查要點

本章對齊 OWASP Top 10:2025 A03 Software Supply Chain Failures、Dependency Confusion 機制與 GitHub Actions pull_request_target 安全模型。

## 關聯標準與事實摘錄（Landscape 2026-11）

- **OWASP Top 10:2025**（2025 年底釋出、2026 年初正式定版）：A01 仍為 Broken Access Control（已併入 SSRF）、A02 Security Misconfiguration、A03 Software Supply Chain Failures、A10 新增 Mishandling of Exceptional Conditions。
  - 來源：OWASP Top 10 專案頁（https://owasp.org/Top10/）

- **AI 輔助審計與修補（2025–2026 趨勢）**：業界將 LLM/Agent 整合於 SAST 誤報分流、Fuzzer Harness 生成與 Crash 根因分析；同時歐盟 Cyber Resilience Act（CRA）等法規推動持續 Fuzzing 與供應鏈簽章成為交付門檻。⚠️ AI 審計工具生態快速演進。
  - 來源：GitHub Security Lab / OSS-Fuzz
