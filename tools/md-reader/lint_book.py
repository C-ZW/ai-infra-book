#!/usr/bin/env python3
"""Check book contracts. Zero matched chapters always fails."""
import argparse
import json
from pathlib import Path
import re
import sys
import unicodedata
from common import book_config, is_chapter, markdown_files


def is_punct(ch):
    return bool(ch) and unicodedata.category(ch).startswith(("P", "S"))


def lint(root, config):
    root = Path(root).resolve()
    files, errors = [], []
    for path in markdown_files(root):
        if "_meta" in path.relative_to(root).parts:
            continue
        text = path.read_text(encoding="utf-8")
        # Code and URL targets are not prose; link labels remain visible.
        no_fences = re.sub(r"(?ms)^(`{3,}|~{3,}).*?^\1[^\S\n]*$", lambda m: "\n" * m[0].count("\n"), text)
        prose = re.sub(r"`[^`\n]*`|https?://[^\s)]+", "", no_fences)
        chapter = is_chapter(path, root, config)
        entry = dict(file=str(path.relative_to(root)), is_chapter=chapter, depth_units=len(re.findall(config["depth_unit_pattern"], prose)), findings=[])

        def add(rule, message, line=None):
            severity = config.get("severity", {}).get(rule, "error")
            if severity != "off":
                entry["findings"].append(dict(rule=rule, severity=severity, message=message, line=line))

        if chapter:
            if entry["depth_units"] < config["depth_min"]:
                add("depth", f"Depth {entry['depth_units']} < {config['depth_min']}")
            headings = re.findall(r"(?m)^#{2,4}\s+(.+)$", prose)
            positions = []
            for slot in config.get("skeleton_slots", []):
                variants = [slot] if isinstance(slot, str) else slot
                pos = next((i for i, h in enumerate(headings) if any(v in h for v in variants)), None)
                if pos is None:
                    add("skeleton", f"Missing heading: {variants}")
                else:
                    positions.append(pos)
            if positions != sorted(positions):
                add("skeleton_order", "Skeleton headings are out of order")
            if not re.search(config["solution_pattern"], prose):
                add("solution", "Missing worked-solution heading")
            for rule in ["difficulty", "time"]:
                if not re.search(config[rule + "_pattern"], prose):
                    add(rule, "Missing " + rule + " marker")
            if not re.search(r"(?ms)^```[^\n]*\n.*?\d.*?^```", text):
                add("worked_example", "No fenced numerical example; review manually")
        for number, (line, raw_line) in enumerate(zip(prose.splitlines(), no_fences.splitlines()), 1):
            chars = sorted(set(line) & set(config.get("forbidden_chars", "")))
            if chars:
                add("forbidden_chars", "Review simplified characters: " + "".join(chars), number)
            for term, replacement in config.get("vocab_error", {}).items():
                if term in line:
                    add("vocab", f"{term} -> {replacement}", number)
            for rule in config.get("vocab_regex_warn", []):
                if re.search(rule["pattern"], line):
                    add("vocab_regex", f"{rule['term']} -> {rule['replace']}", number)
            for m in re.finditer(r"\*\*([^*\n]+)\*\*", raw_line):
                inner = m.group(1)
                before = raw_line[m.start() - 1] if m.start() > 0 else " "
                after = raw_line[m.end()] if m.end() < len(raw_line) else " "
                if (
                    inner[0].isspace()
                    or inner[-1].isspace()
                    or (is_punct(inner[0]) and not before.isspace() and not is_punct(before))
                    or (is_punct(inner[-1]) and not after.isspace() and not is_punct(after))
                ):
                    add("bold_flanking", f"CommonMark bold will not render: {before.strip()}**{inner}**{after.strip()} -> move outer punctuation outside **", number)
        files.append(entry)
    count = sum(f["is_chapter"] for f in files)
    if count == 0:
        errors.append("Zero chapters matched chapter_globs")
    return dict(chapter_count=count, files=files, errors=errors, passed=not errors and not any(f["severity"] == "error" for e in files for f in e["findings"]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("book_src", type=Path)
    parser.add_argument("--lang", default="zh-TW")
    parser.add_argument("--config", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        report = lint(args.book_src, book_config(args.book_src, args.lang, args.config))
    except (OSError, ValueError, KeyError, re.error) as exc:
        report = dict(passed=False, chapter_count=0, files=[], errors=[str(exc)])
    if args.json:
        print(json.dumps(report, ensure_ascii=False))
    else:
        print(f"Chapters: {report['chapter_count']}; {'PASS' if report['passed'] else 'FAIL'}")
        for error in report["errors"]:
            print("ERROR:", error)
        for entry in report["files"]:
            for finding in entry["findings"]:
                print(f"{entry['file']}:{finding['line'] or '-'}: {finding['severity']}: {finding['message']}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
