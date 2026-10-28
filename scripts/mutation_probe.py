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

It is not a gate. It copies the project once and then runs the fast suite once
per probe, under ``-x``: a caught probe stops at the first failure and a missed
one pays for the whole suite. That is too slow for a pre-commit loop and too
blunt for a release chain anyway, since a ``MISSED`` is not always a defect.
Some clauses cannot fail on supplied data, and for those the right answer is
to say so on the contract page rather than to write a test that forces an
unreachable state.

What these probes do and do not reproduce
-----------------------------------------

They ask today's question of today's code. Every one of them should report
``CAUGHT``; a miss means a control has been lost since ``0.4.0rc13``, and
``tests/test_scripts.py`` checks that every fragment still matches the code it
aims at.

The set holds 110 probes. That sentence is held against ``PROBES`` by
``tests/test_scripts.py``, which is the only reason to write a number here at
all. Until ``0.7.0rc11`` this paragraph carried a running total instead, one
audit's addition at a time, and an audit of ``0.7.0rc10`` found it one too
high: the file said sixty-one and the set held sixty. Which increment is wrong
cannot be settled from this repository, because each of them is a claim about
a tree that is now a tag. A chain of additions nobody can recompute goes stale
without saying so, so the chain is gone and one checked number stands in its
place. ``docs/provenance.md`` carried a third number, older than both.

Which probes were added and why is worth keeping, and that is history rather
than arithmetic. The set began at eighteen with ``UnipotentStep``, whose three
source obligations are the first here that a constructed step cannot make
true, and grew with the homogenization, the compression and the symmetric
lift. The audits of milestone 0.6 added five between ``0.6.0rc1`` and
``0.6.0rc5``, and the audit of ``0.7.0rc1`` three for the descent.

The audit of ``0.7.0rc6`` added seven: one each for COL-7, BCW-12, LIN-6,
SEA-13, SEA-14, UNT-1 and the evaluation under DOM-4. Those are the promises
its four ring-semantics blockers turned out to rest on, and of the five files
they live in, ``search.py``, ``untargeted.py`` and ``polynomial_map.py`` had
no selector at all, which is why that audit could not run the selection this
project's rules ask for after a change like that one.

The audit of ``0.7.0rc7`` added the fallback the evaluation takes when a point
lies outside the domain and the unit test in ``conjugate``. Both were places
where the repair of the previous audit had itself gone wrong, which is the
argument for probing a repair and not only the thing repaired. The audits of
``0.7.0rc8`` and ``0.7.0rc9`` added three and four.

The audit of ``0.7.0rc10`` replaced the LIN-6 probe with one per clause of the
rewritten verifier, and added one for the candidate rule of FAC-1, two for
WID-2, one for WID-1 and two for FAC-2. The last two it found missing
altogether: it stripped the refusal of everything FAC-2 requires it to say and
the suite passed.

The audit of ``0.7.0rc11`` added two for MAP-4 and two for WID-1, whose single
probe covered ``Z/4Z`` directly and did not reach ``(Z/4Z)[T]``. One of the new
ones aims at the walk down the tower rather than at either refusal, because
that walk is what both readings of the clause rest on. One puts the replaced route
back, which is the mutation that matters: it does not raise on most blocks, it
returns a wrong determinant on some, and a control that only watched for an
exception would pass it. The other drops the sign of the size.

Milestone 0.7 added ten obligations and only three of them are here. HOM-11 and
HOM-12 cannot fail after HOM-1, which the contract page argues where it says
which of the HOM family can fail on supplied data, so a probe for either would
report a miss for a reason that is not a missing control. UNT-12 is an
enumerator and offers rather than certifies, as no UNT clause has a probe. What
is left is DSC-3 in both halves and DSC-4 in the half that is about arithmetic,
and those are exactly the clauses that page names as able to fail on data a
caller supplies.

