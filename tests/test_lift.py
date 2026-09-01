"""The symmetric lift as a certificate.

The control is external and is the same file the compression is checked
against: lifting Thompson's compressed twenty has to give a form of 350
monomials, which is the figure Theorem 3 of arXiv:2608.12543v1 reports.

SYM-7 is the one obligation this library states and does not check, so the
determinant appears here twice: once at dimension six, where it is an
independent cross-check in the sense ``AGENTS.md`` gives that phrase, and once
as the reason a source that fails SYM-4 makes the lift fail too.

The small sources here are not Keller maps and say so where it matters.
``transport`` does not need SYM-4, and no small Keller map with a collision is
known.
"""

import math

import pytest
import sympy as sp

from kellermap import (
    Collision,
    CompressionStep,
    PolynomialMap,
    Provenance,
    Reduction,
    Step,
    SymmetricLiftStep,
    VerificationError,
    examples,
    over_field,
)
from kellermap.bcw import HomogenizationStep, UnipotentStep
from kellermap.variables import IndexedVariableFactory

x1, x2, x3 = sp.symbols("x1 x2 x3")

# (x1 + x2^3, x2, x3): homogeneous of degree three and a Keller map, with no
# collision. Everything about verification uses it.
KELLER = over_field(PolynomialMap((x1, x2, x3), (x1 + x2**3, x2, x3)))

# (x1 + x1^2) in one variable: homogeneous of degree two, not a Keller map, and
# ``t + t^2`` folds 0 onto -1, so there is a pair to lift.
FOLD = over_field(PolynomialMap((x1,), (x1 + x1**2,)))
FOLD_COLLISION = Collision(((0,), (-1,)), (0,))


@pytest.fixture(scope="module")
def lifted() -> SymmetricLiftStep:
    return SymmetricLiftStep.build(KELLER)


# --------------------------------------------------------------------------
# Construction
# --------------------------------------------------------------------------


def test_the_step_is_a_step(lifted: SymmetricLiftStep) -> None:
    assert isinstance(lifted, Step)


def test_the_lift_doubles_the_dimension(lifted: SymmetricLiftStep) -> None:
    assert lifted.source.dimension == 3
    assert lifted.target.dimension == 6


def test_the_form_is_homogeneous_of_one_degree_more(
    lifted: SymmetricLiftStep,
) -> None:
    """SYM-6. The displacement is cubic, so ``P`` is quartic."""
    form = sp.Poly(lifted.form, *lifted.variables)

    assert {sum(monomial) for monomial in form.monoms()} == {4}


def test_the_target_is_the_gradient_of_the_form(lifted: SymmetricLiftStep) -> None:
    """SYM-2, recomputed here rather than read off ``verify``.

    A map that equals ``id - grad`` of an exhibited polynomial is a gradient
    map, and this is what a reader checks to see it.
    """
    gradient = tuple(
        sp.expand(variable - sp.diff(lifted.form, variable))
        for variable in lifted.variables
    )

    assert gradient == tuple(sp.expand(c) for c in lifted.target.components)


def test_the_coefficient_domain_gains_i(lifted: SymmetricLiftStep) -> None:
    """SYM-5. Every other step in this library keeps the domain."""
    assert lifted.source.ring.domain == sp.QQ
    assert lifted.target.ring.domain == sp.QQ_I


def test_a_domain_that_already_has_i_is_unchanged() -> None:
    """Adjoining ``i`` twice adjoins it once."""
    source = PolynomialMap((x1, x2, x3), (x1 + sp.I * x2**3, x2, x3))

    assert source.ring.domain == sp.ZZ_I
    assert SymmetricLiftStep.build(source).target.ring.domain == sp.ZZ_I


def test_a_source_over_an_algebraic_number_field_lifts() -> None:
    """SYM-5 over a domain that is not ``QQ``, which an audit of ``0.6.0rc1`` found.

    ``QQ<sqrt(2)>`` with ``i`` adjoined is ``QQ<sqrt(2) + I>``, a third field
    whose elements are algebraic numbers over another minimal polynomial.
    Converting a coefficient between the two with ``convert`` tries to unify
    the representations and raises; going through the expression they agree on
    works. Nothing else in the suite has a source over an algebraic field, so
    nothing else would have found it.
    """
    field = sp.QQ.algebraic_field(sp.sqrt(2))
    ring = sp.ring("y1,y2,y3", field)[0]
    first, second, third = ring.gens
    source = PolynomialMap.from_ring(
        ring,
        (first + field.from_sympy(sp.sqrt(2)) * second**3, second, third),
    )

    step = SymmetricLiftStep.build(source)

    assert step.verify() is None
    assert step.target.determinant() == 1

    # Two ``AlgebraicField`` objects for one field need not compare equal, so
    # what is checked is that the field contains what it has to contain.
    domain = step.target.ring.domain

    assert domain.is_Field
    assert domain.from_sympy(sp.I) == domain.from_sympy(sp.I)
    assert sp.simplify(domain.to_sympy(domain.from_sympy(sp.sqrt(2)))) == sp.sqrt(2)


