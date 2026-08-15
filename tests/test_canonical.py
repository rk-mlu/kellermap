"""What "the same value" means in this package.

The occasion is a finding of the audit of 0.2.0rc1. ``Collision`` compared
coordinates with ``expand``, and that clears no denominator. Over ``k(T)`` the
identity ``(T^2 - 1)/(T - 1) = T + 1`` holds, and the old test saw two points
where one stands. That is COL-4 read backwards, and in the other direction a
correct image coordinate, merely written awkwardly, that COL-3 would have
rejected.

The regression tests at the end record exactly these two directions.
"""

import pytest
import sympy as sp

from kellermap import Collision, PolynomialMap, VerificationError
from kellermap.canonical import agree, canonical, is_zero

T = sp.Symbol("T")
x, y = sp.symbols("x y")

# The same number, written twice.
FOLDED = (T**2 - 1) / (T - 1)
PLAIN = T + 1


# --------------------------------------------------------------------------
# The test for zero itself
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("left", "right"),
    [
        (FOLDED, PLAIN),
        ((T * y + y) / y, T + 1),
        (sp.Rational(2, 4), sp.Rational(1, 2)),
        ((T**2 - 1) / ((T - 1) * (T + 1)), 1),
        (0, 0),
        (sp.sqrt(2) ** 2, 2),
    ],
)
def test_expressions_that_denote_one_value(left: sp.Expr, right: sp.Expr) -> None:
    assert agree(left, right)


@pytest.mark.parametrize(
    ("left", "right"),
    [
        (T + 1, T + 2),
        (FOLDED, T),
        (sp.Rational(1, 3), sp.Rational(1, 4)),
        (T, 0),
    ],
)
def test_expressions_that_do_not(left: sp.Expr, right: sp.Expr) -> None:
    assert not agree(left, right)


def test_expand_would_have_missed_it() -> None:
    """The control on the old test, so that the finding does not return."""
    assert sp.expand(FOLDED - PLAIN) != 0
    assert agree(FOLDED, PLAIN)


def test_canonical_normalizes() -> None:
    assert canonical(FOLDED) == PLAIN


def test_canonical_is_not_conversion() -> None:
    """A normal form is not a conversion: a float stays a float."""
    assert canonical(sp.Float(0.25)) != sp.Rational(1, 4)


def test_is_zero() -> None:
    assert is_zero((T**2 - 1) / (T - 1) - T - 1)
    assert not is_zero(T)


# --------------------------------------------------------------------------
# COL-4: two ways of writing it are one point
# --------------------------------------------------------------------------


def test_COL4_two_spellings_of_one_point() -> None:  # noqa: N802
    """The blocker from the audit, in its original form."""
    with pytest.raises(ValueError, match="distinct points"):
        Collision(((FOLDED, 0), (PLAIN, 0)), (0, 0))


def test_the_coordinates_are_stored_in_normal_form() -> None:
    """So that ``__eq__`` and ``__hash__`` can agree with each other."""
    collision = Collision(((FOLDED, 0), (T, 0)), (0, 0))

    assert collision.points[0] == (PLAIN, sp.Integer(0))


def test_equality_and_hash_survive_a_rewriting() -> None:
    """Two ways of writing down one collision are one object."""
    folded = Collision(((FOLDED, 0), (T, 0)), (FOLDED, 0))
    plain = Collision(((PLAIN, 0), (T, 0)), (PLAIN, 0))

    assert folded == plain
    assert hash(folded) == hash(plain)


# --------------------------------------------------------------------------
# COL-3: a correct image coordinate, merely written differently
# --------------------------------------------------------------------------


@pytest.fixture(scope="module")
def parametric() -> PolynomialMap:
    """F(x, y) = ((T + 1) x^2, y) over ZZ(T), with a collision."""
    return PolynomialMap((x, y), ((T + 1) * x**2, y))


def test_COL3_an_image_written_the_long_way(parametric: PolynomialMap) -> None:  # noqa: N802
    """The image at x = 1 is T + 1, written here as (T^2 - 1)/(T - 1)."""
    collision = Collision(((1, 0), (-1, 0)), (FOLDED, 0))

    assert collision.verify(parametric) is None


def test_COL3_still_rejects_a_wrong_image(parametric: PolynomialMap) -> None:  # noqa: N802
    """The normal form does not make the check lenient."""
    with pytest.raises(VerificationError) as failure:
        Collision(((1, 0), (-1, 0)), (T, 0)).verify(parametric)

    assert failure.value.obligation == "COL-3"


def test_a_parametric_collision_carries_through(parametric: PolynomialMap) -> None:
    collision = Collision.at(parametric, ((1, 0), (-1, 0)))

    assert collision.image == (PLAIN, sp.Integer(0))
    assert parametric.determinant() == 2 * (T + 1) * x
