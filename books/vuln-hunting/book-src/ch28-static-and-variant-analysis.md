# 第 28 章：靜態分析、變體分析與自動化規則工程

前面 27 章我們一路拆解了從協定解析差異、授權失效、密碼學破口、AI Agent 邊界，到 `ptmalloc2` 堆積、Rust/C FFI 與 Linux 核心的單點漏洞成因。但走進真實的大型工程團隊或資安研究現場，真正的瓶頸往往不是「看不懂單一漏洞」，而是**怎麼把腦袋裡抓漏洞的直覺放大到幾十萬行程式碼上**。當系統長成幾百個微服務、TypeScript 與 C/Rust 混寫的龐大 Monorepo 時，光靠人工逐檔看 code 或在審 PR 時用肉眼盯，遲早會在某次重構時漏掉同一個坑。

拿 **NexusPay** 來說，我們在前面幾章抓出的高風險破口橫跨了不同語言層：Node.js / NestJS API 層有跨租戶 BOLA（第 6 章）跟未參數化的 SQL 排序注入（第 8 章）；底層透過 N-API 掛載的 `libnexus-parse` 原生 TLV 解析模組（第 25 章，`8 bytes` 檔頭、`len` 為 `4B` 無號整數、合法 payload 上限 `65,536 bytes`）則有長度加法回繞與緩衝區越界。本章就要帶你把這些人工抓出來的漏洞樣態，寫成可以自動執行、可以塞進 CI 防止回流、還能跨專案批量狩獵同類破口的**靜態分析**（Static Analysis）與**變體分析**（Variant Analysis）規則。

---

## 從你已知的出發

為什麼團隊好不容易用正規表達式或 AST 規則寫了一條掃描器去抓 `pool.query(` 與 `memcpy(`，結果第一次跑就噴出 200 筆誤報被開發者直接關掉，同時卻又放過了真正跨了三個檔案才炸開的 SQL 注入？

因為一般 Linter（像 ESLint 或 `clippy`）跟簡單的 `grep` 只看得到「單一語法節點」或「同一行文字」。它們既分不清楚 `pool.query(sql, [param])` 裡面哪個參數是危險的 SQL 字串、哪個是安全的綁定參數，也不知道某個變數在進到 Sink 之前其實早就通過了 `ALLOWED_FIELDS.includes(x)` 的白名單檢查；更沒辦法順著 Controller → Service → Repository 跨函式把整條髒資料的傳遞路線串起來。

要同時打破「高誤報牆」跟「跨函式盲區」，靜態分析器就必須把原始碼轉成**控制流圖**（CFG）、**靜態單賦值**（SSA）與**跨函式呼叫圖**（Call Graph），並精準定義哪些條件分支能切斷污點（Barrier / Sanitizer）。這正是現代兩大主力工具——輕量快速的 **Semgrep** 與具備跨檔案關聯式追蹤能力的 **CodeQL**——各自上場解決的核心難題。

---

## 機制與推導

### 攻擊者目標與實質影響

當研究員、紅隊或資安團隊把靜態分析與變體分析武器化之後，挖洞的效率就不再是「一天看一個檔案」的手工業，而是直接升級成三種規模化能力：

第一是**從單一公開 CVE 橫向收割整個生態系的 0-day 變體**。只要某個開源套件或同業系統發了一個修補 commit（比如修掉某處路徑解析繞過，或是某個 C 解析器的 `len + 8` 整數溢位），研究員透過比對修補前後的差異（Patch Diffing）抽出核心漏洞模式，花半小時寫成一條 Semgrep 或 CodeQL 規則，就能在幾分鐘內掃遍幾百個 GitHub 專案或公司內部的微服務，把還沒修的雙胞胎漏洞（Variants）一網打盡。

第二是**看穿多層包裝，直接定位深藏在跨模組裡的攻擊鏈**。在大型 TypeScript + C/Rust 系統裡，外部輸入（Source）跟危險操作（Sink）中間常常隔著四五層 DTO 轉換與輔助函式。跨檔案的全域污點追蹤能自動幫你把 Express/NestJS 路由入口一路連到底層 SQL 驅動或 FFI 邊界，省下好幾天人工翻找呼叫鏈的時間。

第三則是**幫防禦端築起不會忘記教訓的自動化護欄**（Regression Guardrails）。對 AppSec 團隊來說，每修完一個像 NexusPay 跨租戶漏檢 `tenant_id` 或 `libnexus-parse` 溢位的高危漏洞，隨手補一條對應的掃描規則進 CI/CD，就等於把這次的血淚教訓變成永遠在線的守門員，誰以後在 PR 裡不小心寫出同樣的破口，當場就會被攔下來。

---

### 靜態分析的四層程式表示：AST、CFG、SSA 與 Call Graph

為什麼有的工具掃十萬行只要 5 秒卻追不到跨檔案呼叫，有的工具要先跑半小時建資料庫卻能精準排除白名單？答案全在於分析引擎把原始碼「拆解」到了哪一層中間表示（Intermediate Representation）：

```text
原始碼 (Source Code)
  │
  ▼  詞法/語法解析 (Tree-sitter / Compiler Frontend)
[1. AST 抽象語法樹] ──────► 結構形狀完整，但無執行順序與分支因果
  │
  ▼  基本區塊切分與控制邊建立
[2. CFG 控制流圖] ────────► 知道「先檢查」還是「先使用」，可判定 BarrierGuard
  │
  ▼  靜態單賦值轉換 (φ 節點匯流)
[3. SSA / Def-Use 鏈] ────► 變數每個版本獨立成節點，資料流沿 Def-Use 邊前進
  │
  ▼  跨函式解析 (型別推論 / 指標分析 / 虛擬派發)
[4. Call Graph + 全域資料流] ► 串接 Controller -> Service -> Sink 跨檔案路徑
```

#### 1. AST（Abstract Syntax Tree，抽象語法樹）與它的極限

AST 把程式碼變成一棵語法樹：函式宣告、二元運算、方法呼叫各是一個節點，空白跟註解則被拿掉。純 AST 比對最大的好處是**根本不用編譯專案**，甚至連相依套件都不用裝，一秒鐘就能掃過幾萬行程式碼。

但只看 AST 有個致命傷：它只知道「語法長什麼樣子」，卻不知道「執行時會怎麼走」。看看下面這兩段長得幾乎一模一樣的 TypeScript 程式碼：

```ts
// 片段 A：安全（檢查沒過直接 throw 中斷，後面一定安全）
function getSortFieldSafe(input: string): string {
  if (!ALLOWED_FIELDS.includes(input)) {
    throw new BadRequestException("invalid sort field");
  }
  return buildOrderClause(input);
}

// 片段 B：有漏洞！（檢查沒過只印了一行 log，程式繼續往下跑！）
function getSortFieldVuln(input: string): string {
  if (!ALLOWED_FIELDS.includes(input)) {
    logger.warn("suspicious sort field", { input }); // 沒 return 也沒 throw！
  }
  return buildOrderClause(input);
}
```

如果你的規則只看 AST「這個函式裡有沒有呼叫 `ALLOWED_FIELDS.includes(input)`」，那它在看到片段 A 跟片段 B 時會給出完全一樣的判斷——要嘛把有洞的片段 B 當成好人放走（漏報 False Negative），要嘛連安全的片段 A 也一起抓起來警報（誤報 False Positive）。

#### 2. CFG（Control Flow Graph，控制流圖）與支配關係

為了看懂「檢查到底有沒有擋住執行流」，引擎必須往下建立 **CFG**（控制流圖）。CFG 會把函式切成一個個不會中途跳走的**基本區塊**（Basic Block），再用箭頭把 `if/else` 的 `True` 分支跟 `False` 分支連起來。

