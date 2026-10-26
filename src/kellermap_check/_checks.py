"""The checks of CHK-4, one function per object of a file.

Each function receives what ``_reading`` read, checks the obligations of
``docs/contracts.md`` that can fail on a file, and raises ``Refusal`` citing
the first that fails. The order within an object is fixed and stands in the
docstring of each function. A check a caller left out is not made, and a later
check that needs what it would have established checks that for itself and
cites its own identifier.

Nothing here imports ``kellermap``. The formulas are the ones the contract
page states, written out again.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

import sympy as sp
from sympy.polys.matrices import DomainMatrix
from sympy.polys.rings import PolyElement, PolyRing

from . import _algebra as algebra
from ._reading import Collision, Map, Step
from ._report import Ledger, Refusal


class Context:
    """One object under check: its location, the ledger, and the refusal."""

    def __init__(self, ledger: Ledger, location: str) -> None:
        self.ledger = ledger
        self.location = location

    def wants(self, obligation: str) -> bool:
        return self.ledger.wants(self.location, obligation)

    def require(self, obligation: str, holds: bool, message: str) -> None:
        if not holds:
            raise Refusal(obligation, self.location, message)


def _reserved(source: Map) -> set[str]:
    """The names a fresh generator may not take: generators and parameters."""
    return set(source.names) | set(source.domain.parameters)


def _fresh(
    context: Context, obligation: str, source: Map, names: Sequence[str]
) -> None:
    """Fresh names are distinct and free of the source's names, RC-4."""
    context.require(
        obligation,
        len(set(names)) == len(names),
        f"the fresh variables {list(names)} are not distinct",
    )
    taken = set(names) & _reserved(source)
    context.require(
        obligation, not taken, f"the variables {sorted(taken)} are taken by the source"
    )


def _same_domain(context: Context, obligation: str, source: Map, target: Map) -> None:
    context.require(
        obligation,
        target.domain == source.domain,
        "the target is over another domain than the source",
    )


def _equal(
    context: Context,
    obligation: str,
    expected: Sequence[PolyElement],
    target: Map,
    what: str,
) -> None:
    """Compare a computed map with the target, component by component."""
    context.require(
        obligation,
        len(expected) == len(target.components),
        f"the target has {len(target.components)} components and {what} has "
        f"{len(expected)}",
    )
    for position, (left, right) in enumerate(
        zip(expected, target.components, strict=True)
    ):
        context.require(
            obligation,
            left == right,
            f"component {position} of the target is not {what}",
        )


def _determinant(
    context: Context, obligation: str, ring: PolyRing, components: Sequence[PolyElement]
) -> None:
    context.require(
        obligation,
        algebra.determinant_is_one(ring, components),
        "the Jacobian determinant is not one",
    )


def _is_field(source: Map) -> bool:
    return bool(source.domain.sympy.is_Field)


# --------------------------------------------------------------------------
# BCWStep
# --------------------------------------------------------------------------


