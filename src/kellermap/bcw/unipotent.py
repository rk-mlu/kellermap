"""The second step of the Reduction Theorem, BCW Chapter II, Section 4, p. 306.

The first step lowers the degree to three. This one doubles the dimension and
makes the Jacobian of the displacement nilpotent. Given ``F = X + F_(2) +
F_(3)`` in ``MA^1_n(k)``, the paper works over ``k[T]`` with

    E(T) = X + T F_(2) + T^2 F_(3),
    G(T) = (X + T Y, Y),
    H(T) = (X, Y - T F_(3)),

so that ``J(E(T)) = J(F)(TX)`` and

    G(T) o E(T)^[n] o H(T) = (X, Y) + N T,   N = (F_(2) + Y, -F_(3)).

The Jacobian of that composition is ``I + J(N) T`` and is invertible over
``k[T]``, so Lemma (4.1) gives that ``J(N)`` is nilpotent.

The certificate is the composition at ``T = 1``. The parameter carries the
grading Lemma (4.1) needs and nothing else: the identity

    target = G o F^[n] o H,   target = (X + F_(2) + Y, Y - F_(3)),

holds without it, and it is that identity a reader checks. What the parameter
buys is the nilpotence, and UNI-9 establishes that separately and by a
different route.

Two things follow from the shape of the result and are worth stating before a
caller trips over them. The target is not in ``MA^1``: its displacement has the
linear part ``(Y, 0)``. And the step doubles the dimension, so a chain applies
it once, at the end, and not repeatedly -- UNI-2 refuses its own target.

There is nothing here to search for. Every other step type in this package has
a choice in it; given a source, this one is determined up to the names of the
fresh generators.

See ``docs/contracts.md``, UNI-1 to UNI-12.
"""

from __future__ import annotations

from dataclasses import dataclass

import sympy as sp
from sympy.polys.rings import PolyElement, PolyRing

from ..canonical import agree
from ..collision import Collision
from ..context import ReductionContext
from ..elementary import ElementaryAutomorphism, ElementaryFactor
from ..errors import VerificationError
from ..polynomial_map import PolynomialMap
from ..reduction import Provenance
from ..variables import FixedVariableFactory, VariableFactory, reserved_names

FILTRATION_LEVEL = 0
"""The ``EA`` level the step establishes. See UNI-7."""


def homogeneous_part(polynomial: PolyElement, degree: int) -> PolyElement:
    """Return the part of ``polynomial`` homogeneous of ``degree``.

    Total degree in the generators of the ring, so a parameter of the
    coefficient domain does not count towards it. That is the reading the whole
    package uses: ``T x`` over ``k[T]`` is linear in ``x``, and ``PolynomialMap.degree``
    says one.
    """
    ring = polynomial.ring
    terms = [
        (monomial, coefficient)
        for monomial, coefficient in polynomial.iterterms()
        if sum(monomial) == degree
    ]

    return ring.from_terms(terms) if terms else ring.zero


