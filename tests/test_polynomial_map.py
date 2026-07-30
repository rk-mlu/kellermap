import math

import pytest
import sympy as sp

from bcw import PolynomialMap


@pytest.fixture
def F() -> PolynomialMap:
    """Eine einfache lineare Abbildung mit Jacobi-Determinante -2."""
    x, y = sp.symbols("x y")
    return PolynomialMap(variables=(x, y), components=(x + y, x - y))


# --------------------------------------------------------------------------
# Smoke tests: jede oeffentliche Methode wird mindestens einmal aufgerufen.
# --------------------------------------------------------------------------


def test_dimension(F: PolynomialMap) -> None:
    assert F.dimension == 2


def test_matrix(F: PolynomialMap) -> None:
    x, y = F.variables
    assert F.matrix == sp.Matrix([x + y, x - y])


def test_matrix_is_cached(F: PolynomialMap) -> None:
    """Regression: cached_property braucht ein __dict__, also kein slots=True."""
    assert F.matrix is F.matrix


def test_jacobian(F: PolynomialMap) -> None:
    assert F.jacobian() == sp.Matrix([[1, 1], [1, -1]])


def test_determinant(F: PolynomialMap) -> None:
    assert F.determinant() == -2


def test_degree(F: PolynomialMap) -> None:
    assert F.degree() == 1


def test_degree_of_mixed_map() -> None:
    x, y = sp.symbols("x y")

    F = PolynomialMap(
        (x, y),
        (
            x**3 + y**5,
            x**7,
        ),
    )

    assert F.degree() == 7


def test_compose(F: PolynomialMap) -> None:
    x, y = F.variables
    G = PolynomialMap((x, y), (x * y, x))

    composed = F.compose(G)

    expected = (x * y + x, x * y - x)
    assert all(
        sp.expand(a - b) == 0
        for a, b in zip(composed.components, expected, strict=True)
    )


def test_compose_with_identity(F: PolynomialMap) -> None:
    identity = PolynomialMap(F.variables, F.variables)
    assert F.compose(identity).components == F.components


def test_compose_is_simultaneous(F: PolynomialMap) -> None:
    """Regression: subs(dict) substituiert sequentiell, xreplace simultan."""
    x, y = F.variables
    swap = PolynomialMap((x, y), (y, x))

    assert F.compose(swap).components == (y + x, y - x)


def test_call_is_simultaneous(F: PolynomialMap) -> None:
    """Regression: dieselbe Falle wie in compose."""
    x, y = F.variables
    assert F(y, x) == sp.Matrix([y + x, y - x])


def test_extend(F: PolynomialMap) -> None:
    x, y = F.variables
    extended = F.extend(2)

    assert extended.dimension == 4
    assert extended.variables[:2] == (x, y)
    assert extended.components[2:] == extended.variables[2:]


def test_call(F: PolynomialMap) -> None:
    assert F(sp.Integer(1), sp.Integer(2)) == sp.Matrix([3, -1])


def test_call_wrong_arity(F: PolynomialMap) -> None:
    with pytest.raises(ValueError, match="Expected 2 arguments"):
        F(sp.Integer(1))


def test_call_symbolic(F: PolynomialMap) -> None:
    a, b = sp.symbols("a b")

    assert F(a, b) == sp.Matrix([a + b, a - b])


def test_repr(F: PolynomialMap) -> None:
    assert repr(F).startswith("PolynomialMap(")


def test_order_of_mixed_map() -> None:
    x, y = sp.symbols("x y")

    F = PolynomialMap(
        (x, y),
        (
            x**3 + y**5,
            x**7,
        ),
    )

    assert F.order() == 3


def test_frozen(F: PolynomialMap) -> None:
    """frozen=True uebernimmt die Rolle, die slots=True hier nicht spielt."""
    from dataclasses import FrozenInstanceError

    with pytest.raises(FrozenInstanceError):
        F.variables = ()  # type: ignore[misc]


def test_hashable(F: PolynomialMap) -> None:
    assert len({F, F}) == 1


