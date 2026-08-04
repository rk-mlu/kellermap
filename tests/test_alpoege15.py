"""alpoege15: eine kubische Keller-Abbildung in Dimension 15.

Kein fremdes Beispiel, sondern die eigene Reduktion dieses Projekts. Sie
entsteht aus der siebzehndimensionalen, indem zwei Schritte einen Traeger
mitbenutzen, den ein frueherer Schritt schon gekauft hat: BCW17 legt ``x1**2``
zweimal an (in ``x5`` und ``x17``) und ``x1*x2`` ebenfalls zweimal (in ``x8``
und ``x14``). Wer die Doppelung vermeidet, spart je eine Variable.

Feste Eingabe, wie ``test_alpoege19.py`` -- und aus dem entgegengesetzten
Grund. Dort ist die Schrittfolge unbekannt; hier ist sie bekannt, aber
``Reduction`` kann sie nicht ausdruecken: beide geteilten Schritte sind der
Fall ``m = 1``, und BCW-2 legt zwei frische Variablen je Schritt fest. Das ist
Meilenstein 0.3. Bis dahin ist die Abbildung eine Handrechnung und keine
Aussage dieser Bibliothek, und die Tests unten rechnen genau das nach, was sich
ohne Zertifikat nachrechnen laesst.

Die zweite, von ``kellermap`` unabhaengige Rechnung steht in
``scripts/reconstruct_alpoege15.py``. Zur Herkunft und zu der Frage, was die
Zahl 15 bedeutet und was nicht, siehe ``docs/references.md``.
"""

import sympy as sp

from kellermap import Collision, PolynomialMap
from tests.test_bcw17 import BCW17_COLLISION
from tests.test_bcw17 import COMPONENTS as BCW17_COMPONENTS

X = sp.symbols("x1:16")
_1, _2, _3, _4, _5, _6, _7, _8, _9, _10, _11, _12, _13, _14, _15 = X

R = sp.Rational

COMPONENTS = (
    -3 * _1**2 * _2 / 2 - _1**2 * _4 + _1 * _3 * _5 / 2 + _1 - _4 * _5,
    12 * _1 * _2**2
    - _1 * _2 * _9
    - 6 * _1 * _3 * _8
    + 3 * _1 * _3
    + 3 * _1 * _7 * _8
    - 3 * _2**2 * _6
    + _2
    + _3 * _6 * _8
    - _6 * _7
    - _8 * _9,
    -3 * _1 * _10 * _3
    + _1 * _12 * _3
    - _1 * _14 * _2
    + 3 * _1 * _2 * _3
    - _10 * _11
    + _10 * _13 * _8
    - 7 * _10 * _2
    + _11 * _2 * _8
    - _12 * _13
    + 3 * _12 * _2
    - _14 * _8
    + 4 * _2**2
    + _3,
    -_1 * _3 / 2 + _4,
    _1**2 + _5,
    3 * _1**2 * _2 + _6,
    _1 * _2 * _3 + 3 * _2**2 + _7,
    _1 * _2 + _8,
    6 * _1 * _3 - 3 * _1 * _7 - _3 * _6 + _9,
    _1 * _2**2 + _10,
    -(_1**2) * _15
    + 3 * _1 * _2**2
    + 3 * _1 * _3
    + _11
    - _15 * _5
    - _2 * _3 * _5
    + 7 * _2,
    _1 * _10 * _2 + _12,
    -_1 * _3 + _13 - 3 * _2,
    -_10 * _13 - _11 * _2 + _14,
    _15 + _2 * _3,
)

COLLISION = (
    (0, 0, R(-1, 4)) + (0,) * 12,
    (
        1,
        R(-3, 2),
        R(13, 2),
        R(13, 4),
        -1,
        R(9, 2),
        3,
        R(3, 2),
        R(-3, 4),
        R(-9, 4),
        -6,
        R(-27, 8),
        2,
        R(9, 2),
        R(39, 4),
    ),
    (
        -1,
        R(3, 2),
        R(13, 2),
        R(-13, 4),
        -1,
        R(-9, 2),
        3,
        R(3, 2),
        R(3, 4),
        R(9, 4),
        6,
        R(27, 8),
        -2,
        R(9, 2),
        R(-39, 4),
    ),
)

IMAGE = (0, 0, R(-1, 4)) + (0,) * 12

# Die zwoelf Stabilisierungskoordinaten x4..x15.
CARRIER_INDICES = tuple(range(3, 15))

ALPOEGE15 = PolynomialMap(X, COMPONENTS)

CARRIERS = {index: sp.expand(COMPONENTS[index] - X[index]) for index in CARRIER_INDICES}