有了 CFG，分析器就能算出關鍵的**支配關係**（Dominance）：如果從函式入口走到 `Sink` 的**每一條可能路線**，都非得先經過 `Guard` 檢查為真的那一條分支不可（因為檢查為假的分支已經 `throw` 或 `return` 離開了），那就代表走到 `Sink` 的那一刻，白名單檢查百分之百已經通過了。回頭看上面的例子：片段 A 裡面的 `buildOrderClause(input)` 完全受 `ALLOWED_FIELDS.includes(input) === true` 支配；但片段 B 裡面的 `logger.warn` 跑完又合流回主幹道，所以走到 `buildOrderClause(input)` 時根本不保證通過了白名單。這就是 CodeQL 的 `MakeBarrierGuard` 跟 Semgrep 的 CFG 污點分析能分辨「真攔截」與「假記 log」的底層原理。

#### 3. SSA（Static Single Assignment）與變數覆寫

再看另一種常讓簡易掃描器犯傻的寫法——同一個變數名被重複賦值：

```ts
let q = req.query.filter;       // q_0 = 外部髒資料 (Source)
q = normalizeWhitespace(q);     // q_1 = f(q_0)  (還是髒的)
q = "status = 'PAID'";          // q_2 = 固定常數 (原本的髒資料已經被蓋掉了！)
pool.query(`SELECT * FROM tx WHERE ${q}`);
```

如果掃描器只是笨笨地記住「變數 `q` 曾經接過 `req.query.filter`」，最後一行就會被誤報成 SQL 注入。

把程式碼轉成 **SSA**（靜態單賦值）形式後，變數每次被重新賦值都會換一個新編號（`q_0`、`q_1`、`q_2`），遇到 `if/else` 兩條路合流時則用 `φ`（Phi）節點（如 `q_3 = φ(q_1, q_2)`）接起來。這樣分析器只要順著「哪裡定義、哪裡使用」（Def-Use Chain）的箭頭走，一眼就能看出最後流進 `pool.query` 的是乾淨常數 `q_2`，跟開頭的 `q_0` 早就沒關係了。

#### 4. Call Graph（呼叫圖）與跨函式追蹤的三個門檻

當髒資料跨出單一函式（Interprocedural Analysis），分析器就得靠 **Call Graph**（呼叫圖）把「呼叫點」跟「目標函式」連起來。能不能追得準，全看引擎有沒有跨過下面三個門檻：

第一個門檻是**上下文敏感度**（Context Sensitivity）。假設有個共用的小函式 `trimStr(x)`，A 處傳了髒資料 `trimStr(req.query.name)`，B 處傳了固定常數 `trimStr("NEXUS_SYSTEM")`。如果分析器不區分呼叫上下文，把兩次呼叫混為一談，就會誤以為 B 處拿到的回傳值也是髒的，瞬間炸出整片誤報。

第二個門檻是**欄位敏感度**（Field Sensitivity）。開發者常把好幾個值包進同一個物件傳給下一層，比如 `const opts = { sort: req.query.sort, limit: 20 }`。如果分析器分不清物件裡的不同欄位，看到 `opts` 裡有一個屬性是髒的就把整包 `opts` 塗黑，那後面明明只拿 `opts.limit` 去拼 SQL 的安全程式碼也會跟著遭殃。

第三個門檻則是**動態派發與依賴注入**。TypeScript 的介面呼叫、NestJS 的 `@Inject()` 依賴注入、Express 的 middleware 串列，或是 C 語言的函式指標表（Function Pointer Table），在原始碼字面上都看不到直接呼叫哪個具體函式。如果分析器看不懂框架的綁定規則或型別階層，污點追到這裡就會直接斷線。

---

### Semgrep 引擎架構：語法樹比對與輕量 Taint Mode

搞懂四層表示法之後，我們先看第一把利器：**Semgrep**。

Semgrep 的定位非常清楚——它是一套**快到可以直接塞進開發者本地 Pre-commit 與 PR 檢查的輕量語意掃描器**。它在底層用 Tree-sitter 把三十幾種語言解析成統一的抽象語法樹（`AST_generic`），再轉成輕量中介語言建立單一函式內的 CFG。最大的好處是不需要跑 `npm install`、`tsc` 或 `make` 編譯，十幾萬行程式碼往往十幾秒就掃完了。

寫 Semgrep 規則時，最常用的是它的**污點追蹤模式**（`mode: taint`）。只要在 YAML 裡填好四個區塊就能跑：
- `pattern-sources`：哪裡是外部髒資料的入口（例如 `req.query` 或 `$HDR->len`）。
- `pattern-sinks`：哪裡是危險的終點（搭配 `focus-metavariable` 可以精準指定「只有第 1 個參數是危險的」）。
- `pattern-sanitizers`：經過什麼函式或條件分支後就算洗乾淨了（加上 `by-side-effect: true` 就能表達「只要在 `if` 分支裡檢查過變數 `$X` 並提早 `return`，後面的 `$X` 就變乾淨了」）。
- `pattern-propagators`（選用）：遇到引擎不認識的自訂容器操作時，告訴它髒資料怎麼從 A 傳給 B。

下面我們直接針對 **NexusPay** 的兩個真實破口，寫出兩條馬上能跑的 Semgrep `mode: taint` 規則。第一條負責抓 TypeScript 裡把未淨化的 HTTP 輸入直接塞進 SQL 第一個命令參數的注入漏洞（第 8 章）；第二條負責抓底層 **`libnexus-parse` C 解析器**（第 25 章）裡，外部 `8 bytes` TLV 檔頭的 `len` 還沒檢查 `> 65536` 上限，就先拿去做加法並丟進 `malloc`/`memcpy` 的整數溢位漏洞：

```yaml
rules:
  - id: nexuspay-ts-req-to-raw-sql
    languages: [typescript, javascript]
    severity: ERROR
    mode: taint
    message: >-
      未淨化的 HTTP 輸入 ($SRC) 流入原生 SQL 查詢字串，可能導致 SQL Injection。
      請改用參數化查詢 ($1, $2) 或白名單檢查。
    pattern-sources:
      - pattern: req.query
      - pattern: req.params
      - pattern: req.body
    pattern-sanitizers:
      - pattern: parseInt($X, ...)
      - pattern: Number($X)
      - patterns:
          - pattern: |
              if (!$ALLOW.includes($VAR)) { ... }
          - focus-metavariable: $VAR
        by-side-effect: true
    pattern-sinks:
      - patterns:
          - pattern-either:
              - pattern: $DB.query($SQL, ...)
              - pattern: $PRISMA.$queryRawUnsafe($SQL, ...)
          - focus-metavariable: $SQL

  - id: nexuspay-c-tlv-len-add-overflow
    languages: [c]
    severity: ERROR
    mode: taint
    message: >-
      來自外部 TLV 封包的無號長度 ($LEN) 在做完加法運算後才用於配置或記憶體複製，
      可能發生 32 位元整數回繞 (例如 0xFFFF_FFF8 + 8 == 0) 導致堆積溢位。
    pattern-sources:
      - pattern: ($HDR : tlv_hdr_t *)->len
      - pattern: $HDR->len
    pattern-sanitizers:
      - patterns:
          - pattern: |
              if ($X > 65536 || ...) { return ...; }
          - focus-metavariable: $X
        by-side-effect: true
    pattern-sinks:
      - patterns:
          - pattern: malloc($SZ)
          - focus-metavariable: $SZ
      - patterns:
          - pattern: memcpy($DST, $SRC, $SZ)
          - focus-metavariable: $SZ
```

