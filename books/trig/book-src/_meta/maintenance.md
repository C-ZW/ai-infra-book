# 維護手冊（內部文件，非書籍內容）

本書《圓的影子：三角函數作為旋轉與週期的語言》的維護基準。**改任何基準數字、恆等式、圖、史實前先讀這裡**，改完照協定同步並在掃描日誌記一行。

## 跨章基準表（改任一處必須全書同步）

**全書脊椎「和角公式四種證法」**：`sin(a+b)=sin a·cos b+cos a·sin b`、`cos(a+b)=cos a·cos b−sin a·sin b`，四章各證一次（ch04 幾何／ch05 旋轉矩陣 R(a)R(b)=R(a+b)／ch07 複數極式相乘／ch08 Euler e^{i(a+b)}=e^{ia}e^{ib}），四章末尾都明確對帳「同一件事＝旋轉可組合」。ch15 與附錄 B 再回收。**動到任一證法，四章＋附錄 B 的對帳表一起改。**

| 元素 | 基準值 | 主場章 | 也出現在 |
|---|---|---|---|
| 特殊角表（唯一真相源） | sin30=1/2、cos30=√3/2≈0.86603、sin45=cos45=√2/2≈0.70711、tan30=√3/3≈0.57735、tan60=√3≈1.73205 | ch03 | ch01/04/09/10/12/14、附錄 A/B |
| 小角近似 | sin(0.1)≈0.0998334、cos(0.1)≈0.9950042、tan(0.1)≈0.1003347；sin x≈x、cos x≈1−x²/2（弧度） | ch02 | ch11 |
| 弧度↔度 | 180°=π rad；1 rad≈57.2958°（=180/π）；s=r·θ、扇形 ½r²θ；換算因子 0.1/0.00174533≈57.2958 | ch02 | — |
| 旋轉矩陣 | R(θ)=[[cosθ,−sinθ],[sinθ,cosθ]]（逆時針為正）；R(a)R(b)=R(a+b)；det R=1 | ch05 | ch07 |
| 點積與夾角 | a·b=\|a\|\|b\|cosθ；cosθ=(a·b)/(\|a\|\|b\|)；正交⇔a·b=0⇔cos=0；範例 a=(3,4),b=(4,3)→cosθ=0.96,θ≈16.26° | ch06 | ch13 |
| 複數基準 | i²=−1；乘以 i=逆時針 90°；(1+i)：\|z\|=√2、arg=45°(π/4)；(1+i)²=2i；(1+i)⁸=16 | ch07 | ch08/09 |
| Euler | e^{iθ}=cosθ+i·sinθ；e^{iπ}+1=0；e^{iπ/2}=i；e^{iπ/3}=1/2+(√3/2)i | ch08 | ch15、附錄 A/B |
| 三角極限 | lim sin h/h=1、lim(1−cos h)/h=0、lim(1−cos h)/h²=1/2（弧度） | ch11 | ch02 |
| 導數 | (sin)′=cos、(cos)′=−sin、sin″=−sin（旋轉/速度⊥半徑推） | ch11 | ch08 |
| 單位根 | n 次單位根＝單位圓正 n 邊形；立方根 1、−1/2±(√3/2)i；n≥2 時和為 0；cos3θ=4cos³θ−3cosθ | ch09 | ch13 |
| 相量加法 | A·sin x+B·cos x=√(A²+B²)·sin(x+φ)，φ=atan2(B,A)；範例 3sinx+4cosx=5sin(x+53.13°) | ch12 | ch10/14 |
| Lissajous | 頻率比 1:1、1:2、2:3；有理比⇒封閉曲線 | ch12 | — |
| **方波傅立葉（跨書錨點）** | 方波=(4/π)(sin x+sin3x/3+sin5x/5+…)；**x=π/2 三項和=(4/π)(1−1/3+1/5)=52/(15π)≈1.10347**；Gibbs 過衝≈**8.95% of the jump**（非 17.9% 半跳躍、非舊誤值 1.0383） | ch13 | ch15、附錄 C |
| 雙曲 | cosh²−sinh²=1；cos x=(e^{ix}+e^{−ix})/2、cosh x=(eˣ+e⁻ˣ)/2；懸鏈線=cosh | ch15 | 附錄 A/B |
| 數字精度 | π≈3.14159、e≈2.71828、√2≈1.41421、√3≈1.73205、√6≈2.44949 | — | 全書一致 |

## 脆弱事實清單（最容易被誤傳或改錯的點）

