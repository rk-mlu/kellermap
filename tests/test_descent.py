"""The descent, DSC-1 to DSC-7.

One obligation carries this family. DSC-3 is the claim a caller supplies and
the only place a wrong claim can fail, so it gets a control for each of its two
halves: a conjugate whose deleted component is not triangular, and one whose
surviving components still mention the deleted coordinate. Everything else here
either follows from it or is a property of the arguments.

The maps are small and built by hand. The one place a real map is needed is the
transport, where a collision has to exist; ``examples.alpoege`` supplies one and
a triangular coordinate is added to it, so the descent is checked against a map
whose collision was not constructed for the occasion.
"""

import math

import pytest
import sympy as sp
from sympy import GF, QQ
from sympy.polys.rings import PolyRing

from kellermap import (
    Collision,
    DescentStep,
    ElementaryAutomorphism,
    ElementaryFactor,
    PolynomialMap,
    Provenance,
    Reduction,
    Step,
    VerificationError,
    examples,
)

x, y, z = sp.symbols("x y z")


def extension() -> PolynomialMap:
    """A map already triangular in its last coordinate."""
    return PolynomialMap((x, y, z), (x + y**2, y, z + x * y))


def hidden() -> tuple[PolynomialMap, ElementaryAutomorphism]:
    """The same map with the triangularity hidden behind a completion.

    ``T`` subtracts ``z**2`` from the first component, so ``T . source`` is the
    extension above and the source itself mentions ``z`` where the target
    cannot.
    """
    plain = extension()
    change = ElementaryAutomorphism((ElementaryFactor(plain.ring, 0, -(z**2)),))

    return change.inverse().apply_to(plain), change


# ----------------------------------------------------------------------
# The arguments, DSC-4 and the constructor
# ----------------------------------------------------------------------


def test_a_source_that_is_not_a_map_is_refused() -> None:
    with pytest.raises(TypeError, match="PolynomialMap"):
        DescentStep("not a map", 0)  # type: ignore[arg-type]


@pytest.mark.parametrize("side", ["left", "right"])
def test_a_change_that_is_not_an_automorphism_is_refused(side: str) -> None:
    """DSC-4. A wrong type is not a statement about arithmetic."""
    with pytest.raises(TypeError, match="ElementaryAutomorphism"):
        DescentStep(extension(), 2, **{side: "not an automorphism"})


def test_an_index_that_is_not_an_integer_is_refused() -> None:
    with pytest.raises(TypeError, match="int"):
        DescentStep(extension(), "2")  # type: ignore[arg-type]


def test_a_boolean_index_is_refused() -> None:
    """``True`` is an ``int`` in Python and is not a coordinate."""
    with pytest.raises(TypeError, match="int"):
        DescentStep(extension(), True)


@pytest.mark.parametrize("index", [-1, 3])
def test_an_index_outside_the_map_is_refused(index: int) -> None:
    with pytest.raises(ValueError, match="coordinate"):
        DescentStep(extension(), index)


def test_a_descent_from_one_variable_is_refused() -> None:
    """There is no map in no variables to descend to."""
    with pytest.raises(ValueError, match="one variable"):
        DescentStep(PolynomialMap((x,), (x,)), 0)


def test_the_identity_is_admitted_on_either_side() -> None:
    """A map already triangular needs no change, and the page says so."""
    step = DescentStep(extension(), 2)
    step.verify()

    assert step.left == ElementaryAutomorphism()
    assert step.right == ElementaryAutomorphism()


# ----------------------------------------------------------------------
# What the step derives, DSC-1 and DSC-2
# ----------------------------------------------------------------------


def test_the_target_is_the_conjugate_without_the_deleted_component() -> None:
    """DSC-1."""
    source, change = hidden()
    step = DescentStep(source, 2, left=change)
    step.verify()

    assert step.conjugate() == extension()
    assert step.target == PolynomialMap((x, y), (x + y**2, y))


def test_the_dimension_falls_by_one_and_the_generators_are_the_source_s() -> None:
    """DSC-2. No generator is fresh, which is what tells this from a compression."""
    step = DescentStep(extension(), 1)

    assert step.index == 1
    assert step.variables == (x, z)
    assert step.ring.symbols == (x, z)
    assert step.source.dimension - 1 == 2


def test_the_tail_is_what_the_deletion_throws_away() -> None:
    """The one thing not recoverable from the target, which is why it is offered."""
    source, change = hidden()
    step = DescentStep(source, 2, left=change)

    assert step.tail() == x * y


# ----------------------------------------------------------------------
# The ring, DSC-2 and DSC-4
# ----------------------------------------------------------------------


