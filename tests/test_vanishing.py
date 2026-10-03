"""The witness to Zhao's Vanishing Conjecture, VAN-1 to VAN-5.

The forty-variable lift of Thompson's map is the witness throughout. It is the
form of Section 4 of arXiv:2608.12543v3, and its figures can be compared with
the paper's.

VAN-3 and VAN-4 cannot fail on a lift that verifies: both follow from Theorem 3
and a verified source. Their negative controls therefore call the two check
functions on forms that are not lifts, as ``docs/contracts.md`` says they must.
The forms are in two or three variables, so the controls cost nothing.
"""

from __future__ import annotations

import pytest
import sympy as sp

from kellermap import (
    Collision,
    CompressionStep,
    PolynomialMap,
    SymmetricLiftStep,
    VanishingWitness,
    VerificationError,
    examples,
    over_field,
)
from kellermap.vanishing import check_conclusion_at_one, check_hypothesis, laplacian

x1, x2, x3 = sp.symbols("x1 x2 x3")

RING, X, Y, Z = sp.ring("X Y Z", sp.QQ_I)


@pytest.fixture(scope="module")
def compressed() -> CompressionStep:
    """Return Thompson's map compressed along its collision, 20 variables."""
    return CompressionStep.build(
        over_field(examples.thompson24_homogeneous()),
        examples.thompson24_homogeneous_collision(),
    )


@pytest.fixture(scope="module")
def pair(compressed: CompressionStep) -> Collision:
    """Return the collision in the twenty variables of the compression."""
    return compressed.transport(examples.thompson24_homogeneous_collision())


@pytest.fixture(scope="module")
def lift(compressed: CompressionStep) -> SymmetricLiftStep:
    """Return the lift of the compression, 40 variables."""
    return SymmetricLiftStep.build(compressed.target)


@pytest.fixture(scope="module")
def collision(lift: SymmetricLiftStep, pair: Collision) -> Collision:
    """Return the collision of ``id - grad(P)`` the lift transports."""
    return lift.transport(pair)


@pytest.fixture(scope="module")
def witness(lift: SymmetricLiftStep, collision: Collision) -> VanishingWitness:
    witness = VanishingWitness(lift, collision)
    witness.verify()

    return witness


# --------------------------------------------------------------------------
# The witness that verifies
# --------------------------------------------------------------------------


def test_the_forty_variable_lift_is_a_witness(witness: VanishingWitness) -> None:
    assert witness.depth == 2
    assert witness.lift.target.dimension == 40
    assert witness.verify() is None


def test_the_form_is_the_lift_form_and_not_a_copy(witness: VanishingWitness) -> None:
    """Derived, not stored: there is no second form that could disagree."""
    assert witness.form == witness.lift.form
    assert "form" not in {f.name for f in witness.__dataclass_fields__.values()}


def test_delta_of_the_square_has_the_published_count(lift: SymmetricLiftStep) -> None:
    """The library's Laplacian against the figure of Section 4 of the paper.

    Not an obligation, since a count of monomials depends on the coordinates.
    It is the cross-check of ``laplacian`` against somebody else's
    computation; ``scripts/reconstruct_prellberg40.py`` reaches the same 8,630
    by derivatives and without this library.
    """
    form = lift._form()

    assert len(laplacian(form**2)) == 8630


