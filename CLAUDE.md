# CLAUDE.md

專案性質：個人 AI Infrastructure 轉職書（繁體中文）＋單檔離線閱讀器。非程式專案，主要產出是 `book/` 下的 Markdown。讀者與作者是同一人（背景見 `Chewei_Chen_Resume.md`）；`plan.md` 是配套的練功路線，書與它互相對應但各自獨立。

## 修改 book/ 內容前，必讀（依序）

1. `book/_meta/maintenance.md` — **跨章一致性基準表**（改任何基準數字必須照表全書同步，如 Llama-3.3-70B 320 KiB/token）、已知脆弱事實清單、掃描協定與掃描日誌。
2. `book/_meta/style-guide.md` — 寫作契約：繁體中文台灣用語（禁簡體詞）、章節骨架（從你已知的出發／故障模式與防禦／動手做／自我檢核／延伸閱讀）、深度標準。
3. `book/_meta/outline.md` — 各章範圍邊界，跨章主題用「（見 chNN）」帶過、不展開。

時效性事實（版本、價格、硬體狀態）以 `book/_meta/landscape-2026.md` 為基準；查證後有修正時：更新 landscape、依一致性基準表同步所有引用章節、在 maintenance.md 掃描日誌記一行。重大修正（推翻既有基準）需兩個獨立來源。

## 修改後，必跑

- 動到 ASCII 圖：`python3 web/check_diagrams.py`（驗證 CJK=2 欄的對齊規則，exit 0 才算過）
- 動到任何 book/ 內容：`python3 web/build_reader.py`（重新打包閱讀器）
- `web/index.html` 是產生物，**不要手改**

## 慣例

- 使用者閱讀偏好：light mode（閱讀器預設紙感米白）。
- 閱讀器字型對齊假設 Apple 平台（Menlo + PingFang size-adjust 120.4%），細節與限制見 maintenance.md。
- 「掃描書的時效性」＝執行 maintenance.md 的掃描協定。
