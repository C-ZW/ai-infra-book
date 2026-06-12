# P3 一致性掃描工作清單（協調者維護；完成後歸檔進 maintenance.md 掃描日誌）

## A. agy（P4a 數學審查）確認的錯誤——必修

1. **ch10**：「7 步抵達 ⟨c, c, 1⟩」——agy 重算為 6 次轉移（nn0→sn0→wn0→cn0→cs0→cw1→cc1）。
   修法：改「6 步抵達」；確認「第 6 步是兇案現場」與上下文步數一致。
2. **ch13**：split vote 表格 n5 列 `votedFor: n5 → Nil`——agy 指出 UpdateTerm 不消費訊息，n5 降級後仍可能在下一步投給 n3，應為「n3 或 Nil」。
   修法：先讀上下文——若該節明示「這是一條特定 behavior」則 Nil 合法，但需補一句非決定性說明；若表格宣稱唯一結果則照 agy 修。
3. **ch17**：小節標題「MBTC：十人週買到一個教訓」vs 內文「2 人 × 10 週」——應為 20 人週，標題與內文一致化。
4. **ch17**：ROI worked example「每季 1～3 筆 × 每筆 2～4 小時 ≈ 一年一～兩個人週」——正確為 8~48 小時 ≈ 0.2~1.2 人週。
   ⚠️ 修數字之外**必須重新檢查該節結論是否仍成立**（若年損失下修，spec 投資 2~5 工作天的回收論證要誠實調整，必要時改寫結論或補入非工程成本的說明）。

4b. **ch08**（ch09 agent 發現）：BadCredit 的六步 crash 路徑被寫成「就是 TLC 會印給你的反例 trace」——實際 BFS 最短反例僅 3 步（Fetch–Credit–Credit，Credit 不動 working 可連按）。修法：把該句改為「這條路徑就是一條反例 trace」（ch09 已以正確事實寫成教學點，勿動 ch09）。

## B. 跨章命名統一（v0 結算系統，基準＝ch06 的 spec）

基準命名：動作 `Fetch`／`Settle`、變數 `queue`／`working`／`ledger`、哨兵 `"idle"`、consumer `c1`/`c2`。

5. **ch02**：動作名 `Take(m)` → `Fetch(m)`（`Settle` 已一致）；變數 `holding` → `working`。ledger 用 0/1 而 ch06 用 BOOLEAN——擇一：改成 已入帳/未入帳 措辭或補一句「寫成 TLA+ 時用 TRUE/FALSE（見 ch06）」。
6. **ch04**：動作名 `Take`/`Credit` → `Fetch`/`Settle`（**`Credit` 與 ch08 v1 的 Credit 撞名、語意不同，必改**）；檢查 `working` 命名是否已一致（其回報用 working，應只需改動作名）。
7. **ch05**：`Take`/`Record` → `Fetch`/`Settle`；`hand` → `working`；`⊥` → `"idle"`。⚠️ ch05 的 copies(m) 證明與 IndPay 推導已被 agy 驗證通過——只做**純字面改名**，不得動證明結構；改完人工重讀一次證明步驟確認沒改壞。

## C. 鉤子反向核對（前章開的支票，後章是否兌現）

8. ch12 → ch16：「Consensus.tla 的 TLAPS 證明當 ch16 預習材料」——grep ch16 是否回收。
9. ch07 → ch08：ch07 建議 v1「Settle 類動作配 SF」；ch08 刻意不加 fairness（指回 ch07）。檢查 ch07 的措辭是否寫成「ch08 會加」（若是，改成「v1 需要時的正確形狀」）。
10. ch12 列出的引用清單（ch11/ch13/ch15/ch16 的鉤子）逐一 grep 核對。
11. 全書路線圖（ch01/ch03/ch06/ch10/ch14/ch17）章短名一致性對照。

## D. ch16 特別檢查（agent 死於回報階段，自檢報告遺失）

12. ch16 全套自檢補跑：骨架 grep、check_diagrams、簡體詞 lint、字數、TLAPS 引文是否標 `tla`、與 ch14 的 IndV1/IndTP 對應是否正確引用。agy 審查待跑。

## E. 例行全書掃描

13. 簡體詞 lint（全書）；骨架標題 grep（每章 5 段）；`check_diagrams.py` 全書 exit 0。
14. 跨章基準數字 grep 對帳：8／14／48／144（v0）、56／72／50,816（TwoPhase）、16／24（DieHard）、20／34（Peterson）、ch09 的 v1 數字（待 ch09 完成）。
15. 「（見 chNN）」引用的章號正確性抽查。
16. outline.md 基準表補註 v1 演進（ledger: Nat、Settle 拆 Credit/Ack、新增 Crash、dedup ⊆ Msgs）——協調者改 meta。

## 完成判準

全部勾銷或明寫「不修理由」；修正後重跑 check_diagrams 與簡體詞 lint；agy 對修過的段落不需重審（純字面改名除外——B 項改完抽查一章）。
