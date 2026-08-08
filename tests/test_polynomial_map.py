import math

import pytest
import sympy as sp

from kellermap import PolynomialMap


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


# --------------------------------------------------------------------------
# Determinantenstrategie: unipotenter Traegerblock und Schur-Komplement
# --------------------------------------------------------------------------

X1, X2, X3, X4 = sp.symbols("X1 X2 X3 X4")

# Kandidaten fuer die Kreuzprobe: mit und ohne Traegerblock, mit rationalen
# und mit symbolischen Koeffizienten.
DETERMINANT_CASES = [
    PolynomialMap((X1, X2), (X1, X2)),
    PolynomialMap((X1, X2), (X1 + X2, X1 - X2)),
    PolynomialMap((X1, X2), (X1**2, X2)),
    PolynomialMap((X1, X2), (X1 * X2 + 1, X1 - X2**2)),
    PolynomialMap((X1, X2), (X1 + X2**2, X2 + X1**2)),
    PolynomialMap((X1, X2), (sp.Symbol("T") * X1 + X2, X1 - X2)),
    PolynomialMap((X1, X2, X3, X4), (X1 - X3 * X4, X2, X3, X4)),
    PolynomialMap((X1, X2, X3, X4), (X1, X2, X3 + X2**2, X4 + X2**2)),
    PolynomialMap((X1, X2, X3), (X1 + X2 * X3, X2 + X3**2, X3)),
]


@pytest.mark.parametrize("F", DETERMINANT_CASES)
def test_determinant_matches_an_expression_valued_computation(
    F: PolynomialMap,
) -> None:
    """Cross-representation test nach ``docs/architecture.md``.

    Die Referenz laeuft vollstaendig ueber ``Expr``: SymPys eigene
    ``Matrix.jacobian`` und ``Matrix.det``. Damit haengt sie an keinem Teil
    der hiesigen Integration mit ``DomainMatrix`` oder der Strategiewahl.
    """
    reference = sp.Matrix(F.components).jacobian(sp.Matrix(F.variables)).det()

    assert sp.expand(F.determinant() - reference) == 0


@pytest.mark.parametrize("F", DETERMINANT_CASES)
def test_schur_complement_agrees_with_the_domain_matrix_path(
    F: PolynomialMap,
) -> None:
    """Beide Strategien muessen dasselbe Polynom liefern."""
    reference = F._determinant_by_domain_matrix(F._jacobian_polynomials)

    assert F.determinant() == reference.as_expr()


def test_elementary_automorphism_is_unipotent_throughout() -> None:
    """Der Grenzfall: der Kopfblock ist leer, die Determinante folgt aus der
    Struktur und nicht aus einer Entwicklung."""
    G = PolynomialMap((X1, X2, X3, X4), (X1 - X3 * X4, X2, X3, X4))

    assert G.carrier_indices == (0, 1, 2, 3)
    assert G.determinant() == 1


def test_carrier_requires_a_unit_diagonal_entry() -> None:
    """dF_i/dX_i muss exakt 1 sein, nicht bloss konstant."""
    F = PolynomialMap((X1, X2), (2 * X1 + X2**2, X2))

    assert F.carrier_indices == (1,)


def test_carrier_drops_coordinates_on_a_dependency_cycle() -> None:
    """X1 haengt von X2 ab und X2 von X1: der Block ist nicht nilpotent.

    Die Diagonale ist hier zweimal 1, die Erkennung darf sich davon nicht
    taeuschen lassen, sonst waere die Neumann-Reihe divergent.
    """
    F = PolynomialMap((X1, X2), (X1 + X2**2, X2 + X1**2))

    assert F.carrier_indices == ()
    assert F.determinant() == 1 - 4 * X1 * X2


def test_carrier_keeps_an_acyclic_chain() -> None:
    """Dieselbe Diagonale, aber azyklisch: der ganze Block ist brauchbar."""
    F = PolynomialMap((X1, X2), (X1 + X2**2, X2))

    assert F.carrier_indices == (0, 1)
    assert F.determinant() == 1


