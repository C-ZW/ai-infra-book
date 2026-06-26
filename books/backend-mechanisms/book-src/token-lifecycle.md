# token 的生命週期與撤銷

凌晨三點，值班的人接到通報：一名員工的筆電在咖啡廳被偷了，瀏覽器裡還登著公司的內部系統。流程很清楚——進管理後台，把這個帳號停用，撤掉它的所有存取權。點下「停用」，後台回了一句綠色的「已停權」。鬆一口氣。

但這口氣鬆得太早。那台被偷的筆電，此刻手裡握著一張還沒過期的 access token。它不需要再登入、不需要再問任何人，只要把這張 token 貼在每個請求的 `Authorization` header 上，後端就會放行——因為後端**驗的是這張 token 的簽章，不是去問「這個帳號還活著嗎」**。你在管理後台按下的那個按鈕，改的是資料庫裡 user 那一列的狀態；而那台筆電手裡的 token，是一張早在停權之前就簽好、印好、發出去的通行證，上面沒有任何欄位會因為你改了資料庫而變色。

於是出現一個讓很多人第一次遇到時不敢相信的事實：**帳號已經停權了，token 卻還能用。** 它能用多久？這就是這一章要把它算清楚、講透的東西——一張 token 從簽發、被使用、到失效，中間到底發生了什麼，以及最棘手的那一段：當你想在它「自然死亡」之前**提前**殺掉它，為什麼這件事比想像中難這麼多。

## 為什麼撤銷一張 token 這麼難

要看清難在哪，先得分清兩種根本不同的 token，因為它們的撤銷難度是天差地別的。

第一種是**有狀態的（stateful）、不透明的（opaque）token**：它本身只是一串隨機字串，像一張寄物櫃的號碼牌，本身不帶任何資訊。後端收到它，拿這串字串去資料庫（或 Redis）查一張表：這個 token 對應哪個 user、有沒有過期、有沒有被撤。撤銷它易如反掌——把那張表裡的那一列刪掉、或標記為失效，下一個請求一查就被擋下，**撤銷在下一次請求就生效**。傳統的 server-side session 就是這種。代價是：每一個請求都要查一次 store，而這個 store 必須被所有驗證請求的節點共享。

第二種是**無狀態的（stateless）、自包含的（self-contained）token**，典型就是簽章過的 JWT（結構與簽章機制見〈JWT 與簽章〉）。它把「這是誰、有什麼權限、何時過期」這些資訊**寫在 token 自己身上**，再用一把只有簽發方握有的金鑰簽名。後端收到它，**不查任何 store**——只要在本地用公鑰（或共享密鑰）驗一下簽章對不對、看一眼裡面寫的 `exp`（到期時間）有沒有過，就能信它。這正是它最迷人的地方：驗證是純本地運算，O(1)，不需要一個大家共享的 session store，所以它能輕鬆水平擴展、能在邊緣節點就地驗、能讓十個微服務各自獨立驗同一張 token 而不必互相打擾。

但這個優點和那個夜裡的麻煩，是同一枚硬幣的兩面。把它寫成一句話，這一章後面所有的設計都是從這句話長出來的：

> 一張自包含的簽章 token，伺服器靠本地驗簽就信它、不查任何 store。這正意味著伺服器手上**沒有一個「這張 token 還算不算數」的開關**。token 一旦簽出去，在它的 `exp` 到期之前都驗得過——即使背後那個 user 已經被停權、密碼已經外洩、權限已經被收回。

簽章是不可逆的。你沒辦法「取消」一個已經算出來的簽章——它在數學上永遠是對的。你也沒辦法回收已經發出去的那串字串——它可能正躺在某台筆電的記憶體裡、某個 app 的 keychain 裡、某份被竊的 log 裡，你根本不知道它有幾份拷貝、在哪裡。**無狀態的 token 沒有「家」，它一旦離開簽發方，就是一張在外面自由流通、誰拿到誰就是它的匿名通行證，直到它寫在身上的那個時間一到、自己過期為止。**

這就是核心張力：**無狀態帶來的「免查 store、易擴展」，和安全上需要的「能即時收回」，是直接對立的。** 你越是讓 token 自包含、自驗證（為了擴展性），就越是放棄了對它的即時掌控（為了能撤銷）。這不是哪個函式庫的 bug，是這個設計本身的物理。整套「token 生命週期」的工程，全部都是在這條張力線上找一個能接受的點。

## 短命 access token：用時間換無狀態

