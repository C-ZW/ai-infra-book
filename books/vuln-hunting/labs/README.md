# NexusPay 本地實驗環境（一鍵啟動）

所有實驗容器只綁定 `127.0.0.1`，不對外網暴露，零雲端費用。

## 一鍵指令

```bash
cd books/vuln-hunting/labs

# 1. 啟動核心 Web / API / PostgreSQL 16 / Redis 7 環境（Part I–III）
./setup.sh up

# 2. 查看服務狀態
./setup.sh status

# 3. 啟動 x86_64 原生二進位／逆向／Fuzzing 容器（Part IV–V，Apple Silicon 透過 Docker linux/amd64 執行）
./setup.sh up-bin
./setup.sh shell-bin

# 4. 清空資料庫與快取並重置為初始基準（每戶 10,000 分）
./setup.sh reset

# 5. 停止並清理容器
./setup.sh down
```

## 基準參數（對齊 `_meta/running-examples.md`）

- Nginx Edge Gateway：`http://127.0.0.1:8080`（`proxy_read_timeout = 30s`）
- Node.js API Direct：`http://127.0.0.1:3000`（`keepAliveTimeout = 5s`）
- PostgreSQL 16：`127.0.0.1:5432`（`tenant-alpha` / `tenant-beta`，初始餘額 `10,000` 分）
- Redis 7：`127.0.0.1:6379`
- `nexus-bin`（`linux/amd64`）：預裝 `gcc`、`clang`、`llvm`、`gdb`、`afl++`、`rust/cargo`、`strace`、`ltrace`、`patchelf`，工作目錄掛載至 `./workspace`。
