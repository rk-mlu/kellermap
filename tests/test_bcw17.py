"""Regression: eine BCW-Reduktion der Alpoege-Abbildung auf Dimension 17.

Diese Abbildung hat Grad 3 und konstante Jacobi-Determinante 1, und sie erbt
die Kollision der Alpoege-Abbildung. Sie ist damit selbst ein Gegenbeispiel
zur Jacobi-Vermutung, nicht bloss eine Keller-Abbildung.

Herkunft
--------
Die Komponenten sind fixiert und nicht von dieser Bibliothek erzeugt. Sie sind
das Ziel, das ein spaeterer ``BCWStep`` reproduzieren muss; bis dahin ist diese
Datei eine Regression gegen ein extern gerechnetes Ergebnis.

Der Weg von Alpoege (Dimension 3, Grad 7, det = -2) hierher besteht aus zwei
Teilen. Der erste ist die lineare Normalisierung aus BCW Paragraph 4,
F'' = F'_(1)^-1 o F'. Sie ist unten in ``test_normalization_...`` vollstaendig
nachgerechnet und erklaert genau die Unterschiede, die zwischen beiden
Abbildungen ins Auge fallen: die Determinante -2 wird 1, weil der Linearteil
von Alpoege ebenfalls Determinante -2 hat, und das Kollisionsbild
(-1/4, 0, 0) wird (0, 0, -1/4), weil dieser Linearteil die erste und dritte
Koordinate vertauscht.

Der zweite Teil -- Stabilisierung auf Dimension 17 und die elementaren
Faktoren aus Proposition (3.1), die den Grad von 7 auf 3 druecken -- ist hier
nicht nachgerechnet. Er ist der Inhalt von ``BCWStep`` in Version 0.2. Was
davon heute schon geprueft ist: die Kollisionspunkte setzen in ihren ersten
drei Koordinaten Alpoeges Punkte fort, und das Bild stimmt mit dem der
normalisierten Abbildung ueberein.
"""

import pytest
import sympy as sp

from kellermap import PolynomialMap

X = sp.symbols("x1:18")
_1, _2, _3, _4, _5, _6, _7, _8, _9, _10, _11, _12, _13, _14, _15, _16, _17 = X

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
    - _1 * _15 * _2
    + 3 * _1 * _2 * _3
    - _10 * _11
    + _10 * _13 * _14
    - 7 * _10 * _2
    + _11 * _14 * _2
    - _12 * _13
    + 3 * _12 * _2
    - _14 * _15
    + 4 * _2**2
    + _3,
    -_1 * _3 / 2 + _4,
    _1**2 + _5,
    3 * _1**2 * _2 + _6,
    _1 * _2 * _3 + 3 * _2**2 + _7,
    _1 * _2 + _8,
    6 * _1 * _3 - 3 * _1 * _7 - _3 * _6 + _9,
    _1 * _2**2 + _10,
    -(_1**2) * _16
    + 3 * _1 * _2**2
    + 3 * _1 * _3
    + _11
    - _16 * _17
    - _17 * _2 * _3
    + 7 * _2,
    _1 * _10 * _2 + _12,
    -_1 * _3 + _13 - 3 * _2,
    _1 * _2 + _14,
    -_10 * _13 - _11 * _2 + _15,
    _16 + _2 * _3,
    _1**2 + _17,
)

R = sp.Rational

# Die drei Urbilder entstehen aus Alpoeges rationaler Kollision, indem die
# Stabilisierungsvariablen x4..x17 topologisch nachgezogen werden.
BCW17_COLLISION = (
    (0, 0, R(-1, 4), 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
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
        R(3, 2),
        R(9, 2),
        R(39, 4),
        -1,
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
        R(3, 2),
        R(9, 2),
        R(-39, 4),
        -1,
    ),
)

BCW17_IMAGE = sp.Matrix([0, 0, R(-1, 4)] + [0] * 14)


# Die 14 Stabilisierungskoordinaten x4..x17 aus BCW Proposition (3.1). Ihr
# Jacobi-Block ist unipotent, worauf die Determinantenstrategie aufsetzt.
CARRIER_INDICES = tuple(range(3, 17))


@pytest.fixture(scope="module")
def bcw17() -> PolynomialMap:
    """``PolynomialMap`` ist unveraenderlich, also genuegt Modul-Scope.

    Der Aufbau des Rings kostet in Dimension 17 spuerbar Zeit; sie faellt so
    einmal statt einmal pro Test an.
    """
    return PolynomialMap(variables=X, components=COMPONENTS)


