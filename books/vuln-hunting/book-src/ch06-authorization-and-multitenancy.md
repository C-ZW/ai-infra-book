# 第 6 章：授權模型崩壞：BOLA、BFLA 與多租戶隔離失效

身分驗證（Authentication）解決的是「你是誰」，授權（Authorization）解決的則是「你能不能對這個資源做這個動作」。在日常寫 NestJS 或 Express 的時候，這兩件事常常被塞進同一個 Guard 或 Middleware 裡：只要 RS256 JWT 的數位簽章驗過了、有效期（`900 s`）還沒到，`req.user` 順利掛上了 `userId` 跟 `tenantId`，請求就被放進 Controller 裡面了。

真正的災難往往就發生在放行之後。驗證失敗頂多是把沒登入的路人擋在門外；但授權一漏，卻是讓已經握有合法登入憑證的一般商戶或低權限操作員，直接在系統裡面橫著走——偷看別家商戶的帳本、自己幫自己把交易手續費改成零、甚至直接呼叫平台管理員專用的結算介面。

這也是為什麼 OWASP API Security Top 10:2023 會把 **BOLA**（API1，物件層級授權失效，也就是常說的 IDOR）、**BOPLA**（API3，物件屬性層級授權失效）與 **BFLA**（API5，功能層級授權失效）高掛在前五名。自動化掃描器看不懂商業規則，而工程師手寫的每一條 SQL、ORM 查詢與 DTO 綁定，只要漏寫一個條件就是一個大洞。

---

## 從你已知的出發

為什麼資料庫明明已經打開了 PostgreSQL 16 的 **Row-Level Security（RLS，列級安全策略）**，規定 `tenant_id = current_setting('app.current_tenant_id')::bigint`，按理說資料庫引擎會在每一條 SQL 執行計畫裡自動幫你鎖死租戶範圍，結果線上還是發生了租戶 B 偷看到租戶 A 帳戶餘額、甚至把自己的結算手續費率偷改成 `0` 的資安事故？

因為 RLS 的保護傘，只罩得住「真的走進了 PostgreSQL、而且受到策略管轄的那幾列（Row）資料」。只要你在資料庫前面擋了一層只寫 `account:${aid}` 卻漏拼 `tid` 的 Redis 快取（快取命中時根本沒進 PostgreSQL），或是在 PgBouncer 連線池（transaction pooling 模式）裡誤用了會殘留在實體連線上的 `SET` 而非隨交易清空的 `SET LOCAL`，RLS 就完全使不上力。更別提 RLS 只管「你能看到哪幾列」，根本不管「你能透過 JSON 偷改同一列裡面的哪幾個敏感欄位」（BOPLA），也不管「你的角色能不能呼叫這支管理員 API」（BFLA）。

---

## 機制與推導

### 攻擊者目標與實質影響

一旦多租戶系統的授權防線出現裂縫，攻擊者連半個密碼學漏洞都不用找，光靠手上那張合法註冊拿到的普通帳號憑證，就能造成三種直接重擊：

第一是**跨租戶偷看與盜領資金**。利用 BOLA（IDOR）或 BOPLA，攻擊者只要改一下網址上的帳戶編號、或在更新請求裡多塞兩個 JSON 欄位，就能看光別家商戶的私密交易明細，甚至直接把別人的帳戶餘額提領一空，或是把自己的平台手續費率歸零。

第二是**越級執行平台管理員功能**。透過 BFLA 找出忘了掛角色檢查的管理端點，一般商戶操作員就能直接呼叫平台營運專用的費率覆寫或帳務重設 API，完成垂直權限提升。

第三則是**為後續的深層攻擊鋪路**。當攻擊者透過授權破口蒐集到其他租戶的內部資源 UUID 與帳戶狀態後，就能拿這些情報去串接更複雜的業務邏輯與併發雙花漏洞（見第 12 章），或是把髒資料塞進後台的報表解析管線（見第 9 章）。

---

### 拆解授權四元組與三大破口（API1 / API3 / API5）

不管你的系統用的是 RBAC（角色權限）、ABAC（屬性權限）還是獨立的政策引擎，後端每一次決定「這筆請求准不准過」，骨子裡都是在核對四件事——也就是**授權四元組**：

```text
Decision = Policy(Subject, Action, Object, Context)
```

這裡的 **Subject** 是從已驗證憑證（像 JWT 或 Session）解出來的呼叫者身分 `{ userId, tenantId, roles, scopes }`；**Action** 是他想做的動作（例如 `PATCH /v1/tenants/:tid/accounts/:aid` 或 `POST /v1/admin/tenants/:tid/fee-override`）。

而 **Object** 是他要動的那筆資源實體以及裡面的欄位（例如帳戶 `aid = 1001` 與它的 `{ balance, isVerified, feeRate }`）；最後的 **Context** 則是當下的環境條件（例如「這筆操作是否已經通過了第 5 章講的 Step-Up MFA」）。

只要後端程式碼在核對這四元組時漏掉了其中一條連線，就會精準對應到 OWASP API Security Top 10:2023 的三大授權漏洞（當然，一支寫壞的 API 完全可能同時中兩三槍）：

