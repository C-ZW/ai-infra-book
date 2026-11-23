# 外部事實與時效基準（Source Evidence — ch25-rust-unsafe-and-ffi）

本文件記錄《邊界失守》[第 25 章：Rust、unsafe 與 C FFI 邊界漏洞] 涉及之 2025/2026 時效性標準、工具版本與外部事實參照（依據 `_meta/landscape-2026-11.md`），供寫作與 Tier-2 審核校驗使用。

## 本章特定事實與審查要點

本章 Rust Soundness 契約、未定義行為（UB）與 C FFI 邊界參照 glibc Safe-Linking 及現代 V8 記憶體安全邊界。

## 關聯標準與事實摘錄（Landscape 2026-11）

- **V8 Sandbox（Ubercage）**：在現代 Chromium 與 V8 執行時期已成生產級隔離邊界。保留 1 TB 連續虛擬位址空間，沙箱內指標壓縮為相對於基底的 32 位元偏移，並將程式碼指標移出 JS 物件改以間接表索引，迫使攻擊者必須額外尋找沙箱逃逸原語。⚠️ 實作細節隨 V8 版本持續收緊。
  - 來源：V8 官方部落格（https://v8.dev/blog/sandbox）

- **glibc `ptmalloc2`**：現代發行版預設啟用 Safe-Linking（tcache / fastbin 單向鏈結指標以 `pos >> 12` XOR 混淆）、Pointer Mangling、嚴格 alignment 與 double-free 檢查，傳統未洩漏堆積位址的單純覆寫已失效。
  - 來源：glibc 原始碼與安全公告

- **Binary / Systems 實驗基準**：pwn.college（亞利桑那州立大學開源系統安全實戰平台）。
  - 來源：pwn.college（https://pwn.college/）