def bcw(context: Context, step: Step, source: Map, target: Map) -> None:
    """BCW-4, BCW-6, BCW-10, BCW-11, BCW-2, BCW-12, BCW-1, in that order.

    BCW-6 and BCW-10 are taken in two parts each: the range of the level and
    the first two clauses of BCW-10 before everything else, and the attained
    level and the third clause of BCW-10 once the slots are known to name
    something.
    """
    fields = step.fields
    n = len(source.names)
    index = fields["index"]
    slots = (fields["left"], fields["right"])
    level = fields["filtration_level"]
    coefficient = fields["coefficient"]
    carried = [slot[1] for slot in slots if slot[0] == "carried"]
    in_range = 0 <= index < n and all(0 <= j < n and j != index for j in carried)

    if context.wants("BCW-4"):
        context.require("BCW-4", 0 <= index < n, f"index {index} is not a component")
    if context.wants("BCW-6"):
        context.require("BCW-6", level in (0, 1), f"the level {level} is not 0 or 1")
    if context.wants("BCW-10"):
        for j in carried:
            context.require("BCW-10", 0 <= j < n, f"a carried slot names {j}")
            context.require(
                "BCW-10", j != index, "a carried slot names the target component"
            )
    if context.wants("BCW-11"):
        context.require("BCW-11", bool(coefficient), "the coefficient is zero")

    fresh: list[str] = []
    for slot in slots:
        if slot[0] == "fresh" and slot[1] not in fresh:
            fresh.append(slot[1])
    names_hold = target.names == source.names + tuple(fresh)
    if context.wants("BCW-2"):
        context.require(
            "BCW-2",
            not set(fresh) & _reserved(source),
            "a fresh variable is taken by the source",
        )
        context.require(
            "BCW-2",
            names_hold,
            "the generators of the target are not the source's followed by the "
            "fresh variables",
        )

    values: dict[str, PolyElement] = {}
    for slot in slots:
        if slot[0] == "fresh":
            if slot[1] in values and context.wants("BCW-12"):
                context.require(
                    "BCW-12",
                    values[slot[1]] == slot[2],
                    f"two fresh slots name {slot[1]} with two values",
                )
            values.setdefault(slot[1], slot[2])

    displaced = algebra.displacement(source.ring, source.components)
    if context.wants("BCW-10"):
        for j in carried:
            if 0 <= j < n:
                context.require(
                    "BCW-10",
                    algebra.free_of(displaced[j], j),
                    f"component {j} of the source is not x{j} plus a term free of it",
                )
    if context.wants("BCW-6") and level in (0, 1):
        for name, value in values.items():
            context.require(
                "BCW-6",
                algebra.order(value) >= level + 1,
                f"the factor of {name} has order below {level + 1}, "
                f"so H is not in EA^{level}",
            )

    if not context.wants("BCW-1"):
        return
    context.require("BCW-1", in_range and names_hold, "the identity cannot be formed")
    _same_domain(context, "BCW-1", source, target)
    ring = target.ring
    lifted = [component.set_ring(ring) for component in source.components]
    generators = dict(zip(target.names, ring.gens, strict=True))

    def factor(slot: tuple[str, Any, Any]) -> PolyElement:
        if slot[0] == "carried":
            return lifted[slot[1]]
        return generators[slot[1]] + values[slot[1]].set_ring(ring)

    scale = ring.ground_new(coefficient)
    expected = list(lifted)
    expected[index] = lifted[index] - scale * factor(slots[0]) * factor(slots[1])
    expected += [generators[name] + values[name].set_ring(ring) for name in fresh]
    _equal(context, "BCW-1", expected, target, "G o F^[m] o H")


# --------------------------------------------------------------------------
# LinearStep and TranslationStep
# --------------------------------------------------------------------------


def _factor_matrix(factor: tuple[Any, ...], n: int, domain: Any) -> list[list[Any]]:
    matrix = [
        [domain.one if i == j else domain.zero for j in range(n)] for i in range(n)
    ]
    if factor[0] == "transvection":
        matrix[factor[1]][factor[2]] = factor[3]
    elif factor[0] == "transposition":
        first, second = factor[1], factor[2]
        matrix[first][first] = matrix[second][second] = domain.zero
        matrix[first][second] = matrix[second][first] = domain.one
    else:
        matrix[factor[1]][factor[1]] = factor[2]

    return matrix