def test_schur_complement_refuses_a_non_nilpotent_block() -> None:
    """Regression fuer einen echten Fehler.

    Ein erster Entwurf hat die Nilpotenz nicht geprueft, sondern aus dem
    Abbruch der Neumann-Reihe geschlossen. Bei leerem Kopfblock bricht die
    Reihe sofort ab, ganz gleich wie L aussieht -- das leere
    Schur-Komplement lieferte dann Determinante 1 fuer eine Abbildung mit
    Determinante 1 - 4*X1*X2.

    ``carrier_indices`` gibt einen solchen Block nie heraus, der Fall wird
    hier von Hand erzwungen.
    """
    F = PolynomialMap((X1, X2), (X1 + X2**2, X2 + X1**2))

    assert F.carrier_indices == ()
    assert F._schur_complement((0, 1)) is None
    assert F.determinant() == 1 - 4 * X1 * X2


def test_unipotent_block_rejects_a_non_unit_diagonal() -> None:
    """Zweiter Teil der Vorbedingung: D muss I + L sein, nicht bloss
    dreiecksfoermig."""
    F = PolynomialMap((X1, X2), (2 * X1 + X2**2, X2))

    assert F._is_unipotent_block((1,))
    assert not F._is_unipotent_block((0, 1))
    assert F._schur_complement((0, 1)) is None


# --------------------------------------------------------------------------
# Unveraenderlichkeit der oeffentlichen Matrizen
# --------------------------------------------------------------------------


def test_matrix_is_immutable(F: PolynomialMap) -> None:
    """Regression fuer einen echten Fehler.

    ``matrix`` ist gecacht. Solange sie veraenderlich war, verfaelschte eine
    Zuweisung von aussen jede spaetere Auswertung: nach ``F.matrix[0] = 0``
    lieferte ``F(1, 2)`` den Wert ``[0, -1]`` statt ``[3, -1]``, obwohl
    ``components`` unberuehrt blieb.
    """
    with pytest.raises(TypeError):
        F.matrix[0] = sp.Integer(0)  # type: ignore[index]

    assert F(sp.Integer(1), sp.Integer(2)) == sp.Matrix([3, -1])


def test_jacobian_is_immutable(F: PolynomialMap) -> None:
    """Hier kein Fehler, sondern Konsistenz: die oeffentliche Grenze sagt
    unveraenderliche SymPy-Objekte zu."""
    with pytest.raises(TypeError):
        F.jacobian()[0, 0] = sp.Integer(0)  # type: ignore[index]


def test_evaluation_returns_an_immutable_matrix(F: PolynomialMap) -> None:
    result = F(sp.Integer(1), sp.Integer(2))

    assert isinstance(result, sp.ImmutableMatrix)
    assert result == sp.Matrix([3, -1])


def test_mutable_copies_remain_available(F: PolynomialMap) -> None:
    """Wer eine veraenderliche Matrix braucht, bekommt sie -- als Kopie."""
    copy = sp.Matrix(F.matrix)
    copy[0] = sp.Integer(0)

    assert F.matrix[0] != 0


# --------------------------------------------------------------------------
# Eindeutigkeit der Generatoren
# --------------------------------------------------------------------------


def test_from_ring_rejects_duplicate_generators() -> None:
    """Ein PolyRing ueber (x, x) laesst sich bauen; die beiden Generatoren
    sind beim Uebergang zu Ausdruecken nicht mehr zu unterscheiden."""
    from sympy.polys.domains import QQ
    from sympy.polys.rings import ring

    x = sp.Symbol("x")
    R, first, second = ring([x, x], QQ)

    with pytest.raises(ValueError, match="pairwise distinct"):
        PolynomialMap.from_ring(R, (first, second))


def test_duplicate_variables_are_detected_by_name() -> None:
    """Verschiedene Annahmen, gleicher Name: die Symbole sind ungleich, ihre
    Ausdruecke aber ununterscheidbar."""
    plain = sp.Symbol("x")
    positive = sp.Symbol("x", positive=True)

    assert plain != positive

    with pytest.raises(ValueError, match="pairwise distinct"):
        PolynomialMap((plain, positive), (plain, positive))


# --------------------------------------------------------------------------
# Leere Eingaben und ungueltige Ringe
# --------------------------------------------------------------------------