| 漏洞類別 | OWASP API 2023 | 到底漏核對了哪裡 | 後端最常寫出的危險程式碼 |
|---|---|---|---|
| **BOLA**（物件層級授權失效） | API1 | 沒核對 `Subject` 是不是真的擁有那個 `Object`（`owner / tenant_id`） | Controller 收了網址上的 `:aid`，Service 直接 `findUnique({ where: { id: aid } })` |
| **BOPLA**（物件屬性層級授權失效） | API3 | 沒核對 `Subject` 能不能讀或寫 `Object` 裡面的特定欄位（`fields`） | 讀：`res.json(entity)` 把整列資料庫物件直接吐回去；寫：`Object.assign(entity, req.body)` 照單全收 |
| **BFLA**（功能層級授權失效） | API5 | 沒核對 `Subject.roles` 夠不夠格執行這個 `Action` | 只在 Gateway 檢查「有登入就好」，卻忘了在管理端點掛上 `@Roles('platform_admin')` |

這裡特別提一下 **BOPLA**。在 2023 版的 OWASP API Top 10 裡，它把以前 2019 版分開列的兩個漏洞合體了。

**寫入面**就是大家熟知的 **Mass Assignment**（大量賦值，以前叫 API6），讓攻擊者自己塞 JSON 欄位去改掉原本不該由前端控制的 `isVerified`、`feeRate` 或 `role`；**讀取面**則是 **Excessive Data Exposure**（過度資料暴露，以前叫 API3），後端圖方便把整張表查出來的機密欄位全塞進 JSON 回傳，天真地靠前端 React 畫面「不顯示那幾個欄位」當作防線。

---

### BOLA 是怎麼發生的：只驗了網址上的租戶，卻沒綁死查詢條件

來看 **NexusPay** 最核心的多租戶帳本路由。每家商戶都有自己的 `tenant_id`，底下可以開多個結算帳戶 `account_id`，查詢帳戶的 API 長這樣：

```text
GET /v1/tenants/:tid/accounts/:aid
```

很多工程師看到網址上有 `:tid`，就寫了一個 `TenantMatchGuard` 去檢查「JWT 裡面的 `user.tenantId` 是不是等於網址上的 `params.tid`」，檢查通過就覺得高枕無憂了。卻沒想到下面這段 Controller 與 Service 程式碼還是留了一個大洞：

```typescript
// 漏洞示範：Guard 只核對了網址上的 params.tid，Service 查資料庫時卻只傳了 aid！
@Get('tenants/:tid/accounts/:aid')
@UseGuards(JwtAuthGuard, TenantMatchGuard)
async getAccount(@Param('aid') aid: string) {
  // 攻擊者乖乖填自己的 tid=1002 騙過 Guard，卻把後面的 aid 換成租戶 1001 的帳戶編號
  return this.accountRepo.findOne({ where: { id: aid } });
}
```

看出問題在哪了嗎？這叫做**驗證參數與查詢參數脫鉤**（Parameter Desync）。

`TenantMatchGuard` 確實盡責地檢查了網址前半截的 `:tid` 是不是攻擊者自己的租戶 `1002`；但進到 `getAccount` 之後，ORM 撈資料庫時卻只寫了 `where: { id: aid }`，把剛剛驗過的 `tid` 丟在一邊根本沒用！

只要系統裡的 `account_id` 是全域唯一的（不管是流水號，還是會從對帳單、Webhook、報錯訊息裡露出去的 UUIDv4），攻擊者只要在網址前半截填自己的 `tid = 1002` 通過警衛檢查，後半截的 `:aid` 填受害租戶 `1001` 的帳戶 ID，就能直接把別人的帳戶明細與 `10,000` 分（`$100.00`）測試餘額看光光。如果連提領端點 `POST /v1/tenants/:tid/accounts/:aid/withdraw` 在扣款時也犯了一樣的錯，那更是直接把別家商戶的錢領進自己口袋。

除了主路由之外，BOLA 最愛躲的另一個角落是**附屬功能與批次介面**。團隊常常把主要的 `/accounts/:aid` 修得密不透風，補上了 `WHERE id = $1 AND tenant_id = $2`；結果旁邊匯出 CSV 報表的 `/ledger/export?accountId=...`、重送通知的 `/webhooks/:wid/retry`，或是第 7 章會講到的 GraphQL 巢狀關聯 Resolver，卻還是傻傻地只拿單一 ID 去查表，讓整道防線從側門被突破。

---

### BOPLA 是怎麼發生的：以為 TypeScript 型別會在執行期保護你

在使用 NestJS 搭配 TypeORM 或 Prisma 的 Node.js 專案裡，最常捅出 BOPLA 簍子的，就是下面這種看起來超乾淨的寫法：

```typescript
// 漏洞示範：沒掛任何執行期白名單裝飾器的 DTO，直接丟給 ORM 更新
export class UpdateAccountDto {
  displayName?: string;
  webhookUrl?: string;
}

@Patch('tenants/:tid/accounts/:aid')
async updateAccount(
  @Param('tid') tid: number,
  @Param('aid') aid: number,
  @Body() dto: UpdateAccountDto,
) {
  // 注意：TypeScript 的型別在編譯成 JS 後就人間蒸發了！
  return this.accountRepo.update({ id: aid, tenantId: tid }, dto as any);
}
```

