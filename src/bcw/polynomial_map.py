from __future__ import annotations

from dataclasses import dataclass

import sympy as sp


@dataclass(slots=True)
class PolynomialMap:

    variables: tuple[sp.Symbol, ...]
    components: sp.Matrix

    def __init__(self, variables, components):

        self.variables = tuple(variables)
        self.components = sp.Matrix(components)

        if len(self.variables) != len(self.components):
            raise ValueError("Number of variables and components differ.")

    @property
    def dimension(self):

        return len(self.variables)

    def compose(self, other):
        """
        self ∘ other
        """

        if self.dimension != other.dimension:
            raise ValueError("Dimensions do not agree.")

        subs = dict(zip(self.variables, other.components, strict=True))

        new = [sp.expand(f.subs(subs)) for f in self.components]

        return PolynomialMap(other.variables, new)

    def jacobian(self):

        return self.components.jacobian(self.variables)

    def determinant(self):

        return sp.expand(self.jacobian().det())

    def degree(self):

        return max(sp.total_degree(f) for f in self.components)

    def extend(self, number=2):

        vars = list(self.variables)
        comps = list(self.components)

        for _ in range(number):

            name = f"X{len(vars)+1}"

            y = sp.Symbol(name)

            vars.append(y)
            comps.append(y)

        return PolynomialMap(vars, comps)

    def __call__(self, *args):

        subs = dict(zip(self.variables, args, strict=True))

        return sp.Matrix([f.subs(subs) for f in self.components])

    def __repr__(self):

        return f"PolynomialMap(" f"{self.components})"
