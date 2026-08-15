"""Collisions: the evidence that a map is not injective.

Two things are checked. The constructor invariants, so that a ``Collision``
object with coinciding points does not come into existence at all. And the
three obligations COL-1 to COL-3 of ``docs/contracts.md`` that ``verify``
checks against a map.

The regression part at the end works with Alpoege's counterexample, so that the
type is exercised once on the object it exists for.
"""

import pytest
import sympy as sp

from kellermap import Collision, PolynomialMap, VerificationError

x, y = sp.symbols("x y")

# F(x, y) = (x^2, y) identifies (1, 0) and (-1, 0).
SQUARE = PolynomialMap((x, y), (x**2, y))

POINTS = ((1, 0), (-1, 0))
IMAGE = (1, 0)


@pytest.fixture
def collision() -> Collision:
    return Collision(POINTS, IMAGE)


# --------------------------------------------------------------------------
# Construction
# --------------------------------------------------------------------------


def test_coordinates_are_sympified(collision: Collision) -> None:
    """Python numbers come back out as SymPy expressions."""
    assert collision.points == (
        (sp.Integer(1), sp.Integer(0)),
        (-sp.Integer(1), sp.Integer(0)),
    )
    assert all(isinstance(c, sp.Expr) for point in collision.points for c in point)


def test_dimension_and_length(collision: Collision) -> None:
    assert collision.dimension == 2
    assert len(collision) == 2


def test_rationals_survive_construction() -> None:
    """Exact arithmetic, with no floating point on the way."""
    points = ((sp.Rational(-1, 4), 0), (sp.Rational(1, 4), 0))
    assert Collision(points, (0, 0)).points[0][0] == sp.Rational(-1, 4)


def test_one_point_is_not_a_collision() -> None:
    with pytest.raises(ValueError, match="at least two points"):
        Collision((POINTS[0],), IMAGE)


def test_points_must_be_distinct() -> None:
    with pytest.raises(ValueError, match="distinct points"):
        Collision((POINTS[0], POINTS[0]), IMAGE)


def test_distinctness_compares_values_not_syntax() -> None:
    """(1/2, 0) and (2/4, 0) are one point, written differently."""
    with pytest.raises(ValueError, match="distinct points"):
        Collision(
            ((sp.Rational(1, 2), 0), (sp.Rational(2, 4), sp.Integer(0))),
            (0, 0),
        )


def test_points_must_have_equal_length() -> None:
    with pytest.raises(ValueError, match="same number of coordinates"):
        Collision(((1, 0), (-1, 0, 0)), IMAGE)


def test_image_must_have_the_same_length() -> None:
    with pytest.raises(ValueError, match="same number of coordinates"):
        Collision(POINTS, (1, 0, 0))


def test_a_point_must_be_iterable() -> None:
    """A single expression is not a point, even if it were iterable."""
    with pytest.raises(TypeError, match="iterable of coordinates"):
        Collision((sp.Integer(1), sp.Integer(-1)), IMAGE)


def test_a_point_needs_a_coordinate() -> None:
    with pytest.raises(ValueError, match="at least one coordinate"):
        Collision(((), ()), ())


def test_at_needs_points() -> None:
    with pytest.raises(ValueError, match="got none"):
        Collision.at(SQUARE, ())


def test_repr_names_the_points(collision: Collision) -> None:
    assert "Collision(points=" in repr(collision)
    assert "image=" in repr(collision)


def test_a_coordinate_that_cannot_be_sympified() -> None:
    with pytest.raises(TypeError, match="not a SymPy expression"):
        Collision(((1, 0), (-1, object())), IMAGE)


def test_coordinates_must_be_expressions() -> None:
    with pytest.raises(TypeError, match="not a SymPy expression"):
        Collision(((1, 0), (-1, [])), IMAGE)


# --------------------------------------------------------------------------
# COL-1 to COL-3
# --------------------------------------------------------------------------


def test_verify_accepts_a_genuine_collision(collision: Collision) -> None:
    assert collision.verify(SQUARE) is None


def test_COL1_dimension_mismatch(collision: Collision) -> None:  # noqa: N802
    z = sp.Symbol("z")
    three_dimensional = PolynomialMap((x, y, z), (x**2, y, z))

    with pytest.raises(VerificationError) as failure:
        collision.verify(three_dimensional)

    assert failure.value.obligation == "COL-1"
    assert failure.value.step is None


def test_COL2_a_coordinate_carrying_a_variable_of_the_map() -> None:  # noqa: N802
    """Otherwise evaluation would substitute the point into itself."""
    suspect = Collision(((x, 0), (-x, 0)), (x**2, 0))

    with pytest.raises(VerificationError) as failure:
        suspect.verify(SQUARE)

    assert failure.value.obligation == "COL-2"


def test_COL2_allows_a_coefficient_parameter() -> None:  # noqa: N802
    """A parameter of the coefficient domain is not a variable."""
    T = sp.Symbol("T")
    scaled = PolynomialMap((x, y), (x**2, T * y))
    parametric = Collision(((T, 0), (-T, 0)), (T**2, 0))

    assert parametric.verify(scaled) is None


def test_COL3_wrong_image(collision: Collision) -> None:  # noqa: N802
    wrong = Collision(POINTS, (0, 0))

    with pytest.raises(VerificationError) as failure:
        wrong.verify(SQUARE)

    assert failure.value.obligation == "COL-3"
    assert "coordinates [0]" in str(failure.value)


