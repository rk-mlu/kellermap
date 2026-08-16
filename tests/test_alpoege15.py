"""alpoege15: a cubic Keller map in dimension 15.

Not an example from elsewhere but this project's own reduction. It arises from
the seventeen-dimensional one by having two steps reuse a carrier that an
earlier step already created: BCW17 creates ``x1**2`` twice, in ``x5`` and
``x17``, and ``x1*x2`` twice as well, in ``x8`` and ``x14``. Avoiding the
duplication saves one variable each time.

Since milestone 0.3 the map is derived and no longer asserted: a ``Reduction``
of eight steps, verified step by step, which carries the collision along. Two
of the seven BCW steps have ``m = 1``.

What is evidence here and what is not
-------------------------------------
Unlike for BCW17 the endpoint is not an external fact here. The fixed
components further down come from the same hand computation that produced the
chain, and ``scripts/reconstruct_alpoege15.py`` carries it out in plain SymPy.
That the last step is given its target therefore shows the agreement of two
implementations of the same formulas, and not agreement with a published map.

The intermediate maps are ``CONSTRUCTED``, and under RED-7 the chain carries
the weaker provenance.

On the provenance, and on what the number 15 means and does not mean, see
``docs/references.md``.
"""

import pytest
import sympy as sp

from kellermap import (
    Collision,
    PolynomialMap,
    Provenance,
    Reduction,
    ReductionContext,
    VerificationError,
    enumerate_candidates,
    examples,
    over_field,
    search,
)
from kellermap.bcw import BCWStep, Carried, Fresh
from kellermap.reduction import LinearStep
from tests.test_bcw17 import BCW17_COLLISION
from tests.test_bcw17 import COMPONENTS as BCW17_COMPONENTS

ALPOEGE15 = examples.alpoege15()
X = ALPOEGE15.variables
COMPONENTS = ALPOEGE15.components
COLLISION = examples.alpoege15_collision().points
IMAGE = examples.alpoege15_collision().image
ALPOEGE_COLLISION = examples.alpoege_collision().points

_1, _2, _3, _4, _5, _6, _7, _8, _9, _10, _11, _12, _13, _14, _15 = X

R = sp.Rational


# The twelve stabilisation coordinates x4 to x15.
CARRIER_INDICES = tuple(range(3, 15))

ALPOEGE15 = PolynomialMap(X, COMPONENTS)

CARRIERS = {index: sp.expand(COMPONENTS[index] - X[index]) for index in CARRIER_INDICES}


# --------------------------------------------------------------------------
# The map itself
# --------------------------------------------------------------------------


def test_dimension_and_degree() -> None:
    assert ALPOEGE15.dimension == 15
    assert ALPOEGE15.degree() == 3


def test_the_determinant_is_one() -> None:
    """Constant, so a Keller map, and normalised as BCW17 is."""
    assert ALPOEGE15.determinant() == 1


def test_reordering_the_generators_changes_no_value() -> None:
    """SEA-4 on a map whose reordering is known.

    The search in 0.4 builds a chain whose generators stand in the order they
    were introduced, while a published map lists the same generators
    differently. Reordering is presentation and not a step, so it has to change
    exactly nothing about the value. Computed here in dimension 15, where a
    defect in the encoding of monomials no longer passes by accident.
    """
    shuffled = X[3:] + X[:3]

    moved = ALPOEGE15.reordered(shuffled)

    assert moved.variables == shuffled
    assert moved != ALPOEGE15
    assert moved.reordered(X) == ALPOEGE15
    assert moved.determinant() == ALPOEGE15.determinant()
    assert moved.degree() == ALPOEGE15.degree()
    assert moved.filtration_degree() == ALPOEGE15.filtration_degree()


def test_it_lies_in_MA0_but_not_in_MA1() -> None:  # noqa: N802
    """For the same reason as BCW17: two steps reach only EA^0."""
    assert ALPOEGE15.is_in_MA(0)
    assert not ALPOEGE15.is_in_MA(1)