特別注意看規則裡面的 `focus-metavariable: $SQL`。在呼叫 `$DB.query($SQL, $PARAMS)` 時，只有第一個參數 `$SQL` 是 SQL 語法字串，第二個參數 `$PARAMS` 是安全的參數化綁定陣列。如果偷懶沒加 `focus-metavariable: $SQL`，那全專案所有規規矩矩寫 `pool.query("SELECT * FROM users WHERE id = $1", [req.query.id])` 的安全程式碼都會被當成漏洞狂報一通。

同時我們也要清楚 **Semgrep OSS（免費開源版）的限制**：它的 `mode: taint` 預設只在**單一檔案、單一函式內**（Intraprocedural）追蹤。只要 Controller 把 `req.query.sort` 傳給另一個檔案 `settlement.service.ts` 裡面的函式去拼 SQL，開源版 Semgrep 的污點鏈就會在那裡斷掉。這時候，就輪到重裝武器 CodeQL 上場了。

---

### CodeQL 關聯式引擎：從程式碼資料庫到全域 `TaintTracking`

如果說 Semgrep 是高速濾網，那 **CodeQL** 就是把整座原始碼倉庫編譯成一個關聯式資料庫，讓你直接寫查詢語言（物件導向 Datalog 方言 **QL**）去抓跨檔案、跨模組的深層攻擊鏈。

用 CodeQL 分析專案分成兩步：第一步是執行 `codeql database create` 建立資料庫。針對不同語言，CodeQL 抽取資料的方式也不同：
- 分析 **JavaScript / TypeScript**（統一用 `--language=javascript`）時，它直接讀取原始碼與 `tsconfig.json` 解析型別，不需要真的執行打包建置。
- 分析 **C / C++**（`--language=cpp`）時，因為 C 語言有大量的預處理器巨集（`#define`）與平台標頭檔，CodeQL 會掛載在真實編譯器旁邊（例如透過 `--command="make ..."`），等編譯器把巨集完全展開、型別全部對齊之後，才把最精確的語法樹與呼叫關係存進資料庫。
- 遇到像 NexusPay 這種 **TypeScript + C 混寫的 Monorepo**，只要加上 `--db-cluster --language=javascript,cpp`，就能一口氣建好雙語言的資料庫叢集。

資料庫建好之後，第二步就是寫 QL 查詢。在現代 CodeQL 的 `DataFlow::ConfigSig` 架構下，寫一條跨檔案的全域污點追蹤只需要定義一個模組並填好三個核心條件（QL 裡面稱為 Predicate）：
1. **`isSource(DataFlow::Node source)`**：定義髒資料從哪裡進來。例如直接繼承官方內建的 `RemoteFlowSource`，就會自動涵蓋 Express 的 `req.query`、`req.params`、`req.body`、`req.headers` 以及 NestJS 的路由參數。
2. **`isSink(DataFlow::Node sink)`**：定義哪裡是危險的終點，例如把 `sink` 綁定到 `call.getArgument(0)`（SQL 查詢的第一個字串參數）。
3. **`isBarrier(DataFlow::Node node)`**：定義哪些節點會把污點洗乾淨，包括像 `parseInt()` 這類數值轉型節點，以及用 `DataFlow::MakeBarrierGuard` 包裝的 CFG 控制流白名單守衛。

最後只要寫一行 `module Flow = TaintTracking::Global<MyConfig>;`，CodeQL 底層的不動點推論引擎就會自動幫你把橫跨十幾個檔案與函式的 `Source → ... → Sink` 完整路徑算出來。

---

### Worked Example：Express/NestJS SQLi `TaintTracking` 查詢與 Barrier 消誤報實算

為了讓你具體感受「隨手寫的天真規則」跟「打磨過 Barrier 的生產級規則」差多少，我們直接拿 **NexusPay** 的 TypeScript API 程式碼庫（共 `120` 個檔案，包含 Express/NestJS Controller、Service 與資料庫存取層）來做一次實測。

先看看這 `120` 個檔案裡面最常見的三種寫法：

```ts
// 1. [真漏洞 TP] 排序欄位沒做白名單檢查，傳進 Service 層跨函式拼進 SQL 字串
// controllers/settlement.controller.ts
app.get("/v1/settlements", async (req, res) => {
  const sortBy = String(req.query.sortBy ?? "created_at");
  const rows = await settlementService.listByMerchant(req.query.merchantId, sortBy);
  res.json(rows);
});
// services/settlement.service.ts
export async function listByMerchant(merchantId: unknown, sortBy: string) {
  const sql = `SELECT id, amount FROM settlements WHERE merchant_id = $1 ORDER BY ${sortBy} DESC`;
  return pool.query(sql, [merchantId]); // 第 0 個引數含髒資料 sortBy！第 1 個引數是安全綁定陣列
}

// 2. [常見誤報 FP-A] 已經用 parseInt / Number 轉成數字了，才放進模板字串
const limit = Number.parseInt(req.query.limit as string, 10);
await pool.query(`SELECT id FROM settlements LIMIT ${limit}`);

// 3. [常見誤報 FP-B] 已經通過 ALLOWED_COLS.includes() 白名單檢查（沒過直接 throw）
const col = String(req.query.col ?? "id");
if (!ALLOWED_COLS.includes(col)) {
  throw new Error("Invalid column");
}
await pool.query(`SELECT ${col} FROM settlements`);
```

如果我們一開始寫了一支「天真版」的 CodeQL 查詢：把所有 `query()` 的任意參數 `call.getAnArgument()` 都當成 Sink，而且完全不寫 `isBarrier`，丟進這 `120` 個檔案跑一輪，會直接炸出 **55 筆警報**：
- 裡面只有 **5 筆是真漏洞**（TP）。
- 高達 **50 筆全是誤報**（FP）！拆開來看：有 **15 筆**（FP-C）是因為把安全的第 2 個參數 `[merchantId]` 也當成了 Sink；有 **18 筆**（FP-A）其實已經先跑過 `parseInt(..., 10)` 或 `Number(...)` 轉成純數值，根本不可能夾帶 SQL 語法或引號；還有 **17 筆**則是早就做過白名單檢查（其中 **12 筆 FP-B** 用了 `ALLOWED_COLS.includes()` / `Set.has()` 守衛，另外 **5 筆**走了跨裝飾器的複雜 Zod Schema 驗證）。

現在我們把這三個痛點一次修好，寫出下面這支完整的 **CodeQL `TaintTracking` 查詢（`NexusSqlInjection.ql`）**：

