"""Steps, and chains of steps.

The weight lies on what a certificate is to achieve. LIN-1 and LIN-6 are the
two obligations that can fail on supplied data, RED-2 holds the chain together,
and RED-4 makes a failure name its place.

LIN-2 and LIN-3 follow from LIN-1 and cannot fail on supplied data. They stand
as self-checks of the library and are accordingly checked here on their
successful path only.
"""

import math

import pytest
import sympy as sp

from kellermap import (
    Collision,
    Dilation,
    ElementaryAutomorphism,
    ElementaryFactor,
    LinearAutomorphism,
    PolynomialMap,
    Transposition,
    VerificationError,
    examples,
    over_field,
)
from kellermap.reduction import LinearStep, Provenance, Reduction, Step

x1, x2, x3 = sp.symbols("x1 x2 x3")

ALPOEGE = over_field(examples.alpoege())

ALPOEGE_POINTS = (
    (0, 0, sp.Rational(-1, 4)),
    (1, sp.Rational(-3, 2), sp.Rational(13, 2)),
    (-1, sp.Rational(3, 2), sp.Rational(13, 2)),
)

IDENTITY = PolynomialMap.from_ring(ALPOEGE.ring, ALPOEGE.ring.gens)


@pytest.fixture(scope="module")
def normalization() -> LinearStep:
    return LinearStep.normalize(ALPOEGE)


@pytest.fixture
def swap() -> LinearAutomorphism:
    return LinearAutomorphism([Transposition(ALPOEGE.ring, 0, 1)])


# --------------------------------------------------------------------------
# The step protocol
# --------------------------------------------------------------------------


def test_a_linear_step_satisfies_the_protocol(normalization: LinearStep) -> None:
    assert isinstance(normalization, Step)


def test_the_protocol_is_structural() -> None:
    """Nothing has to inherit in order to be a step."""
    assert not isinstance(ALPOEGE, Step)


def test_verification_is_idempotent(normalization: LinearStep) -> None:
    """STEP-2: checking twice is like checking once."""
    assert normalization.verify() is None
    assert normalization.verify() is None


# --------------------------------------------------------------------------
# LinearStep: construction
# --------------------------------------------------------------------------


def test_a_linear_step_keeps_the_dimension(swap: LinearAutomorphism) -> None:
    wider = PolynomialMap(sp.symbols("a b c d"), sp.symbols("a b c d"))

    with pytest.raises(ValueError, match="keeps it"):
        LinearStep(ALPOEGE, wider, swap)


def test_the_source_must_be_a_map(swap: LinearAutomorphism) -> None:
    with pytest.raises(TypeError, match="source must be"):
        LinearStep(ALPOEGE.components, ALPOEGE, swap)


def test_the_target_must_be_a_map(swap: LinearAutomorphism) -> None:
    with pytest.raises(TypeError, match="target must be"):
        LinearStep(ALPOEGE, ALPOEGE.components, swap)


def test_the_transformation_must_be_linear() -> None:
    with pytest.raises(TypeError, match="LinearAutomorphism"):
        LinearStep(ALPOEGE, ALPOEGE, ALPOEGE)


def test_normalize_needs_an_invertible_linear_part() -> None:
    """Without J(F)(0) in GL_n(k) Proposition (1.1) does not apply."""
    degenerate = over_field(PolynomialMap((x1, x2, x3), (x1**2, x2, x3)))

    with pytest.raises(ValueError, match="singular"):
        LinearStep.normalize(degenerate)


def test_normalize_needs_the_origin_to_be_fixed() -> None:
    """The translation comes before the linearisation.

    Proposition (1.1) decomposes F as (X + F(0)) o F_(1) o F'. ``normalize``
    builds the last factor and presupposes the first two. Without F(0) = 0 it
    used to give a step that failed its own verification.
    """
    affine = over_field(examples.unit_translation())

    assert not affine.is_in_MA(0)

    with pytest.raises(ValueError, match="translation"):
        LinearStep.normalize(affine)