def test_empty_input_is_rejected() -> None:
    with pytest.raises(ValueError, match="at least one variable"):
        PolynomialMap((), ())


def test_non_expression_components_are_rejected() -> None:
    x, y = sp.symbols("x y")

    with pytest.raises(TypeError, match="SymPy expressions"):
        PolynomialMap((x, y), (x, "y"))  # type: ignore[arg-type]


def test_from_ring_rejects_a_ring_without_generators() -> None:
    from sympy.polys.domains import QQ
    from sympy.polys.rings import ring

    empty = ring("", QQ)[0]

    with pytest.raises(ValueError, match="at least one variable"):
        PolynomialMap.from_ring(empty, ())


def test_from_ring_rejects_non_symbol_generators() -> None:
    """``PolyRing`` nimmt einen zusammengesetzten Ausdruck als Generator an."""
    from sympy.polys.domains import QQ
    from sympy.polys.rings import ring

    x, y = sp.symbols("x y")
    composite = ring([x * y], QQ)[0]

    assert not isinstance(composite.symbols[0], sp.Symbol)

    with pytest.raises(TypeError, match="SymPy symbols"):
        PolynomialMap.from_ring(composite, composite.gens)


def test_from_ring_rejects_a_component_count_mismatch() -> None:
    from sympy.polys.domains import QQ
    from sympy.polys.rings import ring

    R, a, b = ring("a,b", QQ)

    with pytest.raises(ValueError, match="differ"):
        PolynomialMap.from_ring(R, (a,))


def test_from_ring_rejects_a_component_from_another_ring() -> None:
    from sympy.polys.domains import QQ
    from sympy.polys.rings import ring

    R, a, b = ring("a,b", QQ)
    S, c, d = ring("c,d", QQ)

    with pytest.raises(ValueError, match="belong to the specified ring"):
        PolynomialMap.from_ring(R, (a, c))


# --------------------------------------------------------------------------
# Verschachtelte defensive Kopien
# --------------------------------------------------------------------------

# Ueber k[T] ist der Koeffizient eines Monoms selbst ein PolyElement, also
# wieder ein veraenderliches dict. Eine flache Kopie wuerde diese innere
# Ebene teilen; _copy_polynomial steigt deshalb rekursiv ab.


def _nested_coefficient(polynomial: object) -> object:
    """Return the first coefficient that is itself a polynomial."""
    from sympy.polys.rings import PolyElement

    assert isinstance(polynomial, PolyElement)
    for _, coefficient in polynomial.iterterms():
        if isinstance(coefficient, PolyElement) and coefficient != coefficient.ring.one:
            return coefficient
    raise AssertionError("no nested coefficient found")


def test_to_polynomials_copies_nested_coefficients() -> None:
    x, y, T = sp.symbols("x y T")
    F = PolynomialMap((x, y), (T * x + y, x))

    assert str(F.ring.domain) == "ZZ[T]"

    coefficient = _nested_coefficient(F.to_polynomials()[0])
    coefficient[coefficient.ring.zero_monom] = coefficient.ring.domain.one  # type: ignore[index]

    assert F.components == (T * x + y, x)


def test_from_ring_copies_nested_coefficients() -> None:
    """Dieselbe Ebene, andere Richtung: die Eingabe darf nachtraeglich
    veraendert werden, ohne die Abbildung zu treffen."""
    from sympy.polys.rings import ring

    T = sp.Symbol("T")
    R, a, b = ring("a,b", sp.polys.domains.QQ[T])
    component = T * a + b

    F = PolynomialMap.from_ring(R, (component, a))

    coefficient = _nested_coefficient(component)
    coefficient[coefficient.ring.zero_monom] = coefficient.ring.domain.one  # type: ignore[index]

    assert F.components[0] == T * sp.Symbol("a") + sp.Symbol("b")


