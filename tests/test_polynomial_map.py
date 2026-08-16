import math

import pytest
import sympy as sp

from kellermap import PolynomialMap, examples


@pytest.fixture
def F() -> PolynomialMap:
    """A simple linear map with Jacobian determinant -2."""
    x, y = sp.symbols("x y")
    return PolynomialMap(variables=(x, y), components=(x + y, x - y))


# --------------------------------------------------------------------------
# Smoke tests: every public method is called at least once.
# --------------------------------------------------------------------------


def test_dimension(F: PolynomialMap) -> None:
    assert F.dimension == 2


def test_matrix(F: PolynomialMap) -> None:
    x, y = F.variables
    assert F.matrix == sp.Matrix([x + y, x - y])


def test_matrix_is_cached(F: PolynomialMap) -> None:
    """Regression: cached_property needs a __dict__, so no slots=True."""
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
    """Regression: subs(dict) substitutes sequentially, xreplace at once."""
    x, y = F.variables
    swap = PolynomialMap((x, y), (y, x))

    assert F.compose(swap).components == (y + x, y - x)


def test_call_is_simultaneous(F: PolynomialMap) -> None:
    """Regression: the same trap as in compose."""
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
    """frozen=True takes the part that slots=True cannot play here."""
    from dataclasses import FrozenInstanceError

    with pytest.raises(FrozenInstanceError):
        F.variables = ()  # type: ignore[misc]


def test_hashable(F: PolynomialMap) -> None:
    assert len({F, F}) == 1


# --------------------------------------------------------------------------
# Equality and hash
#
# eq=False in the dataclass decorator: __eq__ and __hash__ are written by hand
# and therefore have to be checked on their own. len({F, F}) == 1 tests
# identity only and not equality.
# --------------------------------------------------------------------------


def test_equal_maps_built_separately_compare_equal(F: PolynomialMap) -> None:
    x, y = F.variables
    twin = examples.sum_and_difference()

    assert twin is not F
    assert twin == F


def test_equality_is_polynomial_not_syntactic(F: PolynomialMap) -> None:
    """The normalisation the PolyRing performs can be trusted."""
    x, y = F.variables
    unexpanded = PolynomialMap((x, y), ((x + y) * (x - y) / (x - y), x - y))

    assert unexpanded == F


def test_maps_differing_in_a_component_are_unequal(F: PolynomialMap) -> None:
    x, y = F.variables

    assert PolynomialMap((x, y), (x + y, x + y)) != F


def test_maps_differing_in_the_variables_are_unequal() -> None:
    """The same components, other carrier variables: different maps."""
    x, y, u, v = sp.symbols("x y u v")

    assert PolynomialMap.identity((x, y)) != PolynomialMap.identity((u, v))


def test_variable_order_matters(F: PolynomialMap) -> None:
    """(x, y) and (y, x) generate different rings."""
    x, y = F.variables

    assert PolynomialMap((y, x), (x + y, x - y)) != F


def test_equality_with_a_foreign_type_is_not_implemented(F: PolynomialMap) -> None:
    assert F.__eq__(object()) is NotImplemented
    assert F != object()


def test_equal_maps_share_a_hash(F: PolynomialMap) -> None:
    """The promise __hash__ makes: a == b implies hash(a) == hash(b)."""
    x, y = F.variables
    twin = examples.sum_and_difference()

    assert hash(twin) == hash(F)
    assert len({F, twin}) == 1


# --------------------------------------------------------------------------
# Validation
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
    F = PolynomialMap.identity((x, y))
    G = PolynomialMap.identity((u, v))
    with pytest.raises(ValueError, match="different variables"):
        F.compose(G)


# --------------------------------------------------------------------------
# Degree and order relative to the map's own variables
# --------------------------------------------------------------------------


