"""Was in diesem Paket "derselbe Wert" heisst.

Der Anlass ist ein Befund aus dem Audit von 0.2.0rc1: ``Collision`` verglich
Koordinaten mit ``expand``, und das raeumt keinen Nenner ab. Ueber ``k(T)``
gilt ``(T^2 - 1)/(T - 1) = T + 1``, und der alte Test sah dort zwei Punkte, wo
einer steht -- COL-4 rueckwaerts gelesen, und in der Gegenrichtung eine
korrekte, nur unguenstig geschriebene Bildkoordinate, die COL-3 verworfen
haette.

Die Regressionstests am Ende halten genau diese beiden Richtungen fest.
"""

import pytest
import sympy as sp

from kellermap import Collision, PolynomialMap, VerificationError
from kellermap.canonical import agree, canonical, is_zero

T = sp.Symbol("T")
x, y = sp.symbols("x y")

# Dieselbe Zahl, zweimal geschrieben.
FOLDED = (T**2 - 1) / (T - 1)
PLAIN = T + 1


# --------------------------------------------------------------------------
# Der Nulltest selbst
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
    """Die Gegenprobe auf den alten Test, damit der Befund nicht zurueckkehrt."""
    assert sp.expand(FOLDED - PLAIN) != 0
    assert agree(FOLDED, PLAIN)


def test_canonical_normalizes() -> None:
    assert canonical(FOLDED) == PLAIN


def test_canonical_is_not_conversion() -> None:
    """Normalform ist keine Umwandlung: Float bleibt Float."""
    assert canonical(sp.Float(0.25)) != sp.Rational(1, 4)


def test_is_zero() -> None:
    assert is_zero((T**2 - 1) / (T - 1) - T - 1)
    assert not is_zero(T)


# --------------------------------------------------------------------------
# COL-4: zwei Schreibweisen sind ein Punkt
# --------------------------------------------------------------------------


def test_COL4_two_spellings_of_one_point() -> None:  # noqa: N802
    """Der Blocker aus dem Audit, in seiner urspruenglichen Form."""
    with pytest.raises(ValueError, match="distinct points"):
        Collision(((FOLDED, 0), (PLAIN, 0)), (0, 0))


def test_the_coordinates_are_stored_in_normal_form() -> None:
    """Damit ``__eq__`` und ``__hash__`` miteinander uebereinstimmen koennen."""
    collision = Collision(((FOLDED, 0), (T, 0)), (0, 0))

    assert collision.points[0] == (PLAIN, sp.Integer(0))


def test_equality_and_hash_survive_a_rewriting() -> None:
    """Zwei Wege, dieselbe Kollision hinzuschreiben, sind ein Objekt."""
    folded = Collision(((FOLDED, 0), (T, 0)), (FOLDED, 0))
    plain = Collision(((PLAIN, 0), (T, 0)), (PLAIN, 0))

    assert folded == plain
    assert hash(folded) == hash(plain)


# --------------------------------------------------------------------------
# COL-3: eine korrekte, nur anders geschriebene Bildkoordinate
# --------------------------------------------------------------------------


@pytest.fixture(scope="module")
def parametric() -> PolynomialMap:
    """F(x, y) = ((T + 1) x^2, y) ueber ZZ(T), mit einer Kollision."""
    return PolynomialMap((x, y), ((T + 1) * x**2, y))


def test_COL3_an_image_written_the_long_way(parametric: PolynomialMap) -> None:  # noqa: N802
    """Das Bild bei x = 1 ist T + 1, hier als (T^2 - 1)/(T - 1) geschrieben."""
    collision = Collision(((1, 0), (-1, 0)), (FOLDED, 0))

    assert collision.verify(parametric) is None


def test_COL3_still_rejects_a_wrong_image(parametric: PolynomialMap) -> None:  # noqa: N802
    """Die Normalform macht die Pruefung nicht nachgiebig."""
    with pytest.raises(VerificationError) as failure:
        Collision(((1, 0), (-1, 0)), (T, 0)).verify(parametric)

    assert failure.value.obligation == "COL-3"


def test_a_parametric_collision_carries_through(parametric: PolynomialMap) -> None:
    collision = Collision.at(parametric, ((1, 0), (-1, 0)))

    assert collision.image == (PLAIN, sp.Integer(0))
    assert parametric.determinant() == 2 * (T + 1) * x
