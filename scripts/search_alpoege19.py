"""Run the search for the step sequence of the published 19-dimensional map.

This script is *not* a second independent computation, and it does not belong
beside ``reconstruct_bcw17.py`` and ``reconstruct_alpoege15.py`` for that
reason. Those two render fixed data in plain SymPy so that the library has
something other than itself to agree with. This one drives the library. It is
a long-running job with a printed trail, not a gate, and it is deliberately
left out of ``make check``.

What it does:

* reads Alpoege's three-dimensional map and the published nineteen-dimensional
  one from the test modules that already hold them, rather than copying them;
* uses Alpoege's map unnormalized, because the published map's linear part is
  Alpoege's own, so the chain does not begin with ``LinearStep.normalize``;
* builds the value pool from the published carriers, with the value of ``w2``
  replaced by the one it was introduced with;
* searches with a doubling budget, printing what each round cost and how far
  it got;
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

    python scripts/search_alpoege19.py [start_budget] [max_budget] [spare]

``spare`` is the number of steps a chain may take that introduce no generator,
and it bounds the length of a chain: every other step consumes a name, so a
chain has at most ``len(pool) + spare`` steps. One is the arithmetic minimum
here, since the dimension grows by sixteen over seventeen steps. Two is the
library's default and doubles a branch there is no reason to need yet, so this
script asks for one unless told otherwise.

A first round below 68425 maps is wasted. The run of 8 August 2026 exhausted a
strictly smaller space at that count -- the search then stopped at the last
introduction, so no chain could *end* with a step that introduces nothing, and
this map needs at least one. The space searched now contains that one and
cannot be smaller. The episode is also why an exhausted space is reported
together with the rules that defined it.

The exit status is 0 if a chain was found, 2 if the space was exhausted
without one, and 1 if the budget ran out first. The three are different
outcomes and SEA-6 keeps them apart: only the second says anything about what
does not exist, and it says it about the space this search covers.
"""

from __future__ import annotations

import importlib.util
import sys
import time
from pathlib import Path
from types import ModuleType

import sympy as sp

from kellermap import PolynomialMap, Reduction, conjugate, over_field, search
from kellermap.bcw import Carried

ROOT = Path(__file__).resolve().parent.parent


def read(name: str) -> ModuleType:
    """Return a test module, so that fixed data is read and not copied.

    Alpoege's map and the published nineteen-dimensional one are already in the
    repository, with their provenance recorded beside them. A second copy here
    would add nothing but a way for the two to disagree.
    """
    path = ROOT / "tests" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"{name}_data", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot read fixed data from {path}.")

    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(ROOT))
    spec.loader.exec_module(module)

    return module


def setup() -> tuple[PolynomialMap, PolynomialMap, dict[sp.Symbol, sp.Expr]]:
    """Return the source, the published target, and the value pool."""
    fifteen, nineteen = read("test_alpoege15"), read("test_alpoege19")

    published = PolynomialMap(nineteen.VARIABLES, nineteen.COMPONENTS)
    carriers = nineteen.VARIABLES[3:]
    rename = dict(zip(fifteen.ALPOEGE_VARIABLES, nineteen.VARIABLES[:3], strict=True))
    source = over_field(
        PolynomialMap(
            nineteen.VARIABLES[:3],
            tuple(
                sp.expand(component.subs(rename))
                for component in fifteen.ALPOEGE_COMPONENTS
            ),
        )
    )

    pool = {
        carrier: sp.expand(published.components[3 + position] - carrier)
        for position, carrier in enumerate(carriers)
    }
    # The published component of w2 is the residue of a later step, not an
    # introduced value. See tests/test_alpoege19.py.
    pool[carriers[1]] = nineteen.W2_INTRODUCED

    return source, published, pool


def describe(
    reduction: Reduction,
    signs: tuple[int, ...],
    variables: tuple[sp.Symbol, ...],
) -> str:
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

    flipped = [str(v) for v, sign in zip(variables, signs, strict=True) if sign == -1]
    lines.append("")
    lines.append(f"# D flips: {flipped or 'nothing'}")

    return "\n".join(lines)


def main(start: int = 100_000, ceiling: int = 8_000_000, spare: int = 1) -> int:
    source, published, pool = setup()
    corrected = pool[published.variables[4]]

    print(f"source: dimension {source.dimension}, degree {source.degree()}")
    print(f"target: dimension {published.dimension}, degree {published.degree()}")
    print(f"pool:   {len(pool)} values, w2 corrected to {corrected}")
    print(f"spare:  {spare} step(s) may introduce no generator")
    print()

    budget = start
    outcome = None
    while budget <= ceiling:
        began = time.monotonic()
        outcome = search(source, published, pool, budget=budget, spare=spare)
        spent = time.monotonic() - began
        print(
            f"budget {budget:>9}: examined {outcome.examined:>9}, "
            f"deepest {outcome.deepest:>3}, "
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
            print(describe(outcome.reduction, outcome.signs, published.variables))
            return 0

        if outcome.exhausted:
            print()
            print("The space this search covers holds no chain. The rules that")
            print(f"defined it: spare={spare}; degrees do not rise; the dimension")
            print("does not pass the target's; anchors come from the pool; and")
            print("co-factors are parts of the division of the displacement.")
            print(f"The longest chain it reached was {outcome.deepest} steps.")
            print("That is not a statement that no chain exists; see SEA-6.")
            return 2

        budget *= 2

    print()
    print(f"No chain within {ceiling} maps. The budget ran out, so this says less")
    print("than an exhausted space would: the search did not finish looking.")
    if outcome is not None:
        print(f"The longest chain it reached was {outcome.deepest} steps.")

    return 1


if __name__ == "__main__":
    arguments = [int(value) for value in sys.argv[1:4]]
    raise SystemExit(main(*arguments))