def test_verify_runs_once(
    witness: VanishingWitness, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A second ``verify`` does not compute the powers again."""

    def refuse(*arguments: object) -> None:
        raise AssertionError("verify ran a second time")

    monkeypatch.setattr("kellermap.vanishing.check_hypothesis", refuse)

    assert witness.verify() is None


# --------------------------------------------------------------------------
# The constructor
# --------------------------------------------------------------------------


@pytest.mark.parametrize("depth", [0, -1, 41])
def test_a_depth_outside_one_to_n_is_refused(
    lift: SymmetricLiftStep, collision: Collision, depth: int
) -> None:
    with pytest.raises(ValueError, match="VAN-3 checks"):
        VanishingWitness(lift, collision, depth)


def test_depth_n_is_accepted_and_not_computed(
    lift: SymmetricLiftStep, collision: Collision
) -> None:
    """The bound is the number of variables. Constructing computes nothing."""
    assert VanishingWitness(lift, collision, 40).depth == 40


@pytest.mark.parametrize("depth", [True, 2.0, "2"])
def test_a_depth_that_is_not_an_integer_is_refused(
    lift: SymmetricLiftStep, collision: Collision, depth: object
) -> None:
    with pytest.raises(TypeError, match="integer"):
        VanishingWitness(lift, collision, depth)  # type: ignore[arg-type]


def test_the_lift_and_the_collision_have_their_types(
    lift: SymmetricLiftStep, collision: Collision
) -> None:
    with pytest.raises(TypeError, match="SymmetricLiftStep"):
        VanishingWitness(lift.target, collision)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="Collision"):
        VanishingWitness(lift, collision.points)  # type: ignore[arg-type]


# --------------------------------------------------------------------------
# VAN-1 and VAN-2, which can fail on supplied data
# --------------------------------------------------------------------------


def test_van1_a_lift_that_does_not_verify() -> None:
    """A supplied target that is not the lift. SYM-1 fails, VAN-1 reports it."""
    cubic = over_field(PolynomialMap((x1, x2, x3), (x1 + x2**3, x2, x3)))
    honest = SymmetricLiftStep.build(cubic)
    components = list(honest.target.components)
    components[0] = components[0] + honest.variables[1] ** 3
    wrong = PolynomialMap(honest.variables, tuple(components))
    supplied = SymmetricLiftStep(cubic, over_field(wrong), honest.variables)
    points = Collision(((0,) * 6, (1,) + (0,) * 5), (0,) * 6)

    with pytest.raises(VerificationError) as failure:
        VanishingWitness(supplied, points).verify()

    assert failure.value.obligation == "VAN-1"
    assert "SYM-" in failure.value.message
    assert isinstance(failure.value.__cause__, VerificationError)


def test_van1_a_lift_of_a_quadratic_source() -> None:
    """A Keller map with a quadratic displacement: the lift verifies.

    Its form is a cubic, which Zhao's conjecture is not about. VAN-1 runs
    before VAN-2, so the points need not be a collision; this map has none.
    """
    square = over_field(PolynomialMap((x1, x2), (x1 + x2**2, x2)))
    step = SymmetricLiftStep.build(square)
    step.verify()
    points = Collision(((0,) * 4, (1,) + (0,) * 3), (0,) * 4)

    with pytest.raises(VerificationError, match="degree 2") as failure:
        VanishingWitness(step, points).verify()

    assert failure.value.obligation == "VAN-1"


def test_van2_a_collision_with_the_wrong_image(
    lift: SymmetricLiftStep, collision: Collision
) -> None:
    moved = Collision(collision.points, (sp.Integer(1),) * 40)

    with pytest.raises(VerificationError) as failure:
        VanishingWitness(lift, moved).verify()

    assert failure.value.obligation == "VAN-2"
    assert "COL-3" in failure.value.message


def test_van2_a_collision_of_the_source_and_not_of_the_target(
    lift: SymmetricLiftStep, pair: Collision
) -> None:
    """The pair before the lift is in twenty variables, not forty."""
    with pytest.raises(VerificationError) as failure:
        VanishingWitness(lift, pair).verify()

    assert failure.value.obligation == "VAN-2"
    assert "COL-1" in failure.value.message


# --------------------------------------------------------------------------
# VAN-3 and VAN-4, through the check functions
# --------------------------------------------------------------------------


def test_the_laplacian_of_a_small_polynomial() -> None:
    """Against SymPy's own derivatives, term by term."""
    imaginary = RING.domain.from_sympy(sp.I)
    polynomial = (X + 2 * Y) ** 3 * Z**2 + imaginary * X**2 * Y**4 - 7
    expected = sum(
        sp.diff(polynomial.as_expr(), symbol, 2) for symbol in sp.symbols("X Y Z")
    )

    assert laplacian(polynomial) == RING(sp.expand(expected))
    assert laplacian(RING(5)) == 0


def test_van3_a_form_that_is_not_harmonic() -> None:
    """``X^4`` fails at the first depth: ``Delta(X^4) = 12 X^2``."""
    with pytest.raises(VerificationError, match=r"Delta\^1\(P\^1\)") as failure:
        check_hypothesis(X**4, 1)

    assert failure.value.obligation == "VAN-3"


def test_van3_a_harmonic_form_whose_hessian_is_not_nilpotent() -> None:
    """``Re (X + i Y)^4`` passes depth one and fails depth two.

    So depth two checks something depth one does not. The Hessian has trace
    zero and a non-zero square trace, which is what Zhao's proof of
    Theorem 4.3 says the second Laplacian detects.
    """
    form = X**4 - 6 * X**2 * Y**2 + Y**4

    assert check_hypothesis(form, 1) is None
    with pytest.raises(VerificationError, match=r"Delta\^2\(P\^2\)"):
        check_hypothesis(form, 2)


def test_van3_passes_at_depth_three_on_a_nilpotent_hessian() -> None:
    """``(X + i Y)^4`` has a nilpotent Hessian, so every depth passes."""
    form = (X + RING.domain.from_sympy(sp.I) * Y) ** 4

    assert check_hypothesis(form, 3) == form**2


def test_van4_a_hessian_nilpotent_form_with_a_harmonic_square() -> None:
    """The negative control of VAN-4.

    ``(X + i Y)^4`` passes VAN-3 at every depth, and its square is harmonic.
    Its gradient map is invertible, with inverse ``z + grad(P)``, which is
    what Zhao's Corollary 3.9 says and why a collision rules this out.
    """
    form = (X + RING.domain.from_sympy(sp.I) * Y) ** 4
    square = check_hypothesis(form, 2)

    with pytest.raises(VerificationError) as failure:
        check_conclusion_at_one(form, square)

    assert failure.value.obligation == "VAN-4"
    with pytest.raises(VerificationError, match="Corollary 3.9"):
        check_conclusion_at_one(form)


def test_van4_passes_on_a_form_with_a_non_harmonic_square() -> None:
    assert check_conclusion_at_one(X**4) is None


# --------------------------------------------------------------------------
# The thirty-eight-variable witness, this project's own
# --------------------------------------------------------------------------


@pytest.mark.slow
def test_the_lift_at_the_end_of_the_spacerat11_chain_is_a_witness() -> None:
    """From the eleven-variable map through all four stages, 38 variables."""
    from kellermap import LinearStep
    from kellermap.bcw import HomogenizationStep, UnipotentStep

    source = over_field(examples.spacerat11())
    pair = examples.spacerat11_collision()
    normalized = LinearStep.normalize(source)
    pair = normalized.transport(pair)
    unipotent = UnipotentStep.build(normalized.target)
    pair = unipotent.transport(pair)
    homogenized = HomogenizationStep.build(unipotent.target)
    pair = homogenized.transport(pair)
    compressed = CompressionStep.build(homogenized.target, pair)
    pair = compressed.transport(pair)
    step = SymmetricLiftStep.build(compressed.target)
    lifted = step.transport(Collision(pair.points[:2], pair.image))

    witness = VanishingWitness(step, lifted)
    witness.verify()

    assert step.target.dimension == 38
    assert len(laplacian(step._form() ** 2)) == 8999
