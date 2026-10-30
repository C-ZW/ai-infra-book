"""Regression tests for publication gates, panel failures, and offline builders."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import HERE, book_config, load_config, merge, write_json
from lint_book import lint
from check_diagrams import check
from verify_book import aggregate, parse_panel, providers_from, run_panel, verify
from build_reader import build as build_reader, embed_images
from build_shelf import build as build_shelf


def panel(family, verdict="correct"):
    return dict(family=family, status="complete", claims=[dict(claim="Two plus two equals four", verdict=verdict, reasoning="Direct addition gives four", correct_value="4")])


class ToolchainTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        fragment = json.loads((HERE.parent.parent / ".agents/skills/write-book/references/forms/narrative.lint.json").read_text())
        self.cfg = merge(load_config(), fragment)
        self.cfg["depth_min"] = 20

    def tearDown(self):
        self.temp.cleanup()

    def chapter(self, text=None):
        path = self.root / "ch01-test.md"
        path.write_text(text or "# 測試\n\n" + "形成問題之前，人們習慣接受眼前的解釋。" * 5)
        return path

    def test_zero_chapters_fails(self):
        self.assertFalse(lint(self.root, self.cfg)["passed"])
        (self.root / "topic.md").write_text("# Topic\n" + "內容" * 200)
        self.assertEqual(lint(self.root, self.cfg)["chapter_count"], 0)

    def test_narrative_depth_and_code_exclusion(self):
        self.chapter()
        self.assertTrue(lint(self.root, self.cfg)["passed"])
        self.chapter("# 測試\n```\n" + "內容" * 100 + "\n```\n")
        self.assertFalse(lint(self.root, self.cfg)["passed"])

    def test_instructional_contract(self):
        self.chapter()
        cfg = load_config()
        cfg["depth_min"] = 20
        self.assertFalse(lint(self.root, cfg)["passed"])
        text = "# 測試\n" + "內容" * 30 + "\n"
        text += "\n".join("## " + slot[0] for slot in cfg["skeleton_slots"])
        text += "\n### 參考解答\n難度：入門，10 分鐘\n```\n2 + 2 = 4\n```\n"
        self.chapter(text)
        self.assertTrue(lint(self.root, cfg)["passed"])

    def test_local_config_is_automatically_loaded(self):
        write_json(self.root / "_meta/lint.config.json", self.cfg)
        self.assertEqual(book_config(self.root)["severity"]["skeleton"], "off")

    def test_invalid_config_fails(self):
        path = self.root / "bad.json"
        write_json(path, {"severity": {"depth": "pass"}})
        with self.assertRaises(ValueError):
            load_config(config=path)

    def test_metadata_is_not_a_chapter(self):
        path = self.root / "_meta/ch-not-a-chapter.md"
        path.parent.mkdir()
        path.write_text("test")
        self.assertEqual(lint(self.root, self.cfg)["chapter_count"], 0)

    def test_simplified_and_vocabulary_errors(self):
        self.chapter("# 測試\n" + "內容" * 30 + "\n这是軟件\n")
        self.assertFalse(lint(self.root, self.cfg)["passed"])
        self.chapter("# 測試\n" + "我們的內容" * 30 + "\n法布里修斯走了三公里，于先生與皇后。")
        self.assertTrue(lint(self.root, self.cfg)["passed"])

    def test_bold_flanking_errors(self):
        self.chapter("# 測試\n" + "內容" * 30 + "\n這是**「無法渲染的粗體」**與**大腦旋轉（mental rotation）**之中。\n")
        report = lint(self.root, self.cfg)
        self.assertFalse(report["passed"])
        rules = [f["rule"] for f in report["files"][0]["findings"]]
        self.assertIn("bold_flanking", rules)
        self.chapter("# 測試\n" + "內容" * 30 + "\n這是「**可以渲染的粗體**」與**大腦旋轉**（mental rotation）之中。\n")
        self.assertTrue(lint(self.root, self.cfg)["passed"])

    def test_diagram_widths_and_unclosed_fences(self):
        self.chapter("# 測試\n```text\n┌────┐\n│中文│\n└────┘\n```\n")
        self.assertTrue(check(self.root)["passed"])
        self.chapter("# 測試\n```text\n┌────┐\n│中文字│\n└────┘\n```\n")
        self.assertFalse(check(self.root)["passed"])
        self.chapter("# 測試\n```\nunclosed\n")
        self.assertFalse(check(self.root)["passed"])

    def test_invalid_or_empty_panels_do_not_vote(self):
        for value in ["garbage", '{"status":"complete","claims":[]}', '{"status":"complete","claims":[{"verdict":"correct"}]}']:
            with self.assertRaises(ValueError):
                parse_panel(value)

    def test_quorum_and_writer_exclusion(self):
        self.assertEqual(aggregate([panel("google"), panel("anthropic")], "openai"), "PASS")
        self.assertEqual(aggregate([panel("openai"), panel("google")], "openai"), "INCONCLUSIVE")
        self.assertEqual(aggregate([panel("google"), panel("google")], "openai"), "INCONCLUSIVE")
        self.assertEqual(aggregate([panel("google", "imprecise"), panel("anthropic")], "openai"), "WARN")
        self.assertEqual(aggregate([panel("google", "incorrect"), panel("anthropic", "incorrect")], "openai"), "FAIL")
        self.assertEqual(aggregate([panel("google"), panel("anthropic"), {"family": "openai", "status": "error"}], "openai"), "PASS")

    def test_duplicate_family_config_rejected(self):
        path = self.root / "panel.json"
        write_json(path, {"providers": [{"family": "google", "command": ["x"]}] * 2})
        with self.assertRaises(ValueError):
            providers_from(path)

    def test_cli_timeout_and_invalid_json(self):
        provider = dict(family="google", command=[sys.executable, "-c", "import time; time.sleep(10)"])
        self.assertEqual(run_panel(provider, "prompt", .1)["status"], "error")
        provider["command"] = [sys.executable, "-c", "print('not JSON')"]
        self.assertEqual(run_panel(provider, "prompt", 2)["status"], "error")

    def test_cache_invalidation_and_unmatched_selection(self):
        chapter = self.chapter()
        write_json(self.root / "_meta/dummy.json", {})
        baseline = self.root / "_meta/running-examples.md"
        baseline.write_text("No shared numbers")
        providers = [dict(family=f, command=["test"]) for f in ["google", "anthropic"]]
        with patch("verify_book.run_panel", side_effect=lambda p, *a: panel(p["family"])) as call:
            def run(**kw):
                return verify(self.root, self.cfg, providers, "openai", "Check claims", 1, **kw)
            self.assertEqual(run()["verdict"], "PASS")
            self.assertEqual(call.call_count, 2)
            run()
            self.assertEqual(call.call_count, 2)
            baseline.write_text("Changed baseline")
            run()
            self.assertEqual(call.call_count, 4)
            chapter.write_text(chapter.read_text() + "\nNew claim")
            run()
            self.assertEqual(call.call_count, 6)
            run(no_cache=True)
            self.assertEqual(call.call_count, 8)
            evidence = self.root / "_meta/source-evidence" / (chapter.stem + ".md")
            evidence.parent.mkdir()
            evidence.write_text("Independently read primary-source passage")
            run()
            self.assertEqual(call.call_count, 10)
            with self.assertRaises(ValueError):
                run(selected=["not-a-chapter"])

    def setup_reader(self):
        source = self.chapter("# 測試\n\n內容 </script><script>window.bad=true</script>")
        config = self.root / "book.config.json"
        write_json(config, dict(id="test", title="Test </script> ' \"", groups=[dict(title="章節", files=[source.name])], output="reader.html"))
        registry = self.root / "books.json"
        write_json(registry, dict(shelf_output="shelf.html", books=[dict(id="test", config=config.name)]))
        return config, registry

    def test_builders_and_script_escaping(self):
        config, registry = self.setup_reader()
        build_shelf(registry)
        build_reader(config, registry)
        text = (self.root / "reader.html").read_text()
        self.assertNotIn("@@BOOK_DATA@@", text)
        self.assertIn("\\u003c/script\\u003e", text)
        self.assertNotIn("window.bad=true</script>", text)
        self.assertIn('href="shelf.html"', text)
        self.assertIn("wrapCJK", text)

    def test_duplicate_manifest_and_missing_source_fail(self):
        config, registry = self.setup_reader()
        build_shelf(registry)
        cfg = json.loads(config.read_text())
        cfg["groups"][0]["files"] *= 2
        write_json(config, cfg)
        with self.assertRaises(ValueError):
            build_reader(config, registry)
        cfg["groups"][0]["files"] = ["missing.md"]
        write_json(config, cfg)
        with self.assertRaises(ValueError):
            build_shelf(registry)

    def test_duplicate_book_namespace_rejected(self):
        config, registry = self.setup_reader()
        data = json.loads(registry.read_text())
        data["books"] *= 2
        write_json(registry, data)
        with self.assertRaises(ValueError):
            build_shelf(registry)

    def test_empty_manifest_group_fails(self):
        config, registry = self.setup_reader()
        cfg = json.loads(config.read_text())
        cfg["groups"].append(dict(title="Missing", dir="absent", pattern="*.md"))
        write_json(config, cfg)
        with self.assertRaises(ValueError):
            build_shelf(registry)

    def test_image_embedding_and_remote_failure(self):
        source = self.chapter()
        (self.root / "test.png").write_bytes(b"test")
        self.assertIn("data:image/png;base64,", embed_images("![caption](test.png)", source))
        with self.assertRaises(ValueError):
            embed_images("![caption](https://example.com/test.png)", source)


if __name__ == "__main__":
    unittest.main()
