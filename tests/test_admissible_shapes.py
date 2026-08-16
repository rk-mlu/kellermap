"""Every operation against every admissible shape of a step.

The reason for this module lies in two findings, and neither came from a test.

``peeling.moves`` enumerated the slots with ``combinations`` and therefore
never offered two ``Carried`` slots on one coordinate, although BCW-6 has
admitted that since 0.3 and the constructor builds it. An external audit found
it. And ``BCWStep.transport`` appended one coordinate per ``Fresh`` slot rather
than per fresh generator, which fails for a step with one variable in both
slots. Assembling the chain to the nineteen-dimensional map found that one.

Both times every single obligation of the step type was checked, and nobody
asked whether the *remaining* parts admit the same thing. That is what the
tests here ask: for every shape ``BCWStep`` builds, ``verify``, ``transport``
and the enumerators have to handle it as well.

A new admissible shape belongs in ``SHAPES``. If a test then falls over, that
is the point.
"""

from collections.abc import Callable

import pytest
import sympy as sp

from kellermap import Collision, PolynomialMap, over_field
from kellermap.bcw import BCWStep, Carried, Fresh
from kellermap.peeling import moves, peel, undo
from kellermap.search import enumerate_candidates, search

x1, x2, x3 = sp.symbols("x1 x2 x3")
u, v = sp.symbols("u v")

Shape = tuple[str, Callable[[PolynomialMap], BCWStep]]

# A source in which everything can be built: coordinates 1 and 2 are carriers,
# and coordinate 0 carries enough for every shape to remove something.
SOURCE = over_field(
    PolynomialMap(
        (x1, x2, x3),
        (
            x1**2 + x2**2 * x3**2 + x2**2 * x3**4 + x2**4 + x3**6,
            x2 + x3**2,
            x3 + x2**2,
        ),
    )
)

# ``x1`` occurs only squared, so these two points share an image. A real
# collision and not a pair of points with a hopeful name.
POINTS = ((1, 0, 0), (-1, 0, 0))

# The same source, but with carrier components that are not zero at the
# collision point. A defect that no test found hung on exactly that:
# ``_moved_image`` dropped the coefficient, and while the carried image
# coordinates are zero this does not show, because the product vanishes anyway.
# An external audit reported it.
LOUD = over_field(
    PolynomialMap(
        (x1, x2, x3),
        (x1**2 + 3 * (x2 + 1) * (x3 + 2) + x2**4 + x3**6, x2 + 1, x3 + 2),
    )
)


def two_fresh(source: PolynomialMap, coefficient: sp.Expr) -> BCWStep:
    return BCWStep.build(source, 0, Fresh(x2**2, u), Fresh(x3**2, v), 1, coefficient)


def one_fresh(source: PolynomialMap, coefficient: sp.Expr) -> BCWStep:
    return BCWStep.build(source, 0, Carried(1), Fresh(x3**4, u), 1, coefficient)


def self_fresh(source: PolynomialMap, coefficient: sp.Expr) -> BCWStep:
    return BCWStep.build(source, 0, Fresh(x2**2, u), Fresh(x2**2, u), 1, coefficient)


def two_carried(source: PolynomialMap, coefficient: sp.Expr) -> BCWStep:
    return BCWStep.build(source, 0, Carried(1), Carried(2), 1, coefficient)


def one_carried_twice(source: PolynomialMap, coefficient: sp.Expr) -> BCWStep:
    return BCWStep.build(source, 0, Carried(2), Carried(2), 1, coefficient)


BUILDERS = {
    "two fresh": (two_fresh, 2),
    "one fresh and one carried": (one_fresh, 1),
    "one fresh in both slots": (self_fresh, 1),
    "two carried": (two_carried, 0),
    "one carried in both slots": (one_carried_twice, 0),
}

COEFFICIENTS = [sp.Integer(1), sp.Integer(-3), sp.Rational(1, 2)]

SHAPES = [
    (f"{name}, coefficient {coefficient}", builder, expected, coefficient)
    for name, (builder, expected) in BUILDERS.items()
    for coefficient in COEFFICIENTS
]