def test_LIN6_a_normalizing_claim_over_a_shifted_source() -> None:  # noqa: N802
    """And a supplied step says what the cause is.

    LIN-6 used to report only that the target does not lie in MA^1. That is
    correct, and the cause stands one level earlier.
    """
    affine = over_field(examples.unit_translation())
    identity = LinearAutomorphism([Transposition(affine.ring, 0, 1)])

    with pytest.raises(VerificationError) as failure:
        LinearStep(
            affine, identity.apply_to(affine), identity, normalizing=True
        ).verify()

    assert failure.value.obligation == "LIN-6"
    assert "translation" in str(failure.value)


def test_a_translation_is_elementary() -> None:
    """Unlike the dilation it needs no type of its own.

    ``X_i |-> X_i - c_i`` displaces ``X_i`` by a constant, and that constant is
    free of ``X_i``, which is exactly what BCW call elementary. It lies in no
    ``EA^d`` with ``d >= 0``, however, because ``EA^d`` is defined inside
    ``MA^d`` and a translation leaves ``MA^0``.
    """
    affine = over_field(PolynomialMap((x1, x2, x3), (x1 + 1, x2, x3 + 2)))
    translation = ElementaryAutomorphism(
        [
            ElementaryFactor(affine.ring, index, -value)
            for index, value in enumerate(affine(0, 0, 0))
        ]
    )
    shifted = translation.apply_to(affine)

    assert translation.filtration_degree() == -1
    assert not translation.is_in_EA(0)
    assert shifted.is_in_MA(0)
    assert shifted.determinant() == affine.determinant()
    assert LinearStep.normalize(shifted).verify() is None


# --------------------------------------------------------------------------
# LIN-1 to LIN-6
# --------------------------------------------------------------------------


def test_the_normalization_verifies(normalization: LinearStep) -> None:
    assert normalization.verify() is None
    assert normalization.is_normalizing
    assert not normalization.is_elementary


def test_LIN1_a_target_that_is_not_the_composite(  # noqa: N802
    swap: LinearAutomorphism,
) -> None:
    with pytest.raises(VerificationError) as failure:
        LinearStep(ALPOEGE, ALPOEGE, swap).verify()

    assert failure.value.obligation == "LIN-1"
    assert failure.value.step is None


def test_LIN1_a_transformation_over_another_ring() -> None:  # noqa: N802
    other = over_field(PolynomialMap(sp.symbols("a b c"), sp.symbols("a b c")))
    foreign = LinearAutomorphism([Transposition(other.ring, 0, 1)])

    with pytest.raises(VerificationError) as failure:
        LinearStep(ALPOEGE, ALPOEGE, foreign).verify()

    assert failure.value.obligation == "LIN-1"


def test_LIN3_the_determinant_is_accounted_for(  # noqa: N802
    normalization: LinearStep,
) -> None:
    """From -2 to 1, and the factor -1/2 stands in the certificate."""
    assert ALPOEGE.determinant() == -2
    assert normalization.transformation.determinant() == sp.Rational(-1, 2)
    assert normalization.target.determinant() == 1


def test_LIN4_the_transformation_need_not_be_elementary(  # noqa: N802
    normalization: LinearStep,
) -> None:
    """And here it is not: determinant -1/2, while EA_n(k) has only 1."""
    assert not normalization.transformation.is_elementary
    assert normalization.verify() is None


def test_LIN6_a_step_that_claims_to_normalize_and_does_not(  # noqa: N802
    swap: LinearAutomorphism,
) -> None:
    with pytest.raises(VerificationError) as failure:
        LinearStep.build(ALPOEGE, swap, normalizing=True).verify()

    assert failure.value.obligation == "LIN-6"


def test_LIN6_is_only_claimed_when_declared(swap: LinearAutomorphism) -> None:  # noqa: N802
    """The same step without the claim does not carry the obligation."""
    assert LinearStep.build(ALPOEGE, swap).verify() is None


