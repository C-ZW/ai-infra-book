#!/usr/bin/env python3
"""Audit generated HTML with a standard HTML parser; do not execute its scripts."""

import argparse
import base64
import hashlib
import json
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote


class ReaderAudit(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids = []
        self.fragments = []
        self.resources = []
        self.errors = []
        self.chapters = []
        self.csp = ""
        self.scripts = []
        self.styles = []
        self.active = None
        self.active_text = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if "id" in attributes:
            self.ids.append(attributes["id"])
        if tag == "article" and "chapter" in attributes.get("class", "").split():
            self.chapters.append(attributes.get("id"))
        if tag == "a" and attributes.get("href", "").startswith("#"):
            self.fragments.append(unquote(attributes["href"][1:]))
        if tag in {"script", "img", "iframe", "audio", "video", "source", "link", "object", "embed"}:
            for key in {"src", "href", "data", "srcset"}:
                if key in attributes:
                    self.resources.append({"tag": tag, "attribute": key, "value": attributes[key]})
        if any(key.lower().startswith("on") for key in attributes):
            self.errors.append(f"Inline event handler on <{tag}>.")
        if tag == "meta" and attributes.get("http-equiv", "").lower() == "content-security-policy":
            self.csp = attributes.get("content", "")
        if tag == "script" and attributes.get("type", "") != "application/json":
            self.active = "script"
            self.active_text = []
        if tag == "style":
            self.active = "style"
            self.active_text = []

    def handle_data(self, data):
        if self.active:
            self.active_text.append(data)

    def handle_endtag(self, tag):
        if tag == self.active:
            target = self.scripts if tag == "script" else self.styles
            target.append("".join(self.active_text))
            self.active = None
            self.active_text = []


def audit(path):
    text = path.read_text(encoding="utf-8")
    parsed = ReaderAudit()
    parsed.feed(text)
    errors = list(parsed.errors)
    duplicates = [identifier for identifier, count in Counter(parsed.ids).items() if count != 1]
    if duplicates:
        errors.append(f"Duplicate DOM ids: {duplicates}")
    missing = sorted(set(parsed.fragments) - set(parsed.ids))
    if missing:
        errors.append(f"Missing fragment targets: {missing}")
    if parsed.resources:
        errors.append(f"Reader has external or separate resources: {parsed.resources}")
    chapter_ids = [identifier for identifier in parsed.chapters if identifier.startswith("ch")]
    if chapter_ids != [f"ch{number:02}" for number in range(1, 19)]:
        errors.append(f"Reader chapter ids are not exactly ch01–ch18: {chapter_ids}")
    if len(parsed.scripts) != 1 or len(parsed.styles) != 1:
        errors.append("Reader must contain exactly one executable script and one stylesheet.")
    for block in parsed.scripts + parsed.styles:
        encoded = base64.b64encode(hashlib.sha256(block.encode()).digest()).decode()
        if f"'sha256-{encoded}'" not in parsed.csp:
            errors.append("Inline script/style SHA-256 is absent from the content security policy.")
    if "default-src 'none'" not in parsed.csp:
        errors.append("Content security policy must forbid resource loads by default.")
    if any("@import" in style or "url(" in style for style in parsed.styles):
        errors.append("Stylesheet contains an import or URL resource.")
    return {"pass": not errors, "documents": len(parsed.chapters), "chapters": len(chapter_ids),
            "unique_ids": len(set(parsed.ids)), "internal_links": len(parsed.fragments),
            "separate_resources": len(parsed.resources), "errors": errors,
            "limitations": ["Static HTML integrity checks do not execute JavaScript or establish visual/accessibility correctness; browser-smoke.mjs covers selected browser interactions separately."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", type=Path, default=Path(__file__).resolve().parents[1] / "web/index.html")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        report = audit(args.path)
    except (OSError, ValueError) as error:
        report = {"pass": False, "errors": [str(error)]}
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(("PASS" if report["pass"] else "FAIL") + ": generated reader integrity.")
        for error in report["errors"]:
            print("ERROR: " + error)
    raise SystemExit(0 if report["pass"] else 1)


if __name__ == "__main__":
    main()