def test_fraction_field_coefficients_are_copied() -> None:
    """Ueber k(T) ist ein Koeffizient ein FracElement mit veraenderlichem
    Zaehler und Nenner.

    Regression fuer einen echten Fehler: die Kopie stieg nur in PolyElement
    ab. Weil die Eins der Domain eine einzige geteilte Instanz ist, traf eine
    Mutation dort jeden Term mit Koeffizient eins -- die Abbildung
    (x/(T+1) + y, x) wurde zu (x/(T+1), 0).
    """
    x, y, T = sp.symbols("x y T")
    F = PolynomialMap((x, y), (x / (T + 1) + y, x))

    assert str(F.ring.domain) == "ZZ(T)"

    fractions = [c for _, c in F.to_polynomials()[0].iterterms() if hasattr(c, "numer")]

    assert fractions

    for coefficient in fractions:
        coefficient.numer.clear()
        coefficient.denom.clear()

    assert F.components == (x / (T + 1) + y, x)


def test_maps_over_different_domains_are_unequal() -> None:
    """Gleiche Variablen und Komponenten, andere Koeffizientendomain."""
    from sympy.polys.domains import QQ, ZZ
    from sympy.polys.rings import ring

    a, b = sp.symbols("a b")
    over_zz = ring([a, b], ZZ)[0]
    over_qq = ring([a, b], QQ)[0]

    left = PolynomialMap.from_ring(over_zz, over_zz.gens)
    right = PolynomialMap.from_ring(over_qq, over_qq.gens)

    assert left.components == right.components
    assert left != right


# --------------------------------------------------------------------------
# Der Ring wird nicht geteilt
# --------------------------------------------------------------------------

# PolyRing ist kein Wertobjekt: seine gens sind PolyElement, also veraenderliche
# dicts, und SymPy liest sie in from_expr und ring_new. Ein Aufrufer, der den
# internen Ring in die Hand bekaeme, koennte aendern, was die Abbildung
# rechnet -- ohne dass components davon etwas meldeten.


def test_ring_property_does_not_hand_out_the_internal_ring(
    F: PolynomialMap,
) -> None:
    before = F.displacement().components

    F.ring.gens[0].clear()

    assert F.displacement().components == before


def test_to_polynomials_does_not_leak_the_ring_either(F: PolynomialMap) -> None:
    """Ein PolyElement traegt eine Referenz auf seinen Ring; Kopien am internen
    Ring wuerden ihn direkt wieder herausreichen."""
    before = F.displacement().components

    F.to_polynomials()[0].ring.gens[0].clear()

    assert F.displacement().components == before


def test_from_ring_does_not_adopt_the_callers_ring() -> None:
    from sympy.polys.domains import QQ
    from sympy.polys.rings import ring

    R, a, b = ring("a,b", QQ)
    G = PolynomialMap.from_ring(R, (a + b, a))
    before = G.displacement().components

    R.gens[0].clear()

    assert G.displacement().components == before


def test_the_variable_factory_never_sees_the_internal_ring(
    F: PolynomialMap,
) -> None:
    seen: list[object] = []

    def peeking(ring: object, count: int) -> tuple[sp.Symbol, ...]:
        seen.append(ring)
        return (sp.Symbol("u1"),)

    F.extend(1, peeking)
    before = F.displacement().components

    seen[0].gens[0].clear()  # type: ignore[attr-defined]

    assert F.displacement().components == before


def test_the_handed_out_ring_stays_interchangeable(F: PolynomialMap) -> None:
    """Die Isolierung darf den Ring nicht unbrauchbar machen.

    Der Klon ist wertgleich, komponiert und vergleicht sich also wie der
    interne -- sonst waere er als Argument fuer ``from_ring`` oder eine
    Factory wertlos.
    """
    view = F.ring

    assert view == F.ring
    assert PolynomialMap.from_ring(view, F.to_polynomials()) == F


# Der Klon muss ueber PolyRing gebaut werden, nicht ueber PolyRing.clone:
# letzteres laeuft durch SymPys cacheit, und das Klonen eines Klons gibt
# dasselbe Objekt zurueck. Eine Isolierung darauf waere fuer jede Abbildung
# aus from_ring -- also jedes Ergebnis von compose und extend -- wirkungslos,
# ohne dass ein Test es meldete, der nur den Ausdruckskonstruktor prueft.

CONSTRUCTION_PATHS = ["expressions", "from_ring", "compose", "extend"]


def _build(path: str) -> PolynomialMap:
    x, y = sp.symbols("x y")
    base = PolynomialMap((x, y), (x + y**2, x - y))

    if path == "expressions":
        return base
    if path == "from_ring":
        return PolynomialMap.from_ring(base.ring, base.to_polynomials())
    if path == "compose":
        return base.compose(base)
    return base.extend(2)


