"""Search for a step sequence of the fifteen-dimensional map.

The same job as ``search_alpoege19.py``, on the map whose answer is known. It
exists to be experimented with: a space here is exhausted in minutes rather
than hours, so a rule can be measured before it costs an evening on the
nineteen-dimensional map.

Not a gate and not a second independent computation. It drives the library, as
``search_alpoege19.py`` does, and for the same reason it is left out of
``make check``. The fixed data is read from the test module that holds it
rather than copied.

Run with::

    python scripts/search_alpoege15.py [budget] [spare] [rewrites] [complete]

``complete`` is 0 or 1 and decides what the pool holds:

* ``0`` -- the values the published map carries, and nothing else. Step seven of
  the recorded chain rewrites component 10, so the value that coordinate was
  introduced with is absent. With ``rewrites`` at zero the chain is then not
  merely unfound but inexpressible; with ``rewrites`` at one the search may
  give that coordinate a free name and reach the map anyway.
* ``1`` -- the same values with the missing one supplied from the recorded
  chain. This is the analogue of correcting ``w2`` for the
  nineteen-dimensional map, and it is what makes the recovery cheap.

The interesting comparison is therefore ``complete=1, rewrites=0`` against
``complete=0, rewrites=1``: the first knows the missing value, the second has
to find its way without it. What the second costs here is the best estimate
available for what it will cost there.

The exit status is 0 if a chain was found, 2 if the space was exhausted
without one, and 1 if the budget ran out.
"""

from __future__ import annotations

import importlib.util
import sys
import time
from pathlib import Path
from types import ModuleType

import sympy as sp

from kellermap import LinearStep, PolynomialMap, conjugate, over_field, search

ROOT = Path(__file__).resolve().parent.parent


def read(name: str) -> ModuleType:
    """Return a test module, so that fixed data is read and not copied."""
    path = ROOT / "tests" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"{name}_data", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot read fixed data from {path}.")

    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(ROOT))
    spec.loader.exec_module(module)

    return module


def setup(
    complete: bool,
) -> tuple[PolynomialMap, PolynomialMap, dict[sp.Symbol, sp.Expr]]:
    """Return the source, the published target, and the value pool.

    The chain starts at the linear normalization of Alpoege's map, which is
    where the recorded one starts. That differs from the nineteen-dimensional
    case, whose published linear part is Alpoege's own.
    """
    data = read("test_alpoege15")

    target = PolynomialMap(data.X, data.COMPONENTS)
    source = LinearStep.normalize(
        over_field(PolynomialMap(data.ALPOEGE_VARIABLES, data.ALPOEGE_COMPONENTS))
    ).target

    pool = {
        data.X[index]: sp.expand(data.COMPONENTS[index] - data.X[index])
        for index in target.carrier_indices
    }
    if complete:
        # The value coordinate 10 was introduced with, before step seven of the
        # recorded chain rewrote its component.
        pool[data.X[10]] = sp.expand(data.STEPS[3][2][1])

    return source, target, pool


def main(
    budget: int = 20_000,
    spare: int = 1,
    rewrites: int = 0,
    complete: int = 1,
) -> int:
    source, target, pool = setup(bool(complete))

    print(f"source:   dimension {source.dimension}, degree {source.degree()}")
    print(f"target:   dimension {target.dimension}, degree {target.degree()}")
    print(f"pool:     {len(pool)} values, complete={bool(complete)}")
    print(f"spare:    {spare}   rewrites: {rewrites}   budget: {budget}")
    print()

    began = time.monotonic()
    outcome = search(
        source, target, pool, budget=budget, spare=spare, rewrites=rewrites
    )
    spent = time.monotonic() - began
    print(
        f"examined {outcome.examined}, deepest {outcome.deepest}, "
        f"exhausted {outcome.exhausted}, {spent:.0f}s"
    )

    if outcome.reduction is None or outcome.signs is None:
        print()
        if outcome.exhausted:
            print("The space this search covers holds no chain. The rules that")
            print(f"defined it: spare={spare}; rewrites={rewrites}; degrees do not")
            print("rise; the dimension does not pass the target's; anchors come")
            print("from the pool; co-factors are parts of a division.")
            print("That is not a statement that no chain exists; see SEA-6.")
            return 2
        print("The budget ran out, so this says less than an exhausted space")
        print("would: the search did not finish looking.")
        return 1

    outcome.reduction.verify()
    reached = outcome.reduction.target.reordered(target.variables)
    print()
    print("A chain was found.")
    print(f"  steps      {len(outcome.reduction.steps)}")
    print(f"  dimensions {outcome.reduction.dimensions()}")
    print(f"  degrees    {outcome.reduction.degrees()}")
    print("  verify()   passed")
    print(f"  endpoint   {conjugate(reached, outcome.signs) == target}")
    flipped = [
        str(variable)
        for variable, sign in zip(target.variables, outcome.signs, strict=True)
        if sign == -1
    ]
    print(f"  D flips    {flipped or 'nothing'}")

    return 0


if __name__ == "__main__":
    arguments = [int(value) for value in sys.argv[1:5]]
    raise SystemExit(main(*arguments))