IDS = [shape[0] for shape in SHAPES]


@pytest.mark.parametrize(
    ("name", "builder", "expected", "coefficient"), SHAPES, ids=IDS
)
def test_the_constructor_builds_it(
    name: str, builder: Callable, expected: int, coefficient: sp.Expr
) -> None:
    """The list itself: what does not build here does not belong in ``SHAPES``."""
    step = builder(SOURCE, coefficient)

    assert step.m == expected
    assert step.coefficient == coefficient
    assert step.target.dimension == SOURCE.dimension + expected


@pytest.mark.parametrize(
    ("name", "builder", "expected", "coefficient"), SHAPES, ids=IDS
)
def test_verify_accepts_it(
    name: str, builder: Callable, expected: int, coefficient: sp.Expr
) -> None:
    """BCW-1 to BCW-12, on a step of this shape."""
    assert builder(SOURCE, coefficient).verify() is None


@pytest.mark.parametrize(
    ("name", "builder", "expected", "coefficient"), SHAPES, ids=IDS
)
def test_transport_carries_a_collision_through_it(
    name: str, builder: Callable, expected: int, coefficient: sp.Expr
) -> None:
    """The finding this module was named for.

    One coordinate per fresh generator and not per ``Fresh`` slot.
    """
    step = builder(SOURCE, coefficient)

    carried = step.transport(Collision.at(SOURCE, POINTS))

    assert all(len(point) == SOURCE.dimension + expected for point in carried.points)
    assert len(carried.image) == SOURCE.dimension + expected
    assert carried.verify(step.target) is None


@pytest.mark.parametrize(
    ("name", "builder", "expected", "coefficient"), SHAPES, ids=IDS
)
def test_the_factors_are_exhibited_for_it(
    name: str, builder: Callable, expected: int, coefficient: sp.Expr
) -> None:
    """Exhibit rather than assert: ``G`` and ``H`` are invertible.

    Both are products of elementary factors and therefore unimodular, and ``H``
    shifts one coordinate per fresh generator.
    """
    step = builder(SOURCE, coefficient)
    ring = step.G.ring
    # ``from_ring`` and not ``identity``: equality of ``PolynomialMap``
    # compares the coefficient domain as well, and the automorphisms live over
    # ``QQ``.
    identity = PolynomialMap.from_ring(ring, ring.gens)

    assert step.G.compose(step.G.inverse()).to_polynomial_map() == identity
    assert step.G.determinant() == 1
    assert step.H.determinant() == 1
    assert len(step.variables) == expected


@pytest.mark.parametrize(
    ("name", "builder", "expected", "coefficient"), SHAPES, ids=IDS
)
def test_the_peel_offers_it_back(
    name: str, builder: Callable, expected: int, coefficient: sp.Expr
) -> None:
    """The other finding. The enumerator has to offer what the type builds.

    ``moves`` never offered two ``Carried`` slots on one coordinate, because it
    used ``combinations`` instead of ``combinations_with_replacement``. A chain
    with such a step was therefore unreachable and not unfound.
    """
    step = builder(SOURCE, coefficient)
    offered = list(moves(step.target, spare=1))

    assert any(
        undo(step.target, candidate) == SOURCE
        for candidate in offered
        if len(candidate.dropped) == expected
    )


@pytest.mark.parametrize(
    ("name", "builder", "expected", "coefficient"), SHAPES, ids=IDS
)
def test_the_peel_recovers_a_chain_of_it(
    name: str, builder: Callable, expected: int, coefficient: sp.Expr
) -> None:
    """And the way back leads to a verified ``Reduction``."""
    step = builder(SOURCE, coefficient)

    outcome = peel(SOURCE, step.target, spare=1)

    assert outcome.reduction is not None
    assert outcome.reduction.verify() is None
    assert outcome.reduction.target.reordered(step.target.variables) == step.target


