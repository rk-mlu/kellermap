"""Measure how far the bounded pivot search of FAC-1 reaches.

FAC-2 says the search is incomplete and that the bound is measured rather
than argued. The figure behind it stood in a docstring and on the contract
page and was produced by a computation nobody could rerun from this
repository, which is what an audit of ``0.7.0rc10`` and the change that
followed it made worth fixing.

What is measured, cheapest first, so that a run cut short still reports
something:

* the two ``ZZ[T]`` matrices audits have supplied, and the two readings of
  the boundary a matrix of integers over ``ZZ[T]`` shows;
* every invertible ``2x2`` matrix over ``Z/4``, ``Z/6``, ``Z/8``, ``Z/9``,
  ``Z/10`` and ``Z/12``;
* random invertible ``3x3`` matrices over ``Z/6Z``, as many as the budget
  allows.

Every success is checked and not counted: the factorization has to
reproduce the matrix it was asked for, or a search that returned nonsense
would be recorded as a success. A refusal is counted and named, because
FAC-2 permits it.

Usage: ``python scripts/measure_pivot_search.py [--budget SECONDS]``. The
budget is spent on the random part, which is the only one that scales; the
exhaustive parts run to their end or not at all. The script prints the time
each part took, or the budget it stopped at.
"""

from __future__ import annotations

import argparse
import random
import sys
import time
from itertools import product
from pathlib import Path
from typing import Any

import sympy as sp

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from kellermap import LinearAutomorphism, PolynomialMap  # noqa: E402

PARAMETER = sp.Symbol("T")

MODULI = (4, 6, 8, 9, 10, 12)

DEFAULT_BUDGET = 120.0


def reproduces(ring: Any, given: sp.Matrix) -> bool:
    """Return whether ``factorize`` answers with a factorization of ``given``.

    The check and not the count. A search that returned a factorization of
    some other matrix would otherwise be recorded as a success, and the
    measurement would say the opposite of what it is for.

    Entry by entry through the domain, and not as SymPy integers. ``Z/nZ``
    holds its elements symmetrically, so ``3`` over ``Z/4Z`` comes back as
    ``-1``: the first version of this script compared the two as integers and
    reported 12036 of 13296 matrices refused, which the suite contradicted on
    the spot for two of the moduli.
    """
    domain = ring.domain
    factored = LinearAutomorphism.factorize(ring, given)
    rebuilt = sp.Matrix(factored.matrix(ring))

    return all(
        domain.from_sympy(rebuilt[row, column]) == domain.from_sympy(given[row, column])
        for row in range(given.rows)
        for column in range(given.cols)
    )


def reached(ring: Any, given: sp.Matrix) -> bool:
    """Return whether the search reached a unit pivot, or refused as FAC-2 allows."""
    try:
        return reproduces(ring, given)
    except ValueError:
        return False


def determines(ring: Any, given: sp.Matrix) -> bool:
    """Return whether the map with this linear part has the determinant it should.

    MAP-4, asked of the same matrices. This part is here because an audit of
    ``0.7.0rc11`` found a determinant that raised over exactly these rings
    while ``factorize`` was fine with them, and this script could not see it:
    it called ``factorize`` and nothing else, and its exhaustive part is
    two-by-two, where the determinant is ``ad - bc`` and divides nothing.
    """
    size = given.shape[0]
    names = ",".join(f"x{index}" for index in range(size))
    carrier = sp.ring(names, ring.domain)[0]
    components = tuple(
        sum(
            (
                carrier.domain.from_sympy(given[row, column]) * carrier.gens[column]
                for column in range(size)
            ),
            carrier.zero,
        )
        for row in range(size)
    )
    determinant = PolynomialMap.from_ring(carrier, components).determinant()
    expected = carrier.domain.to_sympy(
        carrier.domain.from_sympy(sp.Integer(given.det()))
    )

    return bool(sp.simplify(determinant - expected) == 0)


def parameter_cases() -> list[tuple[str, sp.Matrix, bool]]:
    """Return the ``ZZ[T]`` matrices, with what each is expected to show."""
    return [
        (
            "[[T, T+1], [T-1, T]], the matrix of the 0.7.0rc9 audit",
            sp.Matrix([[PARAMETER, PARAMETER + 1], [PARAMETER - 1, PARAMETER]]),
            True,
        ),
        (
            "[[T, -1], [2T+1, -2]], the matrix of the 0.7.0rc10 audit",
            sp.Matrix([[PARAMETER, -1], [2 * PARAMETER + 1, -2]]),
            True,
        ),
        (
            "the same matrix with its rows exchanged",
            sp.Matrix([[2 * PARAMETER + 1, -2], [PARAMETER, -1]]),
            True,
        ),
        (
            "[[7, 17], [2, 5]] over ZZ[T], which the bound does not reach",
            sp.Matrix([[7, 17], [2, 5]]),
            False,
        ),
    ]


