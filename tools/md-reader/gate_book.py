#!/usr/bin/env python3
"""Tier-1 book gate; optional Tier-2 must return an actual PASS."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from common import HERE, book_config
from lint_book import lint
from check_diagrams import check


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("book_src", type=Path)
    parser.add_argument("--lang", default="zh-TW")
    parser.add_argument("--config", type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--writer-family", choices=["openai", "google", "anthropic"])
    parser.add_argument("--timeout", type=float, default=240)
    parser.add_argument("--panel-config", type=Path)
    args = parser.parse_args()
    try:
        lint_report = lint(args.book_src, book_config(args.book_src, args.lang, args.config))
        diagrams = check(args.book_src)
        report = dict(passed=lint_report["passed"] and diagrams["passed"], lint=lint_report, diagrams=diagrams)
        if args.verify and report["passed"]:
            if not args.writer_family:
                raise ValueError("--verify requires explicit --writer-family")
            command = [sys.executable, str(HERE / "verify_book.py"), str(args.book_src), "--lang", args.lang, "--writer-family", args.writer_family, "--timeout", str(args.timeout), "--json"]
            for flag, value in [("--config", args.config), ("--panel-config", args.panel_config)]:
                if value:
                    command += [flag, str(value)]
            result = subprocess.run(command, capture_output=True, text=True)
            report["verification"] = json.loads(result.stdout)
            report["passed"] = result.returncode == 0 and report["verification"].get("verdict") == "PASS"
    except (OSError, ValueError, KeyError) as exc:
        report = dict(passed=False, error=str(exc))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
