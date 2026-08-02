"""The linear part of a reduction, and why it is not elementary.

BCW Section 4 begins by replacing ``F'`` with ``F'' = F'_(1)^-1 o F'``. The
transformation is an element of ``GL_n(k)``, and only some of the Gauss
operations it decomposes into are elementary in the sense of the paper.

A transvection ``X_i |-> X_i + a X_j`` with ``i != j`` *is* elementary:
``a X_j`` is free of ``X_i``. It lies in ``EA^0`` and not in ``EA^1``, since
its displacement has order one. ``Transvection.as_elementary_factor`` hands it
to the machinery of ``elementary.py`` unchanged.

A transposition and a dilation are not. A dilation ``X_i |-> a X_i``
displaces ``X_i`` by ``(a - 1) X_i``, which involves ``X_i``; a transposition
moves two coordinates rather than one and has determinant ``-1``. The shortest
argument needs no factorization at all: every element of ``EA_n(k)`` has
determinant one, so nothing of another determinant can lie in it. The
transformation normalizing Alpoege's map has determinant ``-1/2``.

Over a field the transvections generate ``SL_n(k)``, so the non-elementary
content of any element is one dilation: a transposition is three transvections
followed by a dilation by ``-1``. ``factorize`` does not spend those three,
because a transposition is what the Gauss elimination naturally produces and
is easier to read against a hand computation.

This is why the linear part gets its own type rather than a scaling parameter
on ``ElementaryFactor``, and why ``LinearStep`` in version 0.2 is the only
kind of step permitted to change the Jacobian determinant.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Any, cast

import sympy as sp
from sympy.polys.polyerrors import (
    CoercionFailed,
    ExactQuotientFailed,
    NotInvertible,
)
from sympy.polys.rings import PolyElement, PolyRing

from .elementary import ElementaryFactor
from .polynomial_map import (
    PolynomialMap,
    clone_domain,
    clone_ring,
    copy_polynomial,
    validate_ring,
)

_NOT_IN_DOMAIN = (
    "The coefficient {coefficient} does not lie in the coefficient domain "
    "{domain}. A dilation by a non-unit needs the field of fractions; see "
    "over_field()."
)


def field_ring(ring: PolyRing) -> PolyRing:
    """Return the same ring over the field of fractions of its domain.

    A Keller map read off a paper usually lands over ``ZZ``, and the
    normalization of Section 4 immediately needs a reciprocal: the linear part
    of Alpoege's map has determinant ``-2``. Widening the domain is a
    deliberate step rather than something the arithmetic does silently, since
    two maps over different domains are different objects here.
    """
    validate_ring(ring)

    return PolyRing(ring.symbols, clone_domain(ring.domain).get_field(), ring.order)


def over_field(F: PolynomialMap) -> PolynomialMap:  # noqa: N803
    """Return the map over the field of fractions of its coefficient domain."""
    target = field_ring(F.ring)

    return PolynomialMap.from_ring(
        target,
        [copy_polynomial(component, target) for component in F.to_polynomials()],
    )


class LinearFactor(ABC):
    """A generator of ``GL_n(k)``: one Gauss operation on the coordinates.

    Three of them, and the distinction between them is the point of the
    module: ``is_elementary`` says whether BCW would admit the factor into
    ``EA_n(k)``.

    A factor acts on maps over one ring, exactly as ``ElementaryFactor`` does,
    and mismatches are rejected rather than coerced.
    """

    _ring: PolyRing

    @property
    def ring(self) -> PolyRing:
        """Return the arithmetic context, as a clone.

        A clone, for the reason given at ``PolynomialMap.ring``: a ``PolyRing``
        owns mutable generators and SymPy reads them.
        """
        return clone_ring(self._ring)

    @property
    def dimension(self) -> int:
        """Return the number of coordinates."""
        return int(self._ring.ngens)

    @property
    @abstractmethod
    def is_elementary(self) -> bool:
        """Return whether the factor lies in ``EA_n(k)``."""

    @abstractmethod
    def matrix(self) -> sp.ImmutableMatrix:
        """Return the factor as a matrix acting on the coordinate vector."""

    @abstractmethod
    def determinant(self) -> sp.Expr:
        """Return the Jacobian determinant, which is constant."""

    @abstractmethod
    def inverse(self) -> LinearFactor:
        """Return the inverse factor, of the same kind."""

    @abstractmethod
    def apply_to(self, other: PolynomialMap) -> PolynomialMap:
        """Return ``self o other``.

        Left composition, so only the components the factor touches are
        recombined. No substitution happens: a linear map acts on the
        components, not on the variables.
        """

    def to_polynomial_map(self) -> PolynomialMap:
        """Return the factor as a ``PolynomialMap``."""
        return self.apply_to(PolynomialMap.from_ring(self._ring, self._ring.gens))

    def _require_same_ring(self, other: PolynomialMap) -> list[PolyElement]:
        if self._ring != other.ring:
            raise ValueError("The factor and the map use different rings.")

        return list(other.to_polynomials())

    def _identity_matrix(self) -> sp.MutableDenseMatrix:
        return sp.eye(self.dimension)


def _validate_index(ring: PolyRing, index: int, name: str = "index") -> None:
    if isinstance(index, bool) or not isinstance(index, int):
        raise TypeError(f"The {name} must be an integer, not {type(index).__name__}.")

    if not 0 <= index < ring.ngens:
        raise ValueError(f"Index {index} is out of range for {ring.ngens} variables.")


def _convert(ring: PolyRing, coefficient: sp.Expr | Any) -> Any:
    """Return the coefficient as an element of the ring's domain."""
    try:
        return ring.domain.convert(sp.sympify(coefficient))
    except (CoercionFailed, sp.SympifyError, TypeError, ValueError) as error:
        raise ValueError(
            _NOT_IN_DOMAIN.format(coefficient=coefficient, domain=ring.domain)
        ) from error