def test_cached_matrix_does_not_change_hash(F: PolynomialMap) -> None:
    before = hash(F)

    _ = F.matrix

    after = hash(F)

    assert before == after


# --------------------------------------------------------------------------
# Validierung
# --------------------------------------------------------------------------


def test_length_mismatch() -> None:
    x, y = sp.symbols("x y")
    with pytest.raises(ValueError, match="differ"):
        PolynomialMap((x, y), (x + y,))


def test_determinant_need_not_be_constant() -> None:
    x, y = sp.symbols("x y")

    F = PolynomialMap(
        (x, y),
        (
            x**2,
            y,
        ),
    )

    assert sp.expand(F.determinant() - 2 * x) == 0


def test_duplicate_variables() -> None:
    x = sp.Symbol("x")
    with pytest.raises(ValueError, match="pairwise distinct"):
        PolynomialMap((x, x), (x, x))


def test_variables_must_be_symbols() -> None:
    x, y = sp.symbols("x y")
    with pytest.raises(TypeError, match="SymPy symbols"):
        PolynomialMap((x, x * y), (x, y))


def test_compose_requires_same_variables() -> None:
    x, y, u, v = sp.symbols("x y u v")
    F = PolynomialMap((x, y), (x, y))
    G = PolynomialMap((u, v), (u, v))
    with pytest.raises(ValueError, match="different variables"):
        F.compose(G)


def test_compose_is_associative() -> None:
    x, y = sp.symbols("x y")

    F = PolynomialMap((x, y), (x + y, x - y))
    G = PolynomialMap((x, y), (x**2, x + y))
    H = PolynomialMap((x, y), (y, x))

    left = F.compose(G).compose(H)
    right = F.compose(G.compose(H))

    assert all(
        sp.expand(a - b) == 0
        for a, b in zip(left.components, right.components, strict=True)
    )


def test_matrix_is_column_vector(F: PolynomialMap) -> None:
    assert F.matrix.rows == F.dimension
    assert F.matrix.cols == 1


def test_compose_does_not_substitute_recursively() -> None:
    x, y = sp.symbols("x y")

    F = PolynomialMap((x, y), (x, y))
    G = PolynomialMap((x, y), (y, x + 1))

    assert F.compose(G).components == (y, x + 1)


# --------------------------------------------------------------------------
# Grad und Ordnung relativ zu den eigenen Variablen
# --------------------------------------------------------------------------


def test_degree_ignores_parameters() -> None:
    """Regression: total_degree ohne Generatoren zaehlt Fremdsymbole mit.

    In BCW Paragraph 4 wird ueber k[T] gerechnet; T ist Skalar, keine Variable.
    """
    x, y, T = sp.symbols("x y T")
    F = PolynomialMap((x, y), (T**5 * x**2, y))

    assert F.degree() == 2


def test_degree_ignores_symbolic_coefficients() -> None:
    x, y, a = sp.symbols("x y a")
    F = PolynomialMap((x, y), (a**3 * x, y))

    assert F.degree() == 1


def test_order(F: PolynomialMap) -> None:
    assert F.order() == 1


def test_order_ignores_parameters() -> None:
    x, y, T = sp.symbols("x y T")
    F = PolynomialMap((x, y), (x**3 + T**9 * y**2, x))

    assert F.order() == 1


def test_order_skips_zero_components() -> None:
    x, y = sp.symbols("x y")
    F = PolynomialMap((x, y), (sp.Integer(0), x**2))

    assert F.order() == 2


def test_order_of_zero_map_is_infinite() -> None:
    x, y = sp.symbols("x y")
    F = PolynomialMap((x, y), (sp.Integer(0), sp.Integer(0)))

    assert F.order() == math.inf


def test_displacement(F: PolynomialMap) -> None:
    x, y = F.variables
    assert F.displacement().components == (y, x - 2 * y)


def test_identity_lies_in_every_MA() -> None:
    x, y = sp.symbols("x y")
    identity = PolynomialMap((x, y), (x, y))

    assert identity.filtration_degree() == math.inf
    assert identity.is_in_MA(17)


