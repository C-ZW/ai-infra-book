# books/enterprise-agents/CLAUDE.md —《企業級 Agent 工程》維護說明

## 修改前必讀
1. `book-src/_meta/maintenance.md` — 跨章基準數字表（`OrderOps` 50,000 筆/天、$152,250 → ≤ $18,000/月）、脆弱事實清單與掃描協定。
2. `book-src/_meta/style-guide.md` — 繁體中文寫作契約、六段骨架、實戰細節要求與程式碼片段／完整檔分離規範。
3. `book-src/_meta/outline.md` — 12 章範圍邊界、Spine 與 Bridge Registry。

## 修改後必跑（於 repo 根目錄）
```bash
python3 tools/md-reader/gate_book.py books/enterprise-agents/book-src --lang zh-TW --config books/enterprise-agents/book-src/_meta/lint.config.json
python3 tools/md-reader/check_diagrams.py books/enterprise-agents/book-src
python3 tools/md-reader/build_shelf.py
python3 tools/md-reader/build_reader.py books/enterprise-agents/web/book.config.json
```

若修改載重算式或架構機制，須重跑跨模型驗證（寫作者為 Google 家族，務必填 `--writer-family google`）：
```bash
python3 tools/md-reader/verify_book.py books/enterprise-agents/book-src --writer-family google --config books/enterprise-agents/book-src/_meta/lint.config.json --panel-config books/enterprise-agents/book-src/_meta/panel-claude-cli.json --timeout 240 --no-cache
```

## 完整可執行程式碼
見 `examples/README.md`：TypeScript（`examples/ts/ch01/`..`ch12/`）與 Python（`examples/py/ch01/`..`ch12/`）雙語言完整實作。
