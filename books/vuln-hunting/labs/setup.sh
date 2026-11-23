#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

usage() {
  cat <<'EOF'
NexusPay Lab 一鍵環境管理腳本

用法:
  ./setup.sh up         啟動核心 Web/API/DB/Redis 靶機 (Nginx :8080, API :3000, PG :5432, Redis :6379)
  ./setup.sh up-bin     額外建置並啟動 x86_64 原生二進位／逆向／Fuzzing 容器 (Part IV-V)
  ./setup.sh shell-bin  進入 x86_64 原生二進位／Fuzzing 容器互動終端
  ./setup.sh status     查看所有容器與健康狀態
  ./setup.sh reset      清空資料庫與快取卷冊並重新啟動核心環境
  ./setup.sh down       停止並移除所有實驗容器
EOF
}

require_docker() {
  if ! command -v docker >/dev/null 2>&1; then
    echo "[ERROR] 找不到 docker，請先安裝 Docker Desktop。" >&2
    exit 1
  fi
  if ! docker info >/dev/null 2>&1; then
    echo "[ERROR] Docker daemon 未啟動，請先開啟 Docker Desktop。" >&2
    exit 1
  fi
}

cmd="${1:-up}"

case "$cmd" in
  up)
    require_docker
    docker compose up -d --build
    echo ""
    echo "[OK] NexusPay 核心實驗環境已啟動："
    echo "  - Edge Nginx Gateway : http://127.0.0.1:8080"
    echo "  - Node.js API Direct : http://127.0.0.1:3000/health"
    echo "  - PostgreSQL 16      : postgres://nexus:nexuspass@127.0.0.1:5432/nexuspay"
    echo "  - Redis 7            : redis://127.0.0.1:6379"
    ;;
  up-bin)
    require_docker
    docker compose --profile bin up -d --build nexus-bin
    echo "[OK] x86_64 二進位／Fuzzing 容器 (nexus-bin) 已啟動。執行 ./setup.sh shell-bin 進入終端。"
    ;;
  shell-bin)
    require_docker
    docker compose --profile bin exec nexus-bin /bin/bash
    ;;
  status)
    require_docker
    docker compose --profile bin ps
    ;;
  reset)
    require_docker
    docker compose --profile bin down -v
    docker compose up -d --build
    echo "[OK] 環境與資料卷已重置完成。"
    ;;
  down)
    require_docker
    docker compose --profile bin down
    echo "[OK] 所有實驗容器已停止。"
    ;;
  -h|--help|help)
    usage
    ;;
  *)
    echo "[ERROR] 未知指令: $cmd" >&2
    usage
    exit 1
    ;;
esac
