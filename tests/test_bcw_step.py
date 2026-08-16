"""Proposition (3.1) as a certificate.

The weight lies on BCW-1: against a *supplied* target the check has to be able
to fail, otherwise it checks nothing. The unit tests use a small map for that,
whose step can be written down by hand.

At the end stands the first step of the reference reduction with its target
written out. Its first component is already the first component of BCW17,
because no later step touches it again.
"""

import math
import re

import pytest
import sympy as sp

from kellermap import (
    Collision,
    PolynomialMap,
    Provenance,
    Reduction,
    Step,
    VerificationError,
    examples,
    over_field,
)
from kellermap.bcw import BCWStep, Carried, Fresh
from kellermap.reduction import LinearStep

x1, x2, x3, x4, x5, x6, x7 = sp.symbols("x1 x2 x3 x4 x5 x6 x7")

# F = (x1 + x2^2 x3^2, x2, x3). The leading term x2^2 x3^2 of the first
# component factorizes as P * Q with P = x2^2 and Q = x3^2.
SIMPLE = over_field(examples.factorable_shear())

P = x2**2
Q = x3**2
FRESH = (Fresh(P, x4), Fresh(Q, x5))

# G o F^[2] o H, by hand: (F_1 - P Q) - x4 Q - P x5 - x4 x5.
SIMPLE_TARGET = PolynomialMap(
    (x1, x2, x3, x4, x5),
    (
        x1 - x4 * x3**2 - x2**2 * x5 - x4 * x5,
        x2,
        x3,
        x4 + x2**2,
        x5 + x3**2,
    ),
)


@pytest.fixture
def step() -> BCWStep:
    return BCWStep(SIMPLE, over_field(SIMPLE_TARGET), 0, *FRESH)


# --------------------------------------------------------------------------
# Construction
# --------------------------------------------------------------------------


def test_a_step_satisfies_the_protocol(step: BCWStep) -> None:
    assert isinstance(step, Step)


def test_the_source_and_target_must_be_maps() -> None:
    with pytest.raises(TypeError, match="source must be"):
        BCWStep(SIMPLE.components, over_field(SIMPLE_TARGET), 0, *FRESH)

    with pytest.raises(TypeError, match="target must be"):
        BCWStep(SIMPLE, SIMPLE_TARGET.components, 0, *FRESH)


def test_the_fresh_variables_must_be_symbols() -> None:
    with pytest.raises(TypeError, match="SymPy symbol"):
        BCWStep(
            SIMPLE, over_field(SIMPLE_TARGET), 0, Fresh(P, x4), Fresh(Q, sp.Integer(5))
        )


def test_the_index_must_address_a_component() -> None:
    with pytest.raises(ValueError, match="out of range"):
        BCWStep(SIMPLE, over_field(SIMPLE_TARGET), 3, *FRESH)


def test_the_index_must_be_an_integer() -> None:
    with pytest.raises(TypeError, match="must be an integer"):
        BCWStep(SIMPLE, over_field(SIMPLE_TARGET), True, *FRESH)


def test_a_step_needs_two_slots() -> None:
    with pytest.raises(TypeError):
        BCWStep(SIMPLE, over_field(SIMPLE_TARGET), 0, Fresh(P, x4))  # type: ignore[call-arg]


def test_a_slot_must_be_a_factor() -> None:
    with pytest.raises(TypeError, match="Fresh or a Carried"):
        BCWStep(SIMPLE, over_field(SIMPLE_TARGET), 0, P, Fresh(Q, x5))  # type: ignore[arg-type]


def test_BCW10_a_carried_slot_must_be_in_range() -> None:  # noqa: N802
    with pytest.raises(ValueError, match="out of range"):
        BCWStep(SIMPLE, over_field(SIMPLE_TARGET), 0, Carried(7), Fresh(Q, x5))


def test_BCW10_a_carried_slot_may_not_be_the_target() -> None:  # noqa: N802
    """Otherwise the displacement of G would no longer be free of X_index."""
    with pytest.raises(ValueError, match="the component the step acts on"):
        BCWStep(SIMPLE, over_field(SIMPLE_TARGET), 0, Carried(0), Fresh(Q, x5))


def test_a_carried_index_must_be_a_non_negative_integer() -> None:
    with pytest.raises(TypeError, match="must be an integer"):
        Carried(True)

    with pytest.raises(ValueError, match="must not be negative"):
        Carried(-1)


def test_a_fresh_polynomial_must_be_an_expression() -> None:
    with pytest.raises(TypeError, match="not a SymPy expression"):
        Fresh([], x4)

    with pytest.raises(TypeError, match="not a SymPy expression"):
        Fresh(object(), x4)


