#!/usr/bin/env python3
"""稽核 book/ 中 ASCII 圖的對齊一致性。

規則：以「CJK 全形=2 欄、其他=1 欄」計算顯示欄位（與終端機/修正後的閱讀器一致）。
對每個含框線/箭頭字元的 code block，檢查垂直連接字元（│├┤▲▼┼┬┴）在相鄰行之間
的欄位是否能對上（允許落在上一行的框線字元欄位上）。對不上的比例高 → 視為畫歪。

用法：python3 web/check_diagrams.py [--verbose]
"""
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BOOK = ROOT / "book"

DIAG_CHARS = set("│┌┐└┘├┤┬┴┼─►◄▲▼")
VERT = set("│├┤┼┬▲▼")
HORIZ_OK = set("│┌┐└┘├┤┬┴┼─►◄▲▼ ")


def width(ch: str) -> int:
    return 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1


def cols_of(line: str, charset: set) -> set:
    cols, c = set(), 0
    for ch in line:
        if ch in charset:
            cols.add(c)
        c += width(ch)
    return cols


def blocks_of(text: str):
    """yield (start_line_no, block_lines) for fenced code blocks."""
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        if lines[i].lstrip().startswith("```"):
            start = i + 1
            j = start
            while j < len(lines) and not lines[j].lstrip().startswith("```"):
                j += 1
            yield start + 1, lines[start:j]  # 1-based line no of first content line
            i = j + 1
        else:
            i += 1


def audit_block(block):
    """回傳 (垂直字元總數, 對不上的數量, 對不上明細)。"""
    total, miss, detail = 0, 0, []
    anchor_chars = VERT | set("┌┐└┘┬┴┼│├┤")
    for idx in range(len(block)):
        vcols = cols_of(block[idx], VERT)
        if not vcols:
            continue
        prev_anchor = cols_of(block[idx - 1], anchor_chars) if idx > 0 else set()
        next_anchor = cols_of(block[idx + 1], anchor_chars) if idx + 1 < len(block) else set()
        for c in vcols:
            total += 1
            # 一個垂直字元至少要能接上相鄰一行的某個框線欄位（首行/末行豁免）
            if prev_anchor or next_anchor:
                if c not in prev_anchor and c not in next_anchor:
                    miss += 1
                    detail.append((idx, c, block[idx]))
    return total, miss, detail


def main():
    verbose = "--verbose" in sys.argv
    flagged = []
    n_diagrams = 0
    for f in sorted(BOOK.rglob("*.md")):
        text = f.read_text(encoding="utf-8")
        for lineno, block in blocks_of(text):
            content = "".join(block)
            if not (set(content) & DIAG_CHARS):
                continue
            if not any(ch in VERT for ch in content):
                continue  # 純水平線/箭頭，不會跑版
            n_diagrams += 1
            total, miss, detail = audit_block(block)
            if total and miss / total > 0.15:  # >15% 垂直字元接不上 → 可疑
                flagged.append((f.relative_to(ROOT), lineno, total, miss, detail))
    print(f"掃描完成：{n_diagrams} 個含垂直結構的圖，{len(flagged)} 個可疑跑版")
    for path, lineno, total, miss, detail in flagged:
        print(f"\n❌ {path}:{lineno}  垂直字元 {miss}/{total} 接不上")
        if verbose:
            for idx, c, line in detail[:6]:
                print(f"   行+{idx} 欄{c}: {line[:70]}")
    sys.exit(1 if flagged else 0)


if __name__ == "__main__":
    main()