@pytest.mark.parametrize("path", CONSTRUCTION_PATHS)
def test_every_construction_path_owns_its_ring(path: str) -> None:
    F = _build(path)

    assert F.ring is not F._ring
    assert F.ring.gens[0] is not F._ring.gens[0]


@pytest.mark.parametrize("path", CONSTRUCTION_PATHS)
def test_every_construction_path_is_isolated(path: str) -> None:
    F = _build(path)
    before = F.displacement().components

    F.ring.gens[0].clear()
    F.to_polynomials()[0].ring.gens[0].clear()

    assert F.displacement().components == before


def test_clone_ring_is_not_sympys_memoised_clone() -> None:
    """Die Falle festgehalten.

    ``PolyRing.clone`` eines Klons liefert den Klon selbst; ``clone_ring``
    liefert immer ein eigenes Objekt mit eigenen Generatoren.
    """
    from sympy.polys.domains import QQ
    from sympy.polys.rings import ring

    from kellermap.polynomial_map import clone_ring

    R = ring("a,b", QQ)[0]
    memoised = R.clone(symbols=R.symbols)

    assert memoised.clone(symbols=memoised.symbols) is memoised

    fresh = clone_ring(memoised)

    assert fresh is not memoised
    assert fresh == memoised
    assert fresh.gens[0] is not memoised.gens[0]


# --------------------------------------------------------------------------
# Die Ansicht wird nicht geteilt, und die Domain auch nicht
# --------------------------------------------------------------------------


def test_the_view_ring_is_not_cached(F: PolynomialMap) -> None:
    """Regression fuer einen echten Fehler.

    ``_view_ring`` war ein ``cached_property``. Damit bekamen alle Aufrufer
    denselben Klon, und einer, der ihn veraenderte, beschaedigte die Ansicht
    fuer alle folgenden -- ``F.ring`` lieferte anschliessend denselben,
    bereits kaputten Ring zurueck.
    """
    view = F.ring
    view.gens[0].clear()

    assert F.ring is not view
    assert F.ring.gens[0] != 0
    assert F.ring == view


def test_extension_after_a_mutated_view_is_unaffected(F: PolynomialMap) -> None:
    """Die Factory bekommt ebenfalls einen frischen Ring."""
    before = F.extend(1).variables

    F.ring.gens[0].clear()

    assert F.extend(1).variables == before


def test_to_polynomials_binds_each_call_to_its_own_ring(F: PolynomialMap) -> None:
    first, second = F.to_polynomials(), F.to_polynomials()

    assert first[0].ring is not second[0].ring
    # Innerhalb eines Aufrufs teilen sich die Komponenten einen Ring, sonst
    # liessen sie sich nicht miteinander verrechnen.
    assert first[0].ring is first[1].ring

    first[0].ring.gens[0].clear()

    assert F.to_polynomials()[0].ring.gens[0] != 0


def test_the_coefficient_domain_is_cloned_too() -> None:
    """Regression fuer das zweite Leck.

    ``clone_ring`` uebernahm die Domain unveraendert. Nach
    ``caller_domain.gens[0].clear()`` wandelte der angeblich isolierte Ring
    ``T*u`` in ``0`` um -- lautlos, weil ``components`` weiter stimmte.
    """
    from sympy.polys.domains import QQ
    from sympy.polys.rings import ring

    T = sp.Symbol("T")
    R, u, v = ring("u,v", QQ[T])
    caller_domain = R.domain

    G = PolynomialMap.from_ring(R, (T * u + v, u))

    assert caller_domain is not G.ring.domain

    caller_domain.gens[0].clear()

    assert G.ring.from_expr(T * sp.Symbol("u")) == G.to_polynomials()[0].ring.from_expr(
        T * sp.Symbol("u")
    )
    assert G.components == (T * sp.Symbol("u") + sp.Symbol("v"), sp.Symbol("u"))


