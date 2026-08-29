"""Reconstruction of the reduction from Alpoege's map to alpoege12, in SymPy.

This file does not depend on ``kellermap``. It stands to the twelve-dimensional
chain as ``reconstruct_alpoege13.py`` stands to the thirteen-dimensional one: a
second, independent rendering of the same formulas, so that the chain is
checked against something other than the implementation that produced it.

Here that matters more than usual. The chain was found by a search driver
outside this repository, which used the library through its public API, and its
result file ships a replay. A replay checks that the driver agrees with the
library; it cannot check that either of them is right. This script is what can.

Where this chain comes from
---------------------------

An external beam search over the untargeted enumeration, run on 28 August 2026
under a hard dimension bound of twelve. It examined 404117 states in about two
hours and returned ten steps. ``docs/references.md`` records the provenance and
what it is worth; the short form is that the driver is external to the library
and internal to the project, so the agreement below is a check that can fail
and not evidence about anybody else's mathematics.

The steps use one shape that the thirteen-dimensional chain does not, and it is
the reason this script needed writing rather than copying. Two of the ten take
*both* factors from coordinates that earlier steps already bought, so they
introduce no coordinate at all:

- step 2 subtracts ``3 * C4 * C4``, the square of one existing coordinate;
- step 4 subtracts ``9 * C6 * C4``, the product of two.

Proposition (3.1) buys both factors. Buying neither is at the far end of the
same extension that ``alpoege15`` uses when it buys one, and ``docs/api.md``
and ``docs/contracts.md`` mark it as an extension where it is used.

What it establishes, and what it does not
-----------------------------------------

Ten steps into dimension 12, against seven into 13 and eight into 15. Degree
three, determinant one, and Alpoege's three points transported through it:
three distinct preimages of one image. The map is in ``MA^1``, which the
thirteen-dimensional one is not.

It does not establish minimality, and it does not establish anything about
priority: eleven variables at degree three were published on 20 July 2026, and
``docs/references.md`` says so beside every place this number appears.

Run with::

    python scripts/reconstruct_alpoege12.py

The exit status is 0 if every check passes and 1 otherwise.
"""

from __future__ import annotations

from dataclasses import dataclass

import sympy as sp

X = sp.symbols("x1:13")
_1, _2, _3, _4, _5, _6, _7, _8, _9, _10, _11, _12 = X

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
# The step
#
# One shape covers all ten, which is not how ``reconstruct_alpoege13.py`` is
# written. That file has three dataclasses because its chain has three shapes
# and naming them separately says what each one is. This chain has four, and a
# fourth dataclass differing in one line would say less than the two slots do.
#
# A slot is what one of the two factors of Proposition (3.1) is made of. The
# paper has only ``Bought``: both factors are polynomials that the step buys a
# coordinate for. ``Carried`` names a coordinate that an earlier step already
# bought, whose component is then already ``X_j + P``, and taking a factor from
# there is an extension of the paper rather than the paper.
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Bought:
    """A factor the step buys, with the fresh coordinate that carries it."""

    value: sp.Expr
    fresh: sp.Symbol


@dataclass(frozen=True)
class Carried:
    """A factor an earlier step bought, named by its zero-based component."""

    index: int


Slot = Bought | Carried


@dataclass(frozen=True)
class Step:
    """One application of Proposition (3.1), with either factor possibly carried.

    ``G`` subtracts ``coefficient`` times the product of the two factors from
    component ``target``, and ``H`` appends one component for each bought slot.
    The factors are taken monic and the scalar rides in the step, which is what
    the enumerator produces and therefore what ``examples.alpoege12`` is.
    """

    target: int
    left: Slot
    right: Slot
    coefficient: sp.Expr = sp.Integer(1)

    def _factor(self, slot: Slot, components: tuple[sp.Expr, ...]) -> sp.Expr:
        """Return the polynomial the slot contributes to the product."""
        if isinstance(slot, Carried):
            return components[slot.index]

        return sp.expand(slot.fresh + slot.value)

    def apply(self, components: tuple[sp.Expr, ...]) -> tuple[sp.Expr, ...]:
        """Return the target of the step.

        The product is formed from the components *before* the step, and the
        bought coordinates are appended after it. Forming it from the modified
        component would be a different map, and one that is not an
        automorphism away from this one.
        """
        product = self._factor(self.left, components) * self._factor(
            self.right, components
        )

        head = list(components)
        head[self.target] = sp.expand(head[self.target] - self.coefficient * product)

        return tuple(head) + tuple(
            sp.expand(slot.fresh + slot.value)
            for slot in (self.left, self.right)
            if isinstance(slot, Bought)
        )

    def appended(self, point: dict[sp.Symbol, sp.Expr]) -> tuple[sp.Expr, ...]:
        """Return the coordinates a preimage gains, one per bought slot.

        A carried slot appends nothing, so a step that carries both factors
        leaves a point where it was.
        """
        return tuple(
            -sp.expand(slot.value.xreplace(point))
            for slot in (self.left, self.right)
            if isinstance(slot, Bought)
        )