def test_degree_ignores_parameters() -> None:
    """Regression: total_degree without generators counts foreign symbols.

    BCW Section 4 computes over k[T], where T is a scalar and not a variable.
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
    identity = PolynomialMap.identity((x, y))

    assert identity.filtration_degree() == math.inf
    assert identity.is_in_MA(17)


# --------------------------------------------------------------------------
# The filtration MA^d of BCW, Proposition (3.1), formula (1)
# --------------------------------------------------------------------------


def test_bcw_G_lies_in_MA1() -> None:
    """G = (X1 - X3*X4, X2, X3, X4) displaces by order 2, so it lies in MA^1."""
    X1, X2, X3, X4 = sp.symbols("X1 X2 X3 X4")
    G = examples.product_shear()

    assert G.filtration_degree() == 1
    assert G.is_in_MA(1)


def test_bcw_H_lies_in_MA1_when_P_and_Q_are_quadratic() -> None:
    """First part of the proof: deg P, deg Q >= 2, so H lies in MA^1."""
    X1, X2, X3, X4 = sp.symbols("X1 X2 X3 X4")
    H = PolynomialMap((X1, X2, X3, X4), (X1, X2, X3 + X1**2, X4 + X2**2))

    assert H.filtration_degree() == 1
    assert H.is_in_MA(1)


def test_bcw_H_lies_only_in_MA0_when_P_is_linear() -> None:
    """The linearisation part: P = X1 has degree 1, so BCW require only EA^0."""
    X1, X2, X3, X4 = sp.symbols("X1 X2 X3 X4")
    H = PolynomialMap((X1, X2, X3, X4), (X1, X2, X3 + X1, X4 + X1 * X2))

    assert H.filtration_degree() == 0
    assert H.is_in_MA(0)
    assert not H.is_in_MA(1)


# --------------------------------------------------------------------------
# A regression test against an example from the literature
# --------------------------------------------------------------------------

# Alpoege's counterexample to the Jacobian conjecture, X post of 20 July 2026.
# The collision is the rational collision Tao recorded.

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
    """The Jacobian determinant is constant and invertible."""
    determinant = alpoege.determinant()

    assert determinant.free_symbols == set()
    assert determinant == -2


def test_alpoege_is_not_injective(alpoege: PolynomialMap) -> None:
    """The substance: three distinct preimages of one point.

    Together with the constant determinant this refutes the Jacobian
    conjecture in dimension 3.
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
    F = examples.parametric_swap()
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
# The determinant strategy: unipotent carrier block and Schur complement
# --------------------------------------------------------------------------

X1, X2, X3, X4 = sp.symbols("X1 X2 X3 X4")

# Candidates for the cross-check: with and without a carrier block, with
# rational and with symbolic coefficients.
DETERMINANT_CASES = [
    PolynomialMap((X1, X2), (X1, X2)),
    PolynomialMap((X1, X2), (X1 + X2, X1 - X2)),
    PolynomialMap((X1, X2), (X1**2, X2)),
    PolynomialMap((X1, X2), (X1 * X2 + 1, X1 - X2**2)),
    PolynomialMap((X1, X2), (X1 + X2**2, X2 + X1**2)),
    PolynomialMap((X1, X2), (sp.Symbol("T") * X1 + X2, X1 - X2)),
    examples.product_shear(),
    examples.paired_shear(),
    PolynomialMap((X1, X2, X3), (X1 + X2 * X3, X2 + X3**2, X3)),
]


@pytest.mark.parametrize("F", DETERMINANT_CASES)
def test_determinant_matches_an_expression_valued_computation(
    F: PolynomialMap,
) -> None:
    """A cross-representation test as ``docs/architecture.md`` requires.

    The reference runs entirely over ``Expr``, through SymPy's own
    ``Matrix.jacobian`` and ``Matrix.det``. It therefore depends on no part of
    this project's ``DomainMatrix`` integration or of the choice of strategy.
    """
    reference = sp.Matrix(F.components).jacobian(sp.Matrix(F.variables)).det()

    assert sp.expand(F.determinant() - reference) == 0


@pytest.mark.parametrize("F", DETERMINANT_CASES)
def test_schur_complement_agrees_with_the_domain_matrix_path(
    F: PolynomialMap,
) -> None:
    """Both strategies have to give the same polynomial."""
    reference = F._determinant_by_domain_matrix(F._jacobian_polynomials)

    assert F.determinant() == reference.as_expr()


def test_elementary_automorphism_is_unipotent_throughout() -> None:
    """The boundary case: the leading block is empty and the determinant
    follows from the structure and not from an expansion."""
    G = examples.product_shear()

    assert G.carrier_indices == (0, 1, 2, 3)
    assert G.determinant() == 1


def test_carrier_requires_a_unit_diagonal_entry() -> None:
    """dF_i/dX_i has to be exactly 1 and not merely constant."""
    F = examples.doubled_shear()

    assert F.carrier_indices == (1,)


