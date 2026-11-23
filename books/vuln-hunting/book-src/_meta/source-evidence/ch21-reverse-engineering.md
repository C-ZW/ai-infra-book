# 外部事實與時效基準（Source Evidence — ch21-reverse-engineering）

本文件記錄《邊界失守》[第 21 章：無原始碼逆向工程實戰] 涉及之 2025/2026 時效性標準、工具版本與外部事實參照（依據 `_meta/landscape-2026-11.md`），供寫作與 Tier-2 審核校驗使用。

## 本章特定事實與審查要點

本章 Stripped Binary 逆向分析、Ghidra 反編譯引擎與 P-code SSA 還原對齊開源逆向工程實務與 pwn.college 實驗。

## 關聯標準與事實摘錄（Landscape 2026-11）

- **glibc `ptmalloc2`**：現代發行版預設啟用 Safe-Linking（tcache / fastbin 單向鏈結指標以 `pos >> 12` XOR 混淆）、Pointer Mangling、嚴格 alignment 與 double-free 檢查，傳統未洩漏堆積位址的單純覆寫已失效。
  - 來源：glibc 原始碼與安全公告

- **Binary / Systems 實驗基準**：pwn.college（亞利桑那州立大學開源系統安全實戰平台）。
  - 來源：pwn.college（https://pwn.college/）