def test_bcw17_is_not_injective(bcw17: PolynomialMap) -> None:
    """Der eigentliche Inhalt: drei verschiedene Urbilder desselben Punktes."""
    points = tuple(tuple(map(sp.nsimplify, p)) for p in BCW17_COLLISION)

    assert len(set(points)) == 3

    images = [sp.expand(bcw17(*point)) for point in points]

    assert all(image == BCW17_IMAGE for image in images)


def test_bcw17_has_degree_three(bcw17: PolynomialMap) -> None:
    """Das Reduktionsziel von BCW Proposition (3.1)."""
    assert bcw17.dimension == 17
    assert bcw17.degree() == 3


def test_bcw17_lies_in_MA0_but_not_MA1(bcw17: PolynomialMap) -> None:
    """F = X + H mit ord(H) = 1: der Linearteil ist noch nicht normalisiert.

    Die Komponenten 11 und 13 tragen die Linearterme 7*x2 und -3*x2, also
    liegt F in MA^0, nicht in MA^1. Das ist genau der Zustand vor dem ersten
    Schritt von BCW Paragraph 4, der F durch F'' = F'_(1)^-1 o F' ersetzt.
    """
    assert bcw17.displacement().order() == 1
    assert bcw17.is_in_MA(0)
    assert not bcw17.is_in_MA(1)


def test_bcw17_linear_part_is_invertible(bcw17: PolynomialMap) -> None:
    """J(F)(0) muss invertierbar sein, sonst ist der Normalisierungsschritt
    von Paragraph 4 nicht ausfuehrbar."""
    linear_part = bcw17.jacobian().xreplace({v: sp.Integer(0) for v in X})

    assert linear_part.det() == 1


# --------------------------------------------------------------------------
# Keller-Eigenschaft
# --------------------------------------------------------------------------


def test_bcw17_determinant_is_one(bcw17: PolynomialMap) -> None:
    """Keller-Eigenschaft, exakt und als Polynomidentitaet.

    Frueher war dieser Test hinter einer Umgebungsvariablen versteckt, weil
    die 17x17-Determinante ueber QQ[x1..x17] rund eine Minute brauchte. Seit
    ``determinant`` den unipotenten Traegerblock ueber das Schur-Komplement
    herausrechnet, bleiben davon Millisekunden.
    """
    assert bcw17.determinant() == 1


def test_bcw17_carrier_block_is_the_stabilization_block(
    bcw17: PolynomialMap,
) -> None:
    """Woher die Beschleunigung kommt.

    Die Stabilisierungskoordinaten sind genau die, die BCW anfuegt: jede hat
    die Form X_k + P mit P in den uebrigen Variablen, und die Abhaengigkeiten
    unter ihnen sind azyklisch. Der Test haelt fest, dass die Erkennung diese
    Struktur findet und nicht bloss zufaellig irgendeinen Block.
    """
    assert bcw17.carrier_indices == CARRIER_INDICES

    head = bcw17.dimension - len(CARRIER_INDICES)

    assert head == 3


def test_bcw17_determinant_is_not_constant_after_a_perturbation() -> None:
    """Gegenprobe: der Test oben besteht nicht deshalb, weil er nichts prueft.

    Ein zusaetzlicher kubischer Term in der ersten Komponente laesst den
    Traegerblock unberuehrt, aendert aber das Schur-Komplement. Waere die
    Strategie falsch, faende sie hier weiterhin 1.
    """
    perturbed = PolynomialMap(
        variables=X,
        components=(COMPONENTS[0] + _2**3,) + COMPONENTS[1:],
    )

    assert perturbed.carrier_indices == CARRIER_INDICES
    assert perturbed.determinant() != 1


@pytest.mark.slow
def test_bcw17_determinant_strategies_agree(bcw17: PolynomialMap) -> None:
    """Kreuzprobe der beiden Determinantenstrategien in voller Groesse.

    ``architecture.md`` verlangt unter "Cross-representation tests", die
    eigene ``DomainMatrix``-Integration gegen ein unabhaengig gerechnetes
    Ergebnis zu halten. Hier laeuft der Vergleich andersherum: der
    ``DomainMatrix``-Pfad ist die Referenz, das Schur-Komplement die
    Optimierung. Der Zugriff auf die private Methode ist Absicht -- die
    oeffentliche API waehlt die Strategie selbst, und genau diese Wahl soll
    hier umgangen werden.

    Als ``slow`` markiert: der Referenzpfad braucht rund eine Minute. Das ist
    der Preis dafuer, die Optimierung nicht bloss gegen sich selbst zu
    pruefen.
    """
    reference = bcw17._determinant_by_domain_matrix(bcw17._jacobian_polynomials)

    assert reference.as_expr() == bcw17.determinant() == 1


# --------------------------------------------------------------------------
# Herkunft: was sich heute schon nachrechnen laesst
# --------------------------------------------------------------------------

ALPOEGE_VARIABLES = sp.symbols("x y z")

