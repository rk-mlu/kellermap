"""Kubische Keller-Abbildung in Dimension 17, abgeleitet aus Alpoeges.

Diese Abbildung hat Grad 3 und konstante Jacobi-Determinante 1, und sie erbt
die Kollision der Alpoege-Abbildung. Sie ist damit selbst ein Gegenbeispiel
zur Jacobi-Vermutung, nicht bloss eine Keller-Abbildung. All das rechnen die
Tests unten selbst nach.

Bis Version 0.2 war sie ein Regressionskandidat: dass sie *durch eine
BCW-Reduktion* aus der Alpoege-Abbildung hervorgeht, war behauptet und nicht
gezeigt. Der Abschnitt "Ableitung" unten zeigt es jetzt -- eine ``Reduction``
aus acht Schritten, Schritt fuer Schritt verifiziert, die die Kollision
mittraegt.

Was daran Beleg ist und was nicht
---------------------------------
Die Zwischenabbildungen in den Dimensionen 5 bis 15 sind nirgends
veroeffentlicht. Sie *koennen* darum nicht vorgelegt werden, und ihre Schritte
sind ``CONSTRUCTED``: BCW-1 vergleicht dort die Implementierung mit sich
selbst. Die ganze Kette traegt deshalb nach RED-7 die schwaechere Provenienz.

Die aeussere Tatsache ist der Endpunkt, und dort beisst die Pruefung: der
letzte Schritt bekommt die fixierten Komponenten als Ziel vorgelegt, also
vergleicht sein BCW-1 eine extern gerechnete Abbildung mit
``G o F^[2] o H``. Ebenso die Kollision, die am Ende der Kette gegen
``BCW17_COLLISION`` gehalten wird, und die Variablennamen, die der
``ReductionContext`` erzeugt und nicht die Tabelle vorgibt -- benennt er
anders als x4 ... x17, faellt der letzte Schritt.

Die Faktorisierung selbst ist nicht gesucht, sondern aus den fixierten
Komponenten abgelesen: die Komponenten 4 bis 17 haben die Form ``X_j + P``,
und diese ``P`` sind die Faktoren. Sie zu finden ist Sache von 0.3. Eine von
dieser Bibliothek unabhaengige Nachrechnung derselben Kette in reinem SymPy
steht in ``scripts/reconstruct_bcw17.py``.
"""

import math

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
from kellermap.bcw import BCWStep, Fresh
from kellermap.reduction import LinearStep

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


def test_reordering_the_generators_changes_no_value(bcw17: PolynomialMap) -> None:
    """SEA-4 an der zweiten festen Abbildung, in Dimension 17.

    Dieselbe Kontrolle wie fuer ALPOEGE15, an anderen Daten: das Umsortieren
    ist eine Umschreibung der Darstellung, und der Rueckweg liefert das
    Original.
    """
    shuffled = X[8:] + X[:8]

    moved = bcw17.reordered(shuffled)

    assert moved.variables == shuffled
    assert moved != bcw17
    assert moved.reordered(X) == bcw17
    assert moved.determinant() == bcw17.determinant()
    assert moved.degree() == bcw17.degree()
    assert moved.filtration_degree() == bcw17.filtration_degree()


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
# die beiden Faktoren, und die EA-Stufe, die H erreicht. Die frischen
# Variablen stehen hier bewusst nicht -- die vergibt der ReductionContext, und
# dass er dabei x4 ... x17 in dieser Reihenfolge trifft, ist Teil dessen, was
# der letzte Schritt prueft.
STEPS = (
    (0, -_1 * _3 / 2, _1**2, 1),
    (1, 3 * _1**2 * _2, _1 * _2 * _3 + 3 * _2**2, 1),
    (1, _1 * _2, 6 * _1 * _3 - 3 * _1 * _7 - _3 * _6, 1),
    (2, _1 * _2**2, _1**2 * _2 * _3 + 3 * _1 * _2**2 + 3 * _1 * _3 + 7 * _2, 0),
    (2, _1 * _2 * _10, -_1 * _3 - 3 * _2, 0),
    (2, _1 * _2, -_10 * _13 - _2 * _11, 1),
    (10, _2 * _3, _1**2, 1),
)


