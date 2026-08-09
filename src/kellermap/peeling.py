"""Peeling: assembling a chain from the far end.

The forward search of ``kellermap.search`` walks from a source and needs to be
told what a fresh coordinate may carry and what it may be called. Peeling walks
from the target and needs neither. A step that introduces ``X_u`` leaves it in
exactly two components -- its own, as ``X_u + P``, and the residue of the
component it targeted -- so a coordinate occurring anywhere else was read by a
later step and cannot be the last one introduced. That test is what makes the
direction cheap: six of the sixteen carriers of the published
nineteen-dimensional map satisfy it, against the hundred and forty candidates
the forward enumerator offers at a map of that size.

Undoing needs no inverse. A step subtracts the product of its two slot
components, so ``F_i = F'_i +- F'_a F'_b`` recovers the map before it, and every
peeled coordinate must then occur in no remaining component.

The sign is not fixed, and that is the one place where peeling still has to
look outwards. This library's ``G`` always subtracts, but the published map is
not in that convention, and the difference is the diagonal ``D`` of SEA-5.
Peeling that map with ``+`` alone stops at dimension 18 and with ``-`` alone at
17, while both together reach 15. Each step peeled with ``-`` is one linear
equation ``d_i d_a d_b = -1`` over GF(2), so the constraints on ``D`` accumulate
while the peel runs rather than having to be solved for afterwards.

A peel is not a certificate. What it produces is a structure; the chain is
rebuilt forwards with ``BCWStep.build``, verified, and only then a
``Reduction``. See ``docs/contracts.md``, REV-1 to REV-7.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from itertools import combinations

import sympy as sp

from .bcw import BCWStep, Carried, Fresh
from .bcw.step import Factor
from .linear import over_field
from .polynomial_map import PolynomialMap
from .reduction import Reduction
from .search import conjugate


@dataclass(frozen=True)
class Undo:
    """One step of a peel, named by generators and not by positions.

    Positions belong to the map a step was taken at, and peeling changes the
    map at every step. Names do not move.
    """

    target: sp.Symbol
    slots: tuple[sp.Symbol, sp.Symbol]
    dropped: tuple[sp.Symbol, ...]
    factor: sp.Expr


@dataclass(frozen=True)
class PeelOutcome:
    """What a peel returns.

    ``reduction`` is a chain rebuilt forwards and verified, or ``None``.
    ``signs`` is the diagonal of SEA-5. ``examined`` and ``deepest`` report the
    budget and how far the peel got, as SEA-11 asks; ``exhausted`` says whether
    the space this peel covers was seen to the end.
    """

    reduction: Reduction | None
    signs: tuple[int, ...] | None
    examined: int
    deepest: int
    exhausted: bool


def removable(current: PolynomialMap) -> dict[sp.Symbol, sp.Symbol]:
    """Return each coordinate that could have been introduced last.

    The value is the component that coordinate also occurs in, which is the one
    the step that introduced it targeted. REV-2: a coordinate occurring in any
    third component was read by a later step, and a coordinate occurring only
    in its own was never left anywhere by the step that made it.
    """
    found: dict[sp.Symbol, sp.Symbol] = {}

    for position, variable in enumerate(current.variables):
        occurrences = [
            other
            for other, component in zip(
                current.variables, current.components, strict=True
            )
            if variable in sp.expand(component).free_symbols
        ]
        if len(occurrences) == 2 and current.variables[position] in occurrences:
            found[variable] = next(other for other in occurrences if other != variable)

    return found


def undo(
    current: PolynomialMap,
    step: Undo,
) -> PolynomialMap | None:
    """Return the map before ``step``, or ``None`` if it was not that step.

    REV-3. The arithmetic is exact and the check is the second half: a
    coordinate that survives the undoing was not introduced by the step being
    undone.
    """
    index = {variable: position for position, variable in enumerate(current.variables)}
    if step.target not in index or any(slot not in index for slot in step.slots):
        return None

    left, right = (current.components[index[slot]] for slot in step.slots)
    components = list(current.components)
    components[index[step.target]] = sp.expand(
        components[index[step.target]] + step.factor * left * right
    )

    kept = [
        (variable, component)
        for variable, component in zip(current.variables, components, strict=True)
        if variable not in step.dropped
    ]
    if any(
        dropped in sp.expand(component).free_symbols
        for _, component in kept
        for dropped in step.dropped
    ):
        return None

    reached = PolynomialMap(
        tuple(variable for variable, _ in kept),
        tuple(component for _, component in kept),
    )

    # Rebuilding from expressions infers the coefficient domain afresh, and a
    # map over ``QQ`` would come back over ``ZZ`` and compare unequal to the
    # one it came from. Peeling changes the coordinates, not the domain.
    return over_field(reached) if current.ring.domain.is_Field else reached


def factor(
    current: PolynomialMap,
    target: sp.Symbol,
    slots: tuple[sp.Symbol, sp.Symbol],
    dropped: tuple[sp.Symbol, ...],
) -> sp.Expr | None:
    """Return the constant that makes the dropped coordinates cancel.

    A step subtracts ``d_i / (d_u d_v)`` times the product of its slot
    components once the map has been conjugated by a diagonal ``D``, so undoing
    it adds some non-zero constant times that product back. The constant is not
    guessed: the terms carrying a dropped coordinate have to vanish, which
    fixes it, and ``None`` says no constant does.

    ``dropped`` may hold two coordinates, and one of them settles the constant.
    Whether it also suits the other is decided by ``undo``, which requires
    every dropped coordinate to have gone.

    Until 0.4 this tried ``+1`` and ``-1``. That was too narrow -- see
    ``conjugate`` and ``roadmap.md`` -- and solving costs less than trying two.
    """
    components = dict(zip(current.variables, current.components, strict=True))
    product = sp.expand(components[slots[0]] * components[slots[1]])

    # One dropped coordinate settles it. A second would give a second equation
    # for the same constant, and checking that the two agree would duplicate
    # what ``undo`` does anyway: it requires *every* dropped coordinate to have
    # vanished, so a constant that suits only the first is rejected there.
    coordinate = dropped[0]
    here = sp.expand(components[target]).coeff(coordinate, 1)
    there = product.coeff(coordinate, 1)

    # Nicht erreichbar: die Komponente eines Platzes ist ``X + P`` und nie
    # null, also ist das Produkt in jeder Platzkoordinate linear mit einem
    # Koeffizienten ungleich null.
    if there == 0:  # pragma: no cover - a slot component is never zero
        return None

    ratio = sp.cancel(-here / there)

    return None if ratio == 0 or ratio.free_symbols else ratio


def moves(current: PolynomialMap, spare: int) -> Iterator[Undo]:
    """Yield the steps that could have been the last one, in a fixed order.

    Steps removing two coordinates first, then those removing one, then those
    removing none, and the last kind only while ``spare`` allows. The order
    discards nothing -- every move is still walked -- and it decides which
    chain is reached first, which is what a bounded budget makes visible. A
    step that removes two coordinates gets twice as far for the same depth.

    A step that introduces nothing is admitted only where undoing it makes its
    target component shorter, which is what a step that removed a product
    leaves behind.
    """
    peelable = removable(current)
    carriers = tuple(
        variable
        for position, variable in enumerate(current.variables)
        if variable
        not in sp.expand(current.components[position] - variable).free_symbols
    )

    for first, second in combinations(tuple(peelable), 2):
        if peelable[first] != peelable[second]:
            continue
        target = peelable[first]
        found = factor(current, target, (first, second), (first, second))
        if found is not None:
            yield Undo(target, (first, second), (first, second), found)

    for fresh, target in peelable.items():
        for carried in carriers:
            if carried in (fresh, target):
                continue
            found = factor(current, target, (carried, fresh), (fresh,))
            if found is not None:
                yield Undo(target, (carried, fresh), (fresh,), found)

    if spare <= 0:
        return

    components = dict(zip(current.variables, current.components, strict=True))
    sizes = {
        variable: len(sp.Add.make_args(sp.expand(component)))
        for variable, component in components.items()
    }
    # Das Produkt der beiden Platzkomponenten haengt weder vom Ziel noch vom
    # Vorzeichen ab. Es einmal je Paar zu rechnen statt einmal je Kandidat ist
    # bei neunzehn Koordinaten der Unterschied zwischen einer und vierzig
    # Multiplikationen dichter Polynome.
    for left, right in combinations(carriers, 2):
        product = sp.expand(components[left] * components[right])
        shared = sp.Poly(product, *current.variables).as_dict()
        for target, size in sizes.items():
            if size <= 2 or target in (left, right):
                continue
            here = sp.Poly(components[target], *current.variables).as_dict()
            # A step that introduces nothing cancels no coordinate, so the
            # constant is not fixed by REV-3. What fixes it is that the step
            # removed something: every monomial the two share gives the one
            # constant that cancels it, and only a constant that shortens the
            # component is offered.
            for monomial, coefficient in here.items():
                if monomial not in shared:
                    continue
                candidate = sp.cancel(-coefficient / shared[monomial])
                shortened = sp.expand(components[target] + candidate * product)
                if shortened != 0 and len(sp.Add.make_args(shortened)) < size:
                    yield Undo(target, (left, right), (), candidate)


def peel(
    source: PolynomialMap,
    target: PolynomialMap,
    *,
    budget: int = 20000,
    spare: int = 1,
) -> PeelOutcome:
    """Take ``target`` apart until ``source`` is left, then rebuild forwards.

    Nothing is supplied but the two maps: no value pool, no names, no sign
    convention (REV-1). What comes back is a chain built by ``BCWStep.build``
    and verified, together with the diagonal ``D`` of SEA-5, or nothing.

    ``spare`` bounds the steps that remove no coordinate, as it does for the
    forward search. ``budget`` bounds the maps examined.
    """
    remaining = [budget]
    deepest = [0]

    def walk(
        current: PolynomialMap, path: tuple[Undo, ...], spare_left: int
    ) -> PeelOutcome | None:
        if remaining[0] <= 0:
            return None
        remaining[0] -= 1
        deepest[0] = max(deepest[0], len(path))

        if current.dimension == source.dimension:
            found = _rebuild(source, target, path, budget - remaining[0], deepest[0])
            if found is not None:
                return found

        for step in moves(current, spare_left):
            reached = undo(current, step)
            if reached is None or reached.dimension < source.dimension:
                continue

            found = walk(
                reached,
                (*path, step),
                spare_left - (0 if step.dropped else 1),
            )
            if found is not None:
                return found

        return None

    outcome = walk(target, (), spare)
    if outcome is not None:
        return outcome

    return PeelOutcome(
        None, None, budget - max(remaining[0], 0), deepest[0], remaining[0] > 0
    )


def _scaling(
    source: PolynomialMap,
    target: PolynomialMap,
    path: tuple[Undo, ...],
) -> tuple[sp.Expr, ...] | None:
    """Solve the constants the peel collected into the diagonal of SEA-5.

    Conjugating by ``D`` turns a step into

        G'_i = G_i - (d_i / (d_u d_v)) G_u G_v,

    so a step undone with the constant ``f`` says ``f = d_i / (d_u d_v)``. Read
    in the order the chain was built, each step introduces its fresh
    coordinates as new unknowns while its target and any reused coordinate are
    already fixed, so the equations solve by substitution rather than as a
    system. A step with two fresh coordinates leaves one degree of freedom,
    which is spent on the first of them; a step with none is a consistency
    check and can fail.

    The coordinates that survive the whole peel are the source's and are fixed
    to ``1``: the source is data, not something a scaling may be chosen for.
    """
    scale: dict[sp.Symbol, sp.Expr] = {
        variable: sp.Integer(1) for variable in source.variables
    }

    for step in reversed(path):
        fresh = [slot for slot in step.slots if slot in step.dropped]
        known = [slot for slot in step.slots if slot not in step.dropped]

        if len(fresh) == 2:
            scale[fresh[0]] = sp.Integer(1)
            scale[fresh[1]] = sp.cancel(scale[step.target] / step.factor)
        elif len(fresh) == 1:
            scale[fresh[0]] = sp.cancel(
                scale[step.target] / (step.factor * scale[known[0]])
            )
        else:
            wanted = sp.cancel(scale[step.target] / (scale[known[0]] * scale[known[1]]))
            if sp.simplify(wanted - step.factor) != 0:
                return None

    if any(variable not in scale for variable in target.variables):
        return None  # pragma: no cover - every coordinate is source or dropped

    return tuple(scale[variable] for variable in target.variables)


def _rebuild(
    source: PolynomialMap,
    target: PolynomialMap,
    path: tuple[Undo, ...],
    examined: int,
    deepest: int,
) -> PeelOutcome | None:
    """Replay the peel forwards and verify every step of it.

    REV-5. The peel produced a structure; this builds the chain. The two agree
    or the result is discarded, and the endpoint is compared against the target
    as SEA-5 requires.
    """
    signs = _scaling(source, target, path)
    if signs is None:
        return None

    aligned = conjugate(target, signs)
    maps = [aligned]
    for step in path:
        reached = undo(
            maps[-1], Undo(step.target, step.slots, step.dropped, sp.Integer(1))
        )
        # Nicht erreichbar: unter der Konjugation mit ``D`` nimmt der
        # Produktterm eines mit ``s`` abgetragenen Schritts den Faktor
        # ``d_i d_a d_b = s`` auf, wird also ``+1``. Ein loesbares System heisst
        # genau, dass die Wiederholung mit ``+1`` durchgeht.
        if reached is None:  # pragma: no cover - implied by the solved system
            return None
        maps.append(reached)

    if maps[-1].reordered(source.variables) != source:
        return None

    steps: list[BCWStep] = []
    current = maps[-1]
    for step, after in zip(reversed(path), reversed(maps[:-1]), strict=True):
        built = _forward(current, step, after)
        # Nicht erreichbar: ``after`` ist durch Rueckrechnen aus ``current``
        # entstanden, also baut derselbe Schritt vorwaerts wieder ``after``.
        if built is None:  # pragma: no cover - the step came from undoing this
            return None
        steps.append(built)
        current = built.target

    # Nicht erreichbar: jeder Einzelschritt hat oben schon gegen seine Karte
    # geprueft, und die erste davon ist ``aligned``.
    if current.reordered(aligned.variables) != aligned:  # pragma: no cover - per step
        return None

    return PeelOutcome(Reduction(tuple(steps)), signs, examined, deepest, False)


def _forward(
    current: PolynomialMap,
    step: Undo,
    after: PolynomialMap,
) -> BCWStep | None:
    """Build the step the peel undid, and verify it against what it undid."""
    factors: list[Factor] = []
    for slot in step.slots:
        if slot in step.dropped:
            position = after.variables.index(slot)
            factors.append(Fresh(sp.expand(after.components[position] - slot), slot))
        else:
            factors.append(Carried(current.variables.index(slot)))

    orders = [
        min(
            sum(monomial)
            for monomial in sp.Poly(factor.polynomial, *after.variables).monoms()
        )
        for factor in factors
        if isinstance(factor, Fresh)
    ]
    level = 1 if all(order >= 2 for order in orders) else 0

    built = BCWStep.build(
        current,
        current.variables.index(step.target),
        factors[0],
        factors[1],
        level,
    )
    built.verify()

    # Nicht erreichbar, und als Selbstpruefung behalten: der Schritt stammt aus
    # dem Rueckrechnen von ``after`` und baut es daher wieder auf.
    if built.target.reordered(after.variables) != after:  # pragma: no cover - undone
        return None

    return built