def test_carrier_drops_coordinates_on_a_dependency_cycle() -> None:
    """X1 depends on X2 and X2 on X1: the block is not nilpotent.

    The diagonal is 1 twice here, and the detection must not be misled by that,
    otherwise the Neumann series would diverge.
    """
    F = PolynomialMap((X1, X2), (X1 + X2**2, X2 + X1**2))

    assert F.carrier_indices == ()
    assert F.determinant() == 1 - 4 * X1 * X2


def test_carrier_keeps_an_acyclic_chain() -> None:
    """The same diagonal but acyclic: the whole block is usable."""
    F = PolynomialMap((X1, X2), (X1 + X2**2, X2))

    assert F.carrier_indices == (0, 1)
    assert F.determinant() == 1


def test_schur_complement_refuses_a_non_nilpotent_block() -> None:
    """A regression for a real defect.

    A first draft did not check nilpotence but inferred it from the Neumann
    series terminating. With an empty leading block the series terminates at
    once, whatever L looks like, and the empty Schur complement then gave
    determinant 1 for a map of determinant 1 - 4*X1*X2.

    ``carrier_indices`` never hands out such a block, so the case is forced by
    hand here.
    """
    F = PolynomialMap((X1, X2), (X1 + X2**2, X2 + X1**2))

    assert F.carrier_indices == ()
    assert F._schur_complement((0, 1)) is None
    assert F.determinant() == 1 - 4 * X1 * X2


def test_unipotent_block_rejects_a_non_unit_diagonal() -> None:
    """The second half of the precondition: D has to be I + L and not merely
    triangular."""
    F = examples.doubled_shear()

    assert F._is_unipotent_block((1,))
    assert not F._is_unipotent_block((0, 1))
    assert F._schur_complement((0, 1)) is None


# --------------------------------------------------------------------------
# Immutability of the public matrices
# --------------------------------------------------------------------------


def test_matrix_is_immutable(F: PolynomialMap) -> None:
    """A regression for a real defect.

    ``matrix`` is cached. While it was mutable, an assignment from outside
    corrupted every later evaluation: after ``F.matrix[0] = 0``, ``F(1, 2)``
    gave ``[0, -1]`` instead of ``[3, -1]``, although ``components`` was
    untouched.
    """
    with pytest.raises(TypeError):
        F.matrix[0] = sp.Integer(0)  # type: ignore[index]

    assert F(sp.Integer(1), sp.Integer(2)) == sp.Matrix([3, -1])


def test_jacobian_is_immutable(F: PolynomialMap) -> None:
    """No defect here but consistency: the public boundary promises immutable
    SymPy objects."""
    with pytest.raises(TypeError):
        F.jacobian()[0, 0] = sp.Integer(0)  # type: ignore[index]


def test_evaluation_returns_an_immutable_matrix(F: PolynomialMap) -> None:
    result = F(sp.Integer(1), sp.Integer(2))

    assert isinstance(result, sp.ImmutableMatrix)
    assert result == sp.Matrix([3, -1])


def test_mutable_copies_remain_available(F: PolynomialMap) -> None:
    """Whoever needs a mutable matrix gets one, as a copy."""
    copy = sp.Matrix(F.matrix)
    copy[0] = sp.Integer(0)

    assert F.matrix[0] != 0


# --------------------------------------------------------------------------
# Uniqueness of the generators
# --------------------------------------------------------------------------


def test_from_ring_rejects_duplicate_generators() -> None:
    """A PolyRing over (x, x) can be built, and the two generators cannot be
    told apart once they become expressions."""
    from sympy.polys.domains import QQ
    from sympy.polys.rings import ring

    x = sp.Symbol("x")
    R, first, second = ring([x, x], QQ)

    with pytest.raises(ValueError, match="pairwise distinct"):
        PolynomialMap.from_ring(R, (first, second))


def test_duplicate_variables_are_detected_by_name() -> None:
    """Different assumptions, one name: the symbols differ and their
    expressions cannot be told apart."""
    plain = sp.Symbol("x")
    positive = sp.Symbol("x", positive=True)

    assert plain != positive

    with pytest.raises(ValueError, match="pairwise distinct"):
        PolynomialMap((plain, positive), (plain, positive))


