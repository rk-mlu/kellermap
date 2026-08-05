"""alpoege15: eine kubische Keller-Abbildung in Dimension 15.

Kein fremdes Beispiel, sondern die eigene Reduktion dieses Projekts. Sie
entsteht aus der siebzehndimensionalen, indem zwei Schritte einen Traeger
mitbenutzen, den ein frueherer Schritt schon angelegt hat: BCW17 legt ``x1**2``
zweimal an (in ``x5`` und ``x17``) und ``x1*x2`` ebenfalls zweimal (in ``x8``
und ``x14``). Wer die Doppelung vermeidet, spart je eine Variable.

Seit Meilenstein 0.3 wird die Abbildung abgeleitet und nicht mehr behauptet:
eine ``Reduction`` aus acht Schritten, Schritt fuer Schritt verifiziert, die
die Kollision mittraegt. Zwei der sieben BCW-Schritte haben ``m = 1``.

Was daran Beleg ist und was nicht
---------------------------------
Anders als bei BCW17 ist der Endpunkt hier keine aeussere Tatsache. Die
fixierten Komponenten weiter unten stammen aus derselben Handrechnung, die
auch die Kette erzeugt hat; ``scripts/reconstruct_alpoege15.py`` fuehrt sie in
reinem SymPy aus. Dass der letzte Schritt sein Ziel vorgelegt bekommt, zeigt
also die Uebereinstimmung zweier Umsetzungen derselben Formeln, nicht die
Uebereinstimmung mit einer veroeffentlichten Abbildung.

Die Zwischenabbildungen sind ``CONSTRUCTED``, und die Kette traegt nach RED-7
die schwaechere Provenienz.

Zur Herkunft und zu der Frage, was die Zahl 15 bedeutet und was nicht, siehe
``docs/references.md``.
"""

import pytest
import sympy as sp

from kellermap import (
    Collision,
    PolynomialMap,
    Provenance,
    Reduction,
    ReductionContext,
    VerificationError,
    over_field,
)
from kellermap.bcw import BCWStep, Carried, Fresh
from kellermap.reduction import LinearStep
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
# Ableitung: die Kette von Alpoege hierher
# --------------------------------------------------------------------------

ALPOEGE_VARIABLES = (_1, _2, _3)

ALPOEGE_COMPONENTS = (
    (1 + _1 * _2) ** 3 * _3 + _2**2 * (1 + _1 * _2) * (4 + 3 * _1 * _2),
    _2 + 3 * _1 * (1 + _1 * _2) ** 2 * _3 + 3 * _1 * _2**2 * (4 + 3 * _1 * _2),
    2 * _1 - 3 * _1**2 * _2 - _1**3 * _3,
)

ALPOEGE_COLLISION = (
    (0, 0, R(-1, 4)),
    (1, R(-3, 2), R(13, 2)),
    (-1, R(3, 2), R(13, 2)),
)

# Die sieben Anwendungen von Proposition (3.1): Zielkomponente (nullbasiert),
# die beiden Faktorplaetze, und die EA-Stufe. Ein Platz ist entweder
# ("fresh", P) -- die Variable dazu vergibt der ReductionContext -- oder
# ("carried", j) fuer die Koordinate j, die den Faktor schon traegt.
STEPS = (
    (0, ("fresh", -_1 * _3 / 2), ("fresh", _1**2), 1),
    (1, ("fresh", 3 * _1**2 * _2), ("fresh", _1 * _2 * _3 + 3 * _2**2), 1),
    (1, ("fresh", _1 * _2), ("fresh", 6 * _1 * _3 - 3 * _1 * _7 - _3 * _6), 1),
    (
        2,
        ("fresh", _1 * _2**2),
        ("fresh", _1**2 * _2 * _3 + 3 * _1 * _2**2 + 3 * _1 * _3 + 7 * _2),
        0,
    ),
    (2, ("fresh", _1 * _2 * _10), ("fresh", -_1 * _3 - 3 * _2), 0),
    # x1*x2 liegt seit Schritt 3 als Komponente 8 vor, also Index 7.
    (2, ("carried", 7), ("fresh", -_10 * _13 - _2 * _11), 1),
    # x1**2 liegt seit Schritt 1 als Komponente 5 vor, also Index 4.
    (10, ("carried", 4), ("fresh", _2 * _3), 1),
)


@pytest.fixture(scope="module")
def alpoege() -> PolynomialMap:
    """Ueber QQ, weil die Normalisierung sofort einen Kehrwert braucht."""
    return over_field(PolynomialMap(ALPOEGE_VARIABLES, ALPOEGE_COMPONENTS))