@dataclass(frozen=True, eq=False)
class Transvection(LinearFactor):
    """``X_index |-> X_index + coefficient * X_source``, with the two distinct.

    Elementary in the sense of BCW, and the only one of the three that is.
    ``as_elementary_factor`` returns exactly that reading of it, so a
    normalization can hand its transvections to the same machinery that
    carries the reduction steps.
    """

    _ring: PolyRing
    _index: int
    _source: int
    _coefficient: Any

    def __init__(
        self,
        ring: PolyRing,
        index: int,
        source: int,
        coefficient: sp.Expr | Any,
    ) -> None:
        validate_ring(ring)
        _validate_index(ring, index)
        _validate_index(ring, source, "source")

        if index == source:
            raise ValueError(
                f"A transvection needs two distinct coordinates; both are {index}."
            )

        owned = clone_ring(ring)

        object.__setattr__(self, "_ring", owned)
        object.__setattr__(self, "_index", index)
        object.__setattr__(self, "_source", source)
        object.__setattr__(self, "_coefficient", _convert(owned, coefficient))

    @property
    def index(self) -> int:
        """Return the coordinate that moves."""
        return self._index

    @property
    def source(self) -> int:
        """Return the coordinate that is added in."""
        return self._source

    @property
    def coefficient(self) -> sp.Expr:
        """Return the multiple that is added."""
        return cast(sp.Expr, self._ring.domain.to_sympy(self._coefficient))

    @property
    def is_elementary(self) -> bool:
        """Return ``True``: ``coefficient * X_source`` is free of ``X_index``."""
        return True

    def matrix(self) -> sp.ImmutableMatrix:
        entries = self._identity_matrix()
        entries[self._index, self._source] = self.coefficient

        return sp.ImmutableMatrix(entries)

    def determinant(self) -> sp.Expr:
        """Return one. The matrix is unipotent, as for any elementary factor."""
        return cast(sp.Expr, sp.Integer(1))

    def inverse(self) -> Transvection:
        return Transvection(self._ring, self._index, self._source, -self.coefficient)

    def as_elementary_factor(self) -> ElementaryFactor:
        """Return the same map as a generator of ``EA_n(k)``."""
        return ElementaryFactor(
            self._ring,
            self._index,
            self._coefficient * self._ring.gens[self._source],
        )

    def apply_to(self, other: PolynomialMap) -> PolynomialMap:
        components = self._require_same_ring(other)
        components[self._index] = (
            components[self._index] + self._coefficient * components[self._source]
        )

        return PolynomialMap.from_ring(self._ring, components)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Transvection):
            return NotImplemented
        return (
            self._ring.symbols == other._ring.symbols
            and self._ring.domain == other._ring.domain
            and self._index == other._index
            and self._source == other._source
            and self.coefficient == other.coefficient
        )

    def __hash__(self) -> int:
        return hash(
            (
                self._ring.symbols,
                self._ring.domain,
                self._index,
                self._source,
                self.coefficient,
            )
        )

    def __repr__(self) -> str:
        return (
            f"Transvection(index={self._index}, source={self._source}, "
            f"coefficient={self.coefficient})"
        )


