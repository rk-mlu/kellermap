"""The program ``kellermap``, CLI-1 to CLI-4 of ``docs/contracts.md``.

Two commands, and no behaviour of their own::

    kellermap verify FILE [--skip ID ...]
    kellermap latex FILE [--output OUT] [--body]

``verify`` is the command line of ``kellermap_check`` under another name,
CLI-1. ``latex`` writes what ``to_latex`` returns, CLI-2. The entry point in
``pyproject.toml`` installs the program, and ``python -m kellermap`` runs the
same function, CLI-4.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

import kellermap_check.__main__

from .errors import VerificationError
from .latex import to_latex

__all__ = ["main"]


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="kellermap",
        description="Check a kellermap certificate file, or show it as LaTeX.",
    )
    commands = parser.add_subparsers(dest="command", metavar="COMMAND")

    # Listed for the help text only. ``main`` hands ``verify`` and everything
    # after it to the checker before this parser sees it, so that the checker
    # parses its own arguments, CLI-1.
    commands.add_parser(
        "verify",
        help="check a file with kellermap_check; the same as python -m kellermap_check",
        add_help=False,
    )

    latex = commands.add_parser(
        "latex",
        prog="kellermap latex",
        help="write the LaTeX view of a file the checker verifies",
        description="Write the LaTeX view of a certificate file, TEX-1 to TEX-6.",
    )
    latex.add_argument("file", type=Path, help="the certificate file")
    latex.add_argument(
        "--output",
        type=Path,
        metavar="OUT",
        help="write the view to OUT instead of the standard output",
    )
    latex.add_argument(
        "--body",
        action="store_true",
        help="write the body only, to be read into another document",
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the program and return its exit status, CLI-3."""
    arguments = list(sys.argv[1:] if argv is None else argv)

    if arguments[:1] == ["verify"]:
        return kellermap_check.__main__.main(arguments[1:], prog="kellermap verify")

    try:
        parsed = _parser().parse_args(arguments)
    except SystemExit as stop:
        return 2 if stop.code else 0

    if parsed.command is None:
        _parser().print_usage(sys.stderr)
        print("kellermap: a command is required: verify or latex", file=sys.stderr)
        return 2

    return _latex(parsed.file, parsed.output, body=parsed.body)


def _latex(file: Path, output: Path | None, *, body: bool) -> int:
    """Write the view of ``file``, CLI-2, with the status of CLI-3."""
    try:
        text = file.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as failure:
        print(f"{file}: cannot be read: {failure}", file=sys.stderr)
        return 2

    try:
        view = to_latex(text, standalone=not body)
    except VerificationError as refusal:
        print(f"{kellermap_check.REFUSED} {file}")
        # The line ``verify`` prints for the same refusal, CLI-3.
        print(f"  [{refusal.obligation}] in {refusal.location}: {refusal.message}")
        return 1

    if output is None:
        sys.stdout.write(view)
        return 0

    try:
        output.write_text(view, encoding="ascii")
    except OSError as failure:
        print(f"{output}: cannot be written: {failure}", file=sys.stderr)
        return 2

    return 0
