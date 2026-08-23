"""Recompute the measurements the UNT obligations rest on.

`docs/contracts.md` states four obligations about an untargeted enumerator, and
every number in that section came from a measurement. This recomputes them, so
that a reader who does not trust a number on a page can run one command instead
of rebuilding the measurement.

It is a gate and not a report. Every figure below is recomputed and asserted,
and a disagreement stops the run with both numbers side by side.

What the figures are asserted against is the copy held here, not the page
itself. Parsing them out of prose is what ``tests/test_documentation.py`` does
for obligation ranges, and it went wrong twice there, so this does not try.
The two copies are held together from the other side:
``test_the_untargeted_figures_appear_on_the_contract_page`` requires every
number this script checks to occur in that section, so editing one and not the
other fails.

What is checked:

* the size of the space, and that it does not grow with the dimension;
* that it is empty at degree three, which is the stopping rule of UNT-2;
* that every candidate offered builds, verifies and lowers the measure;
* that the measure falls for every offered step that introduces a generator,
  which is the proved half of UNT-3;
* that it does not always fall for a step that introduces none, which is why
  the other half is a rule this project states rather than a theorem.

The maps come from the test modules that build the two long chains, because
those chains are the evidence and rebuilding them here would compare this
script with itself.
"""

from __future__ import annotations

import importlib.util
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import sympy as sp

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from kellermap import (  # noqa: E402
    LinearStep,
    PolynomialMap,
    examples,
    over_field,
    untargeted_candidates,
)
from kellermap.bcw import BCWStep  # noqa: E402
from kellermap.context import ReductionContext  # noqa: E402
from kellermap.peeling import moves, undo  # noqa: E402
from kellermap.reduction import Reduction  # noqa: E402
from kellermap.untargeted import lowers_the_weight, remaining_weight  # noqa: E402


def _load(name: str) -> Any:
    """Load a test module by path, the way ``scripts/_common.py`` loads data.

    By path and not by import. ``mypy --strict`` follows a normal import, and
    the test modules are not written to pass a strict check; pulling them into
    this gate would make it report on files it is not about.
    """
    path = ROOT / "tests" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"untargeted_{name}", path)
    if spec is None or spec.loader is None:  # pragma: no cover - the path exists
        raise SystemExit(f"{path} cannot be loaded.")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    return module


def chains() -> dict[str, Reduction]:
    """Return the two long chains, built by the modules that own them."""
    seventeen = _load("test_bcw17")
    nineteen = _load("test_alpoege19")

    def fixture(module: Any, name: str, *arguments: object) -> Any:
        # The chains are pytest fixtures, so the function behind the decorator
        # is what builds them. Reaching for it keeps this script and the tests
        # on one construction instead of two that could drift apart.
        return getattr(module, name).__wrapped__(*arguments)

    alpoege = fixture(seventeen, "alpoege")
    normalization = fixture(seventeen, "normalization", alpoege)
    bcw17 = fixture(seventeen, "bcw17") if hasattr(seventeen, "bcw17") else None
    built: Reduction = fixture(seventeen, "reduction", alpoege, normalization, bcw17)

    return {"bcw17": built, "alpoege19": nineteen.build()}


def maps_of(chain: Reduction) -> Iterator[PolynomialMap]:
    """Yield every map the chain passes through, source first."""
    for step in chain.steps:
        yield step.source
    yield chain.target


FIGURES = (2, 22, 272, 14, 19, 86, 376, 365, 105, 21, 20, 7, 13, 8, 29, 39)
"""Every number this script asserts, for the test that ties it to the page.

The last seven are the table of UNT-10: steps and dimension for the five orders
on Alpoege's map, and the two Gao figures the slow test carries.

``105`` is the sum of the moves introducing one or two generators, which the
page states as one figure and this script checks as two.
"""


def check(label: str, measured: object, claimed: object) -> None:
    """Compare one recomputed figure with the value the contract page states."""
    mark = "ok " if measured == claimed else "BAD"
    print(f"  [{mark}] {label}: {measured} (page says {claimed})")
    if measured != claimed:
        raise SystemExit(
            f"{label}: measured {measured}, and docs/contracts.md says {claimed}."
        )


ORDERS: dict[str, Any] = {
    "the order the enumerator happened to fix": lambda removed, bought: 0,
    "largest removal": lambda removed, bought: -removed,
    "removal per coordinate bought": lambda removed, bought: -removed / (bought + 1),
    "fewest coordinates, then removal": lambda removed, bought: (bought, -removed),
    "largest removal, then fewest coordinates": lambda removed, bought: (
        -removed,
        bought,
    ),
}
"""The five orders UNT-10 was measured against.

They are built here and not in the library, because four of them are not what
the library does and an unused ordering in ``kellermap.untargeted`` would be a
branch nothing takes. What the library ships is the last one.
"""

