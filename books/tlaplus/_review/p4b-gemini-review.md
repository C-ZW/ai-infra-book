# 《把系統寫成定理：TLA+ 與形式化方法》獨立第二意見審查報告

## 1. 結構審查
1. **【結構性缺口】Liveness 證明深度的缺失（嚴重度：高）**
   - **理由**：目標讀者是資深後端工程師且要「深入證明層」，分散式系統的 liveness（如 deadlock-free、starvation-free、最終一致性）是工作上的主要痛點。Ch14 僅「淺談」leads-to 證明而未深入（例如未教 well-founded ordering / variant），會讓讀者在面對無限狀態空間的 liveness 證明時缺乏數學武器。
2. **【結構性缺口】時間與超時（Timeouts）建模的缺失（嚴重度：中）**
   - **理由**：分散式系統高度依賴超時機制（例如 Ch13 的 Raft 選舉超時）。書中沒有專門探討如何在不依賴 Real-Time TLA+ 的情況下，用語意非決定性（nondeterminism）來抽象超時事件。這對後端工程師在落地真實場景建模時會形成應用落差。
3. **【結構性缺口】系統模組化與組合（Composition）實務指導不足（嚴重度：中）**
   - **理由**：資深工程師面對的是龐大複雜的系統，儘管 Ch08 介紹了完整 spec，但對於如何利用 `INSTANCE` 做大型系統的模組拆分與組合（Composition）著墨較少（僅在 Ch15 稍微提及）。缺乏模組化設計模式容易讓初學者寫出單體式（monolithic）且難以維護的 spec。
4. **【明顯冗餘/順序問題】Refinement 概念的提早與重複曝險（嚴重度：低）**
   - **理由**：Ch11（2PC）與 Ch12（Paxos）都大量預告並依賴 refinement 概念進行解說，直到 Ch15 才正式介紹 mapping 與 auxiliary variables。雖然這有助建立直覺，但對主打「紙上推演」的架構而言，讀者在 Ch11/12 會面臨缺乏精確工具來驗證層次關係的困境，建議可將 Refinement Mapping 的基礎定義提早至 Ch11 前。

## 2. 事實抽查
1. **AWS DynamoDB 35 步 bug（ch01/ch17）**
   - **宣稱原文**：DynamoDB 複寫與群組成員系統的 spec 找到三個 bug，其中一個的最短錯誤路徑要 35 個高層步驟。
   - **查證結果**：查閱 CACM 2015 論文，該 35 步 bug 確實出自 DynamoDB 團隊。
   - **來源 URL**：https://dl.acm.org/doi/10.1145/2699417 
   - **判定**：屬實
2. **AWS CACM 2015 Table 1 數據（ch01/ch17）**
   - **宣稱原文**：S3 的容錯低階網路演算法使用 804 行 PlusCal 寫成，找到 2 個 bug。
   - **查證結果**：論文 Table 1 與內文明確指出 "Fault-tolerant, low-level network algorithm" 使用 804 行 PlusCal 並找到 "two bugs"。
   - **來源 URL**：https://dl.acm.org/doi/10.1145/2699417
   - **判定**：屬實
3. **TLAPS 後端嘗試順序（ch16）**
   - **宣稱原文**：TLAPS 預設依序嘗試 SMT → Zenon → Isabelle/TLA+。
   - **查證結果**：TLAPS 官方文件確認，預設行為正是先呼叫 SMT，然後 Zenon，最後是 Isabelle `auto` tactic。
   - **來源 URL**：https://proofs.tlapl.us/
   - **判定**：屬實
4. **Apalache 維護方現況（ch16）**
   - **宣稱原文**：Apalache 現由 Igor Konnov 等原核心開發者獨立維護，不受單一組織資助（舊資料稱 Informal Systems 維護已過時）。
   - **查證結果**：Apalache GitHub repo 的 README.md 明確聲明未受組織資助，由核心開發者獨立維護。
   - **來源 URL**：https://github.com/apalache-mc/apalache
   - **判定**：屬實
5. **MongoDB 案例 MBTC 失敗報告（ch17）**
   - **宣稱原文**："eXtreme Modelling in Practice" 論文中對 MongoDB Server 做 MBTC (trace-checking) 花費 20 人週但失敗取消。
   - **查證結果**：PVLDB 2020 該論文證實了 MBTC 專案因實務難度過高而被取消。
   - **來源 URL**：https://dl.acm.org/doi/10.14778/3397230.3397233
   - **判定**：屬實
