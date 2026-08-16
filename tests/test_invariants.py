"""The invariants the BCW reduction rests on.

Unlike the smoke tests, these do not check individual methods but the
identities the certificate later rests on: that composition and stabilisation
control the Jacobian determinant, that the filtration MA^d is a submonoid, and
that formulas (1) to (3) of Proposition (3.1) do what the paper claims.

Page references are to Bass, Connell, Wright, Bull. AMS 1982.
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

# A naming policy of its own for the stabilisation variables.
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
    """Equality of polynomials and not of syntax."""
    return bool(sp.expand(a - b) == 0)


# --------------------------------------------------------------------------
# Determinants under composition
# --------------------------------------------------------------------------


@pytest.mark.parametrize(("F", "G"), PAIRS)
def test_chain_rule_for_determinants(F: PolynomialMap, G: PolynomialMap) -> None:
    """det J(F o G) = det J(F)(G) * det J(G).

    This is the identity the whole certificate rests on: it guarantees that
    factors from EA do not change the determinant.
    """
    substitution = dict(zip(F.variables, G.components, strict=True))

    expected = F.determinant().xreplace(substitution) * G.determinant()

    assert vanishes(F.compose(G).determinant(), expected)


def test_elementary_automorphisms_have_determinant_one() -> None:
    """Why the determinant check in verify() is redundant.

    G and H of Proposition (3.1), formula (1), are elementary or products of
    elementary automorphisms. Their Jacobian matrix is the identity but for one
    row, so the determinant is 1.
    """
    X1, X2, X3, X4 = sp.symbols("X1 X2 X3 X4")

    G = examples.product_shear()
    H = examples.paired_shear()

    assert G.determinant() == 1
    assert H.determinant() == 1


# --------------------------------------------------------------------------
# Stabilisation, BCW p. 304
# --------------------------------------------------------------------------


def test_stabilization_jacobian_is_block_diagonal() -> None:
    """J(F^[m]) = diag(J(F), I_m), verbatim from the paper."""
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


# The new components X_{n+i} are monomials of degree exactly 1. Degree and
# order are therefore not preserved but truncated towards 1:
#
#     deg(F^[m]) = max(deg F, 1),    ord(F^[m]) = min(ord F, 1)   for m > 0.
#
# What is preserved is the degree and order of the displacement, and with them
# the filtration degree, and BCW rest on nothing else.

DEGREE_AND_ORDER_CASES = [
    LINEAR,
    TRIANGULAR,
    KELLER,
    QUADRATIC,
    # Order 2: stabilisation lowers it to 1.
    PolynomialMap((x, y), (x**2, y**2)),
    # Degree 0: stabilisation raises it to 1.
    PolynomialMap((x, y), (sp.Integer(5), sp.Integer(7))),
]


@pytest.mark.parametrize("F", DEGREE_AND_ORDER_CASES)
def test_stabilization_truncates_degree_and_order_at_one(F: PolynomialMap) -> None:
    """Degree and order under stabilisation, exactly.

    An earlier version claimed preservation and checked it on four maps that
    all had degree >= 1 and order <= 1, that is on exactly the cases in which
    the truncation does not show. The two additional cases above close that
    gap.
    """
    extended = F.extend(2)

    assert extended.degree() == max(F.degree(), 1)
    assert extended.order() == min(F.order(), 1)


@pytest.mark.parametrize("F", DEGREE_AND_ORDER_CASES)
def test_stabilization_preserves_the_displacement(F: PolynomialMap) -> None:
    """What is really preserved, and what BCW need.

    F^[m] - X differs from F - X by m zero components only, so the degree and
    order of the displacement agree. The filtration degree follows.
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

    ``extend`` reaches the identity through three separate calls, and it holds
    only if all three hand out the same names. This used to stand here as a
    comment and rested on maps of equal dimension agreeing by accident. The
    factory is passed through now: the precondition is in the test instead of
    in a footnote.

    ``CARRIER`` is deliberately not the default factory. Agreeing with its
    names by accident would make the test say nothing again.
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
# The filtration MA^d as a submonoid
# --------------------------------------------------------------------------


