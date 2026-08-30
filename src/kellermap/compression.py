"""Collision-hull compression, Theorem 3 of arXiv:2608.12543v1.

For ``F = id + h`` with ``h`` homogeneous of degree ``d`` and a collision
``F(p) = F(q)``, the subspace

    W_0     = span of the points
    W_(v+1) = W_v + span{ T(w_1, ..., w_d) : w_j in W_v }

with ``T`` the symmetric polarization of ``h`` is invariant under ``h``, and the
restriction of ``F`` to it is again a Keller map with the collision. It is the
smallest invariant subspace containing the points, so the compression is not a
fortunate choice of coordinates: it is what the collision itself generates.

This is the first step in this library that lowers the dimension, and the first
whose target shares no generator with its source. ``docs/contracts.md`` states
what else is new about it under CHC-1 to CHC-10; the three that matter for
reading this file are that ``build`` needs a collision as well as a source,
that ``transport`` may refuse a collision whose points leave the subspace, and
that the certificate is the basis.

It lives at the top level and not in ``kellermap.bcw``. That subpackage holds
one paper, and this is a different one.

See ``docs/contracts.md``, CHC-1 to CHC-10.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from itertools import combinations, combinations_with_replacement
from typing import Any

import sympy as sp
from sympy.polys.domains import Domain
from sympy.polys.rings import PolyElement, PolyRing

from .canonical import agree
from .collision import Collision
from .context import ReductionContext
from .errors import VerificationError
from .polynomial_map import PolynomialMap
from .reduction import Provenance
from .variables import VariableFactory, reserved_names

Vector = tuple[sp.Expr, ...]
Basis = tuple[Vector, ...]

Element = Any
"""An element of the coefficient domain.

