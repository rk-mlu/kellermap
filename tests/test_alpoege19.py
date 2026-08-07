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

import sympy as sp

from kellermap import Collision, PolynomialMap

x, y, z = sp.symbols("x y z")
w = sp.symbols("w1:17")
w1, w2, w3, w4, w5, w6, w7, w8, w9, w10, w11, w12, w13, w14, w15, w16 = w

VARIABLES = (x, y, z) + w

COMPONENTS = (
    x * w1 * w5
    + 3 * x * w4 * w9
    - x * w6 * w9
    + 6 * x * y * w11
    - x * y * w12
    - 7 * x * y * w7
    + 3 * x * y * w8
    + 3 * x * y * z
    + 6 * y * w3 * w9
    - 3 * y * z * w5
    + y**2 * w10
    - 7 * y**2 * w9
    + z * w2 * w7
    - w1 * w2
    - 3 * w3**2
    - 3 * w4 * w5
    + w5 * w6
    + w7 * w10
    - 7 * w7 * w9
    + 3 * w8 * w9
    + 6 * w9 * w11
    - w9 * w12
    + 4 * y**2
    + z,
    3 * x * w4 * w5
    + 12 * x * y**2
    + 9 * x**2 * w14
    - 3 * x**2 * w15
    - 6 * x**2 * w4
    + 9 * y * w7 * w13
    - 3 * y * w8 * w13
    - 6 * y * z * w13
    - 3 * y * z * w2
    - 9 * y**2 * w5
    + 9 * w13 * w14
    - 3 * w13 * w15
    - 3 * w2 * w4
    - 6 * w4 * w13
    - 9 * w5 * w7
    + 3 * w5 * w8
    + 3 * x * z
    + y,
    x * z * w13 + x**2 * w16 - 3 * x**2 * y + w13 * w16 + 2 * x,
    y**2 * z + w1,
    -x * y * w13 - x**2 * w9 - w9 * w13 + w2,
    x * y**2 + w3,
    y * z + w4,
    x**2 * y + w5,
    x * w1 + w6,
    y**2 + w7,
    x * w4 + w8,
    x * y + w9,
    z * w2 + w10,
    y * w3 + w11,
    x * w6 + w12,
    x**2 + w13,
    y * w7 + w14,
    y * w8 + w15,
    x * z + w16,
)

ALPOEGE19 = PolynomialMap(VARIABLES, COMPONENTS)

# Die drei Punkte aus der Quelle, zum Vergleich mit der Rekonstruktion.
R = sp.Rational
PUBLISHED_POINTS = (
    (0, 0, R(-1, 4)) + (0,) * 16,
    (
        1,
        R(-3, 2),
        R(13, 2),
        R(-117, 8),
        R(3, 2),
        R(-9, 4),
        R(39, 4),
        R(3, 2),
        R(117, 8),
        R(-9, 4),
        R(-39, 4),
        R(3, 2),
        R(-39, 4),
        R(-27, 8),
        R(-117, 8),
        -1,
        R(-27, 8),
        R(-117, 8),
        R(-13, 2),
    ),
    (
        -1,
        R(3, 2),
        R(13, 2),
        R(-117, 8),
        R(3, 2),
        R(9, 4),
        R(-39, 4),
        R(-3, 2),
        R(-117, 8),
        R(-9, 4),
        R(-39, 4),
        R(3, 2),
        R(-39, 4),
        R(-27, 8),
        R(-117, 8),
        -1,
        R(27, 8),
        R(117, 8),
        R(13, 2),
    ),
)

ALPOEGE_POINTS = (
    (0, 0, R(-1, 4)),
    (1, R(-3, 2), R(13, 2)),
    (-1, R(3, 2), R(13, 2)),
)

ALPOEGE_IMAGE = (R(-1, 4), 0, 0)

# Die Traegerkomponenten haben die Form w_j + P_j.
CARRIERS = {w[j]: sp.expand(COMPONENTS[3 + j] - w[j]) for j in range(16)}


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
W2_INTRODUCED = x**3 * y


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
