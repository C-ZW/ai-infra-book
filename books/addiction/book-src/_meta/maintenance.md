# maintenance.md — 大腦被劫持（id addct）

維護本書時的權威基準。改任何基準數字，必須照「一致性基準表」全書同步，並在掃描日誌記一行。事實錨點＝`landscape-2026-06.md`（含末尾「補充」addendum）。

## 一致性基準表（各章不得另創寫法／數字／歸屬）

| 基準 | 鎖定值 | 出現章 |
|---|---|---|
| 脊椎兩條曲線 | wanting↑（敏化 sensitization）vs liking↓（allostasis）；dopamine=想要（預測誤差/誘因顯著性）非喜歡（快感） | 全書／ch04 定版 |
| 疾病 vs 學習模型 | 兩造並陳、**本書不裁決**；不可用脊椎替疾病模型背書 | ch10 定版／全書 |
| 習慣化框架 | **Trevor Robbins**：actions → habits → compulsion（2005 *Nat Neurosci*、2016） | ch05 定版 |
| 越戰退伍軍人 | **Lee Robins**（聖路易斯華盛頓大學 / Washington University in St. Louis），經典 1977；在越南約 20% 成癮，返美 8–12 個月降回約 1%，逾 90% 自然戒斷 | ch11/ch12/ch13 |
| **Robins ≠ Robbins** | Lee Robins（越戰）與 Trevor Robbins（習慣化）是**不同人**，鐵律不可混 | 全書 |
| Rat Park | Bruce Alexander，論文 1978–1981；**某些實驗條件下孤立鼠喝多達約 19 倍嗎啡**；複製不穩（Petrie 失敗、2020 僅概念性）；方法有疵（口服嗎啡、樣本小）；不可寫「成癮全是環境」 | ch12 定版 |
| 脆弱性 | 約 **15%** 違法藥物使用者依賴；遺傳率約 **40–60%**（群體變異分配，非個人宿命） | ch11/ch12/ch16 |
| 治療藥 | buprenorphine=**丁基原啡因**（又譯丁丙諾啡；**不是布托啡諾/butorphanol**） | ch14 |
| 經典文獻 | Leshner 1997 = *Science* **Policy Forum**（非社論）；D2 受體下調=Volkow PET；ΔFosB=Nestler | 各章 |
| 物種注意 | dlPFC 是靈長類分區；齧齒類用 PL/IL，勿對老鼠寫 dlPFC | 全書 |

## 已知脆弱事實清單（最易出錯／最該守住）

- **Lee Robins（越戰）≠ Trevor Robbins（習慣化）**——全書最高風險，2026-06-21 查證全書未混淆。
- **Rat Park 嗎啡倍數＝某些條件下約 19 倍**（Wikipedia/Alexander 1981）；landscape 原誤記 7 倍，2026-06-21 已修。複製不穩必 hedge。
- **疾病 vs 學習模型不裁決**；環境是調節因素**之一**、非唯一。
- **buprenorphine=丁基原啡因**（非布托啡諾）；**可卡因→古柯鹼**（台灣用語）。
- dopamine=想要非喜歡（脊椎核心，別寫成「快感分子」）。

## 掃描協定

1. 動基準數字 → 先改 landscape，再全書同步，記日誌。2. ASCII 圖 → `check_diagrams.py book-src`（exit 0）。3. book-src → `lint_book.py book-src`（0 errors）＋重打包。4. 重大修正需 2 獨立來源。

## 掃描日誌

- **2026-06-21 建書（P1–P5）**：起草 ch01–16＋3 附錄（Sonnet 續跑）。P1 agy 修正進 landscape：buprenorphine 中譯（原誤布托啡諾）、Leshner 1997=Policy Forum、加 rodent-PFC≈PL/IL hedge。
- **2026-06-21 P3**：lint 0 errors；diagrams exit 0（重生成 ch08 旋鈕對照表達 CJK=2）；spine 16/16；**Trevor Robbins vs Lee Robins 全書未混淆**（ch05 習慣 vs ch12 越戰乾淨分離）；Rat Park 1978–81、越戰 20%→1%、遺傳率 40–60% 一致。
- **2026-06-21 P4**：agy 逐章審 16/16；套用驗證修正（zh-TW 如「可卡因→古柯鹼」、對齊 landscape、過度宣稱收斂）。**修正 landscape：Rat Park 嗎啡倍數 7 倍 → 約 19 倍**（Wikipedia「Rat Park」＋章節一致，原 landscape 與自身引用來源矛盾）。
- **⚠️ 待網路查證（未改）**：ch06 D2 受體密度「約少 15–20%」精確區間；ch09 near-miss 大鼠 slot-machine 受體（章寫 D2，agy 主張 D4／Cocker 2013）；ch10 Blithikioti 2025（*Lancet Psychiatry*）對「強化疾病模型信念未減汙名」的描述精確度；ch12 Lee Robins 任職已補「聖路易斯華盛頓大學」釐清。
