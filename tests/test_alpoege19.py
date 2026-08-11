"""Die 19-dimensionale kubische Keller-Abbildung aus einer fremden Quelle.

Feste Eingabe wie BCW17, und aus demselben Grund: die Schrittfolge liegt nicht
vor. Anders als bei BCW17 laesst sie sich hier auch nicht ablesen -- die Quelle
veroeffentlicht die Abbildung, nicht ihre Faktorisierung.

Bis 0.4 stand hier, die ``w``-Nummerierung sei nicht die
Einfuehrungsreihenfolge, weil ``G5`` die spaeteren ``w13`` und ``w9`` benutzt.
Das war ein Fehlschluss. ``G5`` ist die Komponente von ``w2``, und die ist kein
eingefuehrter Wert, sondern der Rest eines spaeteren Schritts -- siehe unten.
Nach dieser Korrektur zeigt jede Abhaengigkeit auf einen kleineren Index, und
``w1`` bis ``w16`` ist eine gueltige Einfuehrungsreihenfolge. Bewiesen ist
damit nichts: sie ist eine von etwa 7.26e10 gueltigen. Sie ist nur wieder die
naheliegende.

Die Quelle beschreibt ihr Verfahren als siebzehn elementare Schritte mit
sechzehn Traegervariablen, also nicht zwei je Schritt. Die ``P_j`` bestaetigen
das: ``x^2``, ``xy``, ``y^2``, ``yz``, ``xz``, ``x^2 y``, ``xy^2``, ``y^2 z``
sind Bausteine, die mehr als ein Schritt benutzt. Seit 0.3 kann ``BCWStep``
einen solchen Schritt ausdruecken.

Was fehlt, ist die Schrittfolge. Die Quelle veroeffentlicht die Abbildung, aber
nicht ihre Faktorisierung. Sie zu rekonstruieren ist eine Suchaufgabe und damit
Meilenstein 0.4. Bis dahin steht die Abbildung hier als feste Eingabe.

Die Kollision wird nicht aus der Tabelle der Quelle uebernommen, sondern aus
``w_j = -P_j`` rekonstruiert und danach mit der Tabelle verglichen. Beide Wege
sind unabhaengig.

Die Komponenten unten sind aus der gerenderten Textfassung abgeschrieben, in
der die Exponenten verlorengegangen sind -- ``w32`` ist ``w3^2``. Die Abschrift
wurde am 3. August 2026 gegen den maschinenlesbaren Abzug geprueft, den die
Quelle verlinkt: alle neunzehn Komponenten stimmen als Polynome ueberein, die
Variablenreihenfolge ebenso, und alle drei Punkte in allen neunzehn
Koordinaten. Der Abzug selbst liegt bewusst nicht im Repository; die Gruende
stehen in ``docs/references.md``.

Beilaeufig ist das hier die Messung, die die Entwurfsentscheidung zum
Schur-Komplement traegt: ``determinant()`` braucht ueber den Traegerblock
Sekundenbruchteile, waehrend ``sp.Matrix(F.jacobian()).det()`` bei 19
Variablen in einer Viertelstunde nicht fertig wird.

Zur Herkunft siehe ``docs/references.md``. Die Quelle ist eine
selbstveroeffentlichte Notiz und traegt hier keine Autoritaet; was die Daten
brauchbar macht, ist ausschliesslich, dass die Pruefungen unten sie
nachrechnen.
"""

import pytest
import sympy as sp

from kellermap import Collision, PolynomialMap, Reduction, examples, peel
from kellermap.bcw import BCWStep, Carried, Fresh

pytest.importorskip(
    "tests.data",
    reason=(
        "The nineteen-dimensional map is somebody else's mathematics and its "
        "licence could not be established, so this project does not "
        "distribute it. tests/data.py is in the repository and excluded from "
        "the source archive; without it this module has nothing to check."
    ),
)

from tests.data import (  # noqa: E402, F401
    ALPOEGE_IMAGE,
    ALPOEGE_POINTS,
    CARRIERS,
    COMPONENTS,
    PUBLISHED_POINTS,
    VARIABLES,
    W2_INTRODUCED,
    w,
    w1,
    w2,
    w3,
    w4,
    w5,
    w6,
    w7,
    w8,
    w9,
    w10,
    w11,
    w12,
    w13,
    w14,
    w15,
    w16,
    x,
    y,
    z,
)

