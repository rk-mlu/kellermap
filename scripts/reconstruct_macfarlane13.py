"""Reconstruction of a chain from Alpoege's map to macfarlane13, in SymPy.

This file does not depend on ``kellermap``. It stands to Macfarlane's
thirteen-variable map as ``reconstruct_alpoege19.py`` stands to the published
nineteen-dimensional one: the map is somebody else's, the chain to it is this
project's, and both are written out here so that the agreement rests on two
implementations rather than one.

What is being claimed, and what is not
---------------------------------------

The map is not this project's. A. Macfarlane published it on 22 July 2026,
https://github.com/Amacfa/keller-counterexamples-13-20, obtained by restricting
W. Thompson's twenty-four-variable cubic-homogeneous form to an invariant
subspace. That construction is not in this library and nothing here reproduces
it.

What is claimed is narrower and is the point of the file. The map lies inside
the space this project's untargeted search describes: seven steps of BCW
Proposition (3.1), of exactly the shapes UNT-1 to UNT-9 admit, lead from
Alpoege's normalized map to it. The backward search found them in eight
examined maps; they are transcribed here and recomputed without the library.

That matters because it settles a question the other direction leaves open.
``kellermap.examples.alpoege13`` is a different map, with 58 terms and a
three-point collision against this one's two, and the forward search finds that
one rather than this. The two are not variants of each other. Reaching this map
by a chain says the gap is which chain the order picks and not what the space
contains.

Two of the seven steps carry a coefficient other than one, `-2` and `3`, and
four have a factor with several terms. Neither shape is in Proposition (3.1) as
BCW state it; both are in BCW-11 and BCW-6 as this project states them, and
``docs/contracts.md`` marks them as extensions.

Run with::

    python scripts/reconstruct_macfarlane13.py

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
    """Both factors bought, two fresh variables, and a coefficient.

    ``G`` subtracts ``coefficient * X_u * X_v``. BCW take the coefficient into
    one of the factors; this project keeps the factors as they are found and
    puts the scalar in the step, which is BCW-11.
    """

    target: int
    P: sp.Expr
    Q: sp.Expr
    u: sp.Symbol
    v: sp.Symbol
    coefficient: sp.Expr = sp.Integer(1)

    def apply(self, components: tuple[sp.Expr, ...]) -> tuple[sp.Expr, ...]:
        head = list(components)
        head[self.target] = sp.expand(
            head[self.target] - self.coefficient * (self.u + self.P) * (self.v + self.Q)
        )

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
    shape ``X_j + P``. BCW-10, and the reason a step can cost one coordinate
    instead of two.
    """

    target: int
    carrier: int
    other: sp.Expr
    fresh: sp.Symbol
    coefficient: sp.Expr = sp.Integer(1)

    def apply(self, components: tuple[sp.Expr, ...]) -> tuple[sp.Expr, ...]:
        head = list(components)
        head[self.target] = sp.expand(
            head[self.target]
            - self.coefficient * components[self.carrier] * (self.fresh + self.other)
        )

        return tuple(head) + (sp.expand(self.fresh + self.other),)

    def appended(self, point: dict[sp.Symbol, sp.Expr]) -> tuple[sp.Expr, ...]:
        return (-sp.expand(self.other.xreplace(point)),)


# The seven steps, as the backward search found them. The names are the ones it
# handed out, so the coordinates arrive in its order and not in Macfarlane's;
# ORDER below is the permutation between the two.
STEPS: tuple[Bought | Shared, ...] = (
    Bought(2, _1**2 * _2**2, _1 * _2 * _3 + 3 * _2**2, _4, _5),
    Bought(3, -(_1**2) / 2, _2**2, _6, _7, -2),
    # -x1^2/2 has been component 5 since step 2.
    Shared(0, 5, _1 * _3, _8),
    # x1*x2*x3 + 3*x2^2 has been component 4 since step 1.
    Shared(1, 4, _1**2 * _2, _9, 3),
    # x1*x3 has been component 8 since step 3.
    Shared(2, 8, 3 * _2 * _3 - _2 * _5, _10),
    Bought(2, _1 * _2, -_1 * _10 + 7 * _2**2 - _3 * _4, _11, _12),
    # x1*x2 has been component 10 since step 6.
    Shared(1, 10, 6 * _1 * _3 - 3 * _1 * _5 - 3 * _3 * _9, _13),
)

