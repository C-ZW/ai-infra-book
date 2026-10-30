#!/usr/bin/env python3
"""Build a self-contained reader from an ordered JSON chapter manifest."""
import argparse
import base64
import html
import json
import mimetypes
import os
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit
from common import HERE, ROOT, atomic_write, manifest, read_json


def script_json(value):
    # HTML parsers recognize </script> even inside a JSON string.
    return json.dumps(value, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")


def embed_images(text, source):
    def replace(match):
        alt, target = match.groups()
        target = target.strip().strip("<>")
        if target.startswith("data:image/"):
            return match[0]
        if urlsplit(target).scheme or target.startswith("//"):
            raise ValueError(f"Offline reader requires local image: {target}")
        path = source.parent / unquote(target)
        mime = mimetypes.guess_type(path.name)[0]
        if not mime or not mime.startswith("image/"):
            raise ValueError(f"Unsupported image type: {target}")
        data = base64.b64encode(path.read_bytes()).decode("ascii")
        return f"![{alt}](data:{mime};base64,{data})"
    return re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", replace, text)


def validate_registry(config_path, cfg, registry_path):
    registry = read_json(registry_path)
    entries = registry["books"]
    ids = [book["id"] for book in entries]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate book IDs in registry")
    conflicts = [book for book in entries if book["id"] == cfg["id"] and (registry_path.parent / book["config"]).resolve() != config_path]
    if conflicts:
        raise ValueError(f"Book id {cfg['id']} belongs to another config")
    return registry


def build(config_path, registry_path=ROOT / "books.json", output_override=None):
    config_path = Path(config_path).resolve()
    cfg, chapters = manifest(config_path)
    if not re.fullmatch(r"[A-Za-z0-9_-]+", cfg["id"]):
        raise ValueError("Book id must be a non-empty safe namespace")
    if cfg.get("ui_lang", "zh-TW") != "zh-TW":
        raise ValueError("Only the zh-TW reader UI is bundled")
    if cfg.get("math"):
        raise ValueError("KaTeX assets are not bundled; vendor them before using math=true")
    registry_path = Path(registry_path).resolve()
    registry = validate_registry(config_path, cfg, registry_path)
    output = Path(output_override).resolve() if output_override else (config_path.parent / cfg.get("output", "index.html")).resolve()
    shelf = (registry_path.parent / registry["shelf_output"]).resolve()
    if not shelf.is_file():
        raise ValueError("Build the shelf before building readers")
    for chapter in chapters:
        source = Path(chapter.pop("path"))
        if cfg.get("inline_images"):
            chapter["md"] = embed_images(chapter["md"], source)
        elif re.search(r"!\[", chapter["md"]):
            raise ValueError("Book has images; set inline_images=true for offline delivery")
    brand = '<div class="brand">' + html.escape(cfg["title"]) + '<br><span style="font-weight:400;font-size:12px;color:var(--muted)">' + html.escape(cfg.get("subtitle", "")) + '</span></div>'
    values = dict(BOOK_DATA=script_json(dict(chapters=chapters)), TITLE_HTML=html.escape(cfg["title"]), ID_JSON=script_json(cfg["id"]), TITLE_JSON=script_json(cfg["title"]), BRAND_JSON=script_json(brand), SHELF_HREF=html.escape(os.path.relpath(shelf, output.parent)), FOOTER_HTML=html.escape(cfg.get("footer", "")))
    template = (HERE / "templates/reader.html").read_text(encoding="utf-8")
    result = re.sub(r"@@([A-Z_]+)@@", lambda m: values[m[1]], template)
    atomic_write(output, result)
    return dict(output=str(output), chapters=len(chapters), bytes=len(result.encode()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path)
    parser.add_argument("--registry", type=Path, default=ROOT / "books.json")
    parser.add_argument("--output", type=Path, help="Optional preview output; does not alter config")
    args = parser.parse_args()
    try:
        print(json.dumps(build(args.config, args.registry, args.output), ensure_ascii=False))
        return 0
    except (OSError, ValueError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