```ql
/**
 * @name NexusPay Express/NestJS SQL Injection with Sanitizer Barriers
 * @description Tracks untrusted HTTP input to unparameterized SQL command strings,
 *              pruning parameterized args, numeric coercions, and allowlist guards.
 * @kind path-problem
 * @problem.severity error
 * @security-severity 9.0
 * @precision high
 * @id nexuspay/ts-sqli-with-barriers
 * @tags security
 *       external/cwe/cwe-089
 */

import javascript

/** 1. 定義白名單檢查守衛：ALLOWED.includes(x) 或 ALLOWED.has(x) */
class AllowlistGuard extends DataFlow::CallNode {
  AllowlistGuard() {
    this.getMethodName() in ["includes", "has"] and
    this.getNumArgument() = 1
  }

  /** 當條件評估為 true（例如 if (!ALLOWED.includes(x)) throw; 之後的後續路徑），x 視為已淨化 */
  predicate blocksExpr(Expr e, boolean outcome) {
    outcome = true and
    e = this.getArgument(0).asExpr()
  }
}

/** 2. 定義現代 CodeQL DataFlow::ConfigSig 組態模組 */
module NexusSqlConfig implements DataFlow::ConfigSig {
  // Source：所有遠端 HTTP 輸入（含 Express req.query / req.params / req.body 與 NestJS 對應節點）
  predicate isSource(DataFlow::Node source) {
    source instanceof RemoteFlowSource
  }

  // Sink：只鎖定 SQL 執行方法「第 0 個引數（SQL 命令字串本身）」，排除第 1 個參數綁定陣列
  predicate isSink(DataFlow::Node sink) {
    exists(DataFlow::MethodCallNode call |
      call.getMethodName() in ["query", "$queryRawUnsafe", "$executeRawUnsafe"] and
      sink = call.getArgument(0)
    )
  }

  // Barrier：切斷該程式碼庫中兩類已建模的淨化與白名單守衛路徑（工程近似模型）
  predicate isBarrier(DataFlow::Node node) {
    // (A) 數值轉型淨化：parseInt / Number.parseInt / Number 的回傳節點
    exists(DataFlow::CallNode numCall |
      (
        numCall.getCalleeName() in ["parseInt", "Number"] or
        numCall = DataFlow::globalVarRef("Number").getAMemberCall("parseInt")
      ) and
      node = numCall
    )
    or
    // (B) 控制流白名單守衛：沿 CFG 支配關係，在 AllowlistGuard 通過後的分支消除污點
    node = DataFlow::MakeBarrierGuard<AllowlistGuard>::getABarrierNode()
  }
}

/** 3. 實例化全域跨檔案污點追蹤模組 */
module NexusSqlFlow = TaintTracking::Global<NexusSqlConfig>;

import NexusSqlFlow::PathGraph

from NexusSqlFlow::PathNode source, NexusSqlFlow::PathNode sink
where NexusSqlFlow::flowPath(source, sink)
select sink.getNode(), source, sink,
  "SQL injection: untrusted HTTP input from $@ reaches unparameterized SQL command.",
  source.getNode(), "user-controlled source"
```

把這支加了精準 Sink 與雙重 Barrier 的查詢丟回同一個 CodeQL 資料庫重跑，我們來算算看每一步砍掉了多少誤報，以及 **Precision**（精確率）、**Recall**（召回率）與 **F1 Score** 的變化：

```text
=== NexusPay CodeQL 查詢精準度演進實測 (120 TS 檔案基準集) ===

[基準版本：無 Barrier、Sink 涵蓋所有 query() 引數]
  Total Alerts = 55  (TP = 5, FP = 50, FN = 0)
  Precision    = 5 / 55 = 9.09%
  Recall       = 5 / 5  = 100.0%
  F1 Score     = 2 × (0.0909 × 1.0) / (0.0909 + 1.0) = 16.67%

[演進步驟 1：isSink 限縮為 call.getArgument(0)（排除參數化佔位陣列）]
  消除 FP-C    = 15 筆  (剩餘 FP = 50 - 15 = 35，Precision 升至 5 / 40 = 12.50%)

[演進步驟 2：isBarrier 加入 parseInt / Number 數值轉型節點]
  消除 FP-A    = 18 筆  (剩餘 FP = 35 - 18 = 17)

[演進步驟 3：isBarrier 加入 AllowlistGuard (includes / has) MakeBarrierGuard]
  消除 FP-B    = 12 筆  (剩餘 FP = 17 - 12 = 5，為跨裝飾器複雜 Zod 驗證)

[最終版本彙總]
  Total Alerts = 10  (TP = 5, FP = 5, FN = 0)
  誤報消除比例 = (50 - 5) / 50 = 45 / 50 = 90.0%
  Precision    = 5 / 10 = 50.0%  (較基準 9.09% 提升 5.5 倍)
  Recall       = 5 / 5  = 100.0% (零漏報損失)
  F1 Score     = 2 × (0.50 × 1.0) / (0.50 + 1.0) = 66.67%
```

你看，只是把 Sink 鎖緊在第 0 個引數，再補上數值轉型跟 `MakeBarrierGuard` 兩個屏障，我們就在**半個真漏洞都沒漏掉**（Recall 維持 `100.0%`）的前提下，一口氣砍掉了 **`90.0%`（45 / 50）的誤報**，把警報總數從讓人崩潰的 55 筆壓到 10 筆，Precision 從 `9.09%` 拉升到 `50.0%`（如果再幫剩下那 5 筆自訂 Zod 裝飾器補上專屬 Barrier，就能在該基準集逼近 `100%`）。

不過要注意，如果你打算拿這支查詢去掃外面不熟的開源專案，記得再幫 `AllowlistGuard` 多加一層限制，確認呼叫 `.includes()` 的那個陣列真的是寫死的常數白名單，免得把別人的普通字串比對也當成安全守衛。

---

### 變體分析工作流：從單一 CVE Patch 反推同生態系 0-day

在獨立漏洞研究裡，變體分析（Variant Analysis）最迷人的地方，就是**拿著一個剛公開的 CVE 修補 commit，在 24 小時內掃出十幾個還沒被發現的同類漏洞**。實戰時我們會照著下面五步走：

第一步是 **Patch Diffing 與抽離不變量**。打開某個 CVE 的修復 commit，把專案特有的變數名稱跟業務字眼全部擦掉，只問一句：「它原本打破了哪一條安全不變量？」舉個例子，某個開源 C 語言 TLV 解析庫（一樣是 `8-byte` 檔頭加 `65,536-byte` 上限）修了一個堆積溢位：修補前寫的是 `uint32_t sz = hdr->len + 8; if (sz <= 65536 + 8) ...`，修補後改成 `if (hdr->len > 65536) return -1; uint32_t sz = hdr->len + 8;`。抽離出來的核心模式就是：**外部傳入的無號長度還沒檢查上限，就先拿去做加法，導致整數回繞繞過檢查**。

第二步是**先寫最小正負測試集**（Fixtures）。千萬別急著直接去掃大型專案！先在本地建一個小檔案，裡面放 1 個確定有洞的函式（True Positive）跟 2 個確定修好的安全函式（True Negative）。你的規則必須精準抓到有洞的那個、同時對安全的兩個保持安靜，才算及格。

第三步是**兩段式漏斗掃描**（Semgrep 初篩 → CodeQL 深追）。假設你想掃 GitHub 上 80 個相關的 C/C++ 開源專案，如果要幫這 80 個專案全部編譯建置 CodeQL 資料庫，可能三天三夜都跑不完。聰明的做法是先用不用編譯的 Semgrep 跑一輪結構初篩，花 2 分鐘從 80 個專案裡挑出「有類似加法後配置結構」的 8 個候選專案；接著再只幫這 8 個專案建置 CodeQL 資料庫，用跨函式 `TaintTracking` 確認外部網路封包（如 `recv()`）是不是真的能一路流進那個加法裡。

第四步是**補齊自訂包裝函式**（`isAdditionalFlowStep`）。真實專案很少直接裸寫 `malloc` 或 `pool.query`，通常會包一層像 `nexus_buf_alloc()` 或自訂的 Query Helper。看到污點在某層輔助函式斷掉時，就把那個包裝函式加進 Sink 或 FlowStep 裡。

第五步則是**人工確認可達性與前置條件**。靜態規則找到路徑，只代表「程式碼裡有這條通道」，還得回頭檢查這個入口是不是只有管理員能打、前面的協定解析有沒有其他長度限制，確認真的能觸發後，再走第 33 章的負責任漏洞通報流程。

---

## 故障模式與防禦

