# ch07 — 時序邏輯：safety、liveness 與 fairness

> **本章解決什麼問題**：ch06 結尾留了一句警告：□[Next]_vars 是允許清單，不是待辦清單——它保證系統不做壞事，卻從不承諾任何事終將發生。本章補上承諾的那一半：先給你 □、◇、⤳ 這組對整條 behavior 說話的算子，再把所有性質一刀切成 safety（有限可反駁）與 liveness（永遠可補救）兩類，最後引入 fairness——WF 與 SF——把「可以做」升級成「終究會做」的那條失落條款。結算系統的 liveness 性質 `AllPaid` 在本章正式命名並配上它需要的 fairness。完整 spec 的組裝見 ch08，機器怎麼檢查 liveness 見 ch09，liveness 怎麼證明 ch14 淺談。

## 從你已知的出發

你的結算 pipeline 有一條從來沒寫進任何程式碼、卻撐起整個業務的假設：「丟進 SQS 的訊息，終究會被消費。」

它不在 producer 裡，不在 consumer 裡，也不在 IaC 範本裡。它存在於 K8s 會把掛掉的 pod 拉起來、SQS 會把逾時的訊息重新投遞、你的 on-call 會在半夜處理 OOMKilled 這些機制的**合成效果**裡。ch02 戳破過一次：v0 的動作規則沒有任何一條強迫 consumer 工作，「停在 S1 從此不動」完全合法。ch06 的紙上推演又補了一刀：把 Requeue 加進 Next，訊息可以被拿起、放回、拿起、放回，鬼打牆到天荒地老——safety 毫髮無傷，入帳遙遙無期。當時說「ch07 拿 fairness 來治它」。今天收網。

再看你的監控。On-call 的事故有兩種長相：

- **有犯罪現場的**：錯誤 log、髒資料、重複入帳的 row。壞事發生在某個確切的時刻，你可以指著它說「就是這一步」。
- **沒有現場的**：什麼都沒壞，只是該發生的一直沒發生。佇列深度不降、結算批次卡住、deadlock detector 安靜地等。你的告警規則「queue depth 連續 30 分鐘 > 0」其實是在用有限的觀察，逼近一個關於無限未來的判斷——「它**永遠**不會被消費了」。但嚴格說，30 分鐘證明不了永遠；你拉長到 24 小時也一樣。

這兩種事故的分界線，就是本章的主角：safety 與 liveness。前者違反的證據是有限的，後者違反的證據永遠湊不齊有限版本——這是 ch02 那句「safety 看得到犯罪現場，liveness 永遠在等待戈多」的正式化。而你那條「訊息終究會被消費」的營運信仰，會在本章拿到數學身分：fairness 假設。它有兩個強度——WF 與 SF——粗略地說：WF 對得起一台持續健康的 consumer，SF 對得起一台反覆 crash-restart、卻總會被拉起來的 consumer。你的 K8s 叢集每天都在替你兌現其中一種。

## 時序算子：對整條 behavior 說話

ch06 把性質分了三層：狀態述語談單一狀態、action 談一步、時序公式談整條 behavior。前兩層你已經會了，本章把第三層的詞彙補齊。

設 σ = s₀ → s₁ → s₂ → … 是一條（無限的）behavior。記 σ⁽ⁱ⁾ 為它從位置 i 起的**後綴** sᵢ → sᵢ₊₁ → …。約定：一條狀態述語 P 套在 behavior 上，看的是**第一個狀態**——σ ⊨ P 若且唯若 s₀ ⊨ P。時序算子做的事，就是把「看第一個狀態」推廣成「看每個位置」：

- **□F（always，ASCII `[]`）**：σ ⊨ □F 若且唯若**每個**後綴 σ⁽ⁱ⁾ 都滿足 F。對狀態述語 P，□P 就是「P 在每個位置都成立」——ch02 的 invariant 直覺，現在是一條正式的時序公式。
- **◇F（eventually，ASCII `<>`）**：σ ⊨ ◇F 若且唯若**某個**後綴 σ⁽ⁱ⁾ 滿足 F。注意 i 可以是 0：「終將發生」包含「現在就成立」。
- 兩者對偶：◇F ≡ ¬□¬F。

如果你覺得這對搭檔眼熟——對，□ 就是「對所有位置」的 ∀，◇ 就是「存在位置」的 ∃，只是量化的範圍從集合元素換成了時間位置。ch03 練的否定推移原封不動地搬過來：¬□F ≡ ◇¬F（「並非永遠」＝「終將有一次不」）、¬◇F ≡ □¬F（「永不發生」＝「每一刻都沒發生」）。

另外提一件你可能在別的教材看過的東西：標準 LTL 有個「下一步」算子（通常寫 X 或 ◯）。TLA **刻意沒有它**。理由是 ch06 的 stuttering：任何 TLA 公式對「插入或刪除 stuttering 步」必須不敏感，而「下一步」這個概念數的恰恰是步——兩次取樣之間塞進幾步 stuttering，「下一步是什麼」就變了。所以 TLA 的時序公式說得出「終將」「永遠」，刻意說不出「恰好三步之後」。

### 疊起來用：□◇ 與 ◇□

□ 與 ◇ 可以巢狀。兩個組合重要到值得專門起名：

- **□◇P：「反覆發生」（infinitely often）**。每個位置往後看都還會再遇到 P——P 出現無限多次，永不絕跡。
- **◇□P：「終將穩定」（eventually forever）**。存在某個位置，從那之後 P 再也不退場。

```text
□◇P（反覆發生）：  ─P───P─────P──P───────P───▶  P 永遠還會再來，中間可以斷
◇□P（終將穩定）：  ──────────P──P──P──P──P──▶  某一刻起 P 再也不走
```