- **方波 1.10347**：與姊妹書《馴服無限》ch11 的跨書錨點。任何章若算出別的值（尤其舊誤值 1.0383），先懷疑算錯。Gibbs 一律寫「整個跳躍的 ≈8.95%」。
- **特殊角表只在 ch03**：是全書唯一真相源，其餘章引用。改 ch03 的值＝全書連動。
- **附錄 B 恆等式 23 條**：每條都標「從哪推來（見 chNN）」。增刪章節恆等式時同步附錄 B，並複查「最小集合（畢氏＋和角＋Euler）下游涵蓋」的宣稱仍成立。
- **landscape 的 ⚠️ 清單**（撰章已 hedge，勿在後續改動中變成硬主張）：sine 詞源「誰把 jiba 誤讀成 jaib」不點名；de Moivre 從未寫成今日緊湊形式（經 Euler 定型）；伽利略懸鏈線「曾以為（或當近似）拋物線」不寫死；atan2 的 Fortran 確切版本未驗證；CORDIC 1956 構想/1959 公開兩年份並列。
- **3Blue1Brown 沒有「Essence of trigonometry」**：全書只能以「不存在、請改看 Lockdown Math + Fourier 影片」出現，不得當真實標題引用。
- **圖內文字一律英文/數學**：matplotlib 對中文是豆腐框。圖的 caption（繁中）寫在 markdown 的 alt 文字裡。
- **ch14 右圖用 rasterized=True + dpi=150**：pcolormesh 直接存 SVG 會爆成 11 MB；rasterize 後 ~84 KB。若改該圖務必保留 rasterized。

## 圖片機制（與其他書不同）

- 每章 ≥1 張程式生成圖，腳本在 `figures/chNN-slug-figname.py`，輸出 `figures/out/*.svg`（或 .png）。
- markdown 用相對路徑 `![繁中 caption](figures/out/...)` 引用；`build_reader.py` 在 `inline_images:true`（見 `web/book.config.json`）下把圖 base64 內嵌，保持單檔離線。
- **缺圖會讓 build_reader 直接報錯中止**（防呆）。改內容後務必先 `build_figures.py` 再 `build_reader.py`。
- 圖腳本＝該章 `### 動手生圖` 的 Python 小實驗，markdown 內嵌版與 .py 必須逐字一致。

## 掃描協定（時效性事實的定期重掃）

1. 以 `landscape-2026-06.md` 為事實基準；重掃時逐條確認 §1–§8 的史實/連結是否仍正確（尤其延伸閱讀連結是否 404）。
2. 數學內容不依賴 landscape，但跨章基準表與脆弱事實清單必須自我複核（手算或 agy 重算）。
3. 重大修正（推翻基準）需兩個獨立來源。修正後：更新 landscape → 依基準表同步引用章 → 本檔掃描日誌記一行。
4. 動到 ASCII 圖：`python3 ../../../tools/md-reader/check_diagrams.py book-src`（exit 0 才算過）。
5. 動到任何內容：`python3 ../../../tools/md-reader/build_figures.py book-src/figures` 再 `python3 ../../../tools/md-reader/build_reader.py web/book.config.json`，書架有變動再 `build_shelf.py`。
6. 簡體詞 lint 用 Python 逐字元（shell grep 對繁簡同形字會誤報；已知誤報：然/弧/旋/存/象/麼/划[划算]）。

## 掃描日誌

- **2026-06-13 建書（Opus 4.8，write-book skill）**：15 章＋3 附錄＋15 程式生成圖一次寫成。
  - P3 一致性：特殊角/√2/√3/π/小角值跨章零矛盾；簡體 lint 乾淨；章節骨架全到；check_diagrams exit 0；15 圖全引用、無孤兒。
  - P4 第二意見：①agy（Gemini 3.5 Flash High）math-only 逐章重算；②Opus 帶網路全書審（結構/史實抽查 12 條/重算 5 個 worked example）。網路審判定 **SHIP**，1.10347、sin75°≈0.96593、(1+i)²=2i、cosh²−sinh²=1 等獨立複核全對；12 條史實全過。
  - 裁決後修正（agy 抓到、複核屬實者）：ch02 換算分母改 0.00174533 使 57.2958 可重現；ch04 sin75 中間值 0.35355→0.35356（使 0.61237+0.35356=0.96593 可重現）＋題3「唯一」退化情況改為「最乾淨」並補孤立解 caveat（a=60°,b=300°）；ch09 cos³20° 0.82961→0.82977（修三倍角數值複核）。agy 對 ch12（1.71779 本就是準值）、ch14（象限表符號）、ch03（120° 其實正確、誤報）的指摘經複核為偽陽性或 agy 自己算錯，不採。
  - 圖修正：ch14 右圖 pcolormesh 加 rasterized=True+dpi=150（11 MB→84 KB）；ch07 補上漏掉的圖片引用；ch14 caption 去除中括號（避免 markdown 圖片語法被吃）。
  - 工具變更：給通用 `build_reader.py` 加 opt-in 的本地圖片 base64 內嵌（config 旗標 `inline_images`，預設不動其他書）；新增 `build_figures.py` runner。已端到端煙霧測試（單檔保持、缺圖硬報錯）。