``sympy`` gives no type for one: ``QQ`` yields ``PythonMPQ`` or ``MPQ``
depending on what is installed, and a number field yields ``ANP``. What every
domain does promise is the arithmetic used here, so the alias says ``Any`` and
the name says which ``Any`` it is.
"""

Table = tuple[tuple[tuple[int, ...], Element], ...]


# --------------------------------------------------------------------------
# Linear algebra over the coefficient domain
#
# Small and hand-written, because what is needed is one operation: offer a
# vector to a growing independent set and learn whether it was new. A general
# rank computation would redo the elimination for every offer, and the hull
# offers thousands.
# --------------------------------------------------------------------------


class _Echelon:
    """An independent set of vectors, kept in reduced row echelon form.

    Reduced and not merely triangular, because the rows are what a step then
    carries as its basis. An unreduced basis spans the same subspace and makes
    a much denser restriction: on Thompson's map, 21988 monomials against 1370.
    """

    def __init__(self, domain: Domain) -> None:
        self._domain = domain
        self._pivots: list[int] = []
        self._rows: list[list[Element]] = []

    def __len__(self) -> int:
        return len(self._rows)

    @property
    def rows(self) -> tuple[tuple[Element, ...], ...]:
        """Return the reduced basis, one row per pivot."""
        return tuple(tuple(row) for row in self._rows)

    def offer(self, vector: tuple[Element, ...]) -> bool:
        """Add ``vector`` if it is independent of what is here, and say so."""
        reduced = self.reduce(vector)
        position = next(
            (
                index
                for index, value in enumerate(reduced)
                if value != self._domain.zero
            ),
            None,
        )
        if position is None:
            return False

        leading = reduced[position]
        row = [value / leading for value in reduced]

        for index, other in enumerate(self._rows):
            if other[position] != self._domain.zero:
                factor = other[position]
                self._rows[index] = [
                    value - factor * new for value, new in zip(other, row, strict=True)
                ]

        insert = len([pivot for pivot in self._pivots if pivot < position])
        self._pivots.insert(insert, position)
        self._rows.insert(insert, row)

        return True

    def reduce(self, vector: tuple[Element, ...]) -> list[Element]:
        """Return ``vector`` with every pivot eliminated from it."""
        working = list(vector)
        for position, row in zip(self._pivots, self._rows, strict=True):
            if working[position] != self._domain.zero:
                factor = working[position]
                working = [
                    value - factor * other
                    for value, other in zip(working, row, strict=True)
                ]

        return working

    def spans(self, vector: tuple[Element, ...]) -> bool:
        """Return whether ``vector`` lies in the span of what is here."""
        return all(value == self._domain.zero for value in self.reduce(vector))


def _to_domain(vector: Vector, domain: Domain) -> tuple[Element, ...]:
    """Return the coordinates of ``vector`` as elements of ``domain``."""
    return tuple(domain.from_sympy(sp.sympify(value)) for value in vector)


def _degree(source: PolynomialMap) -> int:
    """Return the degree of a homogeneous displacement, or raise CHC-3.

    The polarization is the reason. A form of one degree has a symmetric
    ``d``-linear polarization and a sum of forms of several degrees does not,
    so a source that fails this has nothing to iterate.
    """
    degrees = {
        sum(monomial)
        for component in source.displacement().to_polynomials()
        if component
        for monomial in component.itermonoms()
    }

    if len(degrees) != 1:
        raise VerificationError(
            "CHC-3",
            f"The displacement of the source has the degrees {sorted(degrees)} "
            "and is not homogeneous, so it has no symmetric polarization. The "
            "homogenization is what produces a source that is.",
        )

    degree = int(degrees.pop())
    if degree < 2:
        raise VerificationError(
            "CHC-3",
            f"The displacement of the source is homogeneous of degree {degree}, "
            "below two. A Keller map with a linear displacement is injective, "
            "so it has no collision to compress.",
        )

    return degree


def _terms(
    displacement: tuple[PolyElement, ...],
) -> tuple[Table, ...]:
    """Return the displacement as term tables, one per component.

    ``PolyElement.evaluate`` on a list of generators substitutes one at a time
    and builds a polynomial at every step. The hull evaluates the displacement
    tens of thousands of times, so it reads the terms once and multiplies in
    the domain afterwards. Measured on Thompson's map: the hull does not finish
    in ten minutes through ``evaluate`` and takes under a second this way.
    """
    return tuple(tuple(component.terms()) for component in displacement)


def _evaluate(
    tables: tuple[Table, ...],
    point: tuple[Element, ...],
    domain: Domain,
) -> list[Element]:
    """Return the displacement at ``point``, in the domain."""
    values = []
    for table in tables:
        total = domain.zero
        for monomial, coefficient in table:
            term = coefficient
            for position, exponent in enumerate(monomial):
                for _ in range(exponent):
                    term = term * point[position]
            total = total + term
        values.append(total)

    return values


def _polarize(
    tables: tuple[Table, ...],
    vectors: tuple[tuple[Element, ...], ...],
    domain: Domain,
    factorial: Element,
) -> tuple[Element, ...]:
    """Return ``T(w_1, ..., w_d)``, the symmetric polarization at the vectors.

    By inclusion and exclusion,

        d! T(w_1, ..., w_d) = sum over non-empty S of
                              (-1)^(d - |S|) h( sum of w_j for j in S )

    Division by ``d!`` needs characteristic zero, which DOM-1 fixes for this
    library.
    """
    degree = len(vectors)
    dimension = len(vectors[0])
    total = [domain.zero] * dimension

    for size in range(1, degree + 1):
        negated = (degree - size) % 2 == 1
        for chosen in combinations(range(degree), size):
            point = [domain.zero] * dimension
            for index in chosen:
                summand = vectors[index]
                for position in range(dimension):
                    point[position] = point[position] + summand[position]

            values = _evaluate(tables, tuple(point), domain)
            for position, value in enumerate(values):
                total[position] = (
                    total[position] - value if negated else total[position] + value
                )

    return tuple(value / factorial for value in total)


def collision_hull(
    source: PolynomialMap, collision: Collision
) -> tuple[Basis, tuple[int, ...]]:
    """Return a basis of the collision hull and the dimensions that reached it.

    CHC-8. The hull is the smallest subspace that contains the points of the
    collision and is invariant under the displacement. The iteration takes its
    arguments from a basis of the current subspace rather than from all of it,
    which spans the same thing because the polarization is ``d``-linear.

    The sequence of dimensions is returned beside the basis and is not stored
    anywhere. It is what a control compares against: on Thompson's map it has
    to be ``2, 4, 11, 20, 20``.
    """
    collision.verify(source)

    ring = source.ring
    domain = ring.domain
    degree = _degree(source)
    displacement = source.displacement().to_polynomials()

    tables = _terms(displacement)
    factorial = domain.from_sympy(sp.Integer(sp.factorial(degree)))

    echelon = _Echelon(domain)
    for point in collision.points:
        echelon.offer(_to_domain(point, domain))

    dimensions = [len(echelon)]
    while True:
        rows = echelon.rows
        for indices in combinations_with_replacement(range(len(rows)), degree):
            echelon.offer(
                _polarize(
                    tables, tuple(rows[index] for index in indices), domain, factorial
                )
            )

        dimensions.append(len(echelon))
        if dimensions[-1] == dimensions[-2]:
            break

    basis = tuple(
        tuple(domain.to_sympy(value) for value in row) for row in echelon.rows
    )

    return basis, tuple(dimensions)


@dataclass(frozen=True, eq=False)
class CompressionStep:
    """The restriction of a homogeneous Keller map to an invariant subspace.

    Parameters
    ----------
    source, target
        The maps before and after. A ``target`` supplied here is what makes
        CHC-1 a real check.
    basis
        The rows of ``B``: ``m`` vectors of ``n`` coordinates, spanning the
        subspace. The certificate, and the only thing that has to be stored:
        the target is what the basis and the source determine.
    variables
        The ``m`` generators of the target. All of them are fresh, since the
        target shares no coordinate with the source.
    """

    _source: PolynomialMap
    _target: PolynomialMap
    _basis: Basis
    _variables: tuple[sp.Symbol, ...]
    _provenance: Provenance
    _verified: bool

    def __init__(
        self,
        source: PolynomialMap,
        target: PolynomialMap,
        basis: Basis,
        variables: tuple[sp.Symbol, ...],
    ) -> None:
        if not isinstance(source, PolynomialMap):
            raise TypeError("The source must be a PolynomialMap.")
        if not isinstance(target, PolynomialMap):
            raise TypeError("The target must be a PolynomialMap.")

        rows = tuple(tuple(sp.sympify(value) for value in row) for row in basis)
        names = tuple(variables)

        for variable in names:
            if not isinstance(variable, sp.Symbol):
                raise TypeError("Every variable of the target must be a SymPy symbol.")

        if len(rows) != len(names):
            raise ValueError(
                f"The basis has {len(rows)} vectors and the target "
                f"{len(names)} generators; there is one generator per vector."
            )

        if not rows:
            raise ValueError("The basis is empty and spans no subspace.")

        # CHC-2. A wrong length describes no subspace of the source's space,
        # and a dependent list describes one of a smaller dimension than it
        # claims. Both are constructor invariants: neither is a statement
        # about arithmetic that ``verify`` could locate.
        for row in rows:
            if len(row) != source.dimension:
                raise ValueError(
                    f"Every basis vector has {source.dimension} coordinates, "
                    f"one per variable of the source; got one with {len(row)}."
                )

        if len(rows) > source.dimension:
            raise ValueError(
                f"The basis has {len(rows)} vectors in a space of dimension "
                f"{source.dimension}."
            )

        domain = source.ring.domain
        echelon = _Echelon(domain)
        for row in rows:
            if not echelon.offer(_to_domain(row, domain)):
                raise ValueError(
                    "The basis vectors are linearly dependent, so they do not "
                    f"span a subspace of dimension {len(rows)}."
                )

        # Fresh against the reserved names and not only the coordinates, as
        # everywhere else. Here it covers every generator of the target: the
        # two rings have nothing in common, and a shared name would mean two
        # different things by one name in one chain.
        taken = {variable.name for variable in names} & reserved_names(source.ring)
        if taken:
            raise ValueError(
                f"The variables {sorted(taken)} are already in use by the source."
            )

        if len({variable.name for variable in names}) != len(names):
            raise ValueError("The variables of the target must be distinct.")

        object.__setattr__(self, "_source", source)
        object.__setattr__(self, "_target", target)
        object.__setattr__(self, "_basis", rows)
        object.__setattr__(self, "_variables", names)
        object.__setattr__(self, "_provenance", Provenance.SUPPLIED)
        object.__setattr__(self, "_verified", False)

    @classmethod
    def build(
        cls,
        source: PolynomialMap,
        collision: Collision,
        factory: VariableFactory | None = None,
    ) -> CompressionStep:
        """Compute the hull of ``collision`` and restrict to it.

        The only step type that needs a collision to be built. A different
        collision generates a different hull, so the transformation is not
        determined by the source alone.

        CHC-3 and CHC-4 are not weakened by this route: they constrain the
        source, and a step built from a source that fails them is built and
        fails to verify. CHC-3 is reached earlier, by ``collision_hull``, which
        cannot form a polarization without it.
        """
        basis, _ = collision_hull(source, collision)

        context = ReductionContext() if factory is None else ReductionContext(factory)
        variables = context.variables(source.ring, len(basis))

        draft = cls(source, source, basis, variables)
        step = cls(source, draft._restriction(), basis, variables)
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
    def basis(self) -> Basis:
        """Return the rows of ``B``, the certificate of this step."""
        return self._basis

    @property
    def variables(self) -> tuple[sp.Symbol, ...]:
        """Return the generators of the target."""
        return self._variables

    @property
    def provenance(self) -> Provenance:
        """Return whether the target was supplied or constructed."""
        return self._provenance

    @property
    def filtration_level(self) -> int | float:
        """Return ``math.inf``: the step makes no ``EA`` claim.

        CHC-7, and the same reason as ``HomogenizationStep``: this is not a
        composition with elementary automorphisms.
        """
        return math.inf

    @property
    def ring(self) -> PolyRing:
        """Return the arithmetic context of the target the basis determines."""
        return self._source.ring.clone(symbols=self._variables)

    def _forms(self) -> tuple[PolyElement, ...]:
        """Return ``B^T c``, the coordinates of a general point of the subspace."""
        ring = self.ring
        domain = ring.domain

        return tuple(
            sum(
                (
                    ring.term_new((0,) * len(self._variables), domain.zero)
                    + generator * domain.from_sympy(sp.sympify(row[position]))
                    for generator, row in zip(ring.gens, self._basis, strict=True)
                ),
                ring.zero,
            )
            for position in range(self._source.dimension)
        )

    def _substituted(self) -> tuple[PolyElement, ...]:
        """Return ``h(B^T c)``, in the target's ring."""
        ring = self.ring
        forms = self._forms()

        substituted = []
        for component in self._source.displacement().to_polynomials():
            total = ring.zero
            for monomial, coefficient in component.iterterms():
                term = ring.ground_new(coefficient)
                for position, exponent in enumerate(monomial):
                    for _ in range(exponent):
                        term = term * forms[position]
                total = total + term
            substituted.append(total)

        return tuple(substituted)

    def _pivot_rows(self) -> tuple[int, ...]:
        """Return ``m`` coordinates on which the basis is already invertible.

        Any such choice does. Solving on them and checking all ``n`` under
        CHC-1 is what makes the choice immaterial.
        """
        domain = self._source.ring.domain
        echelon = _Echelon(domain)
        chosen = []

        for position in range(self._source.dimension):
            column = tuple(
                domain.from_sympy(sp.sympify(row[position])) for row in self._basis
            )
            if echelon.offer(column):
                chosen.append(position)
            if len(chosen) == len(self._basis):
                break

        return tuple(chosen)

    def _restriction(self) -> PolynomialMap:
        """Return the map the basis and the source determine.

        ``B^T hbar = h(B^T c)`` is ``n`` equations in ``m`` unknowns. It is
        solved on ``m`` coordinates where the basis is invertible, and CHC-1
        then checks all ``n``, so an unlucky choice of coordinates cannot make
        a wrong target verify.
        """
        ring = self.ring
        substituted = self._substituted()
        rows = self._pivot_rows()

        matrix = sp.Matrix(
            [[row[position] for row in self._basis] for position in rows]
        ).inv()

        components = []
        for index in range(len(self._basis)):
            total = ring.zero
            for column, position in enumerate(rows):
                factor = ring.domain.from_sympy(sp.sympify(matrix[index, column]))
                total = total + substituted[position] * factor
            components.append(ring.gens[index] + total)

        return PolynomialMap.from_ring(ring, tuple(components))

    # ----------------------------------------------------------------------
    # Verification
    # ----------------------------------------------------------------------

    def verify(self) -> None:
        """Check CHC-1 to CHC-6, or raise ``VerificationError``.

        The source is checked first, as in the two steps of Section 4: a
        failure there is a statement about the caller's map rather than about
        this step's arithmetic.
        """
        if self._verified:
            return

        self._verify_source()
        self._verify_generators()
        self._verify_identity()
        self._verify_target()

        object.__setattr__(self, "_verified", True)

    def _verify_source(self) -> None:
        """CHC-3 and CHC-4.

        Nilpotence of ``J(h)`` needs no obligation of its own here, unlike
        HOM-3. Under CHC-3, ``J(h)(lambda x) = lambda^(d-1) J(h)(x)``, so a
        constant determinant is ``det(I + s J(h)) = 1`` for every ``s``; the
        characteristic polynomial is then ``lambda^n`` and Cayley-Hamilton
        finishes it. The homogenization's source is not homogeneous and cannot
        borrow that argument.
        """
        _degree(self._source)

        determinant = self._source.determinant()
        if not agree(determinant, sp.Integer(1)):
            raise VerificationError(
                "CHC-4",
                f"The source has Jacobian determinant {determinant}, not one, "
                "so it is not a Keller map and the restriction need not be "
                "one either.",
            )

    def _verify_generators(self) -> None:
        """CHC-5, the half that is not a constructor invariant."""
        if self._target.dimension != len(self._basis):
            raise VerificationError(
                "CHC-5",
                f"The basis has {len(self._basis)} vectors, so the target has "
                f"dimension {len(self._basis)}, not {self._target.dimension}.",
            )

        if self._target.variables != self._variables:
            raise VerificationError(
                "CHC-5",
                "The target does not carry the generators the step records.",
            )

    def _verify_identity(self) -> None:
        """CHC-1, in every one of the ``n`` components.

        Two faults land here. A target that is not the restriction, and a
        basis whose span is not invariant, which makes the identity
        unsatisfiable by any target at all.
        """
        ring = self.ring
        domain = ring.domain
        substituted = self._substituted()
        restricted = self._target.displacement().to_polynomials()

        for position in range(self._source.dimension):
            combined = ring.zero
            for component, row in zip(restricted, self._basis, strict=True):
                combined = combined + component * domain.from_sympy(
                    sp.sympify(row[position])
                )

            if combined != substituted[position]:
                raise VerificationError(
                    "CHC-1",
                    f"B^T hbar and h(B^T c) differ in coordinate {position} of "
                    "the source. Either the target is not the restriction, or "
                    "the span of the basis is not invariant under the "
                    "displacement, in which case no target would satisfy this.",
                )

    def _verify_target(self) -> None:
        """CHC-6, both halves. Implied by CHC-1 with CHC-3 and CHC-4."""
        degrees = {
            sum(monomial)
            for component in self._target.displacement().to_polynomials()
            if component
            for monomial in component.itermonoms()
        }
        wanted = {_degree(self._source)}

        if degrees and degrees != wanted:  # pragma: no cover - implied by CHC-1
            raise VerificationError(
                "CHC-6",
                f"The displacement of the target has the degrees "
                f"{sorted(degrees)} and not {sorted(wanted)} alone.",
            )

        determinant = self._target.determinant()

        # Not reachable without the pragma: CHC-1, CHC-3 and CHC-4 run first,
        # and Lemma 2 of the paper makes the restriction Keller.
        if not agree(determinant, sp.Integer(1)):  # pragma: no cover - Lemma 2
            raise VerificationError(
                "CHC-6",
                f"The target has Jacobian determinant {determinant}, not one.",
            )

    def transport(self, collision: Collision) -> Collision:
        """Express a collision in the basis, or refuse it.

        CHC-9. The coordinates of a point ``v`` are the unique ``c`` with
        ``B^T c = v``. A point outside the subspace has none, and the step says
        so rather than producing something: the target is a map on ``W``.

        This is the only transport in the library that can refuse a collision
        that genuinely holds for its source, and it is also the only one that
        would run in the other direction, since distinct coordinates give
        distinct points of ``W``.
        """
        collision.verify(self._source)

        points = tuple(
            self._coordinates(point, f"point {index}")
            for index, point in enumerate(collision.points)
        )
        image = self._coordinates(collision.image, "image")

        moved = Collision(points, image)
        moved.verify(self._target)

        return moved

    def _coordinates(self, vector: Vector, description: str) -> Vector:
        """Return the coordinates of ``vector`` in the basis, or raise CHC-9."""
        domain = self._source.ring.domain
        rows = self._pivot_rows()

        matrix = sp.Matrix(
            [[row[position] for row in self._basis] for position in rows]
        ).inv()
        coordinates = matrix * sp.Matrix([sp.sympify(vector[i]) for i in rows])

        echelon = _Echelon(domain)
        for row in self._basis:
            echelon.offer(_to_domain(row, domain))

        if not echelon.spans(_to_domain(vector, domain)):
            raise VerificationError(
                "CHC-9",
                f"The {description} of the collision is not in the subspace "
                "the step restricts to, so it has no coordinates there. A "
                "step compresses along the collision it was built from.",
            )

        return tuple(sp.expand(value) for value in coordinates)

    # ----------------------------------------------------------------------

    def _key(self) -> tuple[Element, ...]:
        """Return what equality compares."""
        return (
            self._source,
            self._target,
            self._basis,
            tuple(variable.name for variable in self._variables),
            self._provenance,
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CompressionStep):
            return NotImplemented
        return self._key() == other._key()

    def __hash__(self) -> int:
        return hash(self._key())

    def __repr__(self) -> str:
        return (
            f"CompressionStep("
            f"dimension={self._source.dimension}->{self._target.dimension}, "
            f"provenance={self._provenance.value})"
        )
