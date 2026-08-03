"""Der lineare Teil: GL_n(k) als geordnetes Produkt von Gauss-Operationen.

Der inhaltliche Kern dieser Datei ist die Unterscheidung, die dem Modul seinen
Zweck gibt: eine Transvektion ist elementar im Sinne von BCW, eine
Vertauschung und eine Streckung sind es nicht. Der Rest prueft, dass die
Faktorisierung wirklich die Matrix reproduziert und dass ``apply_to`` dasselbe
tut wie die Komposition ueber ``PolynomialMap``.

Am Ende steht die Normalisierung von Alpoeges Abbildung, an der sich beides
zeigt: die Faktorisierung besteht aus genau einer Vertauschung und einer
Streckung, und ihre Determinante -1/2 macht die Keller-Determinante -2 zu 1.
"""

import pytest
import sympy as sp

from kellermap import ElementaryFactor, PolynomialMap
from kellermap.linear import (
    Dilation,
    LinearAutomorphism,
    Transposition,
    Transvection,
    field_ring,
    over_field,
)

x, y, z = sp.symbols("x y z")

QUADRATIC = PolynomialMap((x, y, z), (x**2, y, z))


@pytest.fixture
def ring() -> object:
    return over_field(QUADRATIC).ring


@pytest.fixture
def F() -> PolynomialMap:  # noqa: N802
    return over_field(QUADRATIC)


# --------------------------------------------------------------------------
# Was elementar ist und was nicht
# --------------------------------------------------------------------------


def test_a_transvection_is_elementary(ring: object) -> None:
    """P = a * X_source ist frei von X_index, also ein ElementaryFactor."""
    shear = Transvection(ring, 0, 1, 3)

    assert shear.is_elementary
    assert shear.determinant() == 1
    assert shear.as_elementary_factor() == ElementaryFactor(ring, 0, 3 * y)


def test_a_transvection_lies_in_EA0_and_not_in_EA1(ring: object) -> None:  # noqa: N802
    """Der Linearteil ist genau der Grund, weshalb EA^0 in BCW vorkommt."""
    factor = Transvection(ring, 0, 1, 3).as_elementary_factor()

    assert factor.is_in_EA(0)
    assert not factor.is_in_EA(1)


def test_a_transposition_is_not_elementary(ring: object) -> None:
    """Zwei bewegte Komponenten, und Determinante -1."""
    swap = Transposition(ring, 0, 2)

    assert not swap.is_elementary
    assert swap.determinant() == -1


def test_a_dilation_is_not_elementary(ring: object) -> None:
    """Die Verschiebung (a - 1) * X_index haengt von X_index ab."""
    scaling = Dilation(ring, 0, sp.Rational(1, 2))

    assert not scaling.is_elementary
    assert scaling.determinant() == sp.Rational(1, 2)


def test_a_dilation_is_rejected_by_ElementaryFactor(ring: object) -> None:  # noqa: N802
    """Gegenprobe: die Streckung kaeme durch die Pruefung von 0.1 nicht durch."""
    with pytest.raises(ValueError, match="must not involve"):
        ElementaryFactor(ring, 0, -sp.Rational(1, 2) * x)


# --------------------------------------------------------------------------
# Die einzelnen Faktoren
# --------------------------------------------------------------------------


def test_a_transvection_reports_its_two_coordinates(ring: object) -> None:
    shear = Transvection(ring, 0, 1, 3)

    assert (shear.index, shear.source) == (0, 1)
    assert "Transvection(index=0, source=1" in repr(shear)


def test_transvections_compare_by_content(ring: object) -> None:
    left = Transvection(ring, 0, 1, 3)

    assert left == Transvection(ring, 0, 1, 3)
    assert hash(left) == hash(Transvection(ring, 0, 1, 3))
    assert left != Transvection(ring, 0, 1, 4)
    assert left != object()


def test_the_other_factors_reject_foreign_types(ring: object) -> None:
    assert Transposition(ring, 0, 1) != object()
    assert Dilation(ring, 0, 2) != object()


def test_the_identity_carries_no_dimension() -> None:
    with pytest.raises(ValueError, match="carries no dimension"):
        _ = LinearAutomorphism.identity().dimension


def test_composition_across_rings_is_refused(ring: object) -> None:
    other = over_field(PolynomialMap(sp.symbols("u v w"), sp.symbols("u v w"))).ring
    left = LinearAutomorphism([Transposition(ring, 0, 1)])
    right = LinearAutomorphism([Transposition(other, 0, 1)])

    with pytest.raises(ValueError, match="different rings"):
        left.compose(right)


