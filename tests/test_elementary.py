"""Elementary automorphisms and the group EA_n(k).

Page references are to Bass, Connell, Wright, Bull. AMS 1982.
"""

import math

import pytest
import sympy as sp
from sympy.polys.domains import QQ, ZZ
from sympy.polys.rings import ring

from kellermap import ElementaryAutomorphism, ElementaryFactor, PolynomialMap

R, X1, X2, X3, X4 = ring("X1,X2,X3,X4", QQ)

# The same variables as SymPy symbols. ``components`` sits at the expression
# boundary, and the ring elements above are not comparable with it.
x1, x2, x3, x4 = R.symbols


@pytest.fixture
def identity() -> PolynomialMap:
    return PolynomialMap.from_ring(R, R.gens)


# --------------------------------------------------------------------------
# Validation
# --------------------------------------------------------------------------


def test_polynomial_must_not_involve_the_moving_variable() -> None:
    """The condition the inversion formula depends on.

    X_i |-> a X_i + P can be inverted by a^-1 (X_i - P) only when P stays
    unchanged under the substitution.
    """
    with pytest.raises(ValueError, match="must not involve X1"):
        ElementaryFactor(R, 0, X1 * X2)


def test_index_must_be_in_range() -> None:
    with pytest.raises(ValueError, match="out of range"):
        ElementaryFactor(R, 9, R.zero)


def test_polynomial_must_belong_to_the_ring() -> None:
    other = ring("Y1,Y2", QQ)[1]

    with pytest.raises(ValueError, match="belong to the specified ring"):
        ElementaryFactor(R, 0, other)


def test_polynomial_must_be_polynomial() -> None:
    with pytest.raises(ValueError, match="must be a polynomial"):
        ElementaryFactor(R, 0, sp.sin(sp.Symbol("X2")))


@pytest.mark.parametrize("index", [True, 0.5, "0", None])
def test_index_must_be_an_integer(index: object) -> None:
    """``True`` is an int in Python and ``0.5`` passes every range comparison.
    Both have to fail all the same."""
    with pytest.raises(TypeError, match="must be an integer"):
        ElementaryFactor(R, index, R.zero)  # type: ignore[arg-type]


def test_factors_over_different_domains_are_unequal() -> None:
    """The same symbols, the same P, a different coefficient domain."""
    over_zz = ring("X1,X2", ZZ)[0]
    over_qq = ring("X1,X2", QQ)[0]

    left = ElementaryFactor(over_zz, 0, over_zz.gens[1] ** 2)
    right = ElementaryFactor(over_qq, 0, over_qq.gens[1] ** 2)

    assert left.polynomial == right.polynomial
    assert left != right
    assert hash(left) != hash(right)


def test_factors_of_a_product_must_share_a_ring() -> None:
    other_ring = ring("Y1,Y2", QQ)[0]
    foreign = ElementaryFactor(other_ring, 0, other_ring.zero)

    with pytest.raises(ValueError, match="same ring"):
        ElementaryAutomorphism([ElementaryFactor(R, 0, X2), foreign])


def test_apply_to_requires_the_same_ring(identity: PolynomialMap) -> None:
    other_ring = ring("Y1,Y2", QQ)[0]
    foreign = ElementaryFactor(other_ring, 0, other_ring.zero)

    with pytest.raises(ValueError, match="different rings"):
        foreign.apply_to(identity)


# --------------------------------------------------------------------------
# BCW Proposition (3.1), formula (1)
# --------------------------------------------------------------------------

# G = (X1 - X3 X4, X2, X3, X4) and H = (X1, X2, X3 + P, X4 + Q). G is a single
# factor and H a product of two, which is why there are two classes.

BCW_G = ElementaryFactor(R, index=0, polynomial=-X3 * X4)
BCW_H = ElementaryAutomorphism(
    [ElementaryFactor(R, 2, X2**2), ElementaryFactor(R, 3, X2**2)]
)


def test_bcw_G_reproduces_the_paper() -> None:  # noqa: N802
    assert BCW_G.to_polynomial_map().components == (x1 - x3 * x4, x2, x3, x4)


def test_bcw_H_reproduces_the_paper() -> None:  # noqa: N802
    components = BCW_H.to_polynomial_map().components

    assert components == (x1, x2, x3 + x2**2, x4 + x2**2)


