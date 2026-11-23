# books/vuln-hunting/CLAUDE.md —《邊界失守》維護說明

## 修改前必讀
1. `book-src/_meta/maintenance.md` — 跨章基準數字表、脆弱事實與掃描協定。
2. `book-src/_meta/style-guide.md` — 繁體中文寫作契約、六段骨架與 `### 攻擊者目標與實質影響` 規範。
3. `book-src/_meta/outline.md` — 37 章大綱（含 7 章標記 `unfinished` 之規格）。

## 修改後必跑（於 repo 根目錄）
```bash
python3 tools/md-reader/gate_book.py books/vuln-hunting/book-src --lang zh-TW --config books/vuln-hunting/book-src/_meta/lint.config.json
python3 tools/md-reader/check_diagrams.py books/vuln-hunting/book-src
python3 tools/md-reader/build_shelf.py
python3 tools/md-reader/build_reader.py books/vuln-hunting/web/book.config.json
```

## 本地實驗環境
見 `labs/README.md`，於 `books/vuln-hunting/labs/` 執行 `./setup.sh up`（核心環境）或 `./setup.sh up-bin`（`linux/amd64` 二進位／Fuzzing 容器）。