def test_an_automorphism_names_its_factors(ring: object) -> None:
    assert "LinearAutomorphism(factors=" in repr(
        LinearAutomorphism([Dilation(ring, 0, 2)])
    )


def test_transvection_needs_two_coordinates(ring: object) -> None:
    with pytest.raises(ValueError, match="two distinct coordinates"):
        Transvection(ring, 1, 1, 1)


def test_transposition_needs_two_coordinates(ring: object) -> None:
    with pytest.raises(ValueError, match="two distinct coordinates"):
        Transposition(ring, 1, 1)


def test_transposition_is_an_involution(ring: object) -> None:
    swap = Transposition(ring, 0, 2)

    assert swap.inverse() == swap
    assert swap.indices == (0, 2)
    assert Transposition(ring, 2, 0) == swap


def test_dilation_by_zero_is_rejected(ring: object) -> None:
    with pytest.raises(ValueError, match="not invertible"):
        Dilation(ring, 0, 0)


def test_dilation_needs_a_unit() -> None:
    """Ueber ZZ ist 2 keine Einheit; die Meldung nennt den Ausweg."""
    with pytest.raises(ValueError, match="over_field"):
        Dilation(QUADRATIC.ring, 0, 2)


def test_index_out_of_range(ring: object) -> None:
    with pytest.raises(ValueError, match="out of range"):
        Transvection(ring, 3, 0, 1)


def test_index_must_be_an_integer(ring: object) -> None:
    with pytest.raises(TypeError, match="must be an integer"):
        Dilation(ring, True, 1)


@pytest.mark.parametrize(
    "factor_of",
    [
        lambda r: Transvection(r, 0, 1, 3),
        lambda r: Transposition(r, 0, 2),
        lambda r: Dilation(r, 1, sp.Rational(-1, 3)),
    ],
)
def test_inverse_undoes_the_factor(factor_of, ring: object) -> None:  # type: ignore[no-untyped-def]
    """Auf Matrixebene und auf Abbildungsebene."""
    factor = factor_of(ring)
    identity = PolynomialMap.from_ring(ring, ring.gens)

    assert sp.Matrix(factor.matrix()) * sp.Matrix(factor.inverse().matrix()) == sp.eye(
        3
    )
    assert factor.inverse().apply_to(factor.to_polynomial_map()) == identity


@pytest.mark.parametrize(
    "factor_of",
    [
        lambda r: Transvection(r, 0, 1, 3),
        lambda r: Transposition(r, 0, 2),
        lambda r: Dilation(r, 1, sp.Rational(-1, 3)),
    ],
)
def test_apply_to_agrees_with_composition(factor_of, F: PolynomialMap) -> None:  # type: ignore[no-untyped-def] # noqa: N803
    """apply_to ist eine Abkuerzung, kein anderer Begriff von Komposition."""
    factor = factor_of(F.ring)

    assert factor.apply_to(F) == factor.to_polynomial_map().compose(F)


def test_a_factor_rejects_a_foreign_map(ring: object) -> None:
    other = PolynomialMap(sp.symbols("u v w"), sp.symbols("u v w"))

    with pytest.raises(ValueError, match="different rings"):
        Transposition(ring, 0, 1).apply_to(other)


def test_matrices_act_on_the_components(F: PolynomialMap) -> None:
    """Linkskomposition ist Matrix mal Komponentenvektor, ohne Substitution."""
    factor = Transvection(F.ring, 0, 1, 3)
    expected = sp.Matrix(factor.matrix()) * sp.Matrix(F.components)

    assert list(factor.apply_to(F).components) == list(expected)


# --------------------------------------------------------------------------
# factorize
# --------------------------------------------------------------------------

CASES = [
    sp.Matrix([[1, 0, 0], [0, 1, 0], [0, 0, 1]]),
    sp.Matrix([[0, 0, 1], [0, 1, 0], [1, 0, 0]]),
    sp.Matrix([[0, 0, sp.Rational(1, 2)], [0, 1, 0], [1, 0, 0]]),
    sp.Matrix([[1, 2, 3], [4, 5, 6], [7, 8, 10]]),
    sp.Matrix([[2, 0, 0], [0, sp.Rational(-1, 3), 0], [0, 0, 5]]),
]


@pytest.mark.parametrize("matrix", CASES)
def test_factorize_reproduces_the_matrix(matrix: sp.Matrix, ring: object) -> None:
    factored = LinearAutomorphism.factorize(ring, matrix)

    assert sp.Matrix(factored.matrix(ring)) == matrix