# --------------------------------------------------------------------------
# Empty input and invalid rings
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
    """``PolyRing`` accepts a composite expression as a generator."""
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
# Nested defensive copies
# --------------------------------------------------------------------------

# Over k[T] the coefficient of a monomial is itself a PolyElement, so a
# mutable dict again. A shallow copy would share that inner level, which is why
# _copy_polynomial descends recursively.


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
    F = examples.parametric_swap()

    assert str(F.ring.domain) == "ZZ[T]"

    coefficient = _nested_coefficient(F.to_polynomials()[0])
    coefficient[coefficient.ring.zero_monom] = coefficient.ring.domain.one  # type: ignore[index]

    assert F.components == (T * x + y, x)


def test_from_ring_copies_nested_coefficients() -> None:
    """The same level, the other direction: the input may be changed
    afterwards without affecting the map."""
    from sympy.polys.rings import ring

    T = sp.Symbol("T")
    R, a, b = ring("a,b", sp.polys.domains.QQ[T])
    component = T * a + b

    F = PolynomialMap.from_ring(R, (component, a))

    coefficient = _nested_coefficient(component)
    coefficient[coefficient.ring.zero_monom] = coefficient.ring.domain.one  # type: ignore[index]

    assert F.components[0] == T * sp.Symbol("a") + sp.Symbol("b")


def test_fraction_field_coefficients_are_copied() -> None:
    """Over k(T) a coefficient is a FracElement with a mutable numerator and
    denominator.

    A regression for a real defect: the copy descended into PolyElement only.
    Because the one of the domain is a single shared instance, a mutation there
    hit every term with coefficient one, and the map (x/(T+1) + y, x) became
    (x/(T+1), 0).
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
    """The same variables and components, a different coefficient domain."""
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
# The ring is not shared
# --------------------------------------------------------------------------

# PolyRing is not a value object: its gens are PolyElement, so mutable dicts,
# and SymPy reads them in from_expr and ring_new. A caller who got hold of the
# internal ring could change what the map computes, without components
# reporting anything about it.


def test_ring_property_does_not_hand_out_the_internal_ring(
    F: PolynomialMap,
) -> None:
    before = F.displacement().components

    F.ring.gens[0].clear()

    assert F.displacement().components == before


def test_to_polynomials_does_not_leak_the_ring_either(F: PolynomialMap) -> None:
    """A PolyElement carries a reference to its ring, so copies taken from the
    internal ring would hand it straight back out."""
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
    """The isolation must not make the ring useless.

    The clone is equal by value, so it composes and compares like the internal
    one. Otherwise it would be worthless as an argument to ``from_ring`` or to
    a factory.
    """
    view = F.ring

    assert view == F.ring
    assert PolynomialMap.from_ring(view, F.to_polynomials()) == F


# The clone has to be built through PolyRing and not through PolyRing.clone.
# The latter runs through SymPy's cacheit, and cloning a clone returns the same
# object. An isolation resting on it would have no effect for any map from
# from_ring, that is for every result of compose and extend, and no test that
# checks the expression constructor alone would report it.

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
    """The trap, recorded.

    ``PolyRing.clone`` of a clone gives the clone itself. ``clone_ring`` always
    gives an object of its own with generators of its own.
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
# The view is not shared, and neither is the domain
# --------------------------------------------------------------------------


def test_the_view_ring_is_not_cached(F: PolynomialMap) -> None:
    """A regression for a real defect.

    ``_view_ring`` was a ``cached_property``. Every caller therefore got the
    same clone, and one that changed it damaged the view for all that followed:
    ``F.ring`` then gave back the same, already broken ring.
    """
    view = F.ring
    view.gens[0].clear()

    assert F.ring is not view
    assert F.ring.gens[0] != 0
    assert F.ring == view


def test_extension_after_a_mutated_view_is_unaffected(F: PolynomialMap) -> None:
    """The factory is given a fresh ring as well."""
    before = F.extend(1).variables

    F.ring.gens[0].clear()

    assert F.extend(1).variables == before


def test_to_polynomials_binds_each_call_to_its_own_ring(F: PolynomialMap) -> None:
    first, second = F.to_polynomials(), F.to_polynomials()

    assert first[0].ring is not second[0].ring
    # Within one call the components share a ring, because otherwise they
    # could not be computed with each other.
    assert first[0].ring is first[1].ring

    first[0].ring.gens[0].clear()

    assert F.to_polynomials()[0].ring.gens[0] != 0