def test_the_normalization_reaches_MA1(normalization: LinearStep) -> None:  # noqa: N802
    assert not ALPOEGE.is_in_MA(1)
    assert normalization.target.is_in_MA(1)


# --------------------------------------------------------------------------
# Provenance
# --------------------------------------------------------------------------


def test_build_records_the_target_as_constructed(swap: LinearAutomorphism) -> None:
    assert LinearStep.build(ALPOEGE, swap).provenance is Provenance.CONSTRUCTED


def test_a_supplied_target_is_recorded_as_such(swap: LinearAutomorphism) -> None:
    step = LinearStep(ALPOEGE, swap.apply_to(ALPOEGE), swap)

    assert step.provenance is Provenance.SUPPLIED
    assert step.verify() is None


def test_the_reduction_takes_the_weaker_provenance(
    normalization: LinearStep, swap: LinearAutomorphism
) -> None:
    supplied = LinearStep(ALPOEGE, swap.apply_to(ALPOEGE), swap)

    assert Reduction([supplied]).provenance is Provenance.SUPPLIED
    assert Reduction([normalization]).provenance is Provenance.CONSTRUCTED


# --------------------------------------------------------------------------
# Transport
# --------------------------------------------------------------------------


@pytest.fixture(scope="module")
def collision() -> Collision:
    return Collision.at(ALPOEGE, ALPOEGE_POINTS)


def test_LIN5_the_points_do_not_move(  # noqa: N802
    normalization: LinearStep, collision: Collision
) -> None:
    moved = normalization.transport(collision)

    assert moved.points == collision.points
    assert len(moved) == 3


def test_LIN5_the_image_moves(  # noqa: N802
    normalization: LinearStep, collision: Collision
) -> None:
    """(-1/4, 0, 0) becomes (0, 0, -1/4), the image BCW17 carries."""
    moved = normalization.transport(collision)

    assert collision.image == (sp.Rational(-1, 4), 0, 0)
    assert moved.image == (0, 0, sp.Rational(-1, 4))


def test_transport_rejects_a_foreign_collision(normalization: LinearStep) -> None:
    """STEP-3: what comes in is checked against the source first.

    Source and target of a linear step have the same dimension, so the length
    of the reported points does not tell the two checks apart. The image does:
    the source sends the points to ``(-1/4, 0, 0)`` and the target to
    ``(0, 0, -1/4)``. Without this line the test stayed green when the input
    check was removed, because the output check caught the same case one line
    later.
    """
    wrong = Collision(ALPOEGE_POINTS, (0, 0, 0))

    with pytest.raises(VerificationError) as failure:
        normalization.transport(wrong)

    assert failure.value.obligation == "COL-3"
    assert "(-1/4, 0, 0)" in str(failure.value), str(failure.value)


def test_transport_verifies_the_result(
    normalization: LinearStep, collision: Collision
) -> None:
    assert normalization.transport(collision).verify(normalization.target) is None


def test_transport_rejects_its_own_wrong_result(collision: Collision) -> None:
    """STEP-2 and LIN-5: the output is checked, and that is reachable.

    ``transport`` does not call ``verify()`` of the step, and a ``LinearStep``
    takes its target as given, which is what makes LIN-1 a real check. For a
    supplied step with a wrong target the output check is therefore the only
    thing standing between a false certificate and an apparently machine-checked
    statement about the target.

    Up to 0.4.0rc13 no test told the two checks apart. A mutation probe showed
    it: either one could be removed on its own without the suite turning
    red.
    """
    honest = LinearStep.normalize(ALPOEGE)
    wrong = PolynomialMap(
        honest.target.variables,
        (honest.target.components[0] + 1,) + honest.target.components[1:],
    )
    supplied = LinearStep(ALPOEGE, wrong, honest.transformation)

    with pytest.raises(VerificationError) as failure:
        supplied.transport(collision)

    assert failure.value.obligation == "COL-3"
    assert "(-1/4, 0, 0)" not in str(failure.value), str(failure.value)


# --------------------------------------------------------------------------
# Reduction
# --------------------------------------------------------------------------