@pytest.mark.parametrize("matrix", CASES)
def test_factorize_reproduces_the_determinant(matrix: sp.Matrix, ring: object) -> None:
    """Ohne die Matrix zu bilden: das Produkt der Faktordeterminanten."""
    factored = LinearAutomorphism.factorize(ring, matrix)

    assert factored.determinant() == matrix.det()


@pytest.mark.parametrize("matrix", CASES)
def test_factorize_gives_an_invertible_map(matrix: sp.Matrix, ring: object) -> None:
    factored = LinearAutomorphism.factorize(ring, matrix)
    identity = PolynomialMap.from_ring(ring, ring.gens)

    assert factored.inverse().apply_to(factored.to_polynomial_map(ring)) == identity


def test_factorize_rejects_a_singular_matrix(ring: object) -> None:
    with pytest.raises(ValueError, match="singular"):
        LinearAutomorphism.factorize(ring, sp.Matrix([[1, 0, 0], [2, 0, 0], [0, 0, 1]]))


def test_factorize_rejects_the_wrong_shape(ring: object) -> None:
    with pytest.raises(ValueError, match="3x3"):
        LinearAutomorphism.factorize(ring, sp.eye(2))


def test_factorize_needs_a_field() -> None:
    """Ueber ZZ fehlt der Kehrwert; die Meldung nennt over_field."""
    with pytest.raises(ValueError, match="over_field"):
        LinearAutomorphism.factorize(QUADRATIC.ring, sp.diag(2, 1, 1))


def test_the_identity_factors_into_nothing(ring: object) -> None:
    factored = LinearAutomorphism.factorize(ring, sp.eye(3))

    assert len(factored) == 0
    assert sp.Matrix(factored.matrix(ring)) == sp.eye(3)

    with pytest.raises(ValueError, match="needs a ring"):
        factored.matrix()


# --------------------------------------------------------------------------
# Gruppenstruktur
# --------------------------------------------------------------------------


def test_the_empty_product_carries_no_ring() -> None:
    with pytest.raises(ValueError, match="carries no ring"):
        _ = LinearAutomorphism.identity().ring


def test_the_identity_needs_a_ring_to_become_a_map(ring: object) -> None:
    identity = PolynomialMap.from_ring(ring, ring.gens)

    assert LinearAutomorphism.identity().to_polynomial_map(ring) == identity

    with pytest.raises(ValueError, match="needs a ring"):
        LinearAutomorphism.identity().to_polynomial_map()


def test_composition_concatenates(ring: object) -> None:
    left = LinearAutomorphism([Transposition(ring, 0, 1)])
    right = LinearAutomorphism([Dilation(ring, 2, 3)])

    assert left.compose(right).factors == left.factors + right.factors
    assert sp.Matrix(left.compose(right).matrix()) == sp.Matrix(
        left.matrix()
    ) * sp.Matrix(right.matrix())


def test_factors_must_share_a_ring(ring: object) -> None:
    other = over_field(PolynomialMap(sp.symbols("u v w"), sp.symbols("u v w"))).ring

    with pytest.raises(ValueError, match="same ring"):
        LinearAutomorphism([Transposition(ring, 0, 1), Transposition(other, 0, 1)])


def test_factors_must_be_linear_factors(ring: object) -> None:
    with pytest.raises(TypeError, match="LinearFactor"):
        LinearAutomorphism([ElementaryFactor(ring, 0, y)])


def test_is_elementary_is_a_property_of_the_factorization(ring: object) -> None:
    """Hinreichend, nicht charakterisierend.

    Zwei gleiche Vertauschungen sind die Identitaet und liegen damit in
    EA_n(k), obwohl kein Faktor elementar ist. Die Eigenschaft berichtet ueber
    die vorgelegte Faktorisierung, nicht ueber das Element.
    """
    swap = Transposition(ring, 0, 1)
    twice = LinearAutomorphism([swap, swap])

    assert not twice.is_elementary
    assert sp.Matrix(twice.matrix()) == sp.eye(3)


def test_two_factorizations_of_one_matrix_are_different_objects(
    ring: object,
) -> None:
    """Wie bei ElementaryAutomorphism: die Faktorisierung ist das Zertifikat."""
    swap = Transposition(ring, 0, 1)
    once = LinearAutomorphism([swap])
    thrice = LinearAutomorphism([swap, swap, swap])

    assert sp.Matrix(once.matrix()) == sp.Matrix(thrice.matrix())
    assert once != thrice


def test_equality_and_hash(ring: object) -> None:
    left = LinearAutomorphism([Dilation(ring, 0, 2)])
    right = LinearAutomorphism([Dilation(ring, 0, 2)])

    assert left == right
    assert hash(left) == hash(right)
    assert left != object()


