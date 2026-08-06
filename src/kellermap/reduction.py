"""Steps and chains of them: the induction a reduction carries out.

A reduction is a sequence of steps, each certifying one identity between two
polynomial maps. ``Reduction`` verifies the steps and the adjacency between
them, and nothing else -- that the final map is a Keller map, or has a given
degree, follows from the local certificates rather than from a second,
independent computation.

Nothing here is specific to Bass-Connell-Wright. ``LinearStep`` composes an
element of ``GL_n(k)`` on the left and ``TranslationStep`` composes a
translation on the left, which is what the two outer factors of Chapter II,
Proposition (1.1) of the paper do but is not a notion of that paper;
``Reduction`` chains anything satisfying ``Step``. The Proposition (3.1) step
lives in ``kellermap.bcw``, where the paper-specific machinery belongs.

Proposition (1.1) splits a map with invertible linear part as

    F = (X + F(0)) o F_(1) o F'      with F' in MA^1,

so the two steps here come off in that order: ``TranslationStep.normalize``
first, then ``LinearStep.normalize``. They are two types rather than one
because a translation is affine and not linear -- it is no element of
``GL_n(k)``, and widening ``LinearAutomorphism`` to hold one would break the
two things that type exists for, its matrix and its structural determinant.

See ``docs/contracts.md`` for the obligations, STEP-1 to STEP-5, LIN-1 to
LIN-6, TRA-1 to TRA-8 and RED-1 to RED-8.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from enum import Enum
from typing import Any, Protocol, overload, runtime_checkable

import sympy as sp
from sympy.polys.polyerrors import CoercionFailed
from sympy.polys.rings import PolyRing

from .canonical import agree, canonical, is_zero
from .collision import Collision
from .elementary import ElementaryAutomorphism, ElementaryFactor
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

    The normalization of BCW Chapter II, Proposition (1.1) is the case that
    matters here, and it
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
        Whether the step claims to be the normalization of Proposition (1.1).
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
        """Build the linear normalization of ``source``.

        BCW Chapter II, Proposition (1.1) splits a map with invertible linear
        part as ``F = (X + F(0)) o F_(1) o F'`` with ``F' in MA^1``. This
        builds the second factor, ``F' = F_(1)^-1 o F``, and therefore
        presupposes the first: ``source`` must already satisfy ``F(0) = 0``.

        The first factor is ``TranslationStep``. This method does not insert
        one of its own: Proposition (1.1) has three factors, and a
        ``Reduction`` shows all three rather than folding two of them into one
        step whose name mentions only one.

        The coefficient domain has to be a field for the inverse to exist;
        ``over_field`` first, otherwise.
        """
        if not source.is_in_MA(0):
            raise ValueError(
                "The map does not fix the origin, so the linear normalization "
                "is not the first step: Proposition (1.1) splits F as "
                "(X + F(0)) o F_(1) o F', and the translation (X - F(0)) has "
                "to come off first. Use TranslationStep.normalize on this map "
                "and normalize its target."
            )

        linear_part = sp.Matrix(
            source.jacobian().xreplace(
                {variable: sp.Integer(0) for variable in source.variables}
            )
        )

        if linear_part.det() == 0:
            raise ValueError(
                "The linear part at the origin is singular; the map is not "
                "invertible there and Proposition (1.1) does not apply."
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
        if (  # pragma: no cover - group law, not data
            inverse.apply_to(self._transformation.apply_to(identity)) != identity
        ):
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

        if not agree(  # pragma: no cover - implied by LIN-1
            self._target.determinant(), expected
        ):
            raise VerificationError(
                "LIN-3",
                f"The target has determinant {self._target.determinant()}, "
                f"but the step accounts for {expected}.",
            )

    def _verify_normalization(self) -> None:
        if not self._source.is_in_MA(0):
            raise VerificationError(
                "LIN-6",
                "The step claims to normalize, but the source does not fix "
                "the origin; Proposition (1.1) puts a translation before the "
                "linear part.",
            )

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

        # Nicht erreichbar: LIN-1 laeuft vorher, die Quelle liegt in MA^0 und
        # die Transformation ist die Inverse des Linearteils -- damit ist der
        # Linearteil des Ziels die Identitaet.
        if not self._target.is_in_MA(1):  # pragma: no cover - implied by LIN-1
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
class TranslationStep:
    """``target = (X - shift) o source`` for a constant ``shift``.

    The first factor of BCW Chapter II, Proposition (1.1), which splits a map
    with invertible linear part as ``F = (X + F(0)) o F_(1) o F'``. A source
    outside ``MA^0`` cannot be normalized linearly until this has come off,
    and ``LinearStep.normalize`` refuses such a source rather than inserting a
    translation of its own.

    The step is elementary in the sense of the paper: ``X_i |-> X_i - c_i``
    displaces ``X_i`` by a constant, which is free of ``X_i``, so
    ``translation`` exhibits it as an ``ElementaryAutomorphism``. It belongs
    to no ``EA^d`` for ``d >= 0`` all the same, since a translation leaves
    ``MA^0`` and its filtration degree is ``-1``. What the *step* reports as
    ``filtration_level`` is ``math.inf``, not ``-1``: see the property.

    It is not an application of Proposition (3.1) and is not a ``BCWStep``. It
    removes no product, names no target component and buys no carrier; a
    ``BCWStep`` with both slots carried would state three things that are not
    the case.

    Parameters
    ----------
    source, target
        The two maps. ``target`` supplied here is what makes TRA-1 a real
        check; see ``build`` and ``normalize`` for the constructed case.
    shift
        The constant vector ``c``, one entry per coordinate. Each entry is
        converted into the coefficient domain of the source, so a parameter of
        that domain is admitted and a generator is not.
    normalizing
        Whether the step claims to be the translation of Proposition (1.1),
        which turns on TRA-6.
    """

    _source: PolynomialMap
    _target: PolynomialMap
    _shift: tuple[sp.Expr, ...]
    _normalizing: bool
    _provenance: Provenance
    _verified: bool

    def __init__(
        self,
        source: PolynomialMap,
        target: PolynomialMap,
        shift: Iterable[sp.Expr],
        normalizing: bool = False,
    ) -> None:
        if not isinstance(source, PolynomialMap):
            raise TypeError("The source must be a PolynomialMap.")
        if not isinstance(target, PolynomialMap):
            raise TypeError("The target must be a PolynomialMap.")

        if source.dimension != target.dimension:
            raise ValueError(
                f"The source has dimension {source.dimension}, "
                f"the target {target.dimension}; a translation keeps it."
            )

        entries = self._coerce_shift(source, shift)

        object.__setattr__(self, "_source", source)
        object.__setattr__(self, "_target", target)
        object.__setattr__(self, "_shift", entries)
        object.__setattr__(self, "_normalizing", bool(normalizing))
        object.__setattr__(self, "_provenance", Provenance.SUPPLIED)
        object.__setattr__(self, "_verified", False)

    @staticmethod
    def _coerce_shift(
        source: PolynomialMap,
        shift: Iterable[sp.Expr],
    ) -> tuple[sp.Expr, ...]:
        """Convert every entry into the coefficient domain, and keep it there.

        TRA-2 is enforced by conversion rather than by inspection, in the shape
        of BCW-3. An entry involving a generator does not lie in the domain and
        raises here, so a shift that varies with the point cannot be built at
        all and TRA-2 has no verify-time code. A parameter of the domain passes,
        because a translation by ``T`` over ``k[T]`` is a translation.

        The round trip through the domain also settles what equality of two
        shifts means, which ``__eq__`` then gets for nothing.
        """
        entries = tuple(shift)

        if len(entries) != source.dimension:
            raise ValueError(
                f"The shift has {len(entries)} entries, but the source has "
                f"dimension {source.dimension}."
            )

        domain = source.ring.domain
        converted: list[sp.Expr] = []
        for position, entry in enumerate(entries):
            try:
                converted.append(domain.to_sympy(domain.from_sympy(canonical(entry))))
            except (CoercionFailed, sp.SympifyError) as error:
                raise ValueError(
                    f"Entry {position} of the shift, {entry}, does not lie in "
                    f"the coefficient domain {domain}; a translation is by a "
                    "constant, and an entry involving a generator would not "
                    "have the identity as its Jacobian."
                ) from error

        return tuple(converted)

    @classmethod
    def build(
        cls,
        source: PolynomialMap,
        shift: Iterable[sp.Expr],
        normalizing: bool = False,
    ) -> TranslationStep:
        """Apply the translation and record the result as constructed.

        Convenient, and weaker evidence: TRA-1 then compares the
        implementation against itself. As for ``LinearStep``, this and
        ``normalize`` are the only routes to a ``CONSTRUCTED`` step.
        """
        entries = cls._coerce_shift(source, shift)
        step = cls(
            source,
            _translation(source.ring, entries).apply_to(source),
            entries,
            normalizing=normalizing,
        )
        object.__setattr__(step, "_provenance", Provenance.CONSTRUCTED)

        return step

    @classmethod
    def normalize(cls, source: PolynomialMap) -> TranslationStep:
        """Build the translation that carries ``source`` into ``MA^0``.

        The shift is ``F(0)``, so the target satisfies ``F(0) = 0`` and
        ``LinearStep.normalize`` accepts it.

        A source already in ``MA^0`` is not refused. Its shift is zero, the
        target equals the source, and the step is the identity -- a true
        statement, and simpler than a special case in every caller that does
        not know in advance whether its map fixes the origin.
        """
        origin = (sp.Integer(0),) * source.dimension

        return cls.build(source, tuple(source(*origin)), normalizing=True)

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
    def shift(self) -> tuple[sp.Expr, ...]:
        """Return the constant vector that was subtracted."""
        return self._shift

    @property
    def translation(self) -> ElementaryAutomorphism:
        """Return ``X |-> X - shift`` as an exhibited factorization.

        One factor per non-zero entry, in ascending order of index. The order
        is immaterial, since the displacements are constants and the factors
        commute; ascending is chosen so that two equal shifts give equal
        objects.
        """
        return _translation(self._source.ring, self._shift)

    @property
    def provenance(self) -> Provenance:
        """Return whether the target was supplied or constructed."""
        return self._provenance

    @property
    def is_normalizing(self) -> bool:
        """Return whether the step claims to be the translation of (1.1)."""
        return self._normalizing

    @property
    def filtration_level(self) -> int | float:
        """Return ``math.inf``: a translation establishes no ``EA`` level.

        The transformation has filtration degree ``-1`` -- available as
        ``translation.filtration_degree()`` -- and that is a property of the
        transformation, not a bound the step establishes for its target.
        Reporting ``-1`` here would make ``Reduction.filtration_level`` return
        ``-1`` for every chain that begins with a translation, which says
        nothing about that chain's target.
        """
        return math.inf

    # ----------------------------------------------------------------------
    # Verification
    # ----------------------------------------------------------------------

    def verify(self) -> None:
        """Check TRA-1, TRA-3 and TRA-4, and TRA-6 where it is claimed."""
        if self._verified:
            return

        self._verify_identity()
        self._verify_factorization()
        self._verify_determinant()
        if self._normalizing:
            self._verify_normalization()

        object.__setattr__(self, "_verified", True)

    def _verify_identity(self) -> None:
        if self.translation.apply_to(self._source) != self._target:
            raise VerificationError(
                "TRA-1",
                "The target is not the source translated by the shift.",
            )

    def _verify_factorization(self) -> None:
        """Check that the exhibited inverse undoes the translation.

        ``X_i |-> X_i + c_i``, read off the definition rather than solved. A
        self-check of the group law, which cannot fail on supplied data.
        """
        exhibited = self.translation
        ring = self._source.ring
        identity = PolynomialMap.from_ring(ring, ring.gens)

        if (  # pragma: no cover - group law, not data
            exhibited.inverse().apply_to(exhibited.apply_to(identity)) != identity
        ):
            raise VerificationError(
                "TRA-3",
                "The exhibited inverse does not undo the translation.",
            )

    def _verify_determinant(self) -> None:
        """Check that the determinant is unchanged.

        The Jacobian of a translation is the identity matrix, so this is
        implied by TRA-1 and retained as a cheap self-check, in the shape of
        BCW-7.
        """
        if not agree(  # pragma: no cover - implied by TRA-1
            self._target.determinant(), self._source.determinant()
        ):
            raise VerificationError(
                "TRA-4",
                f"The target has determinant {self._target.determinant()}, "
                f"but the source has {self._source.determinant()}; a "
                "translation leaves it alone.",
            )

    def _verify_normalization(self) -> None:
        origin = (sp.Integer(0),) * self._source.dimension
        expected = tuple(self._source(*origin))

        if not all(
            agree(entry, value)
            for entry, value in zip(self._shift, expected, strict=True)
        ):
            raise VerificationError(
                "TRA-6",
                "The step claims to be the translation of Proposition (1.1), "
                f"but the shift is {self._shift} and F(0) is {expected}.",
            )

        # Nicht erreichbar: TRA-1 laeuft vorher und die erste Klausel oben
        # ebenfalls, also ist das Ziel F - F(0) und verschwindet im Ursprung.
        if not self._target.is_in_MA(0):  # pragma: no cover - implied by TRA-1
            raise VerificationError(
                "TRA-6",
                "The step claims to normalize, but the target does not lie in MA^0.",
            )

    def transport(self, collision: Collision) -> Collision:
        """Move the image by ``-shift`` and leave every preimage where it is.

        Left composition does not touch preimages, as in LIN-5.
        """
        collision.verify(self._source)

        moved = collision.with_image(
            tuple(
                canonical(entry - value)
                for entry, value in zip(collision.image, self._shift, strict=True)
            )
        )
        moved.verify(self._target)

        return moved

    # ----------------------------------------------------------------------

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TranslationStep):
            return NotImplemented
        return (
            self._source == other._source
            and self._target == other._target
            and self._shift == other._shift
            and self._normalizing == other._normalizing
            and self._provenance is other._provenance
        )

    def __hash__(self) -> int:
        return hash(
            (
                self._source,
                self._target,
                self._shift,
                self._normalizing,
                self._provenance,
            )
        )

    def __repr__(self) -> str:
        return (
            f"TranslationStep(dimension={self._source.dimension}, "
            f"shift={self._shift}, "
            f"normalizing={self._normalizing}, "
            f"provenance={self._provenance.value})"
        )


def _translation(ring: PolyRing, shift: tuple[sp.Expr, ...]) -> ElementaryAutomorphism:
    """Return ``X |-> X - shift`` as a product of elementary factors.

    A zero entry contributes no factor, so a zero shift gives the identity,
    which is the empty product and carries no ring. That is the same convention
    ``ElementaryAutomorphism`` already uses.
    """
    domain: Any = ring.domain

    return ElementaryAutomorphism(
        ElementaryFactor(ring, index, ring.ground_new(-domain.from_sympy(entry)))
        for index, entry in enumerate(shift)
        if not is_zero(entry)
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
