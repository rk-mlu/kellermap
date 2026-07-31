"""Regression: eine BCW-Reduktion der Alpoege-Abbildung auf Dimension 17.

Diese Abbildung hat Grad 3 und konstante Jacobi-Determinante 1, und sie erbt
die Kollision der Alpoege-Abbildung. Sie ist damit selbst ein Gegenbeispiel
zur Jacobi-Vermutung, nicht bloss eine Keller-Abbildung.

Die Komponenten sind hier fixiert und nicht von dieser Bibliothek erzeugt: sie
sind das Ziel, das ein spaeterer ``BCWStep`` reproduzieren muss. Bis dahin ist
diese Datei eine Regression gegen ein extern gerechnetes Ergebnis.
"""

import random

import pytest
import sympy as sp

from bcw import PolynomialMap

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


# --------------------------------------------------------------------------
# Parameter der probabilistischen Determinantenpruefung
# --------------------------------------------------------------------------

# deg(det J) <= n * (deg F - 1) = 17 * 2. Nach Schwartz-Zippel verschwindet ein
# von Null verschiedenes Polynom dieses Grades auf einem gleichverteilt
# gezogenen Punkt aus S^n mit Wahrscheinlichkeit hoechstens 34 / |S|.
DETERMINANT_DEGREE_BOUND = 17 * (3 - 1)

# |S| = 2 * 10**6 + 1, also Irrtumswahrscheinlichkeit < 2e-5 je Punkt und
# < 1e-28 fuer alle Punkte zusammen.
SAMPLE_BOUND = 10**6
SAMPLE_COUNT = 6

# Fester Seed: die Stichprobe ist damit Teil der Regression und nicht Quelle
# sporadisch roter Laeufe.
SAMPLE_SEED = 20260720


@pytest.fixture(scope="module")
def bcw17() -> PolynomialMap:
    """``PolynomialMap`` ist unveraenderlich, also genuegt Modul-Scope.

    Der Aufbau des Rings kostet in Dimension 17 spuerbar Zeit; sie faellt so
    einmal statt einmal pro Test an.
    """
    return PolynomialMap(variables=X, components=COMPONENTS)


@pytest.fixture(scope="module")
def sample_points() -> tuple[dict[sp.Symbol, sp.Integer], ...]:
    """Ganzzahlige Auswertungspunkte fuer die Determinantenpruefung."""
    generator = random.Random(SAMPLE_SEED)

    return tuple(
        {
            variable: sp.Integer(generator.randint(-SAMPLE_BOUND, SAMPLE_BOUND))
            for variable in X
        }
        for _ in range(SAMPLE_COUNT)
    )


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


def test_bcw17_determinant_is_one_on_a_random_sample(
    bcw17: PolynomialMap,
    sample_points: tuple[dict[sp.Symbol, sp.Integer], ...],
) -> None:
    """Keller-Eigenschaft, in Sekundenbruchteilen statt in einer Minute.

    Statt det J als Polynom in 17 Variablen aufzustellen, wird die
    Jacobi-Matrix an ganzzahligen Punkten ausgewertet und dort exakt ueber
    Z determiniert. Waere det J - 1 nicht das Nullpolynom, muesste es nach
    Schwartz-Zippel auf jedem der Punkte zufaellig verschwinden; die
    Wahrscheinlichkeit dafuer liegt unter 1e-28.

    Der exakte Nachweis steht darunter und ist als ``slow`` markiert.
    """
    assert bcw17.dimension * (bcw17.degree() - 1) == DETERMINANT_DEGREE_BOUND

    determinants = [
        bcw17.jacobian().xreplace(point).det(method="berkowitz")
        for point in sample_points
    ]

    assert determinants == [sp.Integer(1)] * SAMPLE_COUNT


def test_sample_detects_a_perturbed_determinant(
    sample_points: tuple[dict[sp.Symbol, sp.Integer], ...],
) -> None:
    """Gegenprobe: der Test oben besteht nicht deshalb, weil er nichts prueft.

    Ein zusaetzlicher kubischer Term in der ersten Komponente macht det J
    nicht-konstant. Die Stichprobe muss das bemerken.
    """
    perturbed = PolynomialMap(
        variables=X,
        components=(COMPONENTS[0] + _2**3,) + COMPONENTS[1:],
    )

    determinants = [
        perturbed.jacobian().xreplace(point).det(method="berkowitz")
        for point in sample_points
    ]

    assert any(determinant != 1 for determinant in determinants)


@pytest.mark.slow
def test_bcw17_determinant_is_one_exactly(bcw17: PolynomialMap) -> None:
    """Derselbe Nachweis ohne Stichprobe, als Polynomidentitaet.

    ``PolynomialMap.determinant`` rechnet seit dem Umstieg auf
    ``DomainMatrix`` ueber der Ringdomain und terminiert damit auch in
    Dimension 17 -- in rund einer Minute. Das ist zu langsam fuer jeden
    Lauf, aber schnell genug, um die Stichprobe oben regelmaessig
    abzusichern. Siehe ``docs/architecture.md``, Abschnitt Polynomial
    Backend.
    """
    assert bcw17.determinant() == 1