@dataclass(frozen=True, eq=False)
class Transposition(LinearFactor):
    """Exchange two coordinates. Its own inverse, and of determinant ``-1``.

    Not elementary: an elementary factor moves one coordinate, this moves two,
    and no product of factors of determinant one has determinant ``-1``.
    """

    _ring: PolyRing
    _first: int
    _second: int

    def __init__(self, ring: PolyRing, first: int, second: int) -> None:
        validate_ring(ring)
        _validate_index(ring, first, "first index")
        _validate_index(ring, second, "second index")

        if first == second:
            raise ValueError(
                f"A transposition needs two distinct coordinates; both are {first}."
            )

        object.__setattr__(self, "_ring", clone_ring(ring))
        object.__setattr__(self, "_first", min(first, second))
        object.__setattr__(self, "_second", max(first, second))

    @property
    def indices(self) -> tuple[int, int]:
        """Return the exchanged coordinates, in ascending order."""
        return (self._first, self._second)

    @property
    def is_elementary(self) -> bool:
        """Return ``False``. Its determinant alone rules it out."""
        return False

    def matrix(self) -> sp.ImmutableMatrix:
        entries = self._identity_matrix()
        entries[self._first, self._first] = sp.Integer(0)
        entries[self._second, self._second] = sp.Integer(0)
        entries[self._first, self._second] = sp.Integer(1)
        entries[self._second, self._first] = sp.Integer(1)

        return sp.ImmutableMatrix(entries)

    def determinant(self) -> sp.Expr:
        return cast(sp.Expr, sp.Integer(-1))

    def inverse(self) -> Transposition:
        """Return the same transposition. It is an involution."""
        return self

    def apply_to(self, other: PolynomialMap) -> PolynomialMap:
        components = self._require_same_ring(other)
        components[self._first], components[self._second] = (
            components[self._second],
            components[self._first],
        )

        return PolynomialMap.from_ring(self._ring, components)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Transposition):
            return NotImplemented
        return (
            self._ring.symbols == other._ring.symbols
            and self._ring.domain == other._ring.domain
            and self.indices == other.indices
        )

    def __hash__(self) -> int:
        return hash((self._ring.symbols, self._ring.domain, self.indices))

    def __repr__(self) -> str:
        return f"Transposition(first={self._first}, second={self._second})"