ALPOEGE_COMPONENTS = (
    (1 + ALPOEGE_VARIABLES[0] * ALPOEGE_VARIABLES[1]) ** 3 * ALPOEGE_VARIABLES[2]
    + ALPOEGE_VARIABLES[1] ** 2
    * (1 + ALPOEGE_VARIABLES[0] * ALPOEGE_VARIABLES[1])
    * (4 + 3 * ALPOEGE_VARIABLES[0] * ALPOEGE_VARIABLES[1]),
    ALPOEGE_VARIABLES[1]
    + 3
    * ALPOEGE_VARIABLES[0]
    * (1 + ALPOEGE_VARIABLES[0] * ALPOEGE_VARIABLES[1]) ** 2
    * ALPOEGE_VARIABLES[2]
    + 3
    * ALPOEGE_VARIABLES[0]
    * ALPOEGE_VARIABLES[1] ** 2
    * (4 + 3 * ALPOEGE_VARIABLES[0] * ALPOEGE_VARIABLES[1]),
    2 * ALPOEGE_VARIABLES[0]
    - 3 * ALPOEGE_VARIABLES[0] ** 2 * ALPOEGE_VARIABLES[1]
    - ALPOEGE_VARIABLES[0] ** 3 * ALPOEGE_VARIABLES[2],
)


@pytest.fixture(scope="module")
def normalized_alpoege() -> PolynomialMap:
    """F'' = F'_(1)^-1 o F', die lineare Normalisierung aus BCW Paragraph 4."""
    F = PolynomialMap(ALPOEGE_VARIABLES, ALPOEGE_COMPONENTS)
    linear_part = sp.Matrix(
        F.jacobian().xreplace({v: sp.Integer(0) for v in ALPOEGE_VARIABLES})
    )

    return PolynomialMap(
        ALPOEGE_VARIABLES,
        tuple(sp.expand(e) for e in linear_part.inv() * sp.Matrix(F.components)),
    )


def test_normalization_explains_the_determinant(
    normalized_alpoege: PolynomialMap,
) -> None:
    """Warum BCW17 Determinante 1 hat, Alpoege aber -2.

    Der Linearteil von Alpoege hat selbst Determinante -2. Die Normalisierung
    teilt sie damit heraus; Stabilisierung und elementare Faktoren koennen die
    Determinante danach nicht mehr aendern.
    """
    F = PolynomialMap(ALPOEGE_VARIABLES, ALPOEGE_COMPONENTS)

    assert F.determinant() == -2
    assert normalized_alpoege.determinant() == 1


def test_normalization_reaches_MA1(  # noqa: N802
    normalized_alpoege: PolynomialMap,
) -> None:
    """Die Voraussetzung von Proposition (3.1).

    Alpoege liegt nur in MA^0; erst nach der Normalisierung ist der Linearteil
    die Identitaet und die Abbildung liegt in MA^1.
    """
    assert not PolynomialMap(ALPOEGE_VARIABLES, ALPOEGE_COMPONENTS).is_in_MA(1)
    assert normalized_alpoege.is_in_MA(1)


def test_normalization_explains_the_image(
    normalized_alpoege: PolynomialMap,
) -> None:
    """Warum das Kollisionsbild (0, 0, -1/4) lautet und nicht (-1/4, 0, 0).

    Der Linearteil vertauscht die erste und dritte Koordinate, seine Inverse
    also ebenso. Das Bild der normalisierten Abbildung stimmt genau mit den
    ersten drei Koordinaten des BCW17-Bildes ueberein.
    """
    heads = [tuple(map(sp.nsimplify, p))[:3] for p in BCW17_COLLISION]
    images = [sp.expand(normalized_alpoege(*head)) for head in heads]

    assert len({tuple(image) for image in images}) == 1
    assert list(images[0]) == list(BCW17_IMAGE)[:3]


def test_the_collision_extends_alpoeges(bcw17: PolynomialMap) -> None:
    """Die Kollisionspunkte setzen Alpoeges Punkte fort.

    Der Zusammenhang zwischen beiden Abbildungen ist damit nicht nur
    behauptet: dieselben drei Urbilder, um 14 Stabilisierungskoordinaten
    ergaenzt.
    """
    alpoege_collision = {
        (sp.Integer(0), sp.Integer(0), sp.Rational(-1, 4)),
        (sp.Integer(1), sp.Rational(-3, 2), sp.Rational(13, 2)),
        (sp.Integer(-1), sp.Rational(3, 2), sp.Rational(13, 2)),
    }
    heads = {tuple(map(sp.nsimplify, p))[:3] for p in BCW17_COLLISION}

    assert heads == alpoege_collision
    assert bcw17.dimension - 3 == 14
