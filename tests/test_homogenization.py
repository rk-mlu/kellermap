"""Section 4's third step as a certificate.

The weight lies with HOM-3, which is the obligation that keeps the three stages
in order and the one whose negative control has to show something the wording
insists on: that a *Keller* source is not enough, only a nilpotent one.

The other control worth reading is the one for HOM-1, which uses a target that
passes HOM-8. The two checks are not the same statement and the page says so;
this is where that is shown.

At the end stands ``alpoege12``, lifted and homogenized, which is 25 variables
and cubic homogeneous. It is marked slow.
"""

import math

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
from kellermap.bcw import HomogenizationStep, UnipotentStep
from kellermap.variables import IndexedVariableFactory

x1, x2, x3, x4 = sp.symbols("x1 x2 x3 x4")

# F = (x1 + x2 + x2^2, x2). Its displacement has a linear part and a quadratic
# one, so N_(1) and N_(2) are both non-zero and the two exponents of the
# formula can be told apart. J(N) is nilpotent, so HOM-3 holds.
SIMPLE = over_field(PolynomialMap((x1, x2), (x1 + x2 + x2**2, x2)))

FRESH = x3

# (X + N_(1) T^2 + N_(2) T, T), by hand.
SIMPLE_TARGET = over_field(
    PolynomialMap(
        (x1, x2, x3),
        (x1 + x2 * x3**2 + x2**2 * x3, x2, x3),
    )
)


@pytest.fixture
def step() -> HomogenizationStep:
    return HomogenizationStep(SIMPLE, SIMPLE_TARGET, FRESH)


# --------------------------------------------------------------------------
# Construction
# --------------------------------------------------------------------------


def test_the_step_is_a_step() -> None:
    assert isinstance(HomogenizationStep(SIMPLE, SIMPLE_TARGET, FRESH), Step)


def test_a_supplied_target_is_recorded_as_supplied(step: HomogenizationStep) -> None:
    assert step.provenance is Provenance.SUPPLIED


def test_build_records_the_target_as_constructed() -> None:
    assert HomogenizationStep.build(SIMPLE).provenance is Provenance.CONSTRUCTED


def test_build_reaches_the_target_written_out_by_hand() -> None:
    """The formula and the hand computation agree.

    This is what makes the fixture evidence rather than a copy of the
    implementation's output. The linear part is lifted by ``T^2`` and the
    quadratic one by ``T``.
    """
    built = HomogenizationStep.build(SIMPLE)

    assert built.variable == FRESH
    assert built.target == SIMPLE_TARGET


def test_a_factory_may_name_the_generator() -> None:
    built = HomogenizationStep.build(SIMPLE, factory=IndexedVariableFactory("w"))

    assert built.variable == sp.Symbol("w1")
    assert built.verify() is None


def test_the_fresh_variable_may_not_be_one_of_the_sources() -> None:
    with pytest.raises(ValueError, match="already in use"):
        HomogenizationStep(SIMPLE, SIMPLE_TARGET, x1)


def test_the_fresh_variable_may_not_be_a_parameter_of_the_domain() -> None:
    """Reserved names and not merely coordinates."""
    parameter = sp.Symbol("T")
    parametric = PolynomialMap((x1, x2), (x1 + parameter * x2**2, x2))

    with pytest.raises(ValueError, match="already in use"):
        HomogenizationStep(parametric, parametric, parameter)


def test_the_source_must_be_a_polynomial_map() -> None:
    with pytest.raises(TypeError, match="source must be a PolynomialMap"):
        HomogenizationStep("F", SIMPLE_TARGET, FRESH)  # type: ignore[arg-type]


def test_the_target_must_be_a_polynomial_map() -> None:
    with pytest.raises(TypeError, match="target must be a PolynomialMap"):
        HomogenizationStep(SIMPLE, "F'", FRESH)  # type: ignore[arg-type]


def test_the_fresh_variable_must_be_a_symbol() -> None:
    with pytest.raises(TypeError, match="must be a SymPy symbol"):
        HomogenizationStep(SIMPLE, SIMPLE_TARGET, 7)  # type: ignore[arg-type]


# --------------------------------------------------------------------------
# What the step reports
# --------------------------------------------------------------------------


def test_the_homogeneous_parts_are_reported(step: HomogenizationStep) -> None:
    """``N_(1)``, ``N_(2)``, ``N_(3)``, in that order."""
    assert step.parts == ((x2, 0), (x2**2, 0), (0, 0))


