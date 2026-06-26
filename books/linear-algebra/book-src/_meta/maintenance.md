# 維護手冊（內部文件，非書籍內容）

本書：《矩陣是動詞：線性代數作為空間變換的直覺與驚嘆》（id `linalg`）。22 章＋3 附錄、核心章每章一張程式生成圖。改任何內容前讀本檔＋ `style-guide.md` ＋ `outline.md`；史實以 `landscape-2026-06.md` 為錨。

## 一、跨章基準數值表（改任一格必須照表全書同步）

**脊椎矩陣 S = [[2,1],[1,2]] 七層**（首次出現章／基準值；全書一致）：

| 層 | 章 | 基準值（不得互相矛盾） |
|---|---|---|
| 1 | ch05 | S 兩行＝ê₁、ê₂ 去向：S ê₁=(2,1)ᵀ、S ê₂=(1,2)ᵀ |
| 2 | ch07 | Sx=(3,0)→x=(2,−1)；Sx=(3,3)→x=(1,1) |
| 3 | ch09 | det S = 3（單位正方形→面積 3、不翻面） |
| 4 | ch11 | 特徵值 3、1；特徵向量 (1,1)（λ=3）、(1,−1)（λ=1）；正交 |
| 5 | ch13 | S=P·diag(3,1)·P⁻¹，P=[[1,1],[1,−1]]、P⁻¹=(1/2)[[1,1],[1,−1]] |
| 6 | ch18 | S=QΛQᵀ，Q=(1/√2)[[1,1],[1,−1]]；xᵀSx=2x²+2xy+2y²；橢圓長軸沿 (1,−1)、軸比 1:√3；正定 |
| 7 | ch19 | SVD＝特徵分解：σ=3、1；單位圓→半軸 3、1 橢圓；S²=[[5,4],[4,5]] |

其它：ch08 S⁻¹=(1/3)[[2,−1],[−1,2]]；ch20 S 當共變異→第一主成分 3/(3+1)=**75%**、第二 25%。

**配角矩陣**：剪切 [[1,1],[0,1]]（det=1、defective、奇異值 φ≈1.61803 與 1/φ≈0.61803、積=1）；旋轉 R(θ)=[[cosθ,−sinθ],[sinθ,cosθ]]（det=1、特徵值 e^{±iθ}、R(90°)→±i、R(60°)→1/2±i√3/2）；反射 [[1,0],[0,−1]]（det=−1、特徵值 ±1）；投影 [[1,0],[0,0]]（det=0、秩 1、零空間 y 軸）；奇異 [[1,2],[2,4]]（det=0、第二行=2×第一行）；Fibonacci [[1,1],[1,0]]（特徵值 φ≈1.61803、ψ≈−0.61803、F²=[[2,1],[1,1]]、F³=[[3,2],[2,1]]）。

**其它常數**：√2≈1.41421、√3≈1.73205、√5≈2.23607、φ≈1.61803、PageRank 阻尼 0.85、最小平方基準（點 (1,1)(2,2)(3,2)、ŷ=2/3+(1/2)x、AᵀA=[[3,6],[6,14]]、Aᵀb=(5,11)、殘差和 0）、內積 (2,1)·(1,2)=4、cosθ=0.8、θ≈36.87°、PageRank 玩具圖穩態 π=(0.4,0.2,0.4)。

## 二、脆弱事實清單（⚠️ 易誤傳／來源衝突，引用前回查 landscape）

- **行＝column（直行）、列＝row（橫列）**——台灣慣例、**與中國大陸相反**，全書最高優先級一致性錨點。各 Part 首章＋密集用到行/列的章（ch05/10/11/17）章首釘死。
- **特徵值／特徵向量**（不是「本徵值」）；**單範正交**（亦作標準正交，台灣；不寫簡體「标准正交」）。
- **三個 Jordan**：Gauss–Jordan＝測地學家 Wilhelm Jordan（1842–1899）；Jordan 標準形／SVD 的 Jordan＝數學家 Camille Jordan（1838–1922）；Jordan 代數＝物理學家 Pascual Jordan。ch13/ch19 引用時務必標對。
- **高斯沒發明高斯消去**（《九章算術》早約兩千年）；**Cayley 沒發明行列式**（行列式比 matrix 一詞老約 167 年，關孝和 1683）；**Sylvester 造詞 1850、Cayley 造理論 1858**（兩件事兩人）。
- **|λ₂| ≤ 阻尼 c（≈0.85）**，真實 web 圖緊到等於 c（Haveliwala–Kamvar 2003）——**勿寫成「λ₂ 恰等於 c」的裸述**（landscape §8 已釘正確版＋來源）。
- **來源衝突（用最防禦措辭、勿寫死）**：Leibniz 行列式年代（1683 vs 1693 → 寫「1690 年代初／關孝和之後約十年」）；《九章算術》成書（93 CE vs 題銘 179 CE → 寫「約西元一世紀、不晚於 93 CE」）。
- **David Lay《Linear Algebra and Its Applications》版次未釘死（⚠️）**——延伸閱讀不寫死版次年份，引用前補查 Pearson 官方頁。
- **Hilbert 的「spectrum」命名早於量子力學**（純數學動機，巧合命中光譜）——好軼事，用正確時序。
- **2×2 行列式＝精確有號面積（非近似）**。

