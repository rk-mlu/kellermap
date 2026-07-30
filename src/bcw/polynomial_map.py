from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass
from functools import cached_property

import sympy as sp


@dataclass(frozen=True)
class PolynomialMap:
    """
    A polynomial map F : Kⁿ → Kⁿ.

    Parameters
    ----------
    variables
        Variables of the polynomial ring.
    components
        Components of the polynomial map.
    """

    variables: tuple[sp.Symbol, ...]
    components: tuple[sp.Expr, ...]

    def __init__(
        self, variables: Iterable[sp.Symbol], components: Iterable[sp.Expr]
    ) -> None:
        object.__setattr__(self, "variables", tuple(variables))
        object.__setattr__(self, "components", tuple(components))

        self._validate()

    def _validate(self) -> None:
        """Validate the polynomial map."""
        if len(self.variables) != len(self.components):
            raise ValueError("Number of variables and components differ.")

        if not all(isinstance(v, sp.Symbol) for v in self.variables):
            raise TypeError("Variables must be SymPy symbols.")

        if len(set(self.variables)) != len(self.variables):
            raise ValueError("Variables must be pairwise distinct.")

        if not all(isinstance(c, sp.Expr) for c in self.components):
            raise TypeError("Components must be SymPy expressions.")

    @property
    def dimension(self) -> int:
        """Return the dimension of the polynomial map."""
        return len(self.variables)

    @cached_property
    def matrix(self) -> sp.Matrix:
        """Return the components as a column matrix."""
        return sp.Matrix(self.components)

    def compose(self, other: PolynomialMap) -> PolynomialMap:
        """Return the composition self ∘ other."""

        if self.variables != other.variables:
            raise ValueError("Polynomial maps have different variables.")

        substitutions = dict(zip(self.variables, other.components, strict=True))

        components = tuple(
            component.xreplace(substitutions) for component in self.components
        )

        return PolynomialMap(
            self.variables,
            components,
        )

    def jacobian(self) -> sp.Matrix:
        """Return the Jacobian matrix."""
        return self.matrix.jacobian(self.variables)

    def determinant(self) -> sp.Expr:
        """Return the Jacobian determinant."""
        return sp.expand(self.jacobian().det())

    def _poly(self, component: sp.Expr) -> sp.Poly:
        """Return a component as a polynomial in ``self.variables``.

        Symbols that are not among ``self.variables`` (an indeterminate ``T``,
        a symbolic coefficient) end up in the coefficient domain and therefore
        do not contribute to degree or order.
        """
        return sp.Poly(component, *self.variables)

    def degree(self) -> int:
        """Return the total degree of the map with respect to its variables.

        The degree of the zero map is ``0`` by SymPy convention.
        """
        return max(int(self._poly(f).total_degree()) for f in self.components)

    def order(self) -> int | float:
        """Return the order: the lowest total degree occurring in the map.

        The order of the zero map is ``math.inf``.
        """
        orders = [
            min(sum(monomial) for monomial in poly.monoms())
            for f in self.components
            if not (poly := self._poly(f)).is_zero
        ]

        return min(orders) if orders else math.inf

    def displacement(self) -> PolynomialMap:
        """Return ``F - X``."""
        return PolynomialMap(
            self.variables,
            tuple(
                sp.expand(component - variable)
                for component, variable in zip(
                    self.components, self.variables, strict=True
                )
            ),
        )

    def filtration_degree(self) -> int | float:
        """Return the largest ``d`` with ``F`` in ``MA^d``.

        Bass–Connell–Wright filter ``MA_n(k)`` by the order of ``F - X``:
        ``F`` lies in ``MA^d_n(k)`` exactly when ``ord(F - X) > d``. The
        identity therefore lies in every ``MA^d`` and returns ``math.inf``.
        """
        return self.displacement().order() - 1

    def is_in_MA(self, d: int) -> bool:  # noqa: N802
        """Return whether the map lies in ``MA^d``."""
        return self.filtration_degree() >= d

    def extend(self, number: int = 2) -> PolynomialMap:
        """Extend the polynomial map by the identity."""

        start = self.dimension + 1

        new_variables = tuple(sp.Symbol(f"X{i}") for i in range(start, start + number))

        return PolynomialMap(
            self.variables + new_variables,
            self.components + new_variables,
        )

    def __call__(self, *args: sp.Expr) -> sp.Matrix:
        """Evaluate the polynomial map."""

        if len(args) != self.dimension:
            raise ValueError(f"Expected {self.dimension} arguments, got {len(args)}.")

        substitutions = dict(zip(self.variables, args, strict=True))

        return self.matrix.xreplace(substitutions)

    def __repr__(self) -> str:
        return (
            "PolynomialMap("
            f"variables={self.variables}, "
            f"components={self.components})"
        )
