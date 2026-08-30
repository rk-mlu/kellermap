"""Collision-hull compression as a certificate.

The control is the whole point of this file, and it is not a control this
project set itself: applied to ``examples.thompson24_homogeneous`` the hull has to run
``2, 4, 11, 20, 20``, and the restriction has to be the map
``scripts/reconstruct_prellberg40.py`` transcribes from the published ancillary
file. Both are checked, the second component by component.

Everything small here uses sources that are not Keller maps, and says so where
it does. ``collision_hull`` and ``transport`` do not need CHC-4, and there is
no small Keller map with a collision to use instead.
"""

import importlib.util
import math
import sys
from pathlib import Path

import pytest
import sympy as sp

from kellermap import (
    Collision,
    CompressionStep,
    PolynomialMap,
    Provenance,
    Reduction,
    Step,
    VerificationError,
    collision_hull,
    examples,
    over_field,
)
from kellermap.bcw import HomogenizationStep, UnipotentStep
from kellermap.variables import IndexedVariableFactory

x1, x2, x3, w1 = sp.symbols("x1 x2 x3 w1")

# (x1 + x1^2, x2, x3). The displacement is homogeneous of degree two, and
# ``t + t^2`` folds ``a`` onto ``-1 - a``, so there is a collision to compress.
# It is not a Keller map: the determinant is ``1 + 2 x1``. That is what makes
# it the control for CHC-4 below, and it is why nothing here calls ``verify``
# on it.
FOLD = over_field(PolynomialMap((x1, x2, x3), (x1 + x1**2, x2, x3)))
FOLD_COLLISION = Collision(((0, 0, 0), (-1, 0, 0)), (0, 0, 0))

# (x1 + x2^3, x2, x3), homogeneous of degree three and a Keller map, with no
# collision. Where a check has to be reached that CHC-3 and CHC-4 would
# otherwise shadow, the source has to pass them, and this is the smallest map
# that does.
KELLER = over_field(PolynomialMap((x1, x2, x3), (x1 + x2**3, x2, x3)))