# ``tests/data.py`` holds SymPy constants and nothing else, so that
# ``scripts/reconstruct_alpoege19.py`` can read the map without the library it
# checks. The map itself is built here.
ALPOEGE19 = PolynomialMap(VARIABLES, COMPONENTS)

# Die drei Punkte aus der Quelle, zum Vergleich mit der Rekonstruktion.


# Die Traegerkomponenten haben die Form w_j + P_j.


def lift(point: tuple[sp.Expr, ...]) -> tuple[sp.Expr, ...]:
    """Einen Punkt aus k^3 zu einem Punkt aus k^19 ergaenzen.

    Ein Urbild der stabilisierten Abbildung erfuellt ``w_j = -P_j``. Das System
    ist dreieckig -- der Abhaengigkeitsgraph der Traeger ist azyklisch, sonst
    waere der Jacobiblock nicht unipotent --, also terminiert die Iteration ab
    Null. Dass sie es tut, wird geprueft und nicht angenommen.
    """
    values = dict(zip((x, y, z), point, strict=True))
    values.update({variable: sp.Integer(0) for variable in w})

    for _ in range(len(w) + 1):
        updated = {
            variable: sp.expand(-CARRIERS[variable].xreplace(values)) for variable in w
        }
        if updated == {variable: values[variable] for variable in w}:
            break
        values.update(updated)
    else:  # pragma: no cover
        raise AssertionError("the carrier system did not terminate")

    return tuple(values[variable] for variable in VARIABLES)


# --------------------------------------------------------------------------
# Die Abbildung selbst
# --------------------------------------------------------------------------


def test_dimension_and_degree() -> None:
    assert ALPOEGE19.dimension == 19
    assert ALPOEGE19.degree() == 3


def test_the_determinant_is_minus_two() -> None:
    """Konstant, also eine Keller-Abbildung -- und nicht normalisiert.

    BCW17 hat Determinante 1, weil dort der Schritt aus Proposition (1.1)
    vorangeht. Hier fehlt er.
    """
    assert ALPOEGE19.determinant() == -2


def test_it_lies_in_MA0_but_not_in_MA1() -> None:  # noqa: N802
    assert ALPOEGE19.is_in_MA(0)
    assert not ALPOEGE19.is_in_MA(1)


def test_the_linear_part_is_alpoeges_own() -> None:
    """Weiterer Beleg, dass nicht normalisiert wurde.

    Der Linearteil ist Alpoeges ``[[0,0,1],[0,1,0],[2,0,0]]``, um die
    Identitaet auf den Traegern ergaenzt.
    """
    linear = sp.Matrix(
        ALPOEGE19.jacobian().xreplace(
            {variable: sp.Integer(0) for variable in VARIABLES}
        )
    )

    assert linear[:3, :3] == sp.Matrix([[0, 0, 1], [0, 1, 0], [2, 0, 0]])
    assert linear[3:, 3:] == sp.eye(16)
    assert linear.det() == -2


def test_the_carrier_block_is_the_stabilization() -> None:
    """Die sechzehn hinteren Koordinaten tragen die Reduktion."""
    assert ALPOEGE19.carrier_indices == tuple(range(3, 19))


def test_the_factors_cannot_be_read_off_pairwise() -> None:
    """Deshalb steht die Abbildung hier und nicht als Reduction.

    Bei BCW17 lassen sich die Faktoren paarweise aus den Komponenten ablesen,
    weil Schritt k die Variablen 2k+2 und 2k+3 anlegt. Hier greift die
    Komponente von ``w2`` auf ``w9`` und ``w13`` zu, also gibt es kein solches
    Muster.

    Der Test hiess bis 0.4 ``..._numbering_is_not_the_introduction_order`` und
    behauptete damit mehr, als er zeigt. Die Komponente von ``w2`` ist ein Rest
    und kein eingefuehrter Wert, sagt ueber den Zeitpunkt seiner Einfuehrung
    also nichts.
    """
    assert {w9, w13} <= CARRIERS[w2].free_symbols