用你的維運直覺對照：一個 flapping 的服務——當了又起、起了又當——滿足 □◇healthy，永遠不滿足 ◇□healthy。「它總會回來」與「它終將穩定」是兩個強度的承諾，監控圖上一眼可辨，公式上差一個字母的順序。方向只有一邊成立：◇□P ⇒ □◇P（從此不走，當然反覆出現）；反向不成立，flapping 就是反例。

### ⤳：每一次都會等到

第三個常用算子是 **⤳（leads to，ASCII 寫作 `~>`）**，定義是縮寫：

P ⤳ Q ≜ □(P ⇒ ◇Q)

讀法：「**每當** P 成立，**之後**（含當下）Q 終將成立。」注意 □ 在最外面——這不是「第一次 P 之後會有 Q」，是每一次。對照工程語感：「每一筆 retry 都終將得到回應」是 ⤳；「總有一筆 retry 得到回應」只是 ◇。

它的否定值得先寫下來，之後讀反例會用到：¬(P ⤳ Q) ≡ ◇(P ∧ □¬Q)——「存在某個時刻，P 成立了，而 Q 從此永不發生」。違反 leads-to 的證據是一條**無限**的尾巴，不是一個時間點。記住這個形狀，ch09 講 TLC 找 liveness 反例時它會以「壞循環」的樣子回來。

### ⟨A⟩_v：與 [A]_v 成對的另一半

ch06 給過 [A]_v ≜ A ∨ (v′ = v)——「A 或者不動」，stuttering 的免責條款。它有個對偶的兄弟，本章 fairness 的定義要用：

⟨A⟩_v ≜ A ∧ (v′ ≠ v)　（ASCII：`<<A>>_v`）

讀作「貨真價實的 A 步」：既滿足 A，又真的動了 v。兩兄弟的分工：

| 記號 | 定義 | 用途 | 典型位置 |
|---|---|---|---|
| [A]_v | A ∨ (v′ = v) | 寬容：允許不動 | □[Next]_vars——「每一步要嘛合法要嘛不動」 |
| ⟨A⟩_v | A ∧ (v′ ≠ v) | 嚴格：必須真的動 | ◇⟨A⟩_v——「終將發生一個真正的 A 步」 |

為什麼 fairness 必須用 ⟨ ⟩ 這一半？因為「發生」如果允許 stuttering 充數，承諾就是空的——系統可以宣稱「我做了一步 A，只是這步剛好什麼都沒改」。下標 _v 同時保住了 ch06 講的 stuttering 不敏感性：所有 TLA 公式都得對「插入不動的步」免疫，⟨A⟩_v 用「v 必須真的變」把這件事釘死。

## safety 與 liveness：有限可反駁 vs 永遠可補救

詞彙齊了，現在把 ch02 那句一句話對比升級成正式定義。本書採用的是 Lamport 對 Alpern–Schneider 定義的改寫（出處見延伸閱讀；他們的原始定義用拓撲語言，對 stuttering 不敏感的性質兩者等價）。先約定：把有限的狀態序列 s 看成「之後永遠停在最後一個狀態」的無限 behavior（ch02 的老慣例），於是有限序列也可以談滿不滿足一條性質。

> **safety**：性質 P 是 safety，若且唯若對每條 behavior σ：σ ⊨ P ⟺ σ 的**每個有限前綴**都滿足 P。
>
> **liveness**：性質 P 是 liveness，若且唯若**任何**有限狀態序列都能延伸成一條滿足 P 的 behavior。

白話翻譯，這是本章你最該帶走的兩句：

- **safety 是有限可反駁的**：σ 違反 P，必定存在一個最短的前綴已經回天乏術——那個前綴的最後一步就是犯罪現場，你可以指著它定罪，後面不用看。
- **liveness 是永遠可補救的**：不管目前的歷史多難看，都存在一種未來能把 P 圓回來。所以**任何有限前綴都反駁不了 liveness**——「再等等」永遠是合法辯護。違反 liveness 的證據必須是一條完整的無限 behavior。

拿幾條公式過刀：

| 公式 | 分類 | 理由 |
|---|---|---|
| □P（P 是狀態述語） | safety | 第一個違反 P 的狀態就是現場 |
| ◇P | liveness | 任何前綴都能補：接一個滿足 P 的狀態就贖回來了 |
| □◇P | liveness | 同上，而且要補幾次都行 |
| ◇□P | liveness | 接上「從此永遠 P」的尾巴即可 |
| P ⤳ Q | liveness（只要 Q 不是矛盾式） | 接一個滿足 Q 的狀態，所有欠的債一次還清 |
| Init ∧ □[Next]_vars | safety | 第一個非法的步就是現場（這是個定理，出處見延伸閱讀） |

表的最後一行是本章的軸心，值得放大：**你在 ch06 學會的整套 Init ∧ □[Next]_vars，不管 Init 和 Next 寫得多精緻，都只是一條 safety 性質。** 直覺論證：這條公式的任何違反——起點不對、某步非法——都發生在有限位置；反過來，一條每步都合法的 behavior 不管多消極都滿足它。從 s₀ 起永遠 stuttering 的「原地踏步」behavior 是它的合法公民。所以**任何**非平凡的 liveness 都不可能是它的推論——這不是你 spec 寫得不好，是這個公式形狀的數學極限。

兩個邊界案例，幫你校準直覺：

**「90 秒內必回應」是 safety，不是 liveness。** 等到第 91 秒還沒回應，現場就有了——有限可反駁。你的 SLA、timeout、告警規則全是這一型：工程實務把「終將」改寫成「期限內」，正是因為 liveness 沒辦法監控，而 safety 可以。代價是你得把時鐘建進模型才能談「90 秒」（本書不建模時間，ch02 的抽象帳記過這筆）；以及，期限內沒發生≠永遠不發生——把告警當 liveness 反例是範疇錯誤，陷阱表會回收。