def test_the_slots_are_readable(step: BCWStep) -> None:
    """A certificate names where each factor comes from."""
    assert step.left == Fresh(P, x4)
    assert step.right == Fresh(Q, x5)
    assert step.m == 2


def test_the_filtration_level_is_zero_or_one() -> None:
    with pytest.raises(ValueError, match="must be 0 or 1"):
        BCWStep(SIMPLE, over_field(SIMPLE_TARGET), 0, *FRESH, 2)


def test_BCW3_P_and_Q_live_over_the_source() -> None:  # noqa: N802
    """A factor carrying the fresh variables cannot be built at all."""
    with pytest.raises(ValueError, match="must be a polynomial"):
        BCWStep(SIMPLE, over_field(SIMPLE_TARGET), 0, Fresh(x4 * x2, x4), Fresh(Q, x5))


# --------------------------------------------------------------------------
# P and Q live in the ring of the source
# --------------------------------------------------------------------------

T, S = sp.symbols("T S")

# A map over ZZ[T]: T is a parameter of the coefficient domain and not a
# coordinate. The finding of the audit of rc1 was that BCWStep told the two
# apart by name and therefore rejected T.
PARAMETRIC = PolynomialMap((x1, x2, x3), (x1 + T * x2**2 * x3**2, x2, x3))


def test_a_coefficient_parameter_is_allowed() -> None:
    """COL-2 admits it in a collision, and the opposite held here until now."""
    step = BCWStep.build(PARAMETRIC, 0, Fresh(T * x2**2, x4), Fresh(x3**2, x5))

    assert PARAMETRIC.ring.domain == sp.ZZ[T]
    assert step.verify() is None
    assert step.P == T * x2**2


def test_a_nested_coefficient_domain_is_allowed() -> None:
    nested = PolynomialMap((x1, x2, x3), (x1 + T * S * x2**2 * x3**2, x2, x3))
    step = BCWStep.build(nested, 0, Fresh(T * S * x2**2, x4), Fresh(x3**2, x5))

    assert step.verify() is None
    assert step.P == T * S * x2**2


def test_a_non_polynomial_factor_is_refused() -> None:
    """1/x is not an element of the ring and was noticed much later before."""
    with pytest.raises(ValueError, match="must be a polynomial"):
        BCWStep(SIMPLE, over_field(SIMPLE_TARGET), 0, Fresh(1 / x1, x4), Fresh(Q, x5))


def test_a_foreign_symbol_is_refused() -> None:
    with pytest.raises(ValueError, match="must be a polynomial"):
        BCWStep(
            SIMPLE,
            over_field(SIMPLE_TARGET),
            0,
            Fresh(sp.Symbol("q") * x1, x4),
            Fresh(Q, x5),
        )


def test_a_coefficient_outside_the_domain_is_refused() -> None:
    """Over ZZ[T] x/2 is not a polynomial. Over ZZ(T) it is one."""
    with pytest.raises(ValueError, match="must be a polynomial"):
        BCWStep(PARAMETRIC, PARAMETRIC, 0, Fresh(x2**2 / 2, x4), Fresh(x3**2, x5))

    widened = over_field(PARAMETRIC)
    step = BCWStep.build(widened, 0, Fresh(x2**2 / 2, x4), Fresh(x3**2, x5))

    assert step.verify() is None
    assert step.P == x2**2 / 2


def test_the_factors_are_stored_canonically() -> None:
    """The ring normalises, so two ways of writing it compare as equal."""
    expanded = BCWStep.build(SIMPLE, 0, Fresh(x2**2 + 2 * x2 + 1, x4), Fresh(x3**2, x5))
    folded = BCWStep.build(SIMPLE, 0, Fresh((x2 + 1) ** 2, x4), Fresh(x3**2, x5))

    assert expanded.P == folded.P
    assert expanded == folded
    assert hash(expanded) == hash(folded)


# --------------------------------------------------------------------------
# Fresh variables
# --------------------------------------------------------------------------


def test_a_coefficient_parameter_is_not_a_fresh_name() -> None:
    """T is not a coordinate and is taken all the same."""
    with pytest.raises(ValueError, match="already in use"):
        BCWStep(PARAMETRIC, PARAMETRIC, 0, Fresh(x2**2, T), Fresh(x3**2, x5))