@pytest.mark.parametrize(
    ("domain", "order"), [(QQ, "lex"), (GF(5), "lex"), (QQ, "grlex")]
)
def test_the_target_keeps_the_domain_and_the_order(domain: object, order: str) -> None:
    """The target is carried over and not re-read from expressions.

    The first version built it with the expression constructor, which infers a
    ring: an audit of ``0.7.0rc1`` found a source over ``QQ`` giving a target
    over ``ZZ``, and over a finite field that changes the characteristic and
    with it the arithmetic of every later step.
    """
    ring = PolyRing((x, y, z), domain, order)
    source = PolynomialMap.from_ring(
        ring,
        (
            ring.gens[0] + ring.gens[1] ** 2,
            ring.gens[1],
            ring.gens[2] + ring.gens[0] * ring.gens[1],
        ),
    )
    step = DescentStep(source, 2)
    step.verify()

    assert step.target.ring.domain == domain
    assert step.target.ring.order == ring.order
    assert step.ring == step.target.ring


def test_the_ring_is_a_fresh_object_on_every_access() -> None:
    """``PolyRing.clone`` goes through SymPy's cache and hands one back.

    ``clone_ring`` exists to avoid exactly that, and the first version of this
    property did not use it, so a caller could reach the ring's generators
    through a step. The docstring of ``clone_ring`` records the failure.
    """
    step = DescentStep(extension(), 2)

    assert step.ring is not step.ring
    assert step.ring == step.ring


def test_an_automorphism_over_another_ring_fails_dsc_4() -> None:
    """DSC-4, the half that is about arithmetic rather than about a type.

    Without the check the mismatch surfaced from inside
    ``ElementaryAutomorphism.apply_to`` as a bare ``ValueError`` naming neither
    the obligation nor the side it came from.
    """
    elsewhere = PolynomialMap(sp.symbols("a b c"), sp.symbols("a b c"))
    foreign = ElementaryAutomorphism(
        (ElementaryFactor(elsewhere.ring, 0, -(elsewhere.variables[2] ** 2)),)
    )

    with pytest.raises(VerificationError, match=r"\[DSC-4\].*left change"):
        DescentStep(extension(), 2, left=foreign).verify()

    with pytest.raises(VerificationError, match=r"\[DSC-4\].*right change"):
        DescentStep(extension(), 2, right=foreign).verify()


def foreign_step() -> DescentStep:
    """A step whose left change is an automorphism over another ring."""
    elsewhere = PolynomialMap(sp.symbols("a b c"), sp.symbols("a b c"))
    foreign = ElementaryAutomorphism(
        (ElementaryFactor(elsewhere.ring, 0, -(elsewhere.variables[2] ** 2)),)
    )

    return DescentStep(extension(), 2, left=foreign)


def test_the_conjugate_refuses_a_foreign_automorphism() -> None:
    """Every public route into the step raises the same named exception.

    ``verify`` and ``target`` named DSC-4 while this method and ``tail`` let a
    bare ``ValueError`` out of ``ElementaryAutomorphism.apply_to``. An audit of
    ``0.7.0rc2`` found it, and found that the test meant to cover this called
    ``target`` instead.
    """
    with pytest.raises(VerificationError, match=r"\[DSC-4\]"):
        foreign_step().conjugate()


def test_the_tail_refuses_a_foreign_automorphism() -> None:
    """``tail`` reaches the two changes through ``conjugate``."""
    with pytest.raises(VerificationError, match=r"\[DSC-4\]"):
        foreign_step().tail()


def test_the_target_refuses_a_foreign_automorphism() -> None:
    """The route the mis-described test actually took."""
    with pytest.raises(VerificationError, match=r"\[DSC-4\]"):
        assert foreign_step().target


# ----------------------------------------------------------------------
# DSC-3, the obligation this family exists for
# ----------------------------------------------------------------------


def test_a_conjugate_whose_deleted_component_is_not_triangular_fails() -> None:
    """DSC-3, first half. The negative control for it."""
    source = PolynomialMap((x, y, z), (x + y**2, y, z + z**2 * x))
    step = DescentStep(source, 2)

    with pytest.raises(VerificationError, match=r"\[DSC-3\].*free of z"):
        step.verify()


def test_a_conjugate_whose_other_components_mention_the_coordinate_fails() -> None:
    """DSC-3, second half. The negative control for it.

    The source of ``hidden`` is exactly this map without its completion, so the
    control differs from the passing case by one argument.
    """
    source, _ = hidden()
    step = DescentStep(source, 2)

    with pytest.raises(VerificationError, match=r"\[DSC-3\].*mentions z"):
        step.verify()


