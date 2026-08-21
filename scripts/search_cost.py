"""Measure what a search spends, per step and in total.

Work package 10 of milestone 0.5. It produces numbers and a way of reproducing
them, like ``scripts/mutation_probe.py``. It is not a gate: nothing here is
asserted, because nothing here is a promise. It answers a question, and the
question is where the cost of an untargeted search goes.

What is measured, for every step of every chain this repository can build:

* the dimension, and how much of it the step buys;
* the number of terms, and how much of it the step adds;
* the measure of UNT-3, and how much of it the step removes;
* how many terms each of the two factors has.

Run it with no arguments for every chain. The untargeted chain over Gao's map
takes about forty seconds and is left out unless ``--all`` is given.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import sympy as sp

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import importlib.util  # noqa: E402

from kellermap import (  # noqa: E402
    LinearStep,
    PolynomialMap,
    Reduction,
    examples,
    over_field,
    reduce_to_degree3,
)
from kellermap.bcw import BCWStep  # noqa: E402
from kellermap.untargeted import remaining_weight  # noqa: E402


def _load(name: str) -> Any:
    """Load a test module by path, as ``scripts/untargeted_space.py`` does."""
    path = ROOT / "tests" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"cost_{name}", path)
    if spec is None or spec.loader is None:  # pragma: no cover - the path exists
        raise SystemExit(f"{path} cannot be loaded.")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    return module


def terms(source: PolynomialMap) -> int:
    """Return how many monomials the whole map carries."""
    return sum(
        len(sp.Poly(component, *source.variables).terms())
        for component in source.components
    )


def factor_terms(step: BCWStep) -> tuple[int, int]:
    """Return how many terms each of the two factors has."""
    return (
        len(sp.Add.make_args(sp.expand(step.P))),
        len(sp.Add.make_args(sp.expand(step.Q))),
    )


def report(label: str, chain: Reduction) -> None:
    """Print the per-step table for one chain."""
    print(f"\n{label}: {len(chain.steps)} steps")
    print("    i  dim  deg  terms     phi   bought  +terms   -phi   P   Q")

    maps = [step.source for step in chain.steps] + [chain.target]
    for index, source in enumerate(maps):
        row = f"  {index:3}  {source.dimension:3}  {source.degree():3}"
        row += f"  {terms(source):5}  {remaining_weight(source):6}"
        if index:
            before = maps[index - 1]
            step = chain.steps[index - 1]
            row += f"   {source.dimension - before.dimension:+5}"
            row += f"  {terms(source) - terms(before):+6}"
            row += f"  {remaining_weight(before) - remaining_weight(source):5}"
            if isinstance(step, BCWStep):
                left, right = factor_terms(step)
                row += f"  {left:2}  {right:2}"
        print(row)


def law(label: str, chain: Reduction) -> None:
    """Report how often ``terms`` grew by anything but ``2 + 2m``.

    A step of Proposition (3.1) removes the one monomial it acts on and puts
    three in its place, and each fresh coordinate brings a component of two
    terms. That is ``2 + 2m`` exactly when both factors are monomials and
    nothing else cancels.

    Two things break it, and the measurement separates them. A factor with
    several terms puts more than three in place: that is the five steps of
    ``bcw17`` and the five of ``alpoege15``. And a new term can cancel one the
    map already had: ``alpoege19`` breaks the law once with every factor a
    monomial, which is the other cause and the smaller one.
    """
    off = 0
    for step in chain.steps:
        if not isinstance(step, BCWStep):
            continue
        grew = terms(step.target) - terms(step.source)
        if grew != 2 + 2 * step.m:
            off += 1
    print(f"  {label}: {off} steps where terms grew by anything but 2 + 2m")


def chains(everything: bool) -> list[tuple[str, Reduction]]:
    """Return the chains to measure, hand-computed first."""
    seventeen = _load("test_bcw17")
    fifteen = _load("test_alpoege15")
    nineteen = _load("test_alpoege19")

    def fixture(module: Any, name: str, *arguments: object) -> Any:
        return getattr(module, name).__wrapped__(*arguments)

    alpoege = fixture(seventeen, "alpoege")
    normalization = fixture(seventeen, "normalization", alpoege)
    bcw17 = fixture(seventeen, "bcw17") if hasattr(seventeen, "bcw17") else None

    built: list[tuple[str, Reduction]] = [
        (
            "bcw17, by hand",
            fixture(seventeen, "reduction", alpoege, normalization, bcw17),
        ),
        (
            "alpoege15, by hand",
            fixture(fifteen, "reduction", fixture(fifteen, "alpoege")),
        ),
        ("alpoege19, by hand", nineteen.build()),
    ]

    normalized = LinearStep.normalize(over_field(examples.alpoege())).target
    found = reduce_to_degree3(normalized, budget=2000).reduction
    if found is not None:
        built.append(("alpoege, found without a target", found))

    if everything:
        quartic = LinearStep.normalize(over_field(examples.gao_quartic())).target
        slow = reduce_to_degree3(quartic, budget=3000).reduction
        if slow is not None:
            built.append(("gao_quartic, found without a target", slow))

    return built


def main() -> int:
    measured = chains("--all" in sys.argv)

    for label, chain in measured:
        report(label, chain)

    print("\nTerm growth against dimension bought")
    for label, chain in measured:
        law(label, chain)

    print("\nFactors with more than one term")
    for label, chain in measured:
        several = sum(
            1
            for step in chain.steps
            if isinstance(step, BCWStep) and max(factor_terms(step)) > 1
        )
        total = sum(1 for step in chain.steps if isinstance(step, BCWStep))
        print(f"  {label}: {several} of {total} steps")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
