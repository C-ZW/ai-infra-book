# maintenance.md — 大腦怎麼編造過去（id mem）

維護本書時的權威基準。改任何基準數字，必須照「一致性基準表」全書同步，並在掃描日誌記一行。事實錨點＝`landscape-2026-06.md`（含末尾「補充」addendum）。

## 一致性基準表（各章不得另創寫法／數字／歸屬）

| 基準 | 鎖定值 | 出現章 |
|---|---|---|
| 脊椎隱喻 | 「每次提取都重新建構」＝「每次 read 觸發一次 write」；現象層穩固、分子層（再鞏固臨床）要 hedge | 全書／ch01 立／ch09 兌現 |
| 重建的防線 | 重建說的是「可被污染、鮮明≠正確」，**不是「記憶全不可信」**；多數日常記憶大致準確 | ch01 立／ch12,ch16 重申 |
| Loftus & Palmer 1974 | 實驗一 n=45（動詞→速度估計，約 41 smashed vs 約 32 contacted）；實驗二 n=150（3×50），碎玻璃誤報 **smashed 32%／hit 14%／控制 12%** | ch05 定版 |
| lost-in-the-mall | Loftus & Pickrell 1995：原始 **n=24、約 25%（6 人）**；2023 預註冊複製 Murphy & Loftus **n=123、約 35%** | ch06 定版 |
| DRM | Roediger & McDermott 1995（建基 Deese 1959）；24 串×15 詞；誤記率依測法而異（自由回憶約 40–55%，再認可達 80%+），不咬死單一值 | ch07 定版 |
| HM | Henry Molaison（1926–2008）；**1953 年、27 歲**由 Scoville 施雙側內側顳葉切除；內嗅皮質近全切、後側海馬迴有殘留（Annese 2014）；程序記憶保留 | ch08 定版 |
| 再鞏固 | Nader, Schafe & LeDoux 2000 *Nature*；大鼠聽覺恐懼＋**anisomycin（茴香黴素，不是 propranolol）**注入杏仁核；propranolol 是後來人體線（Brunet 2008），臨床療效未定論 | ch09 定版 |
| 閃光燈記憶 | Neisser & Harsch 1992 挑戰者號：**106→44 人、約 32 個月（2 年半至近 3 年）**；自信與準確脫鉤 | ch10 定版 |
| HSAM | McGaugh 團隊 2006 首例 AJ＝Jill Price；**LePort 2012 命名 HSAM**；HSAM 仍被植入假記憶＝Patihis et al. **2013 PNAS** | ch14 定版 |
| 術語 | **活化（activation，非「激活」）**；活化—監控架構（activation–monitoring framework） | 全書 |

## 已知脆弱事實清單（最易出錯／最該守住）

- **Neisser–Harsch 間隔＝約 32 個月**（不是「兩年半／2.5 年」當主要數字；2.5 年只能作括號範圍）。2026-06-21 已全書統一。
- **Nader 2000 用 anisomycin**，不是 propranolol（propranolol 是後來的人體線）。
- **HSAM 假記憶＝Patihis 2013**，命名是 **LePort 2012**——兩者別混。
- **HM 內嗅皮質近全切、後側海馬迴殘留**（別寫反）。
- **James McGaugh 仍在世（生於 1931-12-17）**——2026-06-21 查證（Wikipedia）；agy 曾誤稱其 2023 逝世，已駁回。
- 重建≠記憶全不可信（守住防線）。

## 掃描協定

1. 動基準數字 → 先改 landscape，再照上表全書同步，記掃描日誌。
2. 動 ASCII 圖 → `check_diagrams.py book-src`（exit 0）。3. 動 book-src → `lint_book.py book-src`（0 errors）＋重打包。4. 重大修正需 2 獨立來源。

## 掃描日誌

- **2026-06-21 建書（P1–P5）**：起草 ch01–16＋3 附錄。P1 agy 修正進 landscape：HM 內嗅皮質方向、HSAM=Patihis 2013（非 LePort 2012）、Neisser 間隔 32 個月（原誤 2.5 年）。
- **2026-06-21 P3**：lint 0 errors；diagrams exit 0；spine 16/16；mall 24/25%・123/35%、Loftus&Palmer 45/150/32/14/12、HM 1953/27 一致。修 Neisser 間隔跨章漂移（ch01「兩年半」×8、ch10「2.5 年」×4 → 約 32 個月）。
- **2026-06-21 P4**：agy 逐章審 16/16；套用驗證修正（最大宗：激活→活化、激活—監控帳→活化—監控架構）。McGaugh 卒年 agy 誤判（實仍在世 1931–），駁回。
- **⚠️ 待網路查證（未改）**：ch13 Garry 1996 想像膨脹第二次評估時點；ch14 Dresler 2017 控制組基準回憶（章寫約 40 詞、agy 主張約 26 詞）；ch15 Rowland 2014 初次提取成功率方向（landscape 鎖「>75% 效應更強」，agy 提反向「提取努力假說」——單一來源不推翻，待查）；ch06 Garry 招募 46 vs 完成 38；ch16 Dresler ResearchGate 連結真偽。
