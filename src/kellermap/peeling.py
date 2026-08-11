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

The constant a step removed is not fixed and is not guessed. It is solved: the
requirement that the peeled coordinates vanish is linear in it. That constant
is the ``coefficient`` of BCW-11 and goes into the step the peel rebuilds. It
was an entry of a diagonal ``D`` between work packages 7 and 10, because the
step had nowhere to put a scalar; BCW-11 gave it one, and SEA-5 went back to
plain equality.

A peel is not a certificate. What it produces is a structure; the chain is
rebuilt forwards with ``BCWStep.build``, verified, and only then a
``Reduction``. See ``docs/contracts.md``, REV-1 to REV-7.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from itertools import combinations, combinations_with_replacement

import sympy as sp
from sympy.polys.polyerrors import CoercionFailed, ExactQuotientFailed

from .bcw import BCWStep, Carried, Fresh
from .bcw.step import Factor
from .errors import VerificationError
from .polynomial_map import PolynomialMap, clone_ring
from .reduction import Reduction


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
    ``examined`` and ``deepest`` report the budget and how far the peel got, as
    SEA-11 asks; ``exhausted`` says whether the space this peel covers was seen
    to the end.

    There was a ``signs`` field between work packages 9 and 10, holding the
    diagonal of SEA-5. BCW-11 removed the need for it: the constant a step is
    undone with is now the step's own coefficient, so the chain reaches the
    target exactly and there is nothing left for a diagonal to carry.
    """

    reduction: Reduction | None
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

    # Rebuilding from expressions would infer the coefficient domain and the
    # monomial order afresh: a map over ``QQ`` came back over ``ZZ``, and
    # ``grlex`` came back as whatever the expressions suggested. Peeling
    # changes which coordinates there are and nothing else, so the ring is
    # cloned from the old one.
    #
    # With the generator objects and not with their printed names. Naming them
    # gave plain symbols back, so ``Symbol("x", positive=True)`` in a component
    # no longer matched the ``Symbol("x")`` of the ring and the conversion
    # failed; a name that is not an identifier was reparsed into several
    # generators. Both found by an external audit.
    reduced = clone_ring(current.ring, tuple(variable for variable, _ in kept))

    return PolynomialMap.from_ring(
        reduced,
        tuple(reduced.from_expr(component) for _, component in kept),
    )


def factor(
    current: PolynomialMap,
    target: sp.Symbol,
    slots: tuple[sp.Symbol, sp.Symbol],
    dropped: tuple[sp.Symbol, ...],
) -> sp.Expr | None:
    """Return the constant that makes the dropped coordinates cancel.

    A step subtracts ``d_i / (d_u d_v)`` times the product of its slot
    components, so undoing it adds some non-zero constant times that product
    back. The constant is not
    guessed: the terms carrying a dropped coordinate have to vanish, which
    fixes it, and ``None`` says no constant of the coefficient domain does. A
    parameter of that domain is a constant here: ``T`` in ``ZZ[T]`` is a legal
    coefficient by BCW-11, and only a quotient involving a *coordinate* is
    refused.

    ``dropped`` may hold two coordinates, and one of them settles the constant.
    Whether it also suits the other is decided by ``undo``, which requires
    every dropped coordinate to have gone.

    Until 0.4 this tried ``+1`` and ``-1``. That was too narrow -- see
    ``conjugate`` and ``roadmap.md`` -- and solving costs less than trying two.
    """
    ring = current.ring
    domain = ring.domain
    polynomials = dict(zip(current.variables, current.to_polynomials(), strict=True))
    product = polynomials[slots[0]] * polynomials[slots[1]]
    position = current.variables.index(dropped[0])

    # Der Rest der Zielkomponente ist frei von der abgetragenen Koordinate,
    # also gibt *jedes* Monom des Produkts, das sie enthaelt, dieselbe
    # Konstante. Genommen wird das mit dem hoechsten Grad darin: bei zwei
    # verschiedenen frischen Koordinaten ist das Grad eins wie bisher, und bei
    # zwei Plaetzen auf einer Koordinate mit Faktor null ist ``(u + 0)**2 =
    # u**2`` das einzige, das sie ueberhaupt enthaelt. Auf Grad eins allein zu
    # sehen liess diesen Fall unauffindbar erscheinen; ein externes Audit hat
    # ihn gebaut.
    carrying = [
        (monomial, coefficient)
        for monomial, coefficient in product.terms()
        if monomial[position]
    ]
    # Nicht erreichbar: einer der beiden Plaetze *ist* die abgetragene
    # Koordinate, ihre Komponente ist ``X_u + P``, und die andere ist nie null,
    # also enthaelt das Produkt sie.
    if not carrying:  # pragma: no cover - a slot component is never zero
        return None

    # Kanonisch und nicht das erste passende: hoechster Grad in der Koordinate,
    # bei Gleichstand das groesste Monom der Ringordnung. Welches genommen wird,
    # darf nicht an der Reihenfolge der Terme haengen.
    monomial, there = max(carrying, key=lambda term: (term[0][position], term[0]))
    here = dict(polynomials[target].terms()).get(monomial)
    if here is None:
        return None

    try:
        ratio = -domain.exquo(here, there)
    except (
        CoercionFailed,
        ExactQuotientFailed,
        NotImplementedError,
        ZeroDivisionError,
    ):
        # Der Quotient liegt nicht in der Koeffizientendomaene. Konversion statt
        # Inspektion, wie BCW-3, BCW-11 und TRA-2: ein Test auf ``free_symbols``
        # wuerde ``T`` in ``ZZ[T]`` fuer eine Koordinate halten und einen
        # Koeffizienten ablehnen, den BCW-11 ausdruecklich zulaesst.
        return None

    return None if not ratio else sp.sympify(domain.to_sympy(ratio))


def _squared(current: PolynomialMap, target: sp.Symbol, fresh: sp.Symbol) -> bool:
    """Return whether ``fresh`` occurs squared in the component of ``target``.

    A step whose two slots are one fresh coordinate leaves ``-c X_u**2`` in the
    component it acted on, so the coordinate stands there squared unless that
    term cancelled. A necessary condition of the same kind as REV-2, and read
    off the map rather than assumed about the chain.
    """
    position = current.variables.index(fresh)
    component = sp.Poly(
        sp.expand(current.components[current.variables.index(target)]),
        *current.variables,
    )

    return any(monomial[position] >= 2 for monomial in component.monoms())


def moves(
    current: PolynomialMap,
    spare: int,
    pairs: int = 16,
    last: bool = True,
) -> Iterator[Undo]:
    """Yield the steps that could have been the last one, in a fixed order.

    Steps removing two coordinates come first while ``pairs`` is plentiful and
    last while it is scarce; steps removing none come last of all. A step
    removing two is offered only while ``pairs`` allows and ``last`` is set, one
    removing none only while ``spare`` allows. The order
    discards nothing -- every move is still walked -- and it decides which
    chain is reached first, which is what a bounded budget makes visible. A
    step that removes two coordinates gets twice as far for the same depth.

    A step that introduces nothing has no dropped coordinate to fix its
    constant, so the constants tried are those that cancel one of the monomials
    the target component shares with the product. REV-10 says what that leaves
    out; the requirement that the component get *shorter* was dropped in
    0.4.0rc4, because undoing adds a product back and the component usually
    grows.
    """
    peelable = removable(current)
    carriers = tuple(
        variable
        for position, variable in enumerate(current.variables)
        if variable
        not in sp.expand(current.components[position] - variable).free_symbols
    )

    doubles = []
    if pairs > 0 and last:
        for first, second in combinations(tuple(peelable), 2):
            if peelable[first] != peelable[second]:
                continue
            target = peelable[first]
            found = factor(current, target, (first, second), (first, second))
            if found is not None:
                doubles.append(Undo(target, (first, second), (first, second), found))

    # Ist die Erlaubnis reichlich, kommen sie zuerst: ein Zug, der zwei
    # Koordinaten entfernt, kommt fuer dieselbe Tiefe doppelt so weit. Ist sie
    # knapp, kommen sie zuletzt -- bei ``pairs = 1`` ist der eine solche Schritt
    # nach REV-8 der letzte des Abtrags, und ihn zuerst zu versuchen gibt die
    # einzige Erlaubnis frueh aus.
    if pairs > 1:
        yield from doubles

    for fresh, target in peelable.items():
        # BCW-12: eine frische Koordinate darf beide Plaetze fuellen. ``G``
        # subtrahiert dann ein Quadrat, also steht die Koordinate quadriert in
        # der Zielkomponente -- dieselbe Art von Signatur wie REV-2, und aus
        # dem Ziel ablesbar. Genau eine Traegervariable der veroeffentlichten
        # Abbildung kommt quadriert vor.
        if _squared(current, target, fresh):
            found = factor(current, target, (fresh, fresh), (fresh,))
            if found is not None:
                yield Undo(target, (fresh, fresh), (fresh,), found)

        for carried in carriers:
            if carried in (fresh, target):
                continue
            found = factor(current, target, (carried, fresh), (fresh,))
            if found is not None:
                yield Undo(target, (carried, fresh), (fresh,), found)

    if pairs <= 1:
        yield from doubles

    if spare <= 0:
        return

    # Von hier an wird im Ring der Karte gerechnet und nicht in Ausdruecken.
    # Ausdruecke haben zweimal getaeuscht: ``S*a*x - T*a*x`` sind zwei
    # Summanden und ein Monom mit Koeffizient ``S - T``, also sah ein Schritt
    # nicht wie eine Kuerzung aus; und ein Quotient wie ``1/2`` sieht wie eine
    # Konstante aus, liegt aber nicht in ``ZZ``, was den Abtrag zum Absturz
    # brachte. Beides hat ein externes Audit gefunden.
    ring = current.ring
    domain = ring.domain
    polynomials = dict(zip(current.variables, current.to_polynomials(), strict=True))
    sizes = {variable: len(value.terms()) for variable, value in polynomials.items()}

    # Das Produkt der beiden Platzkomponenten haengt weder vom Ziel noch von der
    # Konstanten ab. Es einmal je Paar zu rechnen statt einmal je Kandidat ist
    # bei neunzehn Koordinaten der Unterschied zwischen einer und vierzig
    # Multiplikationen dichter Polynome.
    #
    # With replacement: BCW-6 admits both slots naming the same coordinate, and
    # ``combinations`` alone would never offer ``G = X_i - X_j**2``. The step
    # type has accepted it since 0.3; the peel did not enumerate it.
    for left, right in combinations_with_replacement(carriers, 2):
        product = polynomials[left] * polynomials[right]
        shared = dict(product.terms())
        for target in sizes:
            if target in (left, right):
                continue

            # A step that introduces nothing cancels no coordinate, so the
            # constant is not fixed by REV-3. What fixes it is a monomial the
            # step left behind: every monomial the two share gives the one
            # constant that cancels it. Where the removed product cancelled the
            # component's terms exactly, the two share nothing, every constant
            # gives a map, and the step is out of reach -- REV-10 says so.
            #
            # A candidate used to have to shorten the component. That was one
            # case taken for all of them: undoing an m = 0 step adds a product
            # back, so the component usually grows, and the requirement only
            # held where the forward step had grown it.
            #
            # Several shared monomials often give the same constant, and each
            # gave a move of its own until 0.4.0rc2: thirty-six candidates at
            # the root of the published map against sixteen distinct ones.
            constants = set()
            for monomial, coefficient in polynomials[target].terms():
                if monomial not in shared:
                    continue
                try:
                    constants.add(-domain.exquo(coefficient, shared[monomial]))
                except (
                    CoercionFailed,
                    ExactQuotientFailed,
                    NotImplementedError,
                    ZeroDivisionError,
                ):
                    # Der Quotient liegt nicht in der Koeffizientendomaene. Ein
                    # Schritt mit ihm ist ueber diesem Ring keiner.
                    continue

            # Sortiert und nicht in der Reihenfolge einer Menge: ``moves``
            # sagt zu, die Zuege in fester Reihenfolge auszugeben, und die
            # Iteration ueber ein ``set`` haengt am Hash-Seed. Bei knappem
            # Budget entscheidet das, welche Kette zuerst gefunden wird.
            for candidate in sorted(
                constants, key=lambda value: sp.default_sort_key(domain.to_sympy(value))
            ):
                shortened = polynomials[target] + candidate * product
                if shortened and shortened != polynomials[target]:
                    yield Undo(
                        target,
                        (left, right),
                        (),
                        sp.sympify(domain.to_sympy(candidate)),
                    )


def peel(
    source: PolynomialMap,
    target: PolynomialMap,
    *,
    budget: int = 20000,
    spare: int = 1,
    pairs: int = 16,
) -> PeelOutcome:
    """Take ``target`` apart until ``source`` is left, then rebuild forwards.

    Nothing is supplied but the two maps: no value pool, no names, no sign
    convention (REV-1). What comes back is a chain built by ``BCWStep.build``
    and verified, or nothing. The endpoint equals the target exactly; there is
    no diagonal to reconcile, because each step carries its own constant.

    Nothing about the ring changes along the way: the coefficient domain and
    the monomial order of the target are carried into every intermediate map,
    and a constant of that domain -- a parameter such as ``T`` in ``ZZ[T]``
    included -- is a legal coefficient by BCW-11.

    ``spare`` bounds the steps that remove no coordinate, as it does for the
    forward search. ``pairs`` bounds the steps that remove two, which is the
    arithmetic of REV-8 turned into a rule: with ``a`` steps introducing two
    generators, ``b`` introducing one and ``c`` introducing none, a chain of
    ``n`` generators has ``2a + b = n`` and ``S = n - a + c`` steps, so fixing
    the number of steps fixes ``a``. Both bounds are decisions about which
    chains are looked for, and a chain outside them is unreachable rather than
    absent. ``budget`` bounds the maps examined.
    """
    remaining = [budget]
    deepest = [0]
    # A map reached twice with the same allowances leads to the same subtree,
    # and independent steps commute, so the same map is reached by every order
    # of them. What has to be in the key besides the map is what the walk still
    # may spend: the same map with a spare step left is not the same state.
    seen: set[tuple[PolynomialMap, int, int]] = set()

    def walk(
        current: PolynomialMap,
        path: tuple[Undo, ...],
        spare_left: int,
        pairs_left: int,
    ) -> PeelOutcome | None:
        if remaining[0] <= 0:
            return None

        state = (current, spare_left, pairs_left)
        if state in seen:
            return None
        seen.add(state)

        remaining[0] -= 1
        deepest[0] = max(deepest[0], len(path))

        if current.dimension == source.dimension:
            # Der Vergleich hier und nicht in ``_rebuild``: dort kostet er das
            # nochmalige Rueckrechnen des ganzen Pfades, hier eine Gleichheit.
            if current.reordered(source.variables) == source:
                found = _rebuild(
                    source, target, path, budget - remaining[0], deepest[0]
                )
                if found is not None:
                    return found

        reachable = []
        for step in moves(
            current,
            spare_left,
            pairs_left,
            last=current.dimension <= source.dimension + 2 or pairs_left > 1,
        ):
            reached = undo(current, step)
            if reached is None or reached.dimension < source.dimension:
                continue
            # REV-2 ist ein Muster und keine Gewissheit: eine Koordinate der
            # Quelle kann zufaellig in genau zwei Komponenten stehen und wird
            # dann probeweise abgetragen. Die Karte danach kann die Quelle nicht
            # mehr enthalten, und alles Weitere setzt voraus, dass sie es tut.
            # Frueher lief ``_unfinishable`` in einen ``KeyError``; ein externes
            # Audit hat das gebaut.
            if not set(source.variables) <= set(reached.variables):
                continue
            if _stranded(source, reached):
                continue
            if _unfinishable(source, reached, spare_left - (0 if step.dropped else 1)):
                continue
            # Vorwaerts faellt der Grad nie -- die neuen Terme haben Grad
            # hoechstens ``1 + deg Q <= deg(P Q)``, solange kein Faktor konstant
            # ist, und Konstanten sind ausgeschlossen. Rueckwaerts steigt er
            # also nie ueber den der Quelle.
            if reached.degree() > source.degree():
                continue

            reachable.append((_size(reached), step, reached))

        reachable.sort(key=lambda entry: entry[0])

        for _, step, reached in reachable:
            found = walk(
                reached,
                (*path, step),
                spare_left - (0 if step.dropped else 1),
                pairs_left - (1 if len(step.dropped) == 2 else 0),
            )
            if found is not None:
                return found

        return None

    outcome = walk(target, (), spare, pairs)
    if outcome is not None:
        return outcome

    return PeelOutcome(
        None, budget - max(remaining[0], 0), deepest[0], remaining[0] > 0
    )


def _size(reached: PolynomialMap) -> tuple[int, int]:
    """Return how small a map is, for ordering the moves out of one.

    Terms first, then coordinates. Undoing a step takes the residue out and
    puts the removed product back, so a peel going the right way makes the map
    shorter, and the source is the shortest map on the chain.

    An ordering and not a filter. The terms a step leaves behind number
    ``1 + t(P) + t(Q)`` before cancellation, which is six when both factors are
    monomials -- fifteen of the sixteen carrier values of the published map are
    -- and something else for ``bcw17``, where five of fourteen are not.
    Ranking by the result needs no such assumption, and ranking discards
    nothing.
    """
    return (
        sum(len(sp.Add.make_args(component)) for component in reached.components),
        reached.dimension,
    )


def _unfinishable(source: PolynomialMap, reached: PolynomialMap, spare: int) -> bool:
    """Return whether too many components still differ for the steps that are left.

    An undo changes exactly one component, the one its step acted on. Every
    coordinate that survives the whole peel is a coordinate of the source, so
    each of those whose component still differs needs at least one more step
    aimed at it. The steps left are bounded: ``d`` coordinates have to go and a
    step removes at least one unless it is a spare, so at most ``d + spare``
    steps remain.

    Cheap, sound, and it bites late, which is where the search spends its time:
    a peel two steps from the end with all three of the source's components
    still wrong cannot get there.
    """
    remaining = reached.dimension - source.dimension + spare
    position = {variable: index for index, variable in enumerate(reached.variables)}
    differing = sum(
        1
        for variable, component in zip(source.variables, source.components, strict=True)
        if sp.expand(reached.components[position[variable]] - component) != 0
    )

    return differing > remaining


def _stranded(source: PolynomialMap, reached: PolynomialMap) -> bool:
    """Return whether one coordinate too many is left for the source to take.

    A last step that introduces one coordinate has a ``Carried`` slot, and that
    slot is not the component the step acts on, so its component is the same
    before and after -- which makes it a carrier of the source as well. A
    source without carriers therefore cannot be reached by a step that
    introduces one coordinate, and a peel standing at one coordinate more than
    the source has nowhere left to go.

    Alpoege's map has no carriers, so this prunes every branch that spends its
    last removal on a single coordinate. It is a statement about the source
    that was handed in, not a rule about Keller maps.
    """
    return reached.dimension == source.dimension + 1 and not source.carrier_indices


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
    as SEA-5 requires -- as plain equality since work package 10, because the
    constant each step was undone with goes into the step itself.
    """
    maps = [target]
    for step in path:
        reached = undo(maps[-1], step)
        # Nicht erreichbar: der Weg wurde eben durch dieselben Zuege gefunden.
        if reached is None:  # pragma: no cover - the path came from undoing
            return None
        maps.append(reached)

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
    # geprueft, und die erste davon ist das Ziel.
    if current.reordered(target.variables) != target:  # pragma: no cover - per step
        return None

    return PeelOutcome(Reduction(tuple(steps)), examined, deepest, False)


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

    # Der Schritt wird hier vermutet und nicht behauptet. Schlaegt der Bau oder
    # die Pruefung fehl, so war die Vermutung falsch und der Kandidat faellt
    # weg -- eine erfolglose Suche darf keinen Zertifikatsfehler nach aussen
    # geben. Das Beispiel eines externen Audits: ein Faktor vom Grad null macht
    # ``H`` zu einem Element von ``EA^-1``, und BCW-6 lehnt das zu Recht ab.
    try:
        built = BCWStep.build(
            current,
            current.variables.index(step.target),
            factors[0],
            factors[1],
            level,
            step.factor,
        )
        built.verify()
    except (ValueError, VerificationError):
        return None

    # Nicht erreichbar, und als Selbstpruefung behalten: der Schritt stammt aus
    # dem Rueckrechnen von ``after`` und baut es daher wieder auf.
    if built.target.reordered(after.variables) != after:  # pragma: no cover - undone
        return None

    return built
