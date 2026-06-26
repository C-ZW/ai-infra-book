# A/B 報告：default vs custom system prompt（同 Opus、同 CLAUDE.md）

**實驗日期**：2026-06-19
**任務**：`/write-book 混沌理論`（完整建書，繁中、純紙上理論、少硬數學、自動核可大綱）
**控制變數**：模型都 `claude-opus-4-8`；都載入同一套 CLAUDE.md（含「焦慮工程師」人格）；prompt 字字相同（只差 slug）。
**唯一自變數**：base system prompt — `chaos-d`＝Claude Code 預設；`chaos-c`＝`prompts/claude-code-system-prompt-20260615-190227.md`（一份完整的 CC system prompt，身份寫死 Fable 5，但 `--model` 已釘 Opus，故僅字面）。
**審查方式**：單人審（額度上限期間無法跑多代理 workflow）＝全書確定性檢查 ＋ ch03 深度對讀。

---

## 0. 最重要的前提：一個結果是「資源假象」，不是 prompt 效應

`chaos-d`（預設）以 `is_error: true` 收場，訊息是 **`You've hit your session limit · resets 10:50pm`**——帳號 **session 用量上限**。兩個各約 $60 的完整 build 同時跑把額度燒光，chaos-d 跑得久、在**附錄／打包階段被砍斷**。

→ **「預設沒建完、客製建完」不可歸因於 system prompt**。它是並行兩個重任務撞到帳號額度的外部假象。下面凡與「完成度」相關的差異（附錄、reader、maintenance、那個沒修的圖），一律屬此類，**不計入 prompt 品質比較**。

---

## 1. Build 指標（chaos-d 為未完成值）

| 指標 | chaos-d 預設 | chaos-c 客製 |
|---|---|---|
| 結果 | ⚠️ 撞額度截斷 | ✅ 完整 |
| 花費 USD | $50.42（未跑完） | $66.85 |
| 牆鐘 | 99.6 分（跑到撞限） | 72.8 分 |
| turns | 79 | 112 |
| 主-session output tokens | 142,029 | 163,781 |
| cache_read | 7.24M | 17.56M |

註：兩者花費/時間**不可直接比**——chaos-d 未完成。唯一可說的是「同時跑兩個完整 build 會超出單一帳號 session 額度」。要乾淨比成本，需錯開時間、各自單獨跑。

## 2. 全書確定性檢查（可公平比的部分）