def test_the_coefficient_domain_is_cloned_too() -> None:
    """A regression for the second leak.

    ``clone_ring`` took the domain over unchanged. After
    ``caller_domain.gens[0].clear()`` the supposedly isolated ring turned
    ``T*u`` into ``0``, silently, because ``components`` still agreed.
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
    """A PolyElement coefficient carries a ring of its own along."""
    from sympy.polys.domains import QQ
    from sympy.polys.rings import PolyElement, ring

    T = sp.Symbol("T")
    R, u, v = ring("u,v", QQ[T])
    G = PolynomialMap.from_ring(R, (T * u + v, u))

    for _, coefficient in G.to_polynomials()[0].iterterms():
        if isinstance(coefficient, PolyElement):
            assert coefficient.ring is not G._ring.domain.ring


def test_extend_rejects_a_boolean() -> None:
    """bool is a subclass of int.

    ``F.extend(True)`` would otherwise be an extension by exactly one variable,
    almost certainly a typing slip and not what anybody meant.
    """
    x, y = sp.symbols("x y")
    F = examples.shear()

    with pytest.raises(TypeError, match="must be an integer"):
        F.extend(True)  # type: ignore[arg-type]


@pytest.mark.parametrize("number", [2.0, "2", None])
def test_extend_rejects_non_integers(number: object) -> None:
    x, y = sp.symbols("x y")
    F = examples.shear()

    with pytest.raises(TypeError, match="must be an integer"):
        F.extend(number)  # type: ignore[arg-type]


# --------------------------------------------------------------------------
# The expression constructor validates the ring that sring builds
# --------------------------------------------------------------------------


def test_a_coefficient_may_not_shadow_a_coordinate() -> None:
    """A regression for a real defect.

    ``sring`` additionally takes a symbol that is already a generator into the
    coefficient domain when it appears with other assumptions, that is under
    the same name as a different object. The expression constructor did not
    check this and ``from_ring`` did. The map looked valid, printed the same
    character for two things in ``components``, and only ``extend()`` failed.
    """
    x, y = sp.Symbol("x"), sp.Symbol("y")
    parameter = sp.Symbol("x", positive=True)

    with pytest.raises(ValueError, match="coefficient indeterminate"):
        PolynomialMap((x, y), (x + parameter * y, y))


def test_a_genuine_parameter_is_still_accepted() -> None:
    """The control: a parameter with a name of its own stays admissible."""
    x, y, T = sp.symbols("x y T")

    F = examples.parametric_swap()

    assert str(F.ring.domain) == "ZZ[T]"


# --------------------------------------------------------------------------
# The monomial order survives cloning
# --------------------------------------------------------------------------

MONOMIAL_ORDERS = ["lex", "grlex", "grevlex"]


@pytest.mark.parametrize("order", MONOMIAL_ORDERS)
def test_cloning_keeps_the_polynomial_ring_order(order: str) -> None:
    """A regression for a real defect.

    ``clone_domain`` rebuilt the domain without its ``order``. A domain built
    with ``grlex`` came back as ``lex``, so the clone was not equal by value to
    the original, against the promise in ``docs/api.md``.
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
    """What the lost order did besides: two maps over different domains
    compared as equal."""
    from sympy.polys.domains import QQ
    from sympy.polys.rings import ring

    T = sp.Symbol("T")
    graded = ring("u,v", QQ.poly_ring(T, order="grlex"))[0]
    lexical = ring("u,v", QQ.poly_ring(T))[0]

    assert PolynomialMap.from_ring(graded, graded.gens) != PolynomialMap.from_ring(
        lexical, lexical.gens
    )


def test_older_dense_fraction_fields_are_rejected_too() -> None:
    """The same for ``old_frac_field``, the fraction field twin."""
    from sympy.polys.domains import QQ

    from kellermap.polynomial_map import clone_domain

    T = sp.Symbol("T")

    with pytest.raises(ValueError, match="older dense domains"):
        clone_domain(QQ.old_frac_field(T))


