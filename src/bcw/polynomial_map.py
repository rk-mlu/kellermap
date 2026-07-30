from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from functools import cached_property
from typing import cast

import sympy as sp


@dataclass(frozen=True, slots=True)
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
            component.subs(substitutions) for component in self.components
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

    def degree(self) -> int:
        """Return the degree of the polynomial map."""
        return cast(int, max(sp.total_degree(f) for f in self.components))

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

        return self.matrix.subs(substitutions)

    def __repr__(self) -> str:
        return (
            "PolynomialMap("
            f"variables={self.variables}, "
            f"components={self.components})"
        )