# Where each coordinate of the chain sits in Macfarlane's numbering. The search
# names a fresh coordinate when it buys it, and he numbers by another rule, so
# the two agree only after this permutation.
ORDER = (1, 2, 3, 4, 5, 12, 13, 11, 6, 7, 8, 10, 9)


def reduce_alpoege() -> tuple[sp.Expr, ...]:
    """Run the whole chain: normalization, then the seven steps."""
    components = normalize(ALPOEGE)
    for step in STEPS:
        components = step.apply(components)

    return components


def in_macfarlanes_order(components: tuple[sp.Expr, ...]) -> tuple[sp.Expr, ...]:
    """Return the map with its coordinates renamed and reordered to match his.

    A permutation of the generators is a change of presentation and not of the
    map, which is what ``PolynomialMap.reordered`` says in the library and what
    this does by hand.
    """
    renaming = {X[index]: X[position - 1] for index, position in enumerate(ORDER)}
    moved = [sp.expand(component.xreplace(renaming)) for component in components]

    placed: list[sp.Expr] = [sp.Integer(0)] * len(ORDER)
    for index, position in enumerate(ORDER):
        placed[position - 1] = moved[index]

    return tuple(placed)


# --------------------------------------------------------------------------
# Macfarlane's map, transcribed
# --------------------------------------------------------------------------

_RR = (
    -_11 * _12,
    3 * _1 * _3 - _8 * _9 - 3 * _5 * _6,
    -_8 * _10 + 4 * _2**2 - _4 * _5 - _6 * _7,
    2 * _12 * _13,
    3 * _2**2,
    sp.Integer(0),
    3 * _2 * _3 - _2 * _5,
    _1 * _2,
    6 * _1 * _3 - 3 * _1 * _5 - 3 * _3 * _6,
    -_1 * _7 + 7 * _2**2 - _3 * _4,
    _1 * _3,
    -R(1, 2) * _1**2,
    _2**2,
)

_GG = (
    -2 * _1 * _3 * _8
    + _1 * _5 * _8
    - R(1, 3) * _1 * _2 * _9
    + 4 * _1 * _2**2
    + _3 * _6 * _8
    - 3 * _2**2 * _6,
    _1 * _7 * _8
    - _1 * _2 * _10
    - 7 * _2**2 * _8
    + _3 * _4 * _8
    - 3 * _2**2 * _4
    - 3 * _2 * _3 * _6
    + _2 * _5 * _6,
    _1**2 * _13 - 2 * _12 * _2**2,
    -R(1, 2) * _1**2 * _11 + _1 * _12 * _3,
    _1 * _2 * _3,
    _1**2 * _2,
)

_BB = (
    -_GG[3] - R(3, 2) * _GG[5],
    3 * _GG[0],
    _GG[1] + 3 * _GG[4],
    -_GG[2],
    _GG[4],
    _GG[5],
) + (sp.Integer(0),) * 7

MACFARLANE = tuple(sp.expand(X[i] + _RR[i] + _BB[i]) for i in range(13))

ALPOEGE_COLLISION = (
    (sp.Integer(0), sp.Integer(0), R(-1, 4)),
    (sp.Integer(1), R(-3, 2), R(13, 2)),
    (sp.Integer(-1), R(3, 2), R(13, 2)),
)
"""Alpoege's three preimages of one image, before the normalization."""