def test_nested_coefficient_domains_are_cloned_at_every_level() -> None:
    from sympy.polys.domains import QQ
    from sympy.polys.rings import ring

    X3, S = sp.symbols("X3 S")
    R, u, v = ring("u,v", QQ[X3][S])

    G = PolynomialMap.from_ring(R, (u + v, v))
    view = G.ring

    assert view.domain is not R.domain
    assert view.domain.dom is not R.domain.dom
    assert view.domain == R.domain


def test_handed_out_coefficients_do_not_carry_the_internal_domain() -> None:
    """Ein PolyElement-Koeffizient traegt seinen eigenen Ring mit."""
    from sympy.polys.domains import QQ
    from sympy.polys.rings import PolyElement, ring

    T = sp.Symbol("T")
    R, u, v = ring("u,v", QQ[T])
    G = PolynomialMap.from_ring(R, (T * u + v, u))

    for _, coefficient in G.to_polynomials()[0].iterterms():
        if isinstance(coefficient, PolyElement):
            assert coefficient.ring is not G._ring.domain.ring


def test_extend_rejects_a_boolean() -> None:
    """bool ist eine Unterklasse von int.

    ``F.extend(True)`` waere sonst eine Erweiterung um genau eine Variable --
    fast sicher ein Tippfehler und nicht das, was jemand meinte.
    """
    x, y = sp.symbols("x y")
    F = PolynomialMap((x, y), (x + y, y))

    with pytest.raises(TypeError, match="must be an integer"):
        F.extend(True)  # type: ignore[arg-type]


@pytest.mark.parametrize("number", [2.0, "2", None])
def test_extend_rejects_non_integers(number: object) -> None:
    x, y = sp.symbols("x y")
    F = PolynomialMap((x, y), (x + y, y))

    with pytest.raises(TypeError, match="must be an integer"):
        F.extend(number)  # type: ignore[arg-type]


# --------------------------------------------------------------------------
# Der Ausdruckskonstruktor validiert den Ring, den sring baut
# --------------------------------------------------------------------------


def test_a_coefficient_may_not_shadow_a_coordinate() -> None:
    """Regression fuer einen echten Fehler.

    ``sring`` nimmt ein Symbol, das bereits Generator ist, zusaetzlich in die
    Koeffizientendomain auf, wenn es mit anderen Annahmen auftritt: gleicher
    Name, verschiedene Objekte. Der Ausdruckskonstruktor pruefte das nicht,
    ``from_ring`` schon -- die Abbildung sah gueltig aus, druckte in
    ``components`` dasselbe Zeichen fuer zwei Dinge, und erst ``extend()``
    scheiterte.
    """
    x, y = sp.Symbol("x"), sp.Symbol("y")
    parameter = sp.Symbol("x", positive=True)

    with pytest.raises(ValueError, match="coefficient indeterminate"):
        PolynomialMap((x, y), (x + parameter * y, y))


def test_a_genuine_parameter_is_still_accepted() -> None:
    """Die Gegenprobe: ein Parameter mit eigenem Namen bleibt zulaessig."""
    x, y, T = sp.symbols("x y T")

    F = PolynomialMap((x, y), (T * x + y, x))

    assert str(F.ring.domain) == "ZZ[T]"


# --------------------------------------------------------------------------
# Monomordnung ueberlebt das Klonen
# --------------------------------------------------------------------------

MONOMIAL_ORDERS = ["lex", "grlex", "grevlex"]


@pytest.mark.parametrize("order", MONOMIAL_ORDERS)
def test_cloning_keeps_the_polynomial_ring_order(order: str) -> None:
    """Regression fuer einen echten Fehler.

    ``clone_domain`` baute die Domain ohne ihre ``order`` nach. Eine mit
    ``grlex`` gebaute Domain kam als ``lex`` zurueck -- der Klon war also
    nicht wertgleich zum Original, entgegen der Zusage in ``docs/api.md``.
    """
    from sympy.polys.domains import QQ
    from sympy.polys.rings import ring

    T = sp.Symbol("T")
    domain = QQ.poly_ring(T, order=order)
    R = ring("u,v", domain)[0]

    F = PolynomialMap.from_ring(R, R.gens)

    assert F.ring.domain == domain
    assert F.ring.domain is not domain