def test_the_carriers_are_shared_building_blocks() -> None:
    """Siebzehn Schritte, sechzehn Variablen: nicht zwei je Schritt.

    Seit 0.3 laesst sich ein solcher Schritt als ``BCWStep`` mit einem
    ``Carried``-Platz hinschreiben. Was fehlt, ist die Schrittfolge.
    """
    monomials = {CARRIERS[w7], CARRIERS[w9], CARRIERS[w13]}

    assert monomials == {y**2, x * y, x**2}
    # x^2 taucht als Baustein in mehreren spaeteren Traegern wieder auf.
    assert w13 in CARRIERS[w2].free_symbols


# --------------------------------------------------------------------------
# Die Kollision
# --------------------------------------------------------------------------


def test_the_reconstruction_reproduces_the_published_points() -> None:
    """Zwei unabhaengige Wege, dieselben Zahlen.

    Die Punkte kommen hier aus ``w_j = -P_j`` und nicht aus der Tabelle der
    Quelle; die Tabelle dient nur zum Vergleich.
    """
    lifted = tuple(lift(point) for point in ALPOEGE_POINTS)
    expected = tuple(
        tuple(sp.nsimplify(coordinate) for coordinate in point)
        for point in PUBLISHED_POINTS
    )

    assert lifted == expected


def test_the_collision_verifies() -> None:
    collision = Collision.at(ALPOEGE19, [lift(point) for point in ALPOEGE_POINTS])

    assert len(collision) == 3
    assert collision.dimension == 19
    assert collision.verify(ALPOEGE19) is None


def test_the_image_is_alpoeges_own_padded_with_zeros() -> None:
    """Keine Normalisierung, also wandert das Bild auch nicht."""
    collision = Collision.at(ALPOEGE19, [lift(point) for point in ALPOEGE_POINTS])

    assert (
        collision.image
        == tuple(sp.nsimplify(c) for c in ALPOEGE_IMAGE) + (sp.Integer(0),) * 16
    )


def test_the_points_extend_alpoeges_in_their_first_three_coordinates() -> None:
    collision = Collision.at(ALPOEGE19, [lift(point) for point in ALPOEGE_POINTS])

    assert tuple(point[:3] for point in collision.points) == tuple(
        tuple(sp.nsimplify(coordinate) for coordinate in point)
        for point in ALPOEGE_POINTS
    )


def test_the_first_point_is_the_origin_over_alpoeges() -> None:
    """P1 liegt auf allen Traegern bei null, weil alle P_j dort verschwinden."""
    assert lift(ALPOEGE_POINTS[0])[3:] == (sp.Integer(0),) * 16


# --------------------------------------------------------------------------
# Ein Stueck der gesuchten Schrittfolge
# --------------------------------------------------------------------------

# Die Komponente von w2 ist kein eingefuehrter Traegerwert, sondern der Rest
# eines spaeteren Schritts. Proposition (3.1) hinterlaesst in der Zielkomponente
#
#     (F_i - P Q) - X_a Q - P X_b - X_a X_b,
#
# und mit den beiden Traegerkoordinaten w13 und w9 als Plaetzen -- sie tragen
# x^2 und x y -- ist der eingefuehrte Wert von w2 genau P Q = x^3 y, der sich
# gegen den ersten Term weghebt. Was stehen bleibt, sind die drei Restterme.


def test_the_component_of_w2_is_the_residue_of_a_carried_step() -> None:
    """Ein Schritt mit zwei ``Carried``-Plaetzen, also ``m = 0``.

    Die Abbildung waechst von Dimension 3 auf 19, also ist die Summe der ``m``
    ueber siebzehn Schritte gleich sechzehn und mindestens einer hat ``m = 0``.
    Dies ist einer, und es ist der einzige, den die Daten hergeben.
    """
    left, right = CARRIERS[w13], CARRIERS[w9]

    residue = sp.expand(
        (W2_INTRODUCED - left * right) - w13 * right - left * w9 - w13 * w9
    )

    assert left == x**2
    assert right == x * y
    assert residue == sp.expand(CARRIERS[w2])