def test_two_symbols_of_one_name_are_not_two_variables() -> None:
    """Symbol("v") and Symbol("v", positive=True) are one generator.

    For SymPy they differ and for a ``PolyRing`` they do not, so the check goes
    by the name and not by ``Symbol.__eq__``. Since BCW-12 two fresh slots may
    name the same generator, but they then have to carry the same factor, and
    ``P`` and ``Q`` differ.
    """
    with pytest.raises(ValueError, match="same"):
        BCWStep(
            SIMPLE,
            over_field(SIMPLE_TARGET),
            0,
            Fresh(P, sp.Symbol("w")),
            Fresh(Q, sp.Symbol("w", positive=True)),
        )


# --------------------------------------------------------------------------
# Reused carriers: m = 1 and m = 0
# --------------------------------------------------------------------------

# A source whose fourth component carries x2**2: x4 + x2**2.
CARRYING = over_field(
    PolynomialMap(
        (x1, x2, x3, x4),
        (x1 + x2**2 * x3**2, x2, x3, x2**2 + x4),
    )
)

# And one that carries two values: x2**2 in x4 and x3**2 in x5.
CARRYING_TWICE = over_field(
    PolynomialMap(
        (x1, x2, x3, x4, x5),
        (x1 + x2**2 * x3**2, x2, x3, x2**2 + x4, x3**2 + x5),
    )
)


def test_m_is_one_when_one_slot_is_reused() -> None:
    """One factor is there already, the other is bought."""
    step = BCWStep.build(CARRYING, 0, Carried(3), Fresh(x3**2, x5))

    assert step.m == 1
    assert step.P == x2**2
    assert step.Q == x3**2
    assert step.variables == (x5,)
    assert step.verify() is None
    assert step.target.dimension == CARRYING.dimension + 1


def test_m_is_zero_when_both_slots_are_reused() -> None:
    """No new generator: the step is F' = G o F."""
    step = BCWStep.build(CARRYING_TWICE, 0, Carried(3), Carried(4))

    assert step.m == 0
    assert step.variables == ()
    assert step.verify() is None
    assert step.target.dimension == CARRYING_TWICE.dimension
    assert step.target.variables == CARRYING_TWICE.variables


def test_at_m_zero_the_step_is_a_left_composition() -> None:
    """H is the identity, and the target is G o F."""
    step = BCWStep.build(CARRYING_TWICE, 0, Carried(3), Carried(4))

    assert len(step.H) == 0
    assert step.stabilized == CARRYING_TWICE
    assert step.target == step.G.apply_to(CARRYING_TWICE)


def test_at_m_zero_the_filtration_level_constrains_nothing() -> None:
    """H is the identity and lies in every EA^d."""
    step = BCWStep.build(CARRYING_TWICE, 0, Carried(3), Carried(4), 1)

    assert step.attained_filtration_level == math.inf
    assert step.verify() is None
    assert step.G.is_in_EA(1)


def test_the_removed_product_is_the_product_of_the_two_carriers() -> None:
    """Going backwards, x2**2 * x3**2 reappears."""
    step = BCWStep.build(CARRYING_TWICE, 0, Carried(3), Carried(4))
    removed = sp.expand(CARRYING_TWICE.components[0] - step.target.components[0])

    assert sp.expand(removed - (x2**2 + x4) * (x3**2 + x5)) == 0


def test_both_slots_may_reuse_the_same_coordinate() -> None:
    """The step then removes a square, which is admissible."""
    step = BCWStep.build(CARRYING, 0, Carried(3), Carried(3))

    assert step.m == 0
    assert step.P == step.Q == x2**2
    assert step.verify() is None


def test_BCW10_a_reused_coordinate_must_carry_something() -> None:  # noqa: N802
    """The third clause: it can fail on supplied data.

    Component 2 of the source is ``x3`` and not ``x3 + something free of x3``.
    The value ``F_2 - x3`` is zero, while component 1 is ``x2`` and carries
    nothing. What is named here is a component that carries its own variable in
    the residue.
    """
    twisted = over_field(PolynomialMap((x1, x2, x3, x4), (x1, x2, x3, x4 * x2 + x4)))
    step = BCWStep.build(twisted, 0, Carried(3), Fresh(x3, x5))

    with pytest.raises(VerificationError) as failure:
        step.verify()

    assert failure.value.obligation == "BCW-10"


# --------------------------------------------------------------------------
# BCW-8 for every m
# --------------------------------------------------------------------------

# F(x1, x2, x3, x4, x5) = (x1^2, x2, x3, x2^2 + x4, x3^2 + x5).
# (1, 2, 3, 0, 0) and (-1, 2, 3, 0, 0) have the same image (1, 2, 3, 4, 9).
SQUARE_WITH_CARRIERS = over_field(
    PolynomialMap(
        (x1, x2, x3, x4, x5),
        (x1**2, x2, x3, x2**2 + x4, x3**2 + x5),
    )
)

