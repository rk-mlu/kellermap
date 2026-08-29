"""Section 4's second step as a certificate.

The weight lies in two places. UNI-1 has to be able to fail against a
*supplied* target, which the small map below provides, and UNI-2, UNI-3 and
UNI-4 have to be able to fail against a supplied *source*, which is where this
type differs from every other on the contract page: ``build`` cannot make them
true.

At the end stands ``alpoege13``, normalized and lifted, which is the map
milestone 0.6 is about. It is marked slow.
"""

import math

import pytest
import sympy as sp

from kellermap import (
    Collision,
    LinearStep,
    PolynomialMap,
    Provenance,
    Reduction,
    Step,
    VerificationError,
    examples,
    over_field,
)
from kellermap.bcw import UnipotentStep
from kellermap.bcw.unipotent import homogeneous_part
from kellermap.variables import IndexedVariableFactory

x1, x2, x3, x4, x5, x6, x7 = sp.symbols("x1 x2 x3 x4 x5 x6 x7")

# F = (x1 + x2^2 x3, x2, x3), in MA^1 and of degree three. Its displacement has
# F_(2) = 0 and F_(3) = (x2^2 x3, 0, 0), which keeps the target short enough to
# write down.
SIMPLE = over_field(PolynomialMap((x1, x2, x3), (x1 + x2**2 * x3, x2, x3)))

FRESH = (x4, x5, x6)

# G o F^[3] o H, by hand: the X block gains its Y, and Y_1 loses F_(3),1.
SIMPLE_TARGET = over_field(
    PolynomialMap(
        (x1, x2, x3, x4, x5, x6),
        (x1 + x4, x2 + x5, x3 + x6, x4 - x2**2 * x3, x5, x6),
    )
)


@pytest.fixture
def step() -> UnipotentStep:
    return UnipotentStep(SIMPLE, SIMPLE_TARGET, FRESH)


# --------------------------------------------------------------------------
# The homogeneous parts
# --------------------------------------------------------------------------


def test_a_homogeneous_part_that_is_absent_is_zero() -> None:
    """``F_(2)`` of the small map is zero, and zero has no terms to select."""
    polynomial = SIMPLE.displacement().to_polynomials()[0]

    assert homogeneous_part(polynomial, 2) == polynomial.ring.zero
    assert homogeneous_part(polynomial, 3).as_expr() == x2**2 * x3


def test_a_coefficient_parameter_does_not_count_towards_the_degree() -> None:
    """Total degree in the generators, as ``PolynomialMap.degree`` reads it.

    Over ``k[T]`` the term ``T x2 x3`` is quadratic and not cubic. Reading the
    parameter as a variable would put it in ``F_(3)`` and make the step remove
    the wrong part.
    """
    parameter = sp.Symbol("T")
    parametric = PolynomialMap((x1, x2, x3), (x1 + parameter * x2 * x3, x2, x3))
    polynomial = parametric.displacement().to_polynomials()[0]

    assert homogeneous_part(polynomial, 2).as_expr() == parameter * x2 * x3
    assert homogeneous_part(polynomial, 3) == polynomial.ring.zero


# --------------------------------------------------------------------------
# Construction
# --------------------------------------------------------------------------


def test_the_step_is_a_step() -> None:
    """It satisfies the protocol, so a ``Reduction`` can hold it."""
    assert isinstance(UnipotentStep(SIMPLE, SIMPLE_TARGET, FRESH), Step)


def test_a_supplied_target_is_recorded_as_supplied(step: UnipotentStep) -> None:
    assert step.provenance is Provenance.SUPPLIED


def test_build_records_the_target_as_constructed() -> None:
    assert UnipotentStep.build(SIMPLE).provenance is Provenance.CONSTRUCTED


def test_build_reaches_the_target_written_out_by_hand() -> None:
    """The formula and the hand computation agree.

    This is what makes the fixture above evidence rather than a copy of the
    implementation's output.
    """
    built = UnipotentStep.build(SIMPLE)

    assert built.variables == FRESH
    assert built.target == SIMPLE_TARGET


def test_a_factory_may_name_the_generators() -> None:
    """The naming policy is the caller's, and the certificate records the names.

    The default reads the convention off the source, ``x1, x2, x3`` giving
    ``x4, x5, x6``. A caller who wants another prefix says so.
    """
    built = UnipotentStep.build(SIMPLE, factory=IndexedVariableFactory("w"))

    assert built.variables == sp.symbols("w1 w2 w3")
    assert built.verify() is None


