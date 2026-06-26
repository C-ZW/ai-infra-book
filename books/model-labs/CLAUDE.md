# CLAUDE.md

專案性質：個人書《藍圖之外：同一套 Transformer，八家大模型為何各擅勝場》（繁體中文）＋單檔離線閱讀器。非程式專案，主要產出是 `book-src/` 下的 Markdown。讀者與作者是同一人（profile 中樞見 `../../../profile/`）。本書定位：**純興趣科普（與工作無關，2026-06-13 訪談定案）**——回答「底層都是 Transformer，為什麼各家強項不同」。**不選「誰最強」**（排行榜會洗牌），教的是**差異的成因結構**。核心主張四條：架構不是護城河／模型是「養」出來的不是「寫」出來的／**五變數**（資料·後訓練對齊·算力基礎設施·研究文化品味·產品取向）解釋一切差異／「最強」測不準、「風格」才穩定。**純敘事＋紙上推演（口頭自答＋思辨題），無可執行 lab。**

## 修改 book-src/ 內容前，必讀（依序）

1. `book-src/_meta/maintenance.md` — **跨章一致性基準表**（五變數記分卡固定名稱與順序、八家招牌強項→主因落點基準、成因拆解表 house style、架構事實基準、DeepSeek 成本敘事紅線）、脆弱事實索引、結構同步雷區、掃描協定與掃描日誌。
2. `book-src/_meta/style-guide.md` — 寫作契約：繁中台灣用語（禁簡體詞、技術詞留英文）、章節骨架（從你已知的出發／成因拆解〔五格歸因＋影子＋何時不成立〕／紙上推演〔### 推演題N／#### 推演解答〕／自我檢核／延伸閱讀）、深度標準。
3. `book-src/_meta/outline.md` — 21 章×4 Part 的範圍邊界與五變數框架定義、跨章基準表，跨章主題用「（見 chNN）」帶過。

時效性事實以 `book-src/_meta/landscape-2026-06.md` 為基準。**本書是全書架時效最敏感的一本**：任何版本號/排名/價格/GPU·TPU 數字/訓練成本三個月內都可能過期。查證後有修正：**先改 landscape**（標日期戳與 ✅/🟡/⚠️）→ 依基準表同步附錄 A、引用章、**ch21 五變數總帳** → maintenance.md 掃描日誌記一行。重大修正（推翻基準，如某家旗艦易主、開閉源策略再反轉）需兩個獨立來源。**一律標日期戳、禁絕對排名（「截至 2026-06／以…著稱」）。**

## 修改後，必跑（從本目錄 `books/model-labs/` 執行）

- 動到 ASCII 圖：`python3 ../../../tools/md-reader/check_diagrams.py book-src`（CJK=2 欄，exit 0 才算過；**傳目錄非單檔**——傳單檔會回報 0 diagrams 假通過）。
- 動到任何內容：`python3 ../../../tools/md-reader/build_reader.py web/book.config.json` 重新打包，再 `python3 ../../../tools/md-reader/build_shelf.py` 更新書架。
- `web/index.html` 與專案根 `bookshelf.html` 是產生物，**不要手改**；閱讀器「⌂ 書架」按鈕由 build_reader 自動連到最近的上層 bookshelf.html。

## 慣例

- reader config `id` 是 `labs`，全域唯一（登記簿 `../../../profile/books.json`）；使用者閱讀偏好 light mode。
- 簡體詞 lint 用 Python 逐字元比對（shell grep 對繁簡同形字會誤報）；**台灣正解誤判清單**：頻寬=bandwidth、張量=tensor、對象=研究/目標對象、項目=清單項目、用戶皆合法；真正要修的是 優化→最佳化、數據中心→資料中心、調用→動用。
- 紙上推演層級慣例：題目 `### 推演題N`、解答 `#### 推演解答`。
- 全書 ASCII 路線圖出現在 **ch01／ch05／ch13／ch20** 四處 Part 首章（基準圖在 outline.md），各標 `◄你在這裡`；改圖須同步 4 處。路線圖刻意採無右邊框流向式設計（避免 Safari 邊框塌陷）。
- **成因拆解表 house style**：`變數 | 角色 | 為什麼`，角色只用 `✓ 主因`／`△ 次因`／`—`；weakness 只放 (b) 影子。**ch11 DeepSeek 例外**多一列「架構」（MLA/MoE，視為算力格延伸），與 ch21 對齊，**勿刪**。
- **ch21 五變數總帳表**＝ch05–12 (a) 表彙整：改任一公司主因，回頭同步 ch21。
- 程式碼／設定檔／註解一律英文；書內容繁體中文。
- 「掃描書的時效性」＝執行 maintenance.md 的掃描協定；最須重掃 landscape Part 3、附錄 A 整表、ch07 Fable 5/Mythos 5（半年內過期）、ch10 Grok 5、各家旗艦版本號。
