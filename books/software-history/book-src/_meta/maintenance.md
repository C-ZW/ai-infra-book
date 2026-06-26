# 維護手冊（內部文件，非書籍內容）

本書：《複雜度守恆：軟體發展史的工程師讀法》。本檔是改任何內容前的第一站。改 `book-src/` 前依序讀：本檔 → `style-guide.md` → `outline.md`；史實以 `landscape-2026-06.md` 為錨。

## 一、跨章一致性基準（改任一處必照表全書同步）

### 核心命名（全書統一用語，不得各章自創）
| 概念 | 全書統一說法 | 定調章 |
|---|---|---|
| 核心主張 | 「複雜度守恆」——抽象不消滅複雜度、只把偶然複雜度往下搬家；本質複雜度搬不掉；每次搬家在新接縫留一道會漏的縫。**守恆是「眼鏡／預設懷疑」，不是物理定律**（ch01、ch19 都已明標此分寸——改其一須同步另一） | ch01 立、ch19 校準 |
| 兩條 strand | 「抽象 strand（用什麼蓋）」＋「方法 strand（怎麼蓋）」 | ch01 |
| 招牌段 | 每章末 `## 複雜度搬去哪了` 結一筆「複雜度帳單」 | 全書 |
| 本質/偶然複雜度 | Brooks《No Silver Bullet》**1986**（非 1975）的手術刀；偶然可被吸收下沉（對上層像消失、是真進步）、本質搬不掉 | ch10 立、ch08/ch19/ch20 回收 |
| 抽象洩漏 | Joel Spolsky《The Law of Leaky Abstractions》**2002** | ch19 |
| 鐘擺 | 四組張力：效能↔生產力、集中↔分散、單體↔微服務、手工↔自動 | ch01 提、全書回收、ch19/ch21 收束 |

### 關鍵年份（一律照 landscape；以下為高頻引用、易記錯者）
- 儲存程式：EDVAC 報告 1945；Manchester Baby 1948、EDSAC 1949。
- FORTRAN 1957；LISP 1958–60；ALGOL 60；COBOL 1959–60。
- Dijkstra GOTO 1968（**標題〈…Considered Harmful〉是編輯 Wirth 改的**；原題〈A Case against the GO TO Statement〉）。
- Parnas 1972；Unix 1969–71；C ~1972；pipe 1973；K&R 1978。
- Simula 67；Smalltalk 1970s；C++ 1983 命名；Java 1995。
- Hoare logic 1969；**Hoare「billion dollar mistake」= QCon London 2009**（非 1980 圖靈獎演說〈The Emperor's Old Clothes〉）。
- Codd 1970；SQL(SEQUEL) 1974；ACID 一詞 1983。
- Brooks《人月神話》1975、《No Silver Bullet》**1986**；**Conway's Law 1968 Datamation 刊出（1967 投 HBR 被退稿）**。
- Royce 1970（**他畫純瀑布圖是當反例、主張迭代「do it twice」**；「waterfall」一詞 Bell & Thayer 1976）。
- Agile Manifesto 2001（Snowbird, 17 人）；XP 的 C3 專案約 **1993 啟動、Kent Beck 1996 進場**（landscape 原「1995-01」已於 2026-06-13 校正）、1997 上線、2000-02 取消。
- GNU 1983、FSF 1985、**GPLv1 1989**（三者不同年）；Linux 1991。
- **WWW 公開 1991-08-06；CERN 釋入公有領域 1993-04-30**（兩個不同里程碑）。
- **Git 2005-04：起於 4/3、4/7 自我託管、數週內接手 kernel**——**勿寫死「三週」**（ch14 已以「數天自我託管、數週接手 kernel」表述）。
- AWS S3/EC2 2006；Docker 2013；Kubernetes 2014；DevOpsDays 2009；Google SRE book 2016；GitHub Copilot 預覽 2021／GA 2022。

## 二、脆弱事實清單（引用前必回查 landscape，禁憑記憶；多為「大家記錯的事」）
1. Royce 瀑布誤讀（ch11 主場）。
2. Lovelace「第一位程式設計師」歷史學爭議（ch02）。
3. Hopper A-0「第一個編譯器」分寸＝以現代定義更像 loader/linker（ch03）。
4. 「Considered Harmful」標題是編輯 Wirth 下的（ch05）。
5. Kay「OOP=訊息傳遞」引文＝單一原始載體 squeak-dev 1998-10-10 email（ch07，已標 ⚠️）。
6. Brooks《No Silver Bullet》是 1986、非 1975（ch10/ch19/ch20）。
7. Conway's Law 1968 刊出（ch10/ch17/ch21）。
8. Knuth「過早最佳化」完整脈絡含「關鍵 3%」、1989 自歸 Hoare（ch05/ch19）。
9. Hoare「billion dollar mistake」= QCon London 2009、非圖靈獎演說（ch08）。
10. Unix「do one thing well」整齊三句版是 Salus 1994 轉述、非 McIlroy 1978 原句（ch06）。
11. Phil Karlton「兩大難事」確切出處無一手記載、只能「一般歸於」（ch01/ch19）。
12. **所有 LOC／市佔／金額／營收統計一律標估計、禁斷言**（COBOL 行數、AI coding 數字尤甚）。