def test_the_number_of_fresh_variables_is_the_dimension() -> None:
    """UNI-5, the counting half, at construction."""
    with pytest.raises(ValueError, match="one generator per component"):
        UnipotentStep(SIMPLE, SIMPLE_TARGET, (x4, x5))


def test_fresh_variables_must_be_distinct() -> None:
    """Two names for one generator would leave the target short a coordinate."""
    with pytest.raises(ValueError, match="must be distinct"):
        UnipotentStep(SIMPLE, SIMPLE_TARGET, (x4, x5, x4))


def test_fresh_variables_are_compared_by_name() -> None:
    """``Symbol("x4")`` and ``Symbol("x4", positive=True)`` are one generator.

    Distinctness by ``Symbol.__eq__`` would admit this pair, and the extension
    would then let two coordinates denote one generator.
    """
    assumed = sp.Symbol("x4", positive=True)

    with pytest.raises(ValueError, match="must be distinct"):
        UnipotentStep(SIMPLE, SIMPLE_TARGET, (x4, x5, assumed))


def test_a_fresh_variable_may_not_be_a_variable_of_the_source() -> None:
    with pytest.raises(ValueError, match="already in use"):
        UnipotentStep(SIMPLE, SIMPLE_TARGET, (x1, x5, x6))


def test_a_fresh_variable_may_not_be_a_parameter_of_the_domain() -> None:
    """Reserved names and not merely coordinates.

    A parameter of the coefficient domain is taken too, and a coordinate of
    that name would collapse the two.
    """
    parameter = sp.Symbol("T")
    parametric = PolynomialMap((x1, x2), (x1 + parameter * x2**2, x2))

    with pytest.raises(ValueError, match="already in use"):
        UnipotentStep(parametric, parametric, (parameter, x4))


def test_the_source_must_be_a_polynomial_map() -> None:
    with pytest.raises(TypeError, match="source must be a PolynomialMap"):
        UnipotentStep("F", SIMPLE_TARGET, FRESH)  # type: ignore[arg-type]


def test_the_target_must_be_a_polynomial_map() -> None:
    with pytest.raises(TypeError, match="target must be a PolynomialMap"):
        UnipotentStep(SIMPLE, "F'", FRESH)  # type: ignore[arg-type]


def test_a_fresh_variable_must_be_a_symbol() -> None:
    with pytest.raises(TypeError, match="must be a SymPy symbol"):
        UnipotentStep(SIMPLE, SIMPLE_TARGET, (x4, x5, 7))  # type: ignore[arg-type]


# --------------------------------------------------------------------------
# What the step exhibits
# --------------------------------------------------------------------------


def test_G_and_H_are_derived_and_not_stored(step: UnipotentStep) -> None:  # noqa: N802
    """One factor per component in each, and the factors read off the formula."""
    assert [factor.polynomial for factor in step.G.factors] == [x4, x5, x6]
    assert [factor.polynomial for factor in step.H.factors] == [
        -(x2**2) * x3,
        0,
        0,
    ]


def test_the_homogeneous_parts_are_reported(step: UnipotentStep) -> None:
    assert step.quadratic == (0, 0, 0)
    assert step.cubic == (x2**2 * x3, 0, 0)


def test_the_step_establishes_EA_zero_and_no_more(  # noqa: N802
    step: UnipotentStep,
) -> None:
    """UNI-7. ``G`` displaces ``X_i`` by ``Y_i``, which has order one."""
    assert step.filtration_level == 0
    assert step.G.is_in_EA(0)
    assert not step.G.is_in_EA(1)


def test_H_reaches_a_higher_level_and_constrains_nothing(  # noqa: N802
    step: UnipotentStep,
) -> None:
    """``H`` displaces ``Y_i`` by a cubic, so it lies in ``EA^2``."""
    assert step.H.is_in_EA(2)


def test_the_target_leaves_MA_one(step: UnipotentStep) -> None:  # noqa: N802
    """UNI-8. The displacement has the linear part ``(Y, 0)``."""
    assert step.target.filtration_degree() == 0
    assert not step.target.is_in_MA(1)


def test_the_variables_are_the_fresh_ones_only(step: UnipotentStep) -> None:
    assert step.variables == FRESH
    assert step.target.variables == SIMPLE.variables + FRESH


