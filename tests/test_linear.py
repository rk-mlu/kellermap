"""The linear part: GL_n(k) as an ordered product of Gauss operations.

The substance of this file is the distinction that gives the module its
purpose. A transvection is elementary in the sense of BCW; a transposition and
a dilation are not. The rest checks that the factorization really reproduces
the matrix, and that ``apply_to`` does what composition through
``PolynomialMap`` does.

At the end stands the normalisation of Alpoege's map, where both show. The
factorization consists of exactly one transposition and one dilation, and its
determinant -1/2 turns the Keller determinant -2 into 1.
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
# What is elementary and what is not
# --------------------------------------------------------------------------


def test_a_transvection_is_elementary(ring: object) -> None:
    """P = a * X_source is free of X_index, so it is an ElementaryFactor."""
    shear = Transvection(ring, 0, 1, 3)

    assert shear.is_elementary
    assert shear.determinant() == 1
    assert shear.as_elementary_factor() == ElementaryFactor(ring, 0, 3 * y)


def test_a_transvection_lies_in_EA0_and_not_in_EA1(ring: object) -> None:  # noqa: N802
    """The linear part is exactly why EA^0 appears in BCW."""
    factor = Transvection(ring, 0, 1, 3).as_elementary_factor()

    assert factor.is_in_EA(0)
    assert not factor.is_in_EA(1)


def test_a_transposition_is_not_elementary(ring: object) -> None:
    """Two components moved, and determinant -1."""
    swap = Transposition(ring, 0, 2)

    assert not swap.is_elementary
    assert swap.determinant() == -1


def test_a_dilation_is_not_elementary(ring: object) -> None:
    """The displacement (a - 1) * X_index depends on X_index."""
    scaling = Dilation(ring, 0, sp.Rational(1, 2))

    assert not scaling.is_elementary
    assert scaling.determinant() == sp.Rational(1, 2)


def test_a_dilation_is_rejected_by_ElementaryFactor(ring: object) -> None:  # noqa: N802
    """A control: the dilation would not pass the check of 0.1."""
    with pytest.raises(ValueError, match="must not involve"):
        ElementaryFactor(ring, 0, -sp.Rational(1, 2) * x)


# --------------------------------------------------------------------------
# The individual factors
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
    other = over_field(PolynomialMap.identity(sp.symbols("u v w"))).ring
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
    """Over ZZ the number 2 is not a unit. The message names the way out."""
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
    """At the level of the matrix and at the level of the map."""
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
    """apply_to is a shortcut and not another notion of composition."""
    factor = factor_of(F.ring)

    assert factor.apply_to(F) == factor.to_polynomial_map().compose(F)


def test_a_factor_rejects_a_foreign_map(ring: object) -> None:
    other = PolynomialMap.identity(sp.symbols("u v w"))

    with pytest.raises(ValueError, match="different rings"):
        Transposition(ring, 0, 1).apply_to(other)


def test_matrices_act_on_the_components(F: PolynomialMap) -> None:
    """Left composition is matrix times component vector, with no substitution."""
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
    """Without forming the matrix: the product of the factor determinants."""
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


def test_factorize_refuses_a_column_it_cannot_bring_to_a_unit() -> None:
    """Over ZZ the column ``(2, 0, 0)`` has gcd two, which is not a unit.

    The message changed at ``0.7.0rc10`` and says less than it used to on
    purpose. It said the matrix needed the field of fractions, which for this
    matrix is true and was being asserted of every refusal -- including of
    matrices in ``GL_2(ZZ)`` whose determinant is one. It now reports what the
    elimination actually established, that no unit pivot was reached, and
    names FAC-2 for the two reasons that can produce it.

    Each of those parts is asserted here, since ``0.7.0rc11``. This test
    matched the first clause alone, so an audit of ``0.7.0rc10`` could delete
    the two readings, the boundedness and the reference to FAC-2 and watch the
    suite pass. The clause binds the whole message, and half a control is the
    kind that reads as one.
    """
    with pytest.raises(ValueError) as refusal:
        LinearAutomorphism.factorize(QUADRATIC.ring, sp.diag(2, 1, 1))

    message = str(refusal.value)

    assert "No unit pivot was reached in column 0" in message
    assert str(QUADRATIC.ring.domain) in message
    assert "not invertible there" in message
    assert "did not find the row combination" in message
    assert "the search is bounded" in message
    assert "FAC-2" in message


def test_a_coefficient_outside_the_domain_is_rejected() -> None:
    """The conversion every factor puts its coefficient through.

    Reached from a factor and no longer from ``factorize``, which since
    ``0.7.0rc7`` hands the elimination's own domain elements back through
    ``to_sympy`` and so cannot produce one that fails to convert. The check
    still belongs to the factors: a coefficient outside the domain is a
    statement about the caller's data and is reported as one.
    """
    with pytest.raises(ValueError, match="does not lie in"):
        Dilation(QUADRATIC.ring, 0, sp.sqrt(2))

    with pytest.raises(ValueError, match="does not lie in"):
        Transvection(QUADRATIC.ring, 0, 1, sp.sqrt(2))


def test_factorize_works_over_a_finite_field() -> None:
    """The elimination runs in the domain, so ``GF(5)`` needs no widening.

    ``0.7.0rc6`` formed ``1/2`` as a rational here and refused the matrix as
    needing ``over_field()``, which cannot help: ``GF(5)`` already is a field.
    """
    finite = sp.ring("a,b", sp.GF(5))[0]
    factored = LinearAutomorphism.factorize(finite, sp.Matrix([[0, 1], [2, 0]]))

    assert sp.Matrix(factored.matrix(finite)) == sp.Matrix([[0, 1], [2, 0]])
    assert factored.determinant() == finite.domain.to_sympy(
        finite.domain.from_sympy(sp.Integer(-2))
    )


def test_FAC1_the_search_tries_its_candidates_before_applying_one() -> None:  # noqa: N802
    """The matrix of the ``0.7.0rc10`` audit, in both orders of its rows.

    ``0.7.0rc10`` applied the first candidate and left the loop, so minus one
    and the quotient were computed and discarded. The quotient is what reaches
    this matrix: ``(2T+1) - 2 T`` is one. Without it the matrix was refused
    while the same matrix with its rows exchanged factorized, which made the
    answer depend on the order in which the rows were written down.
    """
    parameter = sp.Symbol("T")
    ring = sp.ring("a,b", sp.ZZ[parameter])[0]
    given = sp.Matrix([[parameter, -1], [2 * parameter + 1, -2]])
    exchanged = sp.Matrix([[2 * parameter + 1, -2], [parameter, -1]])

    assert sp.expand(given.det()) == 1

    for matrix in (given, exchanged):
        factored = LinearAutomorphism.factorize(ring, matrix)

        assert sp.expand(sp.Matrix(factored.matrix(ring)) - matrix).is_zero_matrix

    quotients = [
        factor
        for factor in LinearAutomorphism.factorize(ring, given).factors
        if isinstance(factor, Transvection) and factor.coefficient == -2
    ]

    assert quotients, "the quotient candidate did not reach the pivot"


def test_FAC2_the_bound_is_still_reachable_over_a_parameter_ring() -> None:  # noqa: N802
    """The search is wider since ``0.7.0rc11`` and still bounded.

    ``[[7, 17], [2, 5]]`` has determinant one and integer entries. Over ``ZZ``
    the Euclidean fold reaches it; over ``ZZ[T]`` there is no fold, and the
    bounded search does not. A widening that left nothing refused would make
    FAC-2 a clause about nothing, so the boundary needs a witness of its own.
    """
    parameter = sp.Symbol("T")
    ring = sp.ring("a,b", sp.ZZ[parameter])[0]
    integral = sp.ring("a,b", sp.ZZ)[0]
    given = sp.Matrix([[7, 17], [2, 5]])

    with pytest.raises(ValueError, match="No unit pivot was reached in column 0"):
        LinearAutomorphism.factorize(ring, given)

    factored = LinearAutomorphism.factorize(integral, given)

    assert sp.Matrix(factored.matrix(integral)) == given


def test_the_identity_factors_into_nothing(ring: object) -> None:
    factored = LinearAutomorphism.factorize(ring, sp.eye(3))

    assert len(factored) == 0
    assert sp.Matrix(factored.matrix(ring)) == sp.eye(3)

    with pytest.raises(ValueError, match="needs a ring"):
        factored.matrix()


# --------------------------------------------------------------------------
# Group structure
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
    other = over_field(PolynomialMap.identity(sp.symbols("u v w"))).ring

    with pytest.raises(ValueError, match="same ring"):
        LinearAutomorphism([Transposition(ring, 0, 1), Transposition(other, 0, 1)])


def test_factors_must_be_linear_factors(ring: object) -> None:
    with pytest.raises(TypeError, match="LinearFactor"):
        LinearAutomorphism([ElementaryFactor(ring, 0, y)])


def test_is_elementary_is_a_property_of_the_factorization(ring: object) -> None:
    """Sufficient, not characterising.

    Two equal transpositions are the identity and therefore lie in EA_n(k),
    although no factor is elementary. The property reports on the factorization
    presented and not on the element.
    """
    swap = Transposition(ring, 0, 1)
    twice = LinearAutomorphism([swap, swap])

    assert not twice.is_elementary
    assert sp.Matrix(twice.matrix()) == sp.eye(3)


def test_two_factorizations_of_one_matrix_are_different_objects(
    ring: object,
) -> None:
    """As for ElementaryAutomorphism: the factorization is the certificate."""
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


def test_WID1_a_domain_with_no_field_of_fractions_is_refused() -> None:  # noqa: N802
    """`sp.GF(4)` is `Z/4Z`, and `get_field` answers with it again.

    `0.7.0rc10` handed that answer on, so `field_ring` promised a field and
    returned a ring with zero divisors, and a caller told to widen was given
    the same ring and the same refusal. An audit found it.
    """
    residue = sp.ring("u,v", sp.GF(4))[0]

    assert residue.domain.get_field().is_Field is False

    with pytest.raises(ValueError, match="no field of fractions"):
        field_ring(residue)

    with pytest.raises(ValueError, match="no field of fractions"):
        over_field(PolynomialMap.from_ring(residue, residue.gens))


def test_WID1_a_domain_that_is_already_a_field_is_returned(  # noqa: N802
) -> None:
    """A widening that changes nothing is not a failure.

    The refusal above has to separate the two readings of "there is no field
    to widen to". `GF(5)` is a field, and asking for its field of fractions is
    a question with an answer.
    """
    finite = sp.ring("u,v", sp.GF(5))[0]

    assert field_ring(finite).domain == finite.domain


def test_WID2_the_advice_names_over_field_only_where_it_exists() -> None:  # noqa: N802
    """The message a non-unit coefficient raises, over three domains.

    Over `ZZ` the widening exists and the advice is the way out. Over `GF(5)`
    it moves nothing, and over `Z/4Z` there is nothing to move to: an audit of
    `0.7.0rc6` enumerated 392 matrices refused with the first kind of wrong
    advice, and an audit of `0.7.0rc9` found the second.
    """
    residue = sp.ring("u,v", sp.GF(4))[0]

    with pytest.raises(ValueError, match="over_field") as integral:
        Dilation(QUADRATIC.ring, 0, 2)

    with pytest.raises(ValueError) as composite:
        Dilation(residue, 0, 2)

    assert "does not lie in" in str(composite.value)
    assert "over_field" not in str(composite.value)
    assert "QQ" in str(integral.value)

    # The other site, where the coefficient does not convert at all. Both go
    # through one template and both ask WID-2, and a control on one of them
    # would leave the other free to drift.
    with pytest.raises(ValueError, match="over_field"):
        Dilation(QUADRATIC.ring, 0, sp.Rational(1, 2))

    with pytest.raises(ValueError) as unconvertible:
        Dilation(residue, 0, sp.Rational(1, 2))

    assert "over_field" not in str(unconvertible.value)


# --------------------------------------------------------------------------
# Regression: the normalisation of Alpoege's map
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
    """L^-1 for L = J(F)(0), factorized."""
    F = over_field(ALPOEGE)
    linear_part = sp.Matrix(
        F.jacobian().xreplace({v: sp.Integer(0) for v in F.variables})
    )

    return LinearAutomorphism.factorize(F.ring, linear_part.inv())


def test_the_normalization_is_a_transposition_and_a_dilation(
    normalization: LinearAutomorphism,
) -> None:
    """Exactly the two operations of the hand computation, in that order."""
    swap, scaling = normalization.factors

    assert isinstance(swap, Transposition)
    assert swap.indices == (0, 2)
    assert isinstance(scaling, Dilation)
    assert scaling.index == 2
    assert scaling.coefficient == sp.Rational(1, 2)


def test_the_normalization_is_not_elementary(
    normalization: LinearAutomorphism,
) -> None:
    """The shortest argument does not need the factorization at all.

    Every element of EA_n(k) has determinant 1. This one has -1/2, so under no
    factorization does it lie in EA_3(k).
    """
    assert normalization.determinant() == sp.Rational(-1, 2)
    assert not normalization.is_elementary


def test_the_normalization_turns_the_determinant_into_one(
    normalization: LinearAutomorphism,
) -> None:
    """Why BCW17 has determinant 1 and Alpoege has -2."""
    F = over_field(ALPOEGE)

    assert F.determinant() == -2
    assert normalization.apply_to(F).determinant() == 1


def test_the_normalization_reaches_MA1(  # noqa: N802
    normalization: LinearAutomorphism,
) -> None:
    """The hypothesis of Proposition (3.1)."""
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
    """Left composition leaves every preimage where it was.

    The BCW17 points therefore carry Alpoege's points verbatim in their first
    three coordinates, while the image moves from (-1/4, 0, 0) to
    (0, 0, -1/4).
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