def test_the_removed_product_is_the_value_w2_was_introduced_with() -> None:
    """Der ``-P Q``-Term fehlt im Rest, weil er sich weghebt.

    Genau daran ist der eingefuehrte Wert ablesbar: er muss ``P Q`` sein.
    """
    assert sp.expand(CARRIERS[w13] * CARRIERS[w9]) == W2_INTRODUCED


def test_a_perturbed_residue_is_not_the_component() -> None:
    """Negativkontrolle: ohne sie sagt die Uebereinstimmung oben nichts."""
    for perturbation in (w13 * w9, w13 * x * y, w9 * x**2):
        broken = sp.expand(CARRIERS[w2] + perturbation)

        assert broken != sp.expand(CARRIERS[w2])
        assert broken != sp.expand(
            (W2_INTRODUCED - CARRIERS[w13] * CARRIERS[w9])
            - w13 * CARRIERS[w9]
            - CARRIERS[w13] * w9
            - w13 * w9
        )


def test_w2_is_the_only_carrier_that_shows_the_signature() -> None:
    """Der Rest eines Schritts traegt ein Monom in zwei Traegervariablen.

    Das ist keine Faustregel. Beide Platzkoordinaten eines Schritts sind
    Traegervariablen -- ``Carried`` verlangt einen Traeger, ``Fresh`` legt
    einen an -- und die Komponenten von x, y und z sind hier keine Traeger,
    kommen als Platz also nicht in Frage. Ein Rest muss die Signatur tragen.
    Ein Wert wie ``w6 = w1 x`` nennt zwar eine Traegervariable, aber nur eine.

    Was der Test nicht ausschliesst: dass sich der ``-X_a X_b``-Term gegen
    einen Term des eingefuehrten Werts weghebt, so wie sich bei ``w2`` der
    ``-P Q``-Term weghebt. Eine so ueberschriebene Komponente saehe unberuehrt
    aus. Der Test zeigt, dass nur ``w2`` die Signatur traegt, nicht, dass nur
    ``w2`` ueberschrieben wurde.
    """
    rewritten = [
        variable
        for variable, value in CARRIERS.items()
        if any(
            sum(1 for exponent in monomial[3:] if exponent) >= 2
            for monomial in sp.Poly(value, *VARIABLES).monoms()
        )
    ]

    assert rewritten == [w2]


def test_the_numbering_is_a_valid_introduction_order() -> None:
    """Jede Abhaengigkeit zeigt auf einen kleineren Index -- nach der Korrektur.

    Der eingefuehrte Wert von ``w2`` ist ``x^3 y`` und nennt keine
    Traegervariable; die beiden, die seine veroeffentlichte Komponente nennt,
    stehen dort als Rest. Damit ist ``w1`` bis ``w16`` eine gueltige
    topologische Sortierung des Abhaengigkeitsgraphen.

    Das beweist nicht, dass es die Reihenfolge war. Es entkraeftet den einzigen
    Beleg dagegen, den die Quelle hergibt.
    """
    values = dict(CARRIERS)
    values[w2] = W2_INTRODUCED

    for position, variable in enumerate(w):
        used = {
            w.index(symbol) for symbol in values[variable].free_symbols if symbol in w
        }

        assert all(earlier < position for earlier in used), variable


def test_the_uncorrected_value_of_w2_is_what_broke_the_reading() -> None:
    """Negativkontrolle: mit dem abgelesenen Wert scheitert die Sortierung.

    Und zwar an genau einer Stelle. Ohne diese Kontrolle sagt der Test darueber
    die Korrektur nichts -- er koennte auch dann gruen sein, wenn der
    abgelesene Wert ebenso gepasst haette.
    """
    offenders = [
        variable
        for position, variable in enumerate(w)
        if any(
            w.index(symbol) >= position
            for symbol in CARRIERS[variable].free_symbols
            if symbol in w
        )
    ]

    assert offenders == [w2]


