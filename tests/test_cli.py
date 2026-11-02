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


# --- Phản biện Grok 17/08: 5 chỗ hỏng của CLI ---------------------------------

class TestGrokFindings(unittest.TestCase):
    """Mỗi test là một ca Grok dùng để chọc thủng CLI. Giữ lại làm lưới an toàn."""

    def _run(self, argv, stdin_text=None):
        """Chạy main() thật, trả (mã thoát, stdout, stderr)."""
        out, err = io.StringIO(), io.StringIO()
        code = 0
        stdin = io.StringIO(stdin_text) if stdin_text is not None else io.StringIO("")
        with patch.object(sys, "stdout", out), patch.object(sys, "stderr", err), \
             patch.object(sys, "stdin", stdin):
            try:
                main(argv)
            except SystemExit as e:
                code = e.code if isinstance(e.code, int) else 1
        return code, out.getvalue(), err.getvalue()

    def test_closest_honours_kind_money(self):
        # #1 — `--kind` từng bị nhận rồi vứt: "2,5" và "2.50" là CÙNG số tiền.
        code, out, _ = self._run(["closest", "2,5", "2.50", "zzz", "--kind", "money", "--json"])
        self.assertEqual(json.loads(out)["matches"], ["2.50"])
        self.assertEqual(code, 0)

    def test_closest_honours_kind_date(self):
        # #1 — cùng một ngày viết hai kiểu.
        code, out, _ = self._run(["closest", "15/02/2026", "2026-02-15", "foo", "--kind", "date"])
        self.assertIn("2026-02-15", out)
        self.assertEqual(code, 0)

    def test_ambiguous_date_needs_order_flag(self):
        # 01/02/2026 mơ hồ: không đoán; --day-first thì đọc DD/MM.
        code, out, _ = self._run(["compare", "01/02/2026", "2026-02-01", "--kind", "date"])
        self.assertIn("AMBIGUOUS", out)
        self.assertEqual(code, 1)
        code, out, _ = self._run(
            ["compare", "01/02/2026", "2026-02-01", "--kind", "date", "--day-first"]
        )
        self.assertEqual(code, 0)
        code, out, _ = self._run(
            ["closest", "01/02/2026", "2026-02-01", "foo", "--kind", "date", "--day-first"]
        )
        self.assertIn("2026-02-01", out)

    def test_stdin_missing_line_is_usage_error(self):
        # #2 — hai '-' mà stdin chỉ có một dòng: từng lặng lẽ so với chuỗi rỗng
        # và tuyên bố "KHÁC" cho một mã định danh hợp lệ.
        code, _, err = self._run(["compare", "-", "-", "--kind", "id"], stdin_text="031234567890\n")
        self.assertEqual(code, 2)
        self.assertIn("stdin", err)

    def test_stdin_two_lines_still_works(self):
        code, _, _ = self._run(["compare", "-", "-", "--kind", "text"], stdin_text="Hoà\nHòa\n")
        self.assertEqual(code, 0)

    def test_top_zero_is_usage_error_not_traceback(self):
        # #4 — từng nổ ValueError ra ngoài với mã thoát 1.
        code, _, err = self._run(["closest", "Hoà", "Hòa", "--top", "0"])
        self.assertEqual(code, 2)
        self.assertIn("--top", err)

    def test_closest_no_match_exits_one(self):
        # #5 — không tìm được gì mà vẫn báo thành công.
        code, _, _ = self._run(["closest", "zzzz", "aaaa", "bbbb", "--json"])
        self.assertEqual(code, 1)

    def test_closest_with_match_exits_zero(self):
        code, _, _ = self._run(["closest", "Hoà", "Hòa", "Hoa"])
        self.assertEqual(code, 0)
