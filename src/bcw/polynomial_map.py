from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass
from functools import cached_property
from typing import cast

import sympy as sp
from sympy.polys.matrices import DomainMatrix
from sympy.polys.polyerrors import PolynomialError
from sympy.polys.rings import PolyElement, PolyRing, sring


@dataclass(frozen=True, eq=False)
class PolynomialMap:
    """A polynomial endomorphism of an affine space.

    The public boundary uses SymPy expressions, while polynomial arithmetic is
    performed internally in a sparse :class:`~sympy.polys.rings.PolyRing`.

    Parameters
    ----------
    variables
        Pairwise distinct generators of the polynomial ring.
    components
        Polynomial coordinate functions in ``variables``. Symbols not listed
        in ``variables`` are placed in the coefficient domain.
    """

    _ring: PolyRing
    _poly_components: tuple[PolyElement, ...]

    def __init__(
        self, variables: Iterable[sp.Symbol], components: Iterable[sp.Expr]
    ) -> None:
        variables_tuple = tuple(variables)
        components_tuple = tuple(components)

        self._validate_expr_input(variables_tuple, components_tuple)

        try:
            polynomial_ring, polynomial_components = sring(
                components_tuple, *variables_tuple
            )
        except PolynomialError as exc:
            raise ValueError(
                "Components must be polynomials in the specified variables."
            ) from exc

        object.__setattr__(self, "_ring", polynomial_ring)
        object.__setattr__(
            self,
            "_poly_components",
            tuple(
                self._copy_polynomial(polynomial)
                for polynomial in polynomial_components
            ),
        )

    @classmethod
    def from_ring(
        cls,
        polynomial_ring: PolyRing,
        components: Iterable[PolyElement],
    ) -> PolynomialMap:
        """Construct a map directly from elements of ``polynomial_ring``.

        This is the efficient construction path for internal algorithms. The
        components are copied so that the immutable ``PolynomialMap`` does not
        share mutable ``PolyElement`` instances with its caller.
        """
        components_tuple = tuple(components)

        if not polynomial_ring.ngens:
            raise ValueError("A polynomial map needs at least one variable.")

        if not all(isinstance(symbol, sp.Symbol) for symbol in polynomial_ring.symbols):
            raise TypeError("Ring generators must be SymPy symbols.")

        if polynomial_ring.ngens != len(components_tuple):
            raise ValueError("Number of variables and components differ.")

        if not all(polynomial_ring.is_element(f) for f in components_tuple):
            raise ValueError("All components must belong to the specified ring.")

        instance = object.__new__(cls)
        object.__setattr__(instance, "_ring", polynomial_ring)
        object.__setattr__(
            instance,
            "_poly_components",
            tuple(cls._copy_polynomial(component) for component in components_tuple),
        )
        return instance

    @staticmethod
    def _copy_polynomial(polynomial: PolyElement) -> PolyElement:
        """Recursively copy a polynomial and polynomial coefficients."""
        terms = []
        for monomial, coefficient in polynomial.iterterms():
            if isinstance(coefficient, PolyElement):
                coefficient = PolynomialMap._copy_polynomial(coefficient)
            terms.append((monomial, coefficient))
        return polynomial.ring.from_terms(terms)

    @staticmethod
    def _validate_expr_input(
        variables: tuple[sp.Symbol, ...],
        components: tuple[sp.Expr, ...],
    ) -> None:
        """Validate the expression-level constructor arguments."""
        if not variables:
            raise ValueError("A polynomial map needs at least one variable.")

        if len(variables) != len(components):
            raise ValueError("Number of variables and components differ.")

        if not all(isinstance(variable, sp.Symbol) for variable in variables):
            raise TypeError("Variables must be SymPy symbols.")

        if len(set(variables)) != len(variables):
            raise ValueError("Variables must be pairwise distinct.")

        if not all(isinstance(component, sp.Expr) for component in components):
            raise TypeError("Components must be SymPy expressions.")

    @property
    def ring(self) -> PolyRing:
        """Return the internal sparse polynomial ring.

        The returned ring is the arithmetic context. Coordinate polynomials
        remain private because ``PolyElement`` is mutable.
        """
        return self._ring

    @property
    def variables(self) -> tuple[sp.Symbol, ...]:
        """Return the polynomial variables."""
        return cast(tuple[sp.Symbol, ...], self._ring.symbols)

    @cached_property
    def components(self) -> tuple[sp.Expr, ...]:
        """Return the coordinate functions as immutable SymPy expressions."""
        return tuple(component.as_expr() for component in self._poly_components)

    def to_polynomials(self) -> tuple[PolyElement, ...]:
        """Return defensive copies of the internal coordinate polynomials."""
        return tuple(
            self._copy_polynomial(component) for component in self._poly_components
        )

    @property
    def dimension(self) -> int:
        """Return the dimension of the polynomial endomorphism."""
        return self._ring.ngens

    @cached_property
    def matrix(self) -> sp.Matrix:
        """Return the components as an expression-valued column matrix."""
        return sp.Matrix(self.components)

    @cached_property
    def _jacobian_polynomials(self) -> tuple[tuple[PolyElement, ...], ...]:
        return tuple(
            tuple(component.diff(variable) for variable in self._ring.gens)
            for component in self._poly_components
        )

    def jacobian(self) -> sp.Matrix:
        """Return the Jacobian matrix as SymPy expressions."""
        return sp.Matrix(
            [[entry.as_expr() for entry in row] for row in self._jacobian_polynomials]
        )

    @cached_property
    def _determinant_polynomial(self) -> PolyElement:
        domain = self._ring.to_domain()
        matrix = DomainMatrix.from_list(
            [list(row) for row in self._jacobian_polynomials],
            domain,
        )
        return cast(PolyElement, matrix.det())

    def determinant(self) -> sp.Expr:
        """Return the Jacobian determinant.

        The determinant is computed over the sparse polynomial-ring domain,
        not through an expression-valued SymPy matrix.
        """
        return self._determinant_polynomial.as_expr()

    def compose(self, other: PolynomialMap) -> PolynomialMap:
        """Return the simultaneous composition ``self ∘ other``."""
        if self.variables != other.variables:
            raise ValueError("Polynomial maps have different variables.")

        left, right, common_ring = self._coerce_to_common_ring(other)
        substitutions = dict(zip(common_ring.gens, right, strict=True))
        components = tuple(component.compose(substitutions) for component in left)

        return PolynomialMap.from_ring(common_ring, components)

    def _coerce_to_common_ring(self, other: PolynomialMap) -> tuple[
        tuple[PolyElement, ...],
        tuple[PolyElement, ...],
        PolyRing,
    ]:
        """Return both maps in one compatible polynomial ring."""
        if self._ring == other._ring:
            return self._poly_components, other._poly_components, self._ring

        expressions = self.components + other.components
        common_ring, common_components = sring(expressions, *self.variables)
        split = self.dimension
        return (
            tuple(common_components[:split]),
            tuple(common_components[split:]),
            common_ring,
        )

    def degree(self) -> int:
        """Return the largest total degree of a coordinate function."""
        return max(
            (
                sum(monomial)
                for component in self._poly_components
                for monomial in component.itermonoms()
            ),
            default=0,
        )

    def order(self) -> int | float:
        """Return the smallest occurring total degree.

        The order of the zero map is ``math.inf``.
        """
        return min(
            (
                sum(monomial)
                for component in self._poly_components
                for monomial in component.itermonoms()
            ),
            default=math.inf,
        )

    def displacement(self) -> PolynomialMap:
        """Return ``F - X``."""
        components = tuple(
            component - variable
            for component, variable in zip(
                self._poly_components, self._ring.gens, strict=True
            )
        )
        return PolynomialMap.from_ring(self._ring, components)

    def filtration_degree(self) -> int | float:
        """Return the largest ``d`` such that the map lies in ``MA^d``."""
        return self.displacement().order() - 1

    def is_in_MA(self, d: int) -> bool:  # noqa: N802
        """Return whether the map lies in ``MA^d``."""
        return self.filtration_degree() >= d

    def extend(self, number: int = 2) -> PolynomialMap:
        """Extend the map by ``number`` identity coordinates."""
        if number < 0:
            raise ValueError("The extension size must be non-negative.")
        if number == 0:
            return self

        new_variables = self._fresh_variables(number)
        new_ring = self._ring.clone(symbols=self.variables + new_variables)
        old_components = tuple(
            component.set_ring(new_ring) for component in self._poly_components
        )
        components = old_components + new_ring.gens[-number:]
        return PolynomialMap.from_ring(new_ring, components)

    def _fresh_variables(self, number: int) -> tuple[sp.Symbol, ...]:
        """Create deterministic variable names without ring/domain collisions."""
        domain_symbols = tuple(getattr(self._ring.domain, "symbols", ()))
        used_names = {
            symbol.name
            for symbol in self.variables + domain_symbols
            if isinstance(symbol, sp.Symbol)
        }

        fresh: list[sp.Symbol] = []
        index = self.dimension + 1
        while len(fresh) < number:
            name = f"X{index}"
            if name not in used_names:
                fresh.append(sp.Symbol(name))
                used_names.add(name)
            index += 1

        return tuple(fresh)

    def __call__(self, *args: sp.Expr) -> sp.Matrix:
        """Evaluate the map, allowing arbitrary symbolic arguments."""
        if len(args) != self.dimension:
            raise ValueError(f"Expected {self.dimension} arguments, got {len(args)}.")

        substitutions = dict(zip(self.variables, args, strict=True))
        return self.matrix.xreplace(substitutions)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PolynomialMap):
            return NotImplemented
        return self.variables == other.variables and self.components == other.components

    def __hash__(self) -> int:
        return hash((self.variables, self.components))

    def __repr__(self) -> str:
        return (
            "PolynomialMap("
            f"variables={self.variables}, "
            f"components={self.components})"
        )