很多剛轉寫 TypeScript 的工程師會有一個致命誤會：「我明明在 `UpdateAccountDto` 裡面只寫了 `displayName` 跟 `webhookUrl` 兩個欄位，前端多傳別的欄位進來應該會被自動忽略吧？」

完全不會！**TypeScript 的介面與型別檢查，在編譯成 JavaScript 的那一刻就徹底消失了。**

如果你在執行期（Runtime）沒有打開 NestJS `ValidationPipe` 的 `whitelist: true`（而且在 DTO 屬性上乖乖掛上 `class-validator` 裝飾器作為白名單依據），也懶得在 Service 裡手動挑出允許的兩個欄位，那當攻擊者在 JSON 裡送出 `{"displayName": "ShopA", "isVerified": true, "feeRate": 0}` 時，執行期的 `dto` 物件裡就會原封不動躺著 `isVerified: true` 跟 `feeRate: 0`。一旦底層的 Account Entity 剛好有這兩個欄位，TypeORM 的 `.update()` 就會老老實實幫攻擊者拼出 `SET "isVerified" = true, "feeRate" = 0` 的 SQL 送進資料庫！

反過來看**讀取端**也是一樣的道理。如果資料庫 Entity 上的機密欄位（像內部風險評分 `internalRiskScore`、結算密鑰 `settlementSecret`、審核備註 `kycNotes`）沒有設為預設不選取（`select: false`），Controller 又偷懶直接 `return await this.accountRepo.findOne(...)`，整列資料的所有欄位就會一字不漏地被轉成 JSON 吐回給瀏覽器。就算前端畫面沒把這些欄位畫出來，攻擊者只要打開瀏覽器開發者工具（F12）看一眼 Network 回應，所有機密就手到擒來。

---

### BFLA 是怎麼發生的：方法混淆、路徑變形與角色錯覺

至於一般商戶為什麼能呼叫管理員專用的 API（BFLA）？在真實專案裡，很少是因為工程師完全忘了寫權限系統，絕大多數都是栽在下面三種架構落差上：

第一種是 **HTTP 方法只鎖了一半**。開發者在路由上替 `GET /v1/admin/users` 掛了嚴格的管理員檢查，結果旁邊處理新增或刪除的 `POST`、`DELETE` 卻漏掛了 Guard；或是後端框架開了支援 `X-HTTP-Method-Override` 標頭的功能，讓攻擊者用外層放行的 `POST` 請求夾帶 `X-HTTP-Method-Override: DELETE` 偷渡進去。

第二種是**外層代理跟內層框架對網址的看法不一樣**。比如外層的中介層寫了一行區分大小寫、又沒先做路徑正規化的 `if (req.path.startsWith('/v1/admin'))` 來擋非管理員；結果後端的路由引擎卻是不分大小寫的（攻擊者打 `/v1/Admin` 就穿過去了），或是後端在分派路由前會先幫路徑做正規化（攻擊者打 `/v1/public/../admin` 就繞過了外層的前綴檢查）。甚至有些中介層檢查的是帶尾巴斜線的 `startsWith('/v1/admin/')`，卻漏掉了不帶斜線的 `/v1/admin` 本身（這類解析差異我們在第 14 章還會深入對決）。

第三種則是**把「租戶管理員」當成「平台管理員」**。在多租戶系統裡，一家商戶的老闆擁有 `merchant_admin` 角色，代表他可以管理「自己這家店（`tid = 1002`）」的員工與金鑰。但如果開發者在寫平台營運專用的調整手續費端點 `/v1/admin/tenants/:tid/fee-override` 時，權限檢查只粗略寫了「角色名稱裡有 admin 就放行」或誤把 `merchant_admin` 放進白名單，忘了區分這支 API 只有全平台最高權限的 `platform_admin` 才能碰，商戶老闆就能名正言順地呼叫管理端點幫自己把費率改成零。

---

### Worked Example：4 角色 × 6 資源端點授權矩陣與帳本損失推導

現在我們把 NexusPay 多租戶帳本的 **4 個日常角色 × 6 支核心 API 端點**（外加專職管理整個平台的 `platform_admin`）攤開成一張完整的授權矩陣，並用全書統一的基準參數，實際算一遍當 BOLA、BOPLA 與 BFLA 被串在一起時，會在 `900 s`（15 分鐘）內造成多驚人的財務窟窿：