Milestone 0.8 added seven for the witness. VAN-1 and VAN-2 can fail on
supplied data. VAN-3 and VAN-4 cannot on a lift that verifies, which by the
rule above would leave them out. They are in because their checks are module
functions with controls that call them on forms that are not lifts, so a
deletion there is noticed for the right reason. The probe on the loop bound of
VAN-3 is the one that matters most: depth one passes on a harmonic form whose
Hessian is not nilpotent, and only the control at depth two sees the
difference.

Milestone 0.9 added three, LIN-7, TRA-9 and UNI-13, and none of them is here.
Each cannot fail after the identity of its step, for the reason HOM-11 and
HOM-12 cannot. Their hypothesis is code, and its control is a test in
``tests/test_multi_affine.py`` that calls it directly.

Work package 3 of milestone 0.9 added nine for the certificate file. Every
clause of FMT-1 to FMT-9 can fail on a file from outside, so each refusal has a
control that names it. The nine are the refusals no other check would make in
their place: a repeated key, a boolean read as an integer, a rational not in
lowest terms, a domain that does not hold the map's, a lift the witness does
not name, and the comparison of the target a descent derives. Two aim at the
writer: a symbol with assumptions, and the order of the points of a collision,
which FMT-12 fixes. The ninth drops the cause a refusal carries, because FMT-10
asks for it.

Work package 4 added sixteen for the independent checker, ``kellermap_check``.
They carry the identifier of the checker's own clause, so that
``mutation_probe.py CHK`` selects them all, and ``what`` says which check is
edited. Four aim at the reader, CHK-3: the refusals the library's reader has a
probe for. Nine aim at the checks, CHK-4: the identity of a step, the
determinant and its Schur correction, the normalization, the carrier, the
compression, two on the points of a collision, and the depth. Three aim at the
verdict and the report, CHK-6 and CHK-7.

Work package 4.2 removed two, after the first whole sweep that could report a
miss. Each aimed at one half of a check whose other half refuses the same
domains, so no domain SymPy offers tells the halves apart. One is the field
test of WID-1: ``get_field`` answers a non-field only for ``Z/nZ`` with
composite ``n``, which has zero divisors, and the zero-divisor test refuses it.
The other is the zero-divisor half of the gate of the fold, FAC-1: where it
would let the fold run, the fold's own guard returns at its first division.
``docs/contracts.md`` says so at both clauses. The other seven misses of that
sweep have a control now.

Work package 5 added nine for the LaTeX view, TEX-1 to TEX-6. Two aim at
TEX-1, the one that matters: a view made with every check left out, and a
refusal that loses its identifier. The others leave out the witness, make the
view from the text as given, reverse the terms, load a package, render names
with SymPy, show the imaginary unit in italics, and leave text unescaped.

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

    python scripts/mutation_probe.py                # every probe
    python scripts/mutation_probe.py SYM            # one family
    python scripts/mutation_probe.py SYM-8 CHC-2    # named clauses
    python scripts/mutation_probe.py lift.py        # every probe on one file
    python scripts/mutation_probe.py --list SYM     # what that would run

A selection exists because a whole sweep re-runs the suite once per probe and
grows with both. It is for a change that touches one obligation, so that the
probes for it can be run beside the change rather than at the end of the
milestone. It does not replace a whole sweep, which is the only run that says
the set has no gap, and the output says so when a selection is running.

What a selection does not do is narrow the suite. Each probe still runs every
fast test, because a probe asks whether *anything* catches the edit; choosing
which tests may answer would turn a control that exists into a miss, and a
miss is the one thing this script is for.

The tests a probe runs against, and the control
-----------------------------------------------

Every fast test, with one exception: the tests marked ``probe_set``. They read
the fragments of this set from the tree, and under a probe one fragment has
been replaced, so they fail under every probe. ``SUITE`` leaves them out, and
nothing else. Until work package 4.1 of milestone 0.9 they were not left out,
and the suite failed under every probe for that reason alone. Every run since
those tests were written therefore reported every probe of the set as
``CAUGHT``, whatever the other tests did, and so did every selection.
``docs/errata.md`` records it.