**Alpern–Schneider 分解定理**：任何性質都可以寫成一條 safety 與一條 liveness 的合取。這是 1985 年的經典結果（本書不證，見延伸閱讀），但它對你寫 spec 的意義很直白：任何「規格」都拆得成「別做錯事」＋「要把事做完」兩張清單，而這兩張清單的反例形狀、檢查演算法（ch09）、證明技術（ch14）全部不同。先分類、再動手，是時序性質的第一條紀律。順帶一提：既是 safety 又是 liveness 的性質只有一條——恆真。紙上推演題 4 讓你親手證它，證完你會對這兩個定義的咬合方式有肌肉記憶。

## AllPaid：□[Next]_vars 給不了的承諾

回到結算系統 v0（ch06 的 spec：變數 queue、working、ledger；動作 Fetch(c, m) 取訊息、Settle(c) 入帳；Spec ≜ Init ∧ □[Next]_vars）。全書的 liveness 基準性質，現在正式命名：

> **`AllPaid`：每則訊息終會入帳。**

寫成時序公式（ledger[m] 本身是布林值，ch06）：

```tla
AllPaid == \A m \in Msgs : <>ledger[m]
```

內文寫法：AllPaid ≜ ∀ m ∈ Msgs : ◇ledger[m]。逐字讀：對每一則訊息 m，behavior 上存在某個位置，ledger 在那裡標記 m 已入帳。注意 ∀ 在 ◇ 外面——每則訊息**各自**終將入帳，不要求同時。

它是 liveness（◇ 形，有限前綴永遠反駁不了）。那麼：Spec ⇒ AllPaid 成立嗎？

**不成立，而且輸得毫無懸念。** 反例一：σ_idle——s₀ 之後永遠 stuttering。每一步都被 [Next]_vars 的免責條款接住，Spec 滿分通過；ledger 永遠全 FALSE，AllPaid 陣亡。反例二（更陰一點）：Fetch(c1, m1) 之後永遠 stuttering——做了一半、躺著不動，照樣合法。這就是任務交代的「忘了 fairness」的第一種死法：**你以為 liveness 藏在 spec 裡，其實 spec 對它隻字未提**；一旦真的去檢查（ch09 的 TLC 也會這樣告訴你），主張全滅，反例還是最便宜的那種。而第二種死法更危險：你從來沒把 AllPaid 寫下來檢查，於是「它當然成立」以信仰的形式活在你心裡——直到結算季卡單。

缺的東西叫 fairness。

## Fairness：WF 與 SF

### fairness 是什麼：只砍劇本，不立新法

fairness 是加在 Spec 後面的一個合取項：

FairSpec ≜ Init ∧ □[Next]_vars ∧ L

其中 L 是一條 liveness 公式。它的作用是把 behavior 集合**砍小**：那些「明明可以做事卻永遠拖著」的無限劇本，從此不算系統的合法行為。兩件事必須先說死：

- **fairness 不新增任何動作、不禁止任何單一步。** 它管的是無限的調度模式，不是某一步能不能走。已經發生的有限歷史，fairness 一個字都改不了。
- **不是隨便一條 liveness 都配當 fairness。** 合格的 fairness 有一條判準（Lamport 的定義，見延伸閱讀）：加上 L 之後，不可以把 safety 部分的任何有限前綴判成死路——你永遠不會「走著走著就注定違反 L」。直覺版：fairness 只能逼系統做**它本來就被允許做**的事，不能偷偷立新法。隨手寫一條 □◇(…) 塞進 spec，很可能在暗中禁止了 Next 允許的步，spec 從此言行不一。好消息是：接下來的 WF 與 SF（套在 Next 的子動作上）自動滿足這條判準——這正是 TLA+ 要你用它們、而不是手寫時序雜湊的原因。

### WF：持續可做，終究會做

**Weak fairness**，定義（這是本章最重要的兩條公式之一，逐字讀）：

WF_v(A) ≜ ◇□(ENABLED ⟨A⟩_v) ⇒ □◇⟨A⟩_v

- 前件 ◇□(ENABLED ⟨A⟩_v)：「從某一刻起，真正的 A 步**持續**可行」（ENABLED 是 ch06 掛過號的那個「走得出去」述語——欠的帳今天還）。
- 後件 □◇⟨A⟩_v：「真正的 A 步發生無限多次」。
- 合起來：**一個動作不可以永遠可做卻永遠不做。** 等價的反面讀法：behavior 裡不存在這樣的尾巴——A 一路 enabled，卻一步都沒發生。

注意後件是 □◇（無限多次），不是 ◇（一次）。原因：fairness 描述的是長期服務，「做一次就退休」對反覆到來的工作毫無意義；而只要前件持續成立，每做完一次 A 又持續 enabled，承諾就繼續生效——□◇ 正是這個「每次都會再做」的形狀。

### SF：反覆可做，終究會做

**Strong fairness**：

SF_v(A) ≜ □◇(ENABLED ⟨A⟩_v) ⇒ □◇⟨A⟩_v

跟 WF 只差前件的兩個字母：◇□ 變 □◇。WF 要求「**持續** enabled」才觸發承諾；SF 只要求「**反覆** enabled」——哪怕中間一直被打斷，只要可行性無限多次回來，A 就終究要發生（而且無限多次）。

兩者的強弱關係：**SF_v(A) ⇒ WF_v(A)**。理由一行：持續 enabled 蘊涵反覆 enabled（◇□E ⇒ □◇E），所以 SF 的前件更容易成立、承諾觸發得更頻繁，是更強的條款。對寫 spec 的你來說：SF 是更重的**假設**——它排除更多劇本，換句話說，你對調度器、對維運、對世界要求得更多。