```text
================================================================================
NexusPay 授權矩陣實例（4 角色 × 6 端點）
基準規格（依 _meta/running-examples.md）：
- 單戶測試餘額 = 10,000 分（$100.00）；單次提領上限 = 10,000 分（$100.00）
- JWT Access Token（RS256）有效期 = 900 s（15 分鐘）；併發尖峰 = 2,000 req/s
本例情境假設：標準結算手續費率 feeRate = 0.025（250 bps = 2.50%）
================================================================================

角色定義（另設平台最高權限角色 platform_admin，僅限呼叫 E5 等營運管理端點）：
  R1: merchant_viewer   （租戶唯讀角色：可檢視同租戶帳戶明細與匯出唯讀報表）
  R2: merchant_operator （租戶一般操作員：可查詢同租戶帳戶與匯出報表、修改帳戶 displayName 與設定 webhookUrl，不可提領/改費率）
  R3: merchant_admin    （租戶管理員：可管理同租戶帳戶、提領與金鑰）
  R4: platform_auditor  （平台稽核員：跨租戶唯讀，嚴禁任何寫入或金鑰操作）

端點預期授權矩陣（Allow = 允許同租戶/合法範圍；Deny = 應拒絕存取，依 API 語意回傳 403 / 404 / 400）：
+----+----------------------------------------------+------+------+------+------------+
| ID | 端點                                         | R1   | R2   | R3   | R4         |
+----+----------------------------------------------+------+------+------+------------+
| E1 | GET    /v1/tenants/:tid/accounts/:aid        | Allow| Allow| Allow| Allow(跨租戶)|
| E2 | PATCH  /v1/tenants/:tid/accounts/:aid        | Deny | Allow*|Allow*| Deny       |
| E3 | POST   /v1/tenants/:tid/accounts/:aid/withdraw| Deny| Deny | Allow| Deny       |
| E4 | GET    /v1/tenants/:tid/ledger/export        | Allow| Allow| Allow| Allow(跨租戶)|
| E5 | POST   /v1/admin/tenants/:tid/fee-override   | Deny | Deny | Deny | Deny       |
| E6 | DELETE /v1/tenants/:tid/api-keys/:kid        | Deny | Deny | Allow| Deny       |
+----+----------------------------------------------+------+------+------+------------+
* E2 僅允許修改 displayName 與 webhookUrl，嚴禁修改 isVerified 與 feeRate；E5 僅允許矩陣外的 platform_admin 呼叫。

實測破口與情境數值推導：
1) BOPLA（Mass Assignment）於 E2：
   攻擊者以 R2（tid = 1002, aid = 2001）送出：
   PATCH /v1/tenants/1002/accounts/2001
   Body: {"displayName": "AttackShop", "isVerified": true, "feeRate": 0}
   - 單筆結算金額 = 10,000 分（$100.00）
   - 正常手續費   = 10,000 × 0.025 = 250 分（$2.50），淨撥款 = 9,750 分（$97.50）
   - 竄改後手續費 = 10,000 × 0     =   0 分（$0.00），淨撥款 = 10,000 分（$100.00）
   - 單筆平台手續費損失 = 250 分（$2.50）
   情境估算：假設攻擊者商戶在單一 JWT 有效期（900 s）內以 100 req/s（佔系統尖峰 2,000 req/s 的 5%）
   持續完成每筆 10,000 分的自動結算：
   - 總結算筆數 = 100 req/s × 900 s = 90,000 筆
   - 總手續費漏損估算 = 90,000 × 250 分 = 22,500,000 分 = $225,000.00

2) BOLA（跨租戶參數替換）於 E1 + E3（假設 E3 提領服務同樣僅以 aid 查表而未檢核 tenant_id）：
   攻擊者以 R3（merchant_admin）帶自身 tid = 1002 通過 TenantMatchGuard，將 aid 替換為受害租戶
   帳戶 ID（如從公開發票或 E4 過度暴露中取得）。
   - 情境估算：若成功枚舉並提領 500 個測試帳戶，每戶觸及單次提領上限 10,000 分（$100.00）：
   - 帳本直接盜領估算 = 500 × 10,000 分 = 5,000,000 分 = $50,000.00

3) BFLA 於 E5：
   E5 原僅限 platform_admin 呼叫，但實作僅掛載 @UseGuards(JwtAuthGuard) 而缺少角色授權檢查。
   R2（merchant_operator）直接送出 POST /v1/admin/tenants/1002/fee-override
   若後端直接覆寫該租戶費率並回傳 200 OK，即構成功能層級越權，產生與 E2 相同的手續費歸零風險（與 E2 屬於同一費率歸零效果的替代攻擊路徑，不重複累加損失）。
```

看完這張表跟算式，你就能明白為什麼在金流與多租戶 SaaS 系統裡，授權破口永遠是頭號大敵：攻擊者連半行密碼學或底層記憶體都不用碰，光是拿一張合法的普通 JWT，在一張 Token 短短 `900 s` 的壽命裡，就能靠 BOPLA（或 BFLA）白嫖走平台 `$225,000.00` 的手續費，或是靠 BOLA 直接從 500 個別家帳戶裡搬走 `$50,000.00` 的現金。

---

## 故障模式與防禦

在真實的後端架構裡，只靠「提醒大家寫 Controller 時記得加 `if`」是絕對守不住多租戶邊界的。我們必須把下面三個最常出事的架構盲點一次堵死。

### 故障模式 1：快取鍵漏帶 `tenant_id` 與連線池的租戶狀態殘留