@pytest.mark.parametrize(
    ("name", "builder", "expected", "coefficient"), SHAPES, ids=IDS
)
def test_the_forward_enumerator_offers_the_ones_it_claims(
    name: str, builder: Callable, expected: int, coefficient: sp.Expr
) -> None:
    """What the forward enumerator cannot do it says here and not later.

    ``enumerate_candidates`` divides a displacement into two factors and knows
    no coefficient: SEA-9 and SEA-10 describe factors and not weights. A step
    with a coefficient other than one is therefore not enumerable going
    forward. That is a known boundary and not a defect. The peel solves for the
    coefficient, and the tests above show that it recovers every shape.
    """
    step = builder(SOURCE, coefficient)
    values = [
        sp.expand(step.target.components[index] - step.target.variables[index])
        for index in step.target.carrier_indices
    ]

    candidates = list(enumerate_candidates(SOURCE, values))

    assert isinstance(candidates, list)
    if coefficient == 1 and expected == 2:
        assert candidates


@pytest.mark.parametrize("coefficient", COEFFICIENTS)
def test_the_transported_image_is_scaled_by_the_coefficient(
    coefficient: sp.Expr,
) -> None:
    """``G`` scales the removed product, so it does so at the image too.

    The test that should have existed. The collision images of the tests until
    now had a zero in the carried coordinates, and a product with a zero
    remembers no factor. Here they are ``1`` and ``2``, so any forgotten
    coefficient shows.
    """
    collision = Collision.at(LOUD, POINTS)
    step = BCWStep.build(LOUD, 0, Carried(1), Carried(2), 1, coefficient)

    moved = step.transport(collision)

    assert collision.image[1] != 0
    assert collision.image[2] != 0
    assert moved.image[0] == sp.expand(
        collision.image[0] - coefficient * collision.image[1] * collision.image[2]
    )
    assert moved.verify(step.target) is None


@pytest.mark.parametrize("coefficient", COEFFICIENTS)
def test_a_fresh_slot_contributes_nothing_to_the_image(
    coefficient: sp.Expr,
) -> None:
    """And without a carried slot the coefficient does not change the image.

    The control: a fresh coordinate is padded with zero at the image, so the
    product is zero and no coefficient saves it. Without this half the test
    above would be consistent with a rule that is too general.
    """
    collision = Collision.at(LOUD, POINTS)
    step = BCWStep.build(LOUD, 0, Fresh(x2**2, u), Fresh(x3**2, v), 1, coefficient)

    moved = step.transport(collision)

    assert moved.image[: LOUD.dimension] == collision.image
    assert moved.image[LOUD.dimension :] == (0, 0)
    assert moved.verify(step.target) is None


@pytest.mark.parametrize("coefficient", COEFFICIENTS)
def test_the_forward_search_reports_no_result_for_a_weighted_chain(
    coefficient: sp.Expr,
) -> None:
    """SEA-14, and the difference from SEA-7.

    A weighted step lies outside the forward space, because a division has no
    place for a weight. That is not a deferred case but a searched space
    without the chain, so not a defect but a result. The peel finds it.
    """
    step = two_fresh(SOURCE, coefficient)
    pool = {
        step.target.variables[index]: sp.expand(
            step.target.components[index] - step.target.variables[index]
        )
        for index in step.target.carrier_indices
        if step.target.variables[index] not in SOURCE.variables
    }

    forwards = search(SOURCE, step.target, pool, budget=200)

    assert (forwards.reduction is not None) == (coefficient == 1)
    assert peel(SOURCE, step.target, spare=1).reduction is not None


def test_the_forward_search_reports_no_result_for_a_self_fresh_chain() -> None:
    """The same boundary for BCW-12.

    A candidate carries two factors and SEA-8 gives each of them a name from
    the pool, so one coordinate cannot fill both slots.
    """
    step = self_fresh(SOURCE, sp.Integer(1))
    pool = {u: sp.expand(x2**2)}

    assert search(SOURCE, step.target, pool, budget=200).reduction is None
    assert peel(SOURCE, step.target, spare=1).reduction is not None
