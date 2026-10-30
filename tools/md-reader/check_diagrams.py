#!/usr/bin/env python3
"""Find malformed box edges in fenced diagrams using Unicode display widths.

This is a structural check, not a replacement for rendered screenshots.
"""
import argparse
import json
from pathlib import Path
import re
import sys
import unicodedata
from common import markdown_files


def width(text):
    return sum(0 if unicodedata.combining(c) else 2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in text)


def check(root):
    issues = []
    for path in markdown_files(root):
        if "_meta" in path.relative_to(root).parts:
            continue
        lines = path.read_text(encoding="utf-8").splitlines()
        fence = None
        block = []
        for n, line in enumerate(lines, 1):
            marker = re.match(r"^\s*(`{3,}|~{3,})", line)
            if marker:
                if fence and marker[1][0] == fence[0] and len(marker[1]) >= len(fence):
                    # Only complete rectangular box borders are comparable.
                    borders = [(i, width(s)) for i, s in block if re.match(r"^\s*[┌└╔╚].*[┐┘╗╝]\s*$", s)]
                    pending = []
                    for i, w in borders:
                        s = lines[i - 1].lstrip()
                        if s.startswith(("┌", "╔")):
                            pending.append((i, w))
                        elif pending:
                            start, top_width = pending.pop()
                            if w != top_width:
                                issues.append(dict(file=str(path.relative_to(root)), line=i, message=f"Box width {w} differs from top {top_width} at line {start}"))
                            for j, row in block:
                                if start < j < i and re.match(r"^\s*[│║].*[│║]\s*$", row) and width(row) != top_width:
                                    issues.append(dict(file=str(path.relative_to(root)), line=j, message="Box side width differs from border"))
                    fence, block = None, []
                elif not fence:
                    fence = marker[1]
                continue
            if fence:
                block.append((n, line.rstrip()))
        if fence:
            issues.append(dict(file=str(path.relative_to(root)), line=len(lines), message="Unclosed code fence"))
    return dict(passed=not issues, findings=issues)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("book_src", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if not args.book_src.is_dir():
        parser.error("book_src is not a directory")
    report = check(args.book_src)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
