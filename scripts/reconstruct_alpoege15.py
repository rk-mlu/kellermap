"""Reconstruction of the reduction from Alpoege's map to alpoege15, in SymPy.

This file does not depend on ``kellermap``. It stands to
``tests/test_alpoege15.py`` as ``reconstruct_bcw17.py`` stands to
``tests/test_bcw17.py``: a second, independent rendering of the same formulas,
so that the fixed components are checked against something other than the
implementation that will eventually produce them.

The chain is the seventeen-dimensional one with two steps changed. Its first
five steps are identical; steps six and seven each factor through a value an
earlier step had already bought, so each needs one fresh variable instead of
two:

- step 6 removes ``P * Q`` from component 3 with ``P = x1*x2``, which
  component 8 already carries. Only ``Q`` is bought.
- step 7 removes ``P * Q`` from component 11 with ``Q = x1**2``, which
  component 5 already carries. Only ``P`` is bought.

For a step whose two factors are both already carried by coordinates ``u`` and
``w``,

    G = (..., X_i - X_u X_w, ...),   F' = G o F

expands exactly as Proposition (3.1) does, with ``X_w`` in place of the second
fresh variable, and ``G`` stays elementary because ``-X_u X_w`` is free of
``X_i``. The mixed case below buys one of the two.

This technique is not in Bass-Connell-Wright. Using it is a deliberate
extension. Since milestone 0.3 the library can express and verify such a
chain, and ``tests/test_alpoege15.py`` does so; this script stays as the
independent second computation -- see ``docs/references.md``.

Run with::

    python scripts/reconstruct_alpoege15.py

The exit status is 0 if every check passes and 1 otherwise.
"""

from __future__ import annotations

from dataclasses import dataclass

import sympy as sp

X = sp.symbols("x1:16")
_1, _2, _3, _4, _5, _6, _7, _8, _9, _10, _11, _12, _13, _14, _15 = X

R = sp.Rational


# --------------------------------------------------------------------------
# Alpoege's map and the linear normalization
# --------------------------------------------------------------------------

ALPOEGE = (
    (1 + _1 * _2) ** 3 * _3 + _2**2 * (1 + _1 * _2) * (4 + 3 * _1 * _2),
    _2 + 3 * _1 * (1 + _1 * _2) ** 2 * _3 + 3 * _1 * _2**2 * (4 + 3 * _1 * _2),
    2 * _1 - 3 * _1**2 * _2 - _1**3 * _3,
)

ALPOEGE_COLLISION = (
    (sp.Integer(0), sp.Integer(0), R(-1, 4)),
    (sp.Integer(1), R(-3, 2), R(13, 2)),
    (sp.Integer(-1), R(3, 2), R(13, 2)),
)


def normalize(components: tuple[sp.Expr, ...]) -> tuple[sp.Expr, ...]:
    """Return F_(1)^-1 o F, the normalization of BCW II, Proposition (1.1)."""
    variables = X[: len(components)]
    jacobian = sp.Matrix([[sp.diff(f, v) for v in variables] for f in components])
    inverse = jacobian.xreplace({v: sp.Integer(0) for v in variables}).inv()

    return tuple(sp.expand(e) for e in inverse * sp.Matrix(components))


# --------------------------------------------------------------------------
# The two kinds of step
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Classic:
    """Proposition (3.1): both factors bought, two fresh variables."""

    target: int
    P: sp.Expr
    Q: sp.Expr
    u: sp.Symbol
    v: sp.Symbol

    def apply(self, components: tuple[sp.Expr, ...]) -> tuple[sp.Expr, ...]:
        moved = components[self.target] - self.P * self.Q
        moved = moved - self.u * self.Q - self.P * self.v - self.u * self.v

        head = list(components)
        head[self.target] = sp.expand(moved)

        return tuple(head) + (
            sp.expand(self.u + self.P),
            sp.expand(self.v + self.Q),
        )

    def appended(self, point: dict[sp.Symbol, sp.Expr]) -> tuple[sp.Expr, ...]:
        return (
            -sp.expand(self.P.xreplace(point)),
            -sp.expand(self.Q.xreplace(point)),
        )


@dataclass(frozen=True)
class Shared:
    """One factor supplied by an existing coordinate, one fresh variable.

    ``carrier`` is the zero-based index of the component that already has the
    shape ``X_j + P``; ``other`` is the factor still to be bought, and ``fresh``
    the variable that carries it. Which of ``P`` and ``Q`` is which does not
    matter to the formula, since the product is symmetric.
    """

    target: int
    carrier: int
    other: sp.Expr
    fresh: sp.Symbol

    def apply(self, components: tuple[sp.Expr, ...]) -> tuple[sp.Expr, ...]:
        head = list(components)
        head[self.target] = sp.expand(
            head[self.target] - components[self.carrier] * (self.fresh + self.other)
        )

        return tuple(head) + (sp.expand(self.fresh + self.other),)

    def appended(self, point: dict[sp.Symbol, sp.Expr]) -> tuple[sp.Expr, ...]:
        return (-sp.expand(self.other.xreplace(point)),)