def test_the_step_makes_no_EA_claim(step: HomogenizationStep) -> None:  # noqa: N802
    """HOM: it is not a composition, so there is no level to declare."""
    assert step.filtration_level == math.inf


def test_the_target_is_cubic_homogeneous(step: HomogenizationStep) -> None:
    """HOM-5, read off the target rather than through ``verify``."""
    degrees = {
        sum(monomial)
        for component in step.target.displacement().to_polynomials()
        if component
        for monomial in component.itermonoms()
    }

    assert degrees == {3}


def test_the_target_lies_in_MA_two(step: HomogenizationStep) -> None:  # noqa: N802
    """HOM-6. The second step leaves ``MA^1`` and the third comes back past it."""
    assert step.target.filtration_degree() == 2
    assert step.target.is_in_MA(1)


def test_the_variable_is_the_fresh_one_only(step: HomogenizationStep) -> None:
    assert step.variable == FRESH
    assert step.target.variables == SIMPLE.variables + (FRESH,)


# --------------------------------------------------------------------------
# Verification, and what can fail
# --------------------------------------------------------------------------


def test_a_correct_step_verifies(step: HomogenizationStep) -> None:
    assert step.verify() is None


def test_verification_is_idempotent(step: HomogenizationStep) -> None:
    """STEP-2."""
    step.verify()

    assert step.verify() is None


def test_a_target_with_the_exponents_swapped_fails_the_identity() -> None:
    """HOM-1, the negative control, and the one HOM-8 does not catch.

    Lifting ``N_(1)`` by ``T`` and ``N_(2)`` by ``T^2`` gives a map that agrees
    with the source at ``T = 1``, because all three slots contribute alike
    there. The slice check therefore passes on it. HOM-1 is what fails, and the
    contract page says the two are not the same statement.
    """
    swapped = over_field(
        PolynomialMap(
            (x1, x2, x3),
            (x1 + x2 * x3 + x2**2 * x3**2, x2, x3),
        )
    )

    at_one = {x3: sp.Integer(1)}
    assert (
        tuple(
            sp.expand(component.xreplace(at_one))
            for component in swapped.components[:2]
        )
        == SIMPLE.components
    )

    with pytest.raises(VerificationError, match=r"\[HOM-1\]") as failure:
        HomogenizationStep(SIMPLE, swapped, FRESH).verify()

    assert failure.value.obligation == "HOM-1"


def test_a_source_of_degree_four_is_refused() -> None:
    """HOM-2, the negative control."""
    source = over_field(PolynomialMap((x1, x2), (x1 + x2**4, x2)))

    with pytest.raises(VerificationError, match=r"\[HOM-2\]") as failure:
        HomogenizationStep.build(source).verify()

    assert failure.value.obligation == "HOM-2"
    assert "degree 4" in failure.value.message


def test_a_Keller_source_whose_Jacobian_is_not_nilpotent_is_refused() -> None:  # noqa: N802
    """HOM-3, the negative control, and the reason the obligation is worded as it is.

    ``(2 x1, x2 / 2)`` has Jacobian determinant one, so it is a Keller map, and
    its displacement ``(x1, -x2 / 2)`` has Jacobian ``diag(1, -1/2)``, which is
    not nilpotent. Homogenized it would be
    ``(x1 + x1 T^2, x2 - x2 T^2 / 2, T)``, whose determinant is
    ``(1 + T^2)(1 - T^2 / 2)`` and not one.

    So "the source is Keller" is not the precondition, and a control that used
    a non-Keller source would not have shown it.
    """
    source = over_field(PolynomialMap((x1, x2), (2 * x1, x2 / 2)))

    assert source.determinant() == 1

    with pytest.raises(VerificationError, match=r"\[HOM-3\]") as failure:
        HomogenizationStep.build(source).verify()

    assert failure.value.obligation == "HOM-3"
    assert "nilpotent" in failure.value.message


def test_a_source_with_a_constant_term_fails_the_slice() -> None:
    """HOM-8 doing work that is not redundant.

    The formula has three slots and a part of degree zero has none, so the
    constant is dropped. The sum of the three parts is then not the
    displacement, the slice at ``T = 1`` is not the source, and this is the
    check that notices. ``TranslationStep`` is what removes a constant term.
    """
    source = over_field(PolynomialMap((x1, x2), (x1 + 1 + x2**2, x2)))

    with pytest.raises(VerificationError, match=r"\[HOM-8\]") as failure:
        HomogenizationStep.build(source).verify()

    assert failure.value.obligation == "HOM-8"