### 用你的 SQS 直覺讀一遍

把「consumer c 入帳」當作動作 A：

- **WF ≈ consumer 持續健康就會消費。** 只要 c 手上有訊息、行程活著、沒人打斷——也就是 Settle 持續 enabled——它終究會把帳入掉。這對得起一台不會當機的 worker：OS 調度器再怎麼偏心，也不會永遠跳過一個 ready 的執行緒。
- **SF ≈ 反覆 crash-restart 也終會消費。** c 每拿到訊息就 crash，visibility timeout 把訊息收回去，K8s 把 pod 拉起來，訊息又被拿到……Settle 的可行性像壞掉的日光燈一樣閃爍：enabled、disabled、enabled、disabled。WF 的前件 ◇□ENABLED **永遠不成立**——它從頭到尾沒有持續 enabled 過——於是 WF 空洞地滿足，什麼都不保證。SF 的前件 □◇ENABLED 成立（可行性無限多次回來），所以 SF 強迫入帳終究發生。

一句話總結差異：**WF 管「沒人理它」的飢餓，SF 管「反覆被打斷」的飢餓。** 你的系統裡兩種飢餓都真實存在：前者是調度不公，後者是 crash-restart、搶鎖失敗、重試風暴。

### v0 的定理：FairSpec ⇒ AllPaid

現在給 AllPaid 配 fairness。v0 的基準選擇是最便宜的一條——對整個 Next 的 weak fairness：

```tla
FairSpec == Spec /\ WF_vars(Next)

THEOREM FairSpec => AllPaid
```

WF_vars(Next) 讀作：「只要系統還有任何合法的步可走，就不可以永遠不走。」這是對「系統整體不會擺爛」的最低限度假設。它為什麼在 v0 就足夠買到 AllPaid？論證如下（工程師嚴謹的示意——liveness 證明的系統性工具本書不展開，ch14 淺談；但這條論證的每一步都站得住）：

⟨1⟩1. 任何滿足 Spec 的 behavior，真正的步（非 stuttering）至多 4 步。
　　理由：定義剩餘工作量 M ≜ 2·|queue| ＋ |{c ∈ Consumers : working[c] ≠ "idle"}|。逐動作驗：Fetch 讓 |queue| 減 1、忙碌數加 1，M 淨減 1；Settle 讓忙碌數減 1，M 減 1。M 不會是負數，初始 M = 2·2 ＋ 0 = 4。
⟨1⟩2. 所以存在位置 k，從 k 起全是 stuttering——系統凍結在某個狀態 s_k。
⟨1⟩3. 在 FairSpec 下，s_k 必須讓 ⟨Next⟩_vars 不再 enabled。
　　理由：stuttering 不改變狀態。若 ⟨Next⟩_vars 在 s_k enabled，它從 k 起**持續** enabled，WF_vars(Next) 的前件成立，要求真正的 Next 步發生無限多次——與「從 k 起全是 stuttering」矛盾。
⟨1⟩4. Next 不 enabled ⇒ queue = {} 且所有 working[c] = "idle"。
　　理由：只要有 consumer 手上有訊息，Settle 就 enabled，所以全員 "idle"；全員閒著時只要 queue 非空，Fetch 就 enabled，所以 queue = {}。
⟨1⟩5. queue = {} ∧ 全員 "idle" ⇒ ∀ m ∈ Msgs : ledger[m]。
　　理由：ch02 驗過的「恰好一處」——每則訊息恰在佇列、某個 consumer 手上、或帳本三者之一（Fetch 把它從佇列搬到手上、Settle 從手上搬進帳本，沒有動作讓訊息消失或複製；要把這句話升級成歸納證明，手法就是 ch05 的 IndPay 同款）。前兩處都空了，只剩帳本。
⟨1⟩6. Q.E.D. 從位置 k 起 ledger 全真；每個 ◇ledger[m] 在位置 k 得到見證。∎

注意這個證明的液壓從哪來：⟨1⟩1 的量尺 M **每走一步真步就嚴格遞減**——v0 的狀態圖是一張有限的 DAG（ch02 畫過），唯一的死路就是全入帳。WF_vars(Next) 只負責把系統推下去，地形保證它只能滾到正確的終點。這種「遞減量尺」論證是 liveness 證明的雛形，ch14 會再見到它。

### Requeue 進場：WF 的崩塌現場

地形一變，這套便宜的 fairness 立刻破產。把 ch06 紙上推演題 1 的 Requeue 加進 Next（visibility timeout 到期，訊息回佇列）：

```tla
Requeue(c) == /\ working[c] # "idle"
              /\ queue' = queue \cup {working[c]}
              /\ working' = [working EXCEPT ![c] = "idle"]
              /\ UNCHANGED ledger
```

Requeue 讓 M 淨加 1（佇列 +2、忙碌 −1）：量尺壞了，DAG 長出環。具體的殺手是這條 behavior——

```text
             Fetch(c1, m1)
┌─────────────┐      ┌─────────────┐
│ s0：m1 在 Q │─────▶│ s1：m1 在 c1│      σ_loop ≜ s0 → s1 → s0 → s1 → …
│ ledger 全 F │◀─────│ ledger 全 F │      （c2 全程閒置，m2 全程在佇列）
└─────────────┘      └─────────────┘
             Requeue(c1)
```

σ_loop 永遠在取與放之間鬼打牆，ledger 全程 FALSE。現在逐條 fairness 過堂：

