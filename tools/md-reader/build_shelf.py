#!/usr/bin/env python3
"""Build a local bookshelf from books.json without consulting reader profiles."""
import argparse
import html
import json
import os
from pathlib import Path
import re
import sys
from urllib.parse import quote
from common import ROOT, atomic_write, manifest, read_json


def build(registry_path, output_override=None):
    registry_path = Path(registry_path).resolve()
    registry = read_json(registry_path)
    output = Path(output_override).resolve() if output_override else (registry_path.parent / registry["shelf_output"]).resolve()
    cards, ids, titles, progress = [], set(), set(), {}
    for book in registry["books"]:
        cfg_path = (registry_path.parent / book["config"]).resolve()
        cfg, chapters = manifest(cfg_path)
        if cfg["id"] != book["id"]:
            raise ValueError(f"Registry/config id mismatch: {cfg_path}")
        if cfg["id"] in ids or cfg["title"] in titles:
            raise ValueError(f"Duplicate registry id or title: {cfg['id']}")
        ids.add(cfg["id"])
        titles.add(cfg["title"])
        target = (cfg_path.parent / cfg.get("output", "index.html")).resolve()
        href = quote(os.path.relpath(target, output.parent), safe="/")
        progress[cfg["id"]] = [c["id"] for c in chapters]
        cards.append(f'<a class="card" href="{href}" data-book-id="{html.escape(cfg["id"])}"><span class="x" title="從書架隱藏">✕</span><div class="ct">{html.escape(cfg["title"])}</div><div class="cs">{html.escape(cfg.get("subtitle", ""))}</div><div class="meta"><div class="cm">{len(chapters)} 份文件</div></div><div class="prog"><span class="pbar"><i></i></span><span class="ptxt"></span></div></a>')
    if not cards:
        raise ValueError("Registry contains zero books")
    template = (Path(__file__).parent / "templates/shelf.html").read_text(encoding="utf-8")
    values = dict(CARDS="\n".join(cards), PROGRESS=json.dumps(progress, ensure_ascii=False).replace("<", "\\u003c"))
    atomic_write(output, re.sub(r"@@([A-Z_]+)@@", lambda m: values[m[1]], template))
    return dict(output=str(output), books=len(cards))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=ROOT / "books.json")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(build(args.registry, args.output), ensure_ascii=False))
        return 0
    except (OSError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