既然無法「即時收回」一張已發出的無狀態 token，那就退而求其次——**讓它活得夠短，短到就算收不回、危害也有限。** 這是整個現代 token 設計的第一塊基石，簡單到近乎賴皮，卻出奇地有效。

但這裡馬上撞上一個矛盾。如果 access token 設得很短——比如 15 分鐘——那使用者豈不是每 15 分鐘就要重新輸入一次帳號密碼？沒有人能忍受這個。如果為了體驗把它設成好幾天，那它就退化成本章開頭那個惡夢：洩漏了就好幾天無解。

解這個矛盾的，是把一張 token 拆成**兩張、各司其職**的經典設計：

- **access token**：短命（典型 15–60 分鐘，敏感場景甚至 5–15 分鐘）。它是每個請求都要帶、被到處傳遞、曝險面最大的那張。正因為曝險面大，所以讓它命短——洩漏的爆炸半徑被限制在一個 TTL 之內。它通常是自包含的 JWT，這樣每個請求的驗證才能無狀態、才快。
- **refresh token**：長命（幾天到幾週）。它**只**有一個用途：拿去跟簽發方（authorization server）換一張新的 access token。它不會在每個業務請求裡到處跑，只在 access token 過期時、對著那一個專門的 token 端點出現一次。因為它出場次數少、只對一個端點說話，它可以被存放得更嚴密（HttpOnly cookie、行動端的 secure storage），曝險面小得多。而且換新 token 這個動作**本來就要對著 authorization server**——那是一個有狀態、查得到 store 的地方，所以 refresh token 通常是**有狀態的**：它在 server 端有記錄，可以被即時撤銷。

於是兩張 token 形成一個漂亮的分工：access token 負責「快、無狀態、到處驗」，refresh token 負責「可撤銷、嚴密保管、只在一處出現」。撤銷的時候，你撤掉那張**有狀態的** refresh token——它在 store 裡有記錄，一刪就再也換不出新 access token。至於那張還在外面流通的 access token？你撤不掉它，但它最多再活一個 TTL 就自己死了。**撤銷不是即時的，而是「最多延遲一個 access token TTL」。**

## 把延遲算清楚

口頭說「最多延遲一個 TTL」太抽象。把它放到一條真實的時間軸上手算一遍，這個機制才真正在腦中立體起來。

設 access token 的 TTL 是 **15 分鐘**。現在排一條時間線：

```
09:50:00  user 的 app 換到一張新 access token，exp = 10:05:00
10:00:00  安全團隊在後台停權此 user：撤掉它的 refresh token
            （refresh token 有狀態，store 裡那筆立刻失效）
10:00:01  那張 09:50 簽發的 access token 還在筆電上
            它的簽章仍然有效、exp(10:05:00) 還沒到
            → 後端本地驗簽通過 → 放行
10:05:00  access token 到期。app 試圖用 refresh token 換新的
            → refresh token 已被撤 → 換不出來 → 真正登出
```

關鍵的那一段是 **10:00:00 到 10:05:00**——停權之後，那張舊 access token 還能繼續存取整整 **5 分鐘**。為什麼是 5 分鐘而不是 15 分鐘？因為這張 token 是 09:50 簽的、10:05 過期，停權發生在它生命的第 10 分鐘。撤銷延遲不是固定的 TTL，而是**「停權那一刻，到當下這張 access token 的 exp 為止，還剩多少時間」**——它在 0 到 TTL 之間，平均是半個 TTL。最壞情況是停權剛好發生在一張新 token 簽出的瞬間，那就得等滿整整 15 分鐘。

這就把一個含糊的安全直覺，變成了一個可以拿去跟人談判的數字：**「我們的撤銷延遲上界是一個 access token TTL。」** 你把 TTL 設多少，就等於宣告了「停權後最壞情況下還能被濫用多久」。

那把 TTL 設更短不就好了？把 15 分鐘壓到 1 分鐘，撤銷延遲上界就從 15 分鐘掉到 1 分鐘——安全上漂亮。但天下沒有白吃的午餐：access token 每 1 分鐘就過期一次，意味著 app 每 1 分鐘就得拿 refresh token 去 authorization server 換一張新的。相較於 15 分鐘的設定，**對 authorization server 的 refresh 請求量直接變成 15 倍**。那台 authorization server 本來只是偶爾被打擾一下，現在變成每個活躍 user 每分鐘都來敲一次門；它的負載、它的可用性、它的單點風險，全部跟著放大。

