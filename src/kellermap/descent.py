"""Deleting a coordinate that two determinant-one changes made triangular.

The fourth move of the two published reductions at degree three, and the one
this library had no step type for. Work package 4 of milestone ``0.7`` settled
that it was missing rather than merely unwritten: six of the seven step types
cannot lower a dimension at all, and ``CompressionStep`` restricts along a
linear embedding and wants a homogeneous displacement, neither of which this
move has.

Given ``F``, two elementary automorphisms ``S`` and ``T``, and an index ``k``,
the conjugate is ``C = T o F o S``. When ``C`` displaces ``X_k`` by something
free of ``X_k`` and no other component of ``C`` mentions ``X_k``, the map
``C`` is a triangular extension of the map on the remaining coordinates, and
that smaller map is the target.

The step verifies a claim rather than making one. ``S``, ``T`` and ``k`` come
from the caller; there is no ``build`` here, so every instance is ``SUPPLIED``.
Searching for the two changes is a separate thing, on the division ``BCWStep``
and ``peel`` already stand on.

It lives at the top level and not in ``kellermap.bcw``. That subpackage holds
one paper and this move is in neither of its propositions.

See ``docs/contracts.md``, DSC-1 to DSC-7.
"""

from __future__ import annotations

import math

import sympy as sp
from sympy.polys.rings import PolyRing

from .collision import Collision
from .elementary import ElementaryAutomorphism
from .errors import VerificationError
from .polynomial_map import PolynomialMap, clone_ring, reindex
from .reduction import Provenance