STEPS: tuple[Classic | Shared, ...] = (
    Classic(0, -_1 * _3 / 2, _1**2, _4, _5),
    Classic(1, 3 * _1**2 * _2, _1 * _2 * _3 + 3 * _2**2, _6, _7),
    Classic(1, _1 * _2, 6 * _1 * _3 - 3 * _1 * _7 - _3 * _6, _8, _9),
    Classic(
        2,
        _1 * _2**2,
        _1**2 * _2 * _3 + 3 * _1 * _2**2 + 3 * _1 * _3 + 7 * _2,
        _10,
        _11,
    ),
    Classic(2, _1 * _2 * _10, -_1 * _3 - 3 * _2, _12, _13),
    # x1*x2 liegt seit Schritt 3 als Komponente 8 vor.
    Shared(2, 7, -_10 * _13 - _2 * _11, _14),
    # x1**2 liegt seit Schritt 1 als Komponente 5 vor.
    Shared(10, 4, _2 * _3, _15),
)


def reduce_alpoege() -> tuple[sp.Expr, ...]:
    """Run the whole chain: normalization, then the seven steps."""
    components = normalize(ALPOEGE)
    for step in STEPS:
        components = step.apply(components)

    return components


def transport(point: tuple[sp.Expr, ...]) -> tuple[sp.Expr, ...]:
    """Carry one preimage through the chain.

    Each step appends the negated factors it buys: two for a classic step, one
    for a shared one. The normalization acts on the left and moves only the
    image.
    """
    carried = list(point)
    for step in STEPS:
        carried += list(step.appended(dict(zip(X, carried, strict=False))))

    return tuple(carried)


# --------------------------------------------------------------------------
# The fixed target
# --------------------------------------------------------------------------

ALPOEGE15 = (
    -3 * _1**2 * _2 / 2 - _1**2 * _4 + _1 * _3 * _5 / 2 + _1 - _4 * _5,
    12 * _1 * _2**2
    - _1 * _2 * _9
    - 6 * _1 * _3 * _8
    + 3 * _1 * _3
    + 3 * _1 * _7 * _8
    - 3 * _2**2 * _6
    + _2
    + _3 * _6 * _8
    - _6 * _7
    - _8 * _9,
    -3 * _1 * _10 * _3
    + _1 * _12 * _3
    - _1 * _14 * _2
    + 3 * _1 * _2 * _3
    - _10 * _11
    + _10 * _13 * _8
    - 7 * _10 * _2
    + _11 * _2 * _8
    - _12 * _13
    + 3 * _12 * _2
    - _14 * _8
    + 4 * _2**2
    + _3,
    -_1 * _3 / 2 + _4,
    _1**2 + _5,
    3 * _1**2 * _2 + _6,
    _1 * _2 * _3 + 3 * _2**2 + _7,
    _1 * _2 + _8,
    6 * _1 * _3 - 3 * _1 * _7 - _3 * _6 + _9,
    _1 * _2**2 + _10,
    -(_1**2) * _15
    + 3 * _1 * _2**2
    + 3 * _1 * _3
    + _11
    - _15 * _5
    - _2 * _3 * _5
    + 7 * _2,
    _1 * _10 * _2 + _12,
    -_1 * _3 + _13 - 3 * _2,
    -_10 * _13 - _11 * _2 + _14,
    _15 + _2 * _3,
)

ALPOEGE15_COLLISION = (
    (0, 0, R(-1, 4)) + (0,) * 12,
    (
        1,
        R(-3, 2),
        R(13, 2),
        R(13, 4),
        -1,
        R(9, 2),
        3,
        R(3, 2),
        R(-3, 4),
        R(-9, 4),
        -6,
        R(-27, 8),
        2,
        R(9, 2),
        R(39, 4),
    ),
    (
        -1,
        R(3, 2),
        R(13, 2),
        R(-13, 4),
        -1,
        R(-9, 2),
        3,
        R(3, 2),
        R(3, 4),
        R(9, 4),
        6,
        R(27, 8),
        -2,
        R(9, 2),
        R(-39, 4),
    ),
)


# --------------------------------------------------------------------------
# Report
# --------------------------------------------------------------------------


def main() -> int:
    """Print the chain and check it against the fixed data."""
    components = normalize(ALPOEGE)

    print("The chain")
    print(f"  normalization              dim = 3   deg = {_degree(components)}")
    for number, step in enumerate(STEPS, start=1):
        components = step.apply(components)
        kind = "classic" if isinstance(step, Classic) else "shared "
        print(
            f"  step {number}  {kind}  component {step.target + 1:>2}   "
            f"dim = {len(components):>2}  deg = {_degree(components)}"
        )
    print()

    transported = tuple(
        tuple(sp.nsimplify(c) for c in transport(point)) for point in ALPOEGE_COLLISION
    )
    expected = tuple(
        tuple(sp.nsimplify(c) for c in point) for point in ALPOEGE15_COLLISION
    )

    checks = {
        "components agree with alpoege15": all(
            sp.expand(a - b) == 0 for a, b in zip(components, ALPOEGE15, strict=True)
        ),
        "collision agrees with alpoege15": transported == expected,
        "degree of the result is 3": _degree(components) == 3,
        "dimension of the result is 15": len(components) == 15,
    }

    print("Checks")
    for description, passed in checks.items():
        print(f"  [{'ok' if passed else 'FAILED'}] {description}")
    print()

    print("Two steps share a carrier an earlier step had already bought:")
    print("  step 6 reuses component 8, which carries x1*x2 since step 3")
    print("  step 7 reuses component 5, which carries x1**2 since step 1")
    print("Each therefore buys one fresh variable rather than two, which is")
    print("what takes the chain to dimension 15 instead of 17.")

    return 0 if all(checks.values()) else 1


def _degree(components: tuple[sp.Expr, ...]) -> int:
    variables = X[: len(components)]

    return int(max(sp.Poly(e, *variables).total_degree() for e in components))


if __name__ == "__main__":
    raise SystemExit(main())