def test_the_target_refuses_a_truncation_before_it_makes_one() -> None:
    """A wrong claim raises rather than yielding a plausible map.

    ``PolynomialMap`` takes a symbol outside its generators into the
    coefficient domain, so without this check the deleted coordinate would
    quietly become a parameter of the target.
    """
    source, _ = hidden()

    with pytest.raises(VerificationError, match=r"\[DSC-3\].*mentions z"):
        assert DescentStep(source, 2).target


# ----------------------------------------------------------------------
# DSC-5 and the Step protocol
# ----------------------------------------------------------------------


def test_the_determinant_carries_over() -> None:
    """DSC-5, from outside the step as well as inside it."""
    source, change = hidden()
    step = DescentStep(source, 2, left=change)
    step.verify()

    assert step.source.determinant() == step.target.determinant() == 1


def test_verification_is_pure_and_cached() -> None:
    """STEP-2. Calling it twice is calling it once."""
    step = DescentStep(extension(), 2)

    assert step.verify() is None
    assert step.verify() is None


def test_the_step_satisfies_the_protocol() -> None:
    """STEP-1 to STEP-5, in the one place they are asked of a new type."""
    step = DescentStep(extension(), 2)

    assert isinstance(step, Step)
    assert step.provenance is Provenance.SUPPLIED
    assert step.filtration_level == math.inf


def test_the_provenance_is_supplied_and_nothing_can_change_it() -> None:
    """DSC-7. This milestone gives the type no ``build``."""
    step = DescentStep(extension(), 2)

    assert step.provenance is Provenance.SUPPLIED
    assert not hasattr(DescentStep, "build")


def test_the_step_is_immutable() -> None:
    """STEP-5."""
    step = DescentStep(extension(), 2)

    with pytest.raises(AttributeError):
        step._index = 0  # type: ignore[misc]
    with pytest.raises(AttributeError):
        del step._index


def test_steps_compare_by_content() -> None:
    """STEP-5, including the provenance the page says is part of it."""
    source, change = hidden()

    assert DescentStep(source, 2, left=change) == DescentStep(source, 2, left=change)
    assert DescentStep(source, 2, left=change) != DescentStep(source, 1, left=change)
    assert len({DescentStep(source, 2), DescentStep(source, 2)}) == 1
    assert DescentStep(source, 2).__eq__("not a step") is NotImplemented


def test_the_repr_says_which_way_the_dimension_goes() -> None:
    assert "3->2" in repr(DescentStep(extension(), 2))


# ----------------------------------------------------------------------
# DSC-6
# ----------------------------------------------------------------------


def lifted() -> tuple[PolynomialMap, Collision, PolynomialMap, Collision]:
    """Alpoege's map with a triangular coordinate added, and its collision.

    The added component is ``w + x1``, so the last coordinate of each point has
    to absorb the difference: the images agree only when ``s_i + x1(p_i)`` is
    one value, and taking ``s_i = -x1(p_i)`` makes it zero.
    """
    small = examples.alpoege()
    collision = examples.alpoege_collision()
    w = sp.Symbol("w")

    large = PolynomialMap(
        small.variables + (w,), small.components + (w + small.variables[0],)
    )
    points = tuple(
        tuple(sp.sympify(value) for value in point) + (-sp.sympify(point[0]),)
        for point in collision.points
    )

    return small, collision, large, Collision.at(large, points)


def test_a_collision_transports_and_the_points_come_back() -> None:
    """DSC-6 and STEP-4, on a collision that was not made for this test."""
    small, collision, large, extended = lifted()
    step = DescentStep(large, 3)
    step.verify()

    moved = step.transport(extended)

    assert step.target == small
    assert len(moved.points) == len(extended.points) == 3
    assert moved.points == collision.points


def test_transport_undoes_the_change_on_the_source_side() -> None:
    """The points go through ``right.inverse()`` before the coordinate drops."""
    small, collision, large, extended = lifted()
    change = ElementaryAutomorphism(
        (ElementaryFactor(large.ring, 3, large.variables[1] ** 2),)
    )
    moved_source = small.__class__(
        large.variables,
        large.compose(change.to_polynomial_map(large.ring)).components,
    )
    step = DescentStep(moved_source, 3, right=change.inverse())
    step.verify()

    assert step.target == small


def test_transport_refuses_a_collision_that_does_not_hold() -> None:
    """STEP-3. It never returns an unverified result."""
    _, _, large, _ = lifted()
    step = DescentStep(large, 3)

    with pytest.raises(VerificationError):
        step.transport(Collision.at(large, ((0, 0, 0, 0), (1, 1, 1, 1))))


def test_a_descent_is_a_step_of_a_reduction() -> None:
    """The point of satisfying the protocol: chains take it."""
    _, collision, large, extended = lifted()
    chain = Reduction((DescentStep(large, 3),))
    chain.verify()

    assert chain.transport(extended).points == collision.points