def test_the_pool_read_off_the_map_misses_that_value() -> None:
    """Was der Befund fuer die Suche heisst.

    SEA-8 laesst einen Anker aus dem Vorrat kommen, und der Vorrat wird von
    der Zielabbildung abgelesen. Der Wert, mit dem ``w2`` eingefuehrt wurde,
    steht dort nicht: ein Aufzaehler erreicht diesen Schritt nur ueber seinen
    Partner. Die Bedingung, unter der ein abgelesener Vorrat traegt, steht
    unter SEA-8 in ``docs/contracts.md``.
    """
    assert W2_INTRODUCED not in set(CARRIERS.values())


# --------------------------------------------------------------------------
# Was zuletzt eingefuehrt worden sein kann
# --------------------------------------------------------------------------


def occurrences(variable: sp.Symbol) -> list[int]:
    """Return the components a carrier variable occurs in."""
    return [
        index
        for index, component in enumerate(COMPONENTS)
        if variable in sp.expand(component).free_symbols
    ]


def test_six_coordinates_could_have_been_introduced_last() -> None:
    """Ein Schritt hinterlaesst seine frische Koordinate an genau zwei Stellen.

    In ihrer eigenen Komponente, als ``X_u + P``, und im Rest der
    Zielkomponente. Kommt sie sonst nirgends vor, kann sie die zuletzt
    eingefuehrte sein; kommt sie oefter vor, hat ein spaeterer Schritt sie
    benutzt und sie kann es nicht sein.

    Sechs von sechzehn erfuellen das. Das ist der Grund, warum die Suche
    rueckwaerts guenstiger ist als vorwaerts: hier sind es sechs Kandidaten
    fuer den letzten Schritt, vorwaerts bietet der Aufzaehler an einer Karte
    dieser Groesse ueber hundert an.
    """
    last = {
        variable
        for variable in w
        if len(occurrences(variable)) == 2
        and VARIABLES.index(variable) in occurrences(variable)
    }

    assert last == {w[9], w[10], w[11], w[13], w[14], w[15]}


def test_the_target_of_each_such_step_is_read_off_too() -> None:
    """Die zweite Komponente ist die, auf die der einfuehrende Schritt zielte.

    Drei der sechs zielen auf ``x``, zwei auf ``y``, eine auf ``z``. Keine auf
    eine Traegerkomponente, was zu dem passt, was ``w2`` als einzige
    ueberschriebene Traegerkomponente ausweist.
    """
    targets = {
        variable: [
            index
            for index in occurrences(variable)
            if index != VARIABLES.index(variable)
        ][0]
        for variable in (w[9], w[10], w[11], w[13], w[14], w[15])
    }

    assert [targets[w[j]] for j in (9, 10, 11)] == [0, 0, 0]
    assert [targets[w[j]] for j in (13, 14)] == [1, 1]
    assert targets[w[15]] == 2


# --------------------------------------------------------------------------
# Die Schrittfolge
# --------------------------------------------------------------------------

# Rekonstruiert von einem externen Audit dieses Projekts im August 2026 und
# hier unabhaengig nachgerechnet, bevor sie aufgeschrieben wurde. Sie benutzt
# drei Erweiterungen von Proposition (3.1): einen wiederbenutzten Traeger
# (BCW-10), einen Koeffizienten (BCW-11) und einen Schritt, dessen beide
# Plaetze eine frische Variable nennen (BCW-12).
#
# Ein Eintrag ist (Zielkoordinate, Platz, Platz, Koeffizient). Ein Platz ist
# ("fresh", Variable, Wert) oder ("carried", Variable). Positionen gehoeren
# der Kette, Namen nicht -- deshalb steht hier keine einzige Zahl als Index.
FRESH, CARRIED = "fresh", "carried"

