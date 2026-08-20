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

from kellermap import PolynomialMap, untargeted_candidates  # noqa: E402
from kellermap.bcw import BCWStep  # noqa: E402
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


FIGURES = (2, 13, 12, 172, 14, 19, 86, 376, 365, 105)
"""Every number this script asserts, for the test that ties it to the page.

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
                    1,
                    candidate.coefficient,
                )
                step.verify()
                built += 1
                lowering += lowers_the_weight(source, step.target)
                shared += candidate.shares_one_generator

    print("UNT-1, the size of the space")
    check("smallest count above degree three", min(above), 2)
    check("largest count above degree three", max(above), 13)
    check("count at the normalized Alpoege map", offered[0], 12)

    print("\nUNT-2, empty at the reduction target")
    check("counts at maps of degree three", set(ends), {0})

    print("\nUNT-1 and UNT-3, the bridge to the certificate")
    check("candidates built and verified", built, 172)
    check("of those, lowering the measure", lowering, 172)
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

    print("\nEvery figure agrees with docs/contracts.md.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