@dataclass(frozen=True, eq=False)
class Dilation(LinearFactor):
    """``X_index |-> coefficient * X_index``, the coefficient a unit.

    Not elementary: the displacement ``(coefficient - 1) X_index`` involves
    ``X_index``, which BCW exclude by definition. This is the factor that
    carries the whole non-elementary content of a linear transformation, and
    the only source of a determinant other than one in a reduction.
    """

    _ring: PolyRing
    _index: int
    _coefficient: Any

    def __init__(self, ring: PolyRing, index: int, coefficient: sp.Expr | Any) -> None:
        validate_ring(ring)
        _validate_index(ring, index)

        owned = clone_ring(ring)
        value = _convert(owned, coefficient)

        if not value:
            raise ValueError("A dilation by zero is not invertible.")

        # Der Kehrwert wird hier gebildet und nicht erst in inverse(): ein
        # Faktor, dessen Inverses nicht im Bereich liegt, ist kein Element von
        # GL_n(k), und das soll bei der Konstruktion auffallen.
        try:
            owned.domain.exquo(owned.domain.one, value)
        except (
            CoercionFailed,
            ExactQuotientFailed,
            NotInvertible,
            ZeroDivisionError,
        ) as error:
            raise ValueError(
                _NOT_IN_DOMAIN.format(
                    coefficient=f"1/{owned.domain.to_sympy(value)}",
                    domain=owned.domain,
                )
            ) from error

        object.__setattr__(self, "_ring", owned)
        object.__setattr__(self, "_index", index)
        object.__setattr__(self, "_coefficient", value)

    @property
    def index(self) -> int:
        """Return the coordinate that is scaled."""
        return self._index

    @property
    def coefficient(self) -> sp.Expr:
        """Return the scaling factor."""
        return cast(sp.Expr, self._ring.domain.to_sympy(self._coefficient))

    @property
    def is_elementary(self) -> bool:
        """Return ``False``. Its displacement involves its own variable."""
        return False

    def matrix(self) -> sp.ImmutableMatrix:
        entries = self._identity_matrix()
        entries[self._index, self._index] = self.coefficient

        return sp.ImmutableMatrix(entries)

    def determinant(self) -> sp.Expr:
        return self.coefficient

    def inverse(self) -> Dilation:
        return Dilation(
            self._ring,
            self._index,
            self._ring.domain.to_sympy(
                self._ring.domain.exquo(self._ring.domain.one, self._coefficient)
            ),
        )

    def apply_to(self, other: PolynomialMap) -> PolynomialMap:
        components = self._require_same_ring(other)
        components[self._index] = self._coefficient * components[self._index]

        return PolynomialMap.from_ring(self._ring, components)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Dilation):
            return NotImplemented
        return (
            self._ring.symbols == other._ring.symbols
            and self._ring.domain == other._ring.domain
            and self._index == other._index
            and self.coefficient == other.coefficient
        )

    def __hash__(self) -> int:
        return hash(
            (self._ring.symbols, self._ring.domain, self._index, self.coefficient)
        )

    def __repr__(self) -> str:
        return f"Dilation(index={self._index}, coefficient={self.coefficient})"


