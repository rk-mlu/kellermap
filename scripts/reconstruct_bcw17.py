"""Reconstruction of the reduction from Alpoege's map to BCW17, in plain SymPy.

This file does not depend on ``kellermap``. Since version 0.2 the test suite
derives the same map through ``Reduction`` and ``BCWStep``, and this script
stays as the independent second implementation: two separate renderings of
formula (1) agreeing on all seventeen components and all three collision points
say more than one implementation checked against itself.

The reduction has two parts.

1. The linear normalization of BCW Section 4, ``N = L^-1 o F`` with ``L = J(F)(0)``.
   Here ``L^-1`` transposes the first and third coordinate and then scales the
   result coordinate by 1/2. Its determinant is -1/2, so it does *not* lie in
   ``EA_3(k)``.

2. Seven applications of Proposition (3.1), two fresh variables each,
   dimension 3 -> 17 and degree 7 -> 3.

The data in ``STEPS`` are read off the fixed BCW17 components: components
4..17 all have the shape ``X_j + P``, and those ``P`` are exactly the factors
of the seven steps. This is therefore a reconstruction from the result, not a
search. Searching for such a factorization is milestone 0.3.

Run with::

    python scripts/reconstruct_bcw17.py

The exit status is 0 if every check passes and 1 otherwise, so that the script
is usable as a gate rather than only for reading.
"""

from __future__ import annotations

from dataclasses import dataclass

import sympy as sp

X = sp.symbols("x1:18")
_1, _2, _3, _4, _5, _6, _7, _8, _9, _10, _11, _12, _13, _14, _15, _16, _17 = X

R = sp.Rational


# --------------------------------------------------------------------------
# Part 1: Alpoege's map and the linear normalization
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

ALPOEGE_IMAGE = (R(-1, 4), sp.Integer(0), sp.Integer(0))


def linear_part(components: tuple[sp.Expr, ...]) -> sp.Matrix:
    """Return J(F)(0)."""
    variables = X[: len(components)]
    jacobian = sp.Matrix([[sp.diff(f, v) for v in variables] for f in components])

    return jacobian.xreplace({v: sp.Integer(0) for v in variables})


def normalize(components: tuple[sp.Expr, ...]) -> tuple[sp.Expr, ...]:
    """Return F'' = F'_(1)^-1 o F', the normalization of BCW Section 4."""
    inverse = linear_part(components).inv()

    return tuple(sp.expand(e) for e in inverse * sp.Matrix(components))


# --------------------------------------------------------------------------
# Part 2: the seven steps of Proposition (3.1)
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Step:
    """One step ``F' = G o F^[2] o H``.

    ``target`` is the zero-based index of the component from which ``P * Q``
    is removed. BCW state the proposition for the first component; step seven
    below acts on component 11, a coordinate that step four introduced.
    """

    target: int
    P: sp.Expr
    Q: sp.Expr
    u: sp.Symbol
    v: sp.Symbol

    def apply(self, components: tuple[sp.Expr, ...]) -> tuple[sp.Expr, ...]:
        """Apply formulas (2) and (3): F_i' = (F_i - P*Q) - u*Q - P*v - u*v."""
        moved = components[self.target] - self.P * self.Q
        moved = moved - self.u * self.Q - self.P * self.v - self.u * self.v

        head = list(components)
        head[self.target] = sp.expand(moved)

        return tuple(head) + (
            sp.expand(self.u + self.P),
            sp.expand(self.v + self.Q),
        )

    def pull_back(self, point: tuple[sp.Expr, ...]) -> tuple[sp.Expr, ...]:
        """Apply H^-1 to the point padded with zeros.

        H is (..., u + P, ..., v + Q), so H^-1 is (..., u - P, ..., v - Q).
        Applied to (a, 0, 0) that means the two fresh coordinates become
        -P(a) and -Q(a). Both P and Q are free of u and v, so the order of the
        two factors of H does not matter here.
        """
        substitution = dict(zip(X, point, strict=False))

        return point + (
            -self.P.xreplace(substitution),
            -self.Q.xreplace(substitution),
        )

    def filtration_level(self) -> int:
        """Return 0 if P or Q carries a linear term, and 1 otherwise.

        Proposition (3.1) asks for EA^1 but admits EA^0 once the factorization
        is allowed to become linear. This is what decides whether the result
        still lies in MA^1.
        """
        variables = tuple(sorted(self.P.free_symbols | self.Q.free_symbols, key=str))
        if not variables:
            return 1

        orders = [
            min(sum(monomial) for monomial in sp.Poly(factor, *variables).monoms())
            for factor in (self.P, self.Q)
            if factor != 0
        ]

        return 1 if min(orders) >= 2 else 0