def test_bcw_factors_lie_in_EA1() -> None:  # noqa: N802
    """First part of the proof: deg P, deg Q >= 2, so G, H lie in EA^1."""
    assert BCW_G.is_in_EA(1)
    assert BCW_H.is_in_EA(1)


def test_a_linear_polynomial_only_gives_EA0() -> None:  # noqa: N802
    """The linearisation part, where BCW require only EA^0."""
    factor = ElementaryFactor(R, 2, X1)

    assert factor.filtration_degree() == 0
    assert factor.is_in_EA(0)
    assert not factor.is_in_EA(1)


# --------------------------------------------------------------------------
# Group structure
# --------------------------------------------------------------------------

FACTORS = [
    BCW_G,
    ElementaryFactor(R, 2, X2**2),
    ElementaryFactor(R, 1, X3**3 + X4),
    ElementaryFactor(R, 0, X2 + X3 * X4),
    ElementaryFactor(R, 3, R.zero),
]


@pytest.mark.parametrize("factor", FACTORS)
def test_factor_inverse_is_two_sided(
    factor: ElementaryFactor, identity: PolynomialMap
) -> None:
    """Both orders, because a one-sided inverse proves nothing here."""
    E = factor.to_polynomial_map()
    E_inverse = factor.inverse().to_polynomial_map()

    assert factor.inverse().apply_to(E) == identity
    assert factor.apply_to(E_inverse) == identity


@pytest.mark.parametrize("factor", FACTORS)
def test_inverting_twice_returns_the_factor(factor: ElementaryFactor) -> None:
    assert factor.inverse().inverse() == factor


@pytest.mark.parametrize("factor", FACTORS)
def test_structural_determinant_matches_the_computed_one(
    factor: ElementaryFactor,
) -> None:
    """Every generator of EA_n(k) has determinant 1, without computing.

    This is the promise ``BCWStep.verify`` is to rely on. Here it is held
    against the computed route.
    """
    assert factor.determinant() == 1
    assert factor.to_polynomial_map().determinant() == 1


@pytest.mark.parametrize("factor", FACTORS)
def test_apply_to_agrees_with_full_composition(
    factor: ElementaryFactor, identity: PolynomialMap
) -> None:
    """The cheap path has to give what the full composition gives.

    ``apply_to`` touches one component only. That is the reason for the class,
    and therefore it is checked against ``PolynomialMap.compose``.
    """
    target = PolynomialMap.from_ring(R, (X1 + X2**2, X2 * X3, X3 + X4, X4))

    assert factor.apply_to(target) == factor.to_polynomial_map().compose(target)


def test_product_inverse_reverses_the_order() -> None:
    """With factors that do not commute, otherwise the test does not check
    that the order is reversed."""
    first = ElementaryFactor(R, 0, X2**2)
    second = ElementaryFactor(R, 1, X1**2)

    forward = ElementaryAutomorphism([first, second])
    backward = ElementaryAutomorphism([second, first])

    assert forward.to_polynomial_map() != backward.to_polynomial_map()

    assert forward.inverse().factors == (second.inverse(), first.inverse())


@pytest.mark.parametrize(
    "automorphism",
    [BCW_H, ElementaryAutomorphism(FACTORS), ElementaryAutomorphism([FACTORS[0]])],
)
def test_product_inverse_is_two_sided(
    automorphism: ElementaryAutomorphism, identity: PolynomialMap
) -> None:
    assert automorphism.compose(automorphism.inverse()).to_polynomial_map() == identity
    assert automorphism.inverse().compose(automorphism).to_polynomial_map() == identity


def test_every_element_of_EA_has_determinant_one() -> None:  # noqa: N802
    """BCW p. 304: EA_n(k) is generated by maps of determinant 1.

    An earlier draft admitted X_j |-> a X_j + P for an arbitrary unit a. That
    is a polynomial automorphism but not an elementary one: its displacement
    (a - 1) X_j depends on X_j. It would have brought elements of determinant
    other than 1 into EA_n(k) and destroyed the argument that a reduction step
    preserves the Jacobian determinant.
    """
    automorphism = ElementaryAutomorphism(FACTORS)

    assert automorphism.determinant() == 1
    assert automorphism.to_polynomial_map().determinant() == 1