SQUARE_COLLISION = Collision(((1, 2, 3, 0, 0), (-1, 2, 3, 0, 0)), (1, 2, 3, 4, 9))


def test_BCW8_at_m_one_one_coordinate_is_appended() -> None:  # noqa: N802
    """One bought carrier, so one new coordinate per point."""
    step = BCWStep.build(SQUARE_WITH_CARRIERS, 0, Carried(3), Fresh(x3**2, x6))
    carried = step.transport(SQUARE_COLLISION)

    assert carried.dimension == 6
    assert carried.points[0] == (1, 2, 3, 0, 0, -9)
    assert carried.points[1] == (-1, 2, 3, 0, 0, -9)


def test_BCW8_at_m_one_the_image_only_gains_a_zero() -> None:  # noqa: N802
    """The fresh slot carries a zero at the image, so the product vanishes."""
    step = BCWStep.build(SQUARE_WITH_CARRIERS, 0, Carried(3), Fresh(x3**2, x6))

    assert step.transport(SQUARE_COLLISION).image == (1, 2, 3, 4, 9, 0)


def test_BCW8_at_m_zero_nothing_is_appended() -> None:  # noqa: N802
    step = BCWStep.build(SQUARE_WITH_CARRIERS, 0, Carried(3), Carried(4))
    carried = step.transport(SQUARE_COLLISION)

    assert carried.dimension == 5
    assert carried.points == SQUARE_COLLISION.points


def test_BCW8_at_m_zero_the_image_moves() -> None:  # noqa: N802
    """The only place where a step really moves the image.

    Both carriers have values different from zero at the image, 4 and 9, so the
    target component becomes smaller by 36: 1 - 4 * 9 = -35.
    """
    step = BCWStep.build(SQUARE_WITH_CARRIERS, 0, Carried(3), Carried(4))
    carried = step.transport(SQUARE_COLLISION)

    assert SQUARE_COLLISION.image == (1, 2, 3, 4, 9)
    assert carried.image == (-35, 2, 3, 4, 9)


def test_BCW8_the_number_of_points_survives_every_m() -> None:  # noqa: N802
    """STEP-4: a counterexample stays one, however much is bought."""
    steps = (
        BCWStep.build(SQUARE_WITH_CARRIERS, 0, Fresh(x2**2, x6), Fresh(x3**2, x7)),
        BCWStep.build(SQUARE_WITH_CARRIERS, 0, Carried(3), Fresh(x3**2, x6)),
        BCWStep.build(SQUARE_WITH_CARRIERS, 0, Carried(3), Carried(4)),
    )

    assert [step.m for step in steps] == [2, 1, 0]
    assert all(
        len(step.transport(SQUARE_COLLISION)) == len(SQUARE_COLLISION) for step in steps
    )


def test_BCW8_the_result_is_verified_against_the_target() -> None:  # noqa: N802
    """STEP-3: what comes out is checked and not asserted."""
    step = BCWStep.build(SQUARE_WITH_CARRIERS, 0, Carried(3), Carried(4))
    carried = step.transport(SQUARE_COLLISION)

    assert carried.verify(step.target) is None


# --------------------------------------------------------------------------
# G und H
# --------------------------------------------------------------------------


def test_the_factors_are_derived_not_stored(step: BCWStep) -> None:
    """G and H follow from index and the two slots, formula (1)."""
    assert len(step.G) == 1
    assert len(step.H) == 2
    assert step.G.factors[0].variable == x1
    assert step.G.factors[0].polynomial == -x4 * x5
    assert step.H.factors[0].polynomial == P
    assert step.H.factors[1].polynomial == Q


def test_G_lies_in_EA1(step: BCWStep) -> None:  # noqa: N802
    """The displacement -x4 x5 has order 2."""
    assert step.G.is_in_EA(1)


def test_the_two_factors_of_H_commute(step: BCWStep) -> None:  # noqa: N802
    """BCW-3 makes the order within H immaterial."""
    forward, backward = step.H.factors
    swapped = type(step.H)([backward, forward])

    assert swapped.to_polynomial_map() == step.H.to_polynomial_map()


def test_the_stabilized_map_carries_the_fresh_variables(step: BCWStep) -> None:
    assert step.stabilized.variables == (x1, x2, x3, x4, x5)
    assert step.stabilized.components[3:] == (x4, x5)


# --------------------------------------------------------------------------
# BCW-1 to BCW-7
# --------------------------------------------------------------------------


def test_a_correct_step_verifies(step: BCWStep) -> None:
    assert step.verify() is None
    assert step.verify() is None