6. **CockroachDB Parallel Commits 案例（ch17）**
   - **宣稱原文**：CockroachDB Parallel Commits 使用 TLA+ 驗證了 `AckImpliesCommit` 等性質，且是在 Hillel Wayne 的 workshop 產出。
   - **查證結果**：CockroachDB 官方技術部落格記載了該 TLA+ 性質，並致謝 Hillel Wayne 的 workshop。
   - **來源 URL**：https://www.cockroachlabs.com/blog/parallel-commits/
   - **判定**：屬實
7. **Azure Cosmos DB 案例與 Lamport 參與（ch17）**
   - **宣稱原文**：Lamport 曾與 Cosmos DB 團隊合作並受訪，但他不是其一致性協定的設計者。
   - **查證結果**：Cosmos DB 官方 TLA+ repo 連結了 Lamport 的受訪影片，微軟並未宣稱 Lamport 為協定設計者。
   - **來源 URL**：https://github.com/Azure/azure-cosmos-tla
   - **判定**：屬實
8. **Rocq 證明器改名（ch18）**
   - **宣稱原文**：Coq 於 2025 年 3 月隨 9.0 版完成改名為 The Rocq Prover。
   - **查證結果**：The Rocq Prover 官網日誌證實版本 9.0 於 2025 年 3 月 12 日發布，完成更名。
   - **來源 URL**：https://rocq-prover.org/
   - **判定**：屬實

## 3. 數學抽驗
**抽驗案例**：ch08 的 DieHard 範例（3 加侖與 5 加侖壺，目標 4 加侖）

**書中宣稱**：可達狀態總數為 16 個，最短解 6 步且唯一。

**逐步重算過程**：
我們定義狀態為 `(small, big)`，初始狀態為 `(0, 0)`。
利用廣度優先搜尋 (BFS) 逐層推演所有可達狀態：
- **Level 0**: `(0, 0)`
- **Level 1**: `(3, 0)`, `(0, 5)`
- **Level 2**: 
  - 從 `(3, 0)` -> `(3, 5)` [裝滿 big], `(0, 3)` [small 倒給 big]
  - 從 `(0, 5)` -> `(3, 2)` [big 倒給 small]
- **Level 3**:
  - 從 `(0, 3)` -> `(3, 3)` [裝滿 small]
  - 從 `(3, 2)` -> `(0, 2)` [倒空 small]
- **Level 4**:
  - 從 `(3, 3)` -> `(1, 5)` [small 倒給 big]
  - 從 `(0, 2)` -> `(2, 0)` [big 倒給 small]
- **Level 5**:
  - 從 `(1, 5)` -> `(1, 0)` [倒空 big]
  - 從 `(2, 0)` -> `(2, 5)` [裝滿 big]
- **Level 6**:
  - 從 `(1, 0)` -> `(0, 1)` [small 倒給 big]
  - 從 `(2, 5)` -> **`(3, 4)`** [big 倒給 small] **（達成目標！）**
- **Level 7**:
  - 從 `(0, 1)` -> `(3, 1)` [裝滿 small]
- **Level 8**:
  - 從 `(3, 1)` -> **`(0, 4)`** [small 倒給 big] **（達成目標！）**

**總狀態數核對**：
收斂所有走過的不重複節點：`(0,0), (3,0), (0,5), (3,5), (0,3), (3,2), (3,3), (0,2), (1,5), (2,0), (1,0), (2,5), (0,1), (3,4), (3,1), (0,4)`，確實共計 **16 個可達狀態**。

**最短路徑與唯一性分析**：
在 Level 6 時首次達到目標狀態 `(3, 4)`，具體唯一的最短序列如下：
1. `(0, 5)` [裝滿 big]
2. `(3, 2)` [big 倒給 small]
3. `(0, 2)` [倒空 small]
4. `(2, 0)` [big 倒給 small]
5. `(2, 5)` [裝滿 big]
6. `(3, 4)` [big 倒給 small]
（另一條達成目標狀態 `(0, 4)` 的路徑需時 8 步）。

**結論**：經過完整手推重算，書中的宣稱**完全正確**。
