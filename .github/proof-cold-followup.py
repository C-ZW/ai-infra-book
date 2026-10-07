from pathlib import Path
R=Path('books/proof-evolution'); S=R/'book-src'
def edit(name,old,new):
 p=S/name;t=p.read_text();assert t.count(old)==1,(name,old[:60],t.count(old));p.write_text(t.replace(old,new))
def block(name,heading):
 t=(S/name).read_text();a=t.index('## '+heading+'\n');b=t.find('\n## ',a+4)
 if b<0:b=t.index('\n[^',a)
 return t[a:b].rstrip()
edit('ch02-tablets-and-algorithms.md','數值間的吻合讓解讀得到支持。','把這項吻合寫成現代算式，就是 30 × 30547/21600 = 30547/720 = 42 + 25/60 + 35/60²。這是在檢查數值轉寫的一致性，不是多出一份古代計算過程的記錄。數值間的吻合讓解讀得到支持。')
edit('ch03-greek-deduction.md','在本章中，公理是較寬的稱呼，指一套推理所接受的基本陳述；談到歐幾里得文本本身，仍保留公設與共同概念的區別。','用語先固定：本書以「公理」作現代總稱，指推理接受的基本陳述；「公設」與「共同概念」則保留歐幾里得文本本身的分類，不是再往上或往下的一層新前提。')
edit('ch04-plural-traditions.md','以下再用現代語言把通常的三角形面積理由補全。對一個底為 b、高為 h，垂足落在底邊內的三角形，','以下再用現代語言把通常的三角形面積理由補全。從頂點向底邊所在直線作垂線，交點稱為「垂足」；它可能在底邊內、端點或延長線上。對一個底為 b、高為 h，垂足落在底邊內的三角形，')
edit('ch05-algebra-and-symbols.md','也就是比較的量要有相容的量綱。','也就是比較的量要有相容的量綱：例如兩段長度可以直接相加，長度卻不能直接和面積相加；運算時要知道自己比較的是哪一種量。')
edit('ch07-axioms-and-models.md','其中 m 是斜率。每個實數 m 都給出一條經過 P 的模型直線。','其中 m 是斜率。鉛直線 x = 0 不在這個寫法內，另看便知它在 (0, 0) 與 ℓ 相交。以下只分類非鉛直線；每個實數 m 都給出一條經過 P 的模型直線。')
edit('ch08-logic-and-foundations.md','這裡的承諾涵蓋每個符合前提的模型。','這裡的承諾涵蓋每個符合前提的模型。\n\n這個「每個」還有一個邊界：若根本沒有模型滿足 T，就找不到違反結論的 T 模型，因而 T ⊨ φ 對任何 φ 都成立。這叫空真，不表示 T 成功描述了一個世界。用模型說明獨立性時，必須真的建立所需模型，不能只把「所有模型都如此」當作模型存在的證據。')
edit('ch09-incompleteness-and-computation.md','G 的編號正好是 sub(h, h)，所以 G 表達了自己在 T 中不可證。','G 的編號正好是 sub(h, h)，所以 G 表達了自己在 T 中不可證。先分清兩個問題：在標準自然數中讀 G，是在問有沒有一份 T 中的 G 證明；在 T 內證 G，則是要求依 T 的規則交出那份證明。下文會利用兩者的連結導出限制。理論名稱 T 不能省略：換到較強的理論，原來那個 G 可能變成可證，並非永遠沒有任何理論能處理它。')
edit('ch10-construction-and-programs.md','兩群之中至少一群的平均不低於原值。','若把目前的平均叫 M，兩群平均叫 M_左、M_右，就是 M = (M_左 + M_右)/2。因此 max(M_左, M_右) ≥ M；兩群之中至少一群的平均不低於原值。')
edit('ch11-experiment-and-evidence.md','並對可能的剩餘效應提出上限；','並按當時裝置與判讀條件估計剩餘效應的尺度上限，而不是給出一個帶現代信賴水準的區間；')
old='''這種標準化識別路徑常以三項條件表達。條件可交換性要求：在已調整的基礎條件內，接受哪個安排，不再攜帶足以改變潛在結果分布的選擇資訊。正值性要求：在目標群體中每個需要比較、且有正機率的基礎條件層內，兩種安排的條件機率都大於零。若分派規則使基礎較弱者絕不可能使用，這一層就缺少使用安排的母體比較條件。反過來，即使兩種安排的母體機率都大於零，有限樣本也可能碰巧沒抽到其中一組；那是樣本支撐不足，不能僅憑空白格就斷言母體正值性失敗。一致性要求：一個人實際接受某安排時，觀察結果就是那個安排所定義的潛在結果。這三項是這條估計路徑的充分識別條件的一部分，不能說成所有因果方法永遠只能用的一套必要條件。[^ch13-hernan]'''
new='''先不背名詞，回到表格中基礎較弱的一層。我們想用這層未使用者的結果，推想使用者若沒使用會如何。這個替代公平嗎？若使用者即使不用程式，也會因更有動機而表現不同，只按基礎分層就還不夠。條件可交換性正是在排除這類殘留的選擇差異：調整後，接受哪個安排，不再攜帶會改變潛在結果分布的資訊。

第二個問題是，有沒有比較的機會？若規則使這層人絕不可能使用程式，就沒有使用安排的母體比較條件。正值性要求：在目標群體每個需要比較、且有正機率的條件層內，兩種安排的條件機率都大於零。這和有限樣本碰巧少了一組不同；母體機率雖為正，樣本仍可能沒有抽到，不能只看空白格就宣布正值性失敗。

第三個問題是，比較的安排有沒有說成同一件事？「使用程式」若有人每天練習，有人只註冊一次，就可能混了不同安排。一致性要求：一個人實際接受某安排時，看到的結果，就是該安排所定義的潛在結果。因此版本、時間與使用方式需要先說清楚。

這三項條件與本章的無干擾等設定一起，支撐的是眼前這條標準化識別路徑；**不是所有因果方法都必須照搬的一張通用清單。** 名詞的用途，是把哪一步不能成立說清楚，而不是替分層後的差值自動加上「因果」標籤。[^ch13-hernan]'''
edit('ch13-causality-and-replication.md',old,new)
edit('ch14-computer-assisted-proofs.md','這段小論證完整展示了一種「可約性」：','把剛才的放回步驟縮到四個點，就容易核對：A、B、C 兩兩相連，V 也連到這三點。刪去 V，三角形可用紅、藍、綠三色；把 V 放回去，塗黃即可。這只示範「縮小、著色、接回」為什麼在最多三個鄰點時有效，不是宣稱所有平面圖都有這種頂點。真正困難的正是如何處理不含這種簡單形狀的圖。\n\n這段小論證完整展示了一種「可約性」：')
name='ch15-proof-assistants.md';core=block(name,'讓靈活的工具繞著小核心工作');tiny=block(name,'從三個假設看見一份證明的內部');gap=block(name,'系統可以精確地證明錯的問題')
edit(name,core+'\n\n'+tiny+'\n\n'+gap,tiny.replace('先不使用任何軟體，','先把負責檢查推導的那小部分叫作「核心」。核心像只核對規則的裁判：它不必幫人猜下一步，但收到的紀錄每一步都得合法。先不使用任何軟體，',1)+'\n\n'+gap+'\n\n'+core)
name='ch16-interactive-and-zero-knowledge.md';t=(S/name).read_text();start=t.index('用三個節點可以');end=t.index('\n\n',start);example=t[start:end]
edit(name,example+'\n\n','')
edit(name,'公開的圖是 G₀、G₁，節點數同為 n。',example.replace('用三個節點可以把每一步攤開。','先用三個節點把要比較的對象放在眼前。')+'\n\n把剛才三節點的問題推廣，公開的圖仍稱 G₀、G₁，節點數同為 n。')
edit(name,'假設這一輪抽到 r(1) = v、r(2) = u、r(3) = w。','回到三節點例子，假設這一輪抽到 r(1) = v、r(2) = u、r(3) = w。')
edit(name,'重複二十輪，規定每輪通過才繼續，全部通過才接受。','先把三種承諾放回同一個例子：真命題的兩種挑戰都有答案，談的是完備性；假命題最多答中一種，談的是健全性；真命題的問答透露多少資訊，則留到下一節用模擬器分析。此處縮小的是第二種錯誤率，還沒有證明第三種保密性。\n\n重複二十輪，規定每輪通過才繼續，全部通過才接受。')
name='ch17-ai-and-proof.md';old=block(name,'獎牌分數旁邊必須留下條件');a=old.index('下表的形式驗證狀態');b=old.index('讀表時還要分清楚');prefix=old[:a]
cases='''以下的驗證狀態依原始報告，本書沒有重新執行其中的大型證明專案。先看三個問題：題目由誰翻譯、花多少時間與人力、最後由誰檢查。不同案例的條件不同，所以分開讀，不將分數排成能力榜。

AlphaProof 與 AlphaGeometry 2 在 IMO 2024 的分工，是先由人把題目翻進系統語言。AlphaProof 解出的三題有 Lean 核心檢查，另一道幾何題由專門系統處理，數學家再按競賽規則評分。部分求解耗時達三天，因此這不是與人類同時限的一次作答。放回這些條件，團隊的結果是合計四題、28／42 分，達當年的銀牌分數範圍。

進階 Gemini Deep Think 的 IMO 2025 公告則描述另一種工作：直接讀原題的自然語言，不先由人翻成專門形式語言，交出自然語言解答，由 IMO 協調與評分人員評閱。團隊稱符合 4.5 小時的競賽時限；這項時程是團隊報告的條件，並非以下所述 IMO 對整個系統的驗證。公告結果為五題完整解答、35／42 分，達金牌分數範圍。這不是一份聲稱經 Lean 核心檢查的成果。

Aristotle 的 2025 年 10 月研究報告，又把分工放在別處：原題陳述由人手形式化，中間引理由系統產生與形式化，結果則以形式證明交付。專案公開第 1 至 5 題的 Lean 陳述與證明；所引初稿報告解出 IMO 2025 六題中的五題，達金牌等值表現，但沒有足以確認同等競賽時限的總時程。這一例應先追問正式陳述與證明物件，而不是把「五題」直接當成與上一例相同的實驗。

這三份報告不能單獨回答：在同一輸入語言、同樣人力與相同時限下，誰能解出更多新題。要回答那個問題，還需要共同條件下的評量；把分數並排並不會補出缺少的實驗。

'''
tail=old[b:].replace('讀表時還要分清楚','還要分清楚',1).replace('本表保留 Gemini','本節保留 Gemini',1)
edit(name,old,prefix+cases+tail)
geom=block(name,'翻譯正確，才有理由談原題');edit(name,geom+'\n\n','');edit(name,'## 把靈感放在可以出錯的位置',geom+'\n\n## 把靈感放在可以出錯的位置')
edit('appendix-a-methods.md','## 從前提走到結論','這是讀過章節後的速查，不需要一次學完所有方法。先看直接證明、反證與歸納，再依問題回讀模型、對角化或機器驗證；每節的章節連結才是完整學習路線。\n\n## 從前提走到結論')
edit('appendix-a-methods.md','原命題與逆命題不能混淆','不能倒轉成 B ⇒ A；例如能被 4 整除會是偶數，但 6 是偶數卻不能被 4 整除')
edit('appendix-b-timeline.md','## 容易混淆的術語','## 容易混淆的術語\n\n本表是回讀時的速查，不取代各章的第一次解釋。尤其互動證明的幾個名稱，先抓住同一個小例子：一個人有兩張圖的節點對照，對方想核對卻不直接取得這份對照。\n\n真圖確實只差重新命名，持有對照者能照規則應答，這是完備性要保證的事；兩圖若不同構，仍誤收它們的機率，則由健全性界限控制。零知識問的是另一件事：對真主張，沒有秘密對照、只有公開圖的模擬器，能否重現驗證者看到的紀錄。它不保證假主張也成立。三者的完整問答與前提見[第十六章](ch16-interactive-and-zero-knowledge.md)，與第八章的邏輯完備性不是同一問題。')
edit('appendix-b-timeline.md','起點與歸納步配合自然數的結構','例如先證 P(1)，再證每個正整數 k 都有 P(k) ⇒ P(k+1)，得到所有正整數的 P(n)；其他起點須另明說')
edit('appendix-c-worked-examples.md','在具體數字中，59 和 509 都不在原清單。即使不先證明這兩數各自都是質數，因為','在具體數字中，59 和 509 都不在原清單。因為')
edit('appendix-c-worked-examples.md','令 E_t 表示前 t 輪全部通過。','每多通過一輪，上界再除以二：一輪至多 1/2，兩輪至多 1/4，三輪至多 1/8。這不是假設整段作弊策略毫無關聯，而是每一步即使考慮先前紀錄，條件通過機率仍至多一半。\n\n令 E_t 表示前 t 輪全部通過。')
edit('appendix-d-sources.md','[第十二章的原始統計來源（具名作品、版本與直接網址列於該章註腳，此處不重複列出）](ch12-probability-and-statistics.md)','[Bayes 1763 年論文之重排全文](https://www.gtfp.cs.rhul.ac.uk/pulskamp/Bayes/bayesessay-rjp.pdf)，第一節；[Fisher 1925 年《Statistical Methods for Research Workers》初版轉錄](https://psychclassics.yorku.ca/Fisher/Methods/chap4.htm)，第 IV 章第 20 節；其他來源見第十二章註腳')
edit('appendix-d-sources.md','[第十六章的互動證明原始來源](ch16-interactive-and-zero-knowledge.md)','[Bellare、Goldreich，〈On Defining Proofs of Knowledge〉](https://cseweb.ucsd.edu/~mihir/papers/pok.pdf)，1992-08-26 作者稿，Definition 3.1、§4.4；其他原始來源見第十六章註腳')
p=S/'_meta/outline.md';t=p.read_text().replace('Do not conflate from mathematical certainty only at a conceptual level, no jurisdiction-specific law.','Do not import jurisdiction-specific law into the mathematical argument.');p.write_text(t)
print('Applied bounded cold-read clarifications; no extra review artifacts.')
