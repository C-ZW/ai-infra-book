# 人類證明方法的演化

**從計算、論證與實驗，到形式驗證與 AI**

[正文與目錄](book-src/README.md) · [單檔離線閱讀器](web/index.html)

2026-10-07 已把導讀與前三章改寫成問題導向的正文：連對四十次的公式、能保證誤差的近似、找不到與不存在的差別。舊的獨立樣章已退役，不再維持另一個閱讀版本。第四至十八章仍沿用前輪審稿修訂版，沒有宣稱全書已完成相同幅度的重寫。PR 維持 Draft。

正文以文字為主，五張支援圖保留；兩圓作圖移入附錄 A，詳細近似計算和圓田例子移入附錄 C。來源、假設與完整推理仍可沿連結查回。

## 重建與核對

從本書目錄執行；一般建置需要 Node.js 20 以上、Python 3.9 以上，不需網路安裝：

```sh
python3 scripts/build-figures.py
node scripts/build-reader.mjs
node scripts/verify.mjs --json
```

[scripts/check-math.py](scripts/check-math.py) 重算九組共同算例；成功輸出 `PASS: nine canonical mathematical checks.`。完整使用說明見 [scripts/README.md](scripts/README.md)。測試不取代讀者理解或史料查核。

維護資料仍只保留八份；新舊審閱的範圍、實際結果與限制統一在 [審閱摘要](book-src/_meta/verification-report.md)，不提交分批 review、debug JSON 或截圖。