這就是這一章最核心的那個對價，現在它有了具體的兩端：**撤銷延遲（安全） ←→ refresh 開銷（authorization server 負載）**。TTL 往下調，撤銷變快、但 authorization server 被打爆；TTL 往上調，authorization server 輕鬆、但停權後的危險窗口變大。15 分鐘之所以是個常見的甜蜜點，正是因為它落在這條線上一個多數場景都能接受的位置：5 分鐘的窗口對絕大多數業務可以容忍，而 15 分鐘一輪的 refresh 頻率對 authorization server 也還溫和。沒有「正確」的 TTL，只有「你願意把延遲和開銷各放在哪」的那個點。

## 當「最多 5 分鐘」也不能接受

對絕大多數系統，「停權後最多再被用 5 分鐘」是可以接受的。但有些操作不行——轉一筆大額的帳、改掉某人的權限、刪掉一整批資料。對這些，5 分鐘的窗口意味著被偷的 token 在這 5 分鐘裡可以把錢轉光。這時候，你必須放棄「純無狀態」這個美夢，把那個你一開始就沒有的「開關」**硬裝回去**。

裝回去的方式是一份 **denylist（撤銷清單，有時叫 blocklist）**。它的原理很直白：每張 JWT 在簽發時都帶一個唯一識別碼 `jti`（JWT ID）。當你要提前撤掉某張還沒過期的 access token，就把它的 `jti` 丟進一份清單裡。然後——這是關鍵、也是代價所在——**驗證的每一個請求，在驗完簽章之後，多做一件事：去查這份 denylist，看這個 `jti` 在不在裡面，在就拒絕。**

你立刻看出這付出了什麼。整個 JWT 設計的賣點是「驗證不查 store」，而 denylist 正好就是**在驗證路徑上加回了一次 store 查詢**。你親手把那個讓 JWT 值錢的「無狀態」給抵銷掉了。所以這不是一個能無腦全開的東西——如果每張 token 都查 denylist，那你不如一開始就用有狀態的 opaque token、根本不必繞 JWT 這一大圈。

denylist 真正成立的前提，是一個量上的不對稱：**被「提前」撤銷的 token，永遠是極少數。** 絕大多數 token 都是平平安安地用到 `exp` 自然過期，從來不需要被列入清單；只有「在到期前就出事、必須立刻拔掉」的那一小撮才進 denylist。這帶來兩個讓 denylist 在工程上可行的性質：

第一，清單很短，查它很快——通常就放在 Redis 這種記憶體 store，一次查詢是亞毫秒級，加在驗證路徑上的延遲可以接受。

第二，也是常被忽略、忘了就會出事的一點：**denylist 裡的每一筆都該帶 TTL，而且這個 TTL 就設成「那張 token 原本的 `exp`」。** 為什麼？因為一張 token 過了它自己的 `exp` 之後，簽章驗證那一關本來就會把它擋下來，根本輪不到查 denylist——它已經因為過期而失效了。所以它在 denylist 裡再待下去毫無意義，只是白佔空間。如果你忘了給 denylist 條目設 TTL，這份清單會**只增不減、無限長大**——查詢越來越慢，記憶體越吃越多，最後反而成了系統的拖累。**denylist 是一份會自動瘦身的快取，不是一張永久的黑名單表。** 它的尺寸天然被「同時還活著、且被提前撤銷」的 token 數量所界定，過期的自動掉出去。

這裡藏著一個容易讓人困惑、但想通了就豁然開朗的邊界：denylist 的條目 TTL，**設得比 token 的 `exp` 長是浪費，設得比 `exp` 短卻是個安全漏洞**。設短了會怎樣？假設一張 token 的 `exp` 是 10:05，但你只讓它在 denylist 裡待到 10:03——那麼 10:03 到 10:05 這兩分鐘，這張 token 既不在 denylist 裡了、`exp` 又還沒到，於是它**復活了**，重新變得可用。所以 denylist 條目的 TTL 必須**恰好等於**該 token 的剩餘壽命：不多一秒（多了浪費），不少一秒（少了漏洞）。

## 撤銷一張 token，到底撤掉了什麼

前面把 access token 和 refresh token 分開講，但真實的撤銷動作往往牽一髮動全身，這裡有一層常被略過的細節。標準化「主動告訴 authorization server 作廢某張 token」這件事的，是 **RFC 7009（OAuth 2.0 Token Revocation）**，它定義了一個 revocation 端點。但它的措辭裡藏著正是上面那套無狀態困境的影子，值得逐字看。

