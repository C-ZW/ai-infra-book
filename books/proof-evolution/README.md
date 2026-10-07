# 人類證明方法的演化

**從計算、論證與實驗，到形式驗證與 AI**

目前仍是敘事修訂中的草稿。正文含導讀、18 章與 4 篇附錄；另有開場與前三章的敘事樣章，尚未替換正文與正式閱讀器。檔案完整或測試通過，不代表已適合定稿。

[正文與目錄](book-src/README.md) · [離線閱讀器](web/index.html) · [樣章與章名對照](editorial/README.md)

數學證明是主軸，實驗與統計保有各自的推論條件。正文以連續文字敘述為主，圖片只用來補充具體的空間或程序關係。當代案例的原稿查核基準日為 2026-10-06，不是完整的最新系統排名。

## 核對與重建

從本書目錄執行；Node.js 20 以上、Python 3.9 以上，一般建置不需安裝 npm 套件：

```sh
python3 scripts/build-figures.py
python3 scripts/check-math.py
node scripts/build-reader.mjs
node scripts/verify.mjs --json
```

第二個指令重算附錄 C 相關的七組基準算例；成功時輸出 `PASS: seven canonical mathematical checks.`。程式是 [scripts/check-math.py](scripts/check-math.py)，完整使用說明與限制見 [工具說明](scripts/README.md)。它不是全書數學或史實正確性的證明。

本輪已針對審稿修訂正文與樣章，加入五張必要的支援圖；樣章仍是獨立替代稿，不代表全書敘事已重寫。歷史查核、零上下文審閱、逐項處置與實際測試範圍，統一記在 [審閱摘要](book-src/_meta/verification-report.md)。後續更新依 [維護規則](book-src/_meta/maintenance.md)。必要的建置工具與測試保留；一次性輸出不納入版本控制。