為了撐住每秒 `2,000 req/s` 的尖峰流量，我們一定會把常查的帳戶資料放進 Redis 7。這時候如果快取鍵偷懶寫成 `acct:${aid}`，而不是把租戶編號一起綁進去的 `tenant:${tid}:acct:${aid}`（而且從快取拿出來後也沒再核對一次 `tenantId`），那只要租戶 A 先查過一次帳戶、資料進了 Redis，下一秒租戶 B 帶著同一個 `aid` 來查，就會直接從 Redis 命中並拿走租戶 A 的資料——你精心設計的 PostgreSQL RLS 連被呼叫的機會都沒有！

更陰險的坑出在 **PostgreSQL RLS 遇上 PgBouncer 連線池（transaction pooling 模式）** 的時候。看看下面這兩行很多人在設定租戶上下文時會寫出的 SQL：

```sql
-- 危險寫法：SET 會一直黏在這條實體連線上，直到連線斷開或被下一個人覆寫！
SET app.current_tenant_id = '1002';
SELECT * FROM accounts WHERE id = 2001;
```

當這筆查詢跑完、實體連線歸還給 PgBouncer 連線池之後，上面那個 `'1002'` 並不會自動消失！如果下一個借到這條連線的請求（比如某個背景排程或漏掛中介層的查詢）剛好沒有先執行 `SET`，它就會直接繼承上一個人留下的 `'1002'` 身分去查資料，引發神出鬼沒的跨租戶資料錯亂。

要根治這個問題，必須嚴格遵守兩條資料庫鐵律。第一，設定租戶變數時，一律包在明確的交易（Transaction）裡面，並改用交易結束就會自動清空的 **`SET LOCAL`**：

```sql
BEGIN;
SET LOCAL app.current_tenant_id = '1002';
SELECT * FROM accounts WHERE id = 2001;
COMMIT;
```

第二，確保應用程式連線用的資料庫帳號**絕對不是 Superuser**、也沒有 `BYPASSRLS` 權限，而且在資料表上開啟 RLS 時，務必兩行指令一起下：

```sql
ALTER TABLE accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE accounts FORCE ROW LEVEL SECURITY;
```

為什麼非加第二行 `FORCE ROW LEVEL SECURITY` 不可？因為 PostgreSQL 預設有一條潛規則：**這張資料表的擁有者（Table Owner）自己查表時，會自動免除 RLS 檢查！** 很多團隊跑資料庫 Migration 建表跟線上微服務查表用的是同一個資料庫帳號（也就是 Table Owner），如果只寫了 `ENABLE` 卻漏寫 `FORCE`，你寫的 RLS 策略在線上其實是整套失效的。

### 故障模式 2：到處手寫 `if` 與忘了掛 Guard 就預設放行（Fail-Open）

當系統長大到有 80 支 API 分散在十幾個 Controller 裡，如果還靠工程師在每支路由上面手動掛 `@Roles(...)` 或在函式裡手寫 `if (user.tenantId !== account.tenantId)`，那只要某天有人新增一支 API 忘了掛裝飾器，那支 API 就會預設對所有人敞開大門（Fail-Open）。

真正穩健的架構必須做到 **Deny-by-Default（預設全拒）加上集中式政策引擎（Policy Decision Point，簡稱 PDP）**：

首先，在 NestJS 全域註冊一個總管權限的 `AuthorizationGuard`，硬性規定每一支路由都必須明確貼上策略標籤（例如 `@Policy('account:read')`）；只要遇到任何沒貼標籤的路由，Guard 二話不說直接回傳 `403 Forbidden`，絕不預設放行。

接著，把散落在各處的權限判斷抽出來，交給集中的政策模組（像 Open Policy Agent、Cedar 或共用的授權核心）。政策引擎會把每次請求收斂成標準的 `{ subject, action, resource, context }` 四元組，算出一個明確的 `Allow / Deny` 布林值與允許讀寫的欄位清單（Field Mask）。

這樣做最大的好處是——你可以寫一支短短的單元測試，離線把前面那張「4 個角色 × 6 支端點」的授權矩陣全部跑過一遍，不用把整座 HTTP 伺服器跟資料庫架起來，就能在 CI/CD 階段抓出哪條規則配錯了（至於路由有沒有乖乖接上 Guard，再交給整合測試去把關）。

### 故障模式 3：相信靜態型別與把資料庫 Entity 直接吐給前端

對付 BOPLA 的讀寫雙向破口，防線必須在框架入口與資料出口同時鎖緊：

在**寫入入口**，直接在 NestJS 全域把 `ValidationPipe` 的白名單與嚴格阻擋打開：

```typescript
app.useGlobalPipes(
  new ValidationPipe({
    whitelist: true,            // 自動砍掉所有沒在 DTO 貼驗證裝飾器的多餘欄位
    forbidNonWhitelisted: true, // 只要前端敢多塞未授權欄位，直接回 400 Bad Request
    transform: true,
  }),
);
```

在**讀取出口**，則是嚴格把「輸入 DTO」、「資料庫 Entity」與「輸出回應 DTO」拆成三個獨立的類別。絕對不准把 ORM 查出來的 Entity 直接 `return` 給前端，一定要經過明確的映射函式（或用 `class-transformer` 先設 `@Exclude()` 全排除，再用 `@Expose()` 一欄一欄挑出白名單），確保像 `settlementSecret` 這種內部欄位永遠出不了後端大門。