# The ten steps. Steps 2 and 4 carry both factors and buy nothing; step 2
# squares one coordinate against itself.
STEPS: tuple[Step, ...] = (
    Step(2, Bought(_1 * _2**2, _4), Bought(_1**2 * _2 * _3, _5)),
    # x1*x2**2 has been component 3 since step 1, and serves as both factors.
    Step(2, Carried(3), Carried(3), sp.Integer(3)),
    Step(1, Bought(_1 * _2, _6), Carried(4), sp.Integer(3)),
    # x1*x2 has been component 5 since step 3.
    Step(1, Carried(5), Carried(3), sp.Integer(9)),
    Step(1, Carried(5), Bought(-3 * _1 * _3 * _6 + 6 * _1 * _3 - 9 * _2 * _6, _7)),
    Step(
        2,
        Carried(5),
        Bought(
            3 * _1 * _2 * _3 - _1 * _3 * _4 + 7 * _2**2 - 6 * _2 * _4 - _2 * _5,
            _8,
        ),
    ),
    Step(4, Bought(_1 * _3, _9), Carried(5)),
    # x1*x3 has been component 8 since step 7.
    Step(1, Bought(_6**2, _10), Carried(8), sp.Integer(3)),
    Step(2, Carried(8), Bought(-3 * _2 * _6 + _4 * _6, _11)),
    Step(0, Carried(8), Bought(_1**2, _12), R(-1, 2)),
)


def reduce_alpoege() -> tuple[sp.Expr, ...]:
    """Run the whole chain: normalization, then the ten steps."""
    components = normalize(ALPOEGE)
    for step in STEPS:
        components = step.apply(components)

    return components


def transport(point: tuple[sp.Expr, ...]) -> tuple[sp.Expr, ...]:
    """Carry one preimage through the chain.

    Each step appends the negated value of every factor it buys: two for the
    first step, one for six of them, none for the two that carry both. The
    normalization acts on the left and moves only the image.
    """
    carried = list(point)
    for step in STEPS:
        carried += list(step.appended(dict(zip(X, carried, strict=False))))

    return tuple(carried)


# --------------------------------------------------------------------------
# What the chain has to come out as
# --------------------------------------------------------------------------

DIMENSION = 12
DEGREE = 3
DETERMINANT = 1
ORDER = 2

IMAGE = (sp.Integer(0), sp.Integer(0), R(-1, 4)) + (sp.Integer(0),) * 9

POINTS = (
    (0, 0, R(-1, 4), 0, 0, 0, 0, 0, 0, 0, 0, 0),
    (
        1,
        R(-3, 2),
        R(13, 2),
        R(-9, 4),
        R(39, 4),
        R(3, 2),
        -30,
        R(9, 2),
        R(-13, 2),
        R(-9, 4),
        R(-27, 8),
        -1,
    ),
    (
        -1,
        R(3, 2),
        R(13, 2),
        R(9, 4),
        R(-39, 4),
        R(3, 2),
        30,
        R(9, 2),
        R(13, 2),
        R(-9, 4),
        R(27, 8),
        -1,
    ),
)


SAMPLE_POINTS = (
    tuple(R(k, 7) for k in range(1, 13)),
    tuple(R((-1) ** k * (k + 2), 3) for k in range(12)),
    (sp.Integer(0),) * 12,
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

    At a point and not as a polynomial, for the reason
    ``reconstruct_alpoege13.py`` gives: the technique that makes the polynomial
    identity tractable is the implementation this script exists to be
    independent of. A determinant that is constantly one evaluates to one
    everywhere, so any other value falsifies the claim, while agreement at
    finitely many points does not prove it.
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
    passed.append(
        check(
            "it takes ten steps, of which two buy nothing",
            len(STEPS) == 10
            and sum(
                1
                for step in STEPS
                if not isinstance(step.left, Bought)
                and not isinstance(step.right, Bought)
            )
            == 2,
        )
    )

    displacement = [
        sp.expand(component - variable)
        for component, variable in zip(components, variables, strict=True)
    ]
    order = min(
        min(sum(monomial) for monomial in sp.Poly(p, *variables).monoms())
        for p in displacement
        if p != 0
    )
    passed.append(
        check(
            f"its displacement has order {ORDER}, so the map is in MA^1",
            order == ORDER,
        )
    )

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