def test_RED1_a_reduction_needs_a_step() -> None:  # noqa: N802
    with pytest.raises(ValueError, match="at least one step"):
        Reduction([])


def test_only_steps_may_enter(normalization: LinearStep) -> None:
    with pytest.raises(TypeError, match="Step protocol"):
        Reduction([normalization, ALPOEGE])


def test_source_and_target_are_the_ends(normalization: LinearStep) -> None:
    chain = Reduction([normalization])

    assert chain.source == ALPOEGE
    assert chain.target == normalization.target


def test_RED2_adjacency_is_checked(  # noqa: N802
    normalization: LinearStep, swap: LinearAutomorphism
) -> None:
    """The second step does not begin where the first one ends."""
    detached = LinearStep.build(ALPOEGE, swap)

    with pytest.raises(VerificationError) as failure:
        Reduction([normalization, detached]).verify()

    assert failure.value.obligation == "RED-2"
    assert failure.value.step == 1


def test_a_well_formed_chain_of_two_verifies(normalization: LinearStep) -> None:
    second = LinearStep.build(
        normalization.target,
        LinearAutomorphism([Dilation(ALPOEGE.ring, 0, 3)]),
    )
    chain = Reduction([normalization, second])

    assert chain.verify() is None
    assert chain.target.determinant() == 3


def test_LIN6_a_singular_linear_part_in_a_supplied_step() -> None:  # noqa: N802
    """A supplied step may claim what normalize() refuses."""
    degenerate = over_field(PolynomialMap((x1, x2, x3), (x1**2, x2, x3)))
    identity = LinearAutomorphism([Transposition(degenerate.ring, 0, 1)])

    with pytest.raises(VerificationError) as failure:
        LinearStep(
            degenerate, identity.apply_to(degenerate), identity, normalizing=True
        ).verify()

    assert failure.value.obligation == "LIN-6"
    assert "singular" in str(failure.value)


def test_RED5_a_transport_failure_names_its_step(
    normalization: LinearStep, collision: Collision, swap: LinearAutomorphism
) -> None:
    """The transport locates a failure just as the verification does."""
    detached = LinearStep.build(ALPOEGE, swap)

    with pytest.raises(VerificationError) as failure:
        Reduction([normalization, detached]).transport(collision)

    assert failure.value.step == 1


def test_RED5_a_foreign_collision_is_not_blamed_on_the_first_step(  # noqa: N802
    normalization: LinearStep,
) -> None:
    """The fold checks the input itself, and the message shows it.

    The check at the fold and that of the first step compare against the same
    map: RED-2 requires ``steps[0].source`` to be the source of the chain. What
    tells them apart is the location. If the collision fails only in the first
    step, the error is marked ``step = 0`` and thereby attributed to a step at
    which nothing is wrong. The caller brought the wrong collision.

    A mutation probe showed that up to 0.4.0rc13 the line at the fold could be
    removed without anything turning red.
    """
    wrong = Collision(ALPOEGE_POINTS, (0, 0, 0))

    with pytest.raises(VerificationError) as failure:
        Reduction([normalization]).transport(wrong)

    assert failure.value.obligation == "COL-3"
    assert failure.value.step is None


def test_a_reduction_does_not_concatenate_with_other_types(
    normalization: LinearStep,
) -> None:
    with pytest.raises(TypeError):
        Reduction([normalization]) + normalization  # type: ignore[operator]


def test_a_step_compares_unequal_to_other_types(normalization: LinearStep) -> None:
    assert normalization != object()


def test_RED4_a_failure_names_its_step(normalization: LinearStep) -> None:  # noqa: N802
    broken = LinearStep(
        normalization.target,
        normalization.target,
        LinearAutomorphism([Transposition(ALPOEGE.ring, 0, 1)]),
    )

    with pytest.raises(VerificationError) as failure:
        Reduction([normalization, broken]).verify()

    assert failure.value.obligation == "LIN-1"
    assert failure.value.step == 1