最後在 **Service 與 Repository 層**，就算底層已經有 PostgreSQL RLS 當最後一道保險，所有資料表查詢方法的函式簽章還是要強制要求同時傳入 `(tenantId, accountId)` 雙條件（甚至在設計資料表時就直接把 `(tenant_id, id)` 設成複合主鍵或唯一索引），在應用程式層與資料庫層形成雙重鎖死（Defense in Depth）。

---

## 動手做

- **難度**：進階
- **預估時間**：45 分鐘

現在我們要在本地 Docker Compose 的 NexusPay 授權靶機上動手實戰：先寫一支自動掃描腳本，一舉抓出靶機上的 BOLA、BOPLA 與 BFLA 三個大洞；接著從 PostgreSQL RLS 與 NestJS DTO 兩頭打上修補補丁，再跑一次腳本確認漏洞全部封死；最後到 PortSwigger 靶場驗收你的實戰手感。

### 任務一：跑通授權矩陣自動化掃描腳本

我們先拿租戶 `1002` 的一般操作員（`merchant_operator`）合法登入拿到的 JWT（`TOKEN_B_OPER`），對靶機的 E1、E2、E5 三支代表性端點發動測試（完整的 CI 測試則會把 4 個角色 × 6 支端點全部跑過一輪並核對資料庫狀態）：

1. **測 BOLA（打 E1）**：拿租戶 `1002` 的 Token，網址前半截乖乖填 `/v1/tenants/1002`，後半截卻填屬於租戶 `1001` 的帳戶 `/accounts/1001`，看看能不能跨租戶偷看到別人的餘額跟機密欄位 `settlementSecret`。
2. **測 BOPLA（打 E2）**：對自己的帳戶送出 `PATCH` 更新，故意在 JSON 裡偷塞 `{"displayName": "Probe", "isVerified": true, "feeRate": 0}`，看看手續費率會不會真的被改成 `0`。
3. **測 BFLA（打 E5）**：以一般操作員身分直接打平台管理員專用的 `POST /v1/admin/tenants/1002/fee-override`，看看後端有沒有回 `403 Forbidden` 把我們擋下來。

```python
# authz_matrix_scan.py — 授權矩陣自動化驗證腳本
import httpx

BASE = "http://localhost:3000"
TOKEN_A_ADMIN = "<JWT_TENANT_1001_ADMIN>"
TOKEN_B_OPER = "<JWT_TENANT_1002_OPERATOR>"

def scan():
    with httpx.Client(base_url=BASE, timeout=5.0) as client:
        # 1. BOLA: 租戶 B 操作員帶著自己的 tid=1002，偷讀租戶 A 的帳戶 aid=1001
        r_bola = client.get(
            "/v1/tenants/1002/accounts/1001",
            headers={"Authorization": f"Bearer {TOKEN_B_OPER}"},
        )
        print(f"[BOLA E1] status={r_bola.status_code}, body={r_bola.text[:120]}")

        # 2. BOPLA: 租戶 B 操作員發動 Mass Assignment 偷改 feeRate 與 isVerified
        r_bopla = client.patch(
            "/v1/tenants/1002/accounts/2001",
            headers={"Authorization": f"Bearer {TOKEN_B_OPER}"},
            json={"displayName": "Probe", "isVerified": True, "feeRate": 0},
        )
        print(f"[BOPLA E2] status={r_bopla.status_code}, body={r_bopla.text[:120]}")

        # 3. BFLA: 租戶 B 操作員越級呼叫平台管理員專用的費率覆寫端點
        r_bfla = client.post(
            "/v1/admin/tenants/1002/fee-override",
            headers={"Authorization": f"Bearer {TOKEN_B_OPER}"},
            json={"feeRate": 0},
        )
        print(f"[BFLA E5] status={r_bfla.status_code}, body={r_bfla.text[:120]}")

if __name__ == "__main__":
    scan()
```

### 任務二：補上 PostgreSQL RLS 與嚴格 DTO 白名單

抓出破口後，請依序從資料庫跟 NestJS 應用程式兩端動手修補：

首先連進 PostgreSQL，建立一個不是 Superuser、也沒有 `BYPASSRLS` 權限的應用程式專用帳號 `nexus_app`，並在 `accounts` 資料表上同時打開 `ENABLE` 與 `FORCE ROW LEVEL SECURITY`：

```sql
CREATE ROLE nexus_app NOINHERIT LOGIN PASSWORD 'dev_only_secret';
GRANT SELECT, INSERT, UPDATE, DELETE ON accounts TO nexus_app;

ALTER TABLE accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE accounts FORCE ROW LEVEL SECURITY;

CREATE POLICY accounts_tenant_isolation ON accounts
  USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::bigint)
  WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::bigint);
```

接著回到 NestJS 程式碼完成四項加固：
1. 在資料庫交易攔截器裡面，每次查詢前執行 `SET LOCAL app.current_tenant_id`。
2. 在 `UpdateAccountDto` 裡，只替合法的 `displayName` 與 `webhookUrl` 貼上 `@IsOptional() @IsString()` 裝飾器，並在全域打開 `ValidationPipe({ whitelist: true, forbidNonWhitelisted: true })`。
3. 在 E1 查詢帳戶若拿到 `null` 時，統一拋出 `NotFoundException`（回傳 `404`）。
4. 在管理端點 E5 補上 `@Roles('platform_admin')` 與集中式 `AuthorizationGuard`。