def test_the_stabilization_honours_the_recorded_names(step: UnipotentStep) -> None:
    """A certificate names the variables it used, and they are not reinvented."""
    assert step.stabilized.variables == (x1, x2, x3, x4, x5, x6)
    assert step.stabilized.components == (x1 + x2**2 * x3, x2, x3, x4, x5, x6)


# --------------------------------------------------------------------------
# Verification, and what can fail
# --------------------------------------------------------------------------


def test_a_correct_step_verifies(step: UnipotentStep) -> None:
    assert step.verify() is None


def test_verification_is_idempotent(step: UnipotentStep) -> None:
    """STEP-2. Calling it twice is calling it once."""
    step.verify()

    assert step.verify() is None


def test_a_wrong_target_fails_the_identity() -> None:
    """UNI-1, the negative control.

    Without one there would be no way to tell whether the check verifies
    anything or merely happens to pass. One sign in the last block is enough.
    """
    wrong = over_field(
        PolynomialMap(
            (x1, x2, x3, x4, x5, x6),
            (x1 + x4, x2 + x5, x3 + x6, x4 + x2**2 * x3, x5, x6),
        )
    )

    with pytest.raises(VerificationError, match=r"\[UNI-1\]") as failure:
        UnipotentStep(SIMPLE, wrong, FRESH).verify()

    assert failure.value.obligation == "UNI-1"


def test_a_source_outside_MA_one_is_refused() -> None:  # noqa: N802
    """UNI-2, the negative control.

    ``(x1 + x2, x2)`` is Keller and its displacement has order one, so Section
    4 does not apply to it. This is the obligation ``alpoege13`` itself fails.
    """
    source = over_field(PolynomialMap((x1, x2), (x1 + x2, x2)))

    with pytest.raises(VerificationError, match=r"\[UNI-2\]") as failure:
        UnipotentStep.build(source).verify()

    assert failure.value.obligation == "UNI-2"
    assert "order 1" in failure.value.message


def test_alpoege13_itself_is_outside_MA_one() -> None:  # noqa: N802
    """The map this milestone starts from needs the normalization first.

    Two entries of the linear part of its displacement are non-zero, so the
    step refuses it and ``LinearStep.normalize`` is what repairs it. Stated as
    a test because the roadmap states it as a fact.
    """
    source = over_field(examples.alpoege13())

    assert not source.is_in_MA(1)

    with pytest.raises(VerificationError, match=r"\[UNI-2\]"):
        UnipotentStep.build(source).verify()

    assert LinearStep.normalize(source).target.is_in_MA(1)


def test_a_source_of_degree_four_is_refused() -> None:
    """UNI-3, the negative control.

    ``E(T) = X + T F_(2) + T^2 F_(3)`` has no slot for a quartic part.
    """
    source = over_field(PolynomialMap((x1, x2), (x1 + x2**4, x2)))

    with pytest.raises(VerificationError, match=r"\[UNI-3\]") as failure:
        UnipotentStep.build(source).verify()

    assert failure.value.obligation == "UNI-3"
    assert "degree 4" in failure.value.message


def test_a_source_that_is_not_Keller_is_refused() -> None:  # noqa: N802
    """UNI-4, the negative control.

    In ``MA^1`` a constant determinant is one, so what this excludes is a
    determinant that is not constant. ``(x1 + x2^2, x2 + x1^2)`` has
    determinant ``1 - 4 x1 x2``.
    """
    source = over_field(PolynomialMap((x1, x2), (x1 + x2**2, x2 + x1**2)))

    with pytest.raises(VerificationError, match=r"\[UNI-4\]") as failure:
        UnipotentStep.build(source).verify()

    assert failure.value.obligation == "UNI-4"


def test_the_source_is_checked_before_the_identity() -> None:
    """A failure about the caller's map is not reported as a failure of ours.

    The target here is wrong *and* the source is outside ``MA^1``. UNI-2 is
    what a reader needs to see.
    """
    source = over_field(PolynomialMap((x1, x2), (x1 + x2, x2)))
    wrong = over_field(PolynomialMap((x1, x2, x3, x4), (x1, x2, x3, x4)))

    with pytest.raises(VerificationError, match=r"\[UNI-2\]"):
        UnipotentStep(source, wrong, (x3, x4)).verify()