class DescentStep:
    """The deletion of a coordinate made triangular by two changes.

    Parameters
    ----------
    source
        The map before the descent.
    index
        Which coordinate is deleted. It is an index into the source's
        generators, and the same position in the conjugate.
    left, right
        The two elementary automorphisms of DSC-4. ``right`` acts on the
        source's variables and ``left`` on its components, so the conjugate is
        ``left o source o right``. The identity is admitted for either.

    The target is derived and not supplied, for the reason ``G`` and ``H`` are
    derived in ``BCWStep``: a stored target beside the two automorphisms could
    disagree with them, and a reader would have no way to tell which was meant.
    """

    _source: PolynomialMap
    _index: int
    _left: ElementaryAutomorphism
    _right: ElementaryAutomorphism
    _provenance: Provenance
    _verified: bool

    def __init__(
        self,
        source: PolynomialMap,
        index: int,
        left: ElementaryAutomorphism | None = None,
        right: ElementaryAutomorphism | None = None,
    ) -> None:
        if not isinstance(source, PolynomialMap):
            raise TypeError("The source must be a PolynomialMap.")

        left = ElementaryAutomorphism() if left is None else left
        right = ElementaryAutomorphism() if right is None else right

        # DSC-4, the half of it that is a statement about the arguments rather
        # than about the arithmetic. What follows from the type is that each is
        # a product of factors ``X_j |-> X_j + P`` with ``P`` free of ``X_j``,
        # so the determinant is one and the inverse is the reversed product of
        # inverted factors. Neither is computed here or anywhere below.
        for automorphism, side in ((left, "left"), (right, "right")):
            if not isinstance(automorphism, ElementaryAutomorphism):
                raise TypeError(
                    f"The {side} change must be an ElementaryAutomorphism; "
                    f"got {type(automorphism).__name__}."
                )

        if not isinstance(index, int) or isinstance(index, bool):
            raise TypeError(f"The index must be an int; got {type(index).__name__}.")

        if not 0 <= index < source.dimension:
            raise ValueError(
                f"The index {index} is not a coordinate of a map in "
                f"{source.dimension} variables."
            )

        if source.dimension < 2:
            raise ValueError(
                "A descent from one variable would leave a map in none, and "
                "PolynomialMap has no such thing."
            )

        object.__setattr__(self, "_source", source)
        object.__setattr__(self, "_index", index)
        object.__setattr__(self, "_left", left)
        object.__setattr__(self, "_right", right)
        object.__setattr__(self, "_provenance", Provenance.SUPPLIED)
        object.__setattr__(self, "_verified", False)

    def __setattr__(self, name: str, value: object) -> None:
        raise AttributeError("DescentStep is immutable.")

    def __delattr__(self, name: str) -> None:
        raise AttributeError("DescentStep is immutable.")

    # ----------------------------------------------------------------------
    # Inspection
    # ----------------------------------------------------------------------

    @property
    def source(self) -> PolynomialMap:
        """Return the map the step starts from."""
        return self._source

    @property
    def index(self) -> int:
        """Return the coordinate that is deleted."""
        return self._index

    @property
    def left(self) -> ElementaryAutomorphism:
        """Return the change applied to the components."""
        return self._left

    @property
    def right(self) -> ElementaryAutomorphism:
        """Return the change applied to the variables."""
        return self._right

    @property
    def provenance(self) -> Provenance:
        """Return ``SUPPLIED``, always.

        DSC-7. This milestone gives the type no ``build``, so nothing can
        produce a ``CONSTRUCTED`` descent. The marker is doing its work rather
        than missing: a descent whose two changes came from a caller is a
        different object from one this library found, and until there is a
        search there is only the first kind.
        """
        return self._provenance

    @property
    def filtration_level(self) -> int | float:
        """Return ``math.inf``: the step makes no ``EA`` claim about its target.

        Its own two changes are elementary, which is a statement about the
        transformation and not about the map that comes out. ``TranslationStep``
        is where the page argues the distinction; the same argument applies
        here, one step further along.
        """
        return math.inf

    @property
    def ring(self) -> PolyRing:
        """Return the arithmetic context of the target.

        The source's domain and monomial order over the source's generators
        without the deleted one, equal to ``target.ring`` and independent of
        it.

        Built with ``clone_ring`` and not with ``PolyRing.clone``, which is
        what the first version called. That goes through SymPy's cache, so the
        property handed the same mutable object back on every access, and an
        audit of ``0.7.0rc1`` reached a caller's generator through it. The
        docstring of ``clone_ring`` records the failure that decision prevents.
        """
        return clone_ring(self._source.ring, self.variables)

    @property
    def variables(self) -> tuple[sp.Symbol, ...]:
        """Return the target's generators: the source's without the deleted one.

        DSC-2. In order, and no generator is fresh: the target is a map in
        coordinates the source already had, which is what tells a descent from
        a compression.
        """
        return tuple(
            variable
            for position, variable in enumerate(self._source.variables)
            if position != self._index
        )

    def conjugate(self) -> PolynomialMap:
        """Return ``left o source o right``, the map the deletion acts on."""
        return self._left.apply_to(
            self._source.compose(self._right.to_polynomial_map(self._source.ring))
        )

    def tail(self) -> sp.Expr:
        """Return what the deleted component displaces its variable by.

        The one thing the deletion throws away that cannot be recovered from
        the target, which is why the step offers it. Under DSC-3 it is free of
        the deleted variable, and DSC-6 is what it is for.
        """
        conjugate = self.conjugate()
        variable = self._source.variables[self._index]

        return sp.expand(conjugate.components[self._index] - variable)

    @property
    def target(self) -> PolynomialMap:
        """Return the map on the remaining coordinates.

        DSC-1. The components of the conjugate other than the deleted one, in
        their order. Derived on every access rather than stored, so that it
        cannot drift from the two automorphisms that determine it.

        The second half of DSC-3 is checked here and not only in ``verify``,
        and the components are carried over by ``reindex`` rather than read as
        expressions. The first version built the target from expressions, which
        re-infers a ring: an audit of ``0.7.0rc1`` found a source over ``QQ``
        giving a target over ``ZZ``, and over a finite field that changes the
        characteristic and with it the arithmetic of everything after the step.
        Reading the exponent vectors keeps the domain and the order.

        ``reindex`` drops the deleted generator, which is sound exactly when
        its exponent is zero in every surviving term. That is the second half
        of DSC-3, so the check above is what licenses the call rather than a
        convenience. Without it ``PolynomialMap`` would take the deleted
        coordinate into the coefficient domain and hand back a plausible map in
        which it had quietly become a parameter.
        """
        self._verify_free()
        conjugate = self.conjugate()
        kept = tuple(
            position
            for position in range(self._source.dimension)
            if position != self._index
        )
        reduced = clone_ring(
            conjugate.ring, tuple(conjugate.variables[position] for position in kept)
        )
        polynomials = conjugate.to_polynomials()

        return PolynomialMap.from_ring(
            reduced,
            tuple(reindex(polynomials[position], reduced, kept) for position in kept),
        )

    # ----------------------------------------------------------------------
    # Verification
    # ----------------------------------------------------------------------

    def verify(self) -> None:
        """Check DSC-3, DSC-5 and DSC-6's premise, or raise ``VerificationError``.

        DSC-3 comes first and is the whole of what a caller can get wrong.
        DSC-1 and DSC-2 are constructor invariants; DSC-4 is checked where the
        arguments arrive, because a wrong type is not a statement about
        arithmetic. DSC-5 follows from DSC-3 and is kept for the reason HOM-5
        to HOM-7 are kept, to name the step that made an error rather than the
        chain that carried it.
        """
        if self._verified:
            return

        self._verify_changes()
        self._verify_tail()
        self._verify_free()
        self._verify_determinant()

        object.__setattr__(self, "_verified", True)

    def _verify_changes(self) -> None:
        """DSC-4, the half that is a statement about the arithmetic.

        The two automorphisms have to be over the source's ring. Without this
        the mismatch surfaced from inside ``ElementaryAutomorphism.apply_to``
        as a bare ``ValueError`` naming neither the obligation nor the side it
        came from, which an audit of ``0.7.0rc1`` reported.

        An automorphism with no factors carries no ring and is admitted, as
        DSC-4 says.
        """
        for automorphism, side in ((self._left, "left"), (self._right, "right")):
            if not automorphism.factors:
                continue
            if automorphism.ring != self._source.ring:
                raise VerificationError(
                    "DSC-4",
                    f"The {side} change is an automorphism over "
                    f"{automorphism.ring.symbols} and the source is a map over "
                    f"{self._source.ring.symbols}. A change is applied to the "
                    "source and has to be over its ring.",
                )

    def _verify_tail(self) -> None:
        """DSC-3, first half: the deleted component is triangular."""
        self._verify_changes()
        conjugate = self.conjugate()
        variable = self._source.variables[self._index]

        tail = sp.expand(conjugate.components[self._index] - variable)
        if tail.has(variable):
            raise VerificationError(
                "DSC-3",
                f"Component {self._index} of the conjugate displaces "
                f"{variable} by {tail}, which is not free of {variable}. The "
                "two changes do not make that coordinate triangular.",
            )

    def _verify_free(self) -> None:
        """DSC-3, second half: nothing else mentions the deleted coordinate.

        What makes the deletion a deletion rather than a truncation. A
        surviving component that still mentions the coordinate would refer to
        a generator the target does not have.
        """
        self._verify_changes()
        conjugate = self.conjugate()
        variable = self._source.variables[self._index]

        for position, component in enumerate(conjugate.components):
            if position == self._index:
                continue
            if sp.expand(component).has(variable):
                raise VerificationError(
                    "DSC-3",
                    f"Component {position} of the conjugate mentions "
                    f"{variable}, the coordinate this step deletes. Deleting "
                    "it would leave a component referring to a generator the "
                    "target does not have.",
                )

    def _verify_determinant(self) -> None:
        """DSC-5.

        Under DSC-3 the Jacobian of the conjugate is block triangular with a
        one in the deleted place, and each of the two changes contributes one
        by DSC-4, so the two determinants agree. Checked rather than argued
        because the descent is the only move here that could lose the Keller
        property while lowering a dimension.
        """
        source = self._source.determinant()
        target = self.target.determinant()

        if sp.simplify(sp.expand(source - target)) != 0:  # pragma: no cover
            # Unreachable after DSC-3, which the line above has passed: the
            # deleted row and column of a triangular block contribute one, and
            # elementary automorphisms contribute one each.
            raise VerificationError(
                "DSC-5",
                f"The source has determinant {source} and the target "
                f"{target}. A descent deletes a triangular coordinate, which "
                "multiplies a Jacobian determinant by one.",
            )

    # ----------------------------------------------------------------------
    # Transport
    # ----------------------------------------------------------------------

    def transport(self, collision: Collision) -> Collision:
        """Carry a collision through the descent.

        DSC-6. A point of the source becomes a point of the target by undoing
        ``right`` and dropping the deleted coordinate. The image goes through
        ``left`` and drops the same coordinate, because the conjugate's image
        is ``left`` applied to the source's.

        The points stay distinct, which is not automatic for a projection. If
        two of them agreed, the two they come from agreed outside the deleted
        place and had one image under the conjugate; the deleted component is
        the variable plus a tail free of it, so their deleted coordinates
        agreed as well and the two points were one.
        """
        collision.verify(self._source)

        undone = self._right.inverse().to_polynomial_map(self._source.ring)
        moved = Collision(
            tuple(self._drop(undone(*point)) for point in collision.points),
            self._drop(
                self._left.to_polynomial_map(self._source.ring)(*collision.image)
            ),
        )
        moved.verify(self.target)

        return moved

    def _drop(self, vector: sp.ImmutableMatrix) -> tuple[sp.Expr, ...]:
        """Return the coordinates of ``vector`` other than the deleted one."""
        return tuple(
            sp.expand(vector[position])
            for position in range(self._source.dimension)
            if position != self._index
        )

    # ----------------------------------------------------------------------
    # Value semantics
    # ----------------------------------------------------------------------

    def _key(self) -> tuple[object, ...]:
        return (
            self._source,
            self._index,
            self._left,
            self._right,
            self._provenance,
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DescentStep):
            return NotImplemented
        return self._key() == other._key()

    def __hash__(self) -> int:
        return hash(self._key())

    def __repr__(self) -> str:
        return (
            f"DescentStep(dimension={self._source.dimension}->"
            f"{self._source.dimension - 1}, index={self._index}, "
            f"provenance={self._provenance.value})"
        )
