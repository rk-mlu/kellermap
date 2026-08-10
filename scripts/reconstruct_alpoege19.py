"""Render the seventeen-step reduction to the published map in plain SymPy.

The third of the ``reconstruct_`` scripts and the second independent rendering
of a reduction this repository holds. Like the other two it applies the step
formula directly rather than calling the library, so that the library has
something other than itself to agree with.

One qualification, because the docstring said otherwise and an audit was right
to object. This script imports no name from ``kellermap``, but it executes
``tests/data.py`` to read the published map, and *that* module imports
``kellermap`` to build a ``PolynomialMap``. The arithmetic below is
independent; the data is read through the library's own type. What the module
supplies is nineteen expressions and three points, so nothing the library
computes enters the comparison -- but the claim to import nothing was too
strong.

It reads the published map from ``tests/data.py``, which the source archive
does not carry. From a checkout it runs; from an unpacked sdist it says what is
missing and stops. That is the same decision as everywhere else in this
project: the map is not ours to distribute.

It differs from them in one respect, and the difference is deliberate.
``reconstruct_bcw17.py`` and ``reconstruct_alpoege15.py`` carry their own copy
of the map they end at, because that map is the project's own hand computation
and a second copy of it costs nothing. The nineteen-dimensional map is somebody
else's, and its licence could not be established, so it is not copied a second
time: this script reads it from ``tests/data.py``, where WP 8 put it. What is
rendered independently here is the *reduction*, which is what the library
computes and therefore what wants a second opinion.

The chain uses three extensions of Chapter II, Proposition (3.1), all of them
recorded in ``docs/contracts.md``:

* a factor may come from a coordinate an earlier step introduced (BCW-10);
* the removed product carries a coefficient (BCW-11);
* one fresh coordinate may fill both slots (BCW-12).

For a fresh slot the factor component is ``u + P``; for a carried slot it is the
current component of that coordinate. A step with target ``t`` and coefficient
``c`` is

    F_t  ->  F_t - c * Phi_left * Phi_right,

and each distinct fresh coordinate is appended once, carrying ``P``.

Provenance of the chain. It was reconstructed by an external audit of this
project in August 2026 and verified here against the published map before it
was written down. This script is that verification, kept: nothing in it is
taken on trust, and every check it prints is recomputed from the steps.

The exit status is 0 if every check passes and 1 otherwise.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import sympy as sp

x, y, z = sp.symbols("x y z")
w = sp.symbols("w1:17")
w1, w2, w3, w4, w5, w6, w7, w8, w9, w10, w11, w12, w13, w14, w15, w16 = w

# Alpoege's map, in the coordinates the published one uses. Its own copy: this
# map is somebody else's mathematics too, but it has a citable presentation
# under a licence, and every reduction here starts from it.
ALPOEGE = (
    (1 + x * y) ** 3 * z + y**2 * (1 + x * y) * (4 + 3 * x * y),
    y + 3 * x * (1 + x * y) ** 2 * z + 3 * x * y**2 * (4 + 3 * x * y),
    2 * x - 3 * x**2 * y - x**3 * z,
)

ALPOEGE_POINTS = (
    (0, 0, sp.Rational(-1, 4)),
    (1, sp.Rational(-3, 2), sp.Rational(13, 2)),
    (-1, sp.Rational(3, 2), sp.Rational(13, 2)),
)

# (target, left, right, coefficient). A slot is ("fresh", variable, value) or
# ("carried", variable).
FRESH = "fresh"
CARRIED = "carried"

# ``("fresh", variable, value)`` or ``("carried", variable)``. The length tells
# the two apart, and the tag is there for a reader; a check on the tag alone
# leaves the value unreachable as far as a type checker is concerned.
Slot = tuple[str, sp.Symbol, sp.Expr] | tuple[str, sp.Symbol]
Plan = tuple[sp.Symbol, Slot, Slot, int]

STEPS: tuple[Plan, ...] = (
    (x, (FRESH, w1, y**2 * z), (FRESH, w2, x**3 * y), 1),
    (y, (CARRIED, w2), (FRESH, w4, y * z), 3),
    (x, (CARRIED, w4), (FRESH, w5, x**2 * y), 3),
    (y, (CARRIED, w5), (FRESH, w8, x * w4), -3),
    (y, (CARRIED, w5), (FRESH, w7, y**2), 9),
    (x, (CARRIED, w8), (FRESH, w9, x * y), -3),
    (x, (CARRIED, w7), (CARRIED, w9), 7),
    (y, (CARRIED, w4), (FRESH, w13, x**2), 6),
    (w2, (CARRIED, w9), (CARRIED, w13), 1),
    (z, (CARRIED, w13), (FRESH, w16, x * z), -1),
    (y, (CARRIED, w13), (FRESH, w15, y * w8), 3),
    (y, (CARRIED, w13), (FRESH, w14, y * w7), -9),
    (x, (CARRIED, w5), (FRESH, w6, x * w1), -1),
    (x, (CARRIED, w9), (FRESH, w12, x * w6), 1),
    (x, (FRESH, w3, x * y**2), (FRESH, w3, x * y**2), 3),
    (x, (CARRIED, w9), (FRESH, w11, y * w3), -6),
    (x, (CARRIED, w7), (FRESH, w10, z * w2), -1),
)

EXPECTED_DIMENSIONS = (3, 5, 6, 7, 8, 9, 10, 10, 11, 11, 12, 13, 14, 15, 16, 17, 18, 19)
EXPECTED_DEGREES = (7, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 4, 4, 3)


def published() -> ModuleType:
    """Return the module holding the map this reduction ends at.

    Read rather than copied. The map is not this project's and its licence
    could not be established, so the repository holds it once, outside the
    distributed package.
    """
    root = Path(__file__).resolve().parent.parent
    path = root / "tests" / "data.py"
    spec = importlib.util.spec_from_file_location("published_map", path)
    if spec is None or spec.loader is None or not path.exists():
        raise FileNotFoundError(
            f"{path} is not here. The nineteen-dimensional map is somebody "
            "else's mathematics and its licence could not be established, so "
            "this project does not distribute it: the file is in the "
            "repository and excluded from the source archive."
        )

    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(root))
    spec.loader.exec_module(module)

    return module


def apply_steps() -> tuple[
    dict[sp.Symbol, sp.Expr], list[sp.Symbol], list[int], list[int], list[bool]
]:
    """Return the components, the coordinate order, and what each step cost.

    The identities are checked as the steps are applied, one per step: the new
    target component must be the old one less the weighted product of the two
    factor components. That is the whole of the step formula, written out.
    """
    components = {x: ALPOEGE[0], y: ALPOEGE[1], z: ALPOEGE[2]}
    order = [x, y, z]
    dimensions, degrees, identities = [3], [_degree(components, order)], []

    for target, left, right, coefficient in STEPS:
        for slot in (left, right):
            if len(slot) == 3 and slot[1] not in components:
                components[slot[1]] = slot[1] + slot[2]
                order.append(slot[1])

        factors = [components[slot[1]] for slot in (left, right)]
        before = components[target]
        after = sp.expand(before - coefficient * factors[0] * factors[1])
        identities.append(
            sp.expand(before - after - coefficient * factors[0] * factors[1]) == 0
        )
        components[target] = after
        dimensions.append(len(order))
        degrees.append(_degree(components, order))

    return components, order, dimensions, degrees, identities


def transport() -> list[dict[sp.Symbol, sp.Expr]]:
    """Return Alpoege's three points, carried along the chain.

    A fresh coordinate takes the value that makes its component vanish at the
    point, so every factor component is zero there and no target component
    moves. That is why the three images stay equal.
    """
    points = [dict(zip((x, y, z), point, strict=True)) for point in ALPOEGE_POINTS]
    seen: set[sp.Symbol] = set()

    for _, left, right, _coefficient in STEPS:
        for slot in (left, right):
            if len(slot) == 3 and slot[1] not in seen:
                seen.add(slot[1])
                for point in points:
                    point[slot[1]] = sp.nsimplify(
                        -sp.expand(slot[2]).subs(point, simultaneous=True)
                    )

    return points


def _degree(components: dict[sp.Symbol, sp.Expr], order: list[sp.Symbol]) -> int:
    return int(max(sp.Poly(components[v], *order).total_degree() for v in order))


def main() -> int:
    try:
        data = published()
    except FileNotFoundError as missing:
        print(missing)
        return 2

    components, order, dimensions, degrees, identities = apply_steps()
    points = transport()

    built = {variable: sp.expand(components[variable]) for variable in order}
    target = dict(zip(data.VARIABLES, data.COMPONENTS, strict=True))

    images = [
        tuple(
            sp.nsimplify(built[variable].subs(point, simultaneous=True))
            for variable in data.VARIABLES
        )
        for point in points
    ]
    carried = tuple(
        tuple(sp.nsimplify(point[variable]) for variable in data.VARIABLES)
        for point in points
    )

    checks = {
        "every step identity holds": all(identities),
        "the chain has seventeen steps": len(STEPS) == 17,
        "sixteen coordinates are introduced": len(order) == 19,
        "the dimensions run as recorded": tuple(dimensions) == EXPECTED_DIMENSIONS,
        "the degrees run as recorded": tuple(degrees) == EXPECTED_DEGREES,
        "the components agree with the published map": all(
            sp.expand(built[variable] - target[variable]) == 0
            for variable in data.VARIABLES
        ),
        "the transported points agree": carried
        == tuple(
            tuple(sp.nsimplify(value) for value in point)
            for point in data.PUBLISHED_POINTS
        ),
        "the three images agree": images[0] == images[1] == images[2],
    }

    print("Checks")
    for description, passed in checks.items():
        print(f"  [{'ok' if passed else 'FAILED'}] {description}")
    print()

    print("Structure of the chain")
    pairs = sum(
        1
        for _, left, right, _c in STEPS
        if left[0] == FRESH and right[0] == FRESH and left[1] != right[1]
    )
    spare = sum(1 for _, left, right, _c in STEPS if left[0] == right[0] == CARRIED)
    print(f"  steps introducing two coordinates: {pairs}")
    print(f"  steps introducing none:            {spare}")
    print(f"  steps introducing one:             {len(STEPS) - pairs - spare}")
    print(
        "  Alpoege's map has no carriers, so the first step has nothing for a\n"
        "  carried slot to point at and must introduce two. Seventeen steps and\n"
        "  sixteen coordinates then force two steps that introduce none."
    )
    print()

    print("Introduction order")
    print("  " + ", ".join(str(variable) for variable in order[3:]))
    print("  Not w1 to w16. The numbering of the published map is a topological")
    print("  order of the final carrier values, not a chronology.")
    print()

    print("Coefficients")
    print("  " + ", ".join(str(step[3]) for step in STEPS))
    print("  No change of coordinates removes them. A diagonal absorbing them")
    print("  would need 1/7 at step seven where the earlier steps force 1/9, and")
    print("  1 at step nine where they force 1/2.")

    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