@pytest.fixture(scope="module")
def alpoege() -> PolynomialMap:
    """Ueber QQ, weil die Normalisierung sofort einen Kehrwert braucht."""
    return over_field(PolynomialMap(ALPOEGE_VARIABLES, ALPOEGE_COMPONENTS))


@pytest.fixture(scope="module")
def normalization(alpoege: PolynomialMap) -> LinearStep:
    """F'' = F'_(1)^-1 o F', die lineare Normalisierung aus BCW Paragraph 4."""
    return LinearStep.normalize(alpoege)


@pytest.fixture(scope="module")
def reduction(
    alpoege: PolynomialMap, normalization: LinearStep, bcw17: PolynomialMap
) -> Reduction:
    """Die vollstaendige Kette, mit vorgelegtem Ziel im letzten Schritt."""
    context = ReductionContext()
    steps: list[LinearStep | BCWStep] = [normalization]
    current = normalization.target

    for position, (index, P, Q, level) in enumerate(STEPS):
        fresh = context.variables(current.ring, 2)
        last = position == len(STEPS) - 1
        slots = (Fresh(P, fresh[0]), Fresh(Q, fresh[1]))
        step = (
            BCWStep(current, bcw17, index, *slots, level)
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


def test_the_reduction_reaches_bcw17(
    reduction: Reduction, bcw17: PolynomialMap
) -> None:
    """Der Endpunkt ist die fixierte Abbildung, nicht nur eine wie sie."""
    assert reduction.target == bcw17


def test_the_last_step_is_the_one_that_can_fail(reduction: Reduction) -> None:
    """Nur dort steht eine extern gerechnete Abbildung auf einer Seite.

    Die Zwischenabbildungen sind nirgends veroeffentlicht, koennen also nicht
    vorgelegt werden; ihre Schritte pruefen die Implementierung gegen sich
    selbst.
    """
    assert reduction[-1].provenance is Provenance.SUPPLIED
    assert reduction.provenance is Provenance.CONSTRUCTED


def test_a_perturbed_target_would_be_caught(
    reduction: Reduction, bcw17: PolynomialMap
) -> None:
    """Gegenprobe: die Pruefung im letzten Schritt beisst wirklich.

    Ein Vorzeichen in der ersten Komponente daneben, und BCW-1 faellt. Ohne
    diesen Test waere nicht zu sehen, ob der letzte Schritt etwas prueft oder
    nur zufaellig durchgeht.
    """
    last = reduction[-1]
    perturbed = PolynomialMap(
        X, (bcw17.components[0] + _4 * _5,) + bcw17.components[1:]
    )
    broken = BCWStep(
        last.source,
        perturbed,
        last.index,
        Fresh(last.P, last.variables[0]),
        Fresh(last.Q, last.variables[1]),
    )

    with pytest.raises(VerificationError) as failure:
        Reduction(list(reduction[:-1]) + [broken]).verify()

    assert failure.value.obligation == "BCW-1"
    assert failure.value.step == 7


def test_the_dimensions_and_degrees(reduction: Reduction) -> None:
    """3 auf 17 in sieben Schritten zu je zwei, Grad 7 auf 3."""
    assert reduction.dimensions() == (3, 3, 5, 7, 9, 11, 13, 15, 17)
    assert reduction.degrees() == (7, 7, 7, 7, 7, 5, 4, 4, 3)


def test_the_context_names_x4_to_x17(reduction: Reduction) -> None:
    """Die Namen kommen aus dem Kontext, nicht aus der Tabelle."""
    allocated = tuple(
        variable
        for step in reduction
        if isinstance(step, BCWStep)
        for variable in step.variables
    )

    assert allocated == X[3:]


def test_the_collision_is_transported(
    reduction: Reduction, alpoege: PolynomialMap
) -> None:
    """Der eigentliche Zweck: aus drei Punkten in k^3 werden drei in k^17."""
    carried = reduction.transport(Collision.at(alpoege, ALPOEGE_COLLISION))

    assert carried == Collision(
        tuple(tuple(map(sp.nsimplify, point)) for point in BCW17_COLLISION),
        tuple(BCW17_IMAGE),
    )


def test_the_determinant_is_settled_by_the_linear_step(
    reduction: Reduction, alpoege: PolynomialMap
) -> None:
    """Nach LIN-3 die einzige Stelle, an der sie sich aendern darf."""
    assert alpoege.determinant() == -2
    assert reduction[0].transformation.determinant() == R(-1, 2)
    assert all(
        step.target.determinant() == 1
        for step in reduction
        if isinstance(step, BCWStep)
    )


def test_the_filtration_explains_MA0(reduction: Reduction) -> None:  # noqa: N802
    """Warum BCW17 in MA^0 liegt und nicht in MA^1.

    Genau zwei der sieben Schritte erreichen nur EA^0, weil ihr Q einen
    Linearterm traegt: 7*x2 und -3*x2. Das sind genau die beiden Linearterme,
    die in den Komponenten 11 und 13 stehen.
    """
    levels = [step.filtration_level for step in reduction if isinstance(step, BCWStep)]

    assert levels == [1, 1, 1, 0, 0, 1, 1]
    assert reduction.filtration_level() == 0
    assert reduction[0].filtration_level == math.inf


def test_the_two_EA0_steps_are_the_linear_terms(  # noqa: N802
    reduction: Reduction, bcw17: PolynomialMap
) -> None:
    """Die Verbindung zwischen Zertifikat und fixierter Abbildung."""
    modest = [
        step
        for step in reduction
        if isinstance(step, BCWStep) and step.filtration_level == 0
    ]

    assert [step.variables for step in modest] == [(_10, _11), (_12, _13)]
    assert 7 * _2 in bcw17.components[10].args
    assert -3 * _2 in bcw17.components[12].args


# --------------------------------------------------------------------------
# Der lineare Schritt einzeln
# --------------------------------------------------------------------------


def test_normalization_explains_the_determinant(
    alpoege: PolynomialMap, normalization: LinearStep
) -> None:
    """Warum BCW17 Determinante 1 hat, Alpoege aber -2.

    Der Linearteil von Alpoege hat selbst Determinante -2. Die Normalisierung
    teilt sie damit heraus; Stabilisierung und elementare Faktoren koennen die
    Determinante danach nicht mehr aendern.
    """
    assert alpoege.determinant() == -2
    assert normalization.target.determinant() == 1


def test_normalization_reaches_MA1(  # noqa: N802
    alpoege: PolynomialMap, normalization: LinearStep
) -> None:
    """Die Voraussetzung von Proposition (3.1).

    Alpoege liegt nur in MA^0; erst nach der Normalisierung ist der Linearteil
    die Identitaet und die Abbildung liegt in MA^1.
    """
    assert not alpoege.is_in_MA(1)
    assert normalization.target.is_in_MA(1)


def test_normalization_is_a_transposition_and_a_dilation(
    normalization: LinearStep,
) -> None:
    """Und damit nicht elementar: EA_n(k) hat nur Determinante 1."""
    assert len(normalization.transformation) == 2
    assert not normalization.transformation.is_elementary


def test_normalization_explains_the_image(
    alpoege: PolynomialMap, normalization: LinearStep
) -> None:
    """Warum das Kollisionsbild (0, 0, -1/4) lautet und nicht (-1/4, 0, 0).

    Der Linearteil vertauscht die erste und dritte Koordinate, seine Inverse
    also ebenso. Linkskomposition laesst dabei jedes Urbild, wo es war.
    """
    moved = normalization.transport(Collision.at(alpoege, ALPOEGE_COLLISION))

    assert moved.points == Collision.at(alpoege, ALPOEGE_COLLISION).points
    assert moved.image == tuple(BCW17_IMAGE)[:3]


def test_the_collision_extends_alpoeges(bcw17: PolynomialMap) -> None:
    """Die Kollisionspunkte setzen Alpoeges Punkte fort.

    Der Zusammenhang zwischen beiden Abbildungen ist damit nicht nur
    behauptet: dieselben drei Urbilder, um 14 Stabilisierungskoordinaten
    ergaenzt.
    """
    heads = {tuple(map(sp.nsimplify, p))[:3] for p in BCW17_COLLISION}
    alpoege_points = {tuple(map(sp.nsimplify, point)) for point in ALPOEGE_COLLISION}

    assert heads == alpoege_points
    assert bcw17.dimension - 3 == 14