def test_older_dense_domains_are_rejected_with_a_readable_message() -> None:
    """``old_poly_ring`` carries DMP coefficients rather than PolyElement.

    Without this check ``from_ring`` failed with a ``CoercionFailed`` deep
    inside SymPy which said nothing about what to do.
    """
    from sympy.polys.domains import QQ
    from sympy.polys.rings import ring

    T = sp.Symbol("T")
    R = ring("u,v", QQ.old_poly_ring(T))[0]

    with pytest.raises(ValueError, match="older dense domains"):
        PolynomialMap.from_ring(R, R.gens)


# --------------------------------------------------------------------------
# reordered: presentation, not value
# --------------------------------------------------------------------------


@pytest.fixture
def spread() -> PolynomialMap:
    """Three variables, so that a permutation can be more than one swap."""
    x, y, z = sp.symbols("x y z")
    return PolynomialMap((x, y, z), (x + y**2 * z, y + z**3, z))


def test_reordered_permutes_variables_and_components_together(
    spread: PolynomialMap,
) -> None:
    """Coordinate ``i`` carries ``variables[i]`` and the component with it.

    If only the list of variables were reordered, the result would be a
    different map. The test holds both lists against each other.
    """
    x, y, z = spread.variables

    moved = spread.reordered((z, x, y))

    assert moved.variables == (z, x, y)
    assert moved.components == (z, x + y**2 * z, y + z**3)


def test_reordering_changes_no_value(spread: PolynomialMap) -> None:
    """Degree, order, filtration degree and determinant survive.

    The Jacobian matrix is permuted equally in rows and columns, so its
    determinant does not change.
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
    """No cost for the most common case, and no new identity."""
    assert spread.reordered(spread.variables) is spread


def test_the_reordered_map_is_not_equal_to_the_original(
    spread: PolynomialMap,
) -> None:
    """That is exactly why the method exists.

    Equality compares the variables as an ordered tuple. Two presentations of
    one map are therefore unequal until one of them is rewritten.
    """
    x, y, z = spread.variables

    assert spread.reordered((y, x, z)) != spread


def test_reordering_carries_the_carriers_along() -> None:
    """Carrier indices are positions and move with the permutation."""
    x, y, z = sp.symbols("x y z")
    mixed = PolynomialMap((x, y, z), (x**2, y + z**3, z))

    assert mixed.carrier_indices == (1, 2)
    assert mixed.reordered((z, x, y)).carrier_indices == (0, 2)


def test_a_composite_domain_survives_the_reordering() -> None:
    """The coefficients are polynomials themselves and are carried along."""
    x, y = sp.symbols("x y")
    T = sp.Symbol("T")
    parametric = examples.parametric_shear()

    moved = parametric.reordered((y, x))

    assert moved.ring.domain == parametric.ring.domain
    assert moved.components == (y, T * y**2 + x)


def test_the_reordered_map_shares_no_ring_with_the_original(
    spread: PolynomialMap,
) -> None:
    """As everywhere else: the new ring is a clone and not a shared object."""
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
    """The same length, the same set, and one variable missing."""
    x, y, _ = spread.variables

    with pytest.raises(ValueError, match="not a permutation"):
        spread.reordered((x, y, x))


def test_a_foreign_variable_is_refused(spread: PolynomialMap) -> None:
    x, y, _ = spread.variables

    with pytest.raises(ValueError, match="not a permutation"):
        spread.reordered((x, y, sp.Symbol("w")))


# --------------------------------------------------------------------------
# identity: an object that should not be written out twice
# --------------------------------------------------------------------------


def test_the_identity_is_the_identity() -> None:
    x, y, z = sp.symbols("x y z")

    built = PolynomialMap.identity((x, y, z))

    assert built == PolynomialMap((x, y, z), (x, y, z))
    assert built.components == (x, y, z)
    assert built.determinant() == 1
    assert built.degree() == 1


def test_the_identity_takes_any_iterable() -> None:
    """As ``PolynomialMap`` itself: a generator is read once."""
    x, y = sp.symbols("x y")

    assert PolynomialMap.identity(v for v in (x, y)) == PolynomialMap.identity((x, y))


def test_the_identity_composes_to_nothing() -> None:
    x, y = sp.symbols("x y")
    other = examples.quadratic_shear()

    assert other.compose(PolynomialMap.identity((x, y))) == other
    assert PolynomialMap.identity((x, y)).compose(other) == other


def test_the_identity_refuses_what_the_constructor_refuses() -> None:
    """No second checking path: the constructor decides."""
    with pytest.raises(ValueError):
        PolynomialMap.identity(())
