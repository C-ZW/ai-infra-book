# 規範術語集（Canonical Terms）

本文件記錄《邊界失守：從架構盲區到 0-day 獵捕的軟體安全工程》全書 30 個已撰寫章節的核心方法論概念、攻擊模型、防禦架構與專門術語。各章寫作契約要求：每個核心概念由其擁有章節首次正式定義並展開，後續章節若需引用，皆以「（見 ChNN）」標記自然回扣，不重複定義，以維持全書概念體系之一致與嚴密。

---

## 術語總覽表

| 序號 | 術語名稱（中／英） | 首次定義章節 | 一句話白話定義 | 引用／後續章節 |
|---|---|---|---|---|
| 01 | 信任邊界<br>(Trust Boundary) | ch01 | 不同特權等級或安全域交會的邏輯邊界，所有穿越此邊界的資料與呼叫皆視為不可信且必須校驗。 | ch02, ch03, ch06, ch11, ch17, ch18 |
| 02 | Source-Sink-Sanitizer 三元組<br>(Source-Sink-Sanitizer Triad) | ch01 | 污點傳播模型的核心元件：未受信任輸入源（Source）、危險執行操作（Sink）與資料淨化驗證器（Sanitizer）。 | ch02, ch08, ch13, ch28 |
| 03 | 不變量違背<br>(Invariant Violation) | ch01 | 系統內部狀態機脫離預期安全假設的現象，是安全漏洞的形式化本質而非單純的語法錯誤。 | ch06, ch12, ch25 |
| 04 | 攻擊面測繪<br>(Attack Surface Mapping) | ch02 | 系統化盤點外部可達之主機、通訊埠、子網域、API 端點與第三方相依性的主動／被動偵察過程。 | ch01, ch18, ch34 |
| 05 | 白箱 Source-to-Sink 逆向審計<br>(Whitebox Source-to-Sink Audit) | ch02 | 從底層危險呼叫（Sink）出發逆向追溯輸入路徑（Source）以快速定位高危鏈的靜態代碼審計方法。 | ch08, ch13, ch28, ch32 |
| 06 | HTTP 請求走私<br>(HTTP Request Smuggling) | ch03 | 前端代理與後端伺服器對 HTTP 訊息邊界（Content-Length 與 Transfer-Encoding）解析不一致導致的管線請求走私攻擊。 | ch11, ch14 |
| 07 | CL.TE / TE.CL 歧義<br>(CL.TE / TE.CL Desynchronization) | ch03 | 前端與後端分別優先採用 Content-Length 或 Transfer-Encoding: chunked 所造成的 HTTP 請求邊界分歧。 | ch14 |
| 08 | JWT 信任根倒置<br>(JWT Trust Root Inversion) | ch04 | 伺服器未強制指定驗證演算法，反而盲信 Token 標頭之 alg 宣告，導致 alg: none 或金鑰混淆攻擊。 | ch05, ch06 |
| 09 | Refresh Token 輪替<br>(Refresh Token Rotation, RTR) | ch04 | 每次使用 Refresh Token 換發存取憑證時皆作廢舊 Token 並發行新 Token，兼具外洩偵測與自動撤銷能力。 | ch05, ch34 |
| 10 | XML 簽章包裝攻擊<br>(XML Signature Wrapping, XSW) | ch05 | 在 SAML 斷言中重組 XML 樹狀結構，使簽章驗證器校驗合法原節點，而業務解析器讀取偽造節點的攻擊。 | ch04, ch09 |
| 11 | MFA 疲勞轟炸<br>(MFA Fatigue / Push Bombing) | ch05 | 攻擊者短時間內發送大量推播認證請求，利用使用者認知疲勞誘使其誤按同意的非技術繞過手段。 | ch04, ch18, ch34 |
| 12 | 物件層級授權失效<br>(Broken Object Level Authorization, BOLA/IDOR) | ch06 | API 依賴客戶端傳入之物件 ID 直接存取資料，而未於資料庫查詢層檢驗請求者之多租戶屬權。 | ch01, ch07, ch34 |
| 13 | 物件屬性層級授權失效<br>(Broken Object Property Level Authorization, BOPLA) | ch06 | ORM 實體直接對接請求 Payload（Mass Assignment），導致攻擊者能竄改未受保護之敏感欄位（如 isAdmin）。 | ch07, ch13 |
| 14 | 功能層級授權失效<br>(Broken Function Level Authorization, BFLA) | ch06 | API 僅隱藏管理員端點 UI，卻未在伺服器端路由與控制器對使用者角色進行嚴格存取控制。 | ch07, ch34 |
| 15 | GraphQL 查詢深度與複雜度濫用<br>(GraphQL Depth & Complexity Abuse) | ch07 | 攻擊者構造遞迴或巨大巢狀 GraphQL 查詢，迫使後端解析器耗盡 CPU 與記憶體引發阻斷服務。 | ch06, ch13 |
| 16 | 跨站 WebSocket 劫持<br>(Cross-Site WebSocket Hijacking, CSWSH) | ch07 | 伺服器於 WebSocket 握手時依賴 Cookie 認證卻未嚴格校驗 Origin 標頭，導致跨站腳本劫持即時連線。 | ch10 |
| 17 | 資料與控制平面混同<br>(Data-Control Plane Confusion) | ch08 | 所有注入漏洞的共同根因：未經結構化轉義的外部資料被直譯器或執行環境誤當成控制指令執行。 | ch01, ch09, ch13, ch20 |
| 18 | 二階注入<br>(Second-Order Injection) | ch08 | 惡意 Payload 首次存入資料庫時未被觸發，而在後續被信任情境讀取並動態傳入 Sink 造成危害。 | ch02, ch28 |
| 19 | 伺服器端模板注入<br>(Server-Side Template Injection, SSTI) | ch08 | 使用者輸入未經防護即嵌入模板引擎原始碼中解析，進而透過執行環境物件反射取得任意代碼執行（RCE）。 | ch13, ch14 |
| 20 | 路徑遍歷正規化繞過<br>(Path Traversal Canonicalization Bypass) | ch09 | 檔案路徑驗證先於規範化（Canonicalization）執行，導致攻擊者利用 `../` 或編碼混淆逃逸安全根目錄。 | ch08, ch11 |
| 21 | Zip Slip 歸檔路徑遍歷<br>(Zip Slip Archive Path Traversal) | ch09 | 解壓縮程式未驗證壓縮檔條目中包含的相對目錄字元，導致解壓時覆寫任意系統敏感檔案。 | ch19, ch25 |
| 22 | XML 外部實體注入<br>(XML External Entity, XXE) | ch09 | XML 解析器啟用外部實體（DTD）解析，允許攻擊者讀取伺服器本機檔案或發動內部網路 SSRF。 | ch05, ch11 |
| 23 | 同源政策<br>(Same-Origin Policy, SOP) | ch10 | 瀏覽器核心安全隔離模型：限制來自不同 Scheme、Host 與 Port 的文檔與腳本存取彼此的資源與 DOM。 | ch04, ch05, ch11 |
| 24 | DOM 型跨站腳本攻擊<br>(DOM-based XSS) | ch10 | 客戶端 JavaScript 從未受信任 Source（如 location.hash）讀取資料，並直接寫入危險 Sink（如 innerHTML）。 | ch08, ch14, ch28 |
| 25 | CORS 錯誤配置<br>(CORS Misconfiguration) | ch10 | 伺服器盲目反射請求端之 Origin 標頭並搭配 Access-Control-Allow-Credentials: true，摧毀 SOP 保護。 | ch06, ch11 |
| 26 | 伺服器端請求偽造<br>(Server-Side Request Forgery, SSRF) | ch11 | 誘導伺服器向未受信任之外部或內部端點發起網路請求，以存取雲端 Metadata 或隔離內部網路資源。 | ch01, ch18 |
| 27 | URL 解析器分歧<br>(URL Parser Differential) | ch11 | 不同函式庫或中介軟體對 RFC 3986 與 WHATWG 標準之使用者名稱、斜線與主機名解析順序不同導致的防禦繞過。 | ch03, ch14 |
| 28 | Web 快取中毒與快取欺騙<br>(Web Cache Poisoning & Deception) | ch11 | 操縱快取鍵值排除的 Unkeyed 標頭或副檔名辨識，使快取伺服器將惡意回應或敏感私有資料向全網快取。 | ch03, ch10 |
| 29 | 檢查時至使用時條件競爭<br>(Time-of-Check to Time-of-Use, TOCTOU) | ch12 | 資源狀態在條件檢查與實際操作之間存在微秒級時間差，遭併發請求利用以破壞不變量。 | ch01, ch17, ch25 |
| 30 | HTTP/2 單封包併發攻擊<br>(Single-Packet Attack) | ch12 | 利用 HTTP/2 多路複用與 TCP Last-Byte 同步技術，將數十個平行請求在同一微秒抵達伺服器以引發競爭。 | ch03, ch11 |
| 31 | 原型鏈汙染<br>(Prototype Pollution) | ch13 | JavaScript 物件深度合併遞迴未過濾 `__proto__` 鍵值，導致竄改所有物件共享之 Object.prototype 屬性與行為。 | ch08, ch10, ch28 |
| 32 | 正規表示式阻斷服務<br>(Regular Expression Denial of Service, ReDoS) | ch13 | 巢狀或重疊量詞正規表示式在非確定有限狀態機（NFA）處理畸形輸入時發生指數級回溯，鎖死事件迴圈。 | ch07, ch34 |
| 33 | WAF 協定混淆繞過<br>(WAF Protocol Mutation Bypass) | ch14 | 利用 WAF 檢驗引擎與後端 Web 伺服器在分塊傳輸或邊界分隔符的解析寬容度差異以隱蔽 Payload。 | ch03, ch11 |
| 34 | 填充預言機攻擊<br>(Padding Oracle Attack) | ch15 | 利用 CBC 解密時伺服器回傳之 PKCS#7 填充錯誤與合法錯誤的側通道差異，逐位元組還原明文或偽造密文。 | ch04, ch20 |
| 35 | 提示詞注入<br>(Prompt Injection, Direct / Indirect) | ch16 | 攻擊者將不受信任指令夾帶於資料平面中，破壞 LLM 控制平面造成指令覆寫與未授權工具呼叫。 | ch08, ch17, ch18 |
| 36 | 工具呼叫劫持與 Agent 提權<br>(Tool-Calling Hijack & Agent Privilege Escalation) | ch16 | LLM Agent 盲信模型輸出而直接呼叫具備破壞性之本機 API 或資料庫操作，欠缺二次確認機制。 | ch01, ch34 |
| 37 | 容器逃逸<br>(Container Escape) | ch17 | 突破 Linux Namespaces 與 cgroups 邊界，藉由特權模式（SYS_ADMIN）或敏感 Host 路徑掛載取得宿主機控制權。 | ch18, ch19, ch20 |
| 38 | Kubernetes RBAC 隱蔽提權<br>(Kubernetes RBAC Hidden Privilege Escalation) | ch17 | 利用 Pod 繫結、Impersonate 或 Token 建立等細粒度授權規則缺口，由低權限 ServiceAccount 取得叢集管理權。 | ch18, ch34 |
| 39 | 執行個體中繼資料服務邊界<br>(Instance Metadata Service Boundary, IMDSv1/v2) | ch18 | 雲端虛擬機取得 IAM 暫時憑證的端點，IMDSv2 透過 PUT 標頭工作階段防範單純 SSRF 竊取金鑰。 | ch11, ch17 |
| 40 | IAM 橫向移動權限圖<br>(IAM Lateral Movement & Privilege Graph) | ch18 | 在雲端多帳號與委派信任關係中，藉由 PassRole、AssumeRole 等原語串接跳板以達成最終目標。 | ch06, ch17, ch34 |
| 41 | 相依性混淆<br>(Dependency Confusion) | ch19 | 內部私人套件名稱未在公開註冊表註冊，導致建置工具因版本優先序優先下載同名惡意公開套件。 | ch17, ch34 |
| 42 | 管線中毒執行<br>(Poisoned Pipeline Execution, PPE) | ch19 | 攻擊者透過對開源或內部儲存庫發送 PR 觸發高權限 CI/CD 工作流程，竊取儲存庫金鑰與投毒建置產物。 | ch18, ch34 |
| 43 | 堆疊緩衝區溢位<br>(Stack Buffer Overflow) | ch20 | 未檢查長度之輸入寫入超出局部變數邊界，覆寫堆疊幀之儲存幀指標（SFP）與回傳位址（Return Address）。 | ch21, ch25, ch29 |
| 44 | 回傳導向程式設計<br>(Return-Oriented Programming, ROP) | ch20 | 在 DEP/NX 防禦下，利用二進位檔既有以 `ret` 結尾的指令片段（Gadget）串接執行任意控制流。 | ch21, ch25, ch32 |
| 45 | 控制流圖還原<br>(Control Flow Graph Reconstruction) | ch21 | 將反組譯機器碼之條件跳躍與分支基本塊重建為有向圖，以理解無符號二進位檔的高層控制邏輯。 | ch20, ch28, ch30 |
| 46 | 靜態單一賦值反編譯<br>(Static Single Assignment Decompilation) | ch21 | 將暫存器操作抽象為變數僅被指派一次的表示法，消除架構細節並還原出高階 C 虛擬碼結構。 | ch25, ch28 |
| 47 | 健全性契約<br>(Soundness Contract in Rust) | ch25 | Rust 安全抽象對編譯器與呼叫者的承諾：無論 safe 程式碼如何調用，封裝內部的 `unsafe` 區塊絕不可誘發未定義行為（UB）。 | ch20, ch29 |
| 48 | 未定義行為<br>(Undefined Behavior, UB) | ch25 | 程式違反語言規範假設（如可變別名衝突、未初始化記憶體讀取），導致編譯器最佳化破壞記憶體安全模型。 | ch20, ch28, ch29 |
| 49 | 語意資料流與污點分析<br>(Semantic Data Flow & Taint Analysis) | ch28 | 跨檔案追蹤未受信任輸入沿著變數指派與函式傳參傳播至危險操作的靜態程式碼分析技術。 | ch01, ch02, ch34 |
| 50 | 變體分析<br>(Variant Analysis) | ch28 | 在已知單一 CVE 漏洞模式後，利用 CodeQL 或 Semgrep 語義查詢在整個代碼庫中批量獵捕同類語意漏洞。 | ch29, ch32 |
| 51 | 覆蓋率導引灰箱 Fuzzing<br>(Coverage-Guided Greybox Fuzzing) | ch29 | 利用輕量編譯插樁追蹤邊緣覆蓋率反饋，挑選觸發新控制流分支的變異種子進行持續演化測試。 | ch30, ch31 |
| 52 | 持久模式<br>(Persistent Mode in AFL++) | ch29 | 將目標測試函式置於重複迴圈內在單一行程內多次呼叫，避免重複 fork() 開銷，將測試吞吐量提升十倍以上。 | ch30, ch31 |
| 53 | 混合式 Fuzzing<br>(Hybrid Fuzzing) | ch30 | 結合灰箱 Fuzzing 的高吞吐量隨機探索與符號執行的精準約束求解，精確擊破魔術數字與複雜檢查路徑。 | ch29, ch31 |
| 54 | 狀態爆炸<br>(Path Explosion) | ch30 | 符號執行時程式分支數量隨路徑深度呈指數級激增，導致約束求解器與記憶體耗盡的經典理論瓶頸。 | ch28, ch29 |
| 55 | OSS-Fuzz 持續模糊測試<br>(OSS-Fuzz Continuous Testing) | ch31 | Google 營運的開源大規模 Fuzzing 服務，將 Sanitizer 與 Fuzzer Harness 整合進開源專案建置以常態挖掘 0-day。 | ch29, ch32, ch34 |
| 56 | 結構感知 Fuzzer Harness<br>(Structure-Aware Fuzz Target) | ch31 | 利用 LibFuzzer 與 FuzzedDataProvider 定義語意合規的輸入生成介面，直接對內部 API 進行高效 Fuzzing。 | ch29, ch30 |
| 57 | 漏洞利用鏈<br>(Exploit Chaining) | ch32 | 將資訊洩漏、記憶體損毀、SSRF 或提權等數個孤立中低危原語依賴串接，達成全系統高危控制的實戰攻防技術。 | ch01, ch18, ch20 |
| 58 | 協調揭露流程<br>(Coordinated Vulnerability Disclosure, CVD) | ch32 | 研究員向受影響廠商通報未公開 0-day 並約定 90 天修復緩衝期後公開細節的標準負責任揭露框架。 | ch34, ch37 |
| 59 | 鋪平之路與預設安全<br>(Paved Road & Secure-by-Default) | ch34 | 提供封裝良好且預設安全的框架與工具鏈，讓工程師走最輕鬆的開發路徑即自動獲得最高安全防護。 | ch01, ch08, ch36 |
| 60 | 可達性分析<br>(Reachability Analysis) | ch34 | 結合靜態呼叫圖與執行期分析，確認依賴套件中之 CVE 是否能被應用程式進入點實際觸及以降低 SCA 誤報。 | ch19, ch28 |
| 61 | 資安能力證明體系<br>(Security Proof of Work, PoW) | ch36 | 以公開可驗證的成果（如 CVE、開源 Fuzzer、研究白皮書與技術專欄）替代履歷主觀宣稱的實力展示體系。 | ch32, ch37 |
| 62 | 實戰操作型認證<br>(Hands-on Performance Certification) | ch37 | 以真機靶場渗透與限時提權報告代替選擇題記憶背誦的高信噪比專業證照評測體系（如 OSCP、CRTP）。 | ch36 |