# --------------------------------------------------------------------------
# over_field
# --------------------------------------------------------------------------


def test_over_field_widens_the_domain() -> None:
    assert QUADRATIC.ring.domain.is_Field is False
    assert over_field(QUADRATIC).ring.domain.is_Field is True


def test_over_field_keeps_the_map() -> None:
    widened = over_field(QUADRATIC)

    assert widened.components == QUADRATIC.components
    assert widened.determinant() == QUADRATIC.determinant()


def test_field_ring_keeps_the_generators() -> None:
    assert field_ring(QUADRATIC.ring).symbols == QUADRATIC.ring.symbols


def test_over_field_is_idempotent() -> None:
    once = over_field(QUADRATIC)

    assert over_field(once) == once


# --------------------------------------------------------------------------
# Regression: die Normalisierung von Alpoeges Abbildung
# --------------------------------------------------------------------------

ALPOEGE_VARIABLES = sp.symbols("x1 x2 x3")
_1, _2, _3 = ALPOEGE_VARIABLES

ALPOEGE = PolynomialMap(
    ALPOEGE_VARIABLES,
    (
        (1 + _1 * _2) ** 3 * _3 + _2**2 * (1 + _1 * _2) * (4 + 3 * _1 * _2),
        _2 + 3 * _1 * (1 + _1 * _2) ** 2 * _3 + 3 * _1 * _2**2 * (4 + 3 * _1 * _2),
        2 * _1 - 3 * _1**2 * _2 - _1**3 * _3,
    ),
)


@pytest.fixture(scope="module")
def normalization() -> LinearAutomorphism:
    """L^-1 zu L = J(F)(0), faktorisiert."""
    F = over_field(ALPOEGE)
    linear_part = sp.Matrix(
        F.jacobian().xreplace({v: sp.Integer(0) for v in F.variables})
    )

    return LinearAutomorphism.factorize(F.ring, linear_part.inv())


def test_the_normalization_is_a_transposition_and_a_dilation(
    normalization: LinearAutomorphism,
) -> None:
    """Genau die beiden Operationen der Handrechnung, in dieser Reihenfolge."""
    swap, scaling = normalization.factors

    assert isinstance(swap, Transposition)
    assert swap.indices == (0, 2)
    assert isinstance(scaling, Dilation)
    assert scaling.index == 2
    assert scaling.coefficient == sp.Rational(1, 2)


def test_the_normalization_is_not_elementary(
    normalization: LinearAutomorphism,
) -> None:
    """Das kuerzeste Argument braucht die Faktorisierung gar nicht.

    Jedes Element von EA_n(k) hat Determinante 1. Diese hier hat -1/2, liegt
    also in keiner Faktorisierung in EA_3(k).
    """
    assert normalization.determinant() == sp.Rational(-1, 2)
    assert not normalization.is_elementary


def test_the_normalization_turns_the_determinant_into_one(
    normalization: LinearAutomorphism,
) -> None:
    """Warum BCW17 Determinante 1 hat und Alpoege -2."""
    F = over_field(ALPOEGE)

    assert F.determinant() == -2
    assert normalization.apply_to(F).determinant() == 1


def test_the_normalization_reaches_MA1(  # noqa: N802
    normalization: LinearAutomorphism,
) -> None:
    """Die Voraussetzung von Proposition (3.1)."""
    F = over_field(ALPOEGE)

    assert not F.is_in_MA(1)
    assert normalization.apply_to(F).is_in_MA(1)


def test_the_normalization_is_reversible(
    normalization: LinearAutomorphism,
) -> None:
    F = over_field(ALPOEGE)

    assert normalization.inverse().apply_to(normalization.apply_to(F)) == F


def test_the_normalization_moves_only_the_image(
    normalization: LinearAutomorphism,
) -> None:
    """Linkskomposition laesst jedes Urbild, wo es war.

    Deshalb tragen die BCW17-Punkte in ihren ersten drei Koordinaten woertlich
    Alpoeges Punkte, waehrend das Bild von (-1/4, 0, 0) nach (0, 0, -1/4)
    wandert.
    """
    F = over_field(ALPOEGE)
    normalized = normalization.apply_to(F)
    points = (
        (0, 0, sp.Rational(-1, 4)),
        (1, sp.Rational(-3, 2), sp.Rational(13, 2)),
        (-1, sp.Rational(3, 2), sp.Rational(13, 2)),
    )

    images = {tuple(sp.expand(e) for e in normalized(*point)) for point in points}

    assert images == {(sp.Integer(0), sp.Integer(0), sp.Rational(-1, 4))}
