"""The third step of the Reduction Theorem, BCW Chapter II, Section 4, p. 307.

The second step doubles the dimension and makes ``J(N)`` nilpotent. This one
adds a single variable and makes the displacement cubic homogeneous. With
``F = X + N`` and ``N = N_(1) + N_(2) + N_(3)``,

    N(T) = N_(1) T^2 + N_(2) T + N_(3),   L = (X + N(T), T)

Each part is lifted by the power of ``T`` its own degree is short of, so every
term of ``N(T)`` has degree three in ``(X, T)``. The Jacobian of ``L`` is
unipotent, which is where Lemma (4.1) is repaid: ``J_X N(T) = T^2 J(N)(X/T)``,
and a nilpotent matrix stays nilpotent under a substitution and a scaling.

Not a composition
-----------------

The three step types written before this one have the shape ``A o F^[m] o B``
and exhibit the factorization, because "invertible" is a claim and a list of
generators with their inverses is something a reader can check. There is
nothing to factor here, and the two written after it have nothing either. The
target is not conjugate to the source, no automorphism relates them, and they
do not have the same dimension.

What relates them is a slice: at ``T = 1`` the first ``n`` components are the
source, since ``N(1) = N_(1) + N_(2) + N_(3)``. Three things follow, and
``docs/contracts.md`` states them under "This step is not a composition".

What is exhibited is the formula. A reader checks the target by recomputing it
rather than by undoing it.

``transport`` goes forward and only forward. A collision of the source gives
one of the target at ``T = 1``; a collision of the target elsewhere need not
come from anywhere, because the slice at ``T = t`` is related to the source by
scaling only at ``t = 1``.

There is no ``EA`` level to declare, so ``filtration_level`` is ``math.inf``,
as for ``LinearStep`` and ``TranslationStep`` and for a different reason than
either: those are compositions whose factors are not elementary, and this is
not a composition.

See ``docs/contracts.md``, HOM-1 to HOM-10.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import sympy as sp
from sympy.polys.rings import PolyElement, PolyRing

from ..canonical import agree
from ..collision import Collision
from ..context import ReductionContext
from ..errors import VerificationError
from ..polynomial_map import PolynomialMap
from ..reduction import Provenance
from ..variables import FixedVariableFactory, VariableFactory, reserved_names
from .grading import homogeneous_part, scaled_displacement

FILTRATION_DEGREE = 2
"""Where the target lands in the filtration. See HOM-6.