def test_the_carrier_block_is_the_stabilization() -> None:
    assert ALPOEGE15.carrier_indices == CARRIER_INDICES


# --------------------------------------------------------------------------
# The collision
# --------------------------------------------------------------------------


def test_alpoege15_is_not_injective() -> None:
    """The substance: three distinct preimages of one point."""
    collision = Collision(COLLISION, IMAGE)

    assert collision.verify(ALPOEGE15) is None
    assert len(collision) == 3
    assert collision.dimension == 15


def test_the_image_is_the_one_bcw17_carries() -> None:
    """The same normalisation, so the same image, padded less far."""
    assert Collision.at(ALPOEGE15, COLLISION).image == tuple(map(sp.nsimplify, IMAGE))


def test_the_points_agree_with_bcw17_where_the_chains_agree() -> None:
    """The first five steps are unchanged, so the first 13 coordinates are.

    Only the shared steps 6 and 7 create different variables. Everything before
    them is the same computation character for character.
    """
    ours = {tuple(map(sp.nsimplify, point))[:13] for point in COLLISION}
    theirs = {tuple(map(sp.nsimplify, point))[:13] for point in BCW17_COLLISION}

    assert ours == theirs


# --------------------------------------------------------------------------
# The connection with BCW17
# --------------------------------------------------------------------------


def test_bcw17_buys_two_values_twice() -> None:
    """The finding the map came out of."""
    bcw17_carriers = [
        sp.expand(BCW17_COMPONENTS[index] - sp.Symbol(f"x{index + 1}"))
        for index in range(3, 17)
    ]
    doubled = [
        value
        for value in {sp.expand(_1**2), sp.expand(_1 * _2)}
        if bcw17_carriers.count(value) == 2
    ]

    assert len(doubled) == 2


def test_alpoege15_buys_each_value_once() -> None:
    """And the gain: no carrier value occurs twice here."""
    values = [sp.expand(value) for value in CARRIERS.values()]

    assert len(values) == len(set(values)) == 12


def test_eleven_components_are_untouched() -> None:
    """What the shared steps do not touch stays verbatim.

    Components 3, 11, 14 and 15 change: the first two because a shared step has
    them as its target, the last two because they are the carriers that are
    named differently in the process.
    """
    unchanged = [
        index
        for index in range(13)
        if sp.expand(COMPONENTS[index] - BCW17_COMPONENTS[index]) == 0
    ]

    assert unchanged == [0, 1, 3, 4, 5, 6, 7, 8, 9, 11, 12]


def test_two_dimensions_below_bcw17() -> None:
    assert len(BCW17_COMPONENTS) - len(COMPONENTS) == 2


# --------------------------------------------------------------------------
# Derivation: the chain from Alpoege to here
# --------------------------------------------------------------------------


# The seven applications of Proposition (3.1): the target component
# (zero-based), the two factor slots, and the EA level. A slot is either
# ("fresh", P), whose variable the ReductionContext hands out, or
# ("carried", j) for the coordinate j that already carries the factor.
STEPS = (
    (0, ("fresh", -_1 * _3 / 2), ("fresh", _1**2), 1),
    (1, ("fresh", 3 * _1**2 * _2), ("fresh", _1 * _2 * _3 + 3 * _2**2), 1),
    (1, ("fresh", _1 * _2), ("fresh", 6 * _1 * _3 - 3 * _1 * _7 - _3 * _6), 1),
    (
        2,
        ("fresh", _1 * _2**2),
        ("fresh", _1**2 * _2 * _3 + 3 * _1 * _2**2 + 3 * _1 * _3 + 7 * _2),
        0,
    ),
    (2, ("fresh", _1 * _2 * _10), ("fresh", -_1 * _3 - 3 * _2), 0),
    # x1*x2 has been component 8 since step 3, so index 7.
    (2, ("carried", 7), ("fresh", -_10 * _13 - _2 * _11), 1),
    # x1**2 has been component 5 since step 1, so index 4.
    (10, ("carried", 4), ("fresh", _2 * _3), 1),
)


