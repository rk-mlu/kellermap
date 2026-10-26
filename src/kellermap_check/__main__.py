"""``python -m kellermap_check FILE [--skip ID ...]``, CHK-6.

The exit status is 0 for ``VERIFIED``, 1 for ``REFUSED``, 2 for a file that
cannot be opened or a wrong call, and 3 for ``INCOMPLETE``.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from . import CHECKS, INCOMPLETE, REFUSED, Refusal, check


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m kellermap_check",
        description="Check a kellermap certificate file without kellermap.",
    )
    parser.add_argument("file", type=Path, help="the certificate file")
    parser.add_argument(
        "--skip",
        action="append",
        default=[],
        metavar="ID",
        help=f"leave out a check; one of {', '.join(sorted(CHECKS))}",
    )
    try:
        arguments = parser.parse_args(argv)
    except SystemExit as stop:
        return 2 if stop.code else 0

    try:
        text = arguments.file.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as failure:
        print(f"{arguments.file}: cannot be read: {failure}", file=sys.stderr)
        return 2

    try:
        report = check(text, arguments.skip)
    except ValueError as failure:
        print(str(failure), file=sys.stderr)
        return 2
    except Refusal as refusal:
        print(f"{REFUSED} {arguments.file}")
        print(f"  [{refusal.obligation}] in {refusal.location}: {refusal.message}")
        return 1

    print(f"{report.verdict} {arguments.file}")
    for line in report.lines()[1:]:
        print(line)

    return 3 if report.verdict == INCOMPLETE else 0


if __name__ == "__main__":  # pragma: no cover - the module runs as a script only
    raise SystemExit(main())
