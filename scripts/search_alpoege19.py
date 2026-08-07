"""Run the search for the step sequence of the published 19-dimensional map.

This script is *not* a second independent computation, and it does not belong
beside ``reconstruct_bcw17.py`` and ``reconstruct_alpoege15.py`` for that
reason. Those two render fixed data in plain SymPy so that the library has
something other than itself to agree with. This one drives the library. It is
a long-running job with a printed trail, not a gate, and it is deliberately
left out of ``make check``.

What it does:

* builds Alpoege's three-dimensional map as the source, in the coordinates the
  published map uses -- the published map's linear part is Alpoege's own, so
  the chain starts at the unnormalized map and not at ``LinearStep.normalize``;
* builds the value pool from the published carriers, with the value of ``w2``
  replaced by the one it was introduced with;
* searches with a doubling budget, printing what each round cost;
* on success prints the chain step by step, together with the diagonal ``D``
  of SEA-5, in a form that can be read into ``tests/test_alpoege19.py``.

Why ``w2`` is replaced: its published component is the residue of a later step
rather than an introduced value, so the value that coordinate was introduced
with, ``x**3 * y``, is absent from the map. ``tests/test_alpoege19.py``
verifies that identity. Without it the chain is not merely unfound but
inexpressible, since a fresh coordinate needs a name and the only names on
offer are the published ones -- ``tests/test_alpoege15.py`` shows the same
effect on a chain whose answer is known.

Why the budget doubles rather than a callback reporting progress: a callback
would widen the public surface of ``kellermap.search`` for the benefit of one
script. Doubling costs a factor of two in wasted work and needs nothing from
the library. A round that reports the space exhausted stops the run, because
every later round would search the same space.

Run with::

    python scripts/search_alpoege19.py [start_budget] [max_budget]

The exit status is 0 if a chain was found, 2 if the space was exhausted
without one, and 1 if the budget ran out first. The three are different
outcomes and SEA-6 keeps them apart: only the second says anything about what
does not exist, and it says it about the space this search covers.
"""

from __future__ import annotations

import sys
import time

import sympy as sp

from kellermap import (
    PolynomialMap,
    Reduction,
    conjugate,
    over_field,
    search,
)
from kellermap.bcw import Carried

x, y, z = sp.symbols("x y z")
w = sp.symbols("w1:17")
VARIABLES = (x, y, z, *w)

# Alpoege's map, in the coordinates of the published one. The published map's
# linear part is this map's own, so no normalization comes first.
SOURCE_COMPONENTS = (
    x**3 * y**3 * z
    + 3 * x**2 * y**4
    + 3 * x**2 * y**2 * z
    + 7 * x * y**3
    + 3 * x * y * z
    + 4 * y**2
    + z,
    3 * x**3 * y**2 * z
    + 9 * x**2 * y**3
    + 6 * x**2 * y * z
    + 12 * x * y**2
    + 3 * x * z
    + y,
    -(x**3) * z - 3 * x**2 * y + 2 * x,
)

# The sixteen carrier values, read off the published map, with w2 corrected.
POOL_VALUES = {
    w[0]: y**2 * z,
    w[1]: x**3 * y,
    w[2]: x * y**2,
    w[3]: y * z,
    w[4]: x**2 * y,
    w[5]: w[0] * x,
    w[6]: y**2,
    w[7]: w[3] * x,
    w[8]: x * y,
    w[9]: w[1] * z,
    w[10]: w[2] * y,
    w[11]: w[5] * x,
    w[12]: x**2,
    w[13]: w[6] * y,
    w[14]: w[7] * y,
    w[15]: x * z,
}


def target() -> PolynomialMap:
    """Return the published map, read from the test module that records it."""
    import importlib.util
    from pathlib import Path

    path = Path(__file__).resolve().parent.parent / "tests" / "test_alpoege19.py"
    spec = importlib.util.spec_from_file_location("alpoege19_data", path)
    if spec is None or spec.loader is None:  # pragma: no cover - packaging
        raise RuntimeError(f"Cannot read the published map from {path}.")

    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(path.parent.parent))
    spec.loader.exec_module(module)

    return PolynomialMap(module.VARIABLES, module.COMPONENTS)


def describe(reduction: Reduction, signs: tuple[int, ...]) -> str:
    """Return the chain in a form that can be read into a test."""
    lines = ["STEPS = ("]
    for step in reduction.steps:
        slots = []
        for slot in (step.left, step.right):
            if isinstance(slot, Carried):
                slots.append(f'("carried", {slot.index})')
            else:
                slots.append(f'("fresh", {slot.polynomial})')
        lines.append(
            f"    ({step.index}, {slots[0]}, {slots[1]}, {step.filtration_level}),"
        )
    lines.append(")")

    flipped = [str(v) for v, sign in zip(VARIABLES, signs, strict=True) if sign == -1]
    lines.append("")
    lines.append(f"# D flips: {flipped or 'nothing'}")

    return "\n".join(lines)


def main(start: int = 500, ceiling: int = 2_000_000) -> int:
    published = target()
    source = over_field(PolynomialMap((x, y, z), SOURCE_COMPONENTS))

    print(f"source: dimension {source.dimension}, degree {source.degree()}")
    print(f"target: dimension {published.dimension}, degree {published.degree()}")
    print(f"pool:   {len(POOL_VALUES)} values, w2 corrected to {POOL_VALUES[w[1]]}")
    print()

    budget = start
    while budget <= ceiling:
        began = time.monotonic()
        outcome = search(source, published, POOL_VALUES, budget=budget)
        spent = time.monotonic() - began
        print(
            f"budget {budget:>9}: examined {outcome.examined:>9}, "
            f"exhausted {outcome.exhausted}, {spent:.0f}s"
        )
        sys.stdout.flush()

        if outcome.reduction is not None and outcome.signs is not None:
            print()
            print("A chain was found.")
            print(f"  steps      {len(outcome.reduction.steps)}")
            print(f"  dimensions {outcome.reduction.dimensions()}")
            print(f"  degrees    {outcome.reduction.degrees()}")
            outcome.reduction.verify()
            print("  verify()   passed")
            reached = outcome.reduction.target.reordered(published.variables)
            print(f"  endpoint   {conjugate(reached, outcome.signs) == published}")
            print()
            print(describe(outcome.reduction, outcome.signs))
            return 0

        if outcome.exhausted:
            print()
            print("The space this search covers holds no chain, under SEA-8, SEA-10")
            print("and SEA-12. That is not a statement that none exists; see SEA-6.")
            return 2

        budget *= 2

    print()
    print(f"No chain within {ceiling} maps. The budget ran out, so this says less")
    print("than an exhausted space would: the search did not finish looking.")

    return 1


if __name__ == "__main__":
    arguments = [int(value) for value in sys.argv[1:3]]
    raise SystemExit(main(*arguments))
