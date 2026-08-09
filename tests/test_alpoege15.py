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
    enumerate_candidates,
    examples,
    over_field,
    search,
)
from kellermap.bcw import BCWStep, Carried, Fresh
from kellermap.reduction import LinearStep
from tests.test_bcw17 import BCW17_COLLISION
from tests.test_bcw17 import COMPONENTS as BCW17_COMPONENTS

ALPOEGE15 = examples.alpoege15()
X = ALPOEGE15.variables
COMPONENTS = ALPOEGE15.components
COLLISION = examples.alpoege15_collision().points
IMAGE = examples.alpoege15_collision().image
ALPOEGE_COLLISION = examples.alpoege_collision().points

_1, _2, _3, _4, _5, _6, _7, _8, _9, _10, _11, _12, _13, _14, _15 = X

R = sp.Rational


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


def test_reordering_the_generators_changes_no_value() -> None:
    """SEA-4 an einer Abbildung, deren Umsortierung bekannt ist.

    Die Suche in 0.4 baut eine Kette, deren Generatoren in der Reihenfolge
    ihrer Einfuehrung stehen; eine veroeffentlichte Abbildung listet dieselben
    Generatoren anders. Umsortieren ist Darstellung und kein Schritt, also muss
    es genau nichts am Wert aendern -- hier in Dimension 15 nachgerechnet, wo
    ein Fehler in der Monomkodierung nicht mehr zufaellig durchgeht.
    """
    shuffled = X[3:] + X[:3]

    moved = ALPOEGE15.reordered(shuffled)

    assert moved.variables == shuffled
    assert moved != ALPOEGE15
    assert moved.reordered(X) == ALPOEGE15
    assert moved.determinant() == ALPOEGE15.determinant()
    assert moved.degree() == ALPOEGE15.degree()
    assert moved.filtration_degree() == ALPOEGE15.filtration_degree()


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
    return over_field(examples.alpoege())


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


def test_the_enumerator_contains_every_step_of_this_chain(
    reduction: Reduction,
) -> None:
    """Die Kontrolle fuer den Kandidatenaufzaehler, an bekannten Schritten.

    Der Vorrat kommt aus der Zielabbildung: die Werte, die ihre Traegerkoor-
    dinaten halten. Fuer jeden Schritt der Kette muss der Aufzaehler an der
    Karte davor einen Kandidaten mit derselben Zielkomponente und denselben
    beiden Faktoren liefern, und die abgeleitete EA-Stufe muss die des
    Schritts sein.

    Ein Aufzaehler, der einen nachweislich existierenden Schritt uebergeht,
    ist unvollstaendig auf eine Weise, die ein Fehlschlag der Suche allein
    nicht zeigen wuerde.
    """
    final = reduction.target
    pool = [
        sp.expand(final.components[index] - final.variables[index])
        for index in final.carrier_indices
    ]

    steps = [step for step in reduction.steps if isinstance(step, BCWStep)]
    assert len(steps) == 7

    for position, step in enumerate(steps, start=1):
        wanted = sorted(str(sp.expand(value)) for value in (step.P, step.Q))
        found = [
            candidate
            for candidate in enumerate_candidates(step.source, pool)
            if candidate.index == step.index
            and sorted(str(sp.expand(v)) for v in candidate.values(step.source))
            == wanted
        ]

        assert found, f"Schritt {position} fehlt in der Aufzaehlung"
        assert found[0].filtration_level(step.source) == step.filtration_level


@pytest.mark.slow
def test_the_search_recovers_a_chain_to_this_map(reduction: Reduction) -> None:
    """Die Abnahmebedingung fuer die Suche, an einer bekannten Abbildung.

    Quelle ist Alpoeges normalisierte Abbildung, Ziel ist ALPOEGE15, und der
    Vorrat sind die Werte, die ihre Traegerkoordinaten halten -- mit einer
    Ergaenzung, die genau die Bedingung unter SEA-8 sichtbar macht. Schritt
    sieben zielt auf Komponente 10 und schreibt sie um, also steht der Wert,
    mit dem diese Koordinate eingefuehrt wurde, in der Zielabbildung nicht
    mehr. Ohne ihn ist die Kette fuer die Suche unerreichbar, nicht bloss
    ungefunden.

    Gefunden wird *eine* Kette, nicht *die* Kette. Ihre Gradfolge unterscheidet
    sich von der ueberlieferten; siehe "No optimality of the sequence" in
    ``docs/contracts.md``.

    ``rewrites=0``, weil dieser Test von der Regel handelt, dass jeder frische
    Platz einen Vorratswert traegt. Mit der Lockerung nach SEA-13 findet
    dieselbe Suche die Kette in 400 Karten nicht -- gemessen, und der Grund,
    warum die Lockerung eine benannte Ausnahme und keine Vorgabe ist.
    """
    source = reduction.steps[0].target
    pool = {
        X[index]: sp.expand(COMPONENTS[index] - X[index])
        for index in ALPOEGE15.carrier_indices
    }
    pool[X[10]] = sp.expand(STEPS[3][2][1])

    outcome = search(source, ALPOEGE15, pool, budget=2000, rewrites=0)

    assert outcome.reduction is not None
    assert outcome.reduction.verify() is None
    assert outcome.reduction.source == source
    assert outcome.reduction.target.reordered(ALPOEGE15.variables) == ALPOEGE15


@pytest.mark.slow
def test_without_that_value_the_chain_is_out_of_reach(reduction: Reduction) -> None:
    """Negativkontrolle zur Bedingung unter SEA-8.

    Derselbe Lauf mit dem Wert, den die Zielabbildung wirklich traegt. Der
    Aufzaehler kann den Schritt dann nicht anbieten, und der Fehlschlag sagt
    nichts ueber die Existenz der Kette -- SEA-6.
    """
    source = reduction.steps[0].target
    pool = {
        X[index]: sp.expand(COMPONENTS[index] - X[index])
        for index in ALPOEGE15.carrier_indices
    }

    outcome = search(source, ALPOEGE15, pool, budget=400, rewrites=0)

    assert outcome.reduction is None