RFC 7009 規定：實作 **MUST**（必須）支援撤銷 refresh token，而撤銷 access token 只是 **SHOULD**（建議）。這個強弱之分不是隨便定的——它正是前面那條物理的直接後果。refresh token 通常有狀態、有家可回，撤它是確定能做到的，所以是 MUST；access token 常是無狀態的 JWT，authorization server 根本沒有它的記錄、也沒有那個開關，所以只能「建議」、做不到也情有可原。

更微妙的是 RFC 7009 對「連坐」的處理。它說：當你撤掉一張 refresh token 時，authorization server **SHOULD** 也一併讓「基於同一份授權（authorization grant）發出的所有 access token」失效——但這句 SHOULD 後面跟著一個關鍵的條件子句：**「如果該 authorization server 支援撤銷 access token 的話」**。這個條件不是客套，它精準地承認了一件事：在一個 access token 是純無狀態 JWT 的系統裡，authorization server **沒有能力**讓那些已經發出去的 access token 失效——它做不到，所以這條 SHOULD 對它而言根本無法套用。規格用一個 if 子句，誠實地把「無狀態 token 撤不掉」這個現實寫進了標準本身。

所以「撤銷一張 token」在實務上是分層的，你心裡要清楚每一層的保證強度：

- 撤 refresh token：一定做得到（它有狀態）。效果是「再也換不出新 access token」。但**這不會讓手上那張還沒過期的 access token 立刻失效**——它得自己活到 `exp`。這就是為什麼撤了 refresh token，還是有那個 5 分鐘窗口。
- 讓那張在途的 access token 也立刻失效：只有在你額外建了 denylist（或改用有狀態 token）時才做得到。否則做不到，只能等它自然過期。

把這兩層分清楚，本章開頭那個夜裡的場景就完全解釋通了：安全團隊撤的是 refresh token（做得到、那台筆電換不出新 token 了），但那張在途的 access token 撤不掉（除非有 denylist），所以還有一個窗口。它不是 bug，是這個架構誠實的代價。

## refresh token 自己被偷了怎麼辦

把長命的權力集中到 refresh token 上，等於把雞蛋集中放進一個籃子——那這個籃子自己破了呢？refresh token 命長、權力大（能源源不絕換出 access token），它一旦外洩，危害遠比一張 access token 嚴重。針對這個，業界發展出一套漂亮的機制：**refresh token 輪替（rotation）配上重用偵測（reuse detection）**。這套做法的權威出處是 **RFC 9700（Best Current Practice for OAuth 2.0 Security，BCP 240，2025-01 發布）**，它把這件事從「大家私下的好習慣」提升成了正式的安全 BCP。

機制是這樣的。傳統做法裡，refresh token 是一張可以反覆使用的長期票——用它換 access token，它自己不變，下次再用同一張。rotation 改掉這一點：**每次拿 refresh token 去換 access token，authorization server 在發新 access token 的同時，也發一張新的 refresh token，並把剛用過的那張舊的立刻作廢。** 於是 refresh token 變成一條**一次性、單次使用**的鏈——每張只能用一次，用完即焚，換來下一張。

光是輪替還不夠，真正的殺招是它搭配的偵測邏輯。設想一條鏈：合法的 app 持有 refresh token `R1`，用它換到 `R2`（`R1` 作廢）。現在假設 `R1` 在被作廢之前，曾被攻擊者偷走過一份。某個時刻攻擊者拿這份偷來的 `R1` 去換 token——但 `R1` 已經被用過、已經作廢了。authorization server 看到「一張**已經被用過的** refresh token 又被拿來用了」，這在正常流程裡**不可能發生**（合法 app 早就換到 `R2` 了，不會回頭用 `R1`）。這個「重用一張已作廢的 token」就是一個明確的入侵訊號。

偵測到這個訊號，authorization server 做的不是只擋下這一次，而是**把整條 token 家族（family）全部撤掉**——`R1`、`R2`、以及這條鏈上後續所有的 token 一起失效，強迫合法 user 和攻擊者**雙雙**重新登入。為什麼要連合法 user 一起踢掉？因為 authorization server 此刻分不清這兩個來用的人**哪一個是賊**——它只知道「同一張一次性 token 被用了兩次，這條鏈上一定有一方是冒充的」。與其賭錯放行了攻擊者，不如把整條鏈炸掉、要求雙方都重新證明自己是誰。RFC 9700 建議（SHOULD）撤銷整個 token family、**而不只是當下這一張**——否則攻擊者可能拿著之前輪替過、被自己快取下來的舊 token 繼續鑽。

