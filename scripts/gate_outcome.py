"""The outcome of ``make reconstruct`` and ``make measure``, over all scripts.

Each target runs every script and does not stop at the first that fails. A
script that does not pass appends one line to a record: its exit code and its
name. This script opens the record at the start of the target and reads it at
the end.

The end reports three kinds of script:

* passed: exit code 0, and nothing is recorded;
* not checked: exit code 3, ``NOT_CHECKED`` in ``scripts/_report.py``, which a
  script takes when its data is not in the tree;
* failed: any other exit code.

The summary exits with 0 only when every script passed, so that a green target
is a list of scripts that ran. It exits with 1 when any script failed and with
3 when some were not checked and none failed. ``make`` reports that as
``Error 1`` or ``Error 3`` and exits with 2 itself.

The source archive does not carry ``tests/data.py``, so from the archive some
scripts are always not checked. ``--expect`` names them. The target then
passes when exactly those were not checked and nothing failed, and fails when
the set differs in either direction. A script that runs there although its
data should be absent is as much a finding as one that stops for another
reason. ``make sdist-test`` passes the sets.

Usage, from the Makefile::

    python scripts/gate_outcome.py reconstruct --start
    python scripts/gate_outcome.py reconstruct --expect "a.py b.py"
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _report import NOT_CHECKED, ROOT  # noqa: E402

RECORDS = ROOT / ".gate-outcome"
"""Where the records lie between the lines of a target. In ``.gitignore``."""

FAILED = 1


def record_of(target: str) -> Path:
    """Return the file that holds the record of one target."""
    return RECORDS / target


def start(target: str) -> None:
    """Open an empty record, so that an interrupted run leaves nothing behind."""
    RECORDS.mkdir(exist_ok=True)
    record_of(target).write_text("", encoding="utf-8")


def read(target: str) -> list[tuple[int, str]]:
    """Return the recorded scripts as pairs of exit code and name.

    A missing record means the target did not open one, which is a defect of
    the Makefile and is refused rather than read as a clean run.
    """
    path = record_of(target)
    if not path.exists():
        raise SystemExit(
            f"No record for make {target}: {path} is missing, so the target did "
            "not start it, and a missing record is not a clean run."
        )

    entries = []
    for line in path.read_text(encoding="utf-8").splitlines():
        code, name = line.split(maxsplit=1)
        entries.append((int(code), name.strip()))

    return entries


def outcome(entries: list[tuple[int, str]], expected: set[str]) -> tuple[int, str]:
    """Return the exit code of the target and the sentence that explains it."""
    failed = sorted(f"{name} ({code})" for code, name in entries if code != NOT_CHECKED)
    missing = {name for code, name in entries if code == NOT_CHECKED}

    if failed:
        return FAILED, f"failed: {', '.join(failed)}."

    if expected:
        if missing == expected:
            return 0, (
                f"not checked, as expected here: {', '.join(sorted(missing))}. "
                "Everything else passed."
            )
        return FAILED, (
            f"not checked: {', '.join(sorted(missing)) or 'nothing'}; expected "
            f"{', '.join(sorted(expected))}. The two sets have to agree."
        )

    if missing:
        return NOT_CHECKED, (
            f"not checked: {', '.join(sorted(missing))}. Everything else passed, "
            "and a target with a script not checked is not green."
        )

    return 0, "every script passed."


def main(argv: list[str] | None = None) -> int:
    """Open or close the record of one target."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("target", choices=("reconstruct", "measure"))
    parser.add_argument("--start", action="store_true")
    parser.add_argument("--expect", default="")
    arguments = parser.parse_args(argv)

    if arguments.start:
        start(arguments.target)
        return 0

    code, sentence = outcome(read(arguments.target), set(arguments.expect.split()))
    print(f"\nmake {arguments.target}: {sentence}")

    return code


if __name__ == "__main__":
    raise SystemExit(main())