@pytest.fixture(scope="module")
def reduction(alpoege: PolynomialMap) -> Reduction:
    """Die vollstaendige Kette, mit vorgelegtem Ziel im letzten Schritt."""
    context = ReductionContext()
    normalization = LinearStep.normalize(alpoege)
    steps: list[LinearStep | BCWStep] = [normalization]
    current = normalization.target

    for position, (index, left, right, level) in enumerate(STEPS):
        specs = (left, right)
        fresh = context.variables(
            current.ring, sum(kind == "fresh" for kind, _ in specs)
        )
        allocated = iter(fresh)
        slots = tuple(
            Fresh(value, next(allocated)) if kind == "fresh" else Carried(int(value))
            for kind, value in specs
        )
        last = position == len(STEPS) - 1
        step = (
            BCWStep(current, ALPOEGE15, index, *slots, level)
            if last
            else BCWStep.build(current, index, *slots, level)
        )
        steps.append(step)
        current = step.target

    return Reduction(steps)


def test_the_reduction_verifies(reduction: Reduction) -> None:
    """Acht Schritte, jeder einzeln geprueft, und jede Naht dazwischen."""
    assert reduction.verify() is None
    assert len(reduction) == 8


def test_the_reduction_reaches_alpoege15(reduction: Reduction) -> None:
    assert reduction.target == ALPOEGE15


def test_two_steps_reuse_a_carrier(reduction: Reduction) -> None:
    """Der Grund fuer die Dimension: zweimal m = 1 statt zweimal m = 2."""
    levels = [step.m for step in reduction if isinstance(step, BCWStep)]

    assert levels == [2, 2, 2, 2, 2, 1, 1]
    assert sum(levels) == 12


def test_the_dimensions_and_degrees(reduction: Reduction) -> None:
    """3 auf 15 statt auf 17, Grad 7 auf 3."""
    assert reduction.dimensions() == (3, 3, 5, 7, 9, 11, 13, 14, 15)
    assert reduction.degrees() == (7, 7, 7, 7, 7, 5, 4, 4, 3)


def test_the_context_names_x4_to_x15(reduction: Reduction) -> None:
    allocated = tuple(
        variable
        for step in reduction
        if isinstance(step, BCWStep)
        for variable in step.variables
    )

    assert allocated == X[3:]


def test_the_reused_coordinates_are_the_ones_bcw17_duplicates(
    reduction: Reduction,
) -> None:
    """Genau die beiden Werte, die BCW17 zweimal anlegt."""
    reused = [
        (step.left, step.P)
        for step in reduction
        if isinstance(step, BCWStep) and isinstance(step.left, Carried)
    ]

    assert reused == [(Carried(7), _1 * _2), (Carried(4), _1**2)]


def test_the_collision_is_transported(
    reduction: Reduction, alpoege: PolynomialMap
) -> None:
    """Drei Punkte in k^3 werden drei Punkte in k^15."""
    carried = reduction.transport(Collision.at(alpoege, ALPOEGE_COLLISION))

    assert carried == Collision(COLLISION, IMAGE)


def test_the_image_does_not_move(reduction: Reduction, alpoege: PolynomialMap) -> None:
    """Kein Schritt hat m = 0, also bleibt das Bild bis auf Nullen stehen."""
    carried = reduction.transport(Collision.at(alpoege, ALPOEGE_COLLISION))

    assert carried.image[:3] == (0, 0, R(-1, 4))
    assert set(carried.image[3:]) == {sp.Integer(0)}


def test_the_provenance_is_constructed(reduction: Reduction) -> None:
    """Der Endpunkt ist keine aeussere Tatsache, anders als bei BCW17."""
    assert reduction.provenance is Provenance.CONSTRUCTED
    assert reduction[-1].provenance is Provenance.SUPPLIED


def test_a_perturbed_target_would_be_caught(reduction: Reduction) -> None:
    """Gegenprobe: der letzte Schritt prueft wirklich etwas."""
    last = reduction[-1]
    perturbed = PolynomialMap(X, (COMPONENTS[0] + _4 * _5,) + COMPONENTS[1:])
    broken = BCWStep(last.source, perturbed, last.index, last.left, last.right)

    with pytest.raises(VerificationError) as failure:
        Reduction([*list(reduction[:-1]), broken]).verify()

    assert failure.value.obligation == "BCW-1"
    assert failure.value.step == 7
