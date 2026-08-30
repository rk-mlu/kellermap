"""Reconstruction of a chain from Alpoege's map to spacerat11, in SymPy.

This file does not depend on ``kellermap``. It stands to the published
eleven-variable map as ``reconstruct_macfarlane13.py`` stands to Macfarlane's:
the map came from outside, a backward search found a chain of this library's
steps that reaches it, and this script recomputes both without the library.

Where the chain comes from
--------------------------

``peel`` was run at the pair and returned six steps, examining seven maps in
about a third of a second. The steps are transcribed below. What that
establishes is narrow and worth stating twice: ``peel`` is given its target, so
nothing here was found. The map is Spacerat's, printed as ``Phi`` in Section 6
of arXiv:2608.05392v1; what the six steps show is that it lies in the space of
Bass-Connell-Wright chains from Alpoege's map, which was not obvious from the
way it was derived.

It also lies outside the space this project's forward search offers. Of the six
steps, none matches any candidate ``untargeted_candidates`` produces at the map
before it. ``docs/references.md`` records the comparison and the control it was
validated against, and the shape of the answer is the same as for
``macfarlane13``, where two of seven matched.

The chain runs from ``alpoege()`` and not from its normalization, which is
forced rather than chosen. A ``BCWStep`` preserves the Jacobian determinant.
Alpoege's map has determinant ``-2`` and so does ``Phi``; the normalized map
has determinant one, and no chain crosses between them.

Three shapes of step appear, and the second is the interesting one:

- steps 1 and 5 buy both factors, which is Proposition (3.1) as written;
- step 2 buys one coordinate and uses it for *both* factors, so it subtracts a
  square. Reusing a carrier this way is an extension of the paper, marked as
  one wherever this project uses it;
- steps 3, 4 and 6 take one factor from a coordinate an earlier step bought.

What it establishes, and what it does not
-----------------------------------------

Six steps into dimension 11 at degree three, against ten for ``alpoege12`` and
seven for ``alpoege13``. Determinant ``-2``, and Alpoege's three points carried
through to the three the paper prints.

It establishes no priority and no minimality. Eleven is the smallest dimension
at degree three this project knows of, and ``docs/references.md`` says where it
comes from and what a comparison with it does and does not settle.

Run with::

    python scripts/reconstruct_spacerat11.py

The exit status is 0 if every check passes and 1 otherwise.
"""

from __future__ import annotations

from dataclasses import dataclass

import sympy as sp

X = sp.symbols("x1:12")
_1, _2, _3, _4, _5, _6, _7, _8, _9, _10, _11 = X

R = sp.Rational


# --------------------------------------------------------------------------
# Alpoege's map
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


# --------------------------------------------------------------------------
# The step
#
# One shape with two slots, as in ``reconstruct_alpoege12.py``. A slot is a
# factor of Proposition (3.1): either a polynomial the step buys a coordinate
# for, or a coordinate an earlier step already bought.
#
# The one thing this chain has that the twelve-dimensional one does not is a
# step whose two bought slots name the *same* coordinate. The paper buys two;
# naming one twice is an extension, and ``Bought`` carries the name so that a
# reader sees which is which.
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Bought:
    """A factor the step buys, with the coordinate that carries it."""

    value: sp.Expr
    fresh: sp.Symbol


@dataclass(frozen=True)
class Carried:
    """A factor an earlier step bought, named by its zero-based component."""

    index: int


Slot = Bought | Carried


