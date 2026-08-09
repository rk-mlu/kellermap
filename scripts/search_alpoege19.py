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

This script once had a second phase that searched for a chain to the map with
the ``m = 0`` step undone, on the assumption that the step came last. That
assumption is now against the evidence: peeling the published map from the back
puts the ``m = 0`` step four steps before the end. The phase is removed rather
than kept, because it cost a whole exhausted space -- hours -- for a hypothesis
the data does not support. It broke nothing while it was there: a chain found
under a wrong assumption is still checked against the published map itself.

The run has two phases. It peels the published map from the far end first,
because that direction needs neither the value pool nor the names, reaches
depth eleven against this map where the forward search stops at six, and
exhausts its spaces in minutes rather than hours. If the peel finds nothing,
the forward search follows.

Run with::

    python scripts/search_alpoege19.py [start_budget] [max_budget] [spare]

``spare`` is the number of steps a chain may take that introduce no generator,
and it bounds the length of a chain: every other step consumes a name, so a
chain has at most ``len(pool) + spare`` steps.

Two, and the derivation is worth writing down because the first version of this
paragraph said one and was wrong. Write ``a`` for the steps introducing two
generators, ``b`` for those introducing one and ``c`` for those introducing
none. Then ``2a + b = 16`` and the chain has ``S = a + b + c = 16 - a + c``
steps. Alpoege's map has no carriers -- measured, and true of its linear
normalization as well -- so a ``Carried`` slot has nothing to point at and the
first step must introduce two generators: ``a >= 1``. If the chain has the
seventeen steps its source describes, then ``c = a + 1 >= 2``.

So ``spare=1`` cannot find a seventeen-step chain at all, whatever the budget.
It can still find shorter ones, which is a different question and a fair one.
With ``spare=2`` the structure is pinned: ``a = 1``, ``b = 14``, ``c = 2`` --
exactly one step introducing two generators, and it is the first.

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

import sys
import time
from pathlib import Path

import sympy as sp

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import describe, flips, read, sanity  # noqa: E402

from kellermap import (  # noqa: E402
    PolynomialMap,
    Reduction,
    examples,
    over_field,
    peel,
    search,
)


def setup() -> tuple[PolynomialMap, PolynomialMap, dict[sp.Symbol, sp.Expr]]:
    """Return the source, the published target, and the value pool."""
    data = read("data")

    published = data.ALPOEGE19
    carriers = published.variables[3:]
    alpoege = examples.alpoege()
    rename = dict(zip(alpoege.variables, published.variables[:3], strict=True))
    source = over_field(
        PolynomialMap(
            published.variables[:3],
            tuple(
                sp.expand(component.subs(rename)) for component in alpoege.components
            ),
        )
    )

    pool = {
        carrier: sp.expand(published.components[3 + position] - carrier)
        for position, carrier in enumerate(carriers)
    }
    # The published component of w2 is the residue of a later step, not an
    # introduced value. See tests/test_alpoege19.py.
    pool[carriers[1]] = data.W2_INTRODUCED

    return source, published, pool


def report(
    label: str,
    source: PolynomialMap,
    target: PolynomialMap,
    pool: dict[sp.Symbol, sp.Expr],
    start: int,
    ceiling: int,
    spare: int,
) -> tuple[int, Reduction | None, tuple[int, ...] | None]:
    """Search with a doubling budget, printing what each round cost."""
    print(f"--- {label} ---")
    budget, outcome = start, None

    while budget <= ceiling:
        began = time.monotonic()
        outcome = search(source, target, pool, budget=budget, spare=spare)
        spent = time.monotonic() - began
        print(
            f"budget {budget:>9}: examined {outcome.examined:>9}, "
            f"deepest {outcome.deepest:>3}, "
            f"exhausted {outcome.exhausted}, {spent:.0f}s"
        )
        sys.stdout.flush()

        if outcome.reduction is not None and outcome.signs is not None:
            return 0, outcome.reduction, outcome.signs

        if outcome.exhausted:
            print("The space this search covers holds no chain. The rules that")
            print(f"defined it: spare={spare}; degrees do not rise; the dimension")
            print("does not pass the target's; anchors come from the pool; and")
            print("co-factors are parts of the division of the displacement.")
            print(f"The longest chain it reached was {outcome.deepest} steps.")
            print("That is not a statement that no chain exists; see SEA-6.")
            return 2, None, None

        budget *= 2

    print(f"No chain within {ceiling} maps. The budget ran out, so this says less")
    print("than an exhausted space would: the search did not finish looking.")
    if outcome is not None:
        print(f"The longest chain it reached was {outcome.deepest} steps.")

    return 1, None, None