## 三、時效性與最須重掃區
- **landscape §Q（AI 輔助編程 2023–2026）半年內必過期**：ch20 只保留「工具存在性」、零具體數字（市佔／SWE-bench／營收一律禁）。下次掃描重點。
- 平台工程、agentic coding 工具景觀（ch18/ch20）仍在演化，判斷標 `（2026-06）`。

## 四、結構同步提醒（橫向複製處，最易在局部修訂後悄悄過期）
- **ch19 全書總帳表**：17 列（ch02–ch18），逐列對應各章 `## 複雜度搬去哪了` 原文。**改任一章的帳單措辭 → 必回頭同步 ch19 該列**。表內「ch10 是空格（不搬、指出本質搬不動）」是全表的錨，勿填。**全書帳單數＝17（ch02–ch18），ch19 內文三處數字與表列數須一致**（已於 2026-06-13 統一為 17）。
- **ch21 總帳表**：19 列（ch02–ch20）。同上，改任一章帳單須同步。
- **附錄 A 時間軸「章」欄**：人工判讀的主場章，重排章節或搬動論述後須複核。
- **附錄 B 人物/術語「首次出現章」**：序章預告詞標 ch01、概念主場另標；搬動內容後複核。
- **附錄 C 延伸閱讀**：彙整自各章 `## 延伸閱讀`；改章內連結須同步。
- **路線圖**：7 個 Part 首章（ch01/04/07/10/13/16/19）＋ch21 收官各含一張全書 ASCII 路線圖（基準圖在 outline.md）。改基準圖須同步 8 處；CJK=2 欄對齊。

## 五、改動後必跑
- 動 ASCII 圖：`python3 ../../../tools/md-reader/check_diagrams.py book-src`（從 `books/software-history/` 執行；CJK=2 欄，exit 0 才算過；**傳目錄非單檔**，單檔會假通過）。
- 動任何內容：`python3 ../../../tools/md-reader/build_reader.py web/book.config.json` 重新打包；書架有變動先 `python3 ../../../tools/md-reader/build_shelf.py`。
- 簡體詞 lint 用 Python 逐字元比對（shell grep 對繁簡同形字如 息/硬/境/存/挑 會誤報）。
- `web/index.html`、專案根 `bookshelf.html` 是產生物，**不要手改**。

## 六、掃描協定（「掃描時效性」＝執行此節）
1. 逐項對 landscape 的 ⚠️／📌 與本檔「脆弱事實清單」重新查證，優先 §Q 與所有統計數字。
2. 有修正：更新 landscape → 依本檔基準表同步所有引用章 → ch19/ch21 總帳表 → 附錄 A/B/C → 本檔掃描日誌記一行。**重大修正（推翻既有基準）需兩個獨立來源。**
3. 可選：用 agy（`agy --model "Gemini 3.5 Flash (High)" -p "..."`）做結構/論點/教學審查（無網路，不准質疑年份事實）；帶網路的事實 spot-check 由協調者用 WebSearch 做。

## 七、掃描日誌
- **2026-06-13（建書）**：Opus 4.8 從零寫成 21 章＋3 附錄。landscape 由研究 agent 約 60 次查證建立。P3 一致性：診斷圖 37/0、骨架齊、簡體 lint CLEAN、推演解答層級統一為 `### 推演題N`＋`#### 推演解答`。事實校正 5 項：XP/C3 日期（1995-01→約1993啟動/Beck1996）、Git 時間軸（三週→數天/數週）、補 CERN 1993-04-30 公有領域、補 MapReduce 2004、Hoare QCon 確認 London。清掉 6 章誤入的協調者 meta。P4：agy 結構審（82/100）採納——ch01/ch19 守恆論點加誠實但書（守恆＝眼鏡非物理定律）、ch19 帳單數 18→17 校正、WebSocket/TCP 排障改寫為 thundering herd（技術精確）、ch19 加 AI Infra 鐘擺橋接。協調者 WebSearch 8/8 高風險事實確認無誤（Wirth 標題、Royce do-it-twice、No Silver Bullet 1986、Hoare QCon London 2009、Conway 1968、Git 2005-04、CERN 1993-04-30、Agile 2001 17 人）。
