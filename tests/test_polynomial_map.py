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


def test_repr(F: PolynomialMap) -> None:
    assert repr(F).startswith("PolynomialMap(")


def test_frozen(F: PolynomialMap) -> None:
    """frozen=True uebernimmt die Rolle, die slots=True hier nicht spielt."""
    from dataclasses import FrozenInstanceError

    with pytest.raises(FrozenInstanceError):
        F.variables = ()  # type: ignore[misc]


def test_hashable(F: PolynomialMap) -> None:
    assert len({F, F}) == 1


# --------------------------------------------------------------------------
# Gleichheit und Hash
#
# eq=False im Dataclass-Dekorator: __eq__ und __hash__ sind handgeschrieben
# und muessen deshalb eigens geprueft werden. len({F, F}) == 1 testet nur
# Identitaet, nicht Gleichheit.
# --------------------------------------------------------------------------


def test_equal_maps_built_separately_compare_equal(F: PolynomialMap) -> None:
    x, y = F.variables
    twin = PolynomialMap((x, y), (x + y, x - y))

    assert twin is not F
    assert twin == F


def test_equality_is_polynomial_not_syntactic(F: PolynomialMap) -> None:
    """Der Normalisierung durch den PolyRing ist zu trauen."""
    x, y = F.variables
    unexpanded = PolynomialMap((x, y), ((x + y) * (x - y) / (x - y), x - y))

    assert unexpanded == F


def test_maps_differing_in_a_component_are_unequal(F: PolynomialMap) -> None:
    x, y = F.variables

    assert PolynomialMap((x, y), (x + y, x + y)) != F


def test_maps_differing_in_the_variables_are_unequal() -> None:
    """Gleiche Komponenten, andere Traegervariablen: verschiedene Abbildungen."""
    x, y, u, v = sp.symbols("x y u v")

    assert PolynomialMap((x, y), (x, y)) != PolynomialMap((u, v), (u, v))


def test_variable_order_matters(F: PolynomialMap) -> None:
    """(x, y) und (y, x) erzeugen verschiedene Ringe."""
    x, y = F.variables

    assert PolynomialMap((y, x), (x + y, x - y)) != F


def test_equality_with_a_foreign_type_is_not_implemented(F: PolynomialMap) -> None:
    assert F.__eq__(object()) is NotImplemented
    assert F != object()


def test_equal_maps_share_a_hash(F: PolynomialMap) -> None:
    """Das Vertragsversprechen von __hash__: a == b impliziert hash(a) == hash(b)."""
    x, y = F.variables
    twin = PolynomialMap((x, y), (x + y, x - y))

    assert hash(twin) == hash(F)
    assert len({F, twin}) == 1


# --------------------------------------------------------------------------
# Validierung
# --------------------------------------------------------------------------


def test_length_mismatch() -> None:
    x, y = sp.symbols("x y")
    with pytest.raises(ValueError, match="differ"):
        PolynomialMap((x, y), (x + y,))


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


# --------------------------------------------------------------------------
# PolyRing backend
# --------------------------------------------------------------------------


def test_internal_backend_is_polyring(F: PolynomialMap) -> None:
    from sympy.polys.rings import PolyElement, PolyRing

    assert isinstance(F.ring, PolyRing)
    assert all(isinstance(component, PolyElement) for component in F.to_polynomials())


def test_from_ring_preserves_polynomial_map() -> None:
    from sympy.polys.domains import QQ
    from sympy.polys.rings import ring

    R, x, y = ring("x,y", QQ)
    F = PolynomialMap.from_ring(R, (x + y, x - y))

    assert F.variables == R.symbols
    assert F.components == (R.symbols[0] + R.symbols[1], R.symbols[0] - R.symbols[1])


def test_from_ring_copies_mutable_polynomials() -> None:
    from sympy.polys.domains import QQ
    from sympy.polys.rings import ring

    R, x, y = ring("x,y", QQ)
    first = x + y
    F = PolynomialMap.from_ring(R, (first, x - y))

    first[R.zero_monom] = R.domain.one

    assert F.components == (R.symbols[0] + R.symbols[1], R.symbols[0] - R.symbols[1])


def test_to_polynomials_returns_defensive_copies(F: PolynomialMap) -> None:
    polynomials = F.to_polynomials()
    polynomials[0][F.ring.zero_monom] = F.ring.domain.one

    x, y = F.variables
    assert F.components == (x + y, x - y)


def test_non_polynomial_component_is_rejected() -> None:
    x, y = sp.symbols("x y")

    with pytest.raises(ValueError, match="must be polynomials"):
        PolynomialMap((x, y), (sp.sin(x), y))


def test_compose_unifies_compatible_coefficient_domains() -> None:
    x, y, T = sp.symbols("x y T")
    F = PolynomialMap((x, y), (T * x + y, x))
    G = PolynomialMap((x, y), (x / 2, y))

    assert F.compose(G).components == (T * x / 2 + y, x / 2)


def test_determinant_with_symbolic_coefficient_domain() -> None:
    x, y, T = sp.symbols("x y T")
    F = PolynomialMap((x, y), (T * x + y, x - y))

    assert F.determinant() == -T - 1


def test_extend_avoids_coefficient_domain_symbol_collision() -> None:
    x, y, X3 = sp.symbols("x y X3")
    F = PolynomialMap((x, y), (X3 * x, y))

    extended = F.extend(2)

    assert extended.variables == (x, y, sp.Symbol("X4"), sp.Symbol("X5"))
    assert extended.components[-2:] == extended.variables[-2:]


def test_extend_rejects_negative_size(F: PolynomialMap) -> None:
    with pytest.raises(ValueError, match="non-negative"):
        F.extend(-1)


def test_extend_by_zero_returns_same_object(F: PolynomialMap) -> None:
    assert F.extend(0) is F