def test_a_target_of_the_wrong_dimension_fails() -> None:
    """UNI-5, the negative control for the half ``verify`` reaches."""
    wrong = over_field(PolynomialMap((x1, x2, x3), (x1, x2, x3)))

    with pytest.raises(VerificationError, match=r"\[UNI-5\]") as failure:
        UnipotentStep(SIMPLE, wrong, FRESH).verify()

    assert failure.value.obligation == "UNI-5"


def test_a_target_carrying_other_variables_fails() -> None:
    """UNI-5 again: the right dimension is not the right generators."""
    wrong = over_field(
        PolynomialMap(
            (x1, x2, x3, x5, x6, x7),
            (x1 + x5, x2 + x6, x3 + x7, x5 - x2**2 * x3, x6, x7),
        )
    )

    with pytest.raises(VerificationError, match=r"\[UNI-5\]"):
        UnipotentStep(SIMPLE, wrong, FRESH).verify()


def test_build_does_not_repair_the_source() -> None:
    """The three source obligations fail on a constructed step too.

    This is what the contract page calls unusual about this type. Everywhere
    else a constructed step compares the implementation against itself; here
    ``build`` cannot make UNI-2 true and does not try.
    """
    source = over_field(PolynomialMap((x1, x2), (x1 + x2, x2)))
    built = UnipotentStep.build(source)

    assert built.provenance is Provenance.CONSTRUCTED
    with pytest.raises(VerificationError, match=r"\[UNI-2\]"):
        built.verify()


# --------------------------------------------------------------------------
# Nilpotence
# --------------------------------------------------------------------------


def test_the_displacement_of_the_target_is_nilpotent(step: UnipotentStep) -> None:
    """UNI-9, cross-checked against the matrix power.

    ``verify`` takes the determinant of ``(X + T (target - X), T)``, which is
    the cheap route. Here the definition is computed directly, which is
    affordable at dimension six and not at dimension twenty-six. An
    independent cross-check, and it says so.
    """
    step.verify()

    variables = step.target.variables
    displacement = step.target.displacement().components
    jacobian = sp.Matrix(6, 6, lambda i, j: sp.diff(displacement[i], variables[j]))

    assert jacobian**6 == sp.zeros(6, 6)


def test_nilpotence_is_what_the_source_lacks() -> None:
    """The step exists because the source's own displacement is not nilpotent.

    Without this the previous test would pass for a step that did nothing.
    """
    variables = SIMPLE.variables
    displacement = SIMPLE.displacement().components
    jacobian = sp.Matrix(3, 3, lambda i, j: sp.diff(displacement[i], variables[j]))

    assert jacobian**3 == sp.zeros(3, 3)


# --------------------------------------------------------------------------
# Transport
#
# The sources here are not Keller maps and do not lie in ``MA^1``, so
# ``verify`` would refuse them. ``transport`` does not: it checks the incoming
# collision against the source and the outgoing one against the target, and
# neither needs the step to apply. That is the only way to exercise transport
# on a small map, because no small Keller map with a collision is known --
# which is the Jacobian conjecture.
# --------------------------------------------------------------------------

# (x1^2 + x2^3, x2, x3), whose cubic part is (x2^3, 0, 0). At the two points
# below it takes the value 8, so the appended block is visible.
CUBIC = over_field(PolynomialMap((x1, x2, x3), (x1**2 + x2**3, x2, x3)))
CUBIC_COLLISION = Collision(((1, 2, 3), (-1, 2, 3)), (9, 2, 3))


def test_transport_appends_the_value_of_the_cubic_part() -> None:
    """UNI-11. ``H^-1`` displaces ``Y`` by ``+F_(3)``, opposite to BCW-8.

    ``F_(3),1 = x2^3`` takes the value 8 at both points, so the appended block
    is ``+8`` and not ``-8``. The sign is the whole content of this test: with
    the other one the transported points are not points of the target.
    """
    moved = UnipotentStep.build(CUBIC).transport(CUBIC_COLLISION)

    assert moved.points == ((1, 2, 3, 8, 0, 0), (-1, 2, 3, 8, 0, 0))


def test_transport_leaves_the_image_where_it_was() -> None:
    """The image gains ``n`` zeros and nothing else.

    ``G`` adds the ``Y`` block of the padded image to its ``X`` block, and that
    block is zero. Unlike BCW-8 at ``m = 0``, the image cannot move here.
    """
    moved = UnipotentStep.build(CUBIC).transport(CUBIC_COLLISION)

    assert moved.image == (9, 2, 3, 0, 0, 0)