這套機制的妙處在於，它不需要你「知道」token 被偷了——它讓偷竊這個行為**自己暴露**。只要小偷和原主都還在用同一條鏈，他們遲早會在某次換 token 時撞在一起（兩個人不可能總是用到對方最新的那張），而那次相撞就是警報。它把「我怎麼知道 token 被偷了」這個幾乎無解的問題，轉化成了一個可以被動偵測的衝突。

但它也不是免費的，有個真實的故障模式藏在裡面：**網路抖動可能造成誤判。** 想像合法 app 用 `R1` 發出換 token 的請求，authorization server 收到了、也發出了 `R2`，但回程的網路斷了——`R2` 沒回到 app 手上。app 那邊看到的是「請求超時」，於是它**重試**，又用了一次 `R1`。從 authorization server 的角度看，這跟攻擊者重用 `R1` 長得**一模一樣**——一張已作廢的 token 又被拿來用了。於是它觸發 reuse detection，把整條鏈炸掉，合法 user 莫名其妙被登出了。這是 rotation 真實存在的代價：它在「偵測竊用」和「容忍合法重試」之間沒有完美的界線，網路的不確定性會偶爾把一次無辜的重試誤判成入侵。實務上的緩解（比如給剛輪替的舊 token 留一個極短的寬限重用窗口）能壓低誤判率，但無法讓它歸零——這又是一個「安全」與「可用」之間，沒有銀彈、只能選位置的取捨。

## 那「登出」又是什麼

順著前面的機制，有一件每個人每天都在做、底下卻比表面更曲折的事值得拆開看：**登出（logout）。**

在純前端的世界裡，「登出」常常只是一行 `localStorage.removeItem('token')`——把瀏覽器裡存的那張 token 刪掉。介面跳回登入頁，看起來登出了。但你現在已經知道這裡的破綻：**刪掉前端那一份 token，不等於那張 token 失效了。** 如果這張 token 在被刪之前曾經被攔截、被複製到別處，那份拷貝完全不受你前端刪除動作的影響——它的簽章還是對的、`exp` 還沒到，後端照樣放行。前端的「登出」只是讓**這一個瀏覽器**忘記了 token，token 本身在世界上依然有效。

所以一個誠實的登出，動作必須發生在 **server 端**：去 authorization server 撤掉這條 session 的 **refresh token**（讓它換不出新 token），如果場景敏感、不能容忍那個 TTL 窗口，再把當前的 access token `jti` 丟進 denylist。對於 OIDC 這種跨多個應用共用登入的場景，標準甚至定義了 **RP-Initiated Logout** 和 **Back-Channel Logout**——讓 identity provider 在一處登出時，能反向通知所有信任它的應用「這個 session 結束了，把相關 token 都清掉」，避免「在 A 應用登出了、B 應用卻還登著」的鬼影 session。

把它收成一句：**登出的本質，是一次撤銷。** 而撤銷的所有難處——無狀態 token 撤不掉、只能等過期、要即時得靠 denylist——在登出這件事上全部重演一遍。一個只清前端的登出，和一個真正去 server 端撤 token 的登出，在「token 被偷」的那條故事線上，是天壤之別。

## 還有一條路：根本不要無狀態

繞了一大圈在無狀態 token 上補各種「把開關裝回去」的機制，你可能會問：那為什麼不一開始就用有狀態的 token？

這確實是另一條路，而且對某些系統是更對的路。**opaque token + introspection** 就是它的完整形態，標準是 **RFC 7662（OAuth 2.0 Token Introspection）**。這裡的 token 是一串不透明的隨機字串，本身不帶資訊；resource server 收到它，**每一次**都拿去向 authorization server 的 introspection 端點問一句：「這張 token 現在還 active 嗎？它代表誰、有什麼 scope？」authorization server 查它權威的 store，回一個 `active: true/false`。

這條路的保證和無狀態恰好對調，把取捨看清楚就知道何時該選它：

- 撤銷是**完全即時**的——authorization server 一把 token 標記為失效，下一個 introspection 請求就拿到 `active: false`，沒有任何 TTL 窗口。
- token 本身**不洩漏任何資訊**（它只是隨機字串，不像 JWT 那樣把 claim 攤在陽光下給人 base64 解碼）。
- 權限永遠是**最新**的——每次都現查，不會像 JWT 那樣把簽發當下的權限「凍」在 token 裡，導致權限改了、token 裡卻還是舊的。