def test_BCW1_a_target_that_is_not_the_composite() -> None:  # noqa: N802
    """One sign wrong and the identity fails."""
    wrong = PolynomialMap(
        (x1, x2, x3, x4, x5),
        (
            x1 - x4 * x3**2 - x2**2 * x5 + x4 * x5,
            x2,
            x3,
            x4 + x2**2,
            x5 + x3**2,
        ),
    )

    with pytest.raises(VerificationError) as failure:
        BCWStep(SIMPLE, over_field(wrong), 0, *FRESH).verify()

    assert failure.value.obligation == "BCW-1"


def test_BCW1_the_wrong_factorization() -> None:  # noqa: N802
    """P * Q has to be the part removed and not some product."""
    with pytest.raises(VerificationError) as failure:
        BCWStep(
            SIMPLE, over_field(SIMPLE_TARGET), 0, Fresh(x2, x4), Fresh(x3, x5)
        ).verify()

    assert failure.value.obligation == "BCW-1"


def test_BCW2_a_target_of_the_wrong_dimension() -> None:  # noqa: N802
    with pytest.raises(VerificationError) as failure:
        BCWStep(SIMPLE, SIMPLE, 0, *FRESH).verify()

    assert failure.value.obligation == "BCW-2"


def test_BCW2_a_target_with_other_variables() -> None:  # noqa: N802
    renamed = PolynomialMap(
        sp.symbols("x1 x2 x3 u v"),
        SIMPLE_TARGET.components,
    )

    with pytest.raises(VerificationError) as failure:
        BCWStep(SIMPLE, over_field(renamed), 0, *FRESH).verify()

    assert failure.value.obligation == "BCW-2"


def test_a_fresh_variable_that_is_not_fresh() -> None:
    """Refused early: otherwise two coordinates would denote one generator."""
    with pytest.raises(ValueError, match="already in use"):
        BCWStep(SIMPLE, over_field(SIMPLE_TARGET), 0, Fresh(P, x2), Fresh(Q, x5))


def test_BCW12_one_variable_in_both_slots_needs_one_value() -> None:  # noqa: N802
    """One coordinate holds one value and not two."""
    with pytest.raises(ValueError, match="same"):
        BCWStep(SIMPLE, over_field(SIMPLE_TARGET), 0, Fresh(P, x4), Fresh(Q, x4))


def test_BCW4_the_component_need_not_be_the_first() -> None:  # noqa: N802
    """A reduction reaches components that an earlier step created."""
    source = over_field(PolynomialMap((x1, x2, x3), (x1, x2 + x1**2 * x3**2, x3)))
    built = BCWStep.build(source, 1, Fresh(x1**2, x4), Fresh(x3**2, x5))

    assert built.verify() is None
    assert built.index == 1


def test_BCW6_a_level_that_is_not_reached() -> None:  # noqa: N802
    """A linear term in Q pushes H down to EA^0."""
    source = over_field(PolynomialMap((x1, x2, x3), (x1 + x2 * x3, x2, x3)))

    with pytest.raises(VerificationError) as failure:
        BCWStep.build(
            source, 0, Fresh(x2, x4), Fresh(x3, x5), filtration_level=1
        ).verify()

    assert failure.value.obligation == "BCW-6"


def test_BCW6_the_weaker_claim_is_accepted() -> None:  # noqa: N802
    """Claiming EA^0 where EA^1 holds is true and is accepted."""
    modest = BCWStep(SIMPLE, over_field(SIMPLE_TARGET), 0, *FRESH, filtration_level=0)

    assert modest.verify() is None
    assert modest.filtration_level == 0
    assert modest.attained_filtration_level == 1


def test_BCW7_the_determinant_is_unchanged(step: BCWStep) -> None:  # noqa: N802
    assert SIMPLE.determinant() == 1
    assert step.target.determinant() == 1


# --------------------------------------------------------------------------
# BCW-8: Transport
# --------------------------------------------------------------------------


def test_BCW8_the_fresh_coordinates_become_minus_P_and_minus_Q() -> None:  # noqa: N802
    source = over_field(PolynomialMap((x1, x2, x3), (x1**2, x2, x3)))
    built = BCWStep.build(source, 0, Fresh(x2**2, x4), Fresh(x3**2, x5))
    collision = Collision.at(source, ((1, 2, 3), (-1, 2, 3)))

    carried = built.transport(collision)

    assert carried.points[0] == (1, 2, 3, -4, -9)
    assert carried.points[1] == (-1, 2, 3, -4, -9)
    assert carried.image == (1, 2, 3, 0, 0)


