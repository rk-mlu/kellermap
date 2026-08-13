"""Mutation probe: break one promise and see whether the suite notices.

Full statement coverage says every line ran. It does not say that removing a
line would be noticed, and those are different questions. A check with no
negative control runs, passes, and would go on passing if it were deleted --
which is the state ``AGENTS.md`` forbids and which nothing in the gates
detects.

This script answers the question directly. Each probe replaces one fragment of
the source with a fragment that breaks the promise beside it, runs the fast
suite, and restores the source. ``CAUGHT`` means at least one test failed and
the promise has a control. ``MISSED`` means the suite is indifferent to whether
the promise is kept.

It is not a gate. It rebuilds the source tree between probes and takes about
ten seconds per probe, which is too slow for a pre-commit loop and too blunt
for a release chain: a ``MISSED`` is not always a defect. Some clauses cannot
fail on supplied data, and for those the right answer is to say so on the
contract page rather than to write a test that forces an unreachable state.
The run of ``0.4.0rc13`` produced ten misses, of which nine were missing
controls and one -- the fold's verification against its own target -- was
provably redundant.

Usage::

    python scripts/mutation_probe.py

The probes below are the ones that were run for ``0.4.0rc13``. They are kept
rather than deleted so that a later change to the same lines can be checked
against the same question, and so that the numbers in ``CHANGELOG.md`` can be
reproduced.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "src"


@dataclass(frozen=True)
class Probe:
    """One promise, and the edit that breaks it.

    ``obligation`` names the clause of ``docs/contracts.md`` the edit is aimed
    at, so that a miss can be looked up rather than guessed at.
    """

    obligation: str
    what: str
    path: str
    old: str
    new: str


PROBES: tuple[Probe, ...] = (
    Probe(
        "BCW-8",
        "BCWStep.transport verifies its input",
        "src/kellermap/bcw/step.py",
        "        collision.verify(self._source)",
        "        pass",
    ),
    Probe(
        "BCW-8",
        "BCWStep.transport verifies its output",
        "src/kellermap/bcw/step.py",
        "        moved.verify(self._target)",
        "        pass",
    ),
    Probe(
        "LIN-5",
        "LinearStep.transport verifies its input",
        "src/kellermap/reduction.py",
        "        collision.verify(self._source)\n\n        matrix = sp.Matrix(",
        "        matrix = sp.Matrix(",
    ),
    Probe(
        "LIN-5",
        "LinearStep.transport verifies its output",
        "src/kellermap/reduction.py",
        "        moved.verify(self._target)\n\n        return moved",
        "        return moved",
    ),
    Probe(
        "TRA-7",
        "TranslationStep.transport verifies its input",
        "src/kellermap/reduction.py",
        "        collision.verify(self._source)\n\n"
        "        moved = collision.with_image(",
        "        moved = collision.with_image(",
    ),
    Probe(
        "TRA-7",
        "TranslationStep.transport verifies its output",
        "src/kellermap/reduction.py",
        "        moved.verify(self._target)\n\n        return moved\n",
        "        return moved\n",
    ),
    Probe(
        "RED-5",
        "the fold verifies its own input",
        "src/kellermap/reduction.py",
        "        collision.verify(self.source)\n\n        carried = collision",
        "        carried = collision",
    ),
    Probe(
        "RED-4",
        "a transport failure names the step it came from",
        "src/kellermap/reduction.py",
        "                raise failure.located_at(position) from failure",
        "                raise failure",
    ),
    Probe(
        "REV-8",
        "the stranded test discards",
        "src/kellermap/peeling.py",
        "def _stranded(source: PolynomialMap, reached: PolynomialMap) -> bool:",
        "def _stranded(source: PolynomialMap, reached: PolynomialMap) -> bool:\n"
        "    return False",
    ),
    Probe(
        "REV-9",
        "the unfinishable bound prunes",
        "src/kellermap/peeling.py",
        "    return differing > remaining",
        "    return False",
    ),
    Probe(
        "BCW-4",
        "the target index is in range",
        "src/kellermap/bcw/step.py",
        "        if not 0 <= index < source.dimension:",
        "        if False:",
    ),
    Probe(
        "COL-6",
        "the hash agrees with equality as a set",
        "src/kellermap/collision.py",
        "        return hash((frozenset(self._points), self._image))",
        "        return hash((tuple(self._points), self._image))",
    ),
)


def run_suite() -> tuple[bool, str]:
    """Return whether the fast suite failed, and the line that says so."""
    finished = subprocess.run(  # noqa: S603
        [
            "uv",
            "run",
            "pytest",
            "-q",
            "-x",
            "--no-header",
            "-p",
            "no:cacheprovider",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    summary = [
        line
        for line in finished.stdout.splitlines()
        if "passed" in line or "failed" in line
    ]

    return finished.returncode != 0, summary[-1] if summary else "no summary"


def apply(probe: Probe) -> None:
    """Write the broken version of one fragment."""
    path = ROOT / probe.path
    text = path.read_text(encoding="utf-8")

    if probe.old not in text:
        raise SystemExit(
            f"{probe.obligation}: the fragment is not in {probe.path} any more. "
            "The probe has to be updated with the code it aims at."
        )

    path.write_text(text.replace(probe.old, probe.new, 1), encoding="utf-8")


def sweep(probes: Sequence[Probe]) -> int:
    """Run every probe and report. Return the number of misses."""
    missed = 0
    with tempfile.TemporaryDirectory() as scratch:
        pristine = Path(scratch) / "src"
        shutil.copytree(SOURCE, pristine)

        for probe in probes:
            apply(probe)
            try:
                caught, summary = run_suite()
            finally:
                shutil.rmtree(SOURCE)
                shutil.copytree(pristine, SOURCE)

            missed += not caught
            mark = "CAUGHT " if caught else "MISSED "
            print(f"{mark} {probe.obligation:7} {probe.what:46} {summary}")
            sys.stdout.flush()

    return missed


def main() -> int:
    print(f"{len(PROBES)} probes; the source tree is restored after each.\n")
    missed = sweep(PROBES)
    print(f"\n{missed} of {len(PROBES)} promises have no control.")

    # Kein Rueckgabewert ungleich null: ein Fehlschlag ist eine Frage und kein
    # Defekt. Wer das Skript in eine Kette haengt, entscheidet selbst, welche
    # Zahl er erwartet.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
