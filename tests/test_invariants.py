"""Invarianten, die die BCW-Reduktion tragen.

Anders als die Smoke-Tests pruefen diese Tests keine einzelnen Methoden,
sondern die Identitaeten, auf denen das Zertifikat spaeter beruht: dass
Komposition und Stabilisierung die Jacobi-Determinante kontrollieren, dass
die Filtrierung MA^d ein Untermonoid ist, und dass Formel (1)-(3) aus
Proposition (3.1) tut, was das Paper behauptet.

Seitenangaben beziehen sich auf Bass, Connell, Wright, Bull. AMS 1982.
"""

import pytest
import sympy as sp

from kellermap import (
    ElementaryAutomorphism,
    ElementaryFactor,
    IndexedVariableFactory,
    PolynomialMap,
    examples,
)

# Eine eigene Namenspolitik fuer die Stabilisierungsvariablen.
CARRIER = IndexedVariableFactory(prefix="u")

x, y = sp.symbols("x y")

LINEAR = examples.sum_and_difference()
TRIANGULAR = examples.quadratic_shear()
KELLER = examples.cubic_shear()
NONCONSTANT = PolynomialMap((x, y), (x**2, y))
QUADRATIC = PolynomialMap((x, y), (x * y + 1, x - y**2))

PAIRS = [
    (LINEAR, TRIANGULAR),
    (TRIANGULAR, KELLER),
    (KELLER, QUADRATIC),
    (NONCONSTANT, LINEAR),
    (QUADRATIC, NONCONSTANT),
]


def vanishes(a: sp.Expr, b: sp.Expr) -> bool:
    """Polynomgleichheit, nicht syntaktische Gleichheit."""
    return bool(sp.expand(a - b) == 0)


# --------------------------------------------------------------------------
# Determinanten unter Komposition
# --------------------------------------------------------------------------


@pytest.mark.parametrize(("F", "G"), PAIRS)
def test_chain_rule_for_determinants(F: PolynomialMap, G: PolynomialMap) -> None:
    """det J(F o G) = det J(F)(G) * det J(G).

    Das ist die Identitaet, auf der das gesamte Zertifikat ruht: sie
    garantiert, dass Faktoren aus EA die Determinante nicht veraendern.
    """
    substitution = dict(zip(F.variables, G.components, strict=True))

    expected = F.determinant().xreplace(substitution) * G.determinant()

    assert vanishes(F.compose(G).determinant(), expected)


def test_elementary_automorphisms_have_determinant_one() -> None:
    """Warum die Determinantenpruefung in verify() redundant ist.

    G und H aus Proposition (3.1), Formel (1), sind elementar bzw. Produkte
    elementarer Automorphismen. Ihre Jacobi-Matrix ist bis auf eine Zeile
    die Einheitsmatrix, die Determinante also 1.
    """
    X1, X2, X3, X4 = sp.symbols("X1 X2 X3 X4")

    G = examples.product_shear()
    H = examples.paired_shear()

    assert G.determinant() == 1
    assert H.determinant() == 1


# --------------------------------------------------------------------------
# Stabilisierung, BCW S. 304
# --------------------------------------------------------------------------


def test_stabilization_jacobian_is_block_diagonal() -> None:
    """J(F^[m]) = diag(J(F), I_m), woertlich aus dem Paper."""
    m = 3
    extended = KELLER.extend(m)
    n = KELLER.dimension

    jacobian = extended.jacobian()

    assert jacobian[:n, :n] == KELLER.jacobian()
    assert jacobian[n:, n:] == sp.eye(m)
    assert jacobian[:n, n:].is_zero_matrix
    assert jacobian[n:, :n].is_zero_matrix


@pytest.mark.parametrize("F", [LINEAR, TRIANGULAR, KELLER, NONCONSTANT])
def test_stabilization_preserves_determinant(F: PolynomialMap) -> None:
    assert vanishes(F.extend(2).determinant(), F.determinant())


# Die neuen Komponenten X_{n+i} sind Monome vom Grad genau 1. Grad und
# Ordnung werden daher nicht erhalten, sondern gegen 1 abgeschnitten:
#
#     deg(F^[m]) = max(deg F, 1),    ord(F^[m]) = min(ord F, 1)   fuer m > 0.
#
# Erhalten bleiben Grad und Ordnung des Displacements und damit der
# Filtrierungsgrad -- und nur darauf stuetzt sich BCW.

DEGREE_AND_ORDER_CASES = [
    LINEAR,
    TRIANGULAR,
    KELLER,
    QUADRATIC,
    # Ordnung 2: die Stabilisierung senkt sie auf 1.
    PolynomialMap((x, y), (x**2, y**2)),
    # Grad 0: die Stabilisierung hebt ihn auf 1.
    PolynomialMap((x, y), (sp.Integer(5), sp.Integer(7))),
]