@pytest.fixture(scope="module")
def alpoege() -> PolynomialMap:
    """Over QQ, because the normalisation needs a reciprocal at once."""
    return over_field(examples.alpoege())


@pytest.fixture(scope="module")
def reduction(alpoege: PolynomialMap) -> Reduction:
    """The complete chain, with a supplied target in the last step."""
    context = ReductionContext()
    normalization = LinearStep.normalize(alpoege)
    steps: list[LinearStep | BCWStep] = [normalization]
    current = normalization.target

    for position, (index, left, right, level) in enumerate(STEPS):
        specs = (left, right)
        fresh = context.variables(
            current.ring, sum(kind == "fresh" for kind, _ in specs)
        )
        allocated = iter(fresh)
        slots = tuple(
            Fresh(value, next(allocated)) if kind == "fresh" else Carried(int(value))
            for kind, value in specs
        )
        last = position == len(STEPS) - 1
        step = (
            BCWStep(current, ALPOEGE15, index, *slots, level)
            if last
            else BCWStep.build(current, index, *slots, level)
        )
        steps.append(step)
        current = step.target

    return Reduction(steps)


def test_the_reduction_verifies(reduction: Reduction) -> None:
    """Eight steps, each checked on its own, and every seam between them."""
    assert reduction.verify() is None
    assert len(reduction) == 8


def test_the_reduction_reaches_alpoege15(reduction: Reduction) -> None:
    assert reduction.target == ALPOEGE15


def test_two_steps_reuse_a_carrier(reduction: Reduction) -> None:
    """The reason for the dimension: m = 1 twice instead of m = 2 twice."""
    levels = [step.m for step in reduction if isinstance(step, BCWStep)]

    assert levels == [2, 2, 2, 2, 2, 1, 1]
    assert sum(levels) == 12


def test_the_dimensions_and_degrees(reduction: Reduction) -> None:
    """3 to 15 instead of to 17, degree 7 to 3."""
    assert reduction.dimensions() == (3, 3, 5, 7, 9, 11, 13, 14, 15)
    assert reduction.degrees() == (7, 7, 7, 7, 7, 5, 4, 4, 3)


def test_the_context_names_x4_to_x15(reduction: Reduction) -> None:
    allocated = tuple(
        variable
        for step in reduction
        if isinstance(step, BCWStep)
        for variable in step.variables
    )

    assert allocated == X[3:]


def test_the_reused_coordinates_are_the_ones_bcw17_duplicates(
    reduction: Reduction,
) -> None:
    """Exactly the two values BCW17 creates twice."""
    reused = [
        (step.left, step.P)
        for step in reduction
        if isinstance(step, BCWStep) and isinstance(step.left, Carried)
    ]

    assert reused == [(Carried(7), _1 * _2), (Carried(4), _1**2)]


def test_the_collision_is_transported(
    reduction: Reduction, alpoege: PolynomialMap
) -> None:
    """Three points in k^3 become three points in k^15."""
    carried = reduction.transport(Collision.at(alpoege, ALPOEGE_COLLISION))

    assert carried == Collision(COLLISION, IMAGE)


def test_the_image_does_not_move(reduction: Reduction, alpoege: PolynomialMap) -> None:
    """No step has m = 0, so the image stays but for zeros."""
    carried = reduction.transport(Collision.at(alpoege, ALPOEGE_COLLISION))

    assert carried.image[:3] == (0, 0, R(-1, 4))
    assert set(carried.image[3:]) == {sp.Integer(0)}


def test_the_provenance_is_constructed(reduction: Reduction) -> None:
    """The endpoint is not an external fact, unlike for BCW17."""
    assert reduction.provenance is Provenance.CONSTRUCTED
    assert reduction[-1].provenance is Provenance.SUPPLIED