def test_COL3_points_that_do_not_collide() -> None:  # noqa: N802
    """Two distinct points with distinct images."""
    apart = Collision(((1, 0), (1, 1)), (1, 0))

    with pytest.raises(VerificationError) as failure:
        apart.verify(SQUARE)

    assert failure.value.obligation == "COL-3"


def test_the_error_names_its_obligation(collision: Collision) -> None:
    """The identifier is in the message and not only in the attribute."""
    with pytest.raises(VerificationError, match=r"\[COL-3\]"):
        Collision(POINTS, (0, 0)).verify(SQUARE)


def test_located_at_attaches_a_step_index() -> None:
    original = VerificationError("COL-3", "something failed")
    located = original.located_at(4)

    assert located.obligation == "COL-3"
    assert located.step == 4
    assert "in step 4" in str(located)
    assert original.step is None


# --------------------------------------------------------------------------
# at()
# --------------------------------------------------------------------------


def test_at_computes_the_image(collision: Collision) -> None:
    assert Collision.at(SQUARE, POINTS) == collision


def test_at_verifies_before_returning() -> None:
    """at() cannot make a collision out of points that are not one."""
    with pytest.raises(VerificationError) as failure:
        Collision.at(SQUARE, ((1, 0), (1, 1)))

    assert failure.value.obligation == "COL-3"


# --------------------------------------------------------------------------
# Value semantics
# --------------------------------------------------------------------------


def test_equality_ignores_the_order_of_the_points(collision: Collision) -> None:
    assert Collision(tuple(reversed(POINTS)), IMAGE) == collision
    assert hash(Collision(tuple(reversed(POINTS)), IMAGE)) == hash(collision)


def test_a_different_image_is_a_different_collision(collision: Collision) -> None:
    assert Collision(POINTS, (1, 1)) != collision


def test_equality_with_other_types(collision: Collision) -> None:
    assert collision != object()


def test_extended_appends_coordinates(collision: Collision) -> None:
    """What a stabilising step needs."""
    wider = collision.extended(((2, 3), (-2, 3)), (0, 0))

    assert wider.dimension == 4
    assert wider.points[0] == (1, 0, 2, 3)
    assert wider.image == (1, 0, 0, 0)


def test_extended_checks_the_number_of_points(collision: Collision) -> None:
    with pytest.raises(ValueError, match="coordinates for 2 points"):
        collision.extended(((2, 3),), (0, 0))


def test_extended_checks_the_width(collision: Collision) -> None:
    with pytest.raises(ValueError, match="same number of coordinates"):
        collision.extended(((2, 3), (-2,)), (0, 0))


def test_extended_may_collapse_nothing(collision: Collision) -> None:
    """The appended coordinates must not make the points equal."""
    assert collision.extended(((), ()), ()) == collision


def test_with_image_keeps_the_points(collision: Collision) -> None:
    moved = collision.with_image((7, 8))

    assert moved.points == collision.points
    assert moved.image == (sp.Integer(7), sp.Integer(8))


def test_operations_return_new_objects(collision: Collision) -> None:
    before = collision.points

    collision.extended(((2, 3), (-2, 3)), (0, 0))
    collision.with_image((7, 8))

    assert collision.points == before


# --------------------------------------------------------------------------
# Regression: Alpoege's counterexample
# --------------------------------------------------------------------------

ALPOEGE_VARIABLES = sp.symbols("x1 x2 x3")
_1, _2, _3 = ALPOEGE_VARIABLES

ALPOEGE = PolynomialMap(
    ALPOEGE_VARIABLES,
    (
        (1 + _1 * _2) ** 3 * _3 + _2**2 * (1 + _1 * _2) * (4 + 3 * _1 * _2),
        _2 + 3 * _1 * (1 + _1 * _2) ** 2 * _3 + 3 * _1 * _2**2 * (4 + 3 * _1 * _2),
        2 * _1 - 3 * _1**2 * _2 - _1**3 * _3,
    ),
)

ALPOEGE_POINTS = (
    (0, 0, sp.Rational(-1, 4)),
    (1, sp.Rational(-3, 2), sp.Rational(13, 2)),
    (-1, sp.Rational(3, 2), sp.Rational(13, 2)),
)


def test_alpoeges_collision_verifies() -> None:
    """Three points, one image, constant determinant: the counterexample."""
    collision = Collision.at(ALPOEGE, ALPOEGE_POINTS)

    assert len(collision) == 3
    assert collision.dimension == 3
    assert collision.image == (sp.Rational(-1, 4), sp.Integer(0), sp.Integer(0))
    assert ALPOEGE.determinant() == -2


def test_the_normalized_image_is_the_one_bcw17_carries() -> None:
    """Normalisation moves the image only, not the preimages.

    This is the computation ``LinearStep`` records as a certificate in WP 3.
    Here it stands as a property of ``with_image``.
    """
    collision = Collision.at(ALPOEGE, ALPOEGE_POINTS)
    jacobian = ALPOEGE.jacobian().xreplace(
        {v: sp.Integer(0) for v in ALPOEGE_VARIABLES}
    )
    normalized = PolynomialMap(
        ALPOEGE_VARIABLES,
        tuple(
            sp.expand(e)
            for e in sp.Matrix(jacobian).inv() * sp.Matrix(ALPOEGE.components)
        ),
    )

    moved = collision.with_image(
        tuple(sp.Matrix(jacobian).inv() * sp.Matrix(collision.image))
    )

    assert moved.points == collision.points
    assert moved.image == (sp.Integer(0), sp.Integer(0), sp.Rational(-1, 4))
    assert moved.verify(normalized) is None