STEPS = (
    (x, (FRESH, w1, y**2 * z), (FRESH, w2, x**3 * y), 1),
    (y, (CARRIED, w2), (FRESH, w4, y * z), 3),
    (x, (CARRIED, w4), (FRESH, w5, x**2 * y), 3),
    (y, (CARRIED, w5), (FRESH, w8, x * w4), -3),
    (y, (CARRIED, w5), (FRESH, w7, y**2), 9),
    (x, (CARRIED, w8), (FRESH, w9, x * y), -3),
    (x, (CARRIED, w7), (CARRIED, w9), 7),
    (y, (CARRIED, w4), (FRESH, w13, x**2), 6),
    (w2, (CARRIED, w9), (CARRIED, w13), 1),
    (z, (CARRIED, w13), (FRESH, w16, x * z), -1),
    (y, (CARRIED, w13), (FRESH, w15, y * w8), 3),
    (y, (CARRIED, w13), (FRESH, w14, y * w7), -9),
    (x, (CARRIED, w5), (FRESH, w6, x * w1), -1),
    (x, (CARRIED, w9), (FRESH, w12, x * w6), 1),
    (x, (FRESH, w3, x * y**2), (FRESH, w3, x * y**2), 3),
    (x, (CARRIED, w9), (FRESH, w11, y * w3), -6),
    (x, (CARRIED, w7), (FRESH, w10, z * w2), -1),
)


def alpoege_in_published_coordinates() -> PolynomialMap:
    """Return the source of the chain: Alpoege's map, renamed.

    Not the linear normalization. The published map's linear part is Alpoege's
    own, so the chain starts at the unnormalized map -- and over ``ZZ``, since
    every coefficient in it is an integer and a Keller map over a ring is not
    the same object as the one over its field of fractions.
    """
    source = examples.alpoege()
    rename = dict(zip(source.variables, VARIABLES[:3], strict=True))

    return PolynomialMap(
        VARIABLES[:3],
        tuple(sp.expand(component.subs(rename)) for component in source.components),
    )


def build(steps: tuple = STEPS) -> Reduction:
    """Return the chain, built step by step with ``BCWStep``.

    The filtration level is derived and not chosen: ``H`` displaces the fresh
    coordinates by the factors, so its degree is one below the smallest order
    among them, and BCW-6 caps the declared level at one.
    """
    current, built = alpoege_in_published_coordinates(), []

    for target, left, right, coefficient in steps:
        slots, orders = [], []
        for slot in (left, right):
            if slot[0] == CARRIED:
                slots.append(Carried(current.variables.index(slot[1])))
                continue
            slots.append(Fresh(slot[2], slot[1]))
            orders.append(
                min(
                    sum(monomial)
                    for monomial in sp.Poly(
                        sp.expand(slot[2]), *current.variables
                    ).monoms()
                )
            )

        step = BCWStep.build(
            current,
            current.variables.index(target),
            slots[0],
            slots[1],
            1 if all(order >= 2 for order in orders) else 0,
            coefficient,
        )
        built.append(step)
        current = step.target

    return Reduction(tuple(built))


@pytest.mark.slow
def test_the_chain_is_a_verified_reduction() -> None:
    """Das Ziel von Meilenstein 0.4, als Zertifikat und nicht als Nachrechnung.

    Siebzehn Schritte, jeder gegen BCW-1 bis BCW-12 geprueft, und am Ende die
    veroeffentlichte Abbildung selbst. Die Kette ist ``CONSTRUCTED``, also ist
    ihre eigene Pruefung nach BCW-9 kein Beleg -- der Beleg ist der Endpunkt,
    verglichen mit Daten, die dieses Projekt nicht gerechnet hat.
    """
    chain = build()

    assert chain.verify() is None
    assert len(chain.steps) == 17
    assert chain.source == alpoege_in_published_coordinates()
    assert chain.target.reordered(VARIABLES) == ALPOEGE19


@pytest.mark.slow
def test_the_chain_runs_as_recorded() -> None:
    """Dimensionen und Grade, und was sie ueber die Gestalt sagen.

    Die Doppelungen in der Dimensionsfolge sind die beiden Schritte, die keinen
    Generator einfuehren; der einzige Sprung um zwei ist der erste, der es muss,
    weil Alpoeges Abbildung keine Traeger hat.
    """
    chain = build()

    assert chain.dimensions() == (
        3,
        5,
        6,
        7,
        8,
        9,
        10,
        10,
        11,
        11,
        12,
        13,
        14,
        15,
        16,
        17,
        18,
        19,
    )
    assert chain.degrees() == (
        7,
        6,
        6,
        6,
        6,
        6,
        6,
        6,
        6,
        6,
        6,
        6,
        6,
        6,
        6,
        4,
        4,
        3,
    )
    assert sum(step.m for step in chain.steps) == 16
    assert [step.m for step in chain.steps].count(2) == 1
    assert [step.m for step in chain.steps].count(0) == 2


