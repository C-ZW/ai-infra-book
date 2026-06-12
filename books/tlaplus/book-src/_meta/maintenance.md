# Maintenance — 維護手冊（內部文件）

本書事實基準時點 **2026-06**。時效性事實以 `_meta/landscape-2026-06.md` 為錨；改任何跨章基準必須照下表全書同步，並在本檔掃描日誌記一行。重大修正（推翻既有基準）需兩個獨立來源。

## 跨章一致性基準表

改動下列任何數字／命名，必須 grep 全書同步所有引用章：

| 基準 | 值 | 出現章 |
|---|---|---|
| 結算系統 v0 命名 | 動作 `Fetch`/`Settle`、變數 `queue`/`working`/`ledger`、哨兵 `"idle"`、consumer `c1`/`c2` | ch02、ch04–ch09、ch14–ch15 |
| v0 可達狀態 | (2 msgs, 1 consumer)＝8；(2, 2)＝14；(3, 2)＝44；(10, 2)＝34,304 | ch02、ch04、ch09 |
| v0 型別空間上界 | 1 consumer＝48；2 consumers＝144（通式 4^m × (m+1)^c） | ch04、ch09 |
| v1（SettlementV1）定案 | `ledger ∈ [Msgs → Nat]`；Settle 拆 `Credit`＋`Ack`；新增 `Crash(c)`；`dedup ⊆ Msgs` 單調；`NoDoublePay ≜ ∀m: ledger[m] ≤ 1` | ch08、ch09、ch14、ch15 |
| v1 可達狀態（2 msgs, 2 consumers） | 41（三路複核：7×7−8／分組 9+24+8／BFS 七層收斂） | ch09 |
| DieHard | 3 與 5 加侖、目標 4；型別 24、可達 16、最短解 6 步且唯一 | ch08、ch09、ch16 |
| Peterson | process {0,1}；可達 20 狀態、34 條邊；性質 `MutualExclusion` | ch10 |
| TwoPhase（2 RM） | TCommit 可達 12；TwoPhase 可達 56、上界 3,072；擴充版（含 TMCrash）可達 72、卡死 9；6 RM＝50,816 | ch11、ch09、ch14 |
| 2PC 命名 | 1 TM＋2 RM {r1, r2}；rmState ∈ {"working","prepared","committed","aborted"}；性質 `TCConsistent`；擴充動作只有 `TMCrash` | ch11、ch14、ch15 |
| Paxos | 3 acceptors {a1,a2,a3}、2 proposers、ballot 1 與 2；不變量稱 P2c | ch12 |
| Raft | 5 nodes、term 從 1 起；五條 safety 性質沿論文命名 | ch13 |
| 證明 invariant 定案 | IndV1（TypeOK ∧ NoDoublePay ∧ DedupCovers）；IndTP（TPTypeOK ∧ I1–I7） | ch14、ch16 |
| AWS CACM 2015 | 35 步 bug＝**DynamoDB**（不是 S3）；804 行 PlusCal＝S3；「七個團隊」綁 2015 時點 | ch01、ch17（更新時 grep「35 步」） |
| 證明格式 | ⟨1⟩1 層級編號（ch05 建立、ch16 接軌 TLAPS） | ch05 起全書 |

## 脆弱事實清單（最容易過期／出錯的點）

1. **CACM 2025 AWS 續篇**：ACM 全域 403，全書僅以摘要等級引用（ch17 已標轉述）；P language 細節改錨定 P 官方案例頁與 Kani 部落格。下次掃描優先補開原文。
2. **AI×FM 數字**（ch18、landscape §6）：全部掛「截至 2026 年中」；「個位數百分比」措辭刻意模糊，引精確值前必須開出處論文。
3. **強時效連結**：`https://quint.sh`（2026 年才從 quint-lang.org 轉址）、SIGOPS 2026 部落格、Apalache repo（**獨立維護**，不是 Informal Systems——網路舊資料普遍寫錯）。
4. **tla2tools 版本措辭**：穩定版 v1.7.4（勿寫精確日期）；v1.8.0 是 CI 持續重發的長期 pre-release，勿稱「最新版」。
5. **引文內數字不適用千分位慣例**：ch11 有一處 Lamport 原檔註解逐字引文含 `50816`——是引文，不得「順手統一」成 50,816。
6. **附錄 A／B 的「首次出現章」**綁定章節現狀：任何章改動符號或術語的使用後，需對附錄抽查重驗（兩附錄卷首各有收錄慣例聲明）。
7. **TLA+ Community Event**：最近一次 2026-04（Torino, ETAPS）；明年掃描時更新。
8. **Lamport 個人站**：官方資源已移交 TLA+ Foundation；引用時寫「長年任職 Microsoft Research」勿寫「現任」。