Every part of the displacement has order three, so the target is in ``MA^2``
and therefore in ``MA^1``. The second step left ``MA^1`` and the third comes
back past it.
"""


@dataclass(frozen=True, eq=False)
class HomogenizationStep:
    """One application of Section 4's third step.

    Parameters
    ----------
    source, target
        The maps before and after. A ``target`` supplied here is what makes
        HOM-1 a real check; ``build`` computes it instead and records the
        weaker provenance. HOM-2 and HOM-3 constrain the *source* and can fail
        on either route.
    variable
        The one fresh generator, the ``T`` of the formula.
    """

    _source: PolynomialMap
    _target: PolynomialMap
    _variable: sp.Symbol
    _provenance: Provenance
    _verified: bool

    def __init__(
        self,
        source: PolynomialMap,
        target: PolynomialMap,
        variable: sp.Symbol,
    ) -> None:
        if not isinstance(source, PolynomialMap):
            raise TypeError("The source must be a PolynomialMap.")
        if not isinstance(target, PolynomialMap):
            raise TypeError("The target must be a PolynomialMap.")
        if not isinstance(variable, sp.Symbol):
            raise TypeError("The fresh variable must be a SymPy symbol.")

        # Early, and not first in verify(). A colliding name can no longer be
        # told apart from a wrong target afterwards, because the extension
        # would then let two coordinates denote one generator. Against the
        # reserved names and not only the coordinates: a parameter of the
        # coefficient domain is taken as well.
        if variable.name in reserved_names(source.ring):
            raise ValueError(
                f"The variable {variable.name} is already in use by the source."
            )

        object.__setattr__(self, "_source", source)
        object.__setattr__(self, "_target", target)
        object.__setattr__(self, "_variable", variable)
        object.__setattr__(self, "_provenance", Provenance.SUPPLIED)
        object.__setattr__(self, "_verified", False)

    @classmethod
    def build(
        cls,
        source: PolynomialMap,
        factory: VariableFactory | None = None,
    ) -> HomogenizationStep:
        """Apply the formula and record the result as constructed.

        Convenient, and weaker evidence for HOM-1, which then compares the
        implementation against itself. HOM-2 and HOM-3 are not weakened by this
        route: they constrain the source, which is supplied either way, and
        ``build`` neither checks nor repairs them. A step built from a source
        whose displacement is not nilpotent is built and fails to verify.

        This is the only way to obtain a ``CONSTRUCTED`` step. The public
        constructor always records ``SUPPLIED``.

        The draft exists only to reach the formula, which needs the fresh
        variable and therefore an instance; its target is a placeholder and is
        never looked at.
        """
        context = ReductionContext() if factory is None else ReductionContext(factory)
        fresh = context.variables(source.ring, 1)[0]

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
    def variable(self) -> sp.Symbol:
        """Return the fresh generator, the ``T`` of the formula."""
        return self._variable

    @property
    def provenance(self) -> Provenance:
        """Return whether the target was supplied or constructed."""
        return self._provenance

    @property
    def filtration_level(self) -> int | float:
        """Return ``math.inf``: the step makes no ``EA`` claim.

        It is not a composition with elementary automorphisms, so there is no
        stage of the filtration it could be said to reach. ``Reduction`` takes
        the minimum over its steps, and an infinity there is the neutral
        element rather than a claim.
        """
        return math.inf

    @property
    def ring(self) -> PolyRing:
        """Return the arithmetic context of the target the formula gives.

        The source extended by the fresh generator, pinned to the name the step
        records. A supplied certificate names the variable it used, and it is
        honoured rather than reinvented.
        """
        return self._source.extend(
            1, factory=FixedVariableFactory((self._variable,))
        ).ring

    @property
    def parts(self) -> tuple[tuple[sp.Expr, ...], ...]:
        """Return ``N_(1)``, ``N_(2)`` and ``N_(3)`` of the source's displacement.

        Three tuples of ``n`` expressions, in that order. What the formula
        reads, and what a reader has to recompute to check HOM-1.
        """
        return tuple(
            tuple(part.as_expr() for part in self._homogeneous(degree))
            for degree in (1, 2, 3)
        )

    def _homogeneous(self, degree: int) -> tuple[PolyElement, ...]:
        """Return one homogeneous part of the displacement, in the source's ring."""
        return tuple(
            homogeneous_part(component, degree)
            for component in self._source.displacement().to_polynomials()
        )

    def _composite(self) -> PolynomialMap:
        """Return ``(X + N_(1) T^2 + N_(2) T + N_(3), T)``.

        A part of degree zero has no slot and is dropped. That is not a
        silent loss: the sum of the three parts is then not the displacement,
        so the slice at ``T = 1`` is not the source and HOM-8 fails. A source
        with a constant term belongs to ``TranslationStep`` and not here.
        """
        ring = self.ring
        parameter = ring.gens[-1]
        exponents = (2, 1, 0)

        lifted = [
            sum(
                (
                    part.set_ring(ring) * parameter**exponent
                    for part, exponent in zip(parts, exponents, strict=True)
                ),
                ring.zero,
            )
            for parts in zip(
                self._homogeneous(1),
                self._homogeneous(2),
                self._homogeneous(3),
                strict=True,
            )
        ]

        return PolynomialMap.from_ring(
            ring,
            tuple(
                generator + part
                for generator, part in zip(ring.gens[:-1], lifted, strict=True)
            )
            + (parameter,),
        )

    # ----------------------------------------------------------------------
    # Verification
    # ----------------------------------------------------------------------

    def verify(self) -> None:
        """Check HOM-1 to HOM-8, or raise ``VerificationError``.

        The source is checked first. HOM-2 and HOM-3 are the reason the step
        applies at all, and a failure there is a statement about the caller's
        map rather than about this step's arithmetic.
        """
        if self._verified:
            return

        self._verify_source()
        self._verify_generators()
        self._verify_identity()
        self._verify_homogeneity()
        self._verify_filtration()
        self._verify_slice()
        self._verify_determinant()

        object.__setattr__(self, "_verified", True)

    def _verify_source(self) -> None:
        """HOM-2 and HOM-3."""
        degree = self._source.degree()
        if degree > 3:
            raise VerificationError(
                "HOM-2",
                f"The source has degree {degree}. The regrading has three "
                "slots and a part of degree four has no power of T to be "
                "lifted by.",
            )

        determinant = scaled_displacement(self._source).determinant()
        if not agree(determinant, sp.Integer(1)):
            raise VerificationError(
                "HOM-3",
                f"det(I + T J(N)) is {determinant} and not one, so the "
                "displacement of the source does not have nilpotent Jacobian. "
                "The second step of Section 4 is what produces one; a Keller "
                "source is not enough, because the target's Jacobian is a "
                "scaled substitution of this one.",
            )

    def _verify_generators(self) -> None:
        """HOM-4, the half that is not a constructor invariant."""
        expected = self._source.dimension + 1
        if self._target.dimension != expected:
            raise VerificationError(
                "HOM-4",
                f"The source has dimension {self._source.dimension}, so the "
                f"target has {expected}, not {self._target.dimension}.",
            )

        if self._target.variables != self._source.variables + (self._variable,):
            raise VerificationError(
                "HOM-4",
                "The target does not carry the variables of the source "
                "followed by the fresh one, in order.",
            )

    def _verify_identity(self) -> None:
        """HOM-1."""
        if self._composite() != self._target:
            raise VerificationError(
                "HOM-1",
                "The target is not (X + N_(1) T^2 + N_(2) T + N_(3), T).",
            )

    def _verify_homogeneity(self) -> None:
        """HOM-5.

        Implied by HOM-1 and checked because it is what the step exists to
        establish. It reads the monomials and computes nothing.
        """
        displacement = self._target.displacement().to_polynomials()

        for component in displacement[:-1]:
            degrees = {sum(monomial) for monomial in component.itermonoms()}
            if degrees - {3}:  # pragma: no cover - implied by HOM-1
                raise VerificationError(
                    "HOM-5",
                    f"A component of the target's displacement has degrees "
                    f"{sorted(degrees)} and not three alone.",
                )

        if displacement[-1] != displacement[-1].ring.zero:  # pragma: no cover
            raise VerificationError(
                "HOM-5",
                "The last component of the target is not the fresh variable.",
            )

    def _verify_filtration(self) -> None:
        """HOM-6."""
        level = self._target.filtration_degree()
        if level != FILTRATION_DEGREE:  # pragma: no cover - implied by HOM-5
            raise VerificationError(
                "HOM-6",
                f"The target lies in MA^{level} and a cubic homogeneous "
                f"displacement puts it in MA^{FILTRATION_DEGREE}.",
            )

    def _verify_slice(self) -> None:
        """HOM-8.

        Implied by HOM-1, and checked because it is the reason ``transport``
        works rather than an arithmetic detail. It is weaker than HOM-1 and is
        not a substitute for it: at ``T = 1`` all three slots contribute alike,
        so a target that lifted ``N_(1)`` by ``T`` and ``N_(2)`` by ``T^2``
        would pass here and fail there.

        Where it is not weaker is a source with a constant term. The formula
        has no slot for one and drops it, and this is the check that notices.
        """
        at_one = {self._variable: sp.Integer(1)}
        sliced = tuple(
            sp.expand(component.xreplace(at_one))
            for component in self._target.components[:-1]
        )
        wanted = tuple(sp.expand(component) for component in self._source.components)

        if sliced != wanted:
            raise VerificationError(
                "HOM-8",
                "Setting T = 1 in the target does not return the source. "
                "If the source has a constant term, the formula has no slot "
                "for it and TranslationStep is what removes it.",
            )

    def _verify_determinant(self) -> None:
        """HOM-7.

        Implied by HOM-1 and HOM-3, and retained because it localizes an error
        to the step that made it.
        """
        determinant = self._target.determinant()

        # Not reachable without the pragma: HOM-1 and HOM-3 run first, and
        # together they force this.
        if not agree(determinant, sp.Integer(1)):  # pragma: no cover - Lemma (4.1)
            raise VerificationError(
                "HOM-7",
                f"The target has Jacobian determinant {determinant}, not one.",
            )

    def transport(self, collision: Collision) -> Collision:
        """Carry a collision to the slice ``T = 1`` of the target.

        Every point and the image gain the coordinate one. A zero would send
        ``(a, 0)`` to itself, which is a fixed point of the target and no
        collision at all, so the appended value is not free here as it is in
        BCW-8 and UNI-11.

        Distinctness needs no argument: the points differ before the
        coordinate is appended and all of them gain the same value.
        """
        collision.verify(self._source)

        one = (sp.Integer(1),)
        moved = collision.extended([one for _ in collision.points], one)
        moved.verify(self._target)

        return moved

    # ----------------------------------------------------------------------

    def _key(self) -> tuple[object, ...]:
        """Return what equality compares."""
        return (
            self._source,
            self._target,
            self._variable.name,
            self._provenance,
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, HomogenizationStep):
            return NotImplemented
        return self._key() == other._key()

    def __hash__(self) -> int:
        return hash(self._key())

    def __repr__(self) -> str:
        return (
            f"HomogenizationStep("
            f"dimension={self._source.dimension}->{self._target.dimension}, "
            f"provenance={self._provenance.value})"
        )