把靜態分析放進日常開發與漏洞挖掘時，最容易踩到下面四種規則設計陷阱，以及一個架構層級的治本之道。

### 故障模式 1：遇到事件佇列與 FFI 非同步工作就斷鏈（Taint Loss）

靜態資料流引擎最擅長追那種「A 呼叫 B、B 回傳給 C」的直線呼叫。但現代後端到處都是非同步解耦：比如在 Node.js 裡呼叫 `eventEmitter.emit("settlement:created", payload)`、丟進 Redis/Kafka 佇列，或是透過 N-API 的 `napi_create_async_work` 把指標交給背景 C/Rust 執行緒池去跑。在靜態呼叫圖上，發送端（`.emit`）跟接收端（`.on`）中間沒有直接的函式呼叫邊，污點追到這裡就會原地消失，造成漏報。

要補上這個缺口，千萬別指望預設的 `TaintTracking` 會自己看懂事件名稱。我們必須主動在 CodeQL 裡寫一條 `isAdditionalFlowStep`（或在 Semgrep 寫 `pattern-propagators`），告訴引擎「只要第一個事件名稱字串一樣，就把 `.emit(topic, data)` 的 `data` 連到 `.on(topic, handler)` 的 `handler` 參數上」；或者乾脆把所有非同步 Consumer 的入口參數都直接標成新的 `Source`。

### 故障模式 2：寫出不夠嚴謹的 Barrier，把真漏洞當成已修好（Unsound Barrier）

這是寫靜態規則最危險的失誤。假設你在幫 `libnexus-parse` 寫 C 語言長度檢查規則時，大筆一揮規定：「只要看到 `if (len <= 65536)` 就當成已經安全淨化（Barrier）！」結果專案裡剛好有一段程式碼是這樣寫的：

```c
int32_t body_len = (int32_t)hdr->len; // 致命轉型！無號 0xFFFF_FFF8 轉成有號變成 -8
if (body_len <= 65536) {              // -8 <= 65536 成立，直接穿過檢查！
    uint8_t *buf = malloc((size_t)body_len + 8);
    memcpy(buf, payload, hdr->len);   // 拿超大無號數複製，當場寫爆堆積
}
```

看到問題了嗎？如果你的 `isBarrier` 只傻傻檢查 `<= 65536`，卻沒有檢查變數是不是無號整數、也沒有檢查下界 `> 0`，你的掃描器就會把這個高危的整數符號截斷漏洞當成「乖寶寶已檢查」直接消音！

所以設計 `isBarrier` 時一定要守住底線：在 C/C++ 檢查長度時，Barrier 必須要求該變數是無號型別（`uint32_t` / `size_t`），或是同時檢查了 `body_len > 0 && body_len <= 65536`。同理，在寫 SQL 注入規則時，`parseInt()` 可以當 Barrier，但像 `str.replace("'", "")` 這種只拿掉單引號的半調子過濾，絕對不能放進 `isBarrier`（因為在 `ORDER BY` 或數字欄位裡，攻擊者根本不需要單引號就能注入）。

### 故障模式 3：C/C++ 沒對齊正式版編譯參數（`assert` 在 `-DNDEBUG` 下人間蒸發）

很多團隊在寫 C/C++ 模組時，習慣用 `assert(hdr->len <= 65536);` 來做輸入邊界檢查。如果在建置 CodeQL 資料庫時用了 Debug 模式的編譯參數，`assert` 會展開成正常的條件判斷與中止呼叫，掃描器看起來覺得一切安全；但等到正式上線編譯 Release 版本時，Makefile 加上了 `-DNDEBUG` 旗標，C 預處理器會把所有的 `assert(...)` **整行刪得一乾二淨**！

因此，對 C/C++ 與 Rust 建置靜態分析資料庫時，一定要對齊線上 Release 的真實編譯指令；而且最好直接加一條 Semgrep 規則，專門抓「把 `assert()` 當成外部輸入安全檢查」的危險寫法。

### 故障模式 4：把低精準度規則塞進 PR 阻斷閘門，引發「狼來了」效應

如果你把一條 Precision 只有 `10%`（報 10 題有 9 題是誤報）的實驗性規則直接設成 GitHub PR 的強制阻斷條件（Blocking Check），不用一個禮拜，被誤報煩死的開發者就會開始在程式碼裡到處貼 `// nosemgrep` 或要求把掃描器拔掉，最後連那 `10%` 的真漏洞也沒人看了。

健康的規則工程一定要做**雙軌分流**（Two-Tier Rule Gating）：

| 規則分級 | 部署位置與觸發時機 | 精準度門檻要求 | 適用規則類型 |
|---|---|---|---|
| **Tier-A（PR 阻斷級）** | 開發者 Pre-commit / PR 合併強制檢查（失敗即禁止 Merge） | **Precision ≥ 95%**（幾乎零誤報，且錯誤訊息直接給出安全寫法） | 明確危險的反模式：如 `$queryRawUnsafe` 字串拼接、`child_process.exec` 動態插值、查詢多租戶表漏寫 `tenant_id`、C 語言 `u32` 先加法後檢查 |
| **Tier-B（變體狩獵與夜間審計級）** | 每日夜間 CI 或資安團隊手動執行（不卡 PR，結果進資安分流佇列） | **Recall 優先**（寧可多抓再由資安工程師微調 `isBarrier`） | 跨越多層微服務的廣域 `TaintTracking`、針對最新 CVE 剛寫好的初版變體搜尋規則 |

### 治本防禦：用型別系統與安全 API 讓危險 Sink 根本寫不出來

說到底，寫靜態規則去抓漏洞終究是在後面追著跑。最省力的防禦工程，是**從架構與 API 設計上，讓開發者連寫出危險 Sink 的機會都沒有**：

在 TypeScript 與資料庫層，直接用設定檔封殺 `$queryRawUnsafe` 與帶動態字串的 `.query()`，規定團隊一律只能用型別安全的查詢建構器或強制帶參數的 Tagged Template（如 `Prisma.sql`），甚至把 `tenantId` 做成呼叫資料庫 Repository 必填的第一個型別參數。

在底層 `libnexus-parse` 原生邊界，則是淘汰手寫 C 語言的 `malloc(len + 8)` 與裸指標算術，改用第 25 章示範過的 Rust 安全切片與 `checked_add`，把溢位與邊界檢查包進回傳型別 `Option`/`Result` 裡（並搭配 `#![deny(unused_must_use)]` 與禁用 `.unwrap()` 的 Clippy 規則）。當不安全的寫法連編譯器那一關都過不了時，你就從根本上消滅了一整類漏洞。

---

## 動手做

- **難度**：進階
- **預估時間**：60 分鐘

現在我們在本地建一個迷你的 **NexusPay** 雙語言實驗倉庫 `nexuspay-variant-lab/`（裡面同時有 TypeScript API 與 `libnexus-parse` 的 C 語言 TLV 解析器），親手使用免費開源的 **Semgrep OSS** 與 **CodeQL CLI** 寫出 **3 條客製化規則**（2 條 Semgrep + 1 條 CodeQL），實際建立 `--db-cluster` 雙語言資料庫，驗證怎麼抓出跨函式真漏洞、同時把三個安全寫法的誤報壓到零。

### 前置環境準備

1. **安裝 Semgrep OSS**（免費開源版）：
   ```bash
   python3 -m pip install --user semgrep
   semgrep --version
   ```
2. **安裝 CodeQL CLI 與標準查詢庫**：
   - 從 GitHub `codeql-cli-binaries` 下載對應你作業系統（macOS / Linux）的壓縮包，解壓縮並把 `codeql` 放進 `PATH`。
   - 下載官方查詢與函式庫套件：`codeql pack download codeql/javascript-queries codeql/cpp-queries`。
   - 確認電腦裡有基本的 C 編譯器（`gcc` 或 `clang`）與 `make`。