def test_BCW8_the_number_of_points_is_preserved() -> None:  # noqa: N802
    source = over_field(PolynomialMap((x1, x2, x3), (x1**2, x2, x3)))
    built = BCWStep.build(source, 0, Fresh(x2**2, x4), Fresh(x3**2, x5))
    collision = Collision.at(source, ((1, 2, 3), (-1, 2, 3)))

    assert len(built.transport(collision)) == len(collision)


def reported_arity(failure: VerificationError) -> int:
    """Return how many coordinates the message of ``failure`` reports.

    Both checks in ``transport`` raise COL-3, so the obligation alone does not
    say which one fired, and a control that only reads it stays green when one
    of the two is removed -- the other catches the same input one line later.
    The two speak about maps of different dimension, and that is what tells
    them apart.
    """
    point = re.search(r"\(([^)]*)\)", str(failure))

    assert point is not None, str(failure)

    return len(point.group(1).split(","))


@pytest.fixture
def collidable() -> BCWStep:
    """A step whose source really has a collision.

    ``SIMPLE`` has none: ``x2`` and ``x3`` stay as they are, so equality of the
    images forces equality of the points. The output check needs a real
    collision, otherwise the input check fails first.
    """
    source = over_field(PolynomialMap((x1, x2, x3), (x1**2, x2, x3)))

    return BCWStep.build(source, 0, Fresh(x2**2, x4), Fresh(x3**2, x5), 1)


def test_transport_rejects_a_collision_of_another_map(step: BCWStep) -> None:
    """STEP-3: what is checked is the input, and against the source.

    The source has three coordinates and the target five. If the error reports
    three, the input check is what fired.
    """
    with pytest.raises(VerificationError) as failure:
        step.transport(Collision(((1, 2, 3), (-1, 2, 3)), (0, 0, 0)))

    assert failure.value.obligation == "COL-3"
    assert reported_arity(failure.value) == 3


def test_transport_verifies_its_own_result(collidable: BCWStep) -> None:
    """STEP-2 and BCW-8: the output is checked, and that is reachable.

    ``transport`` does not call ``verify()`` of the step. For a supplied step
    with a wrong target the output check is therefore the only thing standing
    between a false certificate and an apparently machine-checked
    non-injectivity of the target.

    Until 0.4.0rc13 no test told the two checks apart. A mutation probe over
    ``contracts.md`` showed it: either one could be removed on its own without
    the suite turning red, because the other caught the same case.
    """
    genuine = Collision.at(collidable.source, ((1, 2, 3), (-1, 2, 3)))
    wrong = PolynomialMap(
        collidable.target.variables,
        (collidable.target.components[0] + 1,) + collidable.target.components[1:],
    )
    supplied = BCWStep(
        collidable.source,
        wrong,
        collidable.index,
        collidable.left,
        collidable.right,
        collidable.filtration_level,
    )

    with pytest.raises(VerificationError) as failure:
        supplied.transport(genuine)

    assert failure.value.obligation == "COL-3"
    assert reported_arity(failure.value) == 5


# --------------------------------------------------------------------------
# BCW-9: provenance
# --------------------------------------------------------------------------


def test_a_supplied_target_is_recorded_as_such(step: BCWStep) -> None:
    assert step.provenance is Provenance.SUPPLIED


def test_build_records_the_target_as_constructed() -> None:
    built = BCWStep.build(SIMPLE, 0, *FRESH)

    assert built.provenance is Provenance.CONSTRUCTED
    assert built.target == over_field(SIMPLE_TARGET)
    assert built.verify() is None


def test_a_reduction_takes_the_weaker_provenance(step: BCWStep) -> None:
    assert Reduction([step]).provenance is Provenance.SUPPLIED
    assert (
        Reduction([BCWStep.build(SIMPLE, 0, *FRESH)]).provenance
        is Provenance.CONSTRUCTED
    )


# --------------------------------------------------------------------------
# Value semantics
# --------------------------------------------------------------------------


def test_equality_and_hash(step: BCWStep) -> None:
    twin = BCWStep(SIMPLE, over_field(SIMPLE_TARGET), 0, *FRESH)

    assert step == twin
    assert hash(step) == hash(twin)
    assert step != object()


def test_provenance_is_part_of_the_value(step: BCWStep) -> None:
    """Two steps with the same target, and only one of them is evidence."""
    built = BCWStep.build(SIMPLE, 0, *FRESH)

    assert step.target == built.target
    assert step != built
    assert Reduction([step]) != Reduction([built])


def test_the_public_constructor_cannot_claim_construction() -> None:
    """BCW-9 depends on the marker not being settable."""
    with pytest.raises(TypeError):
        BCWStep(
            SIMPLE,
            over_field(SIMPLE_TARGET),
            0,
            *FRESH,
            provenance=Provenance.CONSTRUCTED,  # type: ignore[call-arg]
        )