| 檢查 | chaos-d 預設 | chaos-c 客製 |
|---|---|---|
| 正文章數 | 16（被砍前已全部寫完） | 19 |
| 附錄 / reader / maintenance | 無（額度砍斷） | 3 附錄＋reader＋maintenance |
| 正文字數 | ~221k（16 章） | ~280k（19 章） |
| check_diagrams | 1 FAIL（ch08，未跑到 P3 修） | 0 FAIL（完成 P3） |
| 簡體 lint | 0 ✓ | 0 ✓ |
| 內部註記外洩（待協調者複核） | 0 ✓ | 0 ✓ |
| 生成圖 | 18（PNG，較密） | 11（SVG） |
| 混沌 canon（Feigenbaum/Lyapunov/logistic） | 覆蓋紮實 | 覆蓋紮實 |
| 純紙上指令遵循 | ✓（手算、```text 表、無可執行 lab） | ✓（同左） |

兩本的 check_diagrams 差異（d 有 1 個未對齊圖）**也是資源假象**：那種圖對齊問題本應在 P3 一致性掃描修掉，而 chaos-d 沒跑到 P3。

## 3. ch03「蝴蝶效應」深度對讀（同章正面對決）

兩本都**優秀**，且都嚴守純紙上＋少硬數學＋繁中。差異：

**chaos-c（客製）的相對優勢——史實精準與學術深度：**
- 把 1963 年**兩篇論文分清**：奠基的 JAS〈Deterministic Nonperiodic Flow〉vs 海鷗出處的 NYAS〈The Predictability of Hydrodynamic Flow〉，並明白警告「坊間常把兩篇混為一談」。chaos-d 講了海鷗→蝴蝶，但沒把兩篇切開。
- 多收**進階分辨**：Palmer 2014《Nonlinearity》「真正的蝴蝶效應」（Lorenz 1969 Tellus 的**絕對有限時間屏障**）＋ Roger Pielke Sr.「斷然的不」。chaos-d 停在標準層。
- 工程橋接更具體：event sourcing / bit-identical replay。

**chaos-d（預設）的相對優勢——教學設計：**
- 「直覺的陷阱」表多一欄「怎麼自我察覺」（給徵兆讓你檢查自己懂沒）。
- 迭代表誠實標出每步「×幾」不是剛好 2（放大率隨位置抖動），破除「每步翻倍」的卡通版。

**兩本都做對的**：洛倫茲 1961 迷思的精確版（機器內部六位 0.506127 vs 列印三位 0.506，非「他主動捨入」）；λ=ln2；n≈log₂(1/ε₀) 的對數報酬表；蝴蝶命名 Merilees 1972 代擬＋hedge。

## 4. Meta 基礎建設（受完成度影響）

chaos-c 完成 P5，產出**完整 maintenance.md＋基準數值表**（x*=1−1/r、r₂=1+√6、r∞≈3.56995、δ≈4.6692、period-3 窗口 1+√8≈3.8284、r=4 λ=ln2、Lorenz σ=10/ρ=28/β=8/3 λ≈0.9056/維度≈2.06、Koch 1.2619），並用了較新的 `lint_book.py`（Tier-1 閘）＋`build_figures.py`。chaos-d 被砍斷，無從得知其 meta 是否等價。

## 5. 誠實的結論

- **完成度、check_diagrams、meta 齊備**這幾項表面差異 = **帳號 session 額度的資源假象**，不是 system prompt 效應。
- **可公平比的章節內容**：兩本品質**同級且都很高**；都嚴守指令；客製版在 ch03 的**史實精準＋學術深度**略勝一籌。
- **但這個「略勝」無法用此實驗下定論**：n=1 本、深讀 n=1 章；LLM 兩次 run 本就有隨機變異，兩本大綱結構也不同（不同章節 → 不同著力點）。觀察到的差異落在「run-to-run 噪音」與「prompt 效應」都解釋得通的範圍。
- 要把差異**可信地**歸因於 system prompt，需要：(a) 每種 prompt 跑 **n≥3** 取分佈、(b) 兩邊都**完整跑完**（chaos-d 須在額度 reset 後重跑）、(c) 多章而非單章的系統性評分（多代理 workflow 最適合）。

## 6. 建議的下一步

1. **22:50 額度 reset 後重跑 chaos-d**（單獨跑，不與他人並行），取得完整的對照本。
2. reset 後跑**完整多代理審查 workflow**：逐本×多維度×多章評分＋對抗式複核，產出有統計意義的對照（本報告是單人抽樣的輕量版）。
3. 若要嚴謹，每種 prompt 各跑 3 次，比較**分佈**而非單點。

---

## 7. 更新（2026-06-20）：complete × complete 乾淨對照

額度 reset 後**單獨重跑 chaos-d 至完整**（不並行，避開上次的額度砍斷）。現在兩本都完整，這才是真正可歸因於 system prompt 的對照。

| 指標 | chaos-d 預設（重跑） | chaos-c 客製 |
|---|---|---|
| 結果 | ✅ 完整 is_error=false | ✅ 完整 |
| 花費 USD | **$90.51** | **$66.85** |
| 牆鐘 | 88.3 分 | 72.8 分 |
| turns | 94 | 112 |
| output tokens | 178,519 | 163,781 |
| 正文字數 | **302,065** | **280,296** |
| 章 / 附錄 / 圖 | 19 / 3 / 11 | 19 / 3 / 11 |
| check_diagrams / 簡體 / 註記外洩 | 0 / 0 / 0 | 0 / 0 / 0 |
| 大綱 | 19 章脊椎 | 19 章脊椎（與左幾乎相同） |

**發現（complete × complete）：**
- 兩個 system prompt 都產出**同級、完整、乾淨、結構高度收斂**的書；都嚴守純紙上／少數學／繁中。**沒有大的品質落差。**
- 唯一一致的可測差異：**客製版更精簡也更便宜**（280k 字 / $66.85），**預設版更冗長也更貴**（302k 字 / $90.51）。方向與客製檔（乾淨 CC prompt、強調簡潔結論先行）一致，也呼應自我介紹小測。
- 仍 **n=1**：成本高變異（快取/重試），$90 vs $67 的差大於 output token 差（178k vs 164k），部分來自快取/子代理開銷而非純內容量。「客製較省」是**一致但未顯著**的訊號。
- 註：第 3 節 ch03 深讀是對**舊的（被砍）** chaos-d；重跑版 ch03 檔名為 `ch03-butterfly-sdic.md`，嚴格內容對讀應重做（多代理 workflow 最適合）。

**此實驗總成本（供參考）**：chaos-c $66.85 ＋ chaos-d 首次（截斷）$50.42 ＋ chaos-d 重跑 $90.51 ≈ **$207.78**。