代價也對調，而且很重：**每一個業務請求都多一次對 authorization server 的網路往返。** 這次往返加在每個請求的延遲上，而且把整個系統的可用性**綁死在 authorization server 身上**——authorization server 一慢、一掛，所有 resource server 的驗證全部跟著慢、跟著掛。你用「即時撤銷」換來了「每請求一次往返 + 中心化的單點依賴」。

所以選擇從來不是「JWT 好還是 opaque 好」，而是把那條張力線攤開，問自己站在哪一端：

| | 無狀態 JWT | opaque + introspection |
|---|---|---|
| 驗證成本 | 本地驗簽，O(1)，不查 store | 每請求一次網路往返 |
| 撤銷即時性 | 不即時（等 TTL，或自建 denylist） | 完全即時 |
| 擴展性 | 極佳（各節點獨立驗） | 受限於 authorization server 吞吐 |
| 可用性耦合 | 低（驗證不依賴中心） | 高（綁 authorization server） |
| 權限新鮮度 | 凍在簽發當下 | 每次最新 |

introspection 為了壓低那次往返的成本，實務上常會**快取** introspection 的結果一小段時間——但你一旦快取，就又在「即時撤銷」上打了折扣，快取多久、就等於放棄了多久的即時性。看到沒有？**繞了一整圈，你還是回到了同一條張力線上的同一個取捨**——只是換了個地方付帳。無論你從哪一端出發，最後都得在「能多快收回」和「驗證要付多少代價」之間，親手選一個點。

## 為什麼是這個形狀

退一步看，token 生命週期這整套看似零碎的機制——短 TTL、refresh token、denylist、rotation、introspection——其實全都是從**同一個無法迴避的事實**裡長出來的：

**一張你信任的、能在本地獨立驗證的 token，本質上就是一張你沒辦法當場叫回的通行證。** 「能離線驗證」和「能即時撤銷」是同一個東西的兩面，你不可能同時把兩面都拿滿。

正因如此，才有了短 TTL——既然叫不回，那就讓它命短，把叫不回的代價限制在一個時間窗口內。正因如此，才把 token 拆成兩張——讓曝險面大的那張命短而無狀態（換取擴展性），讓有狀態、撤得掉的那張藏好而命長（換取可撤銷）。正因如此，當那個時間窗口都嫌長時，才會有 denylist 這種「把無狀態的好處部分吐回去、換一點即時性」的妥協。正因如此，refresh token rotation 才要用「重用即暴露」的巧勁，去應付「我根本不知道 token 有沒有被偷」這個無解的前提。而那條始終撤不掉、只能等它自己過期的 access token，正是你為了「驗證不必每次打擾中心」所付的、寫在物理裡的學費。

下次你設定一個 access token 的 TTL，把它從一天改成十五分鐘的時候，你會知道你不是在調一個無關痛癢的參數——你是在這條「即時撤銷 ←→ 無狀態擴展」的張力線上，親手釘下一個點，並對著它宣告：「我們最壞情況下，停權後還能被濫用這麼久，而我們用這個數字，換來平常不必為每個請求去打擾那台中心伺服器。」那個數字背後，是這一整章的故事。

## 延伸閱讀

- [OAuth 2.0 Token Revocation — RFC 7009](https://www.rfc-editor.org/rfc/rfc7009.html)（定義 revocation 端點；MUST 支援撤 refresh token、SHOULD 支援撤 access token 的措辭來源）
- [OAuth 2.0 Token Introspection — RFC 7662](https://www.rfc-editor.org/rfc/rfc7662.html)（opaque token 即時驗活的標準）
- [JSON Web Token Best Current Practices — RFC 8725](https://www.rfc-editor.org/rfc/rfc8725.html)（JWT 安全實務，含撤銷與短 TTL 的處理建議）
- [Best Current Practice for OAuth 2.0 Security — RFC 9700](https://www.rfc-editor.org/rfc/rfc9700.html)（BCP 240，2025-01；refresh token rotation 與 reuse detection 的權威出處）
- [The OAuth 2.0 Authorization Framework — RFC 6749](https://www.rfc-editor.org/rfc/rfc6749)（access token 與 refresh token 的原始定義）
- [OpenID Connect RP-Initiated Logout 1.0](https://openid.net/specs/openid-connect-rpinitiated-1_0.html)（跨應用登出的標準機制）
- [OpenID Connect Back-Channel Logout 1.0](https://openid.net/specs/openid-connect-backchannel-1_0.html)（identity provider 反向通知各應用終止 session）
