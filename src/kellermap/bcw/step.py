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
milestone 0.4.

Two things are wider here than in the paper, because the reduction of
Alpoege's map to dimension 17 needs them and the identity holds for both:

``P * Q`` is any subsum of the target component, not the factorization of a
single leading monomial. One step of that reduction removes four monomials of
degrees 7, 6, 5 and 4 at once, where a monomial-by-monomial application would
need one step per monomial of degree at least four, and at least eight of
them.

The target component is any component, not the first. Step seven of that
reduction acts on component 11, which step four introduced.

A step is given two *factor slots*. Each slot supplies one factor. ``Fresh``
introduces a new generator that carries the factor; ``Carried`` reuses a
coordinate of the source that already carries it. ``m`` is the number of
``Fresh`` slots, so ``m`` is 0, 1 or 2.

Two ``Fresh`` slots are the step of the paper. Reusing a coordinate is not in
the paper. It is admitted here because the identity above holds for every
``m``, and because a reduction that reuses carriers reaches a lower dimension:
the fifteen-dimensional reduction of Alpoege's map does so twice.

See ``docs/contracts.md``, BCW-1 to BCW-10.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import cast

import sympy as sp
from sympy.polys.rings import PolyElement, PolyRing

from ..canonical import agree
from ..collision import Collision
from ..elementary import ElementaryAutomorphism, ElementaryFactor
from ..errors import VerificationError
from ..polynomial_map import PolynomialMap
from ..reduction import Provenance
from ..variables import FixedVariableFactory, reserved_names


@dataclass(frozen=True)
class Fresh:
    """A factor supplied by a new generator.

    The generator ``variable`` is added by the step, and its component in the
    target is ``variable + polynomial``. The new coordinate therefore carries
    the factor, and a later step can reuse it with ``Carried``.
    """

    polynomial: sp.Expr
    variable: sp.Symbol

    def __post_init__(self) -> None:
        if not isinstance(self.variable, sp.Symbol):
            raise TypeError("A fresh variable must be a SymPy symbol.")

        try:
            value = sp.sympify(self.polynomial)
        except (sp.SympifyError, TypeError) as error:
            raise TypeError(
                f"The factor {self.polynomial!r} is not a SymPy expression."
            ) from error

        if not isinstance(value, sp.Expr):
            raise TypeError(
                f"The factor {self.polynomial!r} is not a SymPy expression."
            )

        object.__setattr__(self, "polynomial", value)


@dataclass(frozen=True)
class Carried:
    """A factor supplied by a coordinate that already carries it.

    Component ``index`` of the source has the form ``X_index + P``, so the
    factor ``P`` is available without a new generator. BCW-10 states what has
    to hold for that reading to be correct.
    """

    index: int

    def __post_init__(self) -> None:
        if isinstance(self.index, bool) or not isinstance(self.index, int):
            raise TypeError(
                f"A carried index must be an integer, not {type(self.index).__name__}."
            )
        if self.index < 0:
            raise ValueError("A carried index must not be negative.")


Factor = Fresh | Carried


def _coerce_factor(
    source: PolynomialMap,
    name: str,
    factor: sp.Expr,
) -> PolyElement:
    """Convert a factor into the source's ring, or explain why it will not go.

    One conversion answers three questions that name-based checks answered
    badly or not at all: whether the factor is a polynomial rather than
    ``1/x``, whether every symbol in it is either a coordinate or a parameter
    of the coefficient domain, and what its canonical form is. It also settles
    BCW-3, since the fresh variables are not generators of this ring.

    Coefficient parameters are admitted deliberately. A collision over
    ``k(T)`` is a collision -- COL-2 says so -- and a step over ``k[T]`` whose
    factor is ``T x`` should not be turned away for mentioning ``T``.
    """
    try:
        return cast(PolyElement, source.ring.from_expr(sp.sympify(factor)))
    except (ValueError, TypeError, sp.SympifyError) as error:
        raise ValueError(
            f"{name} must be a polynomial over the coefficient domain "
            f"{source.ring.domain} in the variables "
            f"{tuple(str(v) for v in source.variables)}; got {factor}."
        ) from error