@dataclass(frozen=True)
class Step:
    """One application of Proposition (3.1)."""

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

        The product is formed from the components before the step, and the
        bought coordinates are appended after it. Where both slots name one
        coordinate, one component is appended and not two.
        """
        product = self._factor(self.left, components) * self._factor(
            self.right, components
        )

        head = list(components)
        head[self.target] = sp.expand(head[self.target] - self.coefficient * product)

        appended: list[sp.Expr] = []
        for slot in (self.left, self.right):
            if isinstance(slot, Bought):
                component = sp.expand(slot.fresh + slot.value)
                if component not in appended:
                    appended.append(component)

        return tuple(head) + tuple(appended)

    def appended(self, point: dict[sp.Symbol, sp.Expr]) -> tuple[sp.Expr, ...]:
        """Return the coordinates a preimage gains, one per bought coordinate."""
        values: list[sp.Expr] = []
        names: list[sp.Symbol] = []
        for slot in (self.left, self.right):
            if isinstance(slot, Bought) and slot.fresh not in names:
                names.append(slot.fresh)
                values.append(-sp.expand(slot.value.xreplace(point)))

        return tuple(values)


# The six steps. Step 2 names x7 in both slots, so it subtracts the square of
# one coordinate and appends one component.
STEPS: tuple[Step, ...] = (
    Step(
        0,
        Bought(_1**2 * _2**2, _4),
        Bought(_1 * _2 * _3 + 3 * _2**2 + 2 * _3, _6),
    ),
    Step(3, Bought(-_1 * _2, _7), Bought(-_1 * _2, _7)),
    # x1*x2*x3 + 3*x2**2 + 2*x3 has been component 4 since step 1.
    Step(1, Carried(4), Bought(3 * _1**2 * _2, _5)),
    # -x1*x2 has been component 5 since step 2.
    Step(1, Carried(5), Bought(3 * _1 * _6 + _3 * _5, _8)),
    Step(2, Bought(-(_1**2), _10), Bought(_1 * _3, _11)),
    Step(
        0,
        Carried(5),
        Bought(
            -_1 * _2 * _3 + _1 * _2 * _6 - 7 * _2**2 + _3 * _4 - _3 * _7 + _6 * _7,
            _9,
        ),
    ),
)


def variables() -> tuple[sp.Symbol, ...]:
    """Return the coordinates in the order the chain introduces them.

    Not ``x1`` to ``x11``. The names are the published map's, and the chain
    reaches its coordinates in another order, so component ``4`` belongs to
    ``x6`` and not to ``x5``. Deriving the order from the steps rather than
    writing it down keeps the two from drifting apart, and the reordering at
    the end of this file is where the difference is settled.
    """
    names = list(X[:3])
    for step in STEPS:
        for slot in (step.left, step.right):
            if isinstance(slot, Bought) and slot.fresh not in names:
                names.append(slot.fresh)

    return tuple(names)


def reduce_alpoege() -> tuple[sp.Expr, ...]:
    """Run the six steps on Alpoege's map."""
    components = ALPOEGE
    for step in STEPS:
        components = step.apply(components)

    return components


def transport(point: tuple[sp.Expr, ...]) -> tuple[sp.Expr, ...]:
    """Carry one preimage through the chain."""
    carried = list(point)
    for step in STEPS:
        carried += list(step.appended(dict(zip(variables(), carried, strict=False))))

    return tuple(carried)


# --------------------------------------------------------------------------
# The published map, and what the chain has to come out as
# --------------------------------------------------------------------------

DIMENSION = 11
DEGREE = 3
DETERMINANT = -2

# Section 6 of arXiv:2608.05392v1, printed there as ``Phi`` and licensed
# CC BY 4.0, https://creativecommons.org/licenses/by/4.0/. Changes: the
# generators are renamed and the components reordered to the order the chain
# introduces them in. The formulas are not altered. The gist the paper cites
# for the calculation carries no licence, so every value here comes from the
# paper.
PUBLISHED = (
    3 * _1 * _2 * _3
    + _1 * _2 * _9
    - 3 * _2**2 * _4
    + 7 * _2**2 * _7
    + 4 * _2**2
    - _3 * _4 * _7
    - 2 * _3 * _4
    + _3 * _7**2
    + _3
    - _4 * _6
    - _6 * _7**2
    - _7 * _9,
    12 * _1 * _2**2
    + _1 * _2 * _8
    + 3 * _1 * _3
    - 3 * _1 * _6 * _7
    - 3 * _2**2 * _5
    + _2
    - _3 * _5 * _7
    - 2 * _3 * _5
    - _5 * _6
    - _7 * _8,
    _1**2 * _11 - 3 * _1**2 * _2 - _1 * _10 * _3 + 2 * _1 - _10 * _11,
    2 * _1 * _2 * _7 + _4 - _7**2,
    3 * _1**2 * _2 + _5,
    _1 * _2 * _3 + 3 * _2**2 + 2 * _3 + _6,
    -_1 * _2 + _7,
    3 * _1 * _6 + _3 * _5 + _8,
    -_1 * _2 * _3 + _1 * _2 * _6 - 7 * _2**2 + _3 * _4 - _3 * _7 + _6 * _7 + _9,
    -(_1**2) + _10,
    _1 * _3 + _11,
)