@pytest.fixture(scope="module")
def published() -> object:
    """Return ``scripts/reconstruct_prellberg40.py`` as a module.

    The transcription of the published data, which does not import this
    library. What the control is measured against therefore sits outside it.
    """
    root = Path(__file__).resolve().parent.parent
    path = root / "scripts" / "reconstruct_prellberg40.py"
    spec = importlib.util.spec_from_file_location("reconstruct_prellberg40", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    return module


@pytest.fixture(scope="module")
def compressed() -> CompressionStep:
    """Return Thompson's map compressed along its collision."""
    return CompressionStep.build(
        over_field(examples.thompson24_homogeneous()),
        examples.thompson24_homogeneous_collision(),
    )


# --------------------------------------------------------------------------
# The hull
# --------------------------------------------------------------------------


def test_the_hull_of_a_small_map() -> None:
    """The two points span one line, and it is already invariant.

    Both points lie on the first axis, one of them at the origin, so ``W_0``
    has dimension one rather than two. The polarization of ``x1^2`` sends that
    line to itself, so the iteration stops at once.
    """
    basis, dimensions = collision_hull(FOLD, FOLD_COLLISION)

    assert dimensions == (1, 1)
    assert basis == ((1, 0, 0),)


def test_the_hull_is_returned_in_reduced_form() -> None:
    """Each row has a leading one and the pivot appears in no other row.

    Not a formality. An unreduced basis spans the same subspace and gives a
    far denser restriction, which is what the module docstring measures.
    """
    basis, _ = collision_hull(FOLD, FOLD_COLLISION)

    assert basis == ((1, 0, 0),)


def test_the_hull_refuses_a_collision_that_is_not_one() -> None:
    """COL-3, before anything is polarized."""
    with pytest.raises(VerificationError):
        collision_hull(FOLD, Collision(((0, 0, 0), (1, 0, 0)), (0, 0, 0)))


def test_the_hull_refuses_an_inhomogeneous_displacement() -> None:
    """CHC-3, the negative control.

    A sum of forms of several degrees has no symmetric polarization, so the
    iteration has nothing to iterate.
    """
    source = over_field(PolynomialMap((x1, x2, x3), (x1 + x1**2 + x2**3, x2, x3)))
    collision = Collision(((0, 0, 0), (-1, 0, 0)), (0, 0, 0))

    with pytest.raises(VerificationError, match=r"\[CHC-3\]") as failure:
        collision_hull(source, collision)

    assert failure.value.obligation == "CHC-3"
    assert "not homogeneous" in failure.value.message


def test_the_hull_refuses_a_linear_displacement() -> None:
    """CHC-3 again, the lower bound.

    A Keller map with a linear displacement is injective, so the case cannot
    arise from a real collision; the check is what says so rather than
    dividing by ``1!`` and returning something.
    """
    source = over_field(PolynomialMap((x1, x2), (x1 + x2, x2 - x2)))
    collision = Collision(((0, 1), (1, 0)), (1, 0))

    with pytest.raises(VerificationError, match=r"\[CHC-3\]") as failure:
        collision_hull(source, collision)

    assert "below two" in failure.value.message


# --------------------------------------------------------------------------
# The control
# --------------------------------------------------------------------------


def test_the_hull_of_thompsons_map_runs_two_four_eleven_twenty(
    compressed: CompressionStep,
) -> None:
    """The sequence the paper states, and a number this project did not set."""
    _, dimensions = collision_hull(
        over_field(examples.thompson24_homogeneous()),
        examples.thompson24_homogeneous_collision(),
    )

    assert dimensions == (2, 4, 11, 20, 20)
    assert compressed.target.dimension == 20


def test_the_compression_reaches_the_published_map(
    compressed: CompressionStep, published: object
) -> None:
    """Component for component, and not only in dimension.

    The subspace is what the two constructions share; the basis agrees because
    a reduced row echelon form is unique and the published embedding is in one.
    So this checks the mathematics and not a convention: had the hull been a
    different subspace, no choice of basis would have made the maps agree.
    """
    variables = compressed.target.variables
    theirs = tuple(
        sp.expand(
            sp.sympify(component).xreplace(
                dict(zip(published.z, variables, strict=True))
            )
        )
        for component in published.h
    )
    ours = tuple(
        sp.expand(component.as_expr())
        for component in compressed.target.displacement().to_polynomials()
    )

    assert ours == theirs


def test_the_basis_is_the_published_embedding(
    compressed: CompressionStep, published: object
) -> None:
    """The rows of ``B`` against the embedding the ancillary file prints."""
    embedding = tuple(
        tuple(published.embed(tuple(int(i == j) for i in range(20)))) for j in range(20)
    )

    assert compressed.basis == embedding


def test_the_compressed_map_is_cubic_homogeneous_and_Keller(  # noqa: N802
    compressed: CompressionStep,
) -> None:
    """CHC-6, read off the target."""
    degrees = {
        sum(monomial)
        for component in compressed.target.displacement().to_polynomials()
        if component
        for monomial in component.itermonoms()
    }

    assert degrees == {3}
    assert compressed.target.determinant() == 1


def test_the_compression_verifies(compressed: CompressionStep) -> None:
    assert compressed.verify() is None


def test_verification_is_idempotent(compressed: CompressionStep) -> None:
    """STEP-2."""
    compressed.verify()

    assert compressed.verify() is None


def test_the_collision_survives_the_compression(compressed: CompressionStep) -> None:
    """CHC-9 on the collision the step was built from."""
    moved = compressed.transport(examples.thompson24_homogeneous_collision())

    assert len(moved.points) == 2
    assert moved.dimension == 20
    assert moved.verify(compressed.target) is None


# --------------------------------------------------------------------------
# What can fail
# --------------------------------------------------------------------------


def test_a_source_that_is_not_Keller_is_refused() -> None:  # noqa: N802
    """CHC-4, the negative control.

    Homogeneous and not Keller: ``x1 + x1^2`` has determinant ``1 + 2 x1``.
    Nilpotence needs no obligation here, because homogeneity and a constant
    determinant give it; this is the map that fails the constant.
    """
    step = CompressionStep.build(FOLD, FOLD_COLLISION)

    assert step.provenance is Provenance.CONSTRUCTED
    with pytest.raises(VerificationError, match=r"\[CHC-4\]") as failure:
        step.verify()

    assert failure.value.obligation == "CHC-4"


def test_a_basis_whose_span_is_not_invariant_fails_the_identity(
    compressed: CompressionStep,
) -> None:
    """CHC-1, the negative control, and the fault is in the basis.

    The first twenty coordinate axes of Thompson's space are a basis of a
    subspace that the displacement does not preserve. No target satisfies the
    identity then, and the message says so.
    """
    axes = tuple(tuple(int(i == j) for i in range(24)) for j in range(20))

    with pytest.raises(VerificationError, match=r"\[CHC-1\]") as failure:
        CompressionStep(
            over_field(examples.thompson24_homogeneous()),
            compressed.target,
            axes,
            compressed.target.variables,
        ).verify()

    assert failure.value.obligation == "CHC-1"
    assert "not invariant" in failure.value.message


def test_a_target_that_is_not_the_restriction_fails_the_identity(
    compressed: CompressionStep,
) -> None:
    """CHC-1 again, with the correct basis and one coefficient moved."""
    components = list(compressed.target.components)
    components[0] = components[0] + compressed.target.variables[0] ** 3
    wrong = PolynomialMap(compressed.target.variables, tuple(components))

    with pytest.raises(VerificationError, match=r"\[CHC-1\]"):
        CompressionStep(
            over_field(examples.thompson24_homogeneous()),
            wrong,
            compressed.basis,
            compressed.target.variables,
        ).verify()


def test_a_target_of_the_wrong_dimension_fails() -> None:
    """CHC-5, the half ``verify`` reaches."""
    wrong = over_field(PolynomialMap((w1,), (w1,)))
    other = sp.Symbol("w2")

    with pytest.raises(VerificationError, match=r"\[CHC-5\]") as failure:
        CompressionStep(KELLER, wrong, ((1, 0, 0), (0, 1, 0)), (w1, other)).verify()

    assert failure.value.obligation == "CHC-5"


def test_a_target_carrying_other_generators_fails() -> None:
    """CHC-5 again."""
    other = sp.Symbol("w2")
    wrong = over_field(PolynomialMap((other,), (other,)))

    with pytest.raises(VerificationError, match=r"\[CHC-5\]"):
        CompressionStep(KELLER, wrong, ((1, 0, 0),), (w1,)).verify()


def test_a_dependent_basis_is_refused() -> None:
    """CHC-2, at construction. A dependent list spans less than it claims."""
    with pytest.raises(ValueError, match="linearly dependent"):
        CompressionStep(FOLD, FOLD, ((1, 0, 0), (2, 0, 0)), sp.symbols("w1 w2"))


def test_a_basis_vector_of_the_wrong_length_is_refused() -> None:
    with pytest.raises(ValueError, match="one per variable of the source"):
        CompressionStep(FOLD, FOLD, ((1, 0),), (w1,))


def test_more_basis_vectors_than_dimensions_is_refused() -> None:
    with pytest.raises(ValueError, match="in a space of dimension"):
        CompressionStep(
            FOLD,
            FOLD,
            ((1, 0, 0), (0, 1, 0), (0, 0, 1), (1, 1, 1)),
            sp.symbols("w1:5"),
        )


def test_an_empty_basis_is_refused() -> None:
    with pytest.raises(ValueError, match="spans no subspace"):
        CompressionStep(FOLD, FOLD, (), ())


def test_a_generator_count_that_does_not_match_the_basis_is_refused() -> None:
    with pytest.raises(ValueError, match="one generator per vector"):
        CompressionStep(FOLD, FOLD, ((1, 0, 0),), (w1, sp.Symbol("w2")))


def test_a_generator_of_the_source_may_not_name_the_target() -> None:
    """RC-4, covering every generator of the target and not an added half."""
    with pytest.raises(ValueError, match="already in use"):
        CompressionStep(FOLD, FOLD, ((1, 0, 0),), (x1,))


def test_the_generators_of_the_target_must_be_distinct() -> None:
    with pytest.raises(ValueError, match="must be distinct"):
        CompressionStep(FOLD, FOLD, ((1, 0, 0), (0, 1, 0)), (w1, sp.Symbol("w1")))


def test_the_source_must_be_a_polynomial_map() -> None:
    with pytest.raises(TypeError, match="source must be a PolynomialMap"):
        CompressionStep("F", FOLD, ((1, 0, 0),), (w1,))  # type: ignore[arg-type]


def test_the_target_must_be_a_polynomial_map() -> None:
    with pytest.raises(TypeError, match="target must be a PolynomialMap"):
        CompressionStep(FOLD, "F'", ((1, 0, 0),), (w1,))  # type: ignore[arg-type]


def test_a_generator_of_the_target_must_be_a_symbol() -> None:
    with pytest.raises(TypeError, match="must be a SymPy symbol"):
        CompressionStep(FOLD, FOLD, ((1, 0, 0),), (7,))  # type: ignore[arg-type]


# --------------------------------------------------------------------------
# Transport
# --------------------------------------------------------------------------


def test_transport_expresses_the_points_in_the_basis() -> None:
    """CHC-9. Three coordinates become one."""
    step = CompressionStep.build(FOLD, FOLD_COLLISION)
    moved = step.transport(FOLD_COLLISION)

    assert moved.points == ((0,), (-1,))
    assert moved.image == (0,)


def test_transport_refuses_a_collision_that_leaves_the_subspace() -> None:
    """CHC-9, the negative control, and the only refusal of its kind here.

    The collision below holds for the source. Its points lie off the line the
    step compressed to, so they have no coordinates in the target and the step
    says that rather than producing something.
    """
    step = CompressionStep.build(FOLD, FOLD_COLLISION)
    elsewhere = Collision(((0, 1, 0), (-1, 1, 0)), (0, 1, 0))

    assert elsewhere.verify(FOLD) is None

    with pytest.raises(VerificationError, match=r"\[CHC-9\]") as failure:
        step.transport(elsewhere)

    assert failure.value.obligation == "CHC-9"


def test_transport_verifies_the_incoming_collision() -> None:
    """STEP-3."""
    step = CompressionStep.build(FOLD, FOLD_COLLISION)

    with pytest.raises(VerificationError, match=r"\[COL-3\]"):
        step.transport(Collision(((0, 0, 0), (1, 0, 0)), (0, 0, 0)))


def test_transport_preserves_the_number_of_points(
    compressed: CompressionStep,
) -> None:
    """STEP-4. Distinct points of the subspace have distinct coordinates."""
    moved = compressed.transport(examples.thompson24_homogeneous_collision())

    assert len(set(moved.points)) == 2


# --------------------------------------------------------------------------
# What the step reports
# --------------------------------------------------------------------------


def test_the_step_is_a_step() -> None:
    assert isinstance(CompressionStep.build(FOLD, FOLD_COLLISION), Step)


def test_the_step_makes_no_EA_claim() -> None:  # noqa: N802
    """CHC-7, as for the homogenization and for the same reason."""
    assert CompressionStep.build(FOLD, FOLD_COLLISION).filtration_level == math.inf


def test_a_factory_may_name_the_generators() -> None:
    built = CompressionStep.build(
        FOLD, FOLD_COLLISION, factory=IndexedVariableFactory("c")
    )

    assert built.variables == (sp.Symbol("c1"),)


def test_a_supplied_basis_is_recorded_as_supplied() -> None:
    step = CompressionStep.build(FOLD, FOLD_COLLISION)
    supplied = CompressionStep(FOLD, step.target, step.basis, step.variables)

    assert supplied.provenance is Provenance.SUPPLIED
    assert step.provenance is Provenance.CONSTRUCTED
    assert supplied != step


def test_two_equal_steps_compare_equal_and_hash_alike() -> None:
    """STEP-5."""
    one = CompressionStep.build(FOLD, FOLD_COLLISION)
    other = CompressionStep.build(FOLD, FOLD_COLLISION)

    assert one == other
    assert hash(one) == hash(other)


def test_a_step_does_not_compare_to_another_type() -> None:
    assert CompressionStep.build(FOLD, FOLD_COLLISION) != FOLD


def test_the_representation_names_the_dimensions(
    compressed: CompressionStep,
) -> None:
    text = repr(compressed)

    assert "24->20" in text
    assert "constructed" in text


def test_a_hull_that_is_the_whole_space_compresses_to_itself() -> None:
    """Nothing requires the dimension to fall.

    A correct step and a useless one, in the shape BCW-1 already has for the
    degree. Whether a step is a good step is a question for the search.
    """
    source = over_field(PolynomialMap((x1, x2), (x1 + x1**2, x2 + x2**2)))
    collision = Collision(((0, -1), (-1, 0)), (0, 0))
    step = CompressionStep.build(source, collision)

    assert step.target.dimension == 2


# --------------------------------------------------------------------------
# The chain the milestone is about
# --------------------------------------------------------------------------


@pytest.mark.slow
def test_alpoege12_compresses_to_twenty_variables() -> None:
    """12 to 24 to 25 to 20, every step verified, with the three points.

    The figure milestone 0.6 was cut for. It is Macfarlane's twenty and not
    below it, and no claim of minimality follows from either.
    """
    lift = UnipotentStep.build(over_field(examples.alpoege12()))
    homogenized = HomogenizationStep.build(lift.target)
    carried = homogenized.transport(lift.transport(examples.alpoege12_collision()))
    compression = CompressionStep.build(homogenized.target, carried)

    chain = Reduction((lift, homogenized, compression))

    assert chain.verify() is None
    assert chain.source.dimension == 12
    assert chain.target.dimension == 20
    assert chain.target.degree() == 3
    assert chain.target.determinant() == 1

    moved = chain.transport(examples.alpoege12_collision())

    assert len(moved.points) == 3
    assert moved.verify(compression.target) is None