| fairness 條款 | σ_loop 的下場 | AllPaid |
|---|---|---|
| （無） | 活得好好的——連 σ_idle 都活著 | 不成立 |
| WF_vars(Next) | **活著**。σ_loop 每一步都是貨真價實的 Next 步，後件 □◇⟨Next⟩_vars 直接成立，WF 滿分通過——它只要求「有在動」，沒要求「動對方向」 | 不成立 |
| 再加 WF_vars(Settle(c1)) | **還是活著**。ENABLED ⟨Settle(c1)⟩_vars 在 s1 為真、在 s0 為假，無限閃爍；前件 ◇□ENABLED 永不成立，WF **空洞地滿足**——這就是「該用 SF 卻用了 WF」的教科書現場 | 不成立 |
| 改加 SF_vars(Settle(c1)) | **死了**。前件 □◇ENABLED 成立（每個 s1 都 enabled），SF 要求 ⟨Settle(c1)⟩_vars 步發生無限多次，σ_loop 一次都沒有——出局 | 這隻反例被殺掉（完整論證見紙上推演題 3） |

三行教訓：

1. **對 Next 整體的 fairness 在有環的世界裡幾乎不值錢**——「忙碌」與「進展」是兩回事，你的 pipeline 卡單時 CPU 也很忙。
2. **WF 會空洞地滿足**。enabledness 一閃爍，◇□ 的前件就永遠湊不齊，WF 變成一紙從不觸發的保單。最毒的是它「成立」——你檢查 fairness 條款本身不會發現任何異常，要檢查的是 liveness 結論。
3. **SF 是對的工具，但它是更貴的假設**。SF_vars(Settle(c)) 翻譯回現實是：「不管 c 被打斷多少次，只要它無限多次回到可入帳的狀態，入帳終究發生。」誰兌現這句話？K8s 的 restart 策略加上 SQS 的 redelivery，再加上「程式不會每次都在同一行 crash」的賭注。寫下 SF 的那一刻，你是在替這整組機制簽名背書。

還有一個容易漏的細節：SF_vars(Settle(c)) **單獨**也不夠——它管「拿了會結」，不管「有人去拿」。σ_idle（從頭躺平）讓 Settle 永遠不 enabled，SF 空洞滿足，AllPaid 照死。所以 v0＋Requeue 的世界裡，誠實的組合是 **WF_vars(Next) ∧ ∀ c ∈ Consumers : SF_vars(Settle(c))**：前者保證系統不擺爛，後者保證忙碌終會轉成進展。fairness 要蓋住「好事」的整條動作鏈，缺一環，鏈就斷在那一環。

### 決策框架：不加、WF、還是 SF

| 問自己 | 答案指向 |
|---|---|
| 我主張的性質是 safety 還是 liveness？ | 純 safety → **完全不加 fairness** 是最誠實的寫法（fairness 只會砍 behavior，所有 safety 結論原封不動，但多寫就是多欠解釋） |
| 這個動作一旦 enabled，會被**別的動作**關掉嗎？ | 不會（只有它自己做了才消失）→ WF 夠 |
| 會被關掉，但可行性會反覆回來（redelivery、restart、重試）嗎？ | 會、且我需要它終究發生 → SF |
| 這條 fairness 對應哪個**現實機制**？ | OS 調度器、K8s restart、SQS redelivery……指認不出來＝你寫的是願望，不是假設——刪掉它，看主張還站不站得住 |

## Worked example：四條白話性質的完整旅程

把本章的工具串成一條流水線，對結算系統 v0 走完整趟：**白話 → 分類（拿「有限前綴反駁得了嗎」過刀）→ 時序公式 → 標 fairness**。四條性質一條一條來，不跳步。

**W1：「同一 msgId 至多入帳一次。」**

- 分類測試：違反它＝某一刻出現「已入帳的訊息又回到佇列或手上」（ch06 的狀態層改寫）。那一刻就是犯罪現場，有限前綴定罪 ⇒ **safety**。
- 公式：□NoDoublePay（NoDoublePay 是 ch06 的狀態述語，□ 把它升格成對整條 behavior 的主張——「invariant」的正式形狀就是 □ 套狀態述語）。
- fairness：**不需要**。safety 的成立與調度無關；v0 的證明 ch05 已經給了，一個 fairness 的字都沒用到。

**W2：「每則訊息終會入帳。」**

- 分類測試：看到第 10⁶ 步還沒入帳，能定罪嗎？不能——「再等等」永遠合法 ⇒ **liveness**。
- 公式：**AllPaid ≜ ∀ m ∈ Msgs : ◇ledger[m]**。
- fairness：v0 配 **WF_vars(Next)** 就夠（上節定理，靠的是 v0 地形是 DAG）；一旦有 Requeue／crash／redelivery 這類「回頭路」動作，升級成 WF_vars(Next) ∧ ∀ c : SF_vars(Settle(c))（上節攻防）。

**W3：「被拿走的訊息，不會爛在 consumer 手裡。」**

- 分類測試：c1 拿著 m1 十萬步沒入帳——還是不能定罪 ⇒ **liveness**。
- 公式：∀ c ∈ Consumers : ∀ m ∈ Msgs : (working[c] = m) ⤳ ledger[m]。注意 ⤳ 自帶的 □：**每一次**被拿起都要兌現，不是僥倖一次。
- fairness：v0 下 FairSpec 同樣足夠（⟨1⟩2–⟨1⟩5 的凍結點是全入帳狀態，途中任何「拿著」終究匯入那裡）。
- 跟 W2 的差別值得咀嚼：W3 的承諾只蓋「**曾被拿起**的訊息」。一條訊息從頭到尾沒人理——W3 對它前件為假，**空洞成立**（ch03 的老朋友），W2 才抓得到它。兩條都要寫，恰恰因為它們在「沒人拿」這個劇本上一個有牙齒、一個沒有。

**W4：「結算季終將收工：佇列清空、全員下工，而且從此保持。」**

