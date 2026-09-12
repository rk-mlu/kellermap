"""Keller maps over a field of positive characteristic.

The core API has no characteristic-zero bound, and BCW state their section for
a commutative ring, so a map over ``GF(2)`` is inside what this library claims.
An audit of ``0.7.0rc5`` found one over ``GF(2)`` breaking four public
operations at once, all from the same cause: ``PolyElement.diff`` leaves a term
with a zero coefficient in the sparse dictionary there, and such a polynomial
compares unequal to the same polynomial without it.

The map below is the audit's. Its Jacobian is the identity, so it is a Keller
map, and every component displaces its variable by that variable squared, so
BCW-10 admits none of them as a carried factor. Those two facts pull the two
carrier notions apart, which is why they cannot be one predicate.
"""

import sympy as sp

from kellermap import PolynomialMap, search
from kellermap.bcw.step import BCWStep, Fresh


def squares() -> PolynomialMap:
    """``(x + x^2, y + y^2, z + z^2)`` over ``GF(2)``."""
    ring, x, y, z = sp.ring("x,y,z", sp.GF(2))

    return PolynomialMap.from_ring(ring, (x + x**2, y + y**2, z + z**2))


def test_the_jacobian_is_the_identity() -> None:
    """A zero-coefficient term in an entry would not show here.

    ``sp.Matrix`` normalizes on the way in, so this passed while everything
    reading the entries directly did not. It is the control that says the
    derivatives themselves are right and their storage was not.
    """
    assert squares().jacobian() == sp.eye(3)


def test_the_unipotent_block_is_every_coordinate() -> None:
    """The diagonal of that Jacobian is one, so the block is the whole map.

    It was empty, because the entry compared unequal to the ring's one.
    """
    assert squares().carrier_indices == (0, 1, 2)


def test_no_coordinate_is_a_carried_factor() -> None:
    """BCW-10 asks that ``F_j - X_j`` be free of ``X_j``, and ``X_j^2`` is not.

    This is where the two notions part, and it cannot be decided by the
    derivative: over ``GF(2)`` the derivative of ``X_j^2`` is zero, so the
    diagonal entry is one and the displacement still depends on the variable.
    The equivalence the property used to claim holds in characteristic zero
    only, and it was a claim this test would have caught.
    """
    assert squares().carrier_indices_for_factors == ()


def test_the_determinant_is_one() -> None:
    """It raised ``ExactQuotientFailed`` from inside the Schur complement."""
    assert squares().determinant() == 1


def test_a_search_from_the_map_to_itself_reports_a_non_answer() -> None:
    """Equal endpoints are a non-answer and not an error, REV-11's shape.

    It raised the same ``ExactQuotientFailed``, through the determinant.
    """
    outcome = search(squares(), squares(), {})

    assert outcome.reduction is None
    assert outcome.exhausted is True


def test_a_step_over_the_field_builds_and_verifies() -> None:
    """``BCWStep.verify`` reaches the determinant too."""
    source = squares()
    first, second = sp.symbols("u v")
    step = BCWStep.build(
        source, 0, Fresh(sp.Symbol("x"), first), Fresh(sp.Symbol("x"), second), 0
    )
    step.verify()

    assert step.m == 2
    assert step.target.dimension == 5


def test_characteristic_zero_is_unchanged() -> None:
    """The normalization is a no-op where the derivative was already sparse."""
    x, y = sp.symbols("x y")
    source = PolynomialMap((x, y), (x + y**2, y))

    assert source.carrier_indices == (0, 1)
    assert source.carrier_indices_for_factors == (0, 1)
    assert source.determinant() == 1