## 三、圖片機制（與《圓的影子》同源）

- 核心章 ch01–ch21 每章一張 `book-src/figures/chNN-slug-figname.py`（numpy+matplotlib、Agg、英文標籤、≤45 行、確定性、OUT 由 `__file__` 推導），輸出 `figures/out/*.svg`（**ch20 是 `.png`**，dpi=150 灰階影像壓縮）。ch22 無圖。
- 內嵌：reader config `inline_images:true` 把 `figures/out/` 圖 base64 內嵌，保持單檔離線。**`.png` 與 `.svg` 都會被內嵌**（build_reader 通用影像嵌入）。
- 每章 `### 動手生圖` 內嵌的 Python 區塊**必須與對應 `.py` 逐字一致**（P3 已掃、無 drift）；改腳本要同步改內嵌區塊。
- 變換類圖鐵則：畫底層方格網變形前後、`set_aspect("equal")`、特徵/基向量顯色。圖內文字一律英文（matplotlib 中文是豆腐框）。

## 四、改動後必跑（工具在 repo 外 `../../../tools/md-reader/`，即 `/Users/cheweichen/Desktop/personal/tools/md-reader/`）

```sh
# 動到 ASCII 圖/矩陣 ```text 排版：
python3 ../../../tools/md-reader/check_diagrams.py book-src      # CJK=2 欄，exit 0 才過
# 動到任何 figure 腳本或新增圖：先生圖（缺圖會讓 build_reader warn 中止）
python3 ../../../tools/md-reader/build_figures.py book-src/figures
# 動到任何內容：重新打包（inline_images 內嵌 out/ 圖），書架有變動再 build_shelf
python3 ../../../tools/md-reader/build_shelf.py
python3 ../../../tools/md-reader/build_reader.py web/book.config.json
```

`web/index.html` 與 `../../bookshelf.html`（專案根書架）是產生物，**不要手改**；閱讀器「⌂ 書架」由 build_reader 自動連到最近的上層 bookshelf.html。

## 五、掃描協定

「掃這本書的時效性」＝(1) 重讀本檔脆弱事實清單＋ landscape 的「常被誤傳」表；(2) 抽查史實連結死活（尤其延伸閱讀）；(3) 確認 David Lay 版次是否能釘死；(4) 跑 check_diagrams＋簡體/大陸詞 lint（注意「不准」的「准」是繁中正字、非簡體誤報）＋骨架 grep（ch22 無 `### 動手生圖`）＋脊椎基準數值跨章一致。線代時效性低，重點永遠是**史實歸屬措辭**而非版本/價格。

## 六、掃描日誌

- **2026-06-13｜建書**（Opus 4.8 協調＋22 章/3 附錄 general-purpose fan-out＋landscape 研究 agent）。
  - P3 一致性：check_diagrams 14 圖 0 suspicious；骨架 22 章齊（ch22 免 動手生圖）；簡體/大陸詞 0 真陽性（「不准」的准為繁中正字）；脊椎基準數值跨章一致；內嵌腳本 vs `.py` 無 drift。
  - P3 修正 3 處：ch01 移除多餘 `### 推演題` 子標題；ch17 清掉對照句裡的簡體「标准正交」；landscape §8 把「λ₂ 等於 c」改為「|λ₂|≤c、真實圖緊到等於 c」＋補 Haveliwala–Kamvar 2003 來源（採納 ch21 agent 的查證）。
  - P4 第二意見：**agy**（Gemini 3.5 Flash High）math-only 重算 25 組脊椎/worked-example 數值；**帶網路 general-purpose agent** 抽查 8 條史實（8/8 確認）＋台灣用語（2/2）＋結構（骨架完整、無偽裝證明）＋延伸閱讀連結（6/7 活，infolab 鏡像逾時→ch21 正文與附錄改用 upenn 鏡像）。無必修史實爭議。