def test_composition_concatenates_the_factorizations() -> None:
    left = ElementaryAutomorphism([FACTORS[0]])
    right = ElementaryAutomorphism([FACTORS[1], FACTORS[2]])

    assert left.compose(right).factors == (FACTORS[0], FACTORS[1], FACTORS[2])


def test_composition_across_rings_is_rejected() -> None:
    other_ring = ring("Y1,Y2", QQ)[0]
    foreign = ElementaryAutomorphism([ElementaryFactor(other_ring, 0, other_ring.zero)])

    with pytest.raises(ValueError, match="different rings"):
        BCW_H.compose(foreign)


# --------------------------------------------------------------------------
# The identity
# --------------------------------------------------------------------------


def test_identity_is_the_empty_product(identity: PolynomialMap) -> None:
    empty = ElementaryAutomorphism.identity()

    assert len(empty) == 0
    assert empty.determinant() == 1
    assert empty.to_polynomial_map(R) == identity


def test_identity_needs_a_ring_to_become_a_map() -> None:
    """An empty product carries no ring and does not know its dimension."""
    with pytest.raises(ValueError, match="needs a ring"):
        ElementaryAutomorphism.identity().to_polynomial_map()


def test_composing_with_the_identity_changes_nothing() -> None:
    empty = ElementaryAutomorphism.identity()

    assert BCW_H.compose(empty) == BCW_H
    assert empty.compose(BCW_H) == BCW_H


# --------------------------------------------------------------------------
# Filtration
# --------------------------------------------------------------------------


def test_order_is_the_order_of_the_polynomial() -> None:
    """The displacement is P, so the order needs no map."""
    assert ElementaryFactor(R, 0, X2**5).order() == 5
    assert ElementaryFactor(R, 0, X2 + X3**4).order() == 1


def test_the_identity_factor_has_infinite_order() -> None:
    assert ElementaryFactor(R, 0, R.zero).order() == float("inf")


def test_a_product_can_lie_deeper_than_its_factors() -> None:
    """Why ``filtration_degree`` forms the map instead of consulting the
    factors.

    Both factors lie in EA^0 and in no deeper level, while their product is
    the identity and lies in every EA^d. The filtration degree of the product
    therefore cannot be read off the factors alone. MA^d as a submonoid gives
    a lower bound only.
    """
    up = ElementaryFactor(R, 0, X2)
    down = ElementaryFactor(R, 0, -X2)

    assert up.filtration_degree() == down.filtration_degree() == 0

    product = ElementaryAutomorphism([up, down])

    assert product.filtration_degree() == float("inf")
    assert product.is_in_EA(17)


# --------------------------------------------------------------------------
# Value semantics
# --------------------------------------------------------------------------


def test_equal_factors_built_separately_compare_equal() -> None:
    assert ElementaryFactor(R, 0, -X3 * X4) == BCW_G
    assert hash(ElementaryFactor(R, 0, -X3 * X4)) == hash(BCW_G)


def test_factors_differing_in_the_index_are_unequal() -> None:
    assert ElementaryFactor(R, 0, X3 * X4) != ElementaryFactor(R, 1, X3 * X4)


def test_factors_differing_in_the_polynomial_are_unequal() -> None:
    assert ElementaryFactor(R, 0, X2) != ElementaryFactor(R, 0, -X2)


def test_comparison_with_a_foreign_type_is_not_implemented() -> None:
    assert BCW_G.__eq__(object()) is NotImplemented
    assert ElementaryAutomorphism.identity().__eq__(object()) is NotImplemented


def test_different_factorizations_of_one_automorphism_are_not_equal(
    identity: PolynomialMap,
) -> None:
    """The design decision, stated.

    Both objects are the identity as a map. As elements of EA they are
    different, because the factorization is the certificate and a reduction
    step has to exhibit the one it used.
    """
    empty = ElementaryAutomorphism.identity()
    cancelling = ElementaryAutomorphism([BCW_G, BCW_G.inverse()])

    assert cancelling.to_polynomial_map() == empty.to_polynomial_map(R) == identity
    assert cancelling != empty


def test_factor_is_immutable() -> None:
    from dataclasses import FrozenInstanceError

    with pytest.raises(FrozenInstanceError):
        BCW_G._index = 1  # type: ignore[misc]


