"""Reconstruction of the reduction from Alpoege's map to alpoege13, in SymPy.

This file does not depend on ``kellermap``. It stands to the thirteen-
dimensional chain as ``reconstruct_alpoege15.py`` stands to the fifteen-
dimensional one: a second, independent rendering of the same formulas, so that
the chain is checked against something other than the implementation that
produced it.

Where this chain comes from
---------------------------

Not from a hand computation. It is the first chain in this project that a
search found: work package 11 of milestone 0.5 widened what an untargeted
enumerator offers, and a greedy walk over the wider offer produced these seven
steps. That is why writing it down independently matters more here than for the
other two, and why this script exists before the widened enumerator does.

The steps use three things beyond Proposition (3.1), each of which the library
admits and each of which is named where it is used below:

- a second factor with several terms, which BCW never take, because they split
  a single monomial and a product of polynomials is a monomial only when both
  are;
- a factor an earlier step already bought, so that the step buys one coordinate
  instead of two;
- a step reaching ``EA^0`` rather than ``EA^1``, which Proposition (3.1) admits
  for the part of its argument that makes ``F'`` linear in each variable.

What it establishes, and what it does not
------------------------------------------

Seven steps into dimension 13, against the eight into 15 of ``alpoege15`` and
the eight into 17 of ``bcw17``. Degree three, determinant one, and Alpoege's
three points transported through it: three distinct preimages of one image.

It does not establish minimality. The walk that found it is greedy and never
looks sideways. It does not establish priority either: the literature is
checked again before any of this leaves the repository, and what a comparison
shows is written beside it. See ``docs/references.md``.

Run with::

    python scripts/reconstruct_alpoege13.py

The exit status is 0 if every check passes and 1 otherwise.
"""

from __future__ import annotations

from dataclasses import dataclass

import sympy as sp

X = sp.symbols("x1:14")
_1, _2, _3, _4, _5, _6, _7, _8, _9, _10, _11, _12, _13 = X

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
class Bought:
    """Both factors bought, two fresh variables.

    The formula of Proposition (3.1), unchanged. What is new is only that ``Q``
    may have several terms: the step then removes every monomial of the target
    component that ``P`` divides, in one move, instead of one monomial.
    """

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
class Scaled:
    """A shared step whose product is scaled, BCW-11.

    ``G`` subtracts ``coefficient * X_j * (X_k + P)``. The enumerator takes its
    factors monic and puts the coefficient in the step, where a hand
    computation would have written the scalar into one of them. The two are the
    same map and this follows the enumerator, because that is what
    ``examples.alpoege13`` is.
    """

    target: int
    carrier: int
    other: sp.Expr
    fresh: sp.Symbol
    coefficient: sp.Expr

    def apply(self, components: tuple[sp.Expr, ...]) -> tuple[sp.Expr, ...]:
        head = list(components)
        head[self.target] = sp.expand(
            head[self.target]
            - self.coefficient * components[self.carrier] * (self.fresh + self.other)
        )

        return tuple(head) + (sp.expand(self.fresh + self.other),)

    def appended(self, point: dict[sp.Symbol, sp.Expr]) -> tuple[sp.Expr, ...]:
        return (-sp.expand(self.other.xreplace(point)),)


@dataclass(frozen=True)
class Shared:
    """One factor supplied by an existing coordinate, one fresh variable.

    ``carrier`` is the zero-based index of the component that already has the
    shape ``X_j + P``, and ``other`` is the factor still to be bought. The
    product is symmetric, so which of the two is carried does not matter to the
    formula.
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


# The seven steps. The first two have a ``Q`` of four and three terms and reach
# ``EA^0``, which is where the chain gains most of its ground.
STEPS: tuple[Bought | Shared | Scaled, ...] = (
    Bought(
        2,
        _1 * _2**2,
        _1**2 * _2 * _3 + 3 * _1 * _2**2 + 3 * _1 * _3 + 7 * _2,
        _4,
        _5,
    ),
    Bought(1, _1**2 * _2, 3 * _1 * _2 * _3 + 9 * _2**2 + 6 * _3, _6, _7),
    Bought(2, _1 * _2, -_4 * _1 * _3 - 3 * _4 * _2 - _5 * _2, _8, _9),
    # x1*x2 has been component 7 since step 3.
    Shared(1, 7, -_1 * _7 - 3 * _3 * _6, _10),
    # The same carrier again, on another component.
    Shared(4, 7, _1 * _3, _11),
    # x1*x3 has been component 10 since step 5. The factor is monic and the
    # scalar rides in the step, which is what the enumerator produces.
    Scaled(0, 10, _1**2, _12, R(-1, 2)),
    Shared(2, 10, _4 * _8, _13),
)


def reduce_alpoege() -> tuple[sp.Expr, ...]:
    """Run the whole chain: normalization, then the seven steps."""
    components = normalize(ALPOEGE)
    for step in STEPS:
        components = step.apply(components)

    return components


def transport(point: tuple[sp.Expr, ...]) -> tuple[sp.Expr, ...]:
    """Carry one preimage through the chain.

    Each step appends the negated factors it buys: two for a bought step, one
    for a shared one. The normalization acts on the left and moves only the
    image.
    """
    carried = list(point)
    for step in STEPS:
        carried += list(step.appended(dict(zip(X, carried, strict=False))))

    return tuple(carried)


# --------------------------------------------------------------------------
# What the chain has to come out as
# --------------------------------------------------------------------------

DIMENSION = 13
DEGREE = 3
DETERMINANT = 1

IMAGE = (sp.Integer(0), sp.Integer(0), R(-1, 4)) + (sp.Integer(0),) * 10

POINTS = (
    (0, 0, R(-1, 4), 0, 0, 0, R(3, 2), 0, 0, 0, 0, 0, 0),
    (
        1,
        R(-3, 2),
        R(13, 2),
        R(-9, 4),
        -6,
        R(3, 2),
        -30,
        R(3, 2),
        R(9, 2),
        R(-3, 4),
        R(-13, 2),
        -1,
        R(27, 8),
    ),
    (
        -1,
        R(3, 2),
        R(13, 2),
        R(9, 4),
        6,
        R(-3, 2),
        -30,
        R(3, 2),
        R(9, 2),
        R(3, 4),
        R(13, 2),
        -1,
        R(-27, 8),
    ),
)


SAMPLE_POINTS = (
    tuple(R(k, 7) for k in range(1, 14)),
    tuple(R((-1) ** k * (k + 2), 3) for k in range(13)),
    (sp.Integer(0),) * 13,
)
"""Where the Jacobian determinant is evaluated.