@dataclass(frozen=True, eq=False)
class UnipotentStep:
    """One application of Section 4's second step.

    ``G`` and ``H`` are derived from the source and the fresh variables. They
    are never supplied alongside them: storing both a factorization and the
    automorphisms built from it would allow the two to disagree.

    Parameters
    ----------
    source, target
        The maps before and after. A ``target`` supplied here is what makes
        UNI-1 a real check; ``build`` computes it instead and records the
        weaker provenance. UNI-2, UNI-3 and UNI-4 constrain the *source* and
        can fail on either route.
    variables
        The ``n`` fresh generators, the ``Y`` of the formula, in the order the
        target carries them.
    """

    _source: PolynomialMap
    _target: PolynomialMap
    _variables: tuple[sp.Symbol, ...]
    _provenance: Provenance
    _verified: bool

    def __init__(
        self,
        source: PolynomialMap,
        target: PolynomialMap,
        variables: tuple[sp.Symbol, ...],
    ) -> None:
        if not isinstance(source, PolynomialMap):
            raise TypeError("The source must be a PolynomialMap.")
        if not isinstance(target, PolynomialMap):
            raise TypeError("The target must be a PolynomialMap.")

        fresh = tuple(variables)
        for variable in fresh:
            if not isinstance(variable, sp.Symbol):
                raise TypeError("Every fresh variable must be a SymPy symbol.")

        # UNI-5, the counting half. A constructor invariant, because the
        # formula introduces one generator per component of the source and a
        # different count describes no step at all.
        if len(fresh) != source.dimension:
            raise ValueError(
                f"The step introduces one generator per component: expected "
                f"{source.dimension} fresh variables, got {len(fresh)}."
            )

        # By name, and not by ``Symbol.__eq__``: ``Symbol("v")`` and
        # ``Symbol("v", positive=True)`` are two symbols for SymPy and one
        # generator for a ``PolyRing``. Same reading as BCW-3.
        names = [variable.name for variable in fresh]
        if len(set(names)) != len(names):
            raise ValueError(
                "The fresh variables must be distinct; "
                f"got {sorted(names)} with a repetition."
            )

        # Early, and not first in verify(). A colliding name can no longer be
        # told apart from a wrong target afterwards, because the extension
        # would then let two coordinates denote one generator. Against the
        # reserved names and not only the coordinates: a parameter of the
        # coefficient domain is taken as well.
        taken = set(names) & reserved_names(source.ring)
        if taken:
            raise ValueError(
                f"The variables {sorted(taken)} are already in use by the source."
            )

        object.__setattr__(self, "_source", source)
        object.__setattr__(self, "_target", target)
        object.__setattr__(self, "_variables", fresh)
        object.__setattr__(self, "_provenance", Provenance.SUPPLIED)
        object.__setattr__(self, "_verified", False)

    @classmethod
    def build(
        cls,
        source: PolynomialMap,
        factory: VariableFactory | None = None,
    ) -> UnipotentStep:
        """Apply the formula and record the result as constructed.

        Convenient, and weaker evidence for UNI-1, which then compares the
        implementation against itself. UNI-2, UNI-3 and UNI-4 are not weakened
        by this route: they constrain the source, which is supplied either way,
        and ``build`` neither checks nor repairs them. A step built from a
        source outside ``MA^1`` is built and fails to verify.

        This is the only way to obtain a ``CONSTRUCTED`` step. The public
        constructor always records ``SUPPLIED``, since a target reaching it
        came from outside.

        The draft exists only to reach the formula, which needs ``G`` and
        ``H`` and therefore an instance; its target is a placeholder and is
        never looked at.
        """
        context = ReductionContext() if factory is None else ReductionContext(factory)
        fresh = context.variables(source.ring, source.dimension)

        draft = cls(source, source, fresh)
        step = cls(source, draft._composite(), fresh)
        object.__setattr__(step, "_provenance", Provenance.CONSTRUCTED)

        return step

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
    def variables(self) -> tuple[sp.Symbol, ...]:
        """Return the fresh generators, the ``Y`` of the formula.

        The new generators only, not the variables of either map; those are
        ``source.variables`` and ``target.variables``.
        """
        return self._variables

    @property
    def provenance(self) -> Provenance:
        """Return whether the target was supplied or constructed."""
        return self._provenance

    @property
    def filtration_level(self) -> int | float:
        """Return the ``EA`` level the step establishes, which is ``0``.

        Not an argument, unlike ``BCWStep``'s. ``G`` displaces ``X_i`` by
        ``Y_i``, of order one, so it lies in ``EA^0`` and in no higher stage,
        and the construction admits no other factorization to declare.
        """
        return FILTRATION_LEVEL

    @property
    def stabilized(self) -> PolynomialMap:
        """Return ``F^[n]``, the source with ``n`` identity coordinates.

        The generators are pinned to the ones the step records. A supplied
        certificate names the variables it used, and those are honoured rather
        than reinvented.
        """
        return self._source.extend(
            len(self._variables), factory=FixedVariableFactory(self._variables)
        )

    @property
    def ring(self) -> PolyRing:
        """Return the arithmetic context of ``G`` and ``H``."""
        return self.stabilized.ring

    @property
    def quadratic(self) -> tuple[sp.Expr, ...]:
        """Return ``F_(2)``, the quadratic part of the source's displacement."""
        return tuple(part.as_expr() for part in self._parts(2))

    @property
    def cubic(self) -> tuple[sp.Expr, ...]:
        """Return ``F_(3)``, the cubic part of the source's displacement."""
        return tuple(part.as_expr() for part in self._parts(3))

    def _parts(self, degree: int) -> tuple[PolyElement, ...]:
        """Return the homogeneous part of the displacement, in the source's ring."""
        return tuple(
            homogeneous_part(component, degree)
            for component in self._source.displacement().to_polynomials()
        )

    @property
    def H(self) -> ElementaryAutomorphism:  # noqa: N802
        """Return ``Y_i |-> Y_i - F_(3),i``, one factor per component.

        Each factor is a polynomial in the source's variables alone, so no
        factor involves any ``Y``. The factors therefore commute, the order
        they are listed in does not matter, and ``H^-1`` is the componentwise
        negation, which is what ``transport`` uses.
        """
        ring = self.ring
        offset = self._source.dimension

        return ElementaryAutomorphism(
            [
                ElementaryFactor(ring, offset + position, -value.set_ring(ring))
                for position, value in enumerate(self._parts(3))
            ]
        )

    @property
    def G(self) -> ElementaryAutomorphism:  # noqa: N802
        """Return ``X_i |-> X_i + Y_i``, one factor per component."""
        ring = self.ring
        offset = self._source.dimension

        return ElementaryAutomorphism(
            [
                ElementaryFactor(ring, position, ring.gens[offset + position])
                for position in range(self._source.dimension)
            ]
        )

    def _composite(self) -> PolynomialMap:
        """Return ``G o F^[n] o H``."""
        return self.G.apply_to(
            self.stabilized.compose(self.H.to_polynomial_map(self.ring))
        )

    # ----------------------------------------------------------------------
    # Verification
    # ----------------------------------------------------------------------

    def verify(self) -> None:
        """Check UNI-1 to UNI-10, or raise ``VerificationError``.

        The source is checked first. UNI-2, UNI-3 and UNI-4 are the reason the
        step applies at all, and a failure there is a statement about the
        caller's map rather than about this step's arithmetic; reporting it
        before the identity keeps the two apart.
        """
        if self._verified:
            return

        self._verify_source()
        self._verify_generators()
        self._verify_identity()
        self._verify_invertibility()
        self._verify_filtration()
        self._verify_nilpotence()
        self._verify_determinant()

        object.__setattr__(self, "_verified", True)

    def _verify_source(self) -> None:
        """UNI-2, UNI-3 and UNI-4."""
        order = self._source.displacement().order()
        if order < 2:
            raise VerificationError(
                "UNI-2",
                f"The source is not in MA^1: its displacement has order "
                f"{order}. Section 4 starts from a map whose displacement has "
                "order at least two; LinearStep.normalize produces one.",
            )

        degree = self._source.degree()
        if degree > 3:
            raise VerificationError(
                "UNI-3",
                f"The source has degree {degree}. The construction has no "
                "place for a homogeneous part above degree three.",
            )

        determinant = self._source.determinant()
        if not agree(determinant, sp.Integer(1)):
            raise VerificationError(
                "UNI-4",
                f"The source has Jacobian determinant {determinant}, not one. "
                "In MA^1 a constant determinant is one, so this source is not "
                "a Keller map.",
            )

    def _verify_generators(self) -> None:
        """UNI-5, the half that is not a constructor invariant."""
        expected = 2 * self._source.dimension
        if self._target.dimension != expected:
            raise VerificationError(
                "UNI-5",
                f"The source has dimension {self._source.dimension}, so the "
                f"target has {expected}, not {self._target.dimension}.",
            )

        if self._target.variables != self._source.variables + self._variables:
            raise VerificationError(
                "UNI-5",
                "The target does not carry the variables of the source "
                "followed by the fresh ones, in order.",
            )

    def _verify_identity(self) -> None:
        """UNI-1."""
        composite = self._composite()

        if composite != self._target:
            raise VerificationError(
                "UNI-1",
                "The target is not G o F^[n] o H, that is not "
                "(X + F_(2) + Y, Y - F_(3)).",
            )

    def _verify_invertibility(self) -> None:
        """UNI-6. Exhibited rather than asserted.

        Each factor is an ``ElementaryFactor``, whose constructor already
        refuses a polynomial involving its own variable, and the inverse comes
        from the definition. What is checked here is that composing the
        exhibited inverse with the automorphism gives the identity map.
        """
        identity = PolynomialMap.from_ring(self.ring, self.ring.gens)

        for name, automorphism in (("G", self.G), ("H", self.H)):
            undone = automorphism.inverse().apply_to(
                automorphism.to_polynomial_map(self.ring)
            )
            if undone != identity:  # pragma: no cover - group law, not data
                raise VerificationError(
                    "UNI-6",
                    f"The exhibited inverse of {name} does not undo it.",
                )

    def _verify_filtration(self) -> None:
        """UNI-7 and UNI-8.

        Both are consequences of the formula rather than statements about
        data, and both are checked because a caller reads them off the step:
        UNI-7 to know what the step establishes, UNI-8 to know that the target
        has left ``MA^1`` and that a following step may not assume otherwise.
        """
        if not self.G.is_in_EA(FILTRATION_LEVEL):  # pragma: no cover - fixed by G
            raise VerificationError(
                "UNI-7",
                f"G does not lie in EA^{FILTRATION_LEVEL}, which the formula "
                "guarantees; something is wrong with the step.",
            )

        if self.G.is_in_EA(1):  # pragma: no cover - G displaces X_i by Y_i
            raise VerificationError(
                "UNI-7",
                "G lies in EA^1, which the formula rules out; something is "
                "wrong with the step.",
            )

        level = self._target.filtration_degree()
        if level != FILTRATION_LEVEL:  # pragma: no cover - implied by UNI-1
            raise VerificationError(
                "UNI-8",
                f"The target lies in MA^{level} and the formula puts it in "
                f"MA^{FILTRATION_LEVEL}: its displacement has the linear part "
                "(Y, 0).",
            )

    def _verify_nilpotence(self) -> None:
        """UNI-9.

        ``det(I + T J(N))`` as the determinant of ``(X + T (target - X), T)``,
        which is block triangular and has exactly that determinant. One means
        that the characteristic polynomial of ``J(N)`` is ``lambda^m``, and
        Cayley-Hamilton over a commutative ring then gives ``J(N)^m = 0``.

        Implied by UNI-1 through Lemma (4.1), and checked because it is the
        property the step exists to establish. On the 26-variable target of
        ``alpoege13`` normalized it costs 0.72 seconds; the matrix power did
        not finish in twenty-five minutes.
        """
        determinant = self._scaled_displacement().determinant()

        # Not reachable without the pragma: UNI-1 runs first and sets the
        # target to G o F^[n] o H, whose displacement Lemma (4.1) makes
        # nilpotent.
        if not agree(determinant, sp.Integer(1)):  # pragma: no cover - Lemma (4.1)
            raise VerificationError(
                "UNI-9",
                f"det(I + T J(N)) is {determinant} and not one, so the "
                "displacement of the target is not nilpotent.",
            )

    def _scaled_displacement(self) -> PolynomialMap:
        """Return ``(X + T (target - X), T)``, one coordinate wider than the target.

        The fresh coordinate is named by the same policy as everything else, so
        it cannot collide with a coordinate or with a parameter of the
        coefficient domain.
        """
        widened = self._target.extend(1)
        ring = widened.ring
        parameter = ring.gens[-1]

        displacement = widened.displacement().to_polynomials()

        return PolynomialMap.from_ring(
            ring,
            tuple(
                generator + parameter * component
                for generator, component in zip(ring.gens, displacement, strict=True)
            )[:-1]
            + (parameter,),
        )

    def _verify_determinant(self) -> None:
        """UNI-10.

        Implied by UNI-1 together with every element of ``EA_n(k)`` having
        determinant one, and retained because it localizes an error to the step
        that made it.
        """
        # Not reachable without the pragma: UNI-1 runs first, and UNI-4 has
        # already put the source's determinant at one.
        if not agree(  # pragma: no cover - implied by UNI-1 and UNI-4
            self._target.determinant(), self._source.determinant()
        ):
            raise VerificationError(
                "UNI-10",
                f"The determinant changed from {self._source.determinant()} "
                f"to {self._target.determinant()}.",
            )

    def transport(self, collision: Collision) -> Collision:
        """Pull a collision back through ``H`` and push its image through ``G``.

        A point gains ``n`` coordinates. With the fresh coordinates filled with
        zero, ``H^-1`` sends ``(a, 0)`` to ``(a, F_(3)(a))``: ``H`` displaces
        ``Y`` by ``-F_(3)``, so its inverse displaces ``Y`` by ``+F_(3)``. The
        sign is opposite to ``BCWStep``'s, where the appended coordinates are
        ``-P(a)`` and ``-Q(a)``.

        The image gains ``n`` zeros, and ``G`` then adds the ``Y`` block of the
        padded image to its ``X`` block. That block is zero, so the image is
        unchanged apart from the padding. Any constant fill shared by the
        points would do; zero is fixed by UNI-11, because a fill ``y`` merely
        moves the image to ``(c + y, y)``.

        Distinctness needs no argument about the appended block: two distinct
        points of the source already differ in the first ``n`` coordinates.
        """
        collision.verify(self._source)

        appended = [self._appended_coordinates(point) for point in collision.points]

        moved = collision.extended(appended, (sp.Integer(0),) * self._source.dimension)
        moved.verify(self._target)

        return moved

    def _appended_coordinates(self, point: tuple[sp.Expr, ...]) -> tuple[sp.Expr, ...]:
        """Return ``F_(3)(a)``, the coordinates a point gains."""
        substitution = dict(zip(self._source.variables, point, strict=True))

        return tuple(
            sp.expand(value.as_expr().xreplace(substitution))
            for value in self._parts(3)
        )

    # ----------------------------------------------------------------------

    def _key(self) -> tuple[object, ...]:
        """Return what equality compares."""
        return (
            self._source,
            self._target,
            tuple(variable.name for variable in self._variables),
            self._provenance,
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, UnipotentStep):
            return NotImplemented
        return self._key() == other._key()

    def __hash__(self) -> int:
        return hash(self._key())

    def __repr__(self) -> str:
        return (
            f"UnipotentStep(EA^{FILTRATION_LEVEL}, "
            f"dimension={self._source.dimension}->{self._target.dimension}, "
            f"provenance={self._provenance.value})"
        )
