#!/usr/bin/env python3
"""Run independent CLI panels with bounded execution and fail-closed verdicts."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
from common import HERE, book_config, chapter_files, digest, read_json, write_json


def validate_panel(value):
    if not isinstance(value, dict) or value.get("status") != "complete":
        raise ValueError("Panel did not return status=complete")
    claims = value.get("claims")
    if not isinstance(claims, list) or not claims:
        raise ValueError("Panel returned no substantive claims")
    for claim in claims:
        if not isinstance(claim, dict) or claim.get("verdict") not in {"correct", "incorrect", "imprecise"}:
            raise ValueError("Invalid claim verdict")
        for key in ["claim", "reasoning", "correct_value"]:
            if not isinstance(claim.get(key), str) or not claim[key].strip():
                raise ValueError(f"Missing substantive {key}")
    return dict(status="complete", claims=claims)


def parse_panel(text):
    text = text.strip()
    if text.startswith("```json") and text.endswith("```"):
        text = text[7:-3].strip()
    return validate_panel(json.loads(text))


def providers_from(path):
    providers = read_json(path)["providers"]
    seen = set()
    if len(providers) < 2:
        raise ValueError("At least two distinct provider families must be configured")
    for provider in providers:
        family = provider["family"]
        if family in seen:
            raise ValueError(f"Duplicate provider family: {family}")
        seen.add(family)
        if family not in {"openai", "google", "anthropic"}:
            raise ValueError(f"Unknown provider family: {family}")
        if not isinstance(provider.get("command"), list) or not provider["command"] or not all(isinstance(x, str) for x in provider["command"]):
            raise ValueError("Provider command must be an argument array")
    return providers


def run_panel(provider, prompt, timeout):
    family = provider["family"]
    try:
        with tempfile.TemporaryDirectory(prefix="book-panel-") as name:
            work = Path(name)
            output = work / "result.json"
            command = [arg.replace("{prompt}", prompt).replace("{output}", str(output)) for arg in provider["command"]]
            # No shell interpolation. Kill the process group on timeout, including children.
            proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=work, start_new_session=True)
            try:
                stdout, stderr = proc.communicate(prompt if not any("{prompt}" in arg for arg in provider["command"]) else None, timeout=timeout)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.communicate()
                return dict(family=family, status="error", error=f"Timeout after {timeout}s")
            if proc.returncode:
                # Do not copy provider logs or credentials into persisted reports.
                return dict(family=family, status="error", error=f"CLI exited {proc.returncode}; check provider authentication and command")
            raw = output.read_text(encoding="utf-8") if output.exists() else stdout
            return dict(family=family, **parse_panel(raw))
    except (OSError, ValueError, KeyError) as exc:
        return dict(family=family, status="error", error=f"{type(exc).__name__}: panel launch or JSON validation failed")


def aggregate(panels, writer_family):
    usable = [p for p in panels if p["family"] != writer_family and p["status"] == "complete"]
    # Count families, not responses or claims. An errored provider cannot vote.
    if len({p["family"] for p in usable}) < 2:
        return "INCONCLUSIVE"
    incorrect = {p["family"] for p in usable if any(c["verdict"] == "incorrect" for c in p["claims"])}
    if len(incorrect) >= 2:
        return "FAIL"
    # Writer-family reports are supplementary but their concerns must also be resolved.
    if any(c["verdict"] != "correct" for p in panels if p["status"] == "complete" for c in p["claims"]):
        return "WARN"
    return "PASS"


def verify(root, config, providers, writer_family, prompt_text, timeout, selected=None, no_cache=False):
    root = Path(root).resolve()
    files = chapter_files(root, config)
    if selected:
        wanted = set(selected)
        files = [p for p in files if p.stem in wanted or p.name in wanted or str(p.relative_to(root)) in wanted]
        matched = {key for key in wanted if any(key in {p.stem, p.name, str(p.relative_to(root))} for p in files)}
        if wanted != matched:
            raise ValueError("Unknown selected chapters: " + ", ".join(sorted(wanted - matched)))
    if not files:
        raise ValueError("Zero chapters selected for verification")
    baseline_file = root / "_meta/running-examples.md"
    if not baseline_file.is_file():
        raise ValueError("Missing _meta/running-examples.md baseline")
    baseline = baseline_file.read_text(encoding="utf-8")
    chapters = []
    for path in files:
        text = path.read_text(encoding="utf-8")
        evidence_path = root / "_meta/source-evidence" / (path.stem + ".md")
        evidence = evidence_path.read_text(encoding="utf-8") if evidence_path.is_file() else ""
        prompt = prompt_text + "\n\n<baseline>\n" + baseline + "\n</baseline>\n<source-evidence>\n" + evidence + "\n</source-evidence>\n<chapter>\n" + text + "\n</chapter>"
        def invoke(provider):
            key = digest("panel-v1", provider, config, prompt)
            cache = root / "_meta/verify-cache" / (key + ".json")
            if cache.exists() and not no_cache:
                try:
                    value = read_json(cache)
                    validate_panel(value)
                    if value.get("family") == provider["family"]:
                        return dict(value, cached=True)
                except (OSError, ValueError):
                    pass
            value = run_panel(provider, prompt, timeout)
            if value["status"] == "complete":
                write_json(cache, value)
            return dict(value, cached=False)
        with ThreadPoolExecutor(max_workers=len(providers)) as pool:
            panels = list(pool.map(invoke, providers))
        verdict = aggregate(panels, writer_family)
        chapters.append(dict(file=str(path.relative_to(root)), verdict=verdict, panels=panels, degraded=any(p["status"] == "error" for p in panels)))
    overall = next((v for v in ["FAIL", "INCONCLUSIVE", "WARN"] if any(ch["verdict"] == v for ch in chapters)), "PASS")
    return dict(verdict=overall, writer_family=writer_family, chapter_count=len(chapters), chapters=chapters)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("book_src", nargs="?", type=Path)
    parser.add_argument("--lang", default="zh-TW")
    parser.add_argument("--config", type=Path)
    parser.add_argument("--panel-config", type=Path, default=HERE / "panel.json")
    parser.add_argument("--writer-family", choices=["openai", "google", "anthropic"])
    parser.add_argument("--timeout", type=float, default=240)
    parser.add_argument("--chapters", nargs="+")
    parser.add_argument("--no-cache", action="store_true")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--smoke", action="store_true", help="Make a real trivial round-trip per configured family")
    args = parser.parse_args()
    try:
        if args.timeout <= 0:
            raise ValueError("Timeout must be positive")
        providers = providers_from(args.panel_config)
        if args.smoke:
            prompt = 'Do not use tools. Return ONLY this JSON: {"status":"complete","claims":[{"claim":"2+2=4","verdict":"correct","reasoning":"Adding two and two gives four.","correct_value":"4"}]}'
            with ThreadPoolExecutor(max_workers=len(providers)) as pool:
                panels = list(pool.map(lambda p: run_panel(p, prompt, args.timeout), providers))
            report = dict(verdict="PASS" if all(p["status"] == "complete" for p in panels) else "INCONCLUSIVE", panels=panels)
        else:
            if not args.book_src or not args.writer_family:
                raise ValueError("book_src and explicit --writer-family are required")
            prompt_path = HERE / ("verify_prompt.md" if args.lang == "zh-TW" else f"verify_prompt.{args.lang}.md")
            report = verify(args.book_src, book_config(args.book_src, args.lang, args.config), providers, args.writer_family, prompt_path.read_text(encoding="utf-8"), args.timeout, args.chapters, args.no_cache)
    except (OSError, ValueError, KeyError) as exc:
        report = dict(verdict="INCONCLUSIVE", error=str(exc), chapters=[])
    if args.out:
        write_json(args.out, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    # WARN is deliberately not an exit-code gate. Consumers must parse JSON.
    return 0 if report["verdict"] in {"PASS", "WARN"} else 1


if __name__ == "__main__":
    sys.exit(main())