### 步驟 1：建立本地 `nexuspay-variant-lab` 靶標原始碼

先建好實驗目錄結構：

```bash
mkdir -p nexuspay-variant-lab/{api,native,rules/semgrep,rules/codeql}
cd nexuspay-variant-lab
```

首先建立 `api/settlement.ts`。這支檔案裡故意放了 2 個真漏洞（跨函式 SQL 注入 `TP-1`、漏寫 `tenant_id` 的跨租戶 BOLA `TP-2`），以及 3 個用來考驗掃描器會不會亂誤報的安全寫法（參數化查詢、經過 `parseInt` 轉型、以及通過 `ALLOWED_SORT.includes()` 白名單守衛）：

```ts
// api/settlement.ts
interface Request {
  query: Record<string, string | undefined>;
  params: Record<string, string | undefined>;
  user: { tenantId: string };
}

interface DbPool {
  query(sql: string, params?: unknown[]): Promise<unknown[]>;
}

const ALLOWED_SORT = ["created_at", "amount", "status"];

// 輔助函式：測試跨函式追蹤（CodeQL Global 必須能追進來）
function executeOrderQuery(pool: DbPool, sortExpr: string, tenantId: string) {
  const sql = "SELECT id, amount FROM settlements WHERE tenant_id = $1 ORDER BY " + sortExpr;
  return pool.query(sql, [tenantId]);
}

export async function listSettlementsVuln(req: Request, pool: DbPool) {
  // [TP-1: SQLi] 未檢核 req.query.sort 跨函式流入 executeOrderQuery 第 0 引數
  const sort = req.query.sort ?? "created_at";
  return executeOrderQuery(pool, sort, req.user.tenantId);
}

export async function listSettlementsSafeParam(req: Request, pool: DbPool) {
  // [FP 測試 1: 安全參數化] req.query.status 只在第 1 個參數陣列，不在 SQL 字串
  return pool.query("SELECT id FROM settlements WHERE tenant_id = $1 AND status = $2", [
    req.user.tenantId,
    req.query.status ?? "PAID",
  ]);
}

export async function listSettlementsSafeParseInt(req: Request, pool: DbPool) {
  // [FP 測試 2: 數值轉型 Barrier]
  const limit = parseInt(req.query.limit ?? "20", 10);
  return pool.query(`SELECT id FROM settlements WHERE tenant_id = $1 LIMIT ${limit}`, [
    req.user.tenantId,
  ]);
}

export async function listSettlementsSafeAllowlist(req: Request, pool: DbPool) {
  // [FP 測試 3: 白名單 BarrierGuard]
  const sort = req.query.sort ?? "created_at";
  if (!ALLOWED_SORT.includes(sort)) {
    throw new Error("invalid sort column");
  }
  return executeOrderQuery(pool, sort, req.user.tenantId);
}

export async function getSettlementByIdBola(req: Request, pool: DbPool) {
  // [TP-2: BOLA] 僅用 params.id 查詢，遺漏 tenant_id = $2 租戶隔離條件
  return pool.query("SELECT * FROM settlements WHERE id = $1", [req.params.id]);
}

export async function getSettlementByIdSafe(req: Request, pool: DbPool) {
  // [安全對照] 同時綁定 id 與 tenant_id
  return pool.query("SELECT * FROM settlements WHERE id = $1 AND tenant_id = $2", [
    req.params.id,
    req.user.tenantId,
  ]);
}
```

接著建立底層 C 解析器 `native/tlv_parser.c` 與 `native/Makefile`，裡面放了一個先做 `hdr->len + 8U` 再檢查上限的溢位漏洞版 `parse_tlv_vuln`（當 `len = 0xFFFF_FFF8` 時回繞為 `0`），以及一個先檢查 `payload_len > NEXUS_MAX_PAYLOAD` 的安全版 `parse_tlv_safe`：

```c
// native/tlv_parser.c
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

#define NEXUS_MAX_PAYLOAD 65536U

typedef struct {
    uint16_t magic;
    uint16_t type;
    uint32_t len;
} tlv_hdr_t;

// [TP-3: C FFI 長度溢位] 先做 hdr->len + 8 再比對上限，當 len = 0xFFFF_FFF8 時 sz 回繞為 0
uint8_t *parse_tlv_vuln(const tlv_hdr_t *hdr, const uint8_t *payload) {
    uint32_t sz = hdr->len + 8U;
    if (sz > NEXUS_MAX_PAYLOAD + 8U) {
        return NULL;
    }
    uint8_t *buf = (uint8_t *)malloc(sz);
    if (!buf) return NULL;
    memcpy(buf, payload, hdr->len); // 大規模堆積越界寫入
    return buf;
}

// [安全對照] 先檢查原始 hdr->len 不超過 65,536 bytes 再做加法
uint8_t *parse_tlv_safe(const tlv_hdr_t *hdr, const uint8_t *payload) {
    uint32_t payload_len = hdr->len;
    if (payload_len == 0 || payload_len > NEXUS_MAX_PAYLOAD) {
        return NULL;
    }
    uint32_t sz = payload_len + 8U;
    uint8_t *buf = (uint8_t *)malloc(sz);
    if (!buf) return NULL;
    memcpy(buf + 8, payload, payload_len);
    return buf;
}
```

```makefile
# native/Makefile
CC ?= cc
CFLAGS = -O2 -Wall -c

all: tlv_parser.o

tlv_parser.o: tlv_parser.c
	$(CC) $(CFLAGS) $< -o $@

clean:
	rm -f *.o
```

### 步驟 2：撰寫 2 條 Semgrep 規則與 1 支 CodeQL 查詢並執行驗證

請在 `rules/semgrep/nexuspay-rules.yaml` 寫下兩條 Semgrep 規則：第一條抓查詢 `settlements` 表卻漏寫 `tenant_id` / `merchant_id` 的 BOLA 破口；第二條用 `mode: taint` 抓 `native/tlv_parser.c` 的未檢核長度加法溢位。

接著在 `rules/codeql/` 下建立 `qlpack.yml` 與 `NexusLabSql.ql`，實作我們前面推導過的跨函式 SQLi `TaintTracking` 查詢，建立 `--db-cluster` 雙語言資料庫並跑出 SARIF 結果。

### 外部靶場對照檢查點（GitHub Security Lab CTF / CodeQL 公開靶場）

本地這 3 條規則跑通後，如果你想挑戰在真實大型開源專案（如 Linux 核心、glibc、熱門 Node.js 套件）的歷史快照上用 CodeQL 挖出真實 CVE，推薦到 **GitHub Security Lab CTF**（https://securitylab.github.com/ctf/ ）免費公開題庫練習。你可以挑一道 JavaScript 或 C/C++ 的真實歷史漏洞題，從 Patch 反推 `isSource`、`isSink` 與 `isBarrier`，體驗一下研究員是怎麼靠一支幾十行的 `.ql` 查詢在龐大程式碼庫裡精準揪出 0-day 的。

---

### 參考解答

#### 1. 步驟 2 Semgrep 雙規則設定檔與執行結果

建立 `rules/semgrep/nexuspay-rules.yaml`：