def test_MA_is_closed_under_composition() -> None:  # noqa: N802
    """MA^d is a submonoid.

    In Proposition (3.1) BCW compose elements of EA^1 repeatedly, which is
    admissible only because the filtration level is preserved.
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
# Degree and order
# --------------------------------------------------------------------------


@pytest.mark.parametrize(("F", "G"), PAIRS)
def test_degree_is_submultiplicative(F: PolynomialMap, G: PolynomialMap) -> None:
    assert F.compose(G).degree() <= F.degree() * G.degree()


def test_homogeneous_map_has_equal_degree_and_order() -> None:
    """The reduction target of Corollary (2.2) is cubic homogeneous.

    With the means at hand, homogeneity can be expressed as degree == order.
    That is the test a later is_homogeneous() has to satisfy.
    """
    cubic = PolynomialMap((x, y), (x**3, x**2 * y))

    assert cubic.degree() == cubic.order() == 3
    assert TRIANGULAR.degree() != TRIANGULAR.order()


# --------------------------------------------------------------------------
# Proposition (3.1), formulas (1) to (3), as an executable identity
# --------------------------------------------------------------------------

# F = X1 + X2^4 has degree d = 4. The leading monomial is M = X2^4 with a = 1,
# and aM = P*Q with P = Q = X2^2, both of degree <= d - 2 = 2.

X1, X2, X3, X4 = sp.symbols("X1 X2 X3 X4")

BCW_F = PolynomialMap((X1, X2), (X1 + X2**4, X2))
BCW_P = X2**2
BCW_Q = X2**2

BCW_G = examples.product_shear()
BCW_H = PolynomialMap((X1, X2, X3, X4), (X1, X2, X3 + BCW_P, X4 + BCW_Q))


@pytest.fixture
def reduced() -> PolynomialMap:
    """F' = G o F^[2] o H of formula (1)."""
    return BCW_G.compose(BCW_F.extend(2).compose(BCW_H))


def test_bcw_step_matches_formula_two_and_three(reduced: PolynomialMap) -> None:
    """F' = (F1', F2, X3 + P, X4 + Q) mit F1' = (F1 - aM) - X3*Q - P*X4 - X3*X4.

    This is the identity a later BCWStep has to reproduce.
    """
    F1, F2 = BCW_F.components
    aM = X2**4

    expected_F1 = (F1 - aM) - X3 * BCW_Q - BCW_P * X4 - X3 * X4
    expected = (expected_F1, F2, X3 + BCW_P, X4 + BCW_Q)

    assert all(
        vanishes(a, b) for a, b in zip(reduced.components, expected, strict=True)
    )


def test_bcw_step_lowers_the_degree(reduced: PolynomialMap) -> None:
    """The purpose of the step: deg(F') < deg(F), here 4 -> 3."""
    assert BCW_F.degree() == 4
    assert reduced.degree() == 3


def test_bcw_step_preserves_the_determinant(reduced: PolynomialMap) -> None:
    """G and H lie in EA, so the step does not change the determinant."""
    assert BCW_F.determinant() == 1
    assert reduced.determinant() == 1


def test_bcw_step_factors_lie_in_EA1() -> None:  # noqa: N802
    """First part of Proposition (3.1): deg P, deg Q >= 2, so G, H in EA^1."""
    assert sp.Poly(BCW_P, X1, X2).total_degree() >= 2
    assert sp.Poly(BCW_Q, X1, X2).total_degree() >= 2

    assert BCW_G.is_in_MA(1)
    assert BCW_H.is_in_MA(1)


@pytest.mark.parametrize("F", [LINEAR, TRIANGULAR, KELLER, QUADRATIC])
@pytest.mark.parametrize(("m", "ell"), [(1, 1), (2, 2), (1, 3)])
def test_stabilization_composes(F: PolynomialMap, m: int, ell: int) -> None:
    """(F^[m])^[l] = F^[m+l], BCW S. 304.

    Together with the monoid homomorphism this is the second promise a
    reduction that stabilises step by step needs: it has to arrive where a
    single stabilisation arrives.
    """
    assert F.extend(m, CARRIER).extend(ell, CARRIER) == F.extend(m + ell, CARRIER)


# --------------------------------------------------------------------------
# Formula (1) with elementary automorphisms instead of raw maps
# --------------------------------------------------------------------------


def test_bcw_step_can_be_built_from_elementary_factors(
    reduced: PolynomialMap,
) -> None:
    """The same reduction, from G and H as group elements.

    Above, G and H are written down as ordinary PolynomialMaps and their
    invertibility is merely asserted. Here they carry their factorization with
    them and the step can be undone. That is the form in which a BCWStep has to
    record them.
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

    # The step is invertible without anything being solved for.
    undone = G.inverse().apply_to(reduced).compose(H.inverse().to_polynomial_map())

    assert undone == stabilized