def linear(context: Context, step: Step, source: Map, target: Map) -> None:
    """LIN-2, LIN-6 where the step normalizes, LIN-1, in that order.

    Of LIN-6 the clauses that can fail on a file are checked: the source fixes
    the origin, the determinant of its linear part is a unit, and the product
    of the transformation with that part is the identity. The ``MA^1`` clause
    follows and is the library's.
    """
    n = len(source.names)
    domain = source.domain.sympy
    factors = step.fields["transformation"]

    def valid(factor: tuple[Any, ...]) -> bool:
        indices = factor[1:3] if factor[0] != "dilation" else factor[1:2]
        if not all(0 <= index < n for index in indices):
            return False
        if factor[0] in ("transvection", "transposition"):
            return bool(factor[1] != factor[2])
        return algebra.is_unit(domain, factor[2])

    if context.wants("LIN-2"):
        for position, factor in enumerate(factors):
            context.require(
                "LIN-2", valid(factor), f"factor {position} is not a generator of GL_n"
            )

    if step.fields["normalizing"] and context.wants("LIN-6"):
        constants = [component.coeff(1) for component in source.components]
        context.require(
            "LIN-6", not any(constants), "the source does not fix the origin"
        )
        context.require(
            "LIN-6",
            all(valid(factor) for factor in factors),
            "the factors are not valid",
        )
        ring = source.ring
        linear_part = [
            [component.coeff(generator) for generator in ring.gens]
            for component in source.components
        ]
        part = DomainMatrix(linear_part, (n, n), domain)
        context.require(
            "LIN-6",
            algebra.is_unit(domain, part.det()),
            "the determinant of the linear part is not a unit of the domain",
        )
        product = DomainMatrix.eye(n, domain)
        for factor in factors:
            product = product * DomainMatrix(
                _factor_matrix(factor, n, domain), (n, n), domain
            )
        identity = (product * part).to_list()
        context.require(
            "LIN-6",
            all(
                identity[i][j] == (domain.one if i == j else domain.zero)
                for i in range(n)
                for j in range(n)
            ),
            "the transformation is not the inverse of the linear part",
        )

    if not context.wants("LIN-1"):
        return
    context.require(
        "LIN-1", target.names == source.names, "the target has other generators"
    )
    _same_domain(context, "LIN-1", source, target)
    context.require(
        "LIN-1", all(valid(factor) for factor in factors), "a factor is not valid"
    )
    components = list(source.components)
    for factor in reversed(factors):
        if factor[0] == "transvection":
            components[factor[1]] = (
                components[factor[1]] + components[factor[2]] * factor[3]
            )
        elif factor[0] == "transposition":
            components[factor[1]], components[factor[2]] = (
                components[factor[2]],
                components[factor[1]],
            )
        else:
            components[factor[1]] = components[factor[1]] * factor[2]
    _equal(
        context,
        "LIN-1",
        [c.set_ring(target.ring) for c in components],
        target,
        "the transformation of the source",
    )


def translation(context: Context, step: Step, source: Map, target: Map) -> None:
    """The length of the shift for TRA-1, TRA-6 where the step normalizes, TRA-1.

    The length comes first because the library refuses it in the constructor
    and cites TRA-1 there.
    """
    shift = step.fields["shift"]
    n = len(source.names)
    if context.wants("TRA-1"):
        context.require(
            "TRA-1", len(shift) == n, f"the shift has {len(shift)} entries for {n}"
        )

    if step.fields["normalizing"] and context.wants("TRA-6"):
        context.require("TRA-6", len(shift) == n, "the shift has the wrong length")
        for position, (value, component) in enumerate(
            zip(shift, source.components, strict=True)
        ):
            context.require(
                "TRA-6",
                value == component.coeff(1),
                f"entry {position} of the shift is not the source at the origin",
            )

    if not context.wants("TRA-1"):
        return
    context.require(
        "TRA-1", target.names == source.names, "the target has other generators"
    )
    _same_domain(context, "TRA-1", source, target)
    ring = target.ring
    expected = [
        component.set_ring(ring) - ring.ground_new(value)
        for component, value in zip(source.components, shift, strict=True)
    ]
    _equal(context, "TRA-1", expected, target, "the source less the shift")


# --------------------------------------------------------------------------
# The steps of Section 4
# --------------------------------------------------------------------------


def _degree(source: Map) -> float:
    return max(algebra.degree(component) for component in source.components)