@pytest.mark.slow
def test_the_chain_carries_the_collision_to_the_published_points() -> None:
    """Der zweite aeussere Beleg, und er ist von der Abbildung unabhaengig.

    Alpoeges drei Punkte, durch siebzehn Schritte transportiert, ergeben die
    siebenundfuenfzig Koordinaten der veroeffentlichten Tabelle.
    """
    chain = build()
    carried = chain.transport(
        Collision.at(alpoege_in_published_coordinates(), ALPOEGE_POINTS)
    )
    place = {variable: index for index, variable in enumerate(chain.target.variables)}

    reordered = tuple(
        tuple(sp.nsimplify(point[place[variable]]) for variable in VARIABLES)
        for point in carried.points
    )

    assert reordered == tuple(
        tuple(sp.nsimplify(value) for value in point) for point in PUBLISHED_POINTS
    )
    assert carried.verify(chain.target) is None


@pytest.mark.slow
def test_a_wrong_coefficient_does_not_reach_the_published_map() -> None:
    """Negativkontrolle: die Koeffizienten sind nicht Zierrat.

    Ein einziger von ihnen geaendert, und die Kette baut sich weiterhin und
    verifiziert weiterhin -- sie kommt nur woanders an. Genau deshalb ist der
    Endpunkt der Beleg und nicht ``verify()``.
    """
    target, left, right, coefficient = STEPS[6]
    perturbed = (*STEPS[:6], (target, left, right, coefficient + 1), *STEPS[7:])

    chain = build(perturbed)

    assert chain.verify() is None
    assert chain.target.reordered(VARIABLES) != ALPOEGE19


@pytest.mark.slow
def test_the_peel_finds_a_chain_to_this_map() -> None:
    """Die Suche erreicht die veroeffentlichte Abbildung, ohne Hilfe.

    Achtzehn gepruefte Karten. Sie bekommt Quelle und Ziel und sonst nichts:
    keinen Wertevorrat, keine Namen, keine Vorzeichenkonvention (REV-1). Was
    sie einschraenkt, ist aus dem Ziel abgelesen oder folgt aus der Arithmetik;
    ``spare`` und ``pairs`` stehen auf den Werten, die sich daraus ergeben.

    Bis 0.4.0rc1 fand sie nichts, und der Grund war kein mathematischer: der
    Treiber baute die Quelle mit ``over_field`` ueber ``QQ``, das Ziel liegt
    ueber ``ZZ``, und ``PolynomialMap`` zaehlt den Koeffizientenbereich zu
    seiner Identitaet. Ein externes Audit hat es gefunden. Dieser Test haelt
    fest, dass der Bereich uebereinstimmt und die Suche ankommt.
    """
    source = alpoege_in_published_coordinates()

    assert source.ring.domain == ALPOEGE19.ring.domain

    outcome = peel(source, ALPOEGE19, budget=200, spare=2, pairs=1)

    assert outcome.reduction is not None
    assert outcome.reduction.verify() is None
    assert len(outcome.reduction.steps) == 17
    assert outcome.reduction.target.reordered(VARIABLES) == ALPOEGE19


@pytest.mark.slow
def test_the_chain_the_peel_finds_is_not_the_recorded_one() -> None:
    """Eine Kette, nicht die Kette.

    Beide haben siebzehn Schritte und dieselbe Struktur -- einer fuehrt zwei
    Koordinaten ein, zwei fuehren keine ein -- und sie fuehren die Koordinaten
    in verschiedener Reihenfolge ein. Ein Test, der die gefundene festschreibt,
    stuende der eigenen Verpflichtung im Weg; dieser haelt fest, dass es mehr
    als eine gibt.
    """
    found = peel(
        alpoege_in_published_coordinates(), ALPOEGE19, budget=200, spare=2, pairs=1
    ).reduction
    recorded = build()

    assert found is not None
    assert len(found.steps) == len(recorded.steps)
    assert found.target.variables != recorded.target.variables
    assert found.target.reordered(VARIABLES) == recorded.target.reordered(VARIABLES)