MACFARLANE_POINTS = (
    (0, 0, R(-1, 4), 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
    (
        1,
        R(-3, 2),
        R(13, 2),
        R(-9, 4),
        3,
        R(3, 2),
        R(99, 4),
        R(3, 2),
        R(-3, 4),
        R(-45, 8),
        R(-13, 2),
        R(1, 2),
        R(-9, 4),
    ),
)

THIRD_POINT = (
    -1,
    R(3, 2),
    R(13, 2),
    R(-9, 4),
    3,
    R(-3, 2),
    R(-99, 4),
    R(3, 2),
    R(3, 4),
    R(-45, 8),
    R(13, 2),
    R(1, 2),
    R(-9, 4),
)
"""The preimage his data does not carry, in his numbering.

His derivation restricts Thompson's twenty-four-variable form, and what
arrives there is what Thompson carried: two points. Alpoege's map has three,
and a chain from it brings all three. This one is this project's; the two above
are his.
"""

DIMENSION = 13
DEGREE = 3
DETERMINANT = 1

SAMPLE_POINTS = (
    tuple(R(k, 7) for k in range(1, 14)),
    tuple(R((-1) ** k * (k + 2), 3) for k in range(13)),
    (sp.Integer(0),) * 13,
)


def determinant_at(
    components: tuple[sp.Expr, ...],
    point: dict[sp.Symbol, sp.Expr],
) -> sp.Expr:
    """Return the Jacobian determinant evaluated at one point.

    At a point and not as a polynomial, for the reason
    ``reconstruct_alpoege13.py`` gives: thirteen variables over ``QQ`` are past
    what expression-level elimination manages, and the way past it is the
    implementation this script is independent of. A value other than one
    falsifies the claim; three points do not prove it.
    """
    variables = X[:DIMENSION]
    jacobian = sp.Matrix(
        [
            [sp.diff(component, variable).xreplace(point) for variable in variables]
            for component in components
        ]
    )

    return sp.expand(jacobian.det())


def transport(point: tuple[sp.Expr, ...]) -> tuple[sp.Expr, ...]:
    """Carry one preimage through the chain, in the chain's own numbering.

    Each step appends the negated factors it buys: two for a bought step, one
    for a shared one. The normalization acts on the left and moves only the
    image.
    """
    carried = list(point)
    for step in STEPS:
        carried += list(step.appended(dict(zip(X, carried, strict=False))))

    return tuple(carried)


def check(label: str, held: bool) -> bool:
    """Print one line and return what was checked."""
    print(f"  [{'ok ' if held else 'BAD'}] {label}")

    return held


def main() -> int:
    passed = []

    print("Macfarlane's map, as transcribed")
    passed.append(check(f"it has {DIMENSION} components", len(MACFARLANE) == DIMENSION))
    degree = max(sp.Poly(c, *X[:DIMENSION]).total_degree() for c in MACFARLANE)
    passed.append(check(f"its degree is {DEGREE}", degree == DEGREE))
    for trial, seed in enumerate(SAMPLE_POINTS):
        sample = dict(zip(X[:DIMENSION], seed, strict=True))
        passed.append(
            check(
                f"its Jacobian determinant is {DETERMINANT} at sample point {trial}",
                determinant_at(MACFARLANE, sample) == DETERMINANT,
            )
        )

    images = []
    for index, preimage in enumerate(MACFARLANE_POINTS):
        substitution = dict(zip(X[:DIMENSION], preimage, strict=True))
        images.append(tuple(sp.expand(c.xreplace(substitution)) for c in MACFARLANE))
        passed.append(
            check(
                f"point {index} is a preimage of the first point",
                images[-1] == tuple(sp.sympify(c) for c in MACFARLANE_POINTS[0]),
            )
        )
    passed.append(check("the two images agree", images[0] == images[1]))
    passed.append(
        check(
            "the two preimages differ",
            tuple(sp.sympify(c) for c in MACFARLANE_POINTS[0])
            != tuple(sp.sympify(c) for c in MACFARLANE_POINTS[1]),
        )
    )

    print("\nThe collision, carried through the chain")
    carried = [in_macfarlanes_order(transport(point)) for point in ALPOEGE_COLLISION]
    passed.append(check("it arrives with three preimages", len(set(carried)) == 3))
    for index, wanted in enumerate(MACFARLANE_POINTS):
        passed.append(
            check(
                f"the first two are his, point {index}",
                carried[index] == tuple(sp.sympify(c) for c in wanted),
            )
        )
    passed.append(
        check(
            "the third is the one his data does not carry",
            carried[2] == tuple(sp.sympify(c) for c in THIRD_POINT),
        )
    )
    substitution = dict(zip(X[:DIMENSION], carried[2], strict=True))
    passed.append(
        check(
            "and it is a preimage of the same image",
            tuple(sp.expand(c.xreplace(substitution)) for c in MACFARLANE)
            == tuple(sp.sympify(c) for c in MACFARLANE_POINTS[0]),
        )
    )

    print("\nThe chain from Alpoege's map")
    built = reduce_alpoege()
    passed.append(check(f"it lands in dimension {DIMENSION}", len(built) == DIMENSION))
    passed.append(
        check(
            f"its degree is {DEGREE}",
            max(sp.Poly(c, *X[:DIMENSION]).total_degree() for c in built) == DEGREE,
        )
    )
    passed.append(
        check(
            "reordered into his numbering, it is his map",
            in_macfarlanes_order(built) == MACFARLANE,
        )
    )

    print(f"\n{sum(passed)} of {len(passed)} checks passed.")

    return 0 if all(passed) else 1


if __name__ == "__main__":
    raise SystemExit(main())