def test_a_wrong_slice_is_caught_on_a_supplied_target() -> None:
    """HOM-8 again, reached before HOM-7 and after HOM-1 cannot see it.

    Here the target is the formula's, so HOM-1 holds; the source is what does
    not match it.
    """
    other = over_field(PolynomialMap((x1, x2), (x1 + x2 + 2 * x2**2, x2)))

    with pytest.raises(VerificationError, match=r"\[HOM-1\]"):
        HomogenizationStep(other, SIMPLE_TARGET, FRESH).verify()


def test_a_target_of_the_wrong_dimension_fails() -> None:
    """HOM-4, the negative control for the half ``verify`` reaches."""
    wrong = over_field(PolynomialMap((x1, x2), (x1, x2)))

    with pytest.raises(VerificationError, match=r"\[HOM-4\]") as failure:
        HomogenizationStep(SIMPLE, wrong, FRESH).verify()

    assert failure.value.obligation == "HOM-4"


def test_a_target_carrying_another_variable_fails() -> None:
    """HOM-4 again: the right dimension is not the right generators."""
    wrong = over_field(
        PolynomialMap((x1, x2, x4), (x1 + x2 * x4**2 + x2**2 * x4, x2, x4))
    )

    with pytest.raises(VerificationError, match=r"\[HOM-4\]"):
        HomogenizationStep(SIMPLE, wrong, FRESH).verify()


def test_the_source_is_checked_before_the_target() -> None:
    """A failure about the caller's map is not reported as one of ours."""
    source = over_field(PolynomialMap((x1, x2), (x1 + x2**4, x2)))
    wrong = over_field(PolynomialMap((x1, x2), (x1, x2)))

    with pytest.raises(VerificationError, match=r"\[HOM-2\]"):
        HomogenizationStep(source, wrong, FRESH).verify()


def test_build_does_not_repair_the_source() -> None:
    """HOM-2 and HOM-3 fail on a constructed step too.

    ``build`` cannot make them true, as ``UnipotentStep.build`` cannot make
    UNI-2 true, and neither tries.
    """
    source = over_field(PolynomialMap((x1, x2), (2 * x1, x2 / 2)))
    built = HomogenizationStep.build(source)

    assert built.provenance is Provenance.CONSTRUCTED
    with pytest.raises(VerificationError, match=r"\[HOM-3\]"):
        built.verify()


# --------------------------------------------------------------------------
# Transport
#
# As in ``tests/test_unipotent.py``, the source here is not a Keller map.
# ``transport`` checks the incoming collision against the source and the
# outgoing one against the target and needs nothing else, and no small Keller
# map with a collision is known.
# --------------------------------------------------------------------------

SQUARE = over_field(PolynomialMap((x1, x2), (x1**2 + x2**3, x2)))
SQUARE_COLLISION = Collision(((1, 2), (-1, 2)), (9, 2))


def test_transport_appends_one_and_not_zero() -> None:
    """HOM-9. The collision lives on the slice ``T = 1``."""
    moved = HomogenizationStep.build(SQUARE).transport(SQUARE_COLLISION)

    assert moved.points == ((1, 2, 1), (-1, 2, 1))
    assert moved.image == (9, 2, 1)


def test_zero_would_not_have_been_a_collision() -> None:
    """Why the appended value is not free, unlike in BCW-8 and UNI-11.

    At ``T = 0`` only ``N_(3)`` survives, since it is the part the formula
    lifts by ``T^0``. The slice is therefore the map ``X + N_(3)``, which is
    not the source and does not collide at these points: ``x1 + x2^3`` sends
    them to 9 and to 7.
    """
    target = HomogenizationStep.build(SQUARE).target
    at_zero = [
        tuple(
            sp.expand(
                component.xreplace(
                    dict(zip(target.variables, point + (0,), strict=True))
                )
            )
            for component in target.components
        )
        for point in SQUARE_COLLISION.points
    ]

    assert at_zero == [(9, 2, 0), (7, 2, 0)]


