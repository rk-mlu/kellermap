"""The symmetric lift, part 3 of Theorem 3 of arXiv:2608.12543v1.

For ``F = id + h`` with ``h`` homogeneous of degree ``d``, over ``K = k(i)``,

    P(X, Y) = i * sum_j Y_j h_j(X + i Y)

is homogeneous of degree ``d + 1`` with nilpotent Hessian, and
``id - grad(P)`` is a Keller map in twice as many variables which inherits the
collision. At ``d = 3`` the quartic ``P`` is a counterexample to the quartic
case of Zhao's Vanishing Conjecture whenever the source is one to the Jacobian
conjecture.

Why a gradient form rather than another Keller map
--------------------------------------------------

Everything else in this library produces a Keller map. This produces one that
is the gradient of a form it exhibits, which is strictly more: it is what the
de Bondt-van den Essen reduction asks for, and it is the object the last
milestone of this project is about.

That is also why SYM-2 states the identity a second time. A map that equals
``id - grad`` of an exhibited polynomial *is* a gradient map, and a reader can
check it; a claim that some potential exists would not be checkable at all.

Three things here are unlike the rest of the package
-----------------------------------------------------

The coefficient domain grows. A source over ``QQ`` gives a target over
``QQ(i)``, where every other step keeps the domain and ``guards.settled`` uses
equality of domains as an invariant no chain of ``BCWStep``s crosses.

``transport`` takes a pair and is asymmetric in it: ``p`` goes to ``(p, 0)``
and ``q`` to ``(q + rho, i rho)``. Which point is which changes both, so a
collision of more than two points is refused rather than narrowed silently.

The determinant of the target is not checked. It follows from the identity and
the source, and on the forty-variable lift of Thompson's compressed twenty it
did not finish in eight hours. SYM-7 carries the measurement.

See ``docs/contracts.md``, SYM-1 to SYM-12.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import sympy as sp
from sympy.polys.rings import PolyElement, PolyRing

from .collision import Collision
from .context import ReductionContext
from .errors import VerificationError
from .polynomial_map import PolynomialMap
from .reduction import Provenance
from .variables import VariableFactory, reserved_names


def _degree(source: PolynomialMap) -> int:
    """Return the degree of a homogeneous displacement, or raise SYM-3.

    The same shape as CHC-3 and for the same reason at one remove: ``P`` is
    homogeneous of degree ``d + 1`` only if ``h`` is homogeneous of degree
    ``d``. A source that fails this lifts to a form with no degree at all.
    """
    degrees = {
        sum(monomial)
        for component in source.displacement().to_polynomials()
        if component
        for monomial in component.itermonoms()
    }

    if len(degrees) != 1:
        raise VerificationError(
            "SYM-3",
            f"The displacement of the source has the degrees {sorted(degrees)} "
            "and is not homogeneous, so the lift of it has no degree either. "
            "The homogenization and the compression both produce a source "
            "that is homogeneous.",
        )

    degree = int(degrees.pop())
    if degree < 2:
        raise VerificationError(
            "SYM-3",
            f"The displacement of the source is homogeneous of degree {degree}, "
            "below two.",
        )

    return degree


@dataclass(frozen=True, eq=False)
class SymmetricLiftStep:
    """The gradient form of a homogeneous Keller map.

    Parameters
    ----------
    source, target
        The maps before and after. A ``target`` supplied here is what makes
        SYM-1 a real check. SYM-3 and SYM-4 constrain the *source* and can fail
        on either route.
    variables
        The ``2m`` generators of the target, the ``X`` block followed by the
        ``Y`` block. All of them are fresh: the target is a map on a different
        space and shares no coordinate with its source.
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

        names = tuple(variables)
        for variable in names:
            if not isinstance(variable, sp.Symbol):
                raise TypeError("Every variable of the target must be a SymPy symbol.")

        if len(names) != 2 * source.dimension:
            raise ValueError(
                f"The lift doubles the dimension: expected "
                f"{2 * source.dimension} generators for a source of "
                f"{source.dimension}, got {len(names)}."
            )

        if len({variable.name for variable in names}) != len(names):
            raise ValueError("The variables of the target must be distinct.")

        taken = {variable.name for variable in names} & reserved_names(source.ring)
        if taken:
            raise ValueError(
                f"The variables {sorted(taken)} are already in use by the source."
            )

        object.__setattr__(self, "_source", source)
        object.__setattr__(self, "_target", target)
        object.__setattr__(self, "_variables", names)
        object.__setattr__(self, "_provenance", Provenance.SUPPLIED)
        object.__setattr__(self, "_verified", False)

    @classmethod
    def build(
        cls,
        source: PolynomialMap,
        factory: VariableFactory | None = None,
    ) -> SymmetricLiftStep:
        """Apply the formula and record the result as constructed.

        The target is determined by the source alone; the collision enters only
        at ``transport``, unlike ``CompressionStep``, where the hull depends on
        it.

        SYM-3 and SYM-4 are not weakened by this route. SYM-3 is reached
        earlier than ``verify``, because the formula cannot be written down
        without a degree.
        """
        _degree(source)

        context = ReductionContext() if factory is None else ReductionContext(factory)
        variables = context.variables(source.ring, 2 * source.dimension)

        draft = cls(source, source, variables)
        step = cls(source, draft._composite(), variables)
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
        """Return the generators of the target, the ``X`` block then the ``Y``."""
        return self._variables

    @property
    def provenance(self) -> Provenance:
        """Return whether the target was supplied or constructed."""
        return self._provenance

    @property
    def filtration_level(self) -> int | float:
        """Return ``math.inf``: the step makes no ``EA`` claim. SYM-11."""
        return math.inf

    @property
    def ring(self) -> PolyRing:
        """Return the arithmetic context the formula builds in.

        The source's ring with twice the generators and ``i`` adjoined to the
        coefficient domain. Unifying with the Gaussian integers is what adjoins
        it: ``ZZ`` becomes ``ZZ_I`` and ``QQ`` becomes ``QQ_I``, and a domain
        that already contains ``i`` is unchanged.
        """
        return self._source.ring.clone(
            symbols=self._variables,
            domain=self._source.ring.domain.unify(sp.ZZ_I),
        )

    @property
    def form(self) -> sp.Expr:
        """Return ``P``, the form whose gradient the target is. SYM-2."""
        return self._form().as_expr()

    def _form(self) -> PolyElement:
        """Return ``P = i * sum_j Y_j h_j(X + i Y)``, in the target's ring."""
        ring = self.ring
        dimension = self._source.dimension
        imaginary = ring.domain.from_sympy(sp.I)

        shifted = tuple(
            ring.gens[position] + ring.gens[dimension + position] * imaginary
            for position in range(dimension)
        )

        total = ring.zero
        for position, component in enumerate(
            self._source.displacement().to_polynomials()
        ):
            substituted = ring.zero
            for monomial, coefficient in component.iterterms():
                term = ring.ground_new(ring.domain.convert(coefficient))
                for index, exponent in enumerate(monomial):
                    for _ in range(exponent):
                        term = term * shifted[index]
                substituted = substituted + term
            total = total + substituted * ring.gens[dimension + position]

        return total * imaginary

    def _composite(self) -> PolynomialMap:
        """Return ``(X, Y) - grad(P)``."""
        ring = self.ring
        form = self._form()

        return PolynomialMap.from_ring(
            ring,
            tuple(generator - form.diff(generator) for generator in ring.gens),
        )

    # ----------------------------------------------------------------------
    # Verification
    # ----------------------------------------------------------------------

    def verify(self) -> None:
        """Check SYM-1 to SYM-6, or raise ``VerificationError``.

        SYM-7 is not among them. The determinant of the target follows from
        SYM-1 with SYM-3 and SYM-4, and on the dimensions this construction
        reaches it is not affordable; the contract page carries the
        measurement.
        """
        if self._verified:
            return

        self._verify_source()
        self._verify_generators()
        self._verify_identity()
        self._verify_degrees()

        object.__setattr__(self, "_verified", True)

    def _verify_source(self) -> None:
        """SYM-3 and SYM-4.

        Nilpotence of ``J(h)`` needs no obligation, by the argument CHC-4
        gives: under SYM-3 a constant determinant is ``det(I + s J(h)) = 1``
        for every ``s``, and Cayley-Hamilton finishes it.
        """
        _degree(self._source)

        determinant = self._source.determinant()
        if determinant != 1:
            raise VerificationError(
                "SYM-4",
                f"The source has Jacobian determinant {determinant}, not one, "
                "so it is not a Keller map and the lift of it need not be one.",
            )

    def _verify_generators(self) -> None:
        """SYM-5, the halves that are not constructor invariants.

        The domain is checked against the one the formula builds in rather than
        against a description of it. A target supplied over the source's own
        domain satisfies every other obligation here until a coefficient of
        ``P`` turns out not to be representable, and the failure would then be
        reported as arithmetic.
        """
        expected = 2 * self._source.dimension
        if self._target.dimension != expected:
            raise VerificationError(
                "SYM-5",
                f"The lift doubles the dimension: the target has "
                f"{self._target.dimension} and not {expected}.",
            )

        if self._target.variables != self._variables:
            raise VerificationError(
                "SYM-5",
                "The target does not carry the generators the step records.",
            )

        wanted = self.ring.domain
        if self._target.ring.domain != wanted:
            raise VerificationError(
                "SYM-5",
                f"The target is over {self._target.ring.domain} and the lift "
                f"is over {wanted}, the source's domain with i adjoined.",
            )

    def _verify_identity(self) -> None:
        """SYM-1 and SYM-2, which are one equation."""
        if self._composite() != self._target:
            raise VerificationError(
                "SYM-1",
                "The target is not (X, Y) - grad(P) for the P this step "
                "exhibits, so it is not the lift and nothing here shows it to "
                "be a gradient map.",
            )

    def _verify_degrees(self) -> None:
        """SYM-6. Implied by SYM-1, and free: it reads monomials."""
        degree = _degree(self._source)
        form = self._form()

        levels = {sum(monomial) for monomial in form.itermonoms()}
        if levels != {degree + 1}:  # pragma: no cover - implied by SYM-1
            raise VerificationError(
                "SYM-6",
                f"P has the degrees {sorted(levels)} and not {degree + 1} alone.",
            )

        displacement = {
            sum(monomial)
            for component in self._target.displacement().to_polynomials()
            if component
            for monomial in component.itermonoms()
        }
        if displacement != {degree}:  # pragma: no cover - implied by SYM-1
            raise VerificationError(
                "SYM-6",
                f"The displacement of the target has the degrees "
                f"{sorted(displacement)} and not {degree} alone.",
            )

    # ----------------------------------------------------------------------
    # Transport
    # ----------------------------------------------------------------------

    def transport(self, collision: Collision) -> Collision:
        """Lift a pair of colliding points into the target. SYM-8 to SYM-10.

        The first point goes to ``(p, 0)`` and the second to
        ``(q + rho, i rho)``, so the two are treated differently and the order
        of the pair is part of the answer.
        """
        collision.verify(self._source)

        if len(collision.points) != 2:
            raise VerificationError(
                "SYM-9",
                f"The lift carries a pair and this collision has "
                f"{len(collision.points)} points. Which two, and which of them "
                "is the first, changes both lifted points, so the step does "
                "not choose; narrow the collision before lifting it.",
            )

        first, second = collision.points
        rho = self._rho(first, second)
        zero = (sp.Integer(0),) * self._source.dimension

        moved = Collision.at(
            self._target,
            (
                tuple(first) + zero,
                tuple(sp.expand(a + b) for a, b in zip(second, rho, strict=True))
                + tuple(sp.expand(sp.I * value) for value in rho),
            ),
        )
        moved.verify(self._target)

        return moved

    def _rho(
        self, first: tuple[sp.Expr, ...], second: tuple[sp.Expr, ...]
    ) -> tuple[sp.Expr, ...]:
        """Return ``rho = (I + J h(q)^T)^-1 (p - q)``, with its equation checked.

        Exhibited rather than trusted, in the shape of UNI-6: the vector is
        computed and then put back into the equation that defines it.

        The matrix is invertible for a Keller source, since ``det J(F)`` is one
        there. A source that is not one can make it singular, and SYM-4 is what
        rules that out for a step that verifies; ``transport`` does not require
        SYM-4 and so has to say what happened.
        """
        dimension = self._source.dimension
        variables = self._source.variables
        displacement = self._source.displacement().components
        at_second = dict(zip(variables, second, strict=True))

        jacobian = sp.Matrix(
            dimension,
            dimension,
            lambda i, j: sp.diff(displacement[i], variables[j]).xreplace(at_second),
        )
        matrix = sp.eye(dimension) + jacobian.T
        difference = sp.Matrix(
            [sp.expand(a - b) for a, b in zip(first, second, strict=True)]
        )

        if matrix.det() == 0:
            raise VerificationError(
                "SYM-8",
                "I + J h(q)^T is singular at the second point, so rho is not "
                "defined. That cannot happen for a Keller source, which SYM-4 "
                "requires and this source does not satisfy.",
            )

        rho = tuple(sp.expand(value) for value in matrix.LUsolve(difference))

        # The defining equation, checked rather than the solver trusted.
        residual = matrix * sp.Matrix(list(rho)) - difference
        if sp.expand(residual) != sp.zeros(dimension, 1):  # pragma: no cover - solver
            raise VerificationError(
                "SYM-8",
                "The computed rho does not satisfy (I + J h(q)^T) rho = p - q.",
            )

        return rho

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
        if not isinstance(other, SymmetricLiftStep):
            return NotImplemented
        return self._key() == other._key()

    def __hash__(self) -> int:
        return hash(self._key())

    def __repr__(self) -> str:
        return (
            f"SymmetricLiftStep("
            f"dimension={self._source.dimension}->{self._target.dimension}, "
            f"provenance={self._provenance.value})"
        )