## 結構提醒

- 章節骨架五標題（從你已知的出發／陷阱與防禦／紙上推演＋推演解答／自我檢核／延伸閱讀）是一致性掃描的 grep 對象，改標題格式前先想清楚。
- 全書路線圖在 ch01、ch03、ch06、ch10、ch14、ch17（＋ch18 回收版）共 7 張——改章名要同步七處。
- 內文數學符號用 Unicode、spec 引文用 ASCII（code block 標 `tla`）；對照表在 ch06 與附錄 A。
- 簡體詞 lint 注意「效」「系」「准」等兩岸同形字會誤報；用 Python 逐字元比對、不要用 shell grep 的 byte-matching。
- **圖的渲染對齊與來源對齊是兩個故障域**：`check_diagrams.py` 只驗源碼的欄數學（CJK=2 模型）；渲染端由 build_reader 的 `wrapCJK` span 機制保證 CJK=2 欄（勿改回 @font-face size-adjust——WebKit 對 local() 忽略它，Safari 會塌、Chrome 看起來正常）。改動閱讀器或圖之後：headless Chrome 截一張中文多的封閉框圖＋使用者瀏覽器目視各驗一次。

## 掃描協定（「掃描書的時效性」＝執行本節）

1. 重驗 landscape 的 ⚠️ 條目（優先：CACM 2025 原文、MongoDB 論文內文、AI×FM 數字出處）。
2. 開頁抽查附錄 C 的強時效連結（quint.sh、SIGOPS、GitHub repos）。
3. 工具版本掃一輪（tla2tools、TLAPS、Apalache release 頁），依「脆弱事實」第 4 條的措辭規則更新。
4. 有修正 → 更新 landscape ＋依基準表同步引用章 ＋ 本檔日誌記一行；動到 ASCII 圖跑 `check_diagrams.py`；重打包（見書級 CLAUDE.md）。

## 掃描日誌

- **2026-06-11**：成書。P0 校準訪談（紙上推演特例）；landscape 由研究 agent 建立（約 26 次查證；AWS CACM 2015 逐字核對 PDF）。
- **2026-06-12**：P2 完成 18 章＋3 附錄。P4a：agy（Gemini 3.5 Flash High）逐章數學審查 20/20，4 個確認錯誤（ch10 步數、ch13 投票分支、ch17 人週×2）＋ch09 發現的 ch08 最短反例誤稱，全數修畢。P3：v0 命名統一（ch02/ch04/ch05 → Fetch/Settle/working/idle）、千分位統一（引文除外）、ch16 補 lint（代碼評審→程式碼審查）、鉤子反向核對（ch07→ch08、ch12 全部、七張路線圖）通過；全書簡體字 lint 0 命中、骨架 18/18、check_diagrams exit 0。
- **2026-06-12（渲染修復）**：使用者回報部分圖在閱讀器跑版（路線圖右邊框隨行內中文字數成比例左塌）。根因＝WebKit/Safari 忽略 `local()` 字型的 `size-adjust`，PingFang 未放大到 2 欄；fontTools 量測確認 Menlo 涵蓋書中全部符號於 1 欄、來源欄數學無誤。修法＝build_reader 改用 `wrapCJK` span（PingFang 120.41%）取代 size-adjust，三本書重建，使用者於實際瀏覽器確認修復。教訓固化至 tools README、write-book skill、本檔結構提醒。
- **2026-06-12（P4b）**：獨立第二意見（agy Gemini 3.1 Pro High＋網路）：事實抽查 8/8 屬實（AWS 35 步＝DynamoDB、804 行＝S3、TLAPS 後端順序、Apalache 獨立維護、MongoDB MBTC、CockroachDB、Cosmos DB/Lamport 措辭、Rocq 改名）；DieHard 數學重算（16 狀態、6 步唯一最短）正確。結構建議 4 項裁決皆不改書：liveness 深論＝閘門核准的取捨（ch07 M 量尺＋ch14 WF1 已給基本武器）；超時建模已由 ch08 Crash／ch11 RMTimeoutAbort／ch13 選舉超時實例覆蓋；composition 超出書本定位（ch18 有路徑指引）；refinement 伏筆式預告為刻意教學設計。報告存 `../_review/p4b-gemini-review.md`。
