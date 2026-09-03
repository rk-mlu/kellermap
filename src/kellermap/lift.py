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
from functools import cmp_to_key

import sympy as sp
from sympy.polys.rings import PolyElement, PolyRing

from .canonical import agree
from .collision import Collision
from .context import ReductionContext
from .errors import VerificationError
from .polynomial_map import PolynomialMap
from .reduction import Provenance
from .variables import VariableFactory, reserved_names


def _field(source: PolynomialMap) -> None:
    """Raise unless the coefficient domain is one this construction works over.

    Theorem 3 of arXiv:2608.12543v1 works over a subfield of the complex
    numbers of characteristic zero, and so does the compression, where CHC-2
    and CHC-8 draw the same boundary. CHC-4 is about the source being a Keller
    map and not about its domain; this docstring cited it wrongly until an
    audit of ``0.6.0rc3``. The lift adjoins ``i``, which is a statement about a
    field, and over ``GF(5)`` ``0.6.0rc2`` reached ``unify`` and ended in
    SymPy's own ``UnificationFailed``. A raw error from a library this one
    wraps is not an answer.
    """
    domain = source.ring.domain

    # Two conditions and two messages. Joined by ``or`` they were one branch,
    # so the test over ``GF(5)`` reached the characteristic alone and a
    # mutation that dropped the field half went unnoticed; and the advice to
    # use ``over_field`` is wrong for ``GF(5)``, whose field of fractions is
    # itself. An audit of ``0.6.0rc3`` found both.
    if not domain.is_Field:
        raise VerificationError(
            "SYM-4",
            f"The coefficient domain is {domain}, which is not a field. The "
            "lift adjoins i to a field of characteristic zero, which is the "
            "setting of Theorem 3; over_field() moves a map to the field of "
            "fractions of its domain.",
        )

    if domain.characteristic() != 0:
        raise VerificationError(
            "SYM-4",
            f"The coefficient domain is {domain}, of characteristic "
            f"{domain.characteristic()}. The lift is stated over a subfield of "
            "the complex numbers, and adjoining i to a field of positive "
            "characteristic is a different construction.",
        )


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
        _field(source)
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

        # Through SymPy and not through ``convert``. The target's domain is the
        # source's with i adjoined, and for an algebraic number field that is a
        # third field again: QQ<sqrt(2)> becomes QQ<sqrt(2) + I>, whose
        # elements are ANPs over another minimal polynomial. ``convert`` tries
        # to unify the two representations and fails; ``to_sympy`` and
        # ``from_sympy`` go through the expression the two agree on. An audit
        # of 0.6.0rc1 found this.
        source_domain = self._source.ring.domain

        total = ring.zero
        for position, component in enumerate(
            self._source.displacement().to_polynomials()
        ):
            substituted = ring.zero
            for monomial, coefficient in component.iterterms():
                ground = ring.domain.from_sympy(source_domain.to_sympy(coefficient))
                term = ring.ground_new(ground)
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
        _field(self._source)
        _degree(self._source)

        determinant = self._source.determinant()
        if not agree(determinant, sp.Integer(1)):
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

        One point goes to ``(p, 0)`` and the other to ``(q + rho, i rho)``, so
        the two are treated differently. Which is which is decided here and not
        by the caller, because a ``Collision`` compares its points as a set:
        see ``_oriented``.
        """
        collision.verify(self._source)

        if len(collision.points) != 2:
            raise VerificationError(
                "SYM-9",
                f"The lift carries a pair and this collision has "
                f"{len(collision.points)} points. Which two are lifted changes "
                "the result, so the step does not choose them; narrow the "
                "collision before lifting it.",
            )

        first, second = self._oriented(collision.points)
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

    @staticmethod
    def _oriented(
        points: tuple[tuple[sp.Expr, ...], ...],
    ) -> tuple[tuple[sp.Expr, ...], tuple[sp.Expr, ...]]:
        """Return the pair in the order this step uses, whatever order it came in.

        The lift is asymmetric: ``p`` goes to ``(p, 0)`` and ``q`` to
        ``(q + rho, i rho)``. A ``Collision`` is not asymmetric -- COL-6 makes
        equality a question about a *set* of points -- so taking the order the
        tuple happens to carry would let two equal collisions transport to two
        unequal ones. RC1 did that, and both results verified, which is the
        worst shape for such a fault.

        The order has to be a function of the *values*, and two orders that
        looked structural were not. Sorting by ``str`` fails because printing
        is not injective: ``Symbol("a", positive=True)`` and
        ``Symbol("a", negative=True)`` print alike, both keys are equal, and a
        stable sort then keeps whatever order arrived. Sorting by ``srepr``
        fails the other way: it is injective on *representations* and not a
        function of equality. ``Symbol("a", finite=True, positive=True)`` and
        ``Symbol("a", positive=True, finite=True)`` are one symbol with two
        representations, and a third symbol can sort between them, so one set
        of points gets two orientations. SymPy's cache hides that by reusing
        symbols; ``SYMPY_USE_CACHE=no`` shows it. Audits of ``0.6.0rc2`` and
        ``0.6.0rc3`` found the two in turn.

        ``Basic.compare`` is not one either, and an audit of ``0.6.0rc4``
        showed it: it separates expression classes by name, and SymPy's public
        ``Function`` API builds different classes with one name, so
        ``Function("f", real=True)(t)`` and ``Function("f", positive=True)(t)``
        are unequal and compare as equal. Their ``srepr`` is the same string,
        and ``default_sort_key`` ties on them too.

        What the three attempts had in common is the mistake, and it is not
        about which ordering is canonical. Each was used *instead of* an
        equality test rather than *after* one. The comparison below asks
        ``left == right`` first, so everything after it sees only values
        already known to differ, and the one thing required of a key there is
        that it decides -- not that it agrees with equality.

        The tie-break is the class: its module, its qualified name and its
        declared assumptions, which is what separates two ``Function`` classes
        of one name. If even that ties, the step refuses under SYM-8 rather
        than taking the order the tuple happened to carry. Keeping that order
        silently is the fault three audits in a row have found, and a refusal
        is an answer where two verifying results are not.
        """

        def rank(value: sp.Expr) -> tuple[str, str, str]:
            """Return a decision for values already known to be unequal."""
            kind = type(value)
            declared = dict(getattr(kind, "default_assumptions", {}) or {})

            return (
                str(getattr(kind, "__module__", "")),
                str(getattr(kind, "__qualname__", kind.__name__)),
                repr(sorted((str(name), str(held)) for name, held in declared.items())),
            )

        def structural(first: tuple[sp.Expr, ...], second: tuple[sp.Expr, ...]) -> int:
            for left, right in zip(first, second, strict=True):
                left, right = sp.sympify(left), sp.sympify(right)
                if left == right:
                    continue

                decision = left.compare(right)
                if decision:
                    return int(decision)

                if rank(left) != rank(right):
                    return -1 if rank(left) < rank(right) else 1

                raise VerificationError(
                    "SYM-8",
                    f"The two points cannot be put in an order: {left} and "
                    f"{right} are different expressions that compare equal and "
                    "have the same class. The lift treats its two points "
                    "differently, so an order it cannot decide is a result it "
                    "cannot give.",
                )

            # Not reachable: two points that compare equal in every coordinate
            # are one point, and a Collision whose points coincide cannot be
            # built -- COL-4 makes that a constructor invariant. The branch is
            # here because a comparison function has to be total.
            return 0  # pragma: no cover - the points of a collision differ

        first, second = sorted(points, key=cmp_to_key(structural))

        return first, second

    def _rho(
        self, first: tuple[sp.Expr, ...], second: tuple[sp.Expr, ...]
    ) -> tuple[sp.Expr, ...]:
        """Return ``rho = (I + J h(q)^T)^-1 (p - q)``, with its equation checked.

        Exhibited rather than trusted, in the shape of UNI-6: the vector is
        computed and then put back into the equation that defines it.

        The residual is decided by ``canonical.agree`` and not by ``expand``.
        Over a rational function field a residual can be zero and not expand to
        zero, and ``0.6.0rc2`` refused a valid collision for that reason. The
        same holds for the two comparisons around it, the determinant of the
        matrix and of the source: ``1.0`` over ``RR`` is not ``1`` to ``!=``
        and is to ``agree``.

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

        if agree(matrix.det(), sp.Integer(0)):
            raise VerificationError(
                "SYM-8",
                "I + J h(q)^T is singular at the second point, so rho is not "
                "defined. That cannot happen for a Keller source, which SYM-4 "
                "requires and this source does not satisfy.",
            )

        rho = tuple(sp.expand(value) for value in matrix.LUsolve(difference))

        # The defining equation, checked rather than the solver trusted.
        residual = matrix * sp.Matrix(list(rho)) - difference
        satisfied = all(
            agree(residual[index], sp.Integer(0)) for index in range(dimension)
        )
        if not satisfied:  # pragma: no cover - solver
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