def unipotent(context: Context, step: Step, source: Map, target: Map) -> None:
    """UNI-5, UNI-2, UNI-3, UNI-4, UNI-1, in that order."""
    names = step.fields["variables"]
    n = len(source.names)
    shape = len(names) == n and target.names == source.names + tuple(names)
    if context.wants("UNI-5"):
        context.require(
            "UNI-5", len(names) == n, f"{len(names)} fresh variables for {n} components"
        )
        _fresh(context, "UNI-5", source, names)
        context.require(
            "UNI-5", shape, "the generators of the target are not the source's and Y"
        )

    displaced = algebra.displacement(source.ring, source.components)
    if context.wants("UNI-2"):
        context.require(
            "UNI-2",
            min(algebra.order(value) for value in displaced) >= 2,
            "the source is not in MA^1",
        )
    if context.wants("UNI-3"):
        context.require(
            "UNI-3", _degree(source) <= 3, "the source has degree above three"
        )
    if context.wants("UNI-4"):
        _determinant(context, "UNI-4", source.ring, source.components)

    if not context.wants("UNI-1"):
        return
    context.require("UNI-1", shape, "the identity cannot be formed")
    _same_domain(context, "UNI-1", source, target)
    ring = target.ring
    gens = ring.gens
    cubic = [algebra.part(value, 3).set_ring(ring) for value in displaced]
    expected = [
        component.set_ring(ring) + gens[n + i] - cubic[i]
        for i, component in enumerate(source.components)
    ] + [gens[n + i] - cubic[i] for i in range(n)]
    _equal(context, "UNI-1", expected, target, "G o F^[n] o H")


def homogenization(context: Context, step: Step, source: Map, target: Map) -> None:
    """HOM-4, HOM-2, HOM-3, HOM-1, in that order."""
    name = step.fields["variable"]
    shape = target.names == source.names + (name,)
    if context.wants("HOM-4"):
        _fresh(context, "HOM-4", source, [name])
        context.require(
            "HOM-4", shape, "the generators of the target are not the source's and T"
        )
    if context.wants("HOM-2"):
        context.require(
            "HOM-2", _degree(source) <= 3, "the source has degree above three"
        )

    displaced = algebra.displacement(source.ring, source.components)
    widened = PolyRing(
        [*source.ring.symbols, sp.Symbol(name)], source.ring.domain, source.order
    )
    scale = widened.gens[-1]
    if context.wants("HOM-3"):
        _determinant(
            context,
            "HOM-3",
            widened,
            [
                generator + scale * value.set_ring(widened)
                for generator, value in zip(widened.gens, displaced, strict=False)
            ]
            + [scale],
        )

    if not context.wants("HOM-1"):
        return
    context.require("HOM-1", shape, "the identity cannot be formed")
    _same_domain(context, "HOM-1", source, target)
    ring = target.ring
    parameter = ring.gens[-1]
    expected = [
        ring.gens[i]
        + algebra.part(value, 1).set_ring(ring) * parameter**2
        + algebra.part(value, 2).set_ring(ring) * parameter
        + algebra.part(value, 3).set_ring(ring)
        for i, value in enumerate(displaced)
    ] + [parameter]
    _equal(context, "HOM-1", expected, target, "the homogenization of the source")


# --------------------------------------------------------------------------
# The compression and the lift
# --------------------------------------------------------------------------


def compression(context: Context, step: Step, source: Map, target: Map) -> None:
    """CHC-2, CHC-5, CHC-3, CHC-4, CHC-1, in that order."""
    basis = step.fields["basis"]
    names = step.fields["variables"]
    n, m = len(source.names), len(basis)
    domain = source.domain.sympy
    rows_hold = bool(basis) and all(len(row) == n for row in basis)

    if context.wants("CHC-2"):
        context.require("CHC-2", _is_field(source), "the domain is not a field")
        context.require(
            "CHC-2", rows_hold, "the basis is empty or a vector has the wrong length"
        )
        rank = DomainMatrix(basis, (m, n), domain).rank()
        context.require("CHC-2", rank == m, "the basis vectors are linearly dependent")
    shape = rows_hold and target.names == tuple(names) and len(names) == m
    if context.wants("CHC-5"):
        context.require("CHC-5", m <= n, f"{m} vectors in a space of dimension {n}")
        _fresh(context, "CHC-5", source, names)
        context.require(
            "CHC-5", shape, "the generators of the target are not one per vector"
        )

    displaced = algebra.displacement(source.ring, source.components)
    if context.wants("CHC-3"):
        d = algebra.homogeneous_degree(displaced)
        context.require(
            "CHC-3",
            d is not None and d >= 2,
            "the displacement is not homogeneous of degree two or more",
        )
    if context.wants("CHC-4"):
        _determinant(context, "CHC-4", source.ring, source.components)

    if not context.wants("CHC-1"):
        return
    context.require("CHC-1", shape, "the identity cannot be formed")
    _same_domain(context, "CHC-1", source, target)
    ring = target.ring
    images = [
        sum((ring.ground_new(basis[k][j]) * ring.gens[k] for k in range(m)), ring.zero)
        for j in range(n)
    ]
    reduced = algebra.displacement(ring, target.components)
    for i in range(n):
        left = sum(
            (ring.ground_new(basis[k][i]) * reduced[k] for k in range(m)), ring.zero
        )
        right = algebra.substitute(displaced[i], images, ring)
        context.require(
            "CHC-1", left == right, f"coordinate {i} of B^T hbar(c) is not h(B^T c)"
        )


