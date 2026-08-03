"""Proposition (3.1) of Bass-Connell-Wright, as a certificate.

The paper reduces the degree of a polynomial map at the cost of two
dimensions. Given ``F`` and a factorization ``P * Q`` of part of one
component,

    H = (..., X_u + P, ..., X_v + Q),
    G = (..., X_i - X_u X_v, ...),
    F' = G o F^[2] o H,

and the component ``i`` of ``F'`` is ``(F_i - P Q) - X_u Q - P X_v - X_u X_v``.
``G`` and ``H`` are elementary, so the Jacobian determinant is unchanged and
the map stays invertible with an inverse one can write down.

The class verifies such a step; it does not look for one. Searching is
milestone 0.3.

Two things are wider here than in the paper, because the reduction of
Alpoege's map to dimension 17 needs them and the identity holds for both:

``P * Q`` is any subsum of the target component, not the factorization of a
single leading monomial. One step of that reduction removes four monomials of
degrees 7, 6, 5 and 4 at once, where a monomial-by-monomial application would
need one step per monomial of degree at least four, and at least eight of
them.

The target component is any component, not the first. Step seven of that
reduction acts on component 11, which step four introduced.

See ``docs/contracts.md``, BCW-1 to BCW-9.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

import sympy as sp
from sympy.polys.rings import PolyRing

from ..collision import Collision
from ..elementary import ElementaryAutomorphism, ElementaryFactor
from ..errors import VerificationError
from ..polynomial_map import PolynomialMap
from ..reduction import Provenance


@dataclass(frozen=True)
class _FixedNames:
    """A pure factory returning names decided in advance.

    Constant, so it satisfies the purity requirement of ``VariableFactory``
    trivially: it cannot count, and it cannot depend on the ring it is handed.
    Until ``ReductionContext`` arrives in work package 5, this is how a step
    says which two generators it used -- and that has to be said either way,
    since a supplied step whose variables were unknown could not be checked at
    all.
    """

    names: tuple[sp.Symbol, ...]

    def __call__(self, ring: PolyRing, count: int) -> tuple[sp.Symbol, ...]:
        if count != len(self.names):
            raise ValueError(
                f"Expected {len(self.names)} fresh names, asked for {count}."
            )

        return self.names


@dataclass(frozen=True, eq=False)
class BCWStep:
    """One application of Proposition (3.1).

    ``G`` and ``H`` are derived from ``index``, ``P``, ``Q`` and ``variables``
    by the formula, never supplied alongside them: two ways to say the same
    thing invite them to disagree.

    Parameters
    ----------
    source, target
        The maps before and after. ``target`` supplied here is what makes
        BCW-1 a real check; ``build`` computes it instead and records the
        weaker provenance.
    index
        The component from which ``P * Q`` is removed, zero-based.
    P, Q
        Polynomials in the variables of ``source``, free of the fresh two.
    variables
        The two generators the step introduces, in order.
    filtration_level
        The ``EA`` level ``H`` is claimed to reach, 0 or 1.
    """

    _source: PolynomialMap
    _target: PolynomialMap
    _index: int
    _P: sp.Expr
    _Q: sp.Expr
    _variables: tuple[sp.Symbol, sp.Symbol]
    _filtration_level: int
    _provenance: Provenance
    _verified: bool

    def __init__(
        self,
        source: PolynomialMap,
        target: PolynomialMap,
        index: int,
        P: sp.Expr,  # noqa: N803
        Q: sp.Expr,  # noqa: N803
        variables: Iterable[sp.Symbol],
        filtration_level: int = 1,
        provenance: Provenance = Provenance.SUPPLIED,
    ) -> None:
        if not isinstance(source, PolynomialMap):
            raise TypeError("The source must be a PolynomialMap.")
        if not isinstance(target, PolynomialMap):
            raise TypeError("The target must be a PolynomialMap.")

        if isinstance(index, bool) or not isinstance(index, int):
            raise TypeError(
                f"The index must be an integer, not {type(index).__name__}."
            )
        if not 0 <= index < source.dimension:
            raise ValueError(
                f"Index {index} is out of range for {source.dimension} "
                "components of the source."
            )

        if isinstance(filtration_level, bool) or filtration_level not in (0, 1):
            raise ValueError(
                f"The filtration level must be 0 or 1, not {filtration_level!r}."
            )

        fresh = tuple(variables)
        if len(fresh) != 2:
            raise ValueError(
                f"A step introduces exactly two variables, got {len(fresh)}."
            )
        if not all(isinstance(symbol, sp.Symbol) for symbol in fresh):
            raise TypeError("The fresh variables must be SymPy symbols.")
        if fresh[0] == fresh[1]:
            raise ValueError("The two fresh variables must be distinct.")

        # Frueh und nicht erst in verify(): ein kollidierender Name laesst
        # sich hinterher nicht mehr von einem falschen Ziel unterscheiden,
        # weil die Erweiterung dann zwei Koordinaten denselben Generator
        # bezeichnen liesse.
        taken = {symbol.name for symbol in fresh} & {
            symbol.name for symbol in source.variables
        }
        if taken:
            raise ValueError(
                f"The variables {sorted(taken)} are already in use by the source."
            )

        factors = tuple(sp.sympify(factor) for factor in (P, Q))
        foreign = {
            symbol.name for factor in factors for symbol in factor.free_symbols
        } - {symbol.name for symbol in source.variables}
        if foreign:
            raise ValueError(
                "P and Q must be polynomials in the variables of the source; "
                f"they also involve {sorted(foreign)}."
            )

        object.__setattr__(self, "_source", source)
        object.__setattr__(self, "_target", target)
        object.__setattr__(self, "_index", index)
        object.__setattr__(self, "_P", factors[0])
        object.__setattr__(self, "_Q", factors[1])
        object.__setattr__(self, "_variables", (fresh[0], fresh[1]))
        object.__setattr__(self, "_filtration_level", int(filtration_level))
        object.__setattr__(self, "_provenance", provenance)
        object.__setattr__(self, "_verified", False)

    @classmethod
    def build(
        cls,
        source: PolynomialMap,
        index: int,
        P: sp.Expr,  # noqa: N803
        Q: sp.Expr,  # noqa: N803
        variables: Iterable[sp.Symbol],
        filtration_level: int = 1,
    ) -> BCWStep:
        """Apply the formula and record the result as constructed.

        Convenient, and weaker evidence: BCW-1 then compares the
        implementation against itself rather than against a target that came
        from somewhere else.
        """
        draft = cls(
            source,
            source,
            index,
            P,
            Q,
            variables,
            filtration_level,
            provenance=Provenance.CONSTRUCTED,
        )

        return cls(
            source,
            draft._composite(),
            index,
            P,
            Q,
            variables,
            filtration_level,
            provenance=Provenance.CONSTRUCTED,
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
    def index(self) -> int:
        """Return the component from which ``P * Q`` is removed."""
        return self._index

    @property
    def P(self) -> sp.Expr:  # noqa: N802
        """Return the left factor."""
        return self._P

    @property
    def Q(self) -> sp.Expr:  # noqa: N802
        """Return the right factor."""
        return self._Q

    @property
    def variables(self) -> tuple[sp.Symbol, sp.Symbol]:
        """Return the two generators the step introduces, in order.

        The two *fresh* ones, not the variables of either map; those are
        ``source.variables`` and ``target.variables``.
        """
        return self._variables

    @property
    def provenance(self) -> Provenance:
        """Return whether the target was supplied or constructed."""
        return self._provenance

    @property
    def filtration_level(self) -> int | float:
        """Return the ``EA`` level the step claims for ``H``."""
        return self._filtration_level

    @property
    def attained_filtration_level(self) -> int | float:
        """Return the level ``H`` actually reaches.

        Reported rather than required. Claiming ``EA^0`` where ``EA^1`` holds
        is a true statement and BCW-6 accepts it; a reduction that does so
        merely reports a weaker bound than it could.
        """
        return self.H.filtration_degree()

    @property
    def stabilized(self) -> PolynomialMap:
        """Return ``F^[2]``, the source with two identity coordinates."""
        return self._source.extend(2, factory=_FixedNames(self._variables))

    @property
    def ring(self) -> PolyRing:
        """Return the arithmetic context of ``G`` and ``H``."""
        return self.stabilized.ring

    @property
    def H(self) -> ElementaryAutomorphism:  # noqa: N802
        """Return ``(X_u + P, X_v + Q)``, the right factor.

        Its two factors commute, since neither ``P`` nor ``Q`` involves the
        fresh variables, so the order they are listed in does not matter.
        """
        ring = self.ring
        offset = self._source.dimension

        return ElementaryAutomorphism(
            [
                ElementaryFactor(ring, offset, ring.from_expr(self._P)),
                ElementaryFactor(ring, offset + 1, ring.from_expr(self._Q)),
            ]
        )

    @property
    def G(self) -> ElementaryAutomorphism:  # noqa: N802
        """Return ``X_index |-> X_index - X_u X_v``, the left factor."""
        ring = self.ring
        offset = self._source.dimension

        return ElementaryAutomorphism(
            [
                ElementaryFactor(
                    ring, self._index, -ring.gens[offset] * ring.gens[offset + 1]
                )
            ]
        )

    def _composite(self) -> PolynomialMap:
        """Return ``G o F^[2] o H``."""
        return self.G.apply_to(self.stabilized.compose(self.H.to_polynomial_map()))

    # ----------------------------------------------------------------------
    # Verification
    # ----------------------------------------------------------------------

    def verify(self) -> None:
        """Check BCW-1 to BCW-7, or raise ``VerificationError``."""
        if self._verified:
            return

        self._verify_generators()
        self._verify_identity()
        self._verify_invertibility()
        self._verify_filtration()
        self._verify_determinant()

        object.__setattr__(self, "_verified", True)

    def _verify_generators(self) -> None:
        """BCW-2 and BCW-3."""
        if self._target.dimension != self._source.dimension + 2:
            raise VerificationError(
                "BCW-2",
                f"The source has dimension {self._source.dimension}, the "
                f"target {self._target.dimension}; a step adds two.",
            )

        expected = self._source.variables + self._variables
        if self._target.variables != expected:
            raise VerificationError(
                "BCW-2",
                "The target does not carry the variables of the source "
                "followed by the two fresh ones.",
            )

        # BCW-3 wird schon im Konstruktor erzwungen: P und Q duerfen nur
        # Variablen der Quelle enthalten, und die frischen sind keine. Hier
        # steht die Gegenprobe gegen den erweiterten Ring, in dem sie es
        # koennten.
        for name, factor in (("P", self._P), ("Q", self._Q)):
            if factor.free_symbols & set(self._variables):
                raise VerificationError(
                    "BCW-3",
                    f"{name} involves one of the fresh variables {self._variables}.",
                )

    def _verify_identity(self) -> None:
        """BCW-1."""
        try:
            composite = self._composite()
        except ValueError as error:
            raise VerificationError(
                "BCW-1", f"The step does not compose: {error}"
            ) from error

        if composite != self._target:
            raise VerificationError(
                "BCW-1",
                "The target is not G o F^[2] o H.",
            )

    def _verify_invertibility(self) -> None:
        """BCW-5. Exhibited rather than asserted.

        Each factor is an ``ElementaryFactor``, whose constructor already
        refuses a polynomial involving its own variable, and the inverse comes
        from the definition. What is checked here is that composing the
        exhibited inverse with the automorphism gives the identity map, which
        is the statement a certificate has to make.
        """
        identity = PolynomialMap.from_ring(self.ring, self.ring.gens)

        for name, automorphism in (("G", self.G), ("H", self.H)):
            undone = automorphism.inverse().apply_to(automorphism.to_polynomial_map())
            if undone != identity:
                raise VerificationError(
                    "BCW-5",
                    f"The exhibited inverse of {name} does not undo it.",
                )

    def _verify_filtration(self) -> None:
        """BCW-6."""
        if not self.H.is_in_EA(self._filtration_level):
            raise VerificationError(
                "BCW-6",
                f"H does not lie in EA^{self._filtration_level}; it reaches "
                f"EA^{self.H.filtration_degree()}.",
            )

        if not self.G.is_in_EA(1):
            raise VerificationError(
                "BCW-6",
                "G does not lie in EA^1, which the formula guarantees; "
                "something is wrong with the step.",
            )

    def _verify_determinant(self) -> None:
        """BCW-7.

        Implied by BCW-1 together with every element of ``EA_n(k)`` having
        determinant one, and retained because it is cheap on the maps a
        reduction produces and localizes an error to the step that made it.
        """
        difference = sp.expand(self._target.determinant() - self._source.determinant())

        if difference != 0:
            raise VerificationError(
                "BCW-7",
                f"The determinant changed from {self._source.determinant()} "
                f"to {self._target.determinant()}.",
            )

    def transport(self, collision: Collision) -> Collision:
        """Pull a collision back through ``H`` and push its image through ``G``.

        With the fresh coordinates filled with zero, ``H^-1`` sends ``(a, 0, 0)``
        to ``(a, -P(a), -Q(a))``, and ``G`` leaves the padded image alone
        because ``X_u X_v`` vanishes there. Any constant fill would do, as
        long as the points share it; zero is fixed by the contract because a
        fill ``(s, t)`` merely moves the image component ``index`` to
        ``c_index - s t``.
        """
        collision.verify(self._source)

        appended = []
        for point in collision.points:
            substitution = dict(zip(self._source.variables, point, strict=True))
            appended.append(
                (
                    -sp.expand(self._P.xreplace(substitution)),
                    -sp.expand(self._Q.xreplace(substitution)),
                )
            )

        moved = collision.extended(appended, (0, 0))
        moved.verify(self._target)

        return moved

    # ----------------------------------------------------------------------

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BCWStep):
            return NotImplemented
        return (
            self._source == other._source
            and self._target == other._target
            and self._index == other._index
            and self._P == other._P
            and self._Q == other._Q
            and self._variables == other._variables
            and self._filtration_level == other._filtration_level
        )

    def __hash__(self) -> int:
        return hash(
            (
                self._source,
                self._target,
                self._index,
                self._P,
                self._Q,
                self._variables,
                self._filtration_level,
            )
        )

    def __repr__(self) -> str:
        return (
            f"BCWStep(index={self._index}, variables={self._variables}, "
            f"EA^{self._filtration_level}, "
            f"dimension={self._source.dimension}->{self._target.dimension}, "
            f"provenance={self._provenance.value})"
        )