@pytest.mark.parametrize("order", MONOMIAL_ORDERS)
def test_cloning_keeps_the_fraction_field_order(order: str) -> None:
    from sympy.polys.domains import QQ
    from sympy.polys.rings import ring

    T = sp.Symbol("T")
    domain = QQ.frac_field(T, order=order)
    R = ring("u,v", domain)[0]

    assert PolynomialMap.from_ring(R, R.gens).ring.domain == domain


def test_cloning_keeps_the_order_at_every_nesting_level() -> None:
    from sympy.polys.domains import QQ
    from sympy.polys.rings import ring

    T, S = sp.symbols("T S")
    domain = QQ.poly_ring(T, order="grlex").poly_ring(S, order="grevlex")
    R = ring("u,v", domain)[0]

    view = PolynomialMap.from_ring(R, R.gens).ring.domain

    assert view == domain
    assert view.ring.order == domain.ring.order
    assert view.dom.ring.order == domain.dom.ring.order


def test_maps_over_differently_ordered_domains_are_unequal() -> None:
    """Was der verlorene Order sonst anrichtete: zwei Abbildungen ueber
    verschiedenen Domains verglichen sich gleich."""
    from sympy.polys.domains import QQ
    from sympy.polys.rings import ring

    T = sp.Symbol("T")
    graded = ring("u,v", QQ.poly_ring(T, order="grlex"))[0]
    lexical = ring("u,v", QQ.poly_ring(T))[0]

    assert PolynomialMap.from_ring(graded, graded.gens) != PolynomialMap.from_ring(
        lexical, lexical.gens
    )


def test_older_dense_fraction_fields_are_rejected_too() -> None:
    """Dasselbe fuer ``old_frac_field``, den Bruchkoerper-Zwilling."""
    from sympy.polys.domains import QQ

    from kellermap.polynomial_map import clone_domain

    T = sp.Symbol("T")

    with pytest.raises(ValueError, match="older dense domains"):
        clone_domain(QQ.old_frac_field(T))


def test_older_dense_domains_are_rejected_with_a_readable_message() -> None:
    """``old_poly_ring`` traegt DMP-Koeffizienten statt PolyElement.

    Ohne diese Pruefung scheiterte ``from_ring`` an einer ``CoercionFailed``
    tief in SymPy, die nichts darueber sagte, was zu tun ist.
    """
    from sympy.polys.domains import QQ
    from sympy.polys.rings import ring

    T = sp.Symbol("T")
    R = ring("u,v", QQ.old_poly_ring(T))[0]

    with pytest.raises(ValueError, match="older dense domains"):
        PolynomialMap.from_ring(R, R.gens)


# --------------------------------------------------------------------------
# reordered: Darstellung, nicht Wert
# --------------------------------------------------------------------------


@pytest.fixture
def spread() -> PolynomialMap:
    """Drei Variablen, damit eine Permutation mehr als ein Tausch sein kann."""
    x, y, z = sp.symbols("x y z")
    return PolynomialMap((x, y, z), (x + y**2 * z, y + z**3, z))


def test_reordered_permutes_variables_and_components_together(
    spread: PolynomialMap,
) -> None:
    """Koordinate ``i`` traegt ``variables[i]`` und die Komponente dazu.

    Wuerde nur die Variablenliste umsortiert, waere das Ergebnis eine andere
    Abbildung. Der Test haelt beide Listen gegeneinander.
    """
    x, y, z = spread.variables

    moved = spread.reordered((z, x, y))

    assert moved.variables == (z, x, y)
    assert moved.components == (z, x + y**2 * z, y + z**3)


def test_reordering_changes_no_value(spread: PolynomialMap) -> None:
    """Grad, Ordnung, Filtrationsgrad und Determinante ueberleben.

    Die Jacobi-Matrix wird in Zeilen und Spalten gleich permutiert, also
    aendert sich ihre Determinante nicht.
    """
    x, y, z = spread.variables

    moved = spread.reordered((y, z, x))

    assert moved.degree() == spread.degree()
    assert moved.order() == spread.order()
    assert moved.filtration_degree() == spread.filtration_degree()
    assert moved.determinant() == spread.determinant()


def test_the_round_trip_returns_the_original(spread: PolynomialMap) -> None:
    x, y, z = spread.variables

    assert spread.reordered((z, y, x)).reordered((x, y, z)) == spread