```yaml
rules:
  - id: nexuspay-bola-missing-tenant-where
    languages: [typescript, javascript]
    severity: WARNING
    message: >-
      查詢 settlements 資料表時未在 SQL WHERE 條件中納入 tenant_id / merchant_id 隔離欄位，
      有跨租戶 BOLA 風險。
    patterns:
      - pattern: $POOL.query($SQL, ...)
      - metavariable-regex:
          metavariable: $SQL
          regex: (?i).*FROM\s+settlements\b.*WHERE\b(?!.*(?:tenant_id|merchant_id)).*

  - id: nexuspay-c-tlv-len-unchecked-add
    languages: [c]
    severity: ERROR
    mode: taint
    message: >-
      TLV 標頭長度 hdr->len 未先驗證 <= 65536 即參與加法並傳入 malloc/memcpy，
      有整數溢位回繞風險。
    pattern-sources:
      - pattern: $HDR->len
    pattern-sanitizers:
      - patterns:
          - pattern: |
              if ($X == 0 || $X > 65536U) { return ...; }
          - focus-metavariable: $X
        by-side-effect: true
      - patterns:
          - pattern: |
              if ($X > NEXUS_MAX_PAYLOAD) { return ...; }
          - focus-metavariable: $X
        by-side-effect: true
    pattern-sinks:
      - patterns:
          - pattern: malloc($SZ)
          - focus-metavariable: $SZ
      - patterns:
          - pattern: memcpy($DST, $SRC, $SZ)
          - focus-metavariable: $SZ
```

執行 Semgrep 掃描：

```bash
semgrep --config rules/semgrep/nexuspay-rules.yaml .
```

你會看到輸出剛好命中兩處真漏洞、且零誤報：
- `nexuspay-bola-missing-tenant-where` 精準抓到 `api/settlement.ts` 裡漏寫 `tenant_id` 的 `getSettlementByIdBola`，並放過有加 `AND tenant_id = $2` 的 `getSettlementByIdSafe`。
- `nexuspay-c-tlv-len-unchecked-add` 精準抓到 `native/tlv_parser.c` 裡 `parse_tlv_vuln` 的 `malloc(sz)` 與 `memcpy(buf, payload, hdr->len)`，而底下的 `parse_tlv_safe` 因為在加法前先通過了 `payload_len > NEXUS_MAX_PAYLOAD` 守衛，被 `by-side-effect: true` 自動淨化而不誤報。

#### 2. 步驟 2 CodeQL 查詢包與跨函式 SQLi 查詢

建立 `rules/codeql/qlpack.yml` 與 `rules/codeql/NexusLabSql.ql`：

```yaml
# rules/codeql/qlpack.yml
name: nexuspay/variant-lab-queries
version: 0.0.1
dependencies:
  codeql/javascript-all: "*"
```

```ql
// rules/codeql/NexusLabSql.ql
/**
 * @name NexusPay Lab SQL Injection (Cross-Function)
 * @kind path-problem
 * @problem.severity error
 * @id nexuspay/lab-ts-sqli
 */

import javascript

class LabAllowlistGuard extends DataFlow::CallNode {
  LabAllowlistGuard() {
    this.getMethodName() = "includes" and
    this.getNumArgument() = 1
  }

  predicate blocksExpr(Expr e, boolean outcome) {
    outcome = true and
    e = this.getArgument(0).asExpr()
  }
}

module LabSqlConfig implements DataFlow::ConfigSig {
  predicate isSource(DataFlow::Node source) {
    exists(DataFlow::PropRead pr |
      pr.getPropertyName() in ["query", "params", "body"] and
      source = pr
    )
    or
    exists(DataFlow::PropRead inner, DataFlow::PropRead outer |
      outer.getPropertyName() in ["query", "params", "body"] and
      inner.getBase() = outer and
      source = inner
    )
  }

  predicate isSink(DataFlow::Node sink) {
    exists(DataFlow::MethodCallNode call |
      call.getMethodName() = "query" and
      sink = call.getArgument(0)
    )
  }

  predicate isBarrier(DataFlow::Node node) {
    exists(DataFlow::CallNode c |
      c.getCalleeName() in ["parseInt", "Number"] and
      node = c
    )
    or
    node = DataFlow::MakeBarrierGuard<LabAllowlistGuard>::getABarrierNode()
  }
}

module LabSqlFlow = TaintTracking::Global<LabSqlConfig>;
import LabSqlFlow::PathGraph

from LabSqlFlow::PathNode source, LabSqlFlow::PathNode sink
where LabSqlFlow::flowPath(source, sink)
select sink.getNode(), source, sink,
  "Unsanitized input from $@ flows to SQL command string.",
  source.getNode(), "request input"
```

#### 3. 建置多語言資料庫叢集並驗證 `100%` 精準度

依序執行下面四道指令：

```bash
# 1. 安裝查詢包依賴
codeql pack install rules/codeql

# 2. 一次建置 TypeScript + C 雙語言資料庫叢集
codeql database create build/nexus-dbs \
  --db-cluster \
  --language=javascript,cpp \
  --source-root=. \
  --command="make -C native clean all" \
  --overwrite

# 3. 針對 javascript 資料庫執行客製 SQLi 查詢並輸出 SARIF
codeql database analyze build/nexus-dbs/javascript \
  rules/codeql/NexusLabSql.ql \
  --format=sarif-latest \
  --output=build/sql-results.sarif

# 4. 印出命中位置（應只有 listSettlementsVuln -> executeOrderQuery 一條路徑）
python3 -c '
import json
data = json.load(open("build/sql-results.sarif"))
for r in data["runs"][0]["results"]:
    loc = r["locations"][0]["physicalLocation"]
    print(r["ruleId"], loc["artifactLocation"]["uri"], loc["region"]["startLine"])
'
```

最後這段 Python 腳本只會印出唯一一筆結果：指向 `api/settlement.ts` 的 `executeOrderQuery`。它不僅成功跨越函式追到了 `listSettlementsVuln` 傳進來的 `req.query.sort`，還同時排除了 `listSettlementsSafeParam`、`listSettlementsSafeParseInt` 與 `listSettlementsSafeAllowlist` 三個安全寫法，在實驗集上達成 `TP = 1, FP = 0, FN = 0`（Precision = `100%`、Recall = `100%`）。

---

## 自我檢核

- **難度**：進階
- **預估時間**：20 分鐘

先別往下看答案，試著自己推導並算出下面 4 個問題：

1. **CFG 支配關係與假防禦識破**：有位工程師在修補報表匯出 API 時寫了這段程式碼：
   ```ts
   const dir = String(req.query.dir ?? "ASC");
   if (!["ASC", "DESC"].includes(dir)) {
     metrics.increment("invalid_sort_dir_attempt");
   }
   await pool.query(`SELECT * FROM invoices ORDER BY created_at ${dir}`);
   ```
   請問如果我們用前面寫好的 CodeQL `MakeBarrierGuard`（設定 `outcome = true`）去掃這段程式碼，CodeQL 會把它當成「已安全淨化」放過，還是會照常抓出 SQL 注入漏洞？為什麼？如果有人偷懶只用純 AST 規則寫「只要函式裡有出現 `.includes(dir)` 就不報警」，會發生什麼慘劇？