- 分類測試：「還沒收工」永遠反駁不了「終將收工」⇒ **liveness**。
- 公式：◇□(queue = {} ∧ ∀ c ∈ Consumers : working[c] = "idle")。◇□ 的形狀——不只到達，還要**穩定**：到達後不再有任何訊息冒出來、沒有 consumer 又拿起東西。
- fairness：WF_vars(Next)（v0 的凍結論證 ⟨1⟩2–⟨1⟩4 給的正是這個終態）。
- 加碼觀察：W4 ∧ □(恰好一處) ⇒ W2——收工狀態裡訊息無處可去，只能在帳本。性質之間有蘊涵結構，挑對「主性質」可以讓其他主張搭便車；但反向不成立（W2 不保證**穩定**收工），所以 W4 不是冗餘。

收進一張表（這張表的格式，是你之後對任何系統做性質盤點的範本）：

| # | 白話 | 分類 | 時序公式 | fairness |
|---|---|---|---|---|
| W1 | 同一 msgId 至多入帳一次 | safety | □NoDoublePay | 不需要 |
| W2 | 每則訊息終會入帳 | liveness | AllPaid ≜ ∀ m ∈ Msgs : ◇ledger[m] | WF_vars(Next)（v0）；有重投遞時加 ∀ c : SF_vars(Settle(c)) |
| W3 | 拿起的訊息不爛在手裡 | liveness | ∀ c, m : (working[c] = m) ⤳ ledger[m] | 同 W2 |
| W4 | 終將收工且保持收工 | liveness | ◇□(queue = {} ∧ ∀ c : working[c] = "idle") | WF_vars(Next)（v0） |

## 陷阱與防禦

時序邏輯的坑有個共同氣味：**公式照樣全綠，承諾卻是空的**。每一條照本書的固定問法：它怎麼給你假安全感、你怎麼發現。

| 故障模式 | 它怎麼騙你 | 防禦 |
|---|---|---|
| 以為 □[Next]_vars 自帶進度 | 寫完 spec 覺得「訊息會入帳」已經在裡面；σ_idle 是免費反例，你卻從沒把 liveness 寫下來檢查，信仰一路綠燈 | 每條 liveness 主張白紙黑字寫成公式，旁邊註明「靠哪條 fairness」；註不出來，先去找 σ_idle 形的反例 |
| fairness 掛錯動作 | 給 Fetch 配了 WF、好事卻由 Settle 產生：訊息全被勤奮地拿走，沒有一則入帳，主張照死 | 從「好事」反推動作鏈（取→結），鏈上**每一環**都要有 fairness 蓋住；斷一環，鏈就斷在那 |
| 該 SF 用了 WF | enabledness 被 Requeue／crash／搶鎖反覆關掉，◇□ENABLED 永不成立，WF 空洞滿足——條款本身看不出任何異常 | 問「誰能關掉這個動作的 enabled、會反覆關嗎」；列得出兇手就考慮 SF。檢查的單位是 liveness 結論，不是 fairness 條款 |
| 用過強的 fairness 藏設計缺陷 | 給「維運救場」「TM 復活」之類的動作掛上 SF，liveness 全綠——你不是證明了系統會好，是把結論當假設買進來了（ch11 的 2PC blocking 會正面撞上這題） | 每條 fairness 指認一個現實機制；指認不出來就刪掉重推，看主張還站不站得住。fairness 是**假設**，不是**機制** |
| □◇ 與 ◇□ 弄反 | 想說「終將穩定」寫成「反覆發生」：flapping 的服務滿足 □◇healthy，你以為它收斂了 | 念白話測試句：□◇＝「永遠還會再來」、◇□＝「從此不再離開」；記住 ◇□ ⇒ □◇ 而反向不成立 |
| 拿有限觀察「反駁」liveness | 「等了一小時還沒消費」就回報 liveness 違反——有限前綴反駁不了 liveness，這在定義層就是範疇錯誤 | 分清楚：告警是工程啟發式（很好，繼續用）；要讓「一小時」成為可反駁的主張，得把時鐘建進模型、把性質改寫成 safety——那是另一份 spec |

## 紙上推演

### 題 1：公式 ⇄ 白話互翻（[15 分鐘] ★）

對結算系統 v0，先把 (a)–(c) 翻成時序公式並分類 safety/liveness，再把 (d)–(f) 翻成白話並分類。

(a) 「佇列一旦空了，就永遠空著。」
(b) 「m2 入帳的前提是 m1 已經入帳。」（業務要求的順序）
(c) 「系統會反覆回到全員閒置的狀態。」
(d) ◇□ledger[m1]
(e) (working[c1] ≠ "idle") ⤳ (working[c1] = "idle")
(f) □◇(queue = {}) 與 ◇□(queue = {})——這兩條在 v0 等價嗎？在一般系統呢？

### 推演解答

(a) □(queue = {} ⇒ □(queue = {}))。**safety**：違反＝某一刻空了、後來又冒出東西，那一步就是現場。（v0 沒有動作往 queue 放東西，所以它成立；加了 Requeue 就不成立——性質的真假永遠是相對於 spec 的。）

(b) □(ledger[m2] ⇒ ledger[m1])。**safety**：第一個「m2 已入帳而 m1 還沒」的狀態就是現場。注意這條在 v0 **不成立**——ch02 題 2 的 P3 就是它，反例兩步可達。寫得出來≠成立，分類與驗證是兩道工序。

(c) □◇(∀ c ∈ Consumers : working[c] = "idle")。**liveness**：任何前綴都能補一個全員放下的未來。

(d) 「終將有一刻起，m1 永遠保持已入帳。」**liveness**。在 v0 裡它與 ◇ledger[m1] 等價——因為沒有任何動作把 ledger 翻回 FALSE（帳本單調）。但這個等價是**模型的**性質，不是邏輯的：在「帳可以被沖正」的系統裡，◇P 與 ◇□P 差一整個世界。寫性質時想清楚你要哪一個。

