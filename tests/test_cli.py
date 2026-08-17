"""Unit tests for vi-textmatch CLI module."""

import io
import json
import subprocess
import sys
import unittest
from unittest.mock import patch

from vi_textmatch.cli import main


class TestCliDirect(unittest.TestCase):
    """Test CLI main function directly by patching sys.argv and stdio."""

    def test_compare_text_identical(self) -> None:
        out = io.StringIO()
        with patch.object(sys, "stdout", out):
            with self.assertRaises(SystemExit) as cm:
                main(["compare", "Nguyễn Thị Huệ", "Nguyễn Thị Huệ", "--kind", "text"])
        self.assertEqual(cm.exception.code, 0)
        output = out.getvalue().strip().splitlines()
        self.assertEqual(output[0], "TRÙNG  (IDENTICAL)")
        self.assertIn("Giống nhau", output[1])

    def test_compare_text_different(self) -> None:
        out = io.StringIO()
        with patch.object(sys, "stdout", out):
            with self.assertRaises(SystemExit) as cm:
                main(["compare", "suýt", "súyt", "--kind", "text"])
        self.assertEqual(cm.exception.code, 1)
        output = out.getvalue().strip().splitlines()
        self.assertEqual(output[0], "KHÁC  (DIFFERENT)")
        self.assertIn("Tỉ lệ khớp: 0.5000", output[1])

    def test_compare_text_json(self) -> None:
        out = io.StringIO()
        with patch.object(sys, "stdout", out):
            with self.assertRaises(SystemExit) as cm:
                main(["compare", "suýt", "súyt", "--kind", "text", "--json"])
        self.assertEqual(cm.exception.code, 1)
        data = json.loads(out.getvalue().strip())
        self.assertFalse(data["match"])
        self.assertEqual(data["level"], "DIFFERENT")
        self.assertEqual(data["kind"], "text")
        self.assertEqual(data["a"], "suýt")
        self.assertEqual(data["b"], "súyt")

    def test_compare_id_kind(self) -> None:
        out = io.StringIO()
        with patch.object(sys, "stdout", out):
            with self.assertRaises(SystemExit) as cm:
                main(["compare", "0312 3456 7890", "031234567890", "--kind", "id"])
        self.assertEqual(cm.exception.code, 0)
        self.assertIn("TRÙNG  (IDENTICAL)", out.getvalue())

        out_diff = io.StringIO()
        with patch.object(sys, "stdout", out_diff):
            with self.assertRaises(SystemExit) as cm2:
                main(["compare", "031234567890", "031234567891", "--kind", "id"])
        self.assertEqual(cm2.exception.code, 1)

    def test_compare_money_kind(self) -> None:
        out = io.StringIO()
        with patch.object(sys, "stdout", out):
            with self.assertRaises(SystemExit) as cm:
                main(["compare", "2.500.000,50 VNĐ", "2500000.50", "--kind", "money"])
        self.assertEqual(cm.exception.code, 0)

        out_diff = io.StringIO()
        with patch.object(sys, "stdout", out_diff):
            with self.assertRaises(SystemExit) as cm2:
                main(["compare", "2.500.000", "2.600.000", "--kind", "money"])
        self.assertEqual(cm2.exception.code, 1)

    def test_compare_date_kind(self) -> None:
        out = io.StringIO()
        with patch.object(sys, "stdout", out):
            with self.assertRaises(SystemExit) as cm:
                main(["compare", "17/08/2026", "2026-08-17", "--kind", "date"])
        self.assertEqual(cm.exception.code, 0)

        out_diff = io.StringIO()
        with patch.object(sys, "stdout", out_diff):
            with self.assertRaises(SystemExit) as cm2:
                main(["compare", "17/08/2026", "18/08/2026", "--kind", "date"])
        self.assertEqual(cm2.exception.code, 1)

    def test_compare_missing_kind(self) -> None:
        err = io.StringIO()
        with patch.object(sys, "stderr", err):
            with self.assertRaises(SystemExit) as cm:
                main(["compare", "a", "b"])
        self.assertEqual(cm.exception.code, 2)

    def test_compare_invalid_kind(self) -> None:
        err = io.StringIO()
        with patch.object(sys, "stderr", err):
            with self.assertRaises(SystemExit) as cm:
                main(["compare", "a", "b", "--kind", "invalid_kind"])
        self.assertEqual(cm.exception.code, 2)

    def test_compare_unparseable_money(self) -> None:
        err = io.StringIO()
        with patch.object(sys, "stderr", err):
            with self.assertRaises(SystemExit) as cm:
                main(["compare", "khong_phai_tien", "100", "--kind", "money"])
        self.assertEqual(cm.exception.code, 2)
        self.assertIn("Cannot parse MONEY", err.getvalue())

    def test_normalize(self) -> None:
        out = io.StringIO()
        with patch.object(sys, "stdout", out):
            with self.assertRaises(SystemExit) as cm:
                main(["normalize", "Nguyễn Thị  Hoà "])
        self.assertEqual(cm.exception.code, 0)
        self.assertEqual(out.getvalue().strip(), "nguyễn thị hòa")

    def test_normalize_json(self) -> None:
        out = io.StringIO()
        with patch.object(sys, "stdout", out):
            with self.assertRaises(SystemExit) as cm:
                main(["normalize", "Nguyễn Thị  Hoà ", "--json"])
        self.assertEqual(cm.exception.code, 0)
        data = json.loads(out.getvalue().strip())
        self.assertEqual(data["text"], "Nguyễn Thị  Hoà ")
        self.assertEqual(data["normalized"], "nguyễn thị hòa")

    def test_closest(self) -> None:
        out = io.StringIO()
        with patch.object(sys, "stdout", out):
            with self.assertRaises(SystemExit) as cm:
                main(["closest", "Hoà", "Hòa", "Hoa", "Bình", "--top", "2"])
        self.assertEqual(cm.exception.code, 0)
        lines = out.getvalue().strip().splitlines()
        self.assertEqual(lines, ["Hòa", "Hoa"])

    def test_closest_json(self) -> None:
        out = io.StringIO()
        with patch.object(sys, "stdout", out):
            with self.assertRaises(SystemExit) as cm:
                main(["closest", "Hoà", "Hòa", "Hoa", "Bình", "--json"])
        self.assertEqual(cm.exception.code, 0)
        data = json.loads(out.getvalue().strip())
        self.assertEqual(data["needle"], "Hoà")
        self.assertIn("Hòa", data["matches"])

    def test_stdin_input(self) -> None:
        fake_stdin = io.StringIO("Trần Văn Nam\n")
        out = io.StringIO()
        with patch.object(sys, "stdin", fake_stdin), patch.object(sys, "stdout", out):
            with self.assertRaises(SystemExit) as cm:
                main(["normalize", "-"])
        self.assertEqual(cm.exception.code, 0)
        self.assertEqual(out.getvalue().strip(), "trần văn nam")

    def test_empty_string(self) -> None:
        out = io.StringIO()
        with patch.object(sys, "stdout", out):
            with self.assertRaises(SystemExit) as cm:
                main(["compare", "", "", "--kind", "text"])
        self.assertEqual(cm.exception.code, 0)
        self.assertIn("TRÙNG  (IDENTICAL)", out.getvalue())


class TestCliSubprocess(unittest.TestCase):
    """Test CLI via subprocess to ensure full environment entrypoint correctness."""

    def test_subprocess_compare(self) -> None:
        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "vi_textmatch.cli",
                "compare",
                "suýt",
                "súyt",
                "--kind",
                "text",
            ],
            capture_output=True,
            text=True,
            env={"PYTHONPATH": "src"},
        )
        self.assertEqual(proc.returncode, 1)
        self.assertIn("KHÁC  (DIFFERENT)", proc.stdout)

    def test_subprocess_stdin(self) -> None:
        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "vi_textmatch.cli",
                "compare",
                "-",
                "Nguyễn Văn A",
                "--kind",
                "text",
                "--json",
            ],
            input="Nguyễn Văn A\n",
            capture_output=True,
            text=True,
            env={"PYTHONPATH": "src"},
        )
        self.assertEqual(proc.returncode, 0)
        data = json.loads(proc.stdout.strip())
        self.assertTrue(data["match"])
        self.assertEqual(data["a"], "Nguyễn Văn A")


if __name__ == "__main__":
    unittest.main()