def test_repr_names_the_essentials(step: BCWStep) -> None:
    assert "index=0" in repr(step)
    assert "3->5" in repr(step)


# --------------------------------------------------------------------------
# Regression: the first step of the reference reduction, target supplied
# --------------------------------------------------------------------------

ALPOEGE = over_field(examples.alpoege())

# Written out and not computed: only then can BCW-1 fail at all.
FIRST_TARGET = PolynomialMap(
    (x1, x2, x3, x4, x5),
    (
        -3 * x1**2 * x2 / 2 - x1**2 * x4 + x1 * x3 * x5 / 2 + x1 - x4 * x5,
        3 * x1**3 * x2**2 * x3
        + 9 * x1**2 * x2**3
        + 6 * x1**2 * x2 * x3
        + 12 * x1 * x2**2
        + 3 * x1 * x3
        + x2,
        x1**3 * x2**3 * x3
        + 3 * x1**2 * x2**4
        + 3 * x1**2 * x2**2 * x3
        + 7 * x1 * x2**3
        + 3 * x1 * x2 * x3
        + 4 * x2**2
        + x3,
        -x1 * x3 / 2 + x4,
        x1**2 + x5,
    ),
)


@pytest.fixture(scope="module")
def first_step() -> BCWStep:
    normalization = LinearStep.normalize(ALPOEGE)

    return BCWStep(
        normalization.target,
        over_field(FIRST_TARGET),
        0,
        Fresh(-x1 * x3 / 2, x4),
        Fresh(x1**2, x5),
        filtration_level=1,
    )


def test_the_first_step_of_the_reference_reduction(first_step: BCWStep) -> None:
    assert first_step.provenance is Provenance.SUPPLIED
    assert first_step.verify() is None


def test_the_first_component_is_already_the_one_BCW17_carries(  # noqa: N802
    first_step: BCWStep,
) -> None:
    """No later step touches it again."""
    expected = -3 * x1**2 * x2 / 2 - x1**2 * x4 + x1 * x3 * x5 / 2 + x1 - x4 * x5

    assert sp.expand(first_step.target.components[0] - expected) == 0


def test_the_normalization_and_the_first_step_chain(first_step: BCWStep) -> None:
    chain = Reduction([LinearStep.normalize(ALPOEGE), first_step])

    assert chain.verify() is None
    assert chain.dimensions() == (3, 3, 5)
    assert chain.degrees() == (7, 7, 7)
    assert chain.target.determinant() == 1


def test_the_collision_survives_the_first_step(first_step: BCWStep) -> None:
    """The fourth and fifth coordinate of BCW17, at three points."""
    chain = Reduction([LinearStep.normalize(ALPOEGE), first_step])
    collision = Collision.at(
        ALPOEGE,
        (
            (0, 0, sp.Rational(-1, 4)),
            (1, sp.Rational(-3, 2), sp.Rational(13, 2)),
            (-1, sp.Rational(3, 2), sp.Rational(13, 2)),
        ),
    )

    carried = chain.transport(collision)

    assert len(carried) == 3
    assert carried.points[0] == (0, 0, sp.Rational(-1, 4), 0, 0)
    assert carried.points[1] == (
        1,
        sp.Rational(-3, 2),
        sp.Rational(13, 2),
        sp.Rational(13, 4),
        -1,
    )
    assert carried.points[2] == (
        -1,
        sp.Rational(3, 2),
        sp.Rational(13, 2),
        sp.Rational(-13, 4),
        -1,
    )
    assert carried.image == (0, 0, sp.Rational(-1, 4), 0, 0)


# --------------------------------------------------------------------------
# BCW-11 and BCW-12: the coefficient and the repeated fresh slot
# --------------------------------------------------------------------------


def test_BCW11_the_coefficient_scales_the_removed_product() -> None:  # noqa: N802
    """``G`` subtracts ``coefficient * X_u X_v``.

    An extension beyond Proposition (3.1), and a necessary one: the published
    nineteen-dimensional chain carries coefficients such as ``3``, ``-3``,
    ``7`` and ``9``, and no change of coordinates removes them.
    """
    source = over_field(PolynomialMap((x1, x2, x3), (x1 + 3 * x2**2 * x3**2, x2, x3)))

    built = BCWStep.build(source, 0, Fresh(x2**2, x4), Fresh(x3**2, x5), 1, 3)

    assert built.verify() is None
    assert built.coefficient == 3
    assert built.target.components[0] == (
        x1 - 3 * x4 * x5 - 3 * x4 * x3**2 - 3 * x2**2 * x5
    )