def measure_parameter_ring() -> int:
    """Report the named matrices over ``ZZ[T]``. Return the number of disagreements."""
    ring = sp.ring("x,y", sp.ZZ[PARAMETER])[0]
    integral = sp.ring("x,y", sp.ZZ)[0]
    disagreements = 0

    print("Over ZZ[T], one matrix at a time:")
    for description, given, expected in parameter_cases():
        actual = reached(ring, given)
        mark = "ok " if actual == expected else "!! "
        verdict = "reached" if actual else "refused"
        print(f"  [{mark}] {description}: {verdict}")
        disagreements += int(actual != expected)

    same = reached(integral, sp.Matrix([[7, 17], [2, 5]]))
    mark = "ok " if same else "!! "
    print(f"  [{mark}] the same integer matrix over ZZ: reached by the fold")
    disagreements += int(not same)

    return disagreements


def invertible_pairs(modulus: int) -> list[sp.Matrix]:
    """Return every invertible ``2x2`` matrix over ``Z/nZ``."""
    found = []
    for entries in product(range(modulus), repeat=4):
        given = sp.Matrix(2, 2, list(entries))
        if sp.gcd(int(given.det()) % modulus, modulus) == 1:
            found.append(given)

    return found


def measure_residue_rings() -> tuple[int, int]:
    """Report every invertible ``2x2`` over the residue rings.

    Returns the number examined and the number refused.
    """
    examined = 0
    refused = 0

    print("Every invertible 2x2 over Z/nZ:")
    for modulus in MODULI:
        ring = sp.ring("x,y", sp.GF(modulus))[0]
        matrices = invertible_pairs(modulus)
        missed = sum(1 for given in matrices if not reached(ring, given))
        examined += len(matrices)
        refused += missed
        mark = "ok " if missed == 0 else "!! "
        print(f"  [{mark}] Z/{modulus}: {len(matrices)} matrices, {missed} refused")

    print(f"  {examined} matrices, {refused} refused")

    return examined, refused


def measure_random_triples(budget: float, seed: int) -> tuple[int, int]:
    """Report random invertible ``3x3`` over ``Z/6Z`` until the budget runs out.

    Each matrix is factorized and its determinant is taken, since
    ``0.7.0rc12``. Three-by-three is where the determinant starts dividing
    and where an audit of ``0.7.0rc11`` found it failing.

    Returns the number examined and the number refused. This part always ends
    at the budget rather than at a count, so the figure it reports is a figure
    with a time beside it and not a total. Random and not exhaustive: there
    are 6**9 matrices of this size over ``Z/6Z``, which is past what any gate
    should spend.
    """
    ring = sp.ring("x,y,z", sp.GF(6))[0]
    generator = random.Random(seed)
    started = time.monotonic()
    examined = 0
    refused = 0
    wrong = 0

    print(f"Random invertible 3x3 over Z/6Z, seed {seed}, budget {budget:.0f} s:")
    while time.monotonic() - started < budget:
        entries = [generator.randrange(6) for _ in range(9)]
        given = sp.Matrix(3, 3, entries)
        if sp.gcd(int(given.det()) % 6, 6) != 1:
            continue
        examined += 1
        refused += int(not reached(ring, given))
        wrong += int(not determines(ring, given))

    mark = "ok " if refused == 0 and wrong == 0 else "!! "
    print(
        f"  [{mark}] {examined} matrices, {refused} refused, "
        f"{wrong} with the wrong determinant"
    )

    return examined, refused + wrong


def main() -> int:
    """Run the three parts in order of cost and report each as it finishes."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--budget", type=float, default=DEFAULT_BUDGET)
    parser.add_argument("--seed", type=int, default=20260916)
    arguments = parser.parse_args()

    disagreements = 0

    started = time.monotonic()
    disagreements += measure_parameter_ring()
    print(f"  {time.monotonic() - started:.1f} s\n")

    started = time.monotonic()
    _, refused = measure_residue_rings()
    disagreements += refused
    print(f"  {time.monotonic() - started:.1f} s\n")

    started = time.monotonic()
    _, missed = measure_random_triples(arguments.budget, arguments.seed)
    disagreements += missed
    spent = time.monotonic() - started
    print(f"  {spent:.1f} s, stopped by the budget of {arguments.budget:.0f} s\n")

    if disagreements:
        print(f"{disagreements} results disagree with what this script expects.")
        return 1

    print("Every part agrees with docs/roadmap.md.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