def unpicking(
    source: PolynomialMap,
    target: PolynomialMap,
    start: int,
    ceiling: int,
    spare: int,
) -> tuple[int, Reduction | None, tuple[sp.Expr, ...] | None]:
    """Peel with a doubling budget, printing what each round cost."""
    print("--- peeling the published map from the far end ---")
    budget, outcome = start, None

    while budget <= ceiling:
        began = time.monotonic()
        outcome = peel(source, target, budget=budget, spare=spare)
        spent = time.monotonic() - began
        print(
            f"budget {budget:>9}: examined {outcome.examined:>9}, "
            f"deepest {outcome.deepest:>3}, "
            f"exhausted {outcome.exhausted}, {spent:.0f}s"
        )
        sys.stdout.flush()

        if outcome.reduction is not None and outcome.signs is not None:
            return 0, outcome.reduction, outcome.signs

        if outcome.exhausted:
            print("The space this peel covers holds no chain. The rules that")
            print(f"defined it: spare={spare}; a coordinate is peeled only where")
            print("it occurs in exactly two components; the constant is the one")
            print("that makes it vanish.")
            print(f"The longest chain it reached was {outcome.deepest} steps.")
            print("That is not a statement that no chain exists; see REV-7.")
            return 2, None, None

        budget *= 2

    print(f"No chain within {ceiling} maps. The budget ran out, so this says less")
    print("than an exhausted space would: the peel did not finish looking.")
    if outcome is not None:
        print(f"The longest chain it reached was {outcome.deepest} steps.")

    return 1, None, None


def main(start: int = 100_000, ceiling: int = 8_000_000, spare: int = 2) -> int:
    source, published, pool = setup()
    corrected = pool[published.variables[4]]

    print(f"source: dimension {source.dimension}, degree {source.degree()}")
    print(f"target: dimension {published.dimension}, degree {published.degree()}")
    print(f"pool:   {len(pool)} values, w2 corrected to {corrected}")
    print(f"spare:  {spare} step(s) may introduce no generator")
    print()

    # Peeling first. It needs neither the pool nor the names, it reaches depth
    # eleven against this map where the forward search stops at six, and its
    # spaces are exhausted in minutes rather than hours.
    status, chain, signs = unpicking(source, published, start, ceiling, spare)
    if chain is None:
        print()
        status, chain, signs = report(
            "the forward search", source, published, pool, start, ceiling, spare
        )

    if chain is None or signs is None:
        return status

    print()
    print("A chain was found.")
    print(f"  steps      {len(chain.steps)}")
    print(f"  dimensions {chain.dimensions()}")
    print(f"  degrees    {chain.degrees()}")
    matched = sanity(chain, signs, published)
    print("  verify()   passed")
    print(f"  endpoint   {matched}")
    print(f"  D flips    {[str(v) for v in flips(signs, published)] or 'nothing'}")
    if not matched:
        print("  The endpoint does not match the published map. Nothing is claimed.")
        return 2
    print()
    print(describe(chain, signs, published))

    return 0


if __name__ == "__main__":
    arguments = [int(value) for value in sys.argv[1:4]]
    raise SystemExit(main(*arguments))
