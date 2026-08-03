"""Steps and chains of them: the induction a reduction carries out.

A reduction is a sequence of steps, each certifying one identity between two
polynomial maps. ``Reduction`` verifies the steps and the adjacency between
them, and nothing else -- that the final map is a Keller map, or has a given
degree, follows from the local certificates rather than from a second,
independent computation.

Nothing here is specific to Bass-Connell-Wright. ``LinearStep`` composes an
element of ``GL_n(k)`` on the left, which is what Section 4 of the paper opens
with but is not a notion of that paper; ``Reduction`` chains anything
satisfying ``Step``. The Proposition (3.1) step lives in ``kellermap.bcw``,
where the paper-specific machinery belongs.

See ``docs/contracts.md`` for the obligations, STEP-1 to STEP-5, LIN-1 to
LIN-6 and RED-1 to RED-8.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from enum import Enum
from typing import Protocol, overload, runtime_checkable

import sympy as sp

from .canonical import agree, is_zero
from .collision import Collision
from .errors import VerificationError
from .linear import LinearAutomorphism
from .polynomial_map import PolynomialMap


class Provenance(Enum):
    """Where the target of a step came from.

    The distinction is the point of milestone 0.2 and has to survive into any
    review. For a ``SUPPLIED`` step, the identity obligation compares an
    externally computed map against the formula and can fail. For a
    ``CONSTRUCTED`` one it compares the implementation against itself and
    cannot: that is a self-check, not evidence.
    """

    SUPPLIED = "supplied"
    CONSTRUCTED = "constructed"


@runtime_checkable
class Step(Protocol):
    """One certified identity between two polynomial maps.

    A protocol rather than a base class: a step is anything that can say what
    it starts from, what it reaches, how it got there, and how to carry a
    collision across. Nothing has to inherit from anything to qualify.
    """

    @property
    def source(self) -> PolynomialMap:
        """Return the map the step starts from."""

    @property
    def target(self) -> PolynomialMap:
        """Return the map the step reaches."""

    @property
    def provenance(self) -> Provenance:
        """Return whether the target was supplied or constructed."""

    @property
    def filtration_level(self) -> int | float:
        """Return the ``EA`` level the step establishes.

        ``math.inf`` where the step constrains nothing, following
        ``ElementaryAutomorphism.filtration_degree()`` on the identity.
        """

    def verify(self) -> None:
        """Check every obligation, or raise ``VerificationError``."""

    def transport(self, collision: Collision) -> Collision:
        """Carry a collision of ``source`` to one of ``target``."""


@dataclass(frozen=True, eq=False)
class LinearStep:
    """``target = transformation o source`` for an element of ``GL_n(k)``.

    The normalization of BCW Section 4 is the case that matters here, and it
    is declared rather than inferred: ``normalizing`` turns on LIN-6, which
    demands that the transformation be the inverse of ``J(source)(0)`` and the
    target land in ``MA^1``. A linear step that makes no such claim carries no
    such obligation.

    This is the only kind of step permitted to change the Jacobian
    determinant, and LIN-3 requires it to say by what factor.

    Parameters
    ----------
    source, target
        The two maps. ``target`` supplied here is what makes LIN-1 a real
        check; see ``build`` and ``normalize`` for the constructed case.
    transformation
        The element of ``GL_n(k)``, as an exhibited factorization.
    normalizing
        Whether the step claims to be the normalization of Section 4.
    """

    _source: PolynomialMap
    _target: PolynomialMap
    _transformation: LinearAutomorphism
    _normalizing: bool
    _provenance: Provenance
    _verified: bool

    def __init__(
        self,
        source: PolynomialMap,
        target: PolynomialMap,
        transformation: LinearAutomorphism,
        normalizing: bool = False,
    ) -> None:
        if not isinstance(source, PolynomialMap):
            raise TypeError("The source must be a PolynomialMap.")
        if not isinstance(target, PolynomialMap):
            raise TypeError("The target must be a PolynomialMap.")
        if not isinstance(transformation, LinearAutomorphism):
            raise TypeError("The transformation must be a LinearAutomorphism.")

        if source.dimension != target.dimension:
            raise ValueError(
                f"The source has dimension {source.dimension}, "
                f"the target {target.dimension}; a linear step keeps it."
            )

        object.__setattr__(self, "_source", source)
        object.__setattr__(self, "_target", target)
        object.__setattr__(self, "_transformation", transformation)
        object.__setattr__(self, "_normalizing", bool(normalizing))
        object.__setattr__(self, "_provenance", Provenance.SUPPLIED)
        object.__setattr__(self, "_verified", False)

    @classmethod
    def build(
        cls,
        source: PolynomialMap,
        transformation: LinearAutomorphism,
        normalizing: bool = False,
    ) -> LinearStep:
        """Apply the transformation and record the result as constructed.

        Convenient, and weaker evidence: LIN-1 then compares the
        implementation against itself.

        This is the only way to obtain a ``CONSTRUCTED`` step. The public
        constructor always records ``SUPPLIED``, since a target reaching it
        came from outside. The marker guards against mislabelling by accident,
        not against a caller determined to forge one -- Python has no privacy,
        and the attribute can be overwritten by anyone who wants to.
        """
        step = cls(
            source,
            transformation.apply_to(source),
            transformation,
            normalizing=normalizing,
        )
        object.__setattr__(step, "_provenance", Provenance.CONSTRUCTED)

        return step

    @classmethod
    def normalize(cls, source: PolynomialMap) -> LinearStep:
        """Build the normalization of BCW Section 4 for ``source``.

        ``F'' = F'_(1)^-1 o F'``. The coefficient domain has to be a field for
        the inverse to exist; ``over_field`` first, otherwise.
        """
        linear_part = sp.Matrix(
            source.jacobian().xreplace(
                {variable: sp.Integer(0) for variable in source.variables}
            )
        )

        if linear_part.det() == 0:
            raise ValueError(
                "The linear part at the origin is singular; the map is not "
                "invertible there and Section 4 does not apply."
            )

        return cls.build(
            source,
            LinearAutomorphism.factorize(source.ring, linear_part.inv()),
            normalizing=True,
        )

    # ----------------------------------------------------------------------
    # Inspection
    # ----------------------------------------------------------------------

    @property
    def source(self) -> PolynomialMap:
        """Return the map the step starts from."""
        return self._source

    @property
    def target(self) -> PolynomialMap:
        """Return the map the step reaches."""
        return self._target

    @property
    def transformation(self) -> LinearAutomorphism:
        """Return the element of ``GL_n(k)`` that was composed on the left."""
        return self._transformation

    @property
    def provenance(self) -> Provenance:
        """Return whether the target was supplied or constructed.

        Part of the value of the step, not metadata beside it: it is publicly
        observable, so two steps that disagree about it are not equal.
        """
        return self._provenance

    @property
    def is_normalizing(self) -> bool:
        """Return whether the step claims to be the normalization."""
        return self._normalizing

    @property
    def is_elementary(self) -> bool:
        """Return whether the exhibited factorization stays in ``EA_n(k)``.

        Usually false, and LIN-4 does not require otherwise: the
        transformation of a normalization generally has a determinant other
        than one, and no element of ``EA_n(k)`` does.
        """
        return self._transformation.is_elementary

    @property
    def filtration_level(self) -> int | float:
        """Return ``math.inf``: a linear step constrains no ``EA`` level.

        It composes on the left, and its transformation is generally not in
        ``EA_n(k)`` at all, so it establishes no lower bound that
        ``Reduction.filtration_level`` would have to respect.
        """
        return math.inf

    # ----------------------------------------------------------------------
    # Verification
    # ----------------------------------------------------------------------

    def verify(self) -> None:
        """Check LIN-1 to LIN-3, and LIN-6 where it is claimed."""
        if self._verified:
            return

        self._verify_identity()
        self._verify_factorization()
        self._verify_determinant()
        if self._normalizing:
            self._verify_normalization()

        object.__setattr__(self, "_verified", True)

    def _verify_identity(self) -> None:
        try:
            composed = self._transformation.apply_to(self._source)
        except ValueError as error:
            raise VerificationError(
                "LIN-1",
                f"The transformation cannot act on the source: {error}",
            ) from error

        if composed != self._target:
            raise VerificationError(
                "LIN-1",
                "The target is not the transformation applied to the source.",
            )

    def _verify_factorization(self) -> None:
        """Check that the exhibited inverse undoes the transformation.

        That the factors multiply to the declared matrix is structural rather
        than checkable: ``LinearAutomorphism.matrix()`` *is* that product, and
        no second, independently declared matrix is stored to compare it
        against -- deliberately, for the reason ``BCWStep`` derives ``G`` and
        ``H`` instead of storing them. What remains is a self-check of the
        group law, which cannot fail on supplied data but would catch an error
        in a factor's inverse.
        """
        ring = self._source.ring
        identity = PolynomialMap.from_ring(ring, ring.gens)

        inverse = self._transformation.inverse()
        if inverse.apply_to(self._transformation.apply_to(identity)) != identity:
            raise VerificationError(
                "LIN-2",
                "The exhibited inverse does not undo the transformation.",
            )

    def _verify_determinant(self) -> None:
        """Check the determinant bookkeeping.

        Implied by LIN-1 and retained anyway: it is two multiplications on
        maps a reduction produces, and it catches an error in a factor's
        determinant before that error propagates through a whole chain.

        The canonical comparison is defensive here rather than load-bearing.
        Both determinants come out of a ``PolyRing``, where the domain has
        already normalized them; no non-canonical value could reach this
        point. It is used anyway so that the package has one answer to what
        equality of values means.
        """
        expected = self._transformation.determinant() * self._source.determinant()

        if not agree(self._target.determinant(), expected):
            raise VerificationError(
                "LIN-3",
                f"The target has determinant {self._target.determinant()}, "
                f"but the step accounts for {expected}.",
            )

    def _verify_normalization(self) -> None:
        linear_part = sp.Matrix(
            self._source.jacobian().xreplace(
                {variable: sp.Integer(0) for variable in self._source.variables}
            )
        )

        if linear_part.det() == 0:
            raise VerificationError(
                "LIN-6",
                "The linear part of the source at the origin is singular.",
            )

        declared = sp.Matrix(self._transformation.matrix(self._source.ring))
        deviation = declared - linear_part.inv()
        if not all(is_zero(entry) for entry in deviation):
            raise VerificationError(
                "LIN-6",
                "The step claims to normalize, but the transformation is not "
                "the inverse of the linear part at the origin.",
            )

        if not self._target.is_in_MA(1):
            raise VerificationError(
                "LIN-6",
                "The step claims to normalize, but the target does not lie in MA^1.",
            )

    def transport(self, collision: Collision) -> Collision:
        """Move the image and leave every preimage where it is.

        Left composition does not touch preimages. This is why the collision
        of BCW17 carries Alpoege's points verbatim in its first three
        coordinates while its image has moved.
        """
        collision.verify(self._source)

        matrix = sp.Matrix(self._transformation.matrix(self._source.ring))
        moved = collision.with_image(
            tuple(sp.expand(entry) for entry in matrix * sp.Matrix(collision.image))
        )
        moved.verify(self._target)

        return moved

    # ----------------------------------------------------------------------

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, LinearStep):
            return NotImplemented
        return (
            self._source == other._source
            and self._target == other._target
            and self._transformation == other._transformation
            and self._normalizing == other._normalizing
            and self._provenance is other._provenance
        )

    def __hash__(self) -> int:
        return hash(
            (
                self._source,
                self._target,
                self._transformation,
                self._normalizing,
                self._provenance,
            )
        )

    def __repr__(self) -> str:
        return (
            f"LinearStep(dimension={self._source.dimension}, "
            f"determinant={self._transformation.determinant()}, "
            f"normalizing={self._normalizing}, "
            f"provenance={self._provenance.value})"
        )


@dataclass(frozen=True, eq=False)
class Reduction:
    """A chain of steps, and the induction over it.

    ``verify`` checks every step and the adjacency between them, and stops
    there. That the target is a Keller map, or has degree three, follows from
    the local certificates; recomputing it would be a second and independent
    argument, which is not what a certificate is for. What the chain reports
    -- degrees, dimensions, filtration -- it reports rather than constrains.
    """

    steps: tuple[Step, ...]

    def __init__(self, steps: Iterable[Step]) -> None:
        collected = tuple(steps)

        if not collected:
            raise ValueError(
                "A reduction needs at least one step, so that its source and "
                "target are defined."
            )

        for position, step in enumerate(collected):
            if not isinstance(step, Step):
                raise TypeError(
                    f"Element {position} does not satisfy the Step protocol."
                )

        object.__setattr__(self, "steps", collected)

    @property
    def source(self) -> PolynomialMap:
        """Return the map the chain starts from."""
        return self.steps[0].source

    @property
    def target(self) -> PolynomialMap:
        """Return the map the chain reaches."""
        return self.steps[-1].target

    @property
    def provenance(self) -> Provenance:
        """Return ``SUPPLIED`` only if every step is supplied."""
        if all(step.provenance is Provenance.SUPPLIED for step in self.steps):
            return Provenance.SUPPLIED

        return Provenance.CONSTRUCTED

    def filtration_level(self) -> int | float:
        """Return the smallest ``EA`` level any step establishes.

        This is what answers, from the certificate alone, why the target lies
        in the filtration stage it does. Steps that constrain nothing report
        ``math.inf`` and do not lower it.
        """
        return min(step.filtration_level for step in self.steps)

    def degrees(self) -> tuple[int, ...]:
        """Return the degree of the source and of every intermediate map."""
        return (self.source.degree(),) + tuple(
            step.target.degree() for step in self.steps
        )

    def dimensions(self) -> tuple[int, ...]:
        """Return the dimension of the source and of every intermediate map."""
        return (self.source.dimension,) + tuple(
            step.target.dimension for step in self.steps
        )

    # ----------------------------------------------------------------------
    # Verification
    # ----------------------------------------------------------------------

    def verify(self) -> None:
        """Check every step and every join, or raise ``VerificationError``.

        Failures are located: the exception names the index of the step that
        failed, which a step cannot know about itself.
        """
        for position, step in enumerate(self.steps):
            try:
                step.verify()
            except VerificationError as failure:
                raise failure.located_at(position) from failure

        self._verify_adjacency()

    def _verify_adjacency(self) -> None:
        for position in range(len(self.steps) - 1):
            if self.steps[position].target != self.steps[position + 1].source:
                raise VerificationError(
                    "RED-2",
                    "The target of one step is not the source of the next.",
                    position + 1,
                )

    def transport(self, collision: Collision) -> Collision:
        """Carry a collision of ``source`` through to one of ``target``.

        Every step verifies the collision it receives and the one it returns,
        so a chain that completes has checked the counterexample at every
        intermediate map, not only at the ends.
        """
        collision.verify(self.source)

        carried = collision
        for position, step in enumerate(self.steps):
            try:
                carried = step.transport(carried)
            except VerificationError as failure:
                raise failure.located_at(position) from failure

        carried.verify(self.target)

        return carried

    # ----------------------------------------------------------------------

    def __len__(self) -> int:
        return len(self.steps)

    def __iter__(self) -> Iterator[Step]:
        return iter(self.steps)

    @overload
    def __getitem__(self, index: int) -> Step: ...

    @overload
    def __getitem__(self, index: slice) -> Reduction: ...

    def __getitem__(self, index: int | slice) -> Step | Reduction:
        if isinstance(index, slice):
            return Reduction(self.steps[index])

        return self.steps[index]

    def __add__(self, other: Reduction) -> Reduction:
        if not isinstance(other, Reduction):
            return NotImplemented

        return Reduction(self.steps + other.steps)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Reduction):
            return NotImplemented
        return self.steps == other.steps

    def __hash__(self) -> int:
        return hash(self.steps)

    def __repr__(self) -> str:
        return (
            f"Reduction(steps={len(self.steps)}, "
            f"dimensions={self.dimensions()}, "
            f"degrees={self.degrees()}, "
            f"provenance={self.provenance.value})"
        )
