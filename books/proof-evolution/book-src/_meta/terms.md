# Terminology ownership

The reader-facing glossary is [appendix-b-timeline.md](../appendix-b-timeline.md). This file records editorial decisions so later revisions do not silently change meanings across chapters.

| Term | Owner / usage decision |
| --- | --- |
| 證明 / 證據 | Ch01 and ch11: deductive proof under stated premises versus empirical support under measurement and modeling conditions. |
| 算法 / 演算法 | Historical algorithms and traditional titles may retain 算法; contemporary computational procedures normally use 演算法. Do not rewrite quoted titles mechanically. |
| 一致性 / 相容性 | Ch08 uses 一致性 and ch09 uses 相容性 for consistency; the glossary explicitly records the synonym. Neither means truth in the intended standard model. |
| 健全性 / 可靠性 | Use 健全性 when referring to logical soundness. General prose may use 可靠性 for ordinary reliability. Ch16 defines protocol soundness and its error bound separately, using 健全性錯誤 for soundness error. |
| 完備性 | Ch08–09 distinguish logical completeness from completeness of a theory. Ch16 uses the same Chinese term for protocol completeness, with a separately stated acceptance guarantee. The glossary labels this 完備性（互動證明）. |
| 數學歸納 / 經驗歸納 | Ch10 and ch11 distinguish a structural proof on natural numbers from generalization supported by observations. |
| 可枚舉 / 可判定 | Ch09 distinguishes eventual listing from a total yes/no decision procedure; neither guarantees practical efficiency. |
| 計算可再現性 / 研究可重複性 | Ch13 states the adopted National Academies convention. The book does not pretend all disciplines use identical English or Chinese labels. |
| 虛無假設 / p 值 / 檢定力 | Ch12 owns the statistical definitions. A p value is not a posterior probability, and power is conditional on a specified alternative. |
| 可信核心 / 形式化落差 | Ch15 owns the distinction between checking a formal object and ensuring that its statement matches the original problem. |
| 零知識 | Ch16 states the adversary and simulator model. The displayed elementary simulation proves the honest-verifier case only. |
| 正式評分 / 形式驗證 | Ch17 distinguishes an organizer's review of submitted solutions from checking a formal proof object and from auditing an entire model or experiment. |
| 古代書名與版本 | Use the title adopted in its chapter, and retain a romanized/original title where a Chinese title could identify a different work. |

Canonical numerical assumptions and results remain in `running-examples.md`; terminology changes do not authorize changing those examples. A maintenance edit should update the owning chapter and this ledger, then check all dependent chapters and the glossary.