(e) 「c1 不會永遠拿著訊息不放——每次拿起，終將放下。」**liveness**，⤳ 形。順帶：在 v0 放下的唯一途徑是 Settle，所以它幾乎是 W3 的影子；加了 Requeue 之後「放下」多了一條路，這條性質就比 W3 弱了——同樣的白話，模型一變，公式的份量就變。

(f) □◇＝「佇列反覆見底」（允許又被填滿）；◇□＝「佇列終將永遠見底」。一般而言 ◇□ 嚴格強於 □◇（flapping 的佇列滿足 □◇ 而不滿足 ◇□）。在 v0 裡兩者等價：queue 只減不增（Fetch 拿走、沒人放回），見底一次就永遠見底。又一次：等價靠的是模型的單調性，不是算子。

### 題 2：對給定 behavior 判定 □◇ 與 ◇□（[15 分鐘] ★★）

令 d 為佇列深度。三條無限 behavior：

- σ_A：d = 1, 0, 1, 0, 1, 0, …（producer 與 consumer 永遠拉鋸）
- σ_B：d = 1, 0, 1, 0, 0, 0, 0, …（拉鋸兩輪後永遠歸零）
- σ_C：d = 1, 1, 1, 1, …（永遠卡著一筆）

對每條 behavior 判定：(i) □◇(d = 0)；(ii) ◇□(d = 0)；(iii) (d = 1) ⤳ (d = 0)。

### 推演解答

| | (i) □◇(d=0) | (ii) ◇□(d=0) | (iii) (d=1) ⤳ (d=0) |
|---|---|---|---|
| σ_A | ✓ 0 無限多次出現 | ✗ 沒有任何位置之後「永遠是 0」——1 永遠還會回來 | ✓ 每個 d=1 的位置，下一步就是 0 |
| σ_B | ✓ 尾巴全是 0 | ✓ 從第 4 個位置起永遠 0 | ✓ 前兩個 1 各自等到了 0；之後再無 1，⤳ 對空前件免費成立 |
| σ_C | ✗ 0 從未出現 | ✗ 同左 | ✗ 位置 0 的 d=1 之後 0 永不出現——¬(P ⤳ Q) ≡ ◇(P ∧ □¬Q) 的見證就是整條尾巴 |

兩個檢查點：σ_A 是「◇□ ⇒ □◇ 的反向不成立」的標準見證；σ_C 的 (iii) 提醒你 liveness 反例是**無限**的——你必須對整條尾巴論證「0 永不出現」，指著任何有限段都不夠。這就是 ch09 之前你該有的體感：liveness 反例 trace 一定帶一個循環記號（「之後永遠重複這段」），不然它什麼都沒證明。

### 題 3：哪條 fairness 救得了 AllPaid？（[25 分鐘] ★★★）

迷你結算機：Msgs = {m1}、Consumers = {c1}，動作 Fetch(c1, m1)、Settle(c1)、Requeue(c1)（定義同本章）。狀態只有三個：

- A ≜ ⟨queue = {m1}, working = (c1 ↦ "idle"), ledger = (m1 ↦ F)⟩
- B ≜ ⟨queue = {}, working = (c1 ↦ m1), ledger = (m1 ↦ F)⟩
- C ≜ ⟨queue = {}, working = (c1 ↦ "idle"), ledger = (m1 ↦ T)⟩

邊：A →Fetch→ B；B →Settle→ C；B →Requeue→ A。對下面五種配置，逐一判定 Spec ∧（該配置）⇒ AllPaid 是否成立；不成立的給出反例 behavior，成立的給出論證。

(1) 無 fairness；(2) WF_vars(Next)；(3) WF_vars(Settle(c1))（單獨）；(4) SF_vars(Settle(c1))（單獨）；(5) WF_vars(Next) ∧ SF_vars(Settle(c1))。

### 推演解答

**(1) 不成立。** 反例 σ_idle：A 之後永遠 stuttering。

**(2) 不成立。** 反例 σ_loop：A → B → A → B → …。每步都是真 Next 步，□◇⟨Next⟩_vars 成立，WF_vars(Next) 滿足；ledger 永遠 F。WF(Next) 殺得掉 σ_idle（A 上 Next 持續 enabled、卻永不發生——違反），但殺不掉「忙而無功」。

**(3) 不成立，雙重死法。** 反例一還是 σ_idle：Settle 在 A 永不 enabled，WF 前件假、空洞滿足，而又沒有任何條款逼系統離開 A。反例二是 σ_loop：ENABLED ⟨Settle(c1)⟩ 在 B 真、A 假，反覆閃爍，◇□ 前件不成立，WF 又一次空洞滿足。教訓：fairness 掛在最後一環、卻沒人保證前面的環會動，照樣全盤皆輸。

**(4) 不成立。** σ_idle 又活了：Settle 從未 enabled，□◇ENABLED 為假，SF 空洞滿足。SF 比 WF 強，但「強」只強在閃爍的場景；對「從頭躺平」兩者一樣無力。

**(5) 成立。** 論證（這個三狀態機小到可以走完全程）：

⟨1⟩1. 設 σ 滿足 Spec ∧ WF_vars(Next) ∧ SF_vars(Settle(c1))，反設 ledger 永遠 F——即 σ 永遠在 {A, B} 內。
⟨1⟩2. σ 含無限多個真步。理由：A、B 上 Next 都 enabled（A 有 Fetch、B 有 Settle 與 Requeue）；若從某刻起全 stuttering，⟨Next⟩_vars 持續 enabled 卻不再發生，違反 WF_vars(Next)。
⟨1⟩3. 在 {A, B} 內的無限真步只能是 A ⇄ B 永遠往返（A 的真步只有去 B，B 不去 C 的真步只有回 A），所以 B 出現無限多次。
⟨1⟩4. 於是 ENABLED ⟨Settle(c1)⟩_vars 無限多次成立，SF_vars(Settle(c1)) 要求 Settle 真步發生無限多次——但 σ 連一次都沒有（發生即離開 {A, B}，與 ⟨1⟩1 矛盾）。
⟨1⟩5. Q.E.D. 反設不成立，◇ledger[m1] 對每條這樣的 σ 成立。∎