2. **Precision、Recall、F1 與誤報消除率實算**：資安團隊寫了一支抓 SSRF 的初版 CodeQL 查詢，去掃公司內部的微服務，一共跳出 **`60` 筆警報**；人工逐一檢查後，發現裡面只有 **`10` 筆是真漏洞**，另外 **`50` 筆全是誤報**；更慘的是，紅隊演練已知還有 **`2` 個真漏洞**因為走了一層自訂的 `httpProxy.forward()` 包裝函式而沒被抓到。接著團隊補上了 `isAdditionalFlowStep` 跟網址白名單 `isBarrier`，重跑一次新版查詢：這次總共只跳出 **`15` 筆警報**，而且把 **`12` 個真漏洞**全數抓齊了。請算出初版與新版的 **Precision**、**Recall**、**F1 Score**，以及新版消除了百分之多少的誤報？
3. **C FFI 有號轉型怎麼騙過粗糙的 `isBarrier`**：看看底下這段 `libnexus-parse` 的 C 程式碼：
   ```c
   int32_t chunk_len = (int32_t)hdr->len; // hdr->len 是 32 位元無號整數 uint32_t
   if (chunk_len <= 65536) {
       uint8_t *buf = malloc((size_t)chunk_len + 8);
       memcpy(buf, src, hdr->len);
   }
   ```
   當攻擊者送來一個 `hdr->len = 0xFFFF_FFF8` 的封包時，第一行轉型後的 `chunk_len` 十進位數值是多少？第三行傳給 `malloc` 的大小算出來會變成多少？為什麼如果靜態規則把單邊的 `chunk_len <= 65536` 無條件當成 Sanitizer Barrier，就會漏掉這個致命漏洞？
4. **大規模變體狩獵的工具分工**：某開源認證套件剛爆出一個跨兩層檔案（先在 `parseToken()` 解開欄位，再傳給另一個檔案的 `verifySignature()` 執行危險操作）的嚴重 CVE。你現在要幫公司快速檢查 GitHub 上 250 個下游開源專案有沒有人複製貼上了這段有洞的程式碼。為什麼這時候「只跑單機版 Semgrep OSS」或「一開始就幫 250 個專案全部建 CodeQL 資料庫」都不是好主意？最有效率的兩階段組合拳該怎麼打？

---

### 參考解答

1. **CFG 支配關係與假防禦識破**：
   - CodeQL 的 `MakeBarrierGuard` 會**精準抓出這題是真漏洞（TP）**！因為在 `if (!["ASC", "DESC"].includes(dir))` 的區塊裡，工程師只呼叫了 `metrics.increment(...)`，根本沒有 `return` 或 `throw`。在 CFG 控制流圖上，當輸入不在白名單內時，程式跑完 `if` 區塊又會合流回主幹道繼續執行 `pool.query(...)`。這代表 `["ASC", "DESC"].includes(dir) == true` 這個條件並沒有**支配**（Dominate）底下的 `pool.query` 節點，污點依然暢行無阻。
   - 如果偷懶只用 AST 檢查「函式內有沒有出現 `.includes(dir)`」，掃描器就會被這行不痛不癢的 `metrics.increment` 騙過去，直接釀成致命的漏報（False Negative）。

2. **精準度指標與誤報消除率實算**：
   - **初版查詢**：
     - `TP = 10`、`FP = 50`、`FN = 2`（實際真漏洞總數為 `10 + 2 = 12` 個）。
     - **Precision** = `10 / 60 = 16.67%`
     - **Recall** = `10 / 12 = 83.33%`
     - **F1 Score** = `2 × (10/60) × (10/12) / (10/60 + 10/12) = 20 / 72 = 27.78%`
   - **新版查詢**：
     - 總警報 `15` 筆，其中 `TP = 12`、剩餘誤報 `FP = 15 - 12 = 3`、`FN = 0`。
     - **Precision** = `12 / 15 = 80.00%`
     - **Recall** = `12 / 12 = 100.00%`
     - **F1 Score** = `2 × 0.80 × 1.00 / (0.80 + 1.00) = 1.60 / 1.80 = 88.89%`
   - **誤報消除率**：
     - `(50 - 3) / 50 = 47 / 50 = 94.00%`（砍掉了高達九成四的誤報，同時把原本漏掉的 2 個跨函式漏洞也抓了回來）。

3. **有號轉型數值與 Unsound Barrier 解析**：
   - 在二補數整數表示下，無號的 `0xFFFF_FFF8`（`4,294,967,288`）最高位元是 `1`，強制轉成有號 32 位元整數 `int32_t` 後，十進位數值會變成 **`-8`**（`4,294,967,288 - 2^32 = -8`）。
   - 接著走進 `if (-8 <= 65536)`，負數當然小於 `65536`，當場過關！到了第三行 `(size_t)chunk_len + 8`，`-8` 先符號擴展成 64 位元的 `0xFFFF_FFFF_FFFF_FFF8`，再加上 `8` 剛好溢位回繞成 **`0`**。結果程式執行了 `malloc(0)` 只拿到一塊合法可寫容量為 `0 bytes` 的極小指標，下一行 `memcpy` 卻直接拿無號的 `hdr->len`（高達 `4,294,967,288 bytes`）硬塞進去，瞬間寫穿堆積。
   - 如果靜態規則的 `isBarrier` 只看單邊的 `<= 65536`，卻沒要求變數必須是無號整數（`uint32_t` / `size_t`）或必須同時檢查下界 `> 0`，就會把這個負數繞過漏洞誤判為已安全過濾而漏報。

4. **大規模變體狩獵的兩階段組合拳**：
   - **為什麼不能只靠單機版 Semgrep OSS**：因為開源版 Semgrep 的污點追蹤只看單一檔案內部，遇到這種 `parseToken()` 跟 `verifySignature()` 分屬兩個不同檔案的跨檔攻擊鏈，一定會斷鏈漏抓。
   - **為什麼不能一開始就建 250 個 CodeQL 資料庫**：幫 250 個專案從頭建立 CodeQL 資料庫非常花時間與硬碟空間，而裡面可能九成以上的專案根本沒用到那個危險函式。
   - **最佳兩階段打法**：第一階段先用不用編譯的 **Semgrep AST 搜尋模式**當快速篩網，花幾分鐘在 250 個專案裡掃出「同時含有特徵結構與目標危險 API 呼叫」的少數候選者（比如縮小到 15 個專案）；第二階段再只針對這 15 個高度可疑的專案建置 **CodeQL 資料庫**，跑跨檔案的 `TaintTracking::Global` 確認髒資料是不是真的能從入口一路流進 Sink。

---

## 延伸閱讀

- **CodeQL 官方文件 — *Analyzing Data Flow in JavaScript/TypeScript* 與 *C/C++***（https://codeql.github.com/docs/codeql-language-guides/analyzing-data-flow-in-javascript-and-typescript/）：完整講解現代 `DataFlow::ConfigSig`、`TaintTracking::Global`、`MakeBarrierGuard` 以及多語言 `--db-cluster` 資料庫的操作細節。
- **Semgrep 官方文件 — *Taint Analysis* 與 *Rule Writing Guide***（https://semgrep.dev/docs/writing-rules/data-flow/taint-mode/）：深入說明 `mode: taint`、`focus-metavariable`、`by-side-effect` Sanitizer 與 `pattern-propagators` 的實戰寫法。
- **GitHub Security Lab — *Variant Analysis Research & CTF***（https://securitylab.github.com/research/ 與 https://securitylab.github.com/ctf/）：收錄大量頂尖研究員如何從單一真實 CVE 寫出 CodeQL 查詢、在開源生態系橫向挖出整串 0-day 的實戰案例與練習題。
- **Anders Møller & Michael I. Schwartzbach — *Static Program Analysis***（https://cs.au.dk/~amoeller/spa/）：想把 CFG 支配樹、Lattice 不動點演算法、SSA 轉換與指標分析（Pointer Analysis）底層數學徹底搞懂的經典免費開源教材。
- **OASIS SARIF v2.1.0 規範**（https://docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.html）：了解如何把 Semgrep 與 CodeQL 掃出來的結果統一轉成標準 SARIF 格式，串進 GitHub Advanced Security 或自建的 CI/CD 分流平台。