Three points and not one. The last is the origin, where every carrier
coordinate vanishes and a determinant is easiest to get right by accident. The
other two have nothing to do with anything the chain was built from.
"""


def determinant_at(
    components: tuple[sp.Expr, ...],
    variables: tuple[sp.Symbol, ...],
    point: dict[sp.Symbol, sp.Expr],
) -> sp.Expr:
    """Return the Jacobian determinant evaluated at one point.

    At a point and not as a polynomial. Thirteen variables over ``QQ`` are past
    what expression-level elimination manages, and the technique the library
    uses to get past it, a Schur complement over the unipotent carrier block,
    is exactly the implementation this script exists to be independent of.

    Evaluating first is cheap and says less. A determinant that is constantly
    one evaluates to one everywhere, so any other value falsifies the claim,
    while agreement at finitely many points does not prove it. The polynomial
    identity is checked against the library in ``tests/``; this is the
    independent control that can fail.
    """
    jacobian = sp.Matrix(
        [
            [sp.diff(component, variable).xreplace(point) for variable in variables]
            for component in components
        ]
    )

    return sp.expand(jacobian.det())


def check(label: str, held: bool) -> bool:
    """Print one line and return what was checked."""
    print(f"  [{'ok ' if held else 'BAD'}] {label}")

    return held


def main() -> int:
    components = reduce_alpoege()
    variables = X[:DIMENSION]
    passed = []

    print("The chain")
    passed.append(
        check(f"it lands in dimension {DIMENSION}", len(components) == DIMENSION)
    )
    degree = max(sp.Poly(c, *variables).total_degree() for c in components)
    passed.append(check(f"its degree is {DEGREE}", degree == DEGREE))

    for trial, seed in enumerate(SAMPLE_POINTS):
        sample = dict(zip(variables, seed, strict=True))
        passed.append(
            check(
                f"its Jacobian determinant is {DETERMINANT} at sample point {trial}",
                determinant_at(components, variables, sample) == DETERMINANT,
            )
        )

    print("\nThe collision")
    moved = normalize(ALPOEGE)
    images = []
    for index, preimage in enumerate(ALPOEGE_COLLISION):
        carried = transport(preimage)
        passed.append(
            check(
                f"point {index} carries {DIMENSION} coordinates",
                len(carried) == DIMENSION,
            )
        )
        substitution = dict(zip(variables, carried, strict=True))
        images.append(tuple(sp.expand(c.xreplace(substitution)) for c in components))

    passed.append(check("the three images agree", images[0] == images[1] == images[2]))
    passed.append(check("and they are the recorded image", images[0] == IMAGE))
    passed.append(
        check(
            "the three preimages are distinct",
            len({tuple(transport(p)) for p in ALPOEGE_COLLISION}) == 3,
        )
    )

    print("\nAgainst the recorded points")
    for index, preimage in enumerate(ALPOEGE_COLLISION):
        carried = tuple(sp.sympify(c) for c in transport(preimage))
        wanted = tuple(sp.sympify(c) for c in POINTS[index])
        passed.append(check(f"point {index} is the one recorded", carried == wanted))

    # A control on the images. Alpoege's own collision has to survive the
    # normalization first, and the normalization moves only the image.
    passed.append(
        check(
            "Alpoege's three points are a collision to begin with",
            len(
                {
                    tuple(
                        sp.expand(c.xreplace(dict(zip(X[:3], p, strict=True))))
                        for c in moved
                    )
                    for p in ALPOEGE_COLLISION
                }
            )
            == 1,
        )
    )

    print(f"\n{sum(passed)} of {len(passed)} checks passed.")

    return 0 if all(passed) else 1


if __name__ == "__main__":
    raise SystemExit(main())