注意 ⟨1⟩4 的句式：SF 不是「終將做一次」，是「無限多次 enabled ⇒ 無限多次做」——這裡用「一次都沒有」打出矛盾，剛剛好。也注意整個論證對 Requeue 發生幾次毫無假設：crash-restart 一百萬次也好，SF 保證入帳終究插隊成功。這就是「SF ≈ 反覆 crash-restart 也終會消費」的數學內容。

### 題 4：既是 safety 又是 liveness 的性質只有一條（[15 分鐘] ★★★）

證明：若性質 P 同時是 safety 與 liveness，則 P 恆真（每條 behavior 都滿足它）。提示：對任意 behavior 的任意有限前綴，先用 liveness、再用 safety。

### 推演解答

⟨1⟩1. 任取 behavior σ，任取它的有限前綴 s。
⟨1⟩2. 由 liveness 定義，s 可延伸成某條滿足 P 的 behavior σ′。
⟨1⟩3. 由 safety 定義套在 σ′（「滿足 ⟺ 每個前綴滿足」的左到右）：σ′ 的每個有限前綴都滿足 P；s 是 σ′ 的前綴，故 s ⊨ P。
⟨1⟩4. s 是任取的，所以 σ 的**每個**有限前綴都滿足 P；再由 safety 定義套在 σ（右到左）：σ ⊨ P。
⟨1⟩5. Q.E.D. σ 任取，P 對所有 behavior 為真。∎

兩個回味。其一，safety 的定義在 ⟨1⟩3 與 ⟨1⟩4 各用了一個方向——這條「⟺」不是裝飾。其二，這個定理是分解定理的暗面：safety 與 liveness 的交集只剩恆真，所以「拆成兩半」拆得乾淨、不重疊；Alpern–Schneider 的原始論文用拓撲語言講同一件事（safety 是閉集、liveness 是稠密集），有興趣見延伸閱讀。

## 自我檢核

口頭回答，講得出來才算過：

1. safety 與 liveness 的正式定義各是什麼？「90 秒內必回應」為什麼是 safety 而不是 liveness？這對監控告警意味著什麼？
2. □◇P 與 ◇□P 各自的白話是什麼？用一個 flapping 服務說明哪邊成立哪邊不成立；誰蘊涵誰？
3. 為什麼 Init ∧ □[Next]_vars 形式的公式永遠只是 safety？σ_idle 在這裡扮演什麼角色？
4. 逐字念出 WF_v(A) 與 SF_v(A) 的定義，說出唯一的差異在哪兩個字母、那兩個字母換掉了什麼意思。為什麼後件是 □◇ 而不是 ◇？
5. 用 SQS 與 consumer 講一遍：什麼場景 WF 夠用、什麼場景非 SF 不可？「WF 空洞地滿足」具體是怎麼發生的？
6. AllPaid 的公式是什麼？v0 為什麼配 WF_vars(Next) 就夠？加了 Requeue 之後這個選擇怎麼崩、換成什麼？
7. 為什麼說 fairness 是「假設」而不是「機制」？拿到一條 SF，你會問它什麼問題才簽收？
8. ⟨A⟩_v 與 [A]_v 的定義差在哪？fairness 的定義為什麼必須用 ⟨ ⟩ 那一半？

## 延伸閱讀

- **Leslie Lamport, “Safety, Liveness, and Fairness”（2019-05-26 講義）**：`https://lamport.azurewebsites.net/tla/safety-liveness.pdf`。本章 safety/liveness 定義與 WF/SF 等價讀法的直接出處，短短 8 頁；第 4 節列了 WF 的五種等價說法，把它們讀到「顯然等價」是最好的自測。（2026-06 開頁核對）
- **Specifying Systems 第 8 章 “Liveness and Fairness”**（Lamport, 2002）：免費 PDF 見 `https://lamport.azurewebsites.net/tla/book.html`。WF/SF 的教科書版，含本章沒展開的「fairness 條款的合取怎麼仍是 fairness」等細節。（2026-06 查證頁面與免費 PDF）
- **Bowen Alpern & Fred B. Schneider, “Defining Liveness”**, *Information Processing Letters* 21(4):181–185, 1985。liveness 正式定義與「任何性質＝safety ∧ liveness」分解定理的原始出處；正文不到五頁，拓撲味比本書直覺版重（他們的 safety 定義與本章版本在 stuttering 不敏感性質上等價——Lamport 上面那份講義有說明）。期刊原文在付費牆內，先讀 Lamport 的轉述也夠用。
- **Hillel Wayne, “Weak and Strong Fairness”**：`https://www.hillelwayne.com/post/fairness/`。用一個 succeed/fail/retry 的 worker 把「WF 救不了反覆失敗、SF 可以」演了一遍，與本章 Requeue 攻防互為印證。（2026-06 開頁核對）
- **learntla.com 的 “Temporal Properties” 一章**（Hillel Wayne）：`https://learntla.com/core/temporal-logic.html`。□、◇、⤳ 與 fairness 在工具使用者視角的長相（PlusCal 用 `fair`／`fair+` 標 WF／SF）；本書不動鍵盤，但看一眼「這些東西在 spec 檔裡長怎樣」對 ch08 有幫助。（2026-06 開頁核對）