def test_transport_verifies_the_incoming_collision() -> None:
    """STEP-3. A collision that does not hold for the source is refused."""
    step = UnipotentStep.build(CUBIC)

    with pytest.raises(VerificationError, match=r"\[COL-3\]"):
        step.transport(Collision(((1, 2, 3), (0, 2, 3)), (9, 2, 3)))


def test_transport_preserves_the_number_of_points() -> None:
    """STEP-4, on four points rather than two.

    Distinctness needs no argument about the appended block: the points
    already differ in the first three coordinates.
    """
    source = over_field(PolynomialMap((x1, x2, x3), (x1**2, x2**2, x3)))
    collision = Collision(((1, 2, 3), (-1, 2, 3), (1, -2, 3), (-1, -2, 3)), (1, 4, 3))

    moved = UnipotentStep.build(source).transport(collision)

    assert len(moved.points) == 4
    assert len(set(moved.points)) == 4
    assert moved.dimension == 6


# --------------------------------------------------------------------------
# Value semantics
# --------------------------------------------------------------------------


def test_two_equal_steps_compare_equal_and_hash_alike() -> None:
    """STEP-5."""
    one = UnipotentStep(SIMPLE, SIMPLE_TARGET, FRESH)
    other = UnipotentStep(SIMPLE, SIMPLE_TARGET, FRESH)

    assert one == other
    assert hash(one) == hash(other)


def test_provenance_is_part_of_the_value() -> None:
    """A supplied step and a constructed one with the same target differ."""
    supplied = UnipotentStep(SIMPLE, SIMPLE_TARGET, FRESH)
    constructed = UnipotentStep.build(SIMPLE)

    assert supplied.target == constructed.target
    assert supplied != constructed


def test_a_step_does_not_compare_to_another_type() -> None:
    assert UnipotentStep(SIMPLE, SIMPLE_TARGET, FRESH) != SIMPLE


def test_the_representation_names_the_dimensions() -> None:
    text = repr(UnipotentStep(SIMPLE, SIMPLE_TARGET, FRESH))

    assert "3->6" in text
    assert "EA^0" in text
    assert "supplied" in text


# --------------------------------------------------------------------------
# In a chain
# --------------------------------------------------------------------------


def test_a_reduction_may_end_with_the_step() -> None:
    """The chain spans the normalization and the lift, and carries a collision."""
    source = over_field(PolynomialMap((x1, x2, x3), (2 * x1 + x2**2 * x3, x2, x3)))
    first = LinearStep.normalize(source)
    chain = Reduction((first, UnipotentStep.build(first.target)))

    assert chain.verify() is None
    assert chain.source.dimension == 3
    assert chain.target.dimension == 6
    assert chain.filtration_level() == 0


def test_the_step_refuses_its_own_target() -> None:
    """A chain applies it once. The target is not in ``MA^1``, and UNI-2 says so."""
    step = UnipotentStep.build(SIMPLE)

    with pytest.raises(VerificationError, match=r"\[UNI-2\]"):
        UnipotentStep.build(step.target).verify()


def test_the_filtration_level_of_a_chain_is_not_infinite() -> None:
    """Unlike ``LinearStep`` and ``TranslationStep``, this step bounds it."""
    step = UnipotentStep.build(SIMPLE)

    assert step.filtration_level == 0
    assert Reduction((step,)).filtration_level() != math.inf


# --------------------------------------------------------------------------
# The map the milestone is about
# --------------------------------------------------------------------------


@pytest.mark.slow
def test_alpoege13_lifts_to_twenty_six_variables() -> None:
    """13 to 26, degree three, and the three collision points survive.

    The figure the roadmap carries for work package 1. The homogenization of
    work package 2 takes it to 27.
    """
    first = LinearStep.normalize(over_field(examples.alpoege13()))
    lift = UnipotentStep.build(first.target)
    chain = Reduction((first, lift))

    assert chain.verify() is None
    assert lift.target.dimension == 26
    assert lift.target.degree() == 3
    assert lift.target.determinant() == 1

    moved = chain.transport(examples.alpoege13_collision())

    assert len(moved.points) == 3
    assert moved.verify(lift.target) is None