Nothing in the runner could show that, because nothing in it could report a
miss it had to report. So every run now starts with ``CONTROL``, a probe that
changes nothing a test can see. It has to be ``MISSED``. If it is caught, some
test fails because a probe is applied and not because of what the probe
breaks, and the run stops before it reports anything.
"""

from __future__ import annotations

import argparse
import re
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


SUITE = "not slow and not probe_set"
"""The marker expression a probe runs the suite with.

The first half is the default of ``pyproject.toml``, and the second leaves out
the tests of the probe set. ``tests/test_scripts.py`` holds both halves.
"""

LAUNCHER = ("uv", "run")
"""What runs ``pytest`` in the working copy. A test gives a project of its own."""

CONTROL = Probe(
    "control",
    "a probe that changes nothing a test can see",
    "src/kellermap/__init__.py",
    "from .certificate import Certificate",
    "from .certificate import (Certificate)",
)
"""The probe that has to be missed, and that every run starts with.

The edit puts parentheses around one imported name. Like every probe it
removes its fragment from the tree, so it fails every test that the fragments
of the set are read by, and it changes nothing else.
"""

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
        "        if not agree(determinant, sp.Integer(1)):",
        "        if False:",
    ),
    Probe(
        "SYM-4",
        "the coefficient domain of the lift is a field",
        "src/kellermap/lift.py",
        "    if not domain.is_Field:\n        raise VerificationError(",
        "    if False:\n        raise VerificationError(",
    ),
    Probe(
        "SYM-4",
        "the coefficient domain of the lift has characteristic zero",
        "src/kellermap/lift.py",
        "    if domain.characteristic() != 0:\n        raise VerificationError(",
        "    if False:\n        raise VerificationError(",
    ),
    Probe(
        "SYM-5",
        "the coefficient domain of the target is compared",
        "src/kellermap/lift.py",
        "        if self._target.ring.domain != wanted:",
        "        if False:",
    ),
    Probe(
        "SYM-8",
        "an order the step cannot decide is refused",
        "src/kellermap/lift.py",
        "                if rank(left) != rank(right):",
        "                if True:",
    ),
    Probe(
        "SYM-8",
        "equality is asked before the order is",
        "src/kellermap/lift.py",
        "                if left == right:\n                    continue",
        "                if False:\n                    continue",
    ),
    Probe(
        "SYM-8",
        "the keywords a class was built with are read",
        "src/kellermap/lift.py",
        '            built = dict(getattr(kind, "_kwargs", {}) or {})',
        "            built = {}",
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
        "        first, second = sorted(points, key=cmp_to_key(structural))",
        "        first, second = points",
    ),
    Probe(
        "CHC-2",
        "the coefficient domain of the compression is a field",
        "src/kellermap/compression.py",
        "    if not domain.is_Field:",
        "    if False and not domain.is_Field:",
    ),
    Probe(
        "CHC-8",
        "the coefficient domain has characteristic zero",
        "src/kellermap/compression.py",
        "    elif domain.characteristic() != 0:",
        "    elif False:",
    ),
    Probe(
        "DSC-3",
        "the deleted component is triangular",
        "src/kellermap/descent.py",
        "        if tail.has(variable):",
        "        if False:",
    ),
    Probe(
        "DSC-3",
        "no surviving component mentions the deleted coordinate",
        "src/kellermap/descent.py",
        "            if sp.expand(component).has(variable):",
        "            if False:",
    ),
    Probe(
        "DSC-4",
        "the two changes are over the source's ring",
        "src/kellermap/descent.py",
        "            if automorphism.ring != self._source.ring:",
        "            if False:",
    ),
    Probe(
        "COL-7",
        "a collision is refused against positive characteristic",
        "src/kellermap/collision.py",
        "    if characteristic != 0:",
        "    if False:",
    ),
    Probe(
        "BCW-12",
        "two fresh slots of one name carry one value",
        "src/kellermap/bcw/step.py",
        "        if len({symbol.name for symbol in fresh}) != len(fresh) and (\n"
        "            values[0] != values[1]\n"
        "        ):",
        "        if False:",
    ),
    Probe(
        "LIN-6",
        "the linear part is invertible over the coefficient domain",
        "src/kellermap/reduction.py",
        "        if not is_unit(domain, determinant):",
        "        if False and is_unit(domain, determinant):",
    ),
    Probe(
        "LIN-6",
        "the transformation is the inverse of the linear part",
        "src/kellermap/reduction.py",
        "        if not _is_identity(declared * linear_part, domain):",
        "        if False and _is_identity(declared * linear_part, domain):",
    ),
    Probe(
        "SEA-13",
        "an exact pool match is compared in the ring of the reached map",
        "src/kellermap/search.py",
        "            and (available := converted[name]) is not None\n"
        "            and wanted in (available, -available)",
        "            and (available := converted[name]) is not None\n"
        "            and wanted in (available.as_expr(), -available.as_expr())",
    ),
    Probe(
        "SEA-14",
        "the forward enumerator asks for no shared generator",
        "src/kellermap/search.py",
        "                    candidate = _canonical(index, anchor, partner)",
        "                    candidate = _canonical(index, anchor, partner)\n"
        "                    candidate = Candidate(\n"
        "                        candidate.index,\n"
        "                        candidate.left,\n"
        "                        candidate.right,\n"
        "                        candidate.coefficient,\n"
        "                        shared=True,\n"
        "                    )",
    ),
    Probe(
        "UNT-1",
        "sharing is asked for only where the two slots agree",
        "src/kellermap/untargeted.py",
        "                shared=_agree_in_ring(source, left, right),\n"
        "            )\n"
        "        )\n"
        "\n"
        "    # UNT-6 after UNT-1",
        "                shared=True,\n"
        "            )\n"
        "        )\n"
        "\n"
        "    # UNT-6 after UNT-1",
    ),
    Probe(
        "MAP-1",
        "evaluation happens in the coefficient domain",
        "src/kellermap/polynomial_map.py",
        "        evaluated = self._evaluate_in_domain(args)",
        "        evaluated = None",
    ),
    Probe(
        "MAP-2",
        "a point outside the domain falls back over every domain",
        "src/kellermap/polynomial_map.py",
        "            except (\n"
        "                CoercionFailed,\n"
        "                NotImplementedError,\n"
        "                ValueError,",
        "            except (\n                CoercionFailed,",
    ),
    Probe(
        "CNJ-1",
        "a unit of the coefficient domain is admitted as a diagonal entry",
        "src/kellermap/search.py",
        "                domain.exquo(domain.one, value)",
        "                if entry not in (1, -1):\n"
        "                    raise ExactQuotientFailed(domain.one, value, domain)",
    ),
    Probe(
        "CNJ-1",
        "a non-unit is refused as a ValueError and not as a SymPy error",
        "src/kellermap/search.py",
        "                NotInvertible,\n                ZeroDivisionError,\n",
        "",
    ),
    Probe(
        "WID-1",
        "a widening onto zero divisors below is refused",
        "src/kellermap/polynomial_map.py",
        "    if has_zero_divisors(widened):\n        return None",
        "    if False:\n        return None",
    ),
    Probe(
        "WID-1",
        "the zero-divisor question reaches the ground domain",
        "src/kellermap/polynomial_map.py",
        "    ground = ground_domain(domain)\n\n    return bool(ground.is_FiniteField)",
        "    ground = domain\n\n    return bool(ground.is_FiniteField)",
    ),
    Probe(
        "WID-2",
        "the advice is withheld where the widening changes nothing",
        "src/kellermap/polynomial_map.py",
        '    if widened is None or widened == domain:\n        return ""',
        '    if widened is None:\n        return ""',
    ),
    Probe(
        "WID-2",
        "the advice is withheld where there is no widening",
        "src/kellermap/polynomial_map.py",
        '    if widened is None or widened == domain:\n        return ""',
        '    if widened == domain:\n        return ""',
    ),
    Probe(
        "MAP-4",
        "the determinant is taken without dividing",
        "src/kellermap/polynomial_map.py",
        "    corner = current[0][0]\n\n    return corner if size % 2 else -corner",
        "    from sympy.polys.matrices import DomainMatrix\n\n"
        "    return DomainMatrix.from_list(\n"
        "        [list(row) for row in block], block[0][0].ring.to_domain()\n"
        "    ).det()",
    ),
    Probe(
        "MAP-4",
        "the sign of the size is carried",
        "src/kellermap/polynomial_map.py",
        "    return corner if size % 2 else -corner",
        "    return corner",
    ),
    Probe(
        "FAC-2",
        "the refusal names the second reading",
        "src/kellermap/linear.py",
        '            "elimination did not find the row combination that shows'
        ' it: over "',
        '            ""',
    ),
    Probe(
        "FAC-2",
        "the refusal names the bound and the clause",
        "src/kellermap/linear.py",
        '            "a domain that is not a field the search is bounded. See FAC-2."',
        '            ""',
    ),
    Probe(
        "FAC-1",
        "the search tries its candidates and does not apply the first",
        "src/kellermap/linear.py",
        "            candidates = [domain.one, -domain.one]\n"
        "            quotient = _quotient(domain, entry, divisor)\n"
        "            if quotient is not None and quotient != domain.zero:\n"
        "                candidates.append(quotient)",
        "            candidates = [domain.one]",
    ),
    Probe(
        "FAC-1",
        "a column without a unit pivot is folded to one",
        "src/kellermap/linear.py",
        "        pivot = _fold_column(matrix, column, owned, operations)",
        "        pivot = None",
    ),
    Probe(
        "FAC-1",
        "a column without a unit pivot is searched for a combination",
        "src/kellermap/linear.py",
        "        pivot = _search_unit_pivot(matrix, column, owned, operations)",
        "        pivot = None",
    ),
    Probe(
        "MAP-3",
        "conjugation exponentiates instead of dividing per unit",
        "src/kellermap/search.py",
        "        if exponent:\n"
        "            value = value * reciprocal[index] ** exponent",
        "        for _ in range(exponent):\n"
        "            value = value * reciprocal[index]",
    ),
    Probe(
        "MAP-3",
        "the evaluator exponentiates instead of multiplying per unit",
        "src/kellermap/polynomial_map.py",
        "            if exponent:\n                term = term * value**exponent",
        "            for _ in range(exponent):\n                term = term * value",
    ),
    Probe(
        "VAN-1",
        "the witness does not verify its lift",
        "src/kellermap/vanishing.py",
        "            self.lift.verify()\n",
        "            pass\n",
    ),
    Probe(
        "VAN-1",
        "the witness accepts a lift of any degree",
        "src/kellermap/vanishing.py",
        "        if degree != 3:",
        "        if False:",
    ),
    Probe(
        "VAN-2",
        "the witness does not verify its collision",
        "src/kellermap/vanishing.py",
        "            self.collision.verify(self.lift.target)",
        "            pass",
    ),
    Probe(
        "VAN-3",
        "a depth outside one to n is accepted",
        "src/kellermap/vanishing.py",
        "        if not 1 <= self.depth <= variables:",
        "        if False:",
    ),
    Probe(
        "VAN-3",
        "a non-zero Delta^m(P^m) is accepted",
        "src/kellermap/vanishing.py",
        "        if value:",
        "        if False:",
    ),
    Probe(
        "VAN-3",
        "the hypothesis is checked at depth one only",
        "src/kellermap/vanishing.py",
        "    for m in range(1, depth + 1):",
        "    for m in range(1, 2):",
    ),
    Probe(
        "VAN-4",
        "a harmonic square is accepted",
        "src/kellermap/vanishing.py",
        "    if not laplacian(square):",
        "    if False:",
    ),
    Probe(
        "FMT-1",
        "a key twice in one object is read as the last",
        "src/kellermap/certificate.py",
        "            if key in found:",
        "            if False:",
    ),
    Probe(
        "FMT-1",
        "a boolean is read as an integer",
        "src/kellermap/certificate.py",
        "    if isinstance(value, bool) or not isinstance(value, int):",
        "    if not isinstance(value, int):",
    ),
    Probe(
        "FMT-6",
        "a rational not in lowest terms is read",
        "src/kellermap/certificate.py",
        "    if denominator and (q < 2 or math.gcd(p, q) != 1):",
        "    if False:",
    ),
    Probe(
        "FMT-7",
        "a symbol with assumptions is written by its name",
        "src/kellermap/certificate.py",
        "    if symbol != sp.Symbol(name):",
        "    if False:",
    ),
    Probe(
        "FMT-8",
        "a collision over a domain without its map's is read",
        "src/kellermap/certificate.py",
        "    if not _contains(descriptor, descriptors[position]):",
        "    if False:",
    ),
    Probe(
        "FMT-9",
        "a witness may name a step that is not a lift",
        "src/kellermap/certificate.py",
        "    if not 0 <= index < len(steps) or not isinstance("
        "steps[index], SymmetricLiftStep):",
        "    if not 0 <= index < len(steps):",
    ),
    Probe(
        "FMT-10",
        "a refusal of a constructor loses its cause",
        "src/kellermap/certificate.py",
        "        ) from refusal\n    except ValueError as refusal:",
        "        ) from None\n    except ValueError as refusal:",
    ),
    Probe(
        "FMT-12",
        "the points of a collision are written as they arrive",
        "src/kellermap/certificate.py",
        "    points = sorted((point(entry) for entry in collision.points), key=_text)",
        "    points = [point(entry) for entry in collision.points]",
    ),
    Probe(
        "DSC-1",
        "the target a descent derives is not compared with the file",
        "src/kellermap/certificate.py",
        "            if derived != maps[index + 1]:",
        "            if False:",
    ),
    Probe(
        "CHK-3",
        "the checker reads a key twice in one object as the last",
        "src/kellermap_check/_reading.py",
        "        if len(set(keys)) != len(keys):",
        "        if False:",
    ),
    Probe(
        "CHK-3",
        "the checker reads a boolean as an integer",
        "src/kellermap_check/_reading.py",
        "        if type(value) is not int:",
        "        if not isinstance(value, int):",
    ),
    Probe(
        "CHK-3",
        "the checker reads a rational not in lowest terms",
        "src/kellermap_check/_reading.py",
        "(q == 1 or math.gcd(p, q) != 1)",
        "(q == 1)",
    ),
    Probe(
        "CHK-3",
        "the checker reads a collision over a domain without its map's",
        "src/kellermap_check/_reading.py",
        "    if not domain.contains(maps[position].domain):",
        "    if False:",
    ),
    Probe(
        "CHK-4",
        "the checker compares no identity of a step",
        "src/kellermap_check/_checks.py",
        "            left == right,\n",
        "            True,\n",
    ),
    Probe(
        "CHK-4",
        "the checker takes every Jacobian determinant to be one",
        "src/kellermap_check/_checks.py",
        "        algebra.determinant_is_one(ring, components),",
        "        True,",
    ),
    Probe(
        "CHK-4",
        "the determinant of the checker leaves out the Schur correction",
        "src/kellermap_check/_algebra.py",
        "            - sum((jacobian[row][j] * solved[j][position] for j in kept), "
        "ring.zero)",
        "            - ring.zero",
    ),
    Probe(
        "CHK-4",
        "the checker does not compare the normalization with the linear part",
        "src/kellermap_check/_checks.py",
        "                identity[i][j] == (domain.one if i == j else domain.zero)",
        "                True",
    ),
    Probe(
        "CHK-4",
        "the checker accepts any carrier of a reused slot",
        "src/kellermap_check/_checks.py",
        "                    algebra.free_of(displaced[j], j),",
        "                    True,",
    ),
    Probe(
        "CHK-4",
        "the checker does not compare a compression with its source",
        "src/kellermap_check/_checks.py",
        '            "CHC-1", left == right, f"coordinate {i}',
        '            "CHC-1", True, f"coordinate {i}',
    ),
    Probe(
        "CHK-4",
        "the checker does not evaluate the points of a collision",
        "src/kellermap_check/_checks.py",
        "                value == entry.image,",
        "                True,",
    ),
    Probe(
        "CHK-4",
        "the checker accepts two equal points",
        "src/kellermap_check/_checks.py",
        "                    entry.points[first] != entry.points[second],",
        "                    True,",
    ),
    Probe(
        "CHK-4",
        "the checker accepts a depth out of range",
        "src/kellermap_check/_checks.py",
        "            1 <= depth <= len(target.names),",
        "            True,",
    ),
    Probe(
        "CHK-6",
        "a skipped check leaves the verdict VERIFIED",
        "src/kellermap_check/__init__.py",
        "        INCOMPLETE if ledger.skipped else VERIFIED,",
        "        VERIFIED,",
    ),
    Probe(
        "CHK-6",
        "a skip that names no check is ignored",
        "src/kellermap_check/__init__.py",
        "    if unknown:",
        "    if False:",
    ),
    Probe(
        "CHK-7",
        "the report does not name SYM-7",
        "src/kellermap_check/__init__.py",
        '        not_computed.append("SYM-7")',
        "        pass",
    ),
    Probe(
        "TEX-1",
        "the view is made with every check left out",
        "src/kellermap/latex.py",
        "        report = kellermap_check.check(text)",
        "        report = kellermap_check.check(text, kellermap_check.CHECKS)",
    ),
    Probe(
        "TEX-1",
        "a refusal of the checker loses its identifier",
        "src/kellermap/latex.py",
        "            refusal.obligation, refusal.message, location=refusal.location",
        '            "FMT-1", refusal.message, location=refusal.location',
    ),
    Probe(
        "TEX-2",
        "the witness is left out of the view",
        "src/kellermap/latex.py",
        "            self.witness(),",
        '            "",',
    ),
    Probe(
        "TEX-3",
        "the view is made from the text as it was given",
        "src/kellermap/latex.py",
        "    canonical = certificate.dumps()",
        "    canonical = text",
    ),
    Probe(
        "TEX-3",
        "terms stand in the reverse of the file's order",
        "src/kellermap/latex.py",
        "        for exponents, coefficient in terms:",
        "        for exponents, coefficient in reversed(terms):",
    ),
    Probe(
        "TEX-4",
        "the document loads a package",
        "src/kellermap/latex.py",
        '        "\\\\documentclass{article}\\n"',
        '        "\\\\documentclass{article}\\n\\\\usepackage{amsmath}\\n"',
    ),
    Probe(
        "TEX-5",
        "SymPy renders the names",
        "src/kellermap/latex.py",
        '    return "\\\\mathit{" + identifier.replace("_", "\\\\_") + "}"',
        "    return str(sp.latex(sp.Symbol(identifier)))",
    ),
    Probe(
        "TEX-5",
        "the imaginary unit is shown as an italic i",
        "src/kellermap/latex.py",
        '                imaginary_unit="ri",',
        '                imaginary_unit="i",',
    ),
    Probe(
        "TEX-6",
        "text from the report is not escaped",
        "src/kellermap/latex.py",
        '    return "".join(_TEXT_SPECIALS.get(character, character) '
        "for character in words)",
        "    return words",
    ),
)


def run_suite(root: Path, launcher: Sequence[str] = LAUNCHER) -> tuple[bool, str]:
    """Return whether the fast suite failed under ``root``, and the line saying so.

    The suite is the one ``SUITE`` names: the fast tests without the tests of
    the probe set.
    """
    finished = subprocess.run(  # noqa: S603
        [
            *launcher,
            "pytest",
            "-q",
            "-x",
            "--no-header",
            "-p",
            "no:cacheprovider",
            "-m",
            SUITE,
        ],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    # A collection error ends the run with "1 error in ..." and no count of
    # passed or failed tests, and that line is the summary then.
    summary = [
        line
        for line in finished.stdout.splitlines()
        if re.search(r"\b(passed|failed|errors?)\b", line)
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

    ``CONTROL`` runs first and is not counted. A run whose control is caught
    stops with ``SystemExit`` before the first probe.
    """
    missed = 0
    with tempfile.TemporaryDirectory() as scratch:
        copy = working_copy(Path(scratch))

        original = apply(CONTROL, copy)
        try:
            caught, summary = run(copy)
        finally:
            restore(CONTROL, copy, original)

        mark = "CAUGHT " if caught else "MISSED "
        print(f"{mark} {CONTROL.obligation:7} {CONTROL.what:46} {summary}")
        sys.stdout.flush()
        if caught:
            raise SystemExit(
                "The control was caught. A test fails because a probe is "
                "applied, and not because of what the probe breaks, so no "
                "result of this run would mean anything. Mark that test "
                "probe_set if it reads the fragments of the set, or give the "
                "control a fragment no test reads."
            )

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


