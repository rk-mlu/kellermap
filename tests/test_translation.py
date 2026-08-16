"""The translation step: the first factor of Proposition (1.1).

What can fail on supplied data is TRA-1 and the first clause of TRA-6. TRA-3
and TRA-4 follow from TRA-1, TRA-2 is a constructor invariant, and the
``MA^0`` clause of TRA-6 follows from the first. These four are checked on
their successful path only, because a test for them would have to force the
object into a state it cannot reach.

The plan for this work package also asked for failure cases for TRA-3, TRA-4
and both clauses of TRA-6. While writing them it turned out that three of them
are unreachable, and the roadmap is corrected accordingly.
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
    TranslationStep,
    VerificationError,
    examples,
    over_field,
)

x, y = sp.symbols("x y")
T = sp.Symbol("T")


@pytest.fixture
def keller() -> PolynomialMap:
    """A Keller map in ``MA^1`` that fixes the origin."""
    return over_field(examples.quadratic_shear())


@pytest.fixture
def moved(keller: PolynomialMap) -> PolynomialMap:
    """The same map, displaced by ``(1, 2)``."""
    return over_field(PolynomialMap((x, y), (x + y**2 + 1, y + 2)))


@pytest.fixture
def square() -> PolynomialMap:
    """Not injective, and displaced by ``(1, 1)``: it carries a collision."""
    return over_field(PolynomialMap((x, y), (x**2 + 1, y + 1)))


# --------------------------------------------------------------------------
# Construction
# --------------------------------------------------------------------------


def test_it_satisfies_the_step_protocol(moved: PolynomialMap) -> None:
    assert isinstance(TranslationStep.normalize(moved), Step)


def test_normalize_takes_off_F0(moved: PolynomialMap, keller: PolynomialMap) -> None:  # noqa: N802
    step = TranslationStep.normalize(moved)

    assert step.shift == (1, 2)
    assert step.target == keller
    assert step.is_normalizing


def test_a_map_in_MA0_gets_the_identity_step(keller: PolynomialMap) -> None:  # noqa: N802
    """Not refused but displaced by zero.

    This saves a case distinction for every caller who does not know in advance
    whether their map fixes the origin.
    """
    step = TranslationStep.normalize(keller)

    assert step.shift == (0, 0)
    assert step.target == keller
    assert len(step.translation) == 0
    assert step.verify() is None


def test_build_accepts_any_constant_shift(keller: PolynomialMap) -> None:
    step = TranslationStep.build(keller, (3, -1))

    assert step.target == over_field(
        PolynomialMap((x, y), (x + y**2 - 3, y + 1)),
    )
    assert not step.is_normalizing
    assert step.verify() is None


def test_the_supplied_route_records_supplied(
    moved: PolynomialMap, keller: PolynomialMap
) -> None:
    """TRA-8: the public constructor can say nothing else."""
    supplied = TranslationStep(moved, keller, (1, 2), normalizing=True)

    assert supplied.provenance is Provenance.SUPPLIED
    assert TranslationStep.normalize(moved).provenance is Provenance.CONSTRUCTED
    assert supplied.verify() is None


# --------------------------------------------------------------------------
# TRA-2: the displacement is constant
# --------------------------------------------------------------------------


def test_a_shift_involving_a_generator_is_refused(keller: PolynomialMap) -> None:
    """Otherwise the Jacobian matrix would not be the identity."""
    with pytest.raises(ValueError, match="coefficient domain"):
        TranslationStep.build(keller, (y, 0))


def test_a_shift_outside_the_domain_is_refused() -> None:
    """Over ``ZZ`` the value ``1/2`` is not a constant of the ring."""
    integral = examples.quadratic_shear()

    with pytest.raises(ValueError, match="coefficient domain"):
        TranslationStep.build(integral, (sp.Rational(1, 2), 0))


def test_a_domain_parameter_is_admitted() -> None:
    """A translation by ``T`` over ``k[T]`` is a translation.

    The same distinction as in COL-2 and BCW-3: parameters of the coefficient
    domain are not variables of the map.
    """
    parametric = examples.parametric_shear()
    step = TranslationStep.build(parametric, (T, 1))

    assert step.shift == (T, 1)
    assert step.verify() is None


def test_a_miscounted_shift_is_refused(keller: PolynomialMap) -> None:
    with pytest.raises(ValueError, match="entries"):
        TranslationStep.build(keller, (1,))


@pytest.mark.parametrize("wrong", [None, 0, "F", (x, y)])
def test_the_maps_must_be_polynomial_maps(keller: PolynomialMap, wrong: object) -> None:
    with pytest.raises(TypeError):
        TranslationStep(wrong, keller, (0, 0))  # type: ignore[arg-type]

    with pytest.raises(TypeError):
        TranslationStep(keller, wrong, (0, 0))  # type: ignore[arg-type]


def test_the_dimensions_must_agree(keller: PolynomialMap) -> None:
    other = over_field(PolynomialMap((x,), (x**2,)))

    with pytest.raises(ValueError, match="a translation keeps it"):
        TranslationStep(keller, other, (0, 0))


# --------------------------------------------------------------------------
# TRA-1 and TRA-6: what can fail on supplied data
# --------------------------------------------------------------------------


def test_a_wrong_target_fails_TRA1(moved: PolynomialMap, keller: PolynomialMap) -> None:  # noqa: N802
    """A negative control: without it the passing case says nothing."""
    step = TranslationStep(moved, keller, (1, 3))

    with pytest.raises(VerificationError) as failure:
        step.verify()

    assert failure.value.obligation == "TRA-1"


def test_a_wrong_shift_fails_TRA6(keller: PolynomialMap) -> None:  # noqa: N802
    """The identity holds and the claim about ``F(0)`` does not.

    Exactly the distinction TRA-6 draws: ``build`` gives a valid certificate,
    and only the predicate ``normalizing`` ties it to ``F(0)``.
    """
    step = TranslationStep.build(keller, (5, 0), normalizing=True)

    with pytest.raises(VerificationError) as failure:
        step.verify()

    assert failure.value.obligation == "TRA-6"
    assert "F(0)" in failure.value.message


def test_a_step_that_makes_no_claim_carries_no_obligation(
    keller: PolynomialMap,
) -> None:
    assert TranslationStep.build(keller, (5, 0)).verify() is None


def test_verification_is_idempotent(moved: PolynomialMap) -> None:
    """STEP-2: checking twice is like checking once."""
    step = TranslationStep.normalize(moved)

    assert step.verify() is None
    assert step.verify() is None


# --------------------------------------------------------------------------
# TRA-3 and TRA-5: the factorization and the filtration degree
# --------------------------------------------------------------------------


def test_the_translation_is_exhibited(moved: PolynomialMap) -> None:
    """TRA-3: one factor per non-zero entry, in ascending order."""
    factors = TranslationStep.normalize(moved).translation.factors

    assert [factor.index for factor in factors] == [0, 1]
    assert [factor.polynomial for factor in factors] == [-1, -2]


def test_only_nonzero_entries_buy_a_factor(keller: PolynomialMap) -> None:
    step = TranslationStep.build(keller, (0, 7))
    factors = step.translation.factors

    assert [factor.index for factor in factors] == [1]


def test_the_inverse_is_read_off_the_definition(moved: PolynomialMap) -> None:
    exhibited = TranslationStep.normalize(moved).translation

    assert [factor.polynomial for factor in exhibited.inverse().factors] == [2, 1]


def test_the_transformation_has_filtration_degree_minus_one(
    moved: PolynomialMap,
) -> None:
    """It lies in no ``EA^d`` with ``d >= 0``, because it leaves ``MA^0``."""
    exhibited = TranslationStep.normalize(moved).translation

    assert exhibited.filtration_degree() == -1
    assert not exhibited.is_in_EA(0)


def test_the_step_establishes_no_level(moved: PolynomialMap) -> None:
    """TRA-5: the degree belongs to the transformation and not to the step."""
    assert TranslationStep.normalize(moved).filtration_level == math.inf


def test_the_determinant_survives(moved: PolynomialMap) -> None:
    """TRA-4 on its successful path."""
    step = TranslationStep.normalize(moved)

    assert step.target.determinant() == step.source.determinant() == 1


# --------------------------------------------------------------------------
# TRA-7: Transport
# --------------------------------------------------------------------------


def test_transport_moves_the_image_and_not_the_points(square: PolynomialMap) -> None:
    collision = Collision.at(square, ((1, 0), (-1, 0)))
    step = TranslationStep.normalize(square)

    carried = step.transport(collision)

    assert carried.points == collision.points
    assert collision.image == (2, 1)
    assert carried.image == (1, 0)


def test_transport_refuses_a_collision_of_another_map(square: PolynomialMap) -> None:
    """STEP-3: the check happens before and not only after.

    The displacement leaves the dimension as it is, so the length of the
    reported points does not tell the input check from the output check. The
    image does: the source sends the two points to ``(2, 1)`` and the target,
    displaced by ``-shift``, to ``(1, 0)``. Without the last line the test
    stayed green when the input check was removed, because the output check
    caught the same case one line later.

    The source here is ``square`` and not ``keller``. ``keller`` fixes the
    origin, its normalisation displaces by zero, and source and target are then
    the same map. A test on it could not tell the two checks apart at all.
    """
    step = TranslationStep.normalize(square)
    foreign = Collision(((1, 0), (-1, 0)), (0, 0))

    with pytest.raises(VerificationError) as failure:
        step.transport(foreign)

    assert failure.value.obligation == "COL-3"
    assert "(2, 1)" in str(failure.value), str(failure.value)


def test_transport_refuses_its_own_wrong_result(square: PolynomialMap) -> None:
    """STEP-2 and TRA-7: the output is checked, and that is reachable.

    ``transport`` does not call ``verify()`` of the step, and a
    ``TranslationStep`` takes its target as given. For a supplied step with a
    wrong target the output check is the only thing that stops a wrong
    transport.

    Up to 0.4.0rc13 no test told it apart from the input check. A mutation probe
    over ``contracts.md`` showed it.
    """
    honest = TranslationStep.normalize(square)
    genuine = Collision.at(square, ((1, 0), (-1, 0)))
    wrong = PolynomialMap(
        honest.target.variables,
        (honest.target.components[0] + 1,) + honest.target.components[1:],
    )
    supplied = TranslationStep(square, wrong, honest.shift)

    with pytest.raises(VerificationError) as failure:
        supplied.transport(genuine)

    assert failure.value.obligation == "COL-3"
    assert "(2, 1)" not in str(failure.value), str(failure.value)


# --------------------------------------------------------------------------
# STEP-5 and the chain
# --------------------------------------------------------------------------


def test_equality_is_by_content_including_provenance(
    moved: PolynomialMap, keller: PolynomialMap
) -> None:
    constructed = TranslationStep.normalize(moved)
    supplied = TranslationStep(moved, keller, (1, 2), normalizing=True)

    assert constructed == TranslationStep.normalize(moved)
    assert hash(constructed) == hash(TranslationStep.normalize(moved))
    assert constructed != supplied
    assert constructed != TranslationStep.build(moved, (1, 2))
    assert constructed.__eq__(42) is NotImplemented


def test_the_repr_names_the_shift_and_the_provenance(moved: PolynomialMap) -> None:
    text = repr(TranslationStep.normalize(moved))

    assert "shift=(1, 2)" in text
    assert "provenance=constructed" in text


def test_the_two_factors_of_proposition_1_1_chain(
    moved: PolynomialMap, keller: PolynomialMap
) -> None:
    """The translation first, then the linear part, in that order."""
    translation = TranslationStep.normalize(moved)
    linear = LinearStep.normalize(translation.target)
    chain = Reduction([translation, linear])

    assert chain.verify() is None
    assert chain.source == moved
    assert chain.target.is_in_MA(1)


def test_a_translation_does_not_lower_the_reported_level(
    moved: PolynomialMap,
) -> None:
    """RED-6: the level describes the target and the translation the source.

    The BCW step removes ``y^2`` from the first component and reaches ``EA^0``.
    The chain reports ``0`` and not ``-1``.
    """
    from kellermap.bcw import BCWStep, Fresh

    u, v = sp.symbols("u v")
    translation = TranslationStep.normalize(moved)
    linear = LinearStep.normalize(translation.target)
    bcw = BCWStep.build(linear.target, 0, Fresh(y, u), Fresh(y, v), 0)
    chain = Reduction([translation, linear, bcw])

    assert chain.verify() is None
    assert chain.filtration_level() == 0
    assert chain.dimensions() == (2, 2, 2, 4)


def test_the_linear_step_names_the_translation(moved: PolynomialMap) -> None:
    """LIN-6: the refusal now names a step that exists."""
    with pytest.raises(ValueError, match="TranslationStep.normalize"):
        LinearStep.normalize(moved)