def test_a_perturbed_target_would_be_caught(reduction: Reduction) -> None:
    """A control: the last step really checks something."""
    last = reduction[-1]
    perturbed = PolynomialMap(X, (COMPONENTS[0] + _4 * _5,) + COMPONENTS[1:])
    broken = BCWStep(last.source, perturbed, last.index, last.left, last.right)

    with pytest.raises(VerificationError) as failure:
        Reduction([*list(reduction[:-1]), broken]).verify()

    assert failure.value.obligation == "BCW-1"
    assert failure.value.step == 7


def test_the_enumerator_contains_every_step_of_this_chain(
    reduction: Reduction,
) -> None:
    """The control for the candidate enumerator, on known steps.

    The pool comes from the target map: the values its carrier coordinates
    hold. For every step of the chain the enumerator has to offer, on the map
    before it, a candidate with the same target component and the same two
    factors, and the derived EA level has to be that of the step.

    An enumerator that passes over a step known to exist is incomplete in a way
    that a failure of the search alone would not show.
    """
    final = reduction.target
    pool = [
        sp.expand(final.components[index] - final.variables[index])
        for index in final.carrier_indices
    ]

    steps = [step for step in reduction.steps if isinstance(step, BCWStep)]
    assert len(steps) == 7

    for position, step in enumerate(steps, start=1):
        wanted = sorted(str(sp.expand(value)) for value in (step.P, step.Q))
        found = [
            candidate
            for candidate in enumerate_candidates(step.source, pool)
            if candidate.index == step.index
            and sorted(str(sp.expand(v)) for v in candidate.values(step.source))
            == wanted
        ]

        assert found, f"step {position} is missing from the enumeration"
        assert found[0].filtration_level(step.source) == step.filtration_level


@pytest.mark.slow
def test_the_search_recovers_a_chain_to_this_map(reduction: Reduction) -> None:
    """The acceptance condition for the search, on a known map.

    The source is Alpoege's normalised map, the target is ALPOEGE15, and the
    pool holds the values its carrier coordinates hold, with one addition that
    makes the condition under SEA-8 visible. Step seven aims at component 10
    and rewrites it, so the value this coordinate was introduced with no longer
    stands in the target map. Without it the chain is unreachable for the
    search and not merely unfound.

    What is found is *a* chain and not *the* chain. Its sequence of degrees
    differs from the recorded one; see "No optimality of the sequence" in
    ``docs/contracts.md``.

    ``rewrites=0``, because this test is about the rule that every fresh slot
    carries a pool value. With the relaxation of SEA-13 the same search does
    not find the chain within 400 maps. That is measured, and it is why the
    relaxation is a named exception and not a default.
    """
    source = reduction.steps[0].target
    pool = {
        X[index]: sp.expand(COMPONENTS[index] - X[index])
        for index in ALPOEGE15.carrier_indices
    }
    pool[X[10]] = sp.expand(STEPS[3][2][1])

    outcome = search(source, ALPOEGE15, pool, budget=2000, rewrites=0)

    assert outcome.reduction is not None
    assert outcome.reduction.verify() is None
    assert outcome.reduction.source == source
    assert outcome.reduction.target.reordered(ALPOEGE15.variables) == ALPOEGE15


@pytest.mark.slow
def test_without_that_value_the_chain_is_out_of_reach(reduction: Reduction) -> None:
    """A negative control for the condition under SEA-8.

    The same run with the value the target map really carries. The enumerator
    cannot offer the step then, and the failure says nothing about the
    existence of the chain, which is SEA-6.
    """
    source = reduction.steps[0].target
    pool = {
        X[index]: sp.expand(COMPONENTS[index] - X[index])
        for index in ALPOEGE15.carrier_indices
    }

    outcome = search(source, ALPOEGE15, pool, budget=400, rewrites=0)

    assert outcome.reduction is None