def matches(probe: Probe, selector: str) -> bool:
    """Return whether one selector names one probe.

    Three ways, because three are the ways a change is described: the clause
    it touches (``SYM-8``), the family that clause belongs to (``SYM``), and
    the file it edits (``lift.py``, matched anywhere in the path).
    """
    return (
        probe.obligation == selector
        or probe.obligation.split("-")[0] == selector
        or selector in probe.path
    )


def select(probes: Sequence[Probe], selectors: Sequence[str]) -> tuple[Probe, ...]:
    """Return the probes the selectors name, in the order the set holds them.

    No selectors means all of them, so that the command without arguments is
    the whole sweep it has always been.

    A selector that names nothing stops the run. The alternative is worse than
    it looks: an empty selection prints "0 of 0 promises have no control",
    which is the sentence a clean sweep prints, so a typo would read as a pass.
    """
    if not selectors:
        return tuple(probes)

    keep: set[int] = set()
    for selector in selectors:
        found = {
            index for index, probe in enumerate(probes) if matches(probe, selector)
        }

        if not found:
            families = sorted({probe.obligation.split("-")[0] for probe in probes})
            raise SystemExit(
                f"No probe matches {selector!r}. The families are "
                f"{', '.join(families)}, and a path fragment such as 'lift.py' "
                "also selects."
            )

        keep |= found

    return tuple(probes[index] for index in sorted(keep))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Delete one check at a time and see whether a test notices."
    )
    parser.add_argument(
        "selector",
        nargs="*",
        help="an obligation, a family of obligations, or part of a path",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        dest="listing",
        help="print what would run, and run nothing",
    )
    arguments = parser.parse_args(argv)
    chosen = select(PROBES, arguments.selector)

    if arguments.listing:
        for probe in chosen:
            print(f"{probe.obligation:7} {probe.what:46} {probe.path}")

        return 0

    print(f"{len(chosen)} of {len(PROBES)} probes, run against a copy of the project.")
    print("The repository is not written to.")
    print("The control runs first and has to be missed.")

    if len(chosen) != len(PROBES):
        print("A selection. Only a whole sweep says the set has no gap.")

    print()
    missed = sweep(chosen)
    print(f"\n{missed} of {len(chosen)} promises have no control.")

    # No non-zero return value: a miss is a question and not a defect. Whoever
    # puts this script into a chain decides what number to expect.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