def test_repr_names_the_moving_variable() -> None:
    assert "variable=X1" in repr(BCW_G)
    assert repr(BCW_H).startswith("ElementaryAutomorphism(")


def test_factors_must_be_elementary_factors() -> None:
    with pytest.raises(TypeError, match="ElementaryFactor"):
        ElementaryAutomorphism([BCW_G, "not a factor"])  # type: ignore[list-item]


def test_identity_has_no_ring() -> None:
    with pytest.raises(ValueError, match="carries no ring"):
        _ = ElementaryAutomorphism.identity().ring


def test_factor_exposes_index_and_variable() -> None:
    assert BCW_G.index == 0
    assert BCW_G.variable == x1
    assert BCW_G.polynomial == -x3 * x4


def test_automorphisms_are_hashable() -> None:
    assert len({BCW_H, ElementaryAutomorphism(BCW_H.factors)}) == 1
    assert len({BCW_H, ElementaryAutomorphism.identity()}) == 2


def test_identity_lies_in_every_EA() -> None:  # noqa: N802
    """The empty product carries no ring and lies in every EA^d."""
    empty = ElementaryAutomorphism.identity()

    assert empty.filtration_degree() == math.inf
    assert empty.is_in_EA(0)
    assert empty.is_in_EA(17)


def test_factor_does_not_adopt_the_callers_ring() -> None:
    """The same promise as for PolynomialMap.ring, for the same reason."""
    R2, Y1, Y2 = ring("Y1,Y2", QQ)
    factor = ElementaryFactor(R2, 0, Y2**2)
    before = factor.to_polynomial_map().components

    R2.gens[0].clear()

    assert factor.to_polynomial_map().components == before


def test_factor_ring_property_does_not_leak() -> None:
    R2, Y1, Y2 = ring("Y1,Y2", QQ)
    factor = ElementaryFactor(R2, 0, Y2**2)
    before = factor.to_polynomial_map().components

    factor.ring.gens[0].clear()

    assert factor.to_polynomial_map().components == before


@pytest.mark.parametrize("factor", FACTORS)
def test_every_generator_has_determinant_one(factor: ElementaryFactor) -> None:
    """EA_n(k) lies in SA_n(k).

    BCW define a factor by E_j - X_j = P with P free of X_j. The linear part is
    then unipotent and the determinant is 1. A factor scaling X_j by a would
    have determinant a and would not be an element of EA_n(k). An earlier draft
    admitted that.
    """
    assert factor.determinant() == 1
    assert factor.to_polynomial_map().determinant() == 1


def test_identity_lies_in_every_filtration_level() -> None:
    """The empty product carries no ring and lies in every EA^d."""
    empty = ElementaryAutomorphism.identity()

    assert empty.filtration_degree() == float("inf")
    assert empty.is_in_EA(17)


# --------------------------------------------------------------------------
# Ring validation
#
# The same check as in PolynomialMap.from_ring, from the same source. It was
# missing here before: a composite generator was accepted, ``variable`` then
# returned a Mul instead of a Symbol, and only ``to_polynomial_map`` failed,
# far away from the cause.
# --------------------------------------------------------------------------


def test_composite_generators_are_rejected() -> None:
    composite = ring([x1 * x2], QQ)[0]

    with pytest.raises(TypeError, match="SymPy symbols"):
        ElementaryFactor(composite, 0, composite.zero)


def test_generators_sharing_a_name_are_rejected() -> None:
    """Different assumptions, one name: indistinguishable as an expression."""
    plain = sp.Symbol("z")
    positive = sp.Symbol("z", positive=True)
    ambiguous = ring([plain, positive], QQ)[0]

    assert plain != positive

    with pytest.raises(ValueError, match="pairwise distinct"):
        ElementaryFactor(ambiguous, 0, ambiguous.zero)


def test_a_ring_without_generators_is_rejected() -> None:
    empty = ring("", QQ)[0]

    with pytest.raises(ValueError, match="at least one variable"):
        ElementaryFactor(empty, 0, empty.zero)


def test_variable_is_always_a_symbol() -> None:
    """The promise that was only asserted before."""
    assert isinstance(BCW_G.variable, sp.Symbol)