改完存檔後，再跑一次 `authz_matrix_scan.py`，確認三筆越權請求分別被 `404`、`400` 與 `403` 乾淨攔截。

### 任務三：PortSwigger *Access control vulnerabilities* 實戰檢查點

本地修補驗證完成後，請到 PortSwigger Web Security Academy 的 **Access control vulnerabilities** 主題，挑戰下面三個經典關卡：

1. **User ID controlled by request parameter, with unpredictable user IDs**（Apprentice）：親眼看看為什麼「把流水號改成猜不到的 UUID」根本不算修好 BOLA——只要系統裡有任何一個文章列表或公開頁面的回應裡露出了別人的 UUID，沒做權限核對的端點照樣一打就穿。
2. **Method-based access control can be circumvented**（Practitioner）：體會一下當開發者只針對 `POST /admin-roles` 鎖了管理員權限，卻沒鎖 `GET` 或其他 HTTP 方法時，攻擊者怎麼換個方法就把自己升成管理員（BFLA）。
3. **Multi-step process with no access control on one step**（Practitioner）：很多敏感操作會做成「第一步填表單、第二步點確認送出（`action=upgrade`）」的兩段式流程；若只在第一步路由掛了權限檢查，卻忘了在最後一步真正寫入資料庫的確認請求上重驗 `Subject.roles`，一般使用者直接發最後一步的封包就能越權成功。

---

### 參考解答

在還沒修補的靶機上執行 `authz_matrix_scan.py`，你會看到三條防線全線失守的輸出：

```text
[BOLA E1] status=200, body={"id":1001,"tenantId":1001,"balance":10000,"settlementSecret":"sec_..."}
[BOPLA E2] status=200, body={"id":2001,"tenantId":1002,"isVerified":true,"feeRate":0}
[BFLA E5] status=200, body={"status":"updated","feeRate":0}
```

等你把 PostgreSQL RLS、交易內的 `SET LOCAL`、`ValidationPipe(whitelist + forbidNonWhitelisted)` 以及 `@Roles('platform_admin')` 全部補齊後重跑一次，畫面就會變成下面這樣：

```text
[BOLA E1] status=404, body={"statusCode":404,"message":"Account not found"}
[BOPLA E2] status=400, body={"statusCode":400,"message":["property isVerified should not exist","property feeRate should not exist"]}
[BFLA E5] status=403, body={"statusCode":403,"message":"Forbidden resource"}
```

這裡有兩個非常值得留意的實戰細節：

第一，為什麼修好之後，跨租戶去讀別人的帳戶（`E1`）回傳的是 **`404 Not Found`** 而不是 `403 Forbidden`？因為當 PostgreSQL 的 `accounts_tenant_isolation` 策略生效後，資料庫在底層就直接把不屬於租戶 `1002` 的資料列過濾掉了，ORM 查回來就是空值（`null`）。讓應用程式對「這個帳戶根本不存在」與「這個帳戶屬於別家租戶」一律回傳相同的 `404`，反而能防止攻擊者靠 `403` 與 `404` 的差異去探測哪些帳戶編號已經被別人註冊了。

第二，仔細看我們寫在 RLS 策略裡的那句 `NULLIF(current_setting('app.current_tenant_id', true), '')::bigint`。為什麼要在外面包一層 `NULLIF(..., '')`？因為如果某個連線曾經設定過變數、後來被重置成空字串 `''`，直接對空字串做 `''::bigint` 轉型會當場讓 PostgreSQL 噴出轉型錯誤！

包了 `NULLIF` 之後，不管是「根本忘了設變數（回傳 `NULL`）」還是「變數是空字串 `''`」，都會被統一轉成 `NULL`。而在 SQL 的三值邏輯裡，`tenant_id = NULL` 的結果永遠是 `UNKNOWN`（一列都不會命中），正好完美達成 **Fail-Closed（忘記設租戶就預設一筆都不准讀）** 的安全效果。

---

## 自我檢核

- **難度**：入門
- **預估時間**：15 分鐘

不看前面的範例，試著診斷下面四個真實的後端架構問題：