def test_BCW11_the_coefficient_defaults_to_one() -> None:  # noqa: N802
    """A step without a coefficient is exactly the step from before."""
    source = over_field(PolynomialMap((x1, x2, x3), (x1 + x2**2 * x3**2, x2, x3)))

    plain = BCWStep.build(source, 0, Fresh(x2**2, x4), Fresh(x3**2, x5))
    spelled = BCWStep.build(source, 0, Fresh(x2**2, x4), Fresh(x3**2, x5), 1, 1)

    assert plain.coefficient == 1
    assert plain == spelled


def test_BCW11_the_coefficient_is_a_constant() -> None:  # noqa: N802
    """Conversion and not inspection, as in BCW-3 and TRA-2."""
    source = over_field(PolynomialMap((x1, x2, x3), (x1 + x2**2 * x3**2, x2, x3)))

    with pytest.raises(ValueError, match="coefficient domain"):
        BCWStep.build(source, 0, Fresh(x2**2, x4), Fresh(x3**2, x5), 1, x1)


def test_BCW11_zero_is_refused() -> None:  # noqa: N802
    """A step that removes nothing is the identity written out."""
    source = over_field(PolynomialMap((x1, x2, x3), (x1 + x2**2 * x3**2, x2, x3)))

    with pytest.raises(ValueError, match="must not be zero"):
        BCWStep.build(source, 0, Fresh(x2**2, x4), Fresh(x3**2, x5), 1, 0)


def test_BCW11_the_coefficient_is_part_of_the_value() -> None:  # noqa: N802
    """Two steps that differ only in the coefficient are different, and so
    are their targets."""
    source = over_field(PolynomialMap((x1, x2, x3), (x1 + 3 * x2**2 * x3**2, x2, x3)))

    one = BCWStep.build(source, 0, Fresh(x2**2, x4), Fresh(x3**2, x5), 1, 3)
    other = BCWStep.build(source, 0, Fresh(x2**2, x4), Fresh(x3**2, x5), 1, 1)

    assert one != other
    assert one.target != other.target


def test_BCW12_one_fresh_variable_may_fill_both_slots() -> None:  # noqa: N802
    """The case the published chain needs.

    Its fifteenth step is ``F_x -> F_x - 3 (w3 + x y^2)^2``. ``G`` then
    subtracts a square, and the coordinate is created once.
    """
    source = over_field(PolynomialMap((x1, x2, x3), (x1 + 3 * x2**2 * x3**2, x2, x3)))

    built = BCWStep.build(source, 0, Fresh(x2 * x3, x4), Fresh(x2 * x3, x4), 1, 3)

    assert built.verify() is None
    assert built.m == 1
    assert built.variables == (x4,)
    assert built.target.dimension == source.dimension + 1
    assert built.target.components[0] == x1 - 3 * x4**2 - 6 * x2 * x3 * x4


def test_BCW12_the_symmetry_with_a_repeated_carried_slot() -> None:  # noqa: N802
    """Two ``Carried`` slots have been allowed to name one coordinate since 0.3.

    Two ``Fresh`` slots are the same shape one step earlier.
    """
    source = over_field(PolynomialMap((x1, x2, x3), (x1 + x2**4, x2, x3 + x2**2)))

    carried = BCWStep.build(source, 0, Carried(2), Carried(2))
    fresh = BCWStep.build(source, 0, Fresh(x2**2, x4), Fresh(x2**2, x4))

    assert carried.verify() is None
    assert fresh.verify() is None
    assert carried.m == 0
    assert fresh.m == 1


def test_BCW12_a_collision_gains_one_coordinate_per_generator() -> None:  # noqa: N802
    """Not one per ``Fresh`` slot.

    Up to WP 11 the transport counted the slots. For a step whose two slots
    name one variable, the points got two coordinates and the image got one,
    and ``Collision.extended`` refused. It was noticed while assembling the
    chain to the nineteen-dimensional map and not by a test: no test had ever
    transported through such a step.
    """
    source = over_field(PolynomialMap((x1, x2, x3), (x1**2, x2, x3)))
    collision = Collision.at(source, ((1, 0, 0), (-1, 0, 0)))
    step = BCWStep.build(source, 1, Fresh(x1 * x3, x4), Fresh(x1 * x3, x4), 1, 3)

    carried = step.transport(collision)

    assert step.m == 1
    assert all(len(point) == source.dimension + 1 for point in carried.points)
    assert len(carried.image) == source.dimension + 1
    assert carried.verify(step.target) is None