# --------------------------------------------------------------------------
# Filtrierung MA^d nach BCW, Proposition (3.1), Formel (1)
# --------------------------------------------------------------------------


def test_bcw_G_lies_in_MA1() -> None:
    """G = (X1 - X3*X4, X2, X3, X4) verschiebt um Ordnung 2, liegt also in MA^1."""
    X1, X2, X3, X4 = sp.symbols("X1 X2 X3 X4")
    G = PolynomialMap((X1, X2, X3, X4), (X1 - X3 * X4, X2, X3, X4))

    assert G.filtration_degree() == 1
    assert G.is_in_MA(1)


def test_bcw_H_lies_in_MA1_when_P_and_Q_are_quadratic() -> None:
    """Erster Teil des Beweises: deg P, deg Q >= 2, also H in MA^1."""
    X1, X2, X3, X4 = sp.symbols("X1 X2 X3 X4")
    H = PolynomialMap((X1, X2, X3, X4), (X1, X2, X3 + X1**2, X4 + X2**2))

    assert H.filtration_degree() == 1
    assert H.is_in_MA(1)


def test_bcw_H_lies_only_in_MA0_when_P_is_linear() -> None:
    """Linearisierungsteil: P = X1 hat Grad 1, deshalb fordert BCW nur EA^0."""
    X1, X2, X3, X4 = sp.symbols("X1 X2 X3 X4")
    H = PolynomialMap((X1, X2, X3, X4), (X1, X2, X3 + X1, X4 + X1 * X2))

    assert H.filtration_degree() == 0
    assert H.is_in_MA(0)
    assert not H.is_in_MA(1)


def test_bcw_G_not_in_MA2() -> None:
    X1, X2, X3, X4 = sp.symbols("X1 X2 X3 X4")

    G = PolynomialMap(
        (X1, X2, X3, X4),
        (
            X1 - X3 * X4,
            X2,
            X3,
            X4,
        ),
    )

    assert not G.is_in_MA(2)


# --------------------------------------------------------------------------
# Regressionstest gegen ein Beispiel aus der Literatur
# --------------------------------------------------------------------------

# Alpoeges Gegenbeispiel zur Jacobi-Vermutung, X-Post vom 20. Juli 2026.
# Die Kollision ist die von Tao notierte rationale Kollision.

ALPOEGE_COLLISION = (
    (sp.Integer(0), sp.Integer(0), sp.Rational(-1, 4)),
    (sp.Integer(1), sp.Rational(-3, 2), sp.Rational(13, 2)),
    (sp.Integer(-1), sp.Rational(3, 2), sp.Rational(13, 2)),
)

ALPOEGE_IMAGE = sp.Matrix([sp.Rational(-1, 4), 0, 0])


@pytest.fixture
def alpoege() -> PolynomialMap:
    x, y, z = sp.symbols("x y z")

    return PolynomialMap(
        variables=(x, y, z),
        components=(
            (1 + x * y) ** 3 * z + y**2 * (1 + x * y) * (4 + 3 * x * y),
            y + 3 * x * (1 + x * y) ** 2 * z + 3 * x * y**2 * (4 + 3 * x * y),
            2 * x - 3 * x**2 * y - x**3 * z,
        ),
    )


def test_alpoege_is_a_keller_map(alpoege: PolynomialMap) -> None:
    """Die Jacobi-Determinante ist konstant und invertierbar."""
    determinant = alpoege.determinant()

    assert determinant.free_symbols == set()
    assert determinant == -2


def test_alpoege_is_not_injective(alpoege: PolynomialMap) -> None:
    """Der eigentliche Inhalt: drei verschiedene Urbilder desselben Punktes.

    Zusammen mit der konstanten Determinante widerlegt das die
    Jacobi-Vermutung in Dimension 3.
    """
    assert len(set(ALPOEGE_COLLISION)) == 3

    images = [sp.expand(alpoege(*point)) for point in ALPOEGE_COLLISION]

    assert all(image == ALPOEGE_IMAGE for image in images)


def test_alpoege_degree(alpoege: PolynomialMap) -> None:
    assert alpoege.dimension == 3
    assert alpoege.degree() == 7
