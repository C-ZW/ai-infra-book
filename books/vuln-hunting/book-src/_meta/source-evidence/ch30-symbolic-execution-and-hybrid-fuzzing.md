# 外部事實與時效基準（Source Evidence — ch30-symbolic-execution-and-hybrid-fuzzing）

本文件記錄《邊界失守》[第 30 章：符號執行、約束求解與混合式 Fuzzing] 涉及之 2025/2026 時效性標準、工具版本與外部事實參照（依據 `_meta/landscape-2026-11.md`），供寫作與 Tier-2 審核校驗使用。

## 本章特定事實與審查要點

本章符號狀態推導與 Z3 SMT BitVec 求解器、狀態爆炸緩解對照混合 Fuzzing（Hybrid Fuzzing）現代研究架構。

## 關聯標準與事實摘錄（Landscape 2026-11）

- **灰箱 Fuzzing**：**AFL++**（C/C++ 覆蓋率導引與 Persistent Mode 標準）、**cargo-fuzz**（Rust 結合 `libFuzzer` 與 `arbitrary` crate 做結構感知 fuzzing）、**OSS-Fuzz / ClusterFuzzLite**（開源大規模持續 fuzzing 與 PR 閘門）。
  - 來源：Google OSS-Fuzz（https://github.com/google/oss-fuzz）與 AFL++ 專案文件

- **Binary / Systems 實驗基準**：pwn.college（亞利桑那州立大學開源系統安全實戰平台）。
  - 來源：pwn.college（https://pwn.college/）