def lift(context: Context, step: Step, source: Map, target: Map) -> None:
    """SYM-3, SYM-4, SYM-5, SYM-1, in that order."""
    names = step.fields["variables"]
    m = len(source.names)
    displaced = algebra.displacement(source.ring, source.components)
    if context.wants("SYM-3"):
        d = algebra.homogeneous_degree(displaced)
        context.require(
            "SYM-3",
            d is not None and d >= 2,
            "the displacement is not homogeneous of degree two or more",
        )
    if context.wants("SYM-4"):
        context.require("SYM-4", _is_field(source), "the domain is not a field")
        _determinant(context, "SYM-4", source.ring, source.components)

    domain = algebra.lifted_domain(source.domain.sympy)
    shape = len(names) == 2 * m and target.names == tuple(names)
    if context.wants("SYM-5"):
        context.require(
            "SYM-5", len(names) == 2 * m, f"{len(names)} variables for 2 * {m}"
        )
        _fresh(context, "SYM-5", source, names)
        context.require(
            "SYM-5", shape, "the generators of the target are not the variables"
        )
        context.require(
            "SYM-5",
            target.domain.sympy == domain,
            "the domain of the target is not the source's with i adjoined",
        )

    if not context.wants("SYM-1"):
        return
    context.require(
        "SYM-1",
        shape and target.domain.sympy == domain,
        "the identity cannot be formed",
    )
    ring = target.ring
    unit = ring.domain.from_sympy(sp.I)
    shifted = [ring.gens[j] + ring.gens[m + j] * unit for j in range(m)]
    form = ring.zero
    for j, value in enumerate(displaced):
        form += ring.gens[m + j] * algebra.substitute(value, shifted, ring)
    form = form * unit
    expected = [generator - form.diff(generator) for generator in ring.gens]
    _equal(context, "SYM-1", expected, target, "(X, Y) - grad(P)")


# --------------------------------------------------------------------------
# DescentStep
# --------------------------------------------------------------------------


def _apply(
    factors: Sequence[tuple[int, PolyElement]], components: list[PolyElement]
) -> list[PolyElement]:
    """Return ``f_1 o ... o f_r o components`` for elementary factors."""
    result = list(components)
    for index, value in reversed(factors):
        result[index] = result[index] + algebra.substitute(
            value, result, result[0].ring
        )

    return result


