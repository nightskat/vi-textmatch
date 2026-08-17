"""Command-line interface for vi-textmatch."""

import argparse
import json
import sys
from typing import Sequence

from vi_textmatch.compare import Kind, Verdict, closest, compare
from vi_textmatch.normalize import normalize

_LEVEL_VI: dict[str, str] = {
    "IDENTICAL": "TRÙNG  (IDENTICAL)",
    "TYPO": "GẦN TRÙNG  (TYPO)",
    "DIFFERENT": "KHÁC  (DIFFERENT)",
}


def _parse_kind(val: str) -> Kind:
    """Parse string into Kind enum (case-insensitive)."""
    try:
        return Kind(val.upper())
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"kind không hợp lệ: '{val}' (chọn từ 'text', 'id', 'money', 'date')"
        )


def _human_detail(detail: str) -> str:
    """Translate or format English Verdict detail into Vietnamese for terminal display."""
    if detail == "Strings are identical after normalization":
        return "Giống nhau sau khi chuẩn hoá"
    if detail.startswith("Match ratio: "):
        rest = detail[len("Match ratio: "):]
        if "(typo suspected)" in rest:
            rest = rest.replace("(typo suspected)", "(nghi lỗi gõ)")
        return f"Tỉ lệ khớp: {rest}"
    if detail == "ID values match exactly after cleaning whitespace and hyphens":
        return "Giống nhau sau khi bỏ khoảng trắng và dấu gạch"
    if detail == "ID values do not match":
        return "Giá trị ID không trùng nhau"
    if detail == "Monetary values match exactly":
        return "Giá trị tiền tệ trùng nhau"
    if detail == "Monetary values differ":
        return "Giá trị tiền tệ khác nhau"
    if detail == "Dates match exactly":
        return "Ngày tháng trùng nhau"
    if detail == "Dates differ":
        return "Ngày tháng khác nhau"
    return detail


def _resolve_stdin_args(args_list: list[str]) -> list[str]:
    """Replace '-' in positional arguments with input read from stdin."""
    dash_count = args_list.count("-")
    if dash_count == 0:
        return args_list
    if dash_count == 1:
        content = sys.stdin.read().rstrip("\r\n")
        return [content if x == "-" else x for x in args_list]
    else:
        lines = sys.stdin.read().splitlines()
        line_iter = iter(lines)
        return [next(line_iter, "") if x == "-" else x for x in args_list]


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the main argument parser."""
    parser = argparse.ArgumentParser(
        prog="vi-textmatch",
        description="Thư viện chuẩn hoá và so khớp văn bản tiếng Việt theo kiểu dữ liệu.",
    )
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # Subcommand: compare
    p_compare = subparsers.add_parser(
        "compare", help="So sánh hai chuỗi theo kiểu dữ liệu."
    )
    p_compare.add_argument("a", help="Chuỗi A (dùng '-' để đọc từ stdin)")
    p_compare.add_argument("b", help="Chuỗi B (dùng '-' để đọc từ stdin)")
    p_compare.add_argument(
        "--kind",
        required=True,
        type=_parse_kind,
        help="Kiểu dữ liệu (bắt buộc): text, id, money, date",
    )
    p_compare.add_argument(
        "--json", action="store_true", help="Xuất kết quả dạng JSON một dòng"
    )

    # Subcommand: normalize
    p_normalize = subparsers.add_parser(
        "normalize", help="Chuẩn hoá văn bản tiếng Việt."
    )
    p_normalize.add_argument(
        "text", help="Chuỗi cần chuẩn hoá (dùng '-' để đọc từ stdin)"
    )
    p_normalize.add_argument(
        "--json", action="store_true", help="Xuất kết quả dạng JSON một dòng"
    )

    # Subcommand: closest
    p_closest = subparsers.add_parser(
        "closest", help="Tìm các chuỗi ứng viên gần nhất."
    )
    p_closest.add_argument("needle", help="Chuỗi cần tìm (dùng '-' để đọc từ stdin)")
    p_closest.add_argument(
        "candidates",
        nargs="+",
        help="Danh sách các chuỗi ứng viên (dùng '-' để đọc từ stdin)",
    )
    p_closest.add_argument(
        "--kind",
        type=_parse_kind,
        default=None,
        help="Kiểu dữ liệu (tùy chọn): text, id, money, date",
    )
    p_closest.add_argument(
        "-t",
        "--top",
        type=int,
        default=3,
        help="Số lượng ứng viên tối đa trả về (mặc định: 3)",
    )
    p_closest.add_argument(
        "--json", action="store_true", help="Xuất kết quả dạng JSON một dòng"
    )

    return parser


def main(argv: Sequence[str] | None = None) -> None:
    """CLI entry point."""
    parser = create_parser()

    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        sys.exit(exc.code)

    if args.subcommand == "compare":
        resolved = _resolve_stdin_args([args.a, args.b])
        str_a, str_b = resolved[0], resolved[1]
        kind_enum: Kind = args.kind

        try:
            verdict: Verdict = compare(str_a, str_b, kind=kind_enum)
        except ValueError as err:
            print(f"Lỗi: {err}", file=sys.stderr)
            sys.exit(2)

        if args.json:
            out = {
                "match": verdict.match,
                "level": verdict.level,
                "detail": verdict.detail,
                "kind": kind_enum.value.lower(),
                "a": str_a,
                "b": str_b,
            }
            print(json.dumps(out, ensure_ascii=False))
        else:
            header = _LEVEL_VI.get(verdict.level, verdict.level)
            detail_vi = _human_detail(verdict.detail)
            print(header)
            print(detail_vi)

        if verdict.match:
            sys.exit(0)
        else:
            sys.exit(1)

    elif args.subcommand == "normalize":
        resolved = _resolve_stdin_args([args.text])
        text_in = resolved[0]
        norm_res = normalize(text_in)

        if args.json:
            out = {"text": text_in, "normalized": norm_res}
            print(json.dumps(out, ensure_ascii=False))
        else:
            print(norm_res)

        sys.exit(0)

    elif args.subcommand == "closest":
        resolved = _resolve_stdin_args([args.needle] + list(args.candidates))
        needle_in = resolved[0]
        candidates_in = resolved[1:]
        top_n: int = args.top

        matches = closest(needle_in, candidates_in, n=top_n)

        if args.json:
            out = {"needle": needle_in, "matches": matches}
            print(json.dumps(out, ensure_ascii=False))
        else:
            for match_item in matches:
                print(match_item)

        sys.exit(0)

    else:
        parser.print_help(sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