# --------------------------------------------------------------------------
# Die Abbildung selbst
# --------------------------------------------------------------------------


def test_dimension_and_degree() -> None:
    assert ALPOEGE15.dimension == 15
    assert ALPOEGE15.degree() == 3


def test_the_determinant_is_one() -> None:
    """Konstant, also eine Keller-Abbildung -- und normalisiert wie BCW17."""
    assert ALPOEGE15.determinant() == 1


def test_it_lies_in_MA0_but_not_in_MA1() -> None:  # noqa: N802
    """Aus demselben Grund wie BCW17: zwei Schritte erreichen nur EA^0."""
    assert ALPOEGE15.is_in_MA(0)
    assert not ALPOEGE15.is_in_MA(1)


def test_the_carrier_block_is_the_stabilization() -> None:
    assert ALPOEGE15.carrier_indices == CARRIER_INDICES


# --------------------------------------------------------------------------
# Die Kollision
# --------------------------------------------------------------------------


def test_alpoege15_is_not_injective() -> None:
    """Der eigentliche Inhalt: drei verschiedene Urbilder desselben Punktes."""
    collision = Collision(COLLISION, IMAGE)

    assert collision.verify(ALPOEGE15) is None
    assert len(collision) == 3
    assert collision.dimension == 15


def test_the_image_is_the_one_bcw17_carries() -> None:
    """Dieselbe Normalisierung, also dasselbe Bild, nur kuerzer aufgefuellt."""
    assert Collision.at(ALPOEGE15, COLLISION).image == tuple(map(sp.nsimplify, IMAGE))


def test_the_points_agree_with_bcw17_where_the_chains_agree() -> None:
    """Die ersten fuenf Schritte sind unveraendert, also die ersten 13 Koordinaten.

    Erst die geteilten Schritte 6 und 7 legen andere Variablen an; alles davor
    ist Zeichen fuer Zeichen dieselbe Rechnung.
    """
    ours = {tuple(map(sp.nsimplify, point))[:13] for point in COLLISION}
    theirs = {tuple(map(sp.nsimplify, point))[:13] for point in BCW17_COLLISION}

    assert ours == theirs


# --------------------------------------------------------------------------
# Der Zusammenhang mit BCW17
# --------------------------------------------------------------------------


def test_bcw17_buys_two_values_twice() -> None:
    """Der Befund, aus dem die Abbildung entstanden ist."""
    bcw17_carriers = [
        sp.expand(BCW17_COMPONENTS[index] - sp.Symbol(f"x{index + 1}"))
        for index in range(3, 17)
    ]
    doubled = [
        value
        for value in {sp.expand(_1**2), sp.expand(_1 * _2)}
        if bcw17_carriers.count(value) == 2
    ]

    assert len(doubled) == 2


def test_alpoege15_buys_each_value_once() -> None:
    """Und der Ertrag: kein Traegerwert kommt hier zweimal vor."""
    values = [sp.expand(value) for value in CARRIERS.values()]

    assert len(values) == len(set(values)) == 12


def test_eleven_components_are_untouched() -> None:
    """Was die geteilten Schritte nicht anfassen, bleibt woertlich stehen.

    Die Komponenten 3, 11, 14 und 15 aendern sich -- die ersten beiden, weil
    ein geteilter Schritt sie als Ziel hat, die letzten beiden, weil sie die
    Traeger sind, die dabei anders benannt werden.
    """
    unchanged = [
        index
        for index in range(13)
        if sp.expand(COMPONENTS[index] - BCW17_COMPONENTS[index]) == 0
    ]

    assert unchanged == [0, 1, 3, 4, 5, 6, 7, 8, 9, 11, 12]


def test_two_dimensions_below_bcw17() -> None:
    assert len(BCW17_COMPONENTS) - len(COMPONENTS) == 2


# --------------------------------------------------------------------------
# Was hier noch nicht steht
# --------------------------------------------------------------------------


def test_the_chain_is_not_yet_expressible() -> None:
    """Die Einschraenkung, die 0.3 aufhebt, als ausgefuehrte Aussage.

    Beide geteilten Schritte heben die Dimension um eins. BCW-2 verlangt zwei,
    also laesst sich diese Kette heute nicht als ``Reduction`` hinschreiben --
    weshalb die Abbildung hier feste Eingabe ist und nicht abgeleitet wie
    BCW17.
    """
    dimensions = (3, 3, 5, 7, 9, 11, 13, 14, 15)
    increments = [
        second - first
        for first, second in zip(dimensions, dimensions[1:], strict=False)
    ]

    assert increments == [0, 2, 2, 2, 2, 2, 1, 1]
    assert increments.count(1) == 2
