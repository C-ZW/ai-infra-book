# CLAUDE.md

專案性質：個人書《乘法的原子：數論與質數的直覺與驚嘆》（繁體中文）＋單檔離線閱讀器。非程式專案，主要產出是 `book-src/` 下的 Markdown。讀者與作者是同一人（profile 中樞見 `../../../profile/`）。本書定位：**欣賞與直覺、純興趣、和工作無關、純紙上推演**（2026-06 建書設定）——讀完要能對另一個工程師講清楚「質數是乘法的不可分原子（每個整數都唯一地由質數相乘搭成）、質數在數線上看似隨機散落卻服從鐵一般的統計律（PNT）——亂與律如何在同一批數裡共存」。脊椎＝**質數作為乘法的原子（同一個分解 60=2²·3·5 被全書反覆看穿）＋「質數長在哪裡」這個謎**。中央張力：**亂與律共存——個別質數位置無公式，整體分布服從 π(x)~x/ln x（PNT）**。屬「推理六書」家族（總綱 `../../../../books/_reasoning-set-design.md`）。

## 修改 book-src/ 內容前，必讀（依序）

1. `book-src/_meta/maintenance.md` — **跨章基準數值表**（脊椎分解 60=2²·3·5、RSA 玩具金鑰 p=3,q=11,n=33,φ=20,e=3,d=7、GCD 示範 gcd(48,18)=6、π(x) 樣本、PNT 漸近、歐拉函數 φ(60)=16、歐拉質數多項式 n²−n+41 等；改任何基準必照表全書同步）、脆弱事實清單、掃描協定與掃描日誌。
2. `book-src/_meta/style-guide.md` — 寫作契約：繁中台灣用語（禁簡體與大陸詞——質數不用「素數」、公因數不用「公約數」、演算法不用「算法」、機率不用「概率」）、章節骨架（從你已知的出發／直覺的陷阱／紙上推演＋推演解答／自我檢核／延伸閱讀）、記號規範（純文字 Unicode、不依賴 LaTeX、多行推導進 ```text）、脊椎兩條落點（脊椎 A：60=2²·3·5；脊椎 B：「質數長在哪裡」）、跨書邊界。
3. `book-src/_meta/outline.md` — 各章範圍邊界（20 章＋3 附錄，5 個 Part）、跨章基準表、史實骨幹，跨章主題用「（見 chNN）」帶過、不展開。

史實與時效性事實以 `book-src/_meta/landscape-2026-06.md` 為基準；查證後有修正：更新 landscape → 依基準表同步引用章 → maintenance.md 掃描日誌記一行。重大修正需兩個獨立來源。數論數學（分解唯一性、費馬小定理、歐拉定理、RSA 加解密、同餘計算）不依賴 landscape 但必須自我複核。

## 修改後，必跑（路徑相對本書根）

- 動到 ASCII 圖：`python3 ../../../tools/md-reader/check_diagrams.py book-src`（CJK=2 欄；exit 0 才算過）。
- 動到任何內容：`python3 ../../../tools/md-reader/lint_book.py book-src`（Tier-1 閘，exit 0）→ `python3 ../../../tools/md-reader/build_reader.py web/book.config.json` 重新打包。書架有變動先 `python3 ../../../tools/md-reader/build_shelf.py`。
- `web/index.html` 與 `../../bookshelf.html`（專案根書架）是產生物，**不要手改**。

（工具路徑相對 book-src/ 內則為 `../../../../tools/md-reader/`，見 maintenance.md 掃描協定。）

## 慣例

- reader config `id` 是 `primes`，**全域唯一**（登記簿 `../../../profile/books.json`）；使用者閱讀偏好 light mode（紙感米白）。
- 全書純紙上推演、零可跑程式；篩法快照／輾轉相除表／同餘表／RSA 手算用 ```text ASCII（無 SVG inline 推導；插圖 SVG 是作者預先算好的，config `inline_images:false`）。
- 簡體詞與大陸用詞：lint 逐字元比對只抓簡體字；**大陸詞（素數、公約數、算法、概率、序貫、灰度、流水線…）lint 抓不到，靠 agy 逐章審＋人工**。
- 數學審查：agy（Gemini 3.5 Flash Medium）逐章重審，**裁決一律 verify-before-apply**——agy 常只看局部會誤判（如把正確的工程師嚴謹版論證誤標為「不夠嚴格」、把欣賞書定位誤認為教科書），每條先自己重算/查證再改（規則見 `../../../../books/_reasoning-set-design.md` §6）。
- 跨書邊界：FTA 唯一分解→前向伏筆《這句話無法被證明》（哥德爾編碼借用這個唯一性）；PNT 的 ln／漸近／Li(x)→《馴服無限》；機率式啟發（Cramér 模型）→《馴服隨機》；驗證≠證明的科學方法→《如何不騙自己》；策略情境非理性偏好→《思考的陷阱》。姊妹書《這句話無法被證明》（godel，同套並建）一律主題式、不寫章號。其他已出版姊妹書可用 `（見《馴服無限》chNN）`，無把握對到正確章號時退成主題式。
- 程式碼（圖檢查、build 工具等）、設定檔、工具註解一律英文；書內容繁體中文。
