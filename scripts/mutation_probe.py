"""Mutation probe: break one promise and see whether the suite notices.

Full statement coverage says every line ran. It does not say that removing a
line would be noticed, and those are different questions. A check with no
negative control runs, passes, and would go on passing if it were deleted --
which is the state ``AGENTS.md`` forbids and which nothing in the gates
detects.

This script answers the question directly. Each probe replaces one fragment of
the source with a fragment that breaks the promise beside it, runs the fast
suite, and puts the fragment back. ``CAUGHT`` means at least one test failed
and the promise has a control. ``MISSED`` means the suite is indifferent to
whether the promise is kept.

**Nothing here writes to the repository.** The project is copied into a
temporary directory first, and every edit, every test run and every restore
happens inside that copy. Until ``0.4.0rc14`` the script mutated the real
``src/`` and put it back by deleting that directory and copying a snapshot
over it. That is a destructive operation on the working tree with no safe
failure: an interrupt between the delete and the copy, an error inside the
copy, or a second run started while the first is mutating, and the repository
is left without a source directory or with a mutation in it. An audit of
``0.4.0rc13`` found mutated files left behind after a run that reported
success. The mechanism was not established -- it did not reproduce here -- and
the design is replaced rather than patched, because a probe that can damage
the tree is not worth running whatever the mechanism turns out to be.

Restoring is now one file written back from the text it held, so there is no
directory removal anywhere in this script.

It is not a gate. It copies the project once and takes about ten seconds per
probe, which is too slow for a pre-commit loop and too blunt for a release
chain: a ``MISSED`` is not always a defect. Some clauses cannot fail on
supplied data, and for those the right answer is to say so on the contract
page rather than to write a test that forces an unreachable state.

What these probes do and do not reproduce
-----------------------------------------

They ask today's question of today's code. Every one of them should report
``CAUGHT``; a miss means a control has been lost since ``0.4.0rc13``, and
``tests/test_scripts.py`` checks that every fragment still matches the code it
aims at. The set grew to eighteen with ``UnipotentStep``, whose three source
obligations are the first here that a constructed step cannot make true, and to
twenty-four with the homogenization twenty-nine with the
compression, thirty-four with the symmetric lift and thirty-seven with the
findings of the audit of ``0.6.0rc1``.

They do **not** reproduce the ten misses of the first run, and until
``0.4.0rc14`` this file and ``CHANGELOG.md`` said they did. Two reasons. The
misses were fixed in ``0.4.0rc13``, so those twelve probes against the current
tree report caught, which is what fixing them means. And the set that
produced the ten was not written down: the clause that turned out to be
redundant rather than uncontrolled -- the fold's verification of its result
against its own ``target`` -- has no probe here, and cannot usefully have one,
since a clause that cannot fail on supplied data reports ``MISSED`` for a
reason that is not a missing control. The historical number stands in
``CHANGELOG.md`` as the record of a run, not as something this file
re-derives.

Usage::

    python scripts/mutation_probe.py
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# What the working copy does not need: environments, caches, build output and
# version control. The fast suite reads ``docs/`` and ``README.md``, so
# everything else stays in.
LEAVE_OUT = shutil.ignore_patterns(
    ".git",
    ".venv",
    "__pycache__",
    "*.egg-info",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".coverage*",
    "htmlcov",
    "dist",
    "build",
    "build_env",
    "min_env",
)


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
    Probe(
        "UNI-1",
        "the identity of the unipotent step is compared",
        "src/kellermap/bcw/unipotent.py",
        "        if composite != self._target:",
        "        if False:",
    ),
    Probe(
        "UNI-2",
        "the source of the unipotent step lies in MA^1",
        "src/kellermap/bcw/unipotent.py",
        "        if order < 2:",
        "        if False:",
    ),
    Probe(
        "UNI-3",
        "the source of the unipotent step has degree at most three",
        "src/kellermap/bcw/unipotent.py",
        "        if degree > 3:",
        "        if False:",
    ),
    Probe(
        "UNI-4",
        "the source of the unipotent step is Keller",
        "src/kellermap/bcw/unipotent.py",
        "        if not agree(determinant, sp.Integer(1)):",
        "        if False:",
    ),
    Probe(
        "UNI-11",
        "UnipotentStep.transport verifies its input",
        "src/kellermap/bcw/unipotent.py",
        "        collision.verify(self._source)",
        "        pass",
    ),
    Probe(
        "UNI-11",
        "UnipotentStep.transport verifies its output",
        "src/kellermap/bcw/unipotent.py",
        "        moved.verify(self._target)\n\n        return moved",
        "        return moved",
    ),
    Probe(
        "HOM-1",
        "the identity of the homogenization is compared",
        "src/kellermap/bcw/homogenization.py",
        "        if self._composite() != self._target:",
        "        if False:",
    ),
    Probe(
        "HOM-2",
        "the source of the homogenization has degree at most three",
        "src/kellermap/bcw/homogenization.py",
        "        if degree > 3:",
        "        if False:",
    ),
    Probe(
        "HOM-3",
        "the source of the homogenization has nilpotent Jacobian",
        "src/kellermap/bcw/homogenization.py",
        "        determinant = scaled_displacement(self._source).determinant()",
        "        determinant = sp.Integer(1)",
    ),
    Probe(
        "HOM-8",
        "the slice at T = 1 is compared with the source",
        "src/kellermap/bcw/homogenization.py",
        "        if sliced != wanted:",
        "        if False:",
    ),
    Probe(
        "HOM-9",
        "HomogenizationStep.transport verifies its input",
        "src/kellermap/bcw/homogenization.py",
        "        collision.verify(self._source)",
        "        pass",
    ),
    Probe(
        "HOM-9",
        "HomogenizationStep.transport verifies its output",
        "src/kellermap/bcw/homogenization.py",
        "        moved.verify(self._target)\n\n        return moved",
        "        return moved",
    ),
    Probe(
        "CHC-1",
        "the restriction is compared in every coordinate of the source",
        "src/kellermap/compression.py",
        "            if combined != substituted[position]:",
        "            if False:",
    ),
    Probe(
        "CHC-3",
        "the displacement of the source is homogeneous",
        "src/kellermap/compression.py",
        "    if len(degrees) != 1:",
        "    if False:",
    ),
    Probe(
        "CHC-4",
        "the source of the compression is Keller",
        "src/kellermap/compression.py",
        "        if not agree(determinant, sp.Integer(1)):",
        "        if False:",
    ),
    Probe(
        "CHC-9",
        "a collision leaving the subspace is refused",
        "src/kellermap/compression.py",
        "        if not echelon.spans(_to_domain(vector, domain)):",
        "        if False:",
    ),
    Probe(
        "CHC-9",
        "CompressionStep.transport verifies its output",
        "src/kellermap/compression.py",
        "        moved.verify(self._target)\n\n        return moved",
        "        return moved",
    ),
    Probe(
        "SYM-1",
        "the identity of the symmetric lift is compared",
        "src/kellermap/lift.py",
        "        if self._composite() != self._target:",
        "        if False:",
    ),
    Probe(
        "SYM-3",
        "the displacement of the source is homogeneous",
        "src/kellermap/lift.py",
        "    if len(degrees) != 1:",
        "    if False:",
    ),
    Probe(
        "SYM-4",
        "the source of the lift is Keller",
        "src/kellermap/lift.py",
        "        if determinant != 1:",
        "        if False:",
    ),
    Probe(
        "SYM-5",
        "the coefficient domain of the target is compared",
        "src/kellermap/lift.py",
        "        if self._target.ring.domain != wanted:",
        "        if False:",
    ),
    Probe(
        "SYM-9",
        "a collision of more than two points is refused",
        "src/kellermap/lift.py",
        "        if len(collision.points) != 2:",
        "        if False:",
    ),
    Probe(
        "SYM-8",
        "the pair is oriented from the set and not from the tuple",
        "src/kellermap/lift.py",
        "        first, second = sorted(points, key=printed)",
        "        first, second = points",
    ),
    Probe(
        "CHC-2",
        "the coefficient domain of the compression is a field",
        "src/kellermap/compression.py",
        "    if not domain.is_Field:",
        "    if False:",
    ),
    Probe(
        "CHC-8",
        "the coefficient domain has characteristic zero",
        "src/kellermap/compression.py",
        "    if domain.characteristic() != 0:",
        "    if False:",
    ),
)


def run_suite(root: Path) -> tuple[bool, str]:
    """Return whether the fast suite failed under ``root``, and the line saying so."""
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
        cwd=root,
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


def apply(probe: Probe, root: Path) -> str:
    """Write the broken version of one fragment, and return the text it replaced.

    The caller hands that text back to ``restore``. Passing the original out
    rather than keeping a snapshot of the tree elsewhere is what removes the
    directory removal from this script: one file is written, and the same file
    is written back.
    """
    path = root / probe.path
    text = path.read_text(encoding="utf-8")

    if probe.old not in text:
        raise SystemExit(
            f"{probe.obligation}: the fragment is not in {probe.path} any more. "
            "The probe has to be updated with the code it aims at."
        )

    path.write_text(text.replace(probe.old, probe.new, 1), encoding="utf-8")

    return text


def restore(probe: Probe, root: Path, text: str) -> None:
    """Put the file back as it was."""
    (root / probe.path).write_text(text, encoding="utf-8")


def working_copy(scratch: Path) -> Path:
    """Copy the project into ``scratch`` and return the copy's root.

    Everything the fast suite reads comes along: the sources, the tests, the
    fixed data under ``tests/``, ``docs/`` and ``README.md`` for the
    documentation gate, and ``pyproject.toml`` with ``uv.lock`` so that the run
    resolves the same dependencies.
    """
    copy = scratch / "project"
    shutil.copytree(ROOT, copy, ignore=LEAVE_OUT)

    # The reason the script was rebuilt, written as a check and not only as a
    # sentence in the docstring.
    if copy.resolve() == ROOT.resolve():  # pragma: no cover - see the condition
        raise SystemExit("The working copy is the repository. Refusing to run.")

    return copy


def sweep(
    probes: Sequence[Probe],
    run: Callable[[Path], tuple[bool, str]] = run_suite,
) -> int:
    """Run every probe against a copy of the project. Return the number of misses.

    ``run`` is a parameter so that ``tests/test_scripts.py`` can drive a whole
    sweep without spending two minutes on twelve suite runs. What the test
    checks is the part that damaged a tree: that the repository is untouched
    afterwards, and that every fragment still matches the code it aims at.
    """
    missed = 0
    with tempfile.TemporaryDirectory() as scratch:
        copy = working_copy(Path(scratch))

        for probe in probes:
            original = apply(probe, copy)
            try:
                caught, summary = run(copy)
            finally:
                restore(probe, copy, original)

            missed += not caught
            mark = "CAUGHT " if caught else "MISSED "
            print(f"{mark} {probe.obligation:7} {probe.what:46} {summary}")
            sys.stdout.flush()

    return missed


def main() -> int:
    print(f"{len(PROBES)} probes, run against a copy of the project.")
    print("The repository is not written to.\n")
    missed = sweep(PROBES)
    print(f"\n{missed} of {len(PROBES)} promises have no control.")

    # No non-zero return value: a miss is a question and not a defect. Whoever
    # puts this script into a chain decides what number to expect.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