ALPOEGE_ORDERS = {
    "the order the enumerator happened to fix": (21, 20),
    "largest removal": (7, 14),
    "removal per coordinate bought": (8, 13),
    "fewest coordinates, then removal": (8, 13),
    "largest removal, then fewest coordinates": (7, 13),
}
"""Steps and dimension each order reaches on the normalized Alpoege map.

The table of UNT-10. Gao's map is measured too and is not here: at twenty
seconds a run it belongs behind the slow marker, and
``tests/test_untargeted.py`` carries it.
"""


def walk_in_order(source: PolynomialMap, key: Any, budget: int = 3000) -> Any:
    """Return the chain a depth-first walk finds under one order.

    The same walk ``reduce_to_degree3`` performs, with the order as a
    parameter. Kept here rather than made a parameter of the library, so that
    the four orders the library does not use exist only where they are
    measured.
    """
    naming = ReductionContext()
    remaining = [budget]

    def go(current: PolynomialMap, steps: tuple[BCWStep, ...]) -> Any:
        if current.degree() <= 3:
            return Reduction(steps) if steps else None
        if remaining[0] <= 0:
            return None

        built = []
        before = remaining_weight(current)
        for candidate in untargeted_candidates(current):
            names = naming.variables(current.ring, candidate.m)
            step = BCWStep.build(
                current,
                candidate.index,
                *candidate.factors(names),
                candidate.filtration_level(current),
                candidate.coefficient,
            )
            removed = before - remaining_weight(step.target)
            if removed <= 0:
                continue
            bought = step.target.dimension - current.dimension
            built.append((key(removed, bought), step))

        for _, step in sorted(built, key=lambda pair: pair[0]):
            if remaining[0] <= 0:
                return None
            remaining[0] -= 1
            found = go(step.target, (*steps, step))
            if found is not None:
                return found

        return None

    return go(source, ())


def main() -> int:
    walked = list(chains().items())

    offered: list[int] = []
    above: list[int] = []
    built = lowering = shared = 0
    ends: list[int] = []

    for _, chain in walked:
        for source in maps_of(chain):
            candidates = untargeted_candidates(source)
            offered.append(len(candidates))
            if source.degree() > 3:
                above.append(len(candidates))
            else:
                ends.append(len(candidates))
            for candidate in candidates:
                names = sp.symbols("untargeted_0 untargeted_1")
                step = BCWStep.build(
                    source,
                    candidate.index,
                    *candidate.factors(names),
                    candidate.filtration_level(source),
                    candidate.coefficient,
                )
                step.verify()
                built += 1
                lowering += lowers_the_weight(source, step.target)
                shared += candidate.shares_one_generator

    print("UNT-1, the size of the space")
    check("smallest count above degree three", min(above), 2)
    check("largest count above degree three", max(above), 22)
    check("count at the normalized Alpoege map", offered[0], 22)

    print("\nUNT-2, empty at the reduction target")
    check("counts at maps of degree three", set(ends), {0})

    print("\nUNT-1 and UNT-3, the bridge to the certificate")
    check("candidates built and verified", built, 272)
    check("of those, lowering the measure", lowering, 272)
    check("of those, sharing one generator", shared, 14)

    print("\nUNT-3, the two halves")
    introduced = {0: [0, 0], 1: [0, 0], 2: [0, 0]}
    for _, chain in walked:
        for chain_step in chain.steps:
            if not isinstance(chain_step, BCWStep):
                continue
            current = chain_step.target
            for move in moves(current, 3, 2):
                earlier = undo(current, move)
                if earlier is None:
                    continue
                seen = introduced[len(move.dropped)]
                seen[0] += 1
                seen[1] += remaining_weight(earlier) > remaining_weight(current)

    check("moves introducing two generators", introduced[2][0], 19)
    check("of those, lowering the measure", introduced[2][1], 19)
    check("moves introducing one generator", introduced[1][0], 86)
    check("of those, lowering the measure", introduced[1][1], 86)
    check("moves introducing none", introduced[0][0], 376)
    check("of those, lowering the measure", introduced[0][1], 365)

    print("\nUNT-10, the order")
    source = LinearStep.normalize(over_field(examples.alpoege())).target
    for label, key in ORDERS.items():
        chain = walk_in_order(source, key)
        if chain is None:
            raise SystemExit(f"{label}: no chain, and the page records one.")
        chain.verify()
        check(
            label,
            (len(chain.steps), chain.target.dimension),
            ALPOEGE_ORDERS[label],
        )

    print("\nEvery figure agrees with docs/contracts.md.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