def descent(context: Context, step: Step, source: Map, target: Map) -> None:
    """DSC-1 for the index, DSC-2 for the dimension, DSC-4, DSC-3, DSC-2, DSC-1."""
    k = step.fields["index"]
    n = len(source.names)
    left, right = step.fields["left"], step.fields["right"]
    if context.wants("DSC-1"):
        context.require("DSC-1", 0 <= k < n, f"index {k} is not a coordinate")
    if context.wants("DSC-2"):
        context.require("DSC-2", n >= 2, "a descent from one variable leaves none")

    factors_hold = all(
        0 <= i < n and algebra.free_of(value, i) for i, value in left + right
    )
    if context.wants("DSC-4"):
        context.require(
            "DSC-4", factors_hold, "a factor is not elementary on the source's ring"
        )

    usable = 0 <= k < n and n >= 2 and factors_hold
    ring = source.ring
    conjugate: list[PolyElement] = []
    if usable:
        moved = _apply(right, list(ring.gens))
        composed = [
            algebra.substitute(component, moved, ring)
            for component in source.components
        ]
        conjugate = _apply(left, composed)

    if context.wants("DSC-3"):
        context.require("DSC-3", usable, "the conjugate cannot be formed")
        context.require(
            "DSC-3",
            algebra.free_of(conjugate[k] - ring.gens[k], k),
            f"the tail of component {k} mentions the coordinate",
        )
        for j, component in enumerate(conjugate):
            if j != k:
                context.require(
                    "DSC-3",
                    algebra.free_of(component, k),
                    f"component {j} mentions the coordinate",
                )

    kept = source.names[:k] + source.names[k + 1 :]
    shape = target.names == kept
    if context.wants("DSC-2"):
        context.require(
            "DSC-2",
            shape,
            "the generators of the target are not the source's without one",
        )
        _same_domain(context, "DSC-2", source, target)
        context.require(
            "DSC-2", target.order == source.order, "the monomial order differs"
        )

    if not context.wants("DSC-1"):
        return
    context.require("DSC-1", usable and shape, "the deletion cannot be formed")
    _same_domain(context, "DSC-1", source, target)
    expected = []
    for j, component in enumerate(conjugate):
        if j != k:
            context.require(
                "DSC-1",
                algebra.free_of(component, k),
                f"component {j} mentions the coordinate",
            )
            expected.append(component.set_ring(target.ring))
    _equal(context, "DSC-1", expected, target, "the conjugate without component k")


STEPS: dict[str, Callable[[Context, Step, Map, Map], None]] = {
    "BCWStep": bcw,
    "LinearStep": linear,
    "TranslationStep": translation,
    "UnipotentStep": unipotent,
    "HomogenizationStep": homogenization,
    "CompressionStep": compression,
    "SymmetricLiftStep": lift,
    "DescentStep": descent,
}


# --------------------------------------------------------------------------
# Collisions and the witness
# --------------------------------------------------------------------------


def collision(context: Context, entry: Collision, polynomial_map: Map) -> None:
    """COL-1, COL-4, COL-3, in that order.

    COL-2 is FMT-7 and COL-7 follows from FMT-5, so both were refused while the
    file was read.
    """
    n = len(polynomial_map.names)
    lengths = all(len(point) == n for point in entry.points) and len(entry.image) == n
    if context.wants("COL-1"):
        context.require(
            "COL-1", lengths and n > 0, "a point or the image has the wrong length"
        )
    if context.wants("COL-4"):
        context.require("COL-4", len(entry.points) >= 2, "a collision needs two points")
        for first in range(len(entry.points)):
            for second in range(first + 1, len(entry.points)):
                context.require(
                    "COL-4",
                    entry.points[first] != entry.points[second],
                    f"points {first} and {second} are equal",
                )
    if context.wants("COL-3"):
        context.require("COL-3", lengths, "the points cannot be evaluated")
        domain = entry.domain.sympy
        for position, point in enumerate(entry.points):
            value = tuple(
                algebra.evaluate(component, point, domain)
                for component in polynomial_map.components
            )
            context.require(
                "COL-3",
                value == entry.image,
                f"point {position} is not sent to the image",
            )


def witness(
    context: Context, source: Map, target: Map, depth: int, collision_checked: bool
) -> None:
    """VAN-1, VAN-2, and the range of the depth in VAN-3."""
    if context.wants("VAN-1"):
        displaced = algebra.displacement(source.ring, source.components)
        context.require(
            "VAN-1",
            max(algebra.degree(value) for value in displaced) == 3,
            "the source of the lift is not cubic",
        )
    if context.wants("VAN-2"):
        context.require(
            "VAN-2",
            collision_checked,
            "the collision of the witness was not checked against the lift's target",
        )
    if context.wants("VAN-3"):
        context.require(
            "VAN-3",
            1 <= depth <= len(target.names),
            f"the depth {depth} is not between one and {len(target.names)}",
        )