def _slot_value(source: PolynomialMap, name: str, slot: Factor) -> PolyElement:
    """Return the factor a slot supplies, as an element of the source's ring.

    A ``Fresh`` slot supplies the polynomial it was given. A ``Carried(j)``
    slot supplies ``source.components[j] - X_j``, which needs no conversion:
    it is built from the source's own components.
    """
    if isinstance(slot, Fresh):
        return _coerce_factor(source, name, slot.polynomial)

    ring = source.ring

    return cast(
        PolyElement, source.to_polynomials()[slot.index] - ring.gens[slot.index]
    )


@dataclass(frozen=True, eq=False)
class BCWStep:
    """One application of Proposition (3.1).

    ``G`` and ``H`` are derived from ``index`` and the two slots by the
    formula, and are never supplied alongside them. Storing both a
    factorization and the automorphisms built from it would allow the two to
    disagree.

    Parameters
    ----------
    source, target
        The maps before and after. A ``target`` supplied here is what makes
        BCW-1 a real check; ``build`` computes it instead and records the
        weaker provenance.
    index
        The component from which ``P * Q`` is removed, zero-based.
    left, right
        The two factor slots. Each is a ``Fresh`` or a ``Carried``. Only two
        ``Fresh`` slots are accepted for now; see work package 2.
    filtration_level
        The ``EA`` level ``H`` is claimed to reach, 0 or 1.
    """

    _source: PolynomialMap
    _target: PolynomialMap
    _index: int
    _slots: tuple[Factor, Factor]
    _values: tuple[PolyElement, ...]
    _filtration_level: int
    _provenance: Provenance
    _verified: bool

    def __init__(
        self,
        source: PolynomialMap,
        target: PolynomialMap,
        index: int,
        left: Factor,
        right: Factor,
        filtration_level: int = 1,
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

        slots = (left, right)
        for position, slot in enumerate(slots):
            if not isinstance(slot, Fresh | Carried):
                raise TypeError(
                    f"Slot {position} must be a Fresh or a Carried, "
                    f"not {type(slot).__name__}."
                )
            # BCW-10, erste beide Klauseln. Konstruktorinvariante, weil ein
            # Platz ausserhalb des Bereichs oder auf der Zielkomponente die
            # Verschiebung von G nicht mehr frei von X_index liesse.
            if isinstance(slot, Carried):
                if not 0 <= slot.index < source.dimension:
                    raise ValueError(
                        f"Slot {position} reuses coordinate {slot.index}, "
                        f"which is out of range for {source.dimension} "
                        "components of the source."
                    )
                if slot.index == index:
                    raise ValueError(
                        f"Slot {position} reuses coordinate {slot.index}, "
                        "which is the component the step acts on."
                    )

        fresh = tuple(slot.variable for slot in slots if isinstance(slot, Fresh))

        # Nach dem Namen und nicht nach Symbol.__eq__: Symbol("v") und
        # Symbol("v", positive=True) sind fuer SymPy verschieden und fuer
        # einen PolyRing derselbe Generator.
        if len({symbol.name for symbol in fresh}) != len(fresh):
            raise ValueError("The fresh variables must be distinct.")

        # Frueh und nicht erst in verify(): ein kollidierender Name laesst
        # sich hinterher nicht mehr von einem falschen Ziel unterscheiden,
        # weil die Erweiterung dann zwei Koordinaten denselben Generator
        # bezeichnen liesse.
        # Gegen die reservierten Namen und nicht nur gegen die Koordinaten:
        # ein Parameter des Koeffizientenbereichs ist ebenso vergeben.
        taken = {symbol.name for symbol in fresh} & reserved_names(source.ring)
        if taken:
            raise ValueError(
                f"The variables {sorted(taken)} are already in use by the source."
            )

        values = tuple(
            _slot_value(source, name, slot)
            for name, slot in (("P", slots[0]), ("Q", slots[1]))
        )

        object.__setattr__(self, "_source", source)
        object.__setattr__(self, "_target", target)
        object.__setattr__(self, "_index", index)
        object.__setattr__(self, "_slots", slots)
        object.__setattr__(self, "_values", values)
        object.__setattr__(self, "_filtration_level", int(filtration_level))
        object.__setattr__(self, "_provenance", Provenance.SUPPLIED)
        object.__setattr__(self, "_verified", False)

    @classmethod
    def build(
        cls,
        source: PolynomialMap,
        index: int,
        left: Factor,
        right: Factor,
        filtration_level: int = 1,
    ) -> BCWStep:
        """Apply the formula and record the result as constructed.

        Convenient, and weaker evidence: BCW-1 then compares the
        implementation against itself rather than against a target that came
        from somewhere else.

        This is the only way to obtain a ``CONSTRUCTED`` step. The public
        constructor always records ``SUPPLIED``, since a target reaching it
        came from outside. The marker guards against mislabelling by accident,
        not against a caller determined to forge one -- Python has no privacy,
        and the attribute can be overwritten by anyone who wants to.

        The draft exists only to reach the formula, which needs ``G`` and
        ``H`` and therefore an instance; its target is a placeholder and is
        never looked at.
        """
        draft = cls(source, source, index, left, right, filtration_level)
        step = cls(source, draft._composite(), index, left, right, filtration_level)
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
    def index(self) -> int:
        """Return the component from which ``P * Q`` is removed."""
        return self._index

    @property
    def left(self) -> Factor:
        """Return the slot supplying the left factor."""
        return self._slots[0]

    @property
    def right(self) -> Factor:
        """Return the slot supplying the right factor."""
        return self._slots[1]

    @property
    def P(self) -> sp.Expr:  # noqa: N802
        """Return the left factor, as an expression."""
        return cast(sp.Expr, self._values[0].as_expr())

    @property
    def Q(self) -> sp.Expr:  # noqa: N802
        """Return the right factor, as an expression."""
        return cast(sp.Expr, self._values[1].as_expr())

    @property
    def variables(self) -> tuple[sp.Symbol, ...]:
        """Return the generators the step introduces, in slot order.

        The new generators only, not the variables of either map; those are
        ``source.variables`` and ``target.variables``.
        """
        return tuple(slot.variable for slot in self._slots if isinstance(slot, Fresh))

    @property
    def m(self) -> int:
        """Return the number of generators the step introduces."""
        return len(self.variables)

    @property
    def provenance(self) -> Provenance:
        """Return whether the target was supplied or constructed.

        Part of the value of the step, not metadata beside it: it is publicly
        observable, so two steps that disagree about it are not equal.
        """
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
        """Return ``F^[m]``, the source with ``m`` identity coordinates.

        The generators are pinned to the ones the step records. A supplied
        certificate names the variables it used, and those are honoured rather
        than reinvented. A step whose variables were unknown could not be
        checked at all. Where the names come from in the first place is the
        business of ``ReductionContext``.
        """
        fresh = self.variables
        if not fresh:
            return self._source

        return self._source.extend(len(fresh), factory=FixedVariableFactory(fresh))

    @property
    def ring(self) -> PolyRing:
        """Return the arithmetic context of ``G`` and ``H``."""
        return self.stabilized.ring

    @property
    def H(self) -> ElementaryAutomorphism:  # noqa: N802
        """Return one elementary factor per ``Fresh`` slot, in slot order.

        The factors commute, since no factor polynomial involves a fresh
        variable, so the order they are listed in does not matter. With no
        ``Fresh`` slot this is the identity.
        """
        ring = self.ring

        return ElementaryAutomorphism(
            [
                ElementaryFactor(ring, position, value.set_ring(ring))
                for position, value in zip(
                    self._fresh_positions(), self._fresh_values(), strict=True
                )
            ]
        )

    @property
    def G(self) -> ElementaryAutomorphism:  # noqa: N802
        """Return ``X_index |-> X_index - A * B``, the left factor.

        ``A`` and ``B`` are the coordinates of the two slots: the fresh
        generator for a ``Fresh`` slot, and ``X_j`` for a ``Carried(j)`` slot.
        """
        ring = self.ring
        left, right = self._slot_coordinates()

        return ElementaryAutomorphism(
            [ElementaryFactor(ring, self._index, -ring.gens[left] * ring.gens[right])]
        )

    def _fresh_positions(self) -> tuple[int, ...]:
        """Return the coordinate index of each fresh generator, in slot order."""
        offset = self._source.dimension

        return tuple(offset + position for position in range(len(self.variables)))

    def _fresh_values(self) -> tuple[PolyElement, ...]:
        """Return the factor of each ``Fresh`` slot, in slot order."""
        return tuple(
            value
            for slot, value in zip(self._slots, self._values, strict=True)
            if isinstance(slot, Fresh)
        )

    def _slot_coordinates(self) -> tuple[int, int]:
        """Return the coordinate index each slot contributes to ``G``."""
        offset = self._source.dimension
        indices = []
        fresh_seen = 0
        for slot in self._slots:
            if isinstance(slot, Fresh):
                indices.append(offset + fresh_seen)
                fresh_seen += 1
            else:
                indices.append(slot.index)

        return (indices[0], indices[1])

    def _composite(self) -> PolynomialMap:
        """Return ``G o F^[2] o H``."""
        return self.G.apply_to(
            self.stabilized.compose(self.H.to_polynomial_map(self.ring))
        )

    # ----------------------------------------------------------------------
    # Verification
    # ----------------------------------------------------------------------

    def verify(self) -> None:
        """Check BCW-1 to BCW-7, or raise ``VerificationError``."""
        if self._verified:
            return

        self._verify_generators()
        self._verify_carriers()
        self._verify_identity()
        self._verify_invertibility()
        self._verify_filtration()
        self._verify_determinant()

        object.__setattr__(self, "_verified", True)

    def _verify_generators(self) -> None:
        """BCW-2.

        BCW-3 does not appear here. ``P`` and ``Q`` are stored as elements of
        the source's ring, whose generators are the source's variables, so a
        factor mentioning a fresh variable cannot be built in the first place
        -- the same reasoning as COL-4, and stronger than reporting it later.
        """
        if self._target.dimension != self._source.dimension + self.m:
            raise VerificationError(
                "BCW-2",
                f"The source has dimension {self._source.dimension}, the "
                f"target {self._target.dimension}; a step with m = {self.m} "
                f"adds {self.m}.",
            )

        expected = self._source.variables + self.variables
        if self._target.variables != expected:
            raise VerificationError(
                "BCW-2",
                "The target does not carry the variables of the source "
                "followed by the fresh ones, in slot order.",
            )

    def _verify_carriers(self) -> None:
        """BCW-10, third clause.

        A reused coordinate has to be a carrier: ``source.components[j] - X_j``
        must be free of ``X_j``. The identity of BCW-1 holds without this, so
        it has to be checked separately. What it secures is the reading of the
        step -- that ``P`` is a value some coordinate carries, and not an
        arbitrary component minus a variable.
        """
        ring = self._source.ring

        for position, slot in enumerate(self._slots):
            if not isinstance(slot, Carried):
                continue

            value = self._values[position]
            if any(monomial[slot.index] for monomial in value.monoms()):
                raise VerificationError(
                    "BCW-10",
                    f"Slot {position} reuses coordinate {slot.index}, but "
                    f"component {slot.index} of the source is not "
                    f"{ring.gens[slot.index]} plus something free of it.",
                )

    def _verify_identity(self) -> None:
        """BCW-1."""
        try:
            composite = self._composite()
        except ValueError as error:  # pragma: no cover - constructor rules it out
            # Erreichbar nur, wenn die Erweiterung scheitert, und deren
            # Vorbedingungen -- Frische der Variablen, P und Q im Quellring --
            # erzwingt schon der Konstruktor.
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
            undone = automorphism.inverse().apply_to(
                automorphism.to_polynomial_map(self.ring)
            )
            if undone != identity:  # pragma: no cover - group law, not data
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

        if not self.G.is_in_EA(1):  # pragma: no cover - the formula fixes G
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

        As in ``LinearStep``, the canonical comparison is defensive: both
        determinants come out of a ``PolyRing`` and are normalized already.
        """
        # pragma-frei nicht erreichbar: BCW-1 laeuft vorher und setzt das Ziel
        # auf G o F^[2] o H, dessen Determinante die der Quelle ist.
        if not agree(  # pragma: no cover - implied by BCW-1
            self._target.determinant(), self._source.determinant()
        ):
            raise VerificationError(
                "BCW-7",
                f"The determinant changed from {self._source.determinant()} "
                f"to {self._target.determinant()}.",
            )

    def transport(self, collision: Collision) -> Collision:
        """Pull a collision back through ``H`` and push its image through ``G``.

        A point gains one coordinate per ``Fresh`` slot, in slot order. With
        the fresh coordinates filled with zero, ``H^-1`` sends ``(a, 0, 0)``
        to ``(a, -P(a), -Q(a))``. A ``Carried`` slot adds no coordinate,
        because the step adds no generator for it.

        The image gains a zero per ``Fresh`` slot, and ``G`` then reduces its
        component ``index`` by the product of the two slot values at that
        image. A ``Fresh`` slot contributes ``0`` there, so for ``m >= 1``
        the product vanishes and the image is unchanged apart from padding.
        Only at ``m = 0`` does the image move, to ``c_index - c_u * c_w``.

        Any constant fill would do, as long as the points share it; zero is
        fixed by the contract, because a fill ``(s, t)`` merely moves the
        image component ``index`` to ``c_index - s t``.
        """
        collision.verify(self._source)

        appended = [self._appended_coordinates(point) for point in collision.points]

        moved = collision.extended(appended, (sp.Integer(0),) * self.m)
        moved = moved.with_image(self._moved_image(moved.image))
        moved.verify(self._target)

        return moved

    def _appended_coordinates(self, point: tuple[sp.Expr, ...]) -> tuple[sp.Expr, ...]:
        """Return the coordinates a point gains, one per ``Fresh`` slot."""
        substitution = dict(zip(self._source.variables, point, strict=True))

        return tuple(
            -sp.expand(value.as_expr().xreplace(substitution))
            for slot, value in zip(self._slots, self._values, strict=True)
            if isinstance(slot, Fresh)
        )

    def _moved_image(self, padded: tuple[sp.Expr, ...]) -> tuple[sp.Expr, ...]:
        """Apply ``G`` to the padded image.

        The coordinate a slot contributes is ``0`` for a ``Fresh`` slot, since
        the fill is zero, and the image's own coordinate ``j`` for
        ``Carried(j)``.
        """
        left, right = (
            sp.Integer(0) if isinstance(slot, Fresh) else padded[slot.index]
            for slot in self._slots
        )

        image = list(padded)
        image[self._index] = sp.expand(image[self._index] - left * right)

        return tuple(image)

    # ----------------------------------------------------------------------

    def _key(self) -> tuple[object, ...]:
        """Return what equality compares.

        The slots are reduced to their content rather than compared directly.
        A ``Fresh`` slot holds the expression it was given, so two spellings
        of one polynomial would compare unequal; the converted value in
        ``_values`` is in normal form and does not have that problem.
        """
        slots = tuple(
            ("fresh", value, slot.variable.name)
            if isinstance(slot, Fresh)
            else ("carried", slot.index)
            for slot, value in zip(self._slots, self._values, strict=True)
        )

        return (
            self._source,
            self._target,
            self._index,
            slots,
            self._filtration_level,
            self._provenance,
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BCWStep):
            return NotImplemented
        return self._key() == other._key()

    def __hash__(self) -> int:
        return hash(self._key())

    def __repr__(self) -> str:
        return (
            f"BCWStep(index={self._index}, m={self.m}, "
            f"variables={self.variables}, "
            f"EA^{self._filtration_level}, "
            f"dimension={self._source.dimension}->{self._target.dimension}, "
            f"provenance={self._provenance.value})"
        )