@dataclass(frozen=True, eq=False)
class LinearAutomorphism:
    """An element of ``GL_n(k)``, as an ordered product of Gauss generators.

    ``factors = (f_1, ..., f_k)`` denotes ``f_1 o ... o f_k``, matching
    ``ElementaryAutomorphism``. The empty product is the identity and carries
    no ring.

    The factorization is kept rather than multiplied out, for the reason it is
    kept there: "invertible" is a claim, "here are the generators and their
    inverses" is a proof, and ``LinearStep`` has to exhibit the one it used.
    Two factorizations of the same matrix are different objects and compare
    unequal.
    """

    factors: tuple[LinearFactor, ...]

    def __init__(self, factors: Iterable[LinearFactor] = ()) -> None:
        collected = tuple(factors)

        if not all(isinstance(factor, LinearFactor) for factor in collected):
            raise TypeError("All factors must be LinearFactor instances.")

        rings = {factor.ring for factor in collected}
        if len(rings) > 1:
            raise ValueError("All factors must use the same ring.")

        object.__setattr__(self, "factors", collected)

    @classmethod
    def identity(cls) -> LinearAutomorphism:
        """Return the empty product."""
        return cls(())

    @classmethod
    def factorize(
        cls, ring: PolyRing, matrix: Sequence[Sequence[sp.Expr]] | sp.MatrixBase
    ) -> LinearAutomorphism:
        """Factor an invertible matrix into Gauss generators.

        Gauss-Jordan elimination records the row operations ``R_1, ..., R_k``
        with ``R_k ... R_1 M = I``, and the factorization is
        ``M = R_1^-1 ... R_k^-1``. Pivots are exchanged by a transposition
        rather than by three transvections and a dilation by ``-1``: the
        result is easier to read against a hand computation, and the
        arithmetic is the same.

        A singular matrix raises ``ValueError``. So does a matrix needing a
        reciprocal the coefficient domain does not have -- ``over_field``
        first, in that case.
        """
        validate_ring(ring)
        working = sp.Matrix(matrix)

        if working.shape != (ring.ngens, ring.ngens):
            raise ValueError(
                f"Expected a {ring.ngens}x{ring.ngens} matrix, "
                f"got {working.shape[0]}x{working.shape[1]}."
            )

        owned = clone_ring(ring)
        operations: list[LinearFactor] = []

        for column in range(owned.ngens):
            pivot = _pivot_row(working, column)
            if pivot is None:
                raise ValueError("The matrix is singular and does not lie in GL_n(k).")

            if pivot != column:
                operations.append(Transposition(owned, column, pivot))
                working.row_swap(column, pivot)

            entry = sp.simplify(working[column, column])
            if entry != 1:
                scaling = Dilation(owned, column, 1 / entry)
                operations.append(scaling)
                working = sp.Matrix(scaling.matrix()) * working

            for row in range(owned.ngens):
                if row == column or sp.simplify(working[row, column]) == 0:
                    continue
                shear = Transvection(
                    owned, row, column, -sp.simplify(working[row, column])
                )
                operations.append(shear)
                working = sp.Matrix(shear.matrix()) * working

        return cls(operation.inverse() for operation in operations)

    @property
    def ring(self) -> PolyRing:
        """Return the shared arithmetic context of the factors."""
        if not self.factors:
            raise ValueError("The identity carries no ring.")

        return self.factors[0].ring

    @property
    def dimension(self) -> int:
        """Return the number of coordinates."""
        if not self.factors:
            raise ValueError("The identity carries no dimension.")

        return self.factors[0].dimension

    @property
    def is_elementary(self) -> bool:
        """Return whether every factor is elementary.

        A sufficient condition, not a characterization: a product of
        non-elementary factors can still land in ``EA_n(k)``, as two equal
        transpositions do. What the property reports is whether the exhibited
        factorization stays inside the group, which is what a certificate can
        check without forming anything.
        """
        return all(factor.is_elementary for factor in self.factors)

    def matrix(self, ring: PolyRing | None = None) -> sp.ImmutableMatrix:
        """Return the product of the factor matrices, in order.

        ``ring`` is required only for the identity, which carries no
        dimension of its own.
        """
        if not self.factors:
            if ring is None:
                raise ValueError("The identity needs a ring to become a matrix.")
            return sp.ImmutableMatrix(sp.eye(ring.ngens))

        product = sp.eye(self.dimension)
        for factor in self.factors:
            product = product * sp.Matrix(factor.matrix())

        return sp.ImmutableMatrix(product)

    def compose(self, other: LinearAutomorphism) -> LinearAutomorphism:
        """Return ``self o other``, by concatenating the factorizations."""
        if self.factors and other.factors and self.ring != other.ring:
            raise ValueError("The automorphisms use different rings.")

        return LinearAutomorphism(self.factors + other.factors)

    def inverse(self) -> LinearAutomorphism:
        """Return ``(f_1 o ... o f_k)^-1 = f_k^-1 o ... o f_1^-1``."""
        return LinearAutomorphism(factor.inverse() for factor in reversed(self.factors))

    def determinant(self) -> sp.Expr:
        """Return the product of the factor determinants.

        Unlike in ``EA_n(k)`` this is not one in general, and a reduction has
        to say by what factor a linear step changes it. Structural all the
        same: no matrix is formed.
        """
        product = sp.Integer(1)
        for factor in self.factors:
            product = product * factor.determinant()

        return cast(sp.Expr, sp.simplify(product))

    def apply_to(self, other: PolynomialMap) -> PolynomialMap:
        """Return ``self o other``, one factor at a time, right to left."""
        result = other
        for factor in reversed(self.factors):
            result = factor.apply_to(result)

        return result

    def to_polynomial_map(self, ring: PolyRing | None = None) -> PolynomialMap:
        """Return the product as a ``PolynomialMap``.

        ``ring`` is required only for the identity, which carries none.
        """
        context = self.ring if self.factors else ring
        if context is None:
            raise ValueError("The identity needs a ring to become a map.")

        return self.apply_to(PolynomialMap.from_ring(context, context.gens))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, LinearAutomorphism):
            return NotImplemented
        return self.factors == other.factors

    def __hash__(self) -> int:
        return hash(self.factors)

    def __len__(self) -> int:
        return len(self.factors)

    def __repr__(self) -> str:
        return f"LinearAutomorphism(factors={self.factors})"


def _pivot_row(matrix: sp.MutableDenseMatrix, column: int) -> int | None:
    """Return the first row at or below ``column`` with a nonzero entry."""
    for row in range(column, matrix.rows):
        if sp.simplify(matrix[row, column]) != 0:
            return row

    return None