@pytest.mark.parametrize("F", DEGREE_AND_ORDER_CASES)
def test_stabilization_truncates_degree_and_order_at_one(F: PolynomialMap) -> None:
    """Grad und Ordnung unter Stabilisierung, exakt.

    Eine fruehere Fassung behauptete Erhaltung und pruefte das an vier
    Abbildungen, die saemtlich Grad >= 1 und Ordnung <= 1 hatten -- also
    genau an den Faellen, in denen die Abschneidung nicht sichtbar wird. Die
    beiden zusaetzlichen Faelle oben schliessen diese Luecke.
    """
    extended = F.extend(2)

    assert extended.degree() == max(F.degree(), 1)
    assert extended.order() == min(F.order(), 1)


@pytest.mark.parametrize("F", DEGREE_AND_ORDER_CASES)
def test_stabilization_preserves_the_displacement(F: PolynomialMap) -> None:
    """Was tatsaechlich erhalten bleibt und was BCW braucht.

    F^[m] - X unterscheidet sich von F - X nur um m Nullkomponenten, also
    stimmen Grad und Ordnung des Displacements ueberein. Der Filtrierungsgrad
    folgt daraus.
    """
    extended = F.extend(2)

    assert extended.displacement().degree() == F.displacement().degree()
    assert extended.displacement().order() == F.displacement().order()
    assert extended.filtration_degree() == F.filtration_degree()


@pytest.mark.parametrize(("F", "G"), PAIRS)
def test_stabilization_is_a_monoid_homomorphism(
    F: PolynomialMap, G: PolynomialMap
) -> None:
    """(F o G)^[m] = F^[m] o G^[m], BCW S. 304.

    Die Identitaet erreicht ``extend`` ueber drei getrennte Aufrufe, und sie
    gilt nur, wenn alle drei dieselben Namen vergeben. Frueher stand das hier
    als Kommentar und wurde davon getragen, dass gleichdimensionale
    Abbildungen zufaellig uebereinstimmten. Jetzt wird die Factory
    durchgereicht: die Voraussetzung steht im Test, statt in einer Fussnote.

    ``CARRIER`` ist absichtlich nicht die Standard-Factory -- ein zufaelliges
    Uebereinstimmen mit deren Namen wuerde den Test wieder aussagelos machen.
    """
    left = F.compose(G).extend(2, CARRIER)
    right = F.extend(2, CARRIER).compose(G.extend(2, CARRIER))

    assert all(
        vanishes(a, b) for a, b in zip(left.components, right.components, strict=True)
    )


def test_stabilization_of_the_identity_is_the_identity() -> None:
    identity = PolynomialMap.identity((x, y))
    extended = identity.extend(2)

    assert extended.components == extended.variables


# --------------------------------------------------------------------------
# Filtrierung MA^d als Untermonoid
# --------------------------------------------------------------------------


def test_MA_is_closed_under_composition() -> None:  # noqa: N802
    """MA^d ist ein Untermonoid.

    BCW komponieren in Proposition (3.1) wiederholt Elemente aus EA^1; das
    ist nur zulaessig, weil die Filtrierungsstufe dabei erhalten bleibt.
    """
    A = examples.cubic_shear()
    B = examples.lower_shear()

    assert A.is_in_MA(1)
    assert B.is_in_MA(1)
    assert A.compose(B).is_in_MA(1)


def test_composition_does_not_lower_the_filtration_degree() -> None:
    """ord(F o G - X) >= min(ord(F - X), ord(G - X))."""
    A = PolynomialMap((x, y), (x + y**4, y))
    B = examples.lower_shear()

    assert A.compose(B).filtration_degree() >= min(
        A.filtration_degree(), B.filtration_degree()
    )


# --------------------------------------------------------------------------
# Grad und Ordnung
# --------------------------------------------------------------------------


@pytest.mark.parametrize(("F", "G"), PAIRS)
def test_degree_is_submultiplicative(F: PolynomialMap, G: PolynomialMap) -> None:
    assert F.compose(G).degree() <= F.degree() * G.degree()


def test_homogeneous_map_has_equal_degree_and_order() -> None:
    """Das Reduktionsziel von Korollar (2.2) ist kubisch homogen.

    Homogenitaet laesst sich mit den vorhandenen Mitteln als degree == order
    ausdruecken; das ist der Test, den ein spaeteres is_homogeneous() erfuellen
    muss.
    """
    cubic = PolynomialMap((x, y), (x**3, x**2 * y))

    assert cubic.degree() == cubic.order() == 3
    assert TRIANGULAR.degree() != TRIANGULAR.order()


# --------------------------------------------------------------------------
# Proposition (3.1), Formel (1)-(3), als ausfuehrbare Identitaet
# --------------------------------------------------------------------------