1. **抓出繞過 RLS 的三個盲區**：某個多租戶微服務已經在 PostgreSQL 資料表上設好了 RLS 策略，而且確定連線用的資料庫帳號既不是 Superuser，也沒有 `BYPASSRLS` 屬性。請舉出三種在真實生產環境裡，還是會導致租戶 A 讀到租戶 B 資料的跨層或配置漏洞。
2. **為什麼換了 Prisma 還是中了 BOPLA**：某團隊從 TypeORM 換成 Prisma，並在更新商戶折扣的 Controller 裡寫了 `await prisma.merchant.update({ where: { id }, data: req.body })`。雖然他們在函數參數上標註了 `req.body: { nickname?: string }`，為什麼攻擊者送出 `{"nickname": "VIP", "commissionRate": 0}` 還是能把資料庫裡的抽成費率改成 `0`？
3. **診斷這支 Guard 到底防了什麼、又漏了什麼**：某平台在 API Gateway 驗過了 RS256 JWT（有效期 `900 s`），並在每支 `/v1/orgs/:orgId/*` 的路由掛了一個 `OrgMatchGuard`，確認 `req.params.orgId === req.user.orgId`。請問這道防線擋住了哪一種最陽春的越權？如果後端工程師以為有這個 Guard 就萬事大吉，後面還可能爆出哪三種不同維度的授權漏洞？
4. **為什麼本地測試 RLS 會動、上線卻整套失效**：工程師在本地測試 PostgreSQL RLS 時，特地建了一個 `test_reader` 帳號去跑查詢，確認跨租戶的資料列真的都被擋掉了；結果部署上正式環境後，微服務用的卻是跟跑資料庫 Schema Migration 建表時同一個 `db_owner` 帳號，結果線上的 RLS 形同虛設。請問為什麼會這樣？只要補上一行什麼 SQL 就能修好？

---

### 參考解答

1. **繞過 RLS 的三個真實盲區**：
   - **快取層沒綁租戶**：在資料庫前面加了 Redis 或 CDN 快取，快取鍵卻只寫了資源 ID（如 `invoice:999`）而沒拼上 `tenant_id`，而且從快取讀出來時也沒重驗租戶歸屬，導致快取命中時直接繞過 PostgreSQL 把別人的資料吐回去。
   - **連線池的 Session 變數殘留**：後端透過 PgBouncer（transaction pooling 模式）連資料庫，卻用了工作階段級別的 `SET app.current_tenant_id` 而不是交易級別的 `SET LOCAL`，導致連線歸還池子後變數沒清掉，被下一個沒設變數的請求誤用。
   - **用了 Table Owner 連線卻漏加 `FORCE`**：應用程式直接拿建立該資料表的擁有者（Table Owner）角色去連線查表，而資料表只執行了 `ENABLE ROW LEVEL SECURITY` 卻沒執行 `FORCE ROW LEVEL SECURITY`。
2. **為什麼換了 Prisma 還是中了 BOPLA**：
   - 因為 TypeScript 的型別標註 `{ nickname?: string }` 只活在編譯期，轉成 JavaScript 執行時早就消失了。只要沒在執行期透過 `ValidationPipe({ whitelist: true })`、Zod schema 或手動解構把允許的欄位挑出來，`req.body` 裡面的 `commissionRate: 0` 就會原封不動傳進 `prisma.merchant.update` 的 `data` 物件裡；既然資料表定義裡確實有 `commissionRate` 這個欄位，Prisma 就會乖乖幫你生出更新該欄位的 SQL。
3. **診斷 `OrgMatchGuard` 防了什麼、漏了什麼**：
   - 它只擋下了最表層的「直接把網址上的 `:orgId` 改成別家公司編號」這種粗淺嘗試。
   - 它漏掉了三個維度的破口：(1) **BOLA**：攻擊者在 `:orgId` 填自己公司編號騙過 Guard，卻把後面的子資源編號（如 `/invoices/:invId`）換成別家公司的發票 ID，而 Service 查表時只寫 `WHERE id = invId` 忘了綁 `org_id`；(2) **BOPLA**：同公司的低權限員工送出未授權欄位更新（大量賦值），或從 API 回應讀到不該看的機密屬性；(3) **BFLA**：一般員工直接呼叫管理員專用端點。
4. **為什麼 Table Owner 會繞過 RLS**：
   - 在 PostgreSQL 的預設規則裡，資料表的擁有者（Table Owner）是自帶免死金牌的，預設不受該表上的 RLS 策略限制。本地測試時用了另外建的 `test_reader`（非 Owner）所以有效；上線後微服務跟建表的 Migration 共用同一個 `db_owner` 角色，RLS 就自動對它放水了。
   - 只要在資料表上補執行一行 `ALTER TABLE <table_name> FORCE ROW LEVEL SECURITY;`，就能強制規定連 Table Owner 自己查表也必須乖乖遵守 RLS 策略。

---

## 延伸閱讀

- **OWASP API Security Top 10:2023（API1 BOLA、API3 BOPLA、API5 BFLA）**：官方對這三大授權破口的完整案例拆解與防禦檢核清單（https://owasp.org/API-Security/）。
- **PostgreSQL 16 官方文件 — Row Security Policies**：詳細說明了 `ENABLE` 與 `FORCE ROW LEVEL SECURITY` 的差異、`current_setting()` 的用法以及 `USING` 與 `WITH CHECK` 的生效時機（https://www.postgresql.org/docs/16/ddl-rowsecurity.html）。
- **PortSwigger Web Security Academy — Access control vulnerabilities**：收錄了水平越權、垂直越權與多步驟流程漏檢的免費線上靶場（https://portswigger.net/web-security/access-control）。
- **Open Policy Agent (OPA) / Cedar Policy Language**：想把散落在各處的權限判斷收斂成集中式 Policy Decision Point（PDP）時，最值得參考的兩套宣告式策略引擎文件（https://www.openpolicyagent.org/docs/latest/）。