def test_build_records_the_target_as_constructed(lifted: SymmetricLiftStep) -> None:
    assert lifted.provenance is Provenance.CONSTRUCTED


def test_a_supplied_target_is_recorded_as_supplied(
    lifted: SymmetricLiftStep,
) -> None:
    supplied = SymmetricLiftStep(KELLER, lifted.target, lifted.variables)

    assert supplied.provenance is Provenance.SUPPLIED
    assert supplied != lifted


def test_a_factory_may_name_the_generators() -> None:
    built = SymmetricLiftStep.build(KELLER, factory=IndexedVariableFactory("w"))

    assert built.variables == sp.symbols("w1:7")
    assert built.verify() is None


def test_the_step_makes_no_EA_claim(lifted: SymmetricLiftStep) -> None:  # noqa: N802
    """SYM-11."""
    assert lifted.filtration_level == math.inf


def test_the_number_of_generators_is_twice_the_dimension() -> None:
    with pytest.raises(ValueError, match="doubles the dimension"):
        SymmetricLiftStep(KELLER, KELLER, sp.symbols("w1:6"))


def test_the_generators_must_be_distinct() -> None:
    names = sp.symbols("w1:6") + (sp.Symbol("w1"),)

    with pytest.raises(ValueError, match="must be distinct"):
        SymmetricLiftStep(KELLER, KELLER, names)


def test_a_generator_of_the_source_may_not_name_the_target() -> None:
    with pytest.raises(ValueError, match="already in use"):
        SymmetricLiftStep(KELLER, KELLER, (x1,) + sp.symbols("w1:6"))


def test_the_source_must_be_a_polynomial_map() -> None:
    with pytest.raises(TypeError, match="source must be a PolynomialMap"):
        SymmetricLiftStep("F", KELLER, sp.symbols("w1:7"))  # type: ignore[arg-type]


def test_the_target_must_be_a_polynomial_map() -> None:
    with pytest.raises(TypeError, match="target must be a PolynomialMap"):
        SymmetricLiftStep(KELLER, "F'", sp.symbols("w1:7"))  # type: ignore[arg-type]


def test_a_generator_must_be_a_symbol() -> None:
    with pytest.raises(TypeError, match="must be a SymPy symbol"):
        SymmetricLiftStep(KELLER, KELLER, (7,) + sp.symbols("w1:6"))  # type: ignore[arg-type]


# --------------------------------------------------------------------------
# Verification, and what can fail
# --------------------------------------------------------------------------


def test_a_correct_step_verifies(lifted: SymmetricLiftStep) -> None:
    assert lifted.verify() is None


def test_verification_is_idempotent(lifted: SymmetricLiftStep) -> None:
    """STEP-2."""
    lifted.verify()

    assert lifted.verify() is None


def test_the_determinant_of_the_lift_is_one(lifted: SymmetricLiftStep) -> None:
    """SYM-7, as an independent cross-check and not as a check of the step.

    ``verify`` does not compute this. At dimension six it costs nothing, and at
    forty it did not finish in eight hours, which is why the obligation is a
    consequence rather than a check. Computing it here at a size where it is
    free is what the phrase in ``AGENTS.md`` means.
    """
    assert lifted.target.determinant() == 1


def test_an_inhomogeneous_source_is_refused() -> None:
    """SYM-3, the negative control."""
    source = over_field(PolynomialMap((x1, x2), (x1 + x2**2 + x2**3, x2)))

    with pytest.raises(VerificationError, match=r"\[SYM-3\]") as failure:
        SymmetricLiftStep.build(source)

    assert failure.value.obligation == "SYM-3"
    assert "not homogeneous" in failure.value.message


def test_a_linear_source_is_refused() -> None:
    """SYM-3 again, the lower bound."""
    source = over_field(PolynomialMap((x1, x2), (x1 + x2, x2)))

    with pytest.raises(VerificationError, match=r"\[SYM-3\]") as failure:
        SymmetricLiftStep.build(source)

    assert "below two" in failure.value.message


def test_a_source_that_is_not_Keller_is_refused() -> None:  # noqa: N802
    """SYM-4, the negative control, and it fails on a constructed step.

    ``build`` cannot make the source Keller and does not try. The lift of this
    one is built and has a determinant that is not constant.
    """
    step = SymmetricLiftStep.build(FOLD)

    assert step.provenance is Provenance.CONSTRUCTED
    assert step.target.determinant() != 1

    with pytest.raises(VerificationError, match=r"\[SYM-4\]") as failure:
        step.verify()

    assert failure.value.obligation == "SYM-4"


