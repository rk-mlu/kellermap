"""Polynomial arithmetic the checks need, written without ``kellermap``.

SymPy supplies the rings and the domains. Everything above them is here: the
homogeneous parts, the order and the degree, substitution, and the test
whether a Jacobian determinant is one.

The determinant follows the same mathematics as the library and is written
differently. A map that a reduction produces has many coordinates whose
diagonal entry in the Jacobian is one. Those coordinates span a block ``D`` of
the form ``I + L``, and where their dependencies have no cycle ``L`` is
nilpotent and ``det D`` is one. Then ``det J = det(A - B D^-1 C)``, the
determinant of the Schur complement. The library drops each cycle it finds
and inverts ``D`` by a Neumann series. This module breaks each cycle at the
coordinate with the most dependencies inside it, solves ``D X = C`` by
substitution in an order of the dependencies, and leaves the small complement
to the fraction-free elimination of SymPy. Every domain a file can hold is an
integral domain, so that elimination is exact.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any

import sympy as sp
from sympy.polys.matrices import DomainMatrix
from sympy.polys.rings import PolyElement, PolyRing


def order(polynomial: PolyElement) -> float:
    """Return the least total degree of a term, or infinity for zero."""
    return min(
        (sum(monomial) for monomial in polynomial.itermonoms()), default=math.inf
    )


def degree(polynomial: PolyElement) -> float:
    """Return the largest total degree of a term, or minus infinity for zero."""
    return max(
        (sum(monomial) for monomial in polynomial.itermonoms()), default=-math.inf
    )


def part(polynomial: PolyElement, wanted: int) -> PolyElement:
    """Return the homogeneous part of total degree ``wanted``."""
    ring = polynomial.ring

    return ring.from_dict(
        {
            monomial: coefficient
            for monomial, coefficient in polynomial.iterterms()
            if sum(monomial) == wanted
        }
    )


def free_of(polynomial: PolyElement, index: int) -> bool:
    """Return whether no term of ``polynomial`` involves generator ``index``."""
    return not any(monomial[index] for monomial in polynomial.itermonoms())


def displacement(
    ring: PolyRing, components: Sequence[PolyElement]
) -> list[PolyElement]:
    """Return ``F - X``."""
    return [
        component - generator
        for component, generator in zip(components, ring.gens, strict=True)
    ]


def homogeneous_degree(polynomials: Sequence[PolyElement]) -> int | None:
    """Return ``d`` if every non-zero polynomial is homogeneous of degree ``d``.

    ``None`` when there is no such ``d``: the degrees differ, a polynomial has
    two degrees, or every polynomial is zero.
    """
    degrees: set[int] = set()
    for polynomial in polynomials:
        degrees |= {sum(monomial) for monomial in polynomial.itermonoms()}

    return degrees.pop() if len(degrees) == 1 else None


def element_into(value: Any, source: Any, target: Any) -> Any:
    """Return an element of ``source`` as one of ``target``, through SymPy.

    Through the expression and not through ``convert``, because the inclusions
    of FMT-8 include a quadratic field, whose elements SymPy keeps in a
    representation that ``convert`` does not always reach.
    """
    if source == target:
        return value

    return target.from_sympy(source.to_sympy(value))


def substitute(
    polynomial: PolyElement, images: Sequence[PolyElement], ring: PolyRing
) -> PolyElement:
    """Return ``polynomial`` with generator ``j`` replaced by ``images[j]``.

    The images lie in ``ring``, whose domain contains the domain of the
    polynomial. Every coefficient is carried into it.
    """
    source = polynomial.ring.domain
    total = ring.zero
    powers: dict[tuple[int, int], PolyElement] = {}
    for monomial, coefficient in polynomial.iterterms():
        term = ring.ground_new(element_into(coefficient, source, ring.domain))
        for index, exponent in enumerate(monomial):
            if exponent:
                key = (index, exponent)
                if key not in powers:
                    powers[key] = images[index] ** exponent
                term = term * powers[key]
        total += term

    return total


def evaluate(polynomial: PolyElement, point: Sequence[Any], domain: Any) -> Any:
    """Return the value of ``polynomial`` at a point of ``domain``."""
    source = polynomial.ring.domain
    total = domain.zero
    for monomial, coefficient in polynomial.iterterms():
        term = element_into(coefficient, source, domain)
        for value, exponent in zip(point, monomial, strict=True):
            if exponent:
                term = term * value**exponent
        total = total + term

    return total


def is_unit(domain: Any, value: Any) -> bool:
    """Return whether ``value`` has an inverse in ``domain``."""
    if not value:
        return False
    try:
        domain.exquo(domain.one, value)
    except Exception:  # noqa: BLE001 - every refusal of SymPy means no inverse
        return False

    return True


# --------------------------------------------------------------------------
# The determinant
# --------------------------------------------------------------------------


def _components(nodes: list[int], edges: dict[int, set[int]]) -> list[list[int]]:
    """Return the strongly connected components, by Tarjan's method, iteratively."""
    index: dict[int, int] = {}
    low: dict[int, int] = {}
    stack: list[int] = []
    on_stack: set[int] = set()
    found: list[list[int]] = []
    counter = 0

    for root in nodes:
        if root in index:
            continue
        index[root] = low[root] = counter
        counter += 1
        stack.append(root)
        on_stack.add(root)
        work = [(root, iter(sorted(edges[root])))]
        while work:
            node, successors = work[-1]
            descended = False
            for successor in successors:
                if successor not in index:
                    index[successor] = low[successor] = counter
                    counter += 1
                    stack.append(successor)
                    on_stack.add(successor)
                    work.append((successor, iter(sorted(edges[successor]))))
                    descended = True
                    break
                if successor in on_stack:
                    low[node] = min(low[node], index[successor])
            if descended:
                continue
            work.pop()
            if work:
                parent = work[-1][0]
                low[parent] = min(low[parent], low[node])
            if low[node] == index[node]:
                component = []
                while True:
                    member = stack.pop()
                    on_stack.discard(member)
                    component.append(member)
                    if member == node:
                        break
                found.append(component)

    return found