STEPS = (
    Step(0, -_1 * _3 / 2, _1**2, _4, _5),
    Step(1, 3 * _1**2 * _2, _1 * _2 * _3 + 3 * _2**2, _6, _7),
    Step(1, _1 * _2, 6 * _1 * _3 - 3 * _1 * _7 - _3 * _6, _8, _9),
    Step(
        2,
        _1 * _2**2,
        _1**2 * _2 * _3 + 3 * _1 * _2**2 + 3 * _1 * _3 + 7 * _2,
        _10,
        _11,
    ),
    Step(2, _1 * _2 * _10, -_1 * _3 - 3 * _2, _12, _13),
    Step(2, _1 * _2, -_10 * _13 - _2 * _11, _14, _15),
    Step(10, _2 * _3, _1**2, _16, _17),
)


def reduce_alpoege() -> tuple[sp.Expr, ...]:
    """Run the whole chain: normalization, then the seven steps."""
    components = normalize(ALPOEGE)
    for step in STEPS:
        components = step.apply(components)

    return components


def transport(point: tuple[sp.Expr, ...]) -> tuple[sp.Expr, ...]:
    """Carry one preimage through the chain.

    The normalization acts on the left and leaves preimages untouched; it only
    moves the image. Every BCW step pulls the preimage back through H^-1.
    """
    for step in STEPS:
        point = step.pull_back(point)

    return point


# --------------------------------------------------------------------------
# The fixed target
# --------------------------------------------------------------------------

BCW17 = (
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
    - _1 * _15 * _2
    + 3 * _1 * _2 * _3
    - _10 * _11
    + _10 * _13 * _14
    - 7 * _10 * _2
    + _11 * _14 * _2
    - _12 * _13
    + 3 * _12 * _2
    - _14 * _15
    + 4 * _2**2
    + _3,
    -_1 * _3 / 2 + _4,
    _1**2 + _5,
    3 * _1**2 * _2 + _6,
    _1 * _2 * _3 + 3 * _2**2 + _7,
    _1 * _2 + _8,
    6 * _1 * _3 - 3 * _1 * _7 - _3 * _6 + _9,
    _1 * _2**2 + _10,
    -(_1**2) * _16
    + 3 * _1 * _2**2
    + 3 * _1 * _3
    + _11
    - _16 * _17
    - _17 * _2 * _3
    + 7 * _2,
    _1 * _10 * _2 + _12,
    -_1 * _3 + _13 - 3 * _2,
    _1 * _2 + _14,
    -_10 * _13 - _11 * _2 + _15,
    _16 + _2 * _3,
    _1**2 + _17,
)

BCW17_COLLISION = (
    (0, 0, R(-1, 4)) + (0,) * 14,
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
        R(3, 2),
        R(9, 2),
        R(39, 4),
        -1,
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
        R(3, 2),
        R(9, 2),
        R(-39, 4),
        -1,
    ),
)


# --------------------------------------------------------------------------
# Report
# --------------------------------------------------------------------------


def main() -> int:
    """Print the chain and check it against the fixed data."""
    matrix = linear_part(ALPOEGE)
    inverse = matrix.inv()

    print("Linear part of Alpoege's map and its inverse")
    print(f"  L      = {matrix.tolist()}   det = {matrix.det()}")
    print(f"  L^-1   = {inverse.tolist()}   det = {inverse.det()}")
    print("  L^-1 is a transposition and a dilation, so it is not elementary:")
    print("  every element of EA_n(k) has determinant one.")
    print()

    components = normalize(ALPOEGE)
    image = tuple(sp.expand(e) for e in inverse * sp.Matrix(ALPOEGE_IMAGE))

    print("The chain")
    print(f"  normalization         dim = 3   deg = {_degree(components)}")
    for number, step in enumerate(STEPS, start=1):
        components = step.apply(components)
        print(
            f"  step {number}  component {step.target + 1:>2}  "
            f"({step.u}, {step.v})  EA^{step.filtration_level()}   "
            f"dim = {len(components):>2}  deg = {_degree(components)}"
        )
    print()

    transported = tuple(
        tuple(sp.nsimplify(c) for c in transport(point)) for point in ALPOEGE_COLLISION
    )
    expected = tuple(tuple(sp.nsimplify(c) for c in point) for point in BCW17_COLLISION)

    checks = {
        "components agree with BCW17": all(
            sp.expand(a - b) == 0 for a, b in zip(components, BCW17, strict=True)
        ),
        "collision agrees with BCW17": transported == expected,
        "degree of the result is 3": _degree(components) == 3,
        "dimension of the result is 17": len(components) == 17,
    }

    print("Checks")
    for description, passed in checks.items():
        print(f"  [{'ok' if passed else 'FAILED'}] {description}")
    print()

    print(f"Collision image after normalization: {image} followed by 14 zeros")
    print(
        "Steps four and five declare EA^0 because their Q carries a linear "
        "term.\nThose two terms are why the result lies in MA^0 and not in MA^1."
    )

    return 0 if all(checks.values()) else 1


def _degree(components: tuple[sp.Expr, ...]) -> int:
    variables = X[: len(components)]

    return max(sp.Poly(e, *variables).total_degree() for e in components)


if __name__ == "__main__":
    raise SystemExit(main())