def test_a_target_that_is_not_the_lift_fails_the_identity(
    lifted: SymmetricLiftStep,
) -> None:
    """SYM-1, the negative control."""
    components = list(lifted.target.components)
    components[0] = components[0] + sp.Rational(1, 2) * lifted.variables[1] ** 3
    wrong = PolynomialMap(lifted.variables, tuple(components))

    # Over the same domain, so that SYM-5 does not answer first. A perturbation
    # with an integer coefficient narrows the inferred domain to ZZ_I and the
    # step then reports the domain rather than the identity.
    assert wrong.ring.domain == lifted.target.ring.domain

    with pytest.raises(VerificationError, match=r"\[SYM-1\]") as failure:
        SymmetricLiftStep(KELLER, wrong, lifted.variables).verify()

    assert failure.value.obligation == "SYM-1"


def test_a_target_of_the_wrong_dimension_fails() -> None:
    """SYM-5, the half ``verify`` reaches."""
    names = sp.symbols("w1:7")
    wrong = over_field(PolynomialMap(names[:3], names[:3]))

    with pytest.raises(VerificationError, match=r"\[SYM-5\]") as failure:
        SymmetricLiftStep(KELLER, wrong, names).verify()

    assert failure.value.obligation == "SYM-5"


def test_a_target_carrying_other_generators_fails(
    lifted: SymmetricLiftStep,
) -> None:
    """SYM-5 again."""
    others = sp.symbols("w1:7")
    wrong = PolynomialMap(others, others)

    with pytest.raises(VerificationError, match=r"\[SYM-5\]"):
        SymmetricLiftStep(KELLER, wrong, lifted.variables).verify()


def test_a_target_over_the_wrong_domain_fails(lifted: SymmetricLiftStep) -> None:
    """SYM-5, the domain clause, which no other step on the page has.

    The identity would fail on this target too, and it would fail for a reason
    that reads as arithmetic. The domain is checked first so that the message
    names what is wrong.
    """
    names = lifted.variables
    wrong = over_field(PolynomialMap(names, names))

    assert wrong.ring.domain == sp.QQ

    with pytest.raises(VerificationError, match=r"\[SYM-5\]") as failure:
        SymmetricLiftStep(KELLER, wrong, names).verify()

    assert "i adjoined" in failure.value.message


# --------------------------------------------------------------------------
# Transport
# --------------------------------------------------------------------------


def test_transport_lifts_the_pair_asymmetrically() -> None:
    """SYM-8. One point goes to ``(p, 0)`` and the other to ``(q + rho, i rho)``.

    The step orients the pair itself, so ``q`` here is ``0`` and ``p`` is
    ``-1``: on this source ``h = x1^2``, the matrix at ``q = 0`` is ``1``, and
    ``rho = p - q = -1``. The second point is therefore ``(-1, -i)``.

    The image moves with the orientation, which is not a defect: a different
    pair of preimages of one map has a different image, and both are
    collisions of the target.
    """
    moved = SymmetricLiftStep.build(FOLD).transport(FOLD_COLLISION)

    assert moved.points == ((-1, 0), (-1, -sp.I))
    assert moved.image == (-1, -sp.I)
    assert moved.verify(SymmetricLiftStep.build(FOLD).target) is None


def test_the_orientation_does_not_depend_on_the_order_of_the_points() -> None:
    """SYM-8 against COL-6, which is what an audit of ``0.6.0rc1`` found.

    A ``Collision`` compares its points as a set, and the lift treats them
    differently. Taking the order the tuple happens to carry made two equal
    collisions transport to two unequal ones, and both results verified, which
    is the worst shape such a fault can have.
    """
    step = SymmetricLiftStep.build(FOLD)
    forwards = Collision(((0,), (-1,)), (0,))
    backwards = Collision(((-1,), (0,)), (0,))

    assert forwards == backwards
    assert hash(forwards) == hash(backwards)
    assert step.transport(forwards) == step.transport(backwards)


def test_the_lifted_points_differ_in_the_second_block() -> None:
    """SYM-10, and the argument is on the second block and not the first.

    ``p != q`` gives ``rho != 0``, so the blocks ``0`` and ``i rho`` differ,
    where the first blocks might in principle agree.
    """
    moved = SymmetricLiftStep.build(FOLD).transport(FOLD_COLLISION)
    first, second = moved.points

    assert first[1:] != second[1:]


