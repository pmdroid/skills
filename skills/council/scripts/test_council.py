#!/usr/bin/env python3
"""Unit tests for the council helper. No network."""

from __future__ import annotations

import tempfile
import types
import unittest
from pathlib import Path


def load_council():
    path = Path(__file__).with_name("council")
    module = types.ModuleType("council")
    exec(compile(path.read_text(), str(path), "exec"), module.__dict__)
    return module


C = load_council()


class BuildArgvTests(unittest.TestCase):
    def test_cursor_uses_ask_not_plan(self) -> None:
        argv, use_stdin = C.build_argv("cursor", None, None, ".")
        self.assertFalse(use_stdin)
        self.assertIn("--mode", argv)
        self.assertEqual(argv[argv.index("--mode") + 1], "ask")
        self.assertNotIn("plan", argv)
        self.assertIn("--output-format", argv)
        self.assertEqual(argv[argv.index("--output-format") + 1], "text")

    def test_no_default_model_injected(self) -> None:
        for engine in ("claude", "codex", "cursor", "grok", "opencode"):
            argv, _ = C.build_argv(engine, None, None, ".")
            joined = " ".join(argv)
            self.assertNotIn("gpt-5.6-sol", joined)
            self.assertNotIn("kimi-k3-max", joined)
            self.assertNotIn("--model", argv)
            self.assertNotIn("-m", argv)

    def test_model_passed_when_requested(self) -> None:
        argv, _ = C.build_argv("cursor", "kimi-k3-max", None, ".")
        self.assertIn("--model", argv)
        self.assertEqual(argv[argv.index("--model") + 1], "kimi-k3-max")

    def test_grok_is_headless_print(self) -> None:
        argv, use_stdin = C.build_argv("grok", None, None, "/tmp/work")
        self.assertFalse(use_stdin)
        self.assertEqual(argv[0], "grok")
        self.assertIn("-p", argv)
        self.assertIn("--no-plan", argv)
        self.assertIn("--no-subagents", argv)
        self.assertIn("--cwd", argv)
        self.assertEqual(argv[argv.index("--cwd") + 1], "/tmp/work")


class ReplyTests(unittest.TestCase):
    def test_empty_reply(self) -> None:
        self.assertTrue(C.is_empty_reply(""))
        self.assertTrue(C.is_empty_reply("\n  \n"))
        self.assertFalse(C.is_empty_reply("recommendation\nconfidence 70"))

    def test_classify_error(self) -> None:
        self.assertEqual(C.classify_error("Failed to authenticate: OAuth session expired"), "auth")
        self.assertEqual(C.classify_error("You've hit your usage limit"), "quota")
        self.assertEqual(
            C.classify_error("The 'gpt-5.6-sol' model is not supported when using Codex"),
            "bad-model",
        )
        self.assertEqual(C.classify_error("Unexpected server error"), "error")

    def test_persist_unique_names(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env_home = Path(tmp)
            self.assertEqual(C.reply_slug("cursor", "kimi-k3-max"), "cursor-kimi-k3-max")
            first = C.unique_path(env_home, "cursor", ".md")
            first.write_text("one")
            second = C.unique_path(env_home, "cursor", ".md")
            self.assertNotEqual(first, second)


if __name__ == "__main__":
    raise SystemExit(unittest.main())
