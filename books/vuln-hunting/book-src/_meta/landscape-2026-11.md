# 事實基準（Landscape — 2026-11）

本檔記錄本書涉及之時效性標準、工具版本、緩解機制現況與業界基線，作為撰寫與審核之單一外部事實參照。標註 `⚠️` 者為易變動項目，後續掃描須優先覆核。

## 1. 漏洞分類與評分標準

- **OWASP Top 10:2025**（2025 年底釋出、2026 年初正式定版）：A01 仍為 Broken Access Control（已併入 SSRF）、A02 Security Misconfiguration、A03 Software Supply Chain Failures、A10 新增 Mishandling of Exceptional Conditions。
  - 來源：OWASP Top 10 專案頁（https://owasp.org/Top10/）
- **OWASP API Security Top 10:2023**：截至 2026 年底仍為最新正式版（API1 BOLA、API2 Broken Authentication、API3 BOPLA、API4 Unrestricted Resource Consumption、API5 BFLA、API6 Sensitive Business Flows、API7 SSRF、API8 Security Misconfiguration、API9 Improper Inventory Management、API10 Unsafe Consumption of APIs）。⚠️ 需留意 2027 年是否釋出新版。
  - 來源：OWASP API Security Project（https://owasp.org/API-Security/）
- **MITRE CWE Top 25（2025 版，沿用至 2026）**：基於近 40,000 筆 CVE 統計；前三名為 CWE-79（XSS）、CWE-89（SQLi）、CWE-352（CSRF），CWE-862（Missing Authorization）躍升至第 4；記憶體安全（CWE-787 Out-of-bounds Write）與命令注入（CWE-78）與 CISA KEV 高度重疊。⚠️ 2026 年度榜單預計年底更新。
  - 來源：MITRE CWE Top 25（https://cwe.mitre.org/top25/）與 CISA Secure by Design 指引（https://www.cisa.gov/）
- **CVSS v4.0 + EPSS + CISA KEV**：FIRST 於 2023-11 發布 CVSS v4.0，引入 Attack Requirements（AT）並拆分 Vulnerable / Subsequent System 影響；截至 2026 年業界處於 v3.1 與 v4.0 並存過渡期（NVD 因 CVE 暴增改採優先富化策略），實務漏洞優先序普遍結合 **CVSS v4.0 + EPSS（Exploit Prediction Scoring System）+ CISA KEV**。⚠️ NVD 富化覆蓋率持續變動。
  - 來源：FIRST CVSS v4.0 規範（https://www.first.org/cvss/v4.0/specification-document）、NIST NVD（https://nvd.nist.gov/）

## 2. 系統、執行時期與底層緩解機制（2025–2026）

- **V8 Sandbox（Ubercage）**：在現代 Chromium 與 V8 執行時期已成生產級隔離邊界。保留 1 TB 連續虛擬位址空間，沙箱內指標壓縮為相對於基底的 32 位元偏移，並將程式碼指標移出 JS 物件改以間接表索引，迫使攻擊者必須額外尋找沙箱逃逸原語。⚠️ 實作細節隨 V8 版本持續收緊。
  - 來源：V8 官方部落格（https://v8.dev/blog/sandbox）
- **glibc `ptmalloc2`**：現代發行版預設啟用 Safe-Linking（tcache / fastbin 單向鏈結指標以 `pos >> 12` XOR 混淆）、Pointer Mangling、嚴格 alignment 與 double-free 檢查，傳統未洩漏堆積位址的單純覆寫已失效。
  - 來源：glibc 原始碼與安全公告
- **Linux `io_uring` 與 `eBPF`**：因共享環形緩衝區生命週期競爭與 UAF 歷史，多租戶環境常透過 `sysctl` 限制非特權 `io_uring`；eBPF 廣泛用於雲端原生安全觀測與執行期阻斷（如 Cilium、Tetragon、Falco），並透過 `CAP_BPF` 與強化 verifier 縮減核心提權面。⚠️ 核心子系統預設政策因發行版與雲端供應商而異。
  - 來源：Linux Kernel 文件、Cilium / Tetragon 專案文件

## 3. 靜態分析、Fuzzing 與 AI 輔助審計工具鏈

- **靜態與變體分析**：**CodeQL**（跨檔案語意資料流與變體分析主力）、**Semgrep**（輕量語法樹規則與 CI/pre-commit 防線）。
- **灰箱 Fuzzing**：**AFL++**（C/C++ 覆蓋率導引與 Persistent Mode 標準）、**cargo-fuzz**（Rust 結合 `libFuzzer` 與 `arbitrary` crate 做結構感知 fuzzing）、**OSS-Fuzz / ClusterFuzzLite**（開源大規模持續 fuzzing 與 PR 閘門）。
- **AI 輔助審計與修補（2025–2026 趨勢）**：業界將 LLM/Agent 整合於 SAST 誤報分流、Fuzzer Harness 生成與 Crash 根因分析；同時歐盟 Cyber Resilience Act（CRA）等法規推動持續 Fuzzing 與供應鏈簽章成為交付門檻。⚠️ AI 審計工具生態快速演進。
  - 來源：GitHub Security Lab / OSS-Fuzz（https://github.com/google/oss-fuzz）

## 4. 靶場與學習資源基準

- **Web / API**：PortSwigger Web Security Academy（免費且涵蓋 HTTP Smuggling、Race Condition、OAuth 等現代議題）。
- **Binary / Systems**：pwn.college（亞利桑那州立大學開源系統安全實戰平台）。
- **真實目標與揭露**：HackerOne、Bugcrowd、Intigriti、GitHub Security Advisories（GHSA）與 MITRE CNA 協調揭露流程。⚠️ 平台獎金中位數與政策隨時調整，書中引用時標註日期。