def test_transport_refuses_more_than_two_points() -> None:
    """SYM-9, the negative control, and it is reached in practice.

    Every collision this milestone produces has three points, so a caller has
    to narrow one before lifting it.
    """
    source = over_field(PolynomialMap((x1, x2), (x1 + x1**2, x2 + x2**2)))
    step = SymmetricLiftStep.build(source)
    three = Collision(((0, 0), (-1, 0), (0, -1)), (0, 0))

    with pytest.raises(VerificationError, match=r"\[SYM-9\]") as failure:
        step.transport(three)

    assert failure.value.obligation == "SYM-9"
    assert "narrow the collision" in failure.value.message


def test_narrowing_the_collision_is_what_a_caller_does() -> None:
    """The other half of the previous test: two of the three lift."""
    source = over_field(PolynomialMap((x1, x2), (x1 + x1**2, x2 + x2**2)))
    step = SymmetricLiftStep.build(source)
    pair = Collision(((0, 0), (-1, 0)), (0, 0))

    assert len(step.transport(pair).points) == 2


def test_a_singular_matrix_is_reported_and_not_raised_through() -> None:
    """SYM-8. ``I + J h(q)^T`` can only be singular for a source that is not Keller.

    ``transport`` does not require SYM-4, so it has to say what happened rather
    than let a solver fail. Here ``h = (x1 x2, 0)`` and the matrix at
    ``(1, -1)`` has a zero row.
    """
    source = over_field(PolynomialMap((x1, x2), (x1 + x1 * x2, x2)))
    step = SymmetricLiftStep.build(source)

    with pytest.raises(VerificationError, match=r"\[SYM-8\]") as failure:
        step.transport(Collision(((0, -1), (1, -1)), (0, -1)))

    assert "singular" in failure.value.message


def test_transport_verifies_the_incoming_collision() -> None:
    """STEP-3."""
    step = SymmetricLiftStep.build(FOLD)

    with pytest.raises(VerificationError, match=r"\[COL-3\]"):
        step.transport(Collision(((0,), (1,)), (0,)))


# --------------------------------------------------------------------------
# Value semantics
# --------------------------------------------------------------------------


def test_two_equal_steps_compare_equal_and_hash_alike() -> None:
    """STEP-5."""
    one = SymmetricLiftStep.build(KELLER)
    other = SymmetricLiftStep.build(KELLER)

    assert one == other
    assert hash(one) == hash(other)


def test_a_step_does_not_compare_to_another_type(lifted: SymmetricLiftStep) -> None:
    assert lifted != KELLER


def test_the_representation_names_the_dimensions(lifted: SymmetricLiftStep) -> None:
    text = repr(lifted)

    assert "3->6" in text
    assert "constructed" in text


# --------------------------------------------------------------------------
# The control
# --------------------------------------------------------------------------


def test_the_lift_of_thompsons_twenty_has_the_published_form() -> None:
    """350 monomials, which is Theorem 3's figure and not this project's.

    The compression reaches the published twenty-dimensional map, and the lift
    of it has to reach the published quartic. The count is what the ancillary
    file reports and what ``scripts/reconstruct_prellberg40.py`` recomputes.
    """
    compressed = CompressionStep.build(
        over_field(examples.thompson24_homogeneous()),
        examples.thompson24_homogeneous_collision(),
    )
    step = SymmetricLiftStep.build(compressed.target)

    assert step.verify() is None
    assert step.target.dimension == 40
    assert len(sp.Poly(step.form, *step.variables).terms()) == 350


# --------------------------------------------------------------------------
# The chain the milestone is about
# --------------------------------------------------------------------------


@pytest.mark.slow
def test_spacerat11_reaches_a_quartic_form_in_thirty_eight_variables() -> None:
    """11 to 22 to 23 to 19 to 38, every step verified.

    The end of the pipeline milestone 0.6 was cut for. Two of the three points
    are carried the whole way; the third is dropped at the lift, where SYM-9
    requires a pair.
    """
    from kellermap import LinearStep

    normalization = LinearStep.normalize(over_field(examples.spacerat11()))
    unipotent = UnipotentStep.build(normalization.target)
    homogenized = HomogenizationStep.build(unipotent.target)
    carried = homogenized.transport(
        unipotent.transport(normalization.transport(examples.spacerat11_collision()))
    )
    compression = CompressionStep.build(homogenized.target, carried)
    compressed = compression.transport(carried)
    lift = SymmetricLiftStep.build(compression.target)

    chain = Reduction((normalization, unipotent, homogenized, compression))

    assert chain.verify() is None
    assert chain.target.dimension == 19
    assert lift.verify() is None
    assert lift.target.dimension == 38

    pair = Collision(compressed.points[:2], compressed.image)
    moved = lift.transport(pair)

    assert len(moved.points) == 2
    assert sp.Poly(lift.form, *lift.variables).total_degree() == 4
