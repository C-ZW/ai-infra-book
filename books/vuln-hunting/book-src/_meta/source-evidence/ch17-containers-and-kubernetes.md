# 外部事實與時效基準（Source Evidence — ch17-containers-and-kubernetes）

本文件記錄《邊界失守》[第 17 章：容器隔離與 Kubernetes 權限提升] 涉及之 2025/2026 時效性標準、工具版本與外部事實參照（依據 `_meta/landscape-2026-11.md`），供寫作與 Tier-2 審核校驗使用。

## 本章特定事實與審查要點

本章容器逃逸與核心隔離參照 Linux Namespaces/cgroups、eBPF 執行期防護（Tetragon/Cilium/Falco）及 io_uring 限制策略。

## 關聯標準與事實摘錄（Landscape 2026-11）

- **Linux `io_uring` 與 `eBPF`**：因共享環形緩衝區生命週期競爭與 UAF 歷史，多租戶環境常透過 `sysctl` 限制非特權 `io_uring`；eBPF 廣泛用於雲端原生安全觀測與執行期阻斷（如 Cilium、Tetragon、Falco），並透過 `CAP_BPF` 與強化 verifier 縮減核心提權面。⚠️ 核心子系統預設政策因發行版與雲端供應商而異。
  - 來源：Linux Kernel 文件、Cilium / Tetragon 專案文件