def test_RED5_transport_folds_through_the_chain(  # noqa: N802
    normalization: LinearStep, collision: Collision
) -> None:
    second = LinearStep.build(
        normalization.target,
        LinearAutomorphism([Transposition(ALPOEGE.ring, 0, 1)]),
    )
    chain = Reduction([normalization, second])

    carried = chain.transport(collision)

    assert len(carried) == 3
    assert carried.points == collision.points
    assert carried.image == (0, 0, sp.Rational(-1, 4))
    assert carried.verify(chain.target) is None


def test_RED5_the_number_of_points_is_preserved(  # noqa: N802
    normalization: LinearStep, collision: Collision
) -> None:
    """STEP-4: a counterexample stays one."""
    assert len(Reduction([normalization]).transport(collision)) == len(collision)


def test_RED6_a_linear_step_constrains_no_level(  # noqa: N802
    normalization: LinearStep,
) -> None:
    assert normalization.filtration_level == math.inf
    assert Reduction([normalization]).filtration_level() == math.inf


def test_RED3_the_chain_reports_degrees_rather_than_constraining_them(  # noqa: N802
    normalization: LinearStep,
) -> None:
    chain = Reduction([normalization])

    assert chain.degrees() == (7, 7)
    assert chain.dimensions() == (3, 3)


# --------------------------------------------------------------------------
# RED-8: value semantics
# --------------------------------------------------------------------------


def test_a_reduction_is_a_sequence(normalization: LinearStep) -> None:
    chain = Reduction([normalization])

    assert len(chain) == 1
    assert list(chain) == [normalization]
    assert chain[0] is normalization


def test_slicing_returns_a_reduction(normalization: LinearStep) -> None:
    second = LinearStep.build(
        normalization.target,
        LinearAutomorphism([Dilation(ALPOEGE.ring, 0, 3)]),
    )
    chain = Reduction([normalization, second])

    assert chain[:1] == Reduction([normalization])
    assert isinstance(chain[:1], Reduction)


def test_concatenation(normalization: LinearStep) -> None:
    second = LinearStep.build(
        normalization.target,
        LinearAutomorphism([Dilation(ALPOEGE.ring, 0, 3)]),
    )

    assert Reduction([normalization]) + Reduction([second]) == Reduction(
        [normalization, second]
    )


def test_equality_and_hash(normalization: LinearStep) -> None:
    assert Reduction([normalization]) == Reduction([normalization])
    assert hash(Reduction([normalization])) == hash(Reduction([normalization]))
    assert Reduction([normalization]) != object()


def test_steps_compare_by_content(swap: LinearAutomorphism) -> None:
    left = LinearStep(ALPOEGE, swap.apply_to(ALPOEGE), swap)
    right = LinearStep(ALPOEGE, swap.apply_to(ALPOEGE), swap)

    assert left == right
    assert hash(left) == hash(right)


def test_provenance_is_part_of_the_value(swap: LinearAutomorphism) -> None:
    """Otherwise there would be equal objects with different attributes.

    Both steps claim the same identity and only one of them is evidence for it:
    for the other the library computed the target itself. Were they equal, a
    set or a cache could replace the stronger by the weaker without anyone
    noticing.
    """
    supplied = LinearStep(ALPOEGE, swap.apply_to(ALPOEGE), swap)
    constructed = LinearStep.build(ALPOEGE, swap)

    assert supplied.target == constructed.target
    assert supplied != constructed
    assert Reduction([supplied]) != Reduction([constructed])


def test_the_public_constructor_cannot_claim_construction(
    swap: LinearAutomorphism,
) -> None:
    """A target that reaches the constructor came from outside."""
    with pytest.raises(TypeError):
        LinearStep(
            ALPOEGE,
            swap.apply_to(ALPOEGE),
            swap,
            provenance=Provenance.CONSTRUCTED,  # type: ignore[call-arg]
        )


def test_repr_is_readable(normalization: LinearStep) -> None:
    assert "normalizing=True" in repr(normalization)
    assert "steps=1" in repr(Reduction([normalization]))