def _block(
    jacobian: list[list[PolyElement]], one: PolyElement
) -> tuple[set[int], dict[int, set[int]]]:
    """Return coordinates that span a unipotent block, and their dependencies.

    A coordinate qualifies when its diagonal entry is one. While the
    dependencies among the qualifying coordinates have a cycle, the coordinate
    with the most edges inside each cyclic component, in or out, is dropped, the
    smallest index on a tie. What is left has no cycle, so its block is ``I``
    plus a nilpotent matrix.
    """
    kept = {index for index, row in enumerate(jacobian) if row[index] == one}
    while True:
        edges = {i: {j for j in kept if j != i and jacobian[i][j]} for i in kept}
        cyclic = [c for c in _components(sorted(kept), edges) if len(c) > 1]
        if not cyclic:
            return kept, edges
        for component in cyclic:
            inside = set(component)

            def weight(
                node: int, inside: set[int] = inside, edges: dict[int, set[int]] = edges
            ) -> int:
                inward = sum(1 for other in inside if node in edges[other])
                return len(edges[node] & inside) + inward

            kept.discard(max(sorted(component), key=weight))


def determinant_is_one(ring: PolyRing, components: Sequence[PolyElement]) -> bool:
    """Return whether the Jacobian determinant of the map is one."""
    size = len(components)
    jacobian = [
        [component.diff(generator) for generator in ring.gens]
        for component in components
    ]
    kept, edges = _block(jacobian, ring.one)

    solved: dict[int, list[PolyElement]] = {}
    head = [index for index in range(size) if index not in kept]
    done: set[int] = set()

    def solve(node: int) -> None:
        # D X = C, row by row: X_i = C_i - sum over dependencies j of L_ij X_j.
        # The dependencies are solved first; without a cycle this ends.
        pending = [node]
        while pending:
            current = pending[-1]
            waiting = [j for j in sorted(edges[current]) if j not in done]
            if waiting:
                pending.extend(waiting)
                continue
            pending.pop()
            if current in done:
                continue
            row = [jacobian[current][column] for column in head]
            for j in edges[current]:
                factor = jacobian[current][j]
                row = [
                    entry - factor * other
                    for entry, other in zip(row, solved[j], strict=True)
                ]
            solved[current] = row
            done.add(current)

    for node in sorted(kept):
        solve(node)

    if not head:
        return True

    complement = [
        [
            jacobian[row][column]
            - sum((jacobian[row][j] * solved[j][position] for j in kept), ring.zero)
            for position, column in enumerate(head)
        ]
        for row in head
    ]
    value = DomainMatrix(complement, (len(head), len(head)), ring.to_domain()).det()

    return bool(value == ring.one)


def lifted_domain(domain: Any) -> Any:
    """Return ``domain`` with ``i`` adjoined, as SYM-5 describes the target's."""
    return domain.unify(sp.ZZ_I)
