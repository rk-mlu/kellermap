"""Reproducible naming of fresh generators across a whole reduction.

``VariableFactory`` answers one question: given a ring and a count, what are
the new names. A reduction asks it many times, and the answers have to fit
together -- extending twice must land where extending once lands, and the same
reduction run twice must produce the same map, not merely an isomorphic one.

The context is what holds a factory to that. It is deliberately thin: it names
generators, extends rings and maps, and knows nothing about steps. Which step
to take is milestone 0.4, and a context that knew would be the wrong object to
ask.

What it does add is distrust. Both properties a factory promises are cheap to
check on the spot, and both are checked rather than assumed:

- calling the factory twice with equal arguments must give equal names, which
  catches the counting factory the ``VariableFactory`` docstring warns about;
- allocating ``count`` names at once must give the same sequence as allocating
  them one at a time, which catches a factory naming its output after the size
  of the ring it was handed.

Neither failure raises anywhere downstream. Both produce perfectly valid
polynomial maps that are simply not the ones the identity needs.

See ``docs/contracts.md``, RC-1 to RC-7.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import sympy as sp
from sympy.polys.rings import PolyRing

from .polynomial_map import PolynomialMap, clone_ring, validate_ring
from .variables import (
    DEFAULT_VARIABLE_FACTORY,
    FixedVariableFactory,
    VariableFactory,
    reserved_names,
)


@dataclass(frozen=True)
class ReductionContext:
    """The naming policy of one reduction.

    Frozen and stateless. Anything a reduction has to remember is passed as an
    argument, never carried here: a context that counted upwards would name
    the two sides of ``(F o G)^[m] = F^[m] o G^[m]`` differently, and would do
    so silently.

    Parameters
    ----------
    factory
        The naming policy. Must be pure and must compose; both are rechecked
        on every call.
    """

    factory: VariableFactory = field(default=DEFAULT_VARIABLE_FACTORY)

    # ----------------------------------------------------------------------
    # Naming
    # ----------------------------------------------------------------------

    def variables(self, ring: PolyRing, count: int) -> tuple[sp.Symbol, ...]:
        """Return ``count`` fresh generator names for ``ring``.

        A pure function of its two arguments: equal arguments give equal
        names, in this reduction, in another, and in a later process.
        """
        validate_ring(ring)
        _validate_count(count)

        if count == 0:
            return ()

        fresh = self._ask(ring, count)
        self._reject_non_composing(ring, fresh)

        return fresh

    def extended_ring(self, ring: PolyRing, count: int) -> PolyRing:
        """Return ``ring`` with ``count`` fresh generators appended.

        Coefficient domain and monomial order are those of ``ring``: a
        reduction runs in one arithmetic context from beginning to end.
        """
        fresh = self.variables(ring, count)
        if not fresh:
            return clone_ring(ring)

        return clone_ring(ring, tuple(ring.symbols) + fresh)

    def extend(self, F: PolynomialMap, count: int) -> PolynomialMap:  # noqa: N803
        """Return ``F^[count]``, with the generators this context names.

        The names are taken from ``variables`` and then pinned, so that the
        extension cannot reach a different answer than the caller would.
        """
        fresh = self.variables(F.ring, count)
        if not fresh:
            return F

        return F.extend(len(fresh), factory=FixedVariableFactory(fresh))

    # ----------------------------------------------------------------------
    # Distrust
    # ----------------------------------------------------------------------

    def _ask(self, ring: PolyRing, count: int) -> tuple[sp.Symbol, ...]:
        """Call the factory, twice, and check what it promised.

        The second call is the whole point of asking twice: a factory holding
        a counter answers differently the second time, and nothing else in the
        pipeline would notice.
        """
        view = clone_ring(ring)
        fresh = tuple(self.factory(view, count))
        again = tuple(self.factory(clone_ring(ring), count))

        if fresh != again:
            raise ValueError(
                "The variable factory is not a pure function of its "
                f"arguments: it returned {fresh} and then {again}."
            )

        _validate_fresh(fresh, count, ring)

        return fresh

    def _reject_non_composing(
        self, ring: PolyRing, fresh: tuple[sp.Symbol, ...]
    ) -> None:
        """Check that allocating one at a time gives the same sequence.

        Stable extension composes, ``(F^[m])^[l] = F^[m+l]``, and a reduction
        reaches the right-hand side through many calls of the left. A factory
        naming its output after the size of the ring it was handed is pure and
        never collides, and still breaks the identity.
        """
        stepwise: tuple[sp.Symbol, ...] = ()
        current = clone_ring(ring)

        for _ in range(len(fresh)):
            one = self._ask(current, 1)
            stepwise += one
            current = clone_ring(current, tuple(current.symbols) + one)

        if stepwise != fresh:
            raise ValueError(
                "The variable factory does not compose: allocating "
                f"{len(fresh)} names at once gave {fresh}, one at a time "
                f"{stepwise}."
            )


def _validate_count(count: int) -> None:
    # bool ist eine Unterklasse von int; count=True waere eine Erweiterung um
    # eine Variable und fast sicher ein Tippfehler.
    if isinstance(count, bool) or not isinstance(count, int):
        raise TypeError(
            f"The number of fresh variables must be an integer, "
            f"not {type(count).__name__}."
        )

    if count < 0:
        raise ValueError("The number of fresh variables must be non-negative.")


def _validate_fresh(fresh: tuple[sp.Symbol, ...], count: int, ring: PolyRing) -> None:
    """Check what the factory promised but is not trusted to have delivered."""
    if len(fresh) != count:
        raise ValueError(
            f"The variable factory returned {len(fresh)} names, expected {count}."
        )

    if not all(isinstance(symbol, sp.Symbol) for symbol in fresh):
        raise TypeError("The variable factory must return SymPy symbols.")

    if len({symbol.name for symbol in fresh}) != len(fresh):
        raise ValueError("The variable factory returned duplicate names.")

    collisions = {symbol.name for symbol in fresh} & reserved_names(ring)
    if collisions:
        raise ValueError(
            f"The variable factory returned names already in use: {sorted(collisions)}."
        )