def test_the_identity_order_is_the_map_itself(spread: PolynomialMap) -> None:
    """Kein Aufwand fuer den haeufigsten Fall, und keine neue Identitaet."""
    assert spread.reordered(spread.variables) is spread


def test_the_reordered_map_is_not_equal_to_the_original(
    spread: PolynomialMap,
) -> None:
    """Genau deshalb gibt es die Methode.

    Gleichheit vergleicht die Variablen als geordnetes Tupel. Zwei
    Darstellungen derselben Abbildung sind also ungleich, solange eine von
    beiden nicht umgeschrieben wird.
    """
    x, y, z = spread.variables

    assert spread.reordered((y, x, z)) != spread


def test_reordering_carries_the_carriers_along() -> None:
    """Traegerindizes sind Positionen und wandern mit der Permutation."""
    x, y, z = sp.symbols("x y z")
    mixed = PolynomialMap((x, y, z), (x**2, y + z**3, z))

    assert mixed.carrier_indices == (1, 2)
    assert mixed.reordered((z, x, y)).carrier_indices == (0, 2)


def test_a_composite_domain_survives_the_reordering() -> None:
    """Die Koeffizienten sind selbst Polynome und werden mitgenommen."""
    x, y = sp.symbols("x y")
    T = sp.Symbol("T")
    parametric = PolynomialMap((x, y), (x + T * y**2, y))

    moved = parametric.reordered((y, x))

    assert moved.ring.domain == parametric.ring.domain
    assert moved.components == (y, T * y**2 + x)


def test_the_reordered_map_shares_no_ring_with_the_original(
    spread: PolynomialMap,
) -> None:
    """Wie ueberall sonst: der neue Ring ist ein Klon, kein geteiltes Objekt."""
    moved = spread.reordered(
        (spread.variables[1], spread.variables[0], spread.variables[2])
    )

    assert moved.ring is not spread.ring
    assert moved.ring.gens[0] is not spread.ring.gens[1]


@pytest.mark.parametrize(
    "wrong",
    [
        (),
        ("x", "y", "z"),
    ],
)
def test_a_non_permutation_is_refused(spread: PolynomialMap, wrong: tuple) -> None:
    with pytest.raises(ValueError, match="not a permutation"):
        spread.reordered(wrong)


def test_a_repeated_variable_is_refused(spread: PolynomialMap) -> None:
    """Gleiche Laenge, gleiche Menge -- aber eine Variable fehlt."""
    x, y, _ = spread.variables

    with pytest.raises(ValueError, match="not a permutation"):
        spread.reordered((x, y, x))


def test_a_foreign_variable_is_refused(spread: PolynomialMap) -> None:
    x, y, _ = spread.variables

    with pytest.raises(ValueError, match="not a permutation"):
        spread.reordered((x, y, sp.Symbol("w")))


# --------------------------------------------------------------------------
# identity: ein Objekt, das nicht zweimal dastehen sollte
# --------------------------------------------------------------------------


def test_the_identity_is_the_identity() -> None:
    x, y, z = sp.symbols("x y z")

    built = PolynomialMap.identity((x, y, z))

    assert built == PolynomialMap((x, y, z), (x, y, z))
    assert built.components == (x, y, z)
    assert built.determinant() == 1
    assert built.degree() == 1


def test_the_identity_takes_any_iterable() -> None:
    """Wie ``PolynomialMap`` selbst; ein Generator wird einmal ausgelesen."""
    x, y = sp.symbols("x y")

    assert PolynomialMap.identity(v for v in (x, y)) == PolynomialMap.identity((x, y))


def test_the_identity_composes_to_nothing() -> None:
    x, y = sp.symbols("x y")
    other = PolynomialMap((x, y), (x + y**2, y))

    assert other.compose(PolynomialMap.identity((x, y))) == other
    assert PolynomialMap.identity((x, y)).compose(other) == other


def test_the_identity_refuses_what_the_constructor_refuses() -> None:
    """Kein zweiter Pruefpfad: der Konstruktor entscheidet."""
    with pytest.raises(ValueError):
        PolynomialMap.identity(())