def test_transport_verifies_the_incoming_collision() -> None:
    """STEP-3."""
    step = HomogenizationStep.build(SQUARE)

    with pytest.raises(VerificationError, match=r"\[COL-3\]"):
        step.transport(Collision(((1, 2), (0, 2)), (9, 2)))


def test_transport_preserves_the_number_of_points() -> None:
    """STEP-4, on four points."""
    source = over_field(PolynomialMap((x1, x2), (x1**2, x2**2)))
    collision = Collision(((1, 2), (-1, 2), (1, -2), (-1, -2)), (1, 4))

    moved = HomogenizationStep.build(source).transport(collision)

    assert len(moved.points) == 4
    assert len(set(moved.points)) == 4


# --------------------------------------------------------------------------
# Value semantics
# --------------------------------------------------------------------------


def test_two_equal_steps_compare_equal_and_hash_alike() -> None:
    """STEP-5."""
    one = HomogenizationStep(SIMPLE, SIMPLE_TARGET, FRESH)
    other = HomogenizationStep(SIMPLE, SIMPLE_TARGET, FRESH)

    assert one == other
    assert hash(one) == hash(other)


def test_provenance_is_part_of_the_value() -> None:
    supplied = HomogenizationStep(SIMPLE, SIMPLE_TARGET, FRESH)
    constructed = HomogenizationStep.build(SIMPLE)

    assert supplied.target == constructed.target
    assert supplied != constructed


def test_a_step_does_not_compare_to_another_type() -> None:
    assert HomogenizationStep(SIMPLE, SIMPLE_TARGET, FRESH) != SIMPLE


def test_the_representation_names_the_dimensions() -> None:
    text = repr(HomogenizationStep(SIMPLE, SIMPLE_TARGET, FRESH))

    assert "2->3" in text
    assert "supplied" in text


# --------------------------------------------------------------------------
# In a chain
# --------------------------------------------------------------------------


def test_the_two_steps_of_section_four_compose() -> None:
    """Lift, then homogenize. The chain is what the milestone is about."""
    source = over_field(PolynomialMap((x1, x2), (x1 + x2**2, x2)))
    lift = UnipotentStep.build(source)
    chain = Reduction((lift, HomogenizationStep.build(lift.target)))

    assert chain.verify() is None
    assert chain.source.dimension == 2
    assert chain.target.dimension == 5
    assert chain.target.filtration_degree() == 2


def test_the_chain_keeps_the_level_the_lift_established() -> None:
    """RED-6 takes the minimum, and ``math.inf`` is the neutral element."""
    source = over_field(PolynomialMap((x1, x2), (x1 + x2**2, x2)))
    lift = UnipotentStep.build(source)
    chain = Reduction((lift, HomogenizationStep.build(lift.target)))

    assert chain.filtration_level() == 0


def test_homogenizing_twice_only_adds_a_variable() -> None:
    """The construction is idempotent up to one identity coordinate.

    A cubic homogeneous displacement has ``N_(1) = N_(2) = 0``, so the second
    application lifts ``N_(3)`` by ``T^0`` and changes nothing else. Worth a
    test because a reader might expect the step to refuse, and it does not:
    HOM-3 holds on the target, since a nilpotent block with a column beside it
    is still nilpotent.
    """
    once = HomogenizationStep.build(SIMPLE)
    twice = HomogenizationStep.build(once.target)

    assert twice.verify() is None
    assert twice.target.dimension == once.target.dimension + 1
    assert twice.target.components[:-1] == once.target.components


# --------------------------------------------------------------------------
# The map the milestone is about
# --------------------------------------------------------------------------


@pytest.mark.slow
def test_alpoege12_homogenizes_to_twenty_five_variables() -> None:
    """12 to 24 to 25, cubic homogeneous, with the three points on ``T = 1``.

    The figure the roadmap carries for work packages 1 and 3. The compression
    of work package 5 is what takes it down again.
    """
    lift = UnipotentStep.build(over_field(examples.alpoege12()))
    homogenized = HomogenizationStep.build(lift.target)
    chain = Reduction((lift, homogenized))

    assert chain.verify() is None
    assert homogenized.target.dimension == 25
    assert homogenized.target.degree() == 3
    assert homogenized.target.filtration_degree() == 2
    assert homogenized.target.determinant() == 1

    moved = chain.transport(examples.alpoege12_collision())

    assert len(moved.points) == 3
    assert {point[-1] for point in moved.points} == {1}
    assert moved.verify(homogenized.target) is None