# F = X1 + X2^4 hat Grad d = 4. Das fuehrende Monom ist M = X2^4 mit a = 1,
# und aM = P*Q mit P = Q = X2^2, beide vom Grad <= d - 2 = 2.

X1, X2, X3, X4 = sp.symbols("X1 X2 X3 X4")

BCW_F = PolynomialMap((X1, X2), (X1 + X2**4, X2))
BCW_P = X2**2
BCW_Q = X2**2

BCW_G = examples.product_shear()
BCW_H = PolynomialMap((X1, X2, X3, X4), (X1, X2, X3 + BCW_P, X4 + BCW_Q))


@pytest.fixture
def reduced() -> PolynomialMap:
    """F' = G o F^[2] o H aus Formel (1)."""
    return BCW_G.compose(BCW_F.extend(2).compose(BCW_H))


def test_bcw_step_matches_formula_two_and_three(reduced: PolynomialMap) -> None:
    """F' = (F1', F2, X3 + P, X4 + Q) mit F1' = (F1 - aM) - X3*Q - P*X4 - X3*X4.

    Das ist die Identitaet, die ein spaeterer BCWStep reproduzieren muss.
    """
    F1, F2 = BCW_F.components
    aM = X2**4

    expected_F1 = (F1 - aM) - X3 * BCW_Q - BCW_P * X4 - X3 * X4
    expected = (expected_F1, F2, X3 + BCW_P, X4 + BCW_Q)

    assert all(
        vanishes(a, b) for a, b in zip(reduced.components, expected, strict=True)
    )


def test_bcw_step_lowers_the_degree(reduced: PolynomialMap) -> None:
    """Der Zweck des Schritts: deg(F') < deg(F), hier 4 -> 3."""
    assert BCW_F.degree() == 4
    assert reduced.degree() == 3


def test_bcw_step_preserves_the_determinant(reduced: PolynomialMap) -> None:
    """G und H liegen in EA, also aendert der Schritt die Determinante nicht."""
    assert BCW_F.determinant() == 1
    assert reduced.determinant() == 1


def test_bcw_step_factors_lie_in_EA1() -> None:  # noqa: N802
    """Erster Teil von Proposition (3.1): deg P, deg Q >= 2, also G, H in EA^1."""
    assert sp.Poly(BCW_P, X1, X2).total_degree() >= 2
    assert sp.Poly(BCW_Q, X1, X2).total_degree() >= 2

    assert BCW_G.is_in_MA(1)
    assert BCW_H.is_in_MA(1)


@pytest.mark.parametrize("F", [LINEAR, TRIANGULAR, KELLER, QUADRATIC])
@pytest.mark.parametrize(("m", "ell"), [(1, 1), (2, 2), (1, 3)])
def test_stabilization_composes(F: PolynomialMap, m: int, ell: int) -> None:
    """(F^[m])^[l] = F^[m+l], BCW S. 304.

    Zusammen mit dem Monoid-Homomorphismus ist das die zweite Zusage, die
    eine schrittweise stabilisierende Reduktion braucht: sie muss dort
    landen, wo eine einzige Stabilisierung landet.
    """
    assert F.extend(m, CARRIER).extend(ell, CARRIER) == F.extend(m + ell, CARRIER)


# --------------------------------------------------------------------------
# Formel (1) mit Elementarautomorphismen statt mit rohen Abbildungen
# --------------------------------------------------------------------------


def test_bcw_step_can_be_built_from_elementary_factors(
    reduced: PolynomialMap,
) -> None:
    """Dieselbe Reduktion, aus G und H als Gruppenelemente.

    Oben werden G und H als gewoehnliche PolynomialMaps hingeschrieben und
    ihre Invertierbarkeit nur behauptet. Hier tragen sie ihre Faktorisierung
    mit sich, und der Schritt laesst sich rueckgaengig machen. Das ist die
    Form, in der ein BCWStep sie ablegen muss.
    """
    stabilized = BCW_F.extend(2)
    ring = stabilized.ring
    X1, X2, X3, X4 = ring.gens

    G = ElementaryAutomorphism([ElementaryFactor(ring, 0, -X3 * X4)])
    H = ElementaryAutomorphism(
        [ElementaryFactor(ring, 2, X2**2), ElementaryFactor(ring, 3, X2**2)]
    )

    assert G.apply_to(stabilized.compose(H.to_polynomial_map())) == reduced

    assert G.determinant() == H.determinant() == 1
    assert G.is_in_EA(1)
    assert H.is_in_EA(1)

    # Der Schritt ist umkehrbar, ohne dass irgendetwas geloest wird.
    undone = G.inverse().apply_to(reduced).compose(H.inverse().to_polynomial_map())

    assert undone == stabilized