PUBLISHED_POINTS = (
    (0, 0, R(-1, 4), 0, 0, R(1, 2), 0, 0, 0, 0, 0),
    (
        1,
        R(-3, 2),
        R(13, 2),
        R(-9, 4),
        R(9, 2),
        -10,
        R(-3, 2),
        R(3, 4),
        R(-153, 8),
        1,
        R(-13, 2),
    ),
    (
        -1,
        R(3, 2),
        R(13, 2),
        R(-9, 4),
        R(-9, 2),
        -10,
        R(-3, 2),
        R(-3, 4),
        R(-153, 8),
        1,
        R(13, 2),
    ),
)

SAMPLE_POINTS = (
    tuple(R(k, 5) for k in range(1, 12)),
    tuple(R((-1) ** k * (k + 3), 2) for k in range(11)),
    (sp.Integer(0),) * 11,
)
"""Where the Jacobian determinant is evaluated. The origin is one of them."""


def determinant_at(
    components: tuple[sp.Expr, ...],
    variables: tuple[sp.Symbol, ...],
    point: dict[sp.Symbol, sp.Expr],
) -> sp.Expr:
    """Return the Jacobian determinant at one point.

    At a point and not as a polynomial, for the reason the other
    reconstructions give: the technique that makes the polynomial identity
    tractable is the implementation this script exists to be independent of.
    Any value other than ``-2`` falsifies the claim; agreement at finitely many
    points does not prove it.
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
    passed = []

    print("The chain")
    passed.append(
        check(f"it lands in dimension {DIMENSION}", len(components) == DIMENSION)
    )
    degree = max(sp.Poly(c, *X).total_degree() for c in components)
    passed.append(check(f"its degree is {DEGREE}", degree == DEGREE))
    passed.append(
        check(
            "it takes six steps, one of which names a coordinate twice",
            len(STEPS) == 6
            and sum(
                1
                for step in STEPS
                if isinstance(step.left, Bought)
                and isinstance(step.right, Bought)
                and step.left.fresh == step.right.fresh
            )
            == 1,
        )
    )

    order = variables()
    for trial, seed in enumerate(SAMPLE_POINTS):
        sample = dict(zip(order, seed, strict=True))
        passed.append(
            check(
                f"its Jacobian determinant is {DETERMINANT} at sample point {trial}",
                determinant_at(components, order, sample) == DETERMINANT,
            )
        )

    print("\nAgainst the published map")
    positions = tuple(order.index(name) for name in X)
    reordered = tuple(components[position] for position in positions)
    for index, (reached, printed) in enumerate(zip(reordered, PUBLISHED, strict=True)):
        passed.append(
            check(
                f"component {index} agrees with Section 6",
                sp.expand(reached - printed) == 0,
            )
        )

    print("\nThe collision")
    images = []
    for index, preimage in enumerate(ALPOEGE_COLLISION):
        carried = transport(preimage)
        passed.append(
            check(
                f"point {index} carries {DIMENSION} coordinates",
                len(carried) == DIMENSION,
            )
        )
        substitution = dict(zip(order, carried, strict=True))
        images.append(tuple(sp.expand(c.xreplace(substitution)) for c in components))

    passed.append(check("the three images agree", images[0] == images[1] == images[2]))
    passed.append(
        check(
            "the three preimages are distinct",
            len({tuple(transport(p)) for p in ALPOEGE_COLLISION}) == 3,
        )
    )

    carried_points = {
        tuple(transport(preimage)[position] for position in positions)
        for preimage in ALPOEGE_COLLISION
    }
    printed_points = {tuple(sp.sympify(v) for v in point) for point in PUBLISHED_POINTS}
    passed.append(
        check(
            "the three carried points are the three the paper prints",
            carried_points == printed_points,
        )
    )

    # A control on the source. Alpoege's three points have to collide before
    # any of this, or the agreement above would be about nothing.
    passed.append(
        check(
            "Alpoege's three points are a collision to begin with",
            len(
                {
                    tuple(
                        sp.expand(c.xreplace(dict(zip(X[:3], p, strict=True))))
                        for c in ALPOEGE
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
