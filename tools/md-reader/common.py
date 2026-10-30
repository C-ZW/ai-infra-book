"""Shared, dependency-free book tool primitives."""
import fnmatch
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def atomic_write(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=path.parent, prefix=path.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(text)
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def write_json(path, value):
    atomic_write(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def merge(base, extra):
    result = dict(base)
    for key, value in extra.items():
        result[key] = merge(result[key], value) if isinstance(value, dict) and isinstance(result.get(key), dict) else value
    return result


def load_config(lang="zh-TW", config=None):
    result = read_json(HERE / "lang" / (lang + ".json"))
    result = merge(result, read_json(config)) if config else result
    if not isinstance(result.get("depth_min"), int) or result["depth_min"] <= 0:
        raise ValueError("depth_min must be a positive integer")
    if not isinstance(result.get("chapter_globs"), list) or not result["chapter_globs"]:
        raise ValueError("chapter_globs must be a non-empty list")
    if any(s not in {"error", "warn", "off"} for s in result.get("severity", {}).values()):
        raise ValueError("Severity must be error, warn, or off")
    for key in ["depth_unit_pattern", "solution_pattern", "difficulty_pattern", "time_pattern"]:
        re.compile(result[key])
    return result


def book_config(root, lang="zh-TW", config=None):
    inferred = Path(root) / "_meta/lint.config.json"
    return load_config(lang, config or (inferred if inferred.is_file() else None))


def matches(path, patterns):
    return any(fnmatch.fnmatch(path.as_posix(), p) or fnmatch.fnmatch(path.name, p) for p in patterns)


def markdown_files(root):
    return sorted(p for p in Path(root).rglob("*.md") if not any(part.startswith(".") for part in p.relative_to(root).parts))


def is_chapter(path, root, config):
    rel = path.relative_to(root)
    return "_meta" not in rel.parts and matches(rel, config["chapter_globs"]) and not matches(rel, config["appendix_globs"])


def chapter_files(root, config):
    return [p for p in markdown_files(root) if is_chapter(p, root, config)]


def digest(*values):
    return hashlib.sha256(json.dumps(values, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def manifest(config_path):
    config_path = Path(config_path).resolve()
    cfg = read_json(config_path)
    chapters, seen, paths = [], set(), set()
    for group in cfg.get("groups", []):
        files = [config_path.parent / p for p in group.get("files", [])]
        if "dir" in group:
            matches_in_dir = sorted((config_path.parent / group["dir"]).glob(group.get("pattern", "*.md")))
            if not matches_in_dir:
                raise ValueError(f"Manifest group matched zero files: {group['dir']}")
            files += matches_in_dir
        for path in files:
            path = path.resolve()
            if not path.is_file():
                raise ValueError(f"Missing manifest file: {path}")
            if path in paths:
                raise ValueError(f"Repeated manifest file: {path}")
            paths.add(path)
            chapter_id = path.stem
            if chapter_id in seen:
                raise ValueError(f"Duplicate chapter id: {chapter_id}")
            if not re.fullmatch(r"[A-Za-z0-9_-]+", chapter_id):
                raise ValueError(f"Unsafe chapter id: {chapter_id}")
            seen.add(chapter_id)
            text = path.read_text(encoding="utf-8")
            title = re.search(r"^#\s+(.+)$", text, re.M)
            chapters.append(dict(id=chapter_id, file=path.name, group=group["title"], title=title.group(1) if title else chapter_id, md=text, path=str(path)))
    if not chapters:
        raise ValueError("Manifest contains zero chapters")
    return cfg, chapters
