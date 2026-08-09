"""Reconstruct the reduction from Alpoege's map to alpoege19 in plain SymPy.

This file does not depend on ``kellermap`` or on its test data. It is a second,
independent rendering of the seventeen reduction steps that lead from
Alpoege's three-dimensional map to the published degree-three map in nineteen
variables. The published JSON is read directly, either from its URL or from a
local copy.

The reduction uses three extensions of the classical step from
Bass-Connell-Wright, Chapter II, Proposition (3.1):

* a factor may be supplied by a coordinate introduced by an earlier step;
* the product may carry an explicit scalar coefficient;
* one fresh coordinate may supply both factors of a square.

For a fresh slot ``Fresh(u, P)``, put ``Phi = u + P``. For a carried slot
``Carried(u)``, put ``Phi = F_u``, the current component indexed by ``u``. A
step with target ``t`` and coefficient ``lambda`` is

    F_t -> F_t - lambda * Phi_left * Phi_right.

Every distinct fresh coordinate is appended once. Step 15 therefore introduces
``w3 + x*y**2`` once and uses that same component in both slots. All formulas
below are implemented directly with SymPy expressions.

Run against the published file online with::

    python scripts/reconstruct_alpoege19.py

For an offline check, pass a downloaded copy instead::

    python scripts/reconstruct_alpoege19.py degree3_map.json

The exit status is 0 if every check passes and 1 otherwise.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any
from urllib.request import urlopen

import sympy as sp

x, y, z = sp.symbols("x y z")
w = sp.symbols("w1:17")
w1, w2, w3, w4, w5, w6, w7, w8, w9, w10, w11, w12, w13, w14, w15, w16 = w

VARIABLES = (x, y, z) + w
SYMBOLS = {str(variable): variable for variable in VARIABLES}

R = sp.Rational

PUBLISHED_JSON = "https://rhicksrad.github.io/jacobian-degree3/degree3_map.json"


# --------------------------------------------------------------------------
# Alpoege's map and its collision
# --------------------------------------------------------------------------

ALPOEGE = {
    x: sp.expand((1 + x * y) ** 3 * z + y**2 * (1 + x * y) * (4 + 3 * x * y)),
    y: sp.expand(y + 3 * x * (1 + x * y) ** 2 * z + 3 * x * y**2 * (4 + 3 * x * y)),
    z: sp.expand(2 * x - 3 * x**2 * y - x**3 * z),
}

ALPOEGE_POINTS = (
    (sp.Integer(0), sp.Integer(0), R(-1, 4)),
    (sp.Integer(1), R(-3, 2), R(13, 2)),
    (sp.Integer(-1), R(3, 2), R(13, 2)),
)

ALPOEGE_IMAGE = (R(-1, 4), sp.Integer(0), sp.Integer(0))


# --------------------------------------------------------------------------
# The generalized reduction step
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Fresh:
    """A slot supplied by the new component ``variable + value``."""

    variable: sp.Symbol
    value: sp.Expr


@dataclass(frozen=True)
class Carried:
    """A slot supplied by the current component indexed by ``variable``."""

    variable: sp.Symbol


Slot = Fresh | Carried
Components = dict[sp.Symbol, sp.Expr]
Point = dict[sp.Symbol, sp.Expr]


@dataclass(frozen=True)
class Step:
    """One weighted step with fresh, carried, or aliased factor slots."""

    target: sp.Symbol
    left: Slot
    right: Slot
    coefficient: sp.Expr = sp.Integer(1)

    def apply(self, components: Components) -> Components:
        """Apply the step and return a new component dictionary."""
        fresh = self._fresh_values()
        self._validate(components, fresh)

        result = dict(components)
        left = self._slot_component(self.left, components)
        right = self._slot_component(self.right, components)
        result[self.target] = sp.expand(
            components[self.target] - self.coefficient * left * right
        )

        for variable, value in fresh.items():
            result[variable] = sp.expand(variable + value)

        return result

    def transport(self, point: Point) -> Point:
        """Pull a domain point back through the fresh-coordinate changes."""
        fresh = self._fresh_values()
        result = dict(point)

        for variable, value in fresh.items():
            if variable in result:
                raise ValueError(f"fresh variable {variable} is already present")
            if not value.free_symbols <= result.keys():
                raise ValueError(f"value for {variable} uses an unavailable variable")
            result[variable] = sp.expand(-value.xreplace(result))

        return result

    def slot_names(self) -> str:
        """Return the two coordinate names used in the report."""
        return f"{self.left.variable},{self.right.variable}"

    def fresh_names(self) -> str:
        """Return the names introduced by the step."""
        names = ",".join(str(variable) for variable in self._fresh_values())

        return names or "-"

    def _fresh_values(self) -> dict[sp.Symbol, sp.Expr]:
        fresh: dict[sp.Symbol, sp.Expr] = {}

        for slot in (self.left, self.right):
            if isinstance(slot, Fresh):
                value = sp.expand(slot.value)
                previous = fresh.get(slot.variable)
                if previous is not None and sp.expand(previous - value) != 0:
                    raise ValueError(
                        f"aliased fresh variable {slot.variable} has two values"
                    )
                fresh[slot.variable] = value

        return fresh

    def _validate(
        self, components: Components, fresh: dict[sp.Symbol, sp.Expr]
    ) -> None:
        if self.target not in components:
            raise ValueError(f"target {self.target} is not present")
        if self.coefficient == 0:
            raise ValueError("a reduction coefficient must be nonzero")

        for slot in (self.left, self.right):
            if slot.variable == self.target:
                raise ValueError("the target cannot supply one of its own slots")
            if isinstance(slot, Carried) and slot.variable not in components:
                raise ValueError(f"carrier {slot.variable} is not present")

        for variable, value in fresh.items():
            if variable in components:
                raise ValueError(f"fresh variable {variable} is already present")
            if variable in value.free_symbols:
                raise ValueError(f"value for {variable} uses itself")
            if not value.free_symbols <= components.keys():
                raise ValueError(f"value for {variable} uses an unavailable variable")

    @staticmethod
    def _slot_component(slot: Slot, components: Components) -> sp.Expr:
        if isinstance(slot, Carried):
            return components[slot.variable]

        return sp.expand(slot.variable + slot.value)


# --------------------------------------------------------------------------
# The reconstructed chain
# --------------------------------------------------------------------------

STEPS = (
    Step(x, Fresh(w1, y**2 * z), Fresh(w2, x**3 * y)),
    Step(y, Carried(w2), Fresh(w4, y * z), 3),
    Step(x, Carried(w4), Fresh(w5, x**2 * y), 3),
    Step(y, Carried(w5), Fresh(w8, x * w4), -3),
    Step(y, Carried(w5), Fresh(w7, y**2), 9),
    Step(x, Carried(w8), Fresh(w9, x * y), -3),
    Step(x, Carried(w7), Carried(w9), 7),
    Step(y, Carried(w4), Fresh(w13, x**2), 6),
    Step(w2, Carried(w9), Carried(w13)),
    Step(z, Carried(w13), Fresh(w16, x * z), -1),
    Step(y, Carried(w13), Fresh(w15, y * w8), 3),
    Step(y, Carried(w13), Fresh(w14, y * w7), -9),
    Step(x, Carried(w5), Fresh(w6, x * w1), -1),
    Step(x, Carried(w9), Fresh(w12, x * w6)),
    Step(x, Fresh(w3, x * y**2), Fresh(w3, x * y**2), 3),
    Step(x, Carried(w9), Fresh(w11, y * w3), -6),
    Step(x, Carried(w7), Fresh(w10, z * w2), -1),
)

EXPECTED_DIMENSIONS = (3, 5, 6, 7, 8, 9, 10, 10, 11, 11, 12, 13, 14, 15, 16, 17, 18, 19)
EXPECTED_DEGREES = (7, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 4, 4, 3)


def reconstruct(steps: tuple[Step, ...] = STEPS) -> Components:
    """Apply all steps to Alpoege's map."""
    components = dict(ALPOEGE)

    for step in steps:
        components = step.apply(components)

    return components


def transport(point: tuple[sp.Expr, ...]) -> tuple[sp.Expr, ...]:
    """Transport one of Alpoege's preimages through the whole chain."""
    values = dict(zip((x, y, z), point, strict=True))

    for step in STEPS:
        values = step.transport(values)

    return tuple(values[variable] for variable in VARIABLES)


# --------------------------------------------------------------------------
# The published JSON
# --------------------------------------------------------------------------


def load_published(
    source: str,
) -> tuple[tuple[sp.Expr, ...], tuple[tuple[sp.Expr, ...], ...]]:
    """Read the published components and points from a URL or local path."""
    if source.startswith(("http://", "https://")):
        with urlopen(source, timeout=30) as response:  # noqa: S310
            text = response.read().decode("utf-8")
    else:
        text = Path(source).read_text(encoding="utf-8")

    data: Any = json.loads(text)
    if not isinstance(data, dict) or data.get("N") != len(VARIABLES):
        raise ValueError("the JSON does not describe a 19-dimensional map")

    raw_components = data.get("components")
    raw_points = data.get("points")
    if not isinstance(raw_components, list) or len(raw_components) != len(VARIABLES):
        raise ValueError("the JSON must contain 19 components")
    if not isinstance(raw_points, list):
        raise ValueError("the JSON must contain a point list")

    components = tuple(_parse_component(component) for component in raw_components)
    points = tuple(_parse_point(point) for point in raw_points)

    return components, points


def _parse_component(raw: Any) -> sp.Expr:
    if not isinstance(raw, dict):
        raise ValueError("each component must be a monomial dictionary")

    result = sp.Integer(0)
    for monomial, coefficient in raw.items():
        if not isinstance(monomial, str) or not isinstance(coefficient, str):
            raise ValueError("monomials and coefficients must be strings")
        result += R(coefficient) * _parse_monomial(monomial)

    return sp.expand(result)


def _parse_monomial(raw: str) -> sp.Expr:
    if raw == "1":
        return sp.Integer(1)

    result = sp.Integer(1)
    for factor in raw.split("*"):
        name, separator, exponent = factor.partition("^")
        if name not in SYMBOLS:
            raise ValueError(f"unknown variable {name!r}")
        power = int(exponent) if separator else 1
        if power < 1:
            raise ValueError("monomial exponents must be positive")
        result *= SYMBOLS[name] ** power

    return result


def _parse_point(raw: Any) -> tuple[sp.Expr, ...]:
    if not isinstance(raw, dict) or set(raw) != set(SYMBOLS):
        raise ValueError("each point must give all 19 coordinates")

    values = []
    for variable in VARIABLES:
        value = raw[str(variable)]
        if not isinstance(value, str):
            raise ValueError("point coordinates must be strings")
        values.append(R(value))

    return tuple(values)


# --------------------------------------------------------------------------
# Report
# --------------------------------------------------------------------------


def main(source: str = PUBLISHED_JSON) -> int:
    """Print the chain and check it against the published JSON."""
    published_components, published_points = load_published(source)

    components = dict(ALPOEGE)
    dimensions = [len(components)]
    degrees = [_degree(components)]

    print(f"Published data: {source}")
    print()
    print("The chain")
    print(f"  source                    dim =  3  deg = {degrees[-1]}")
    for number, step in enumerate(STEPS, start=1):
        components = step.apply(components)
        dimensions.append(len(components))
        degrees.append(_degree(components))
        print(
            f"  step {number:>2}  target {step.target!s:>3}  "
            f"slots {step.slot_names():<7}  fresh {step.fresh_names():<7}  "
            f"lambda = {step.coefficient!s:>2}  "
            f"dim = {len(components):>2}  deg = {degrees[-1]}"
        )
    print()

    result = tuple(components[variable] for variable in VARIABLES)
    transported = tuple(transport(point) for point in ALPOEGE_POINTS)
    source_images = tuple(_evaluate(ALPOEGE, point) for point in ALPOEGE_POINTS)
    result_images = tuple(_evaluate(components, point) for point in transported)
    padded_image = ALPOEGE_IMAGE + (sp.Integer(0),) * len(w)

    broken = STEPS[:6] + (replace(STEPS[6], coefficient=8),) + STEPS[7:]
    broken_result = reconstruct(broken)

    checks = {
        "Alpoege's three points have the stated common image": all(
            image == ALPOEGE_IMAGE for image in source_images
        ),
        "Jacobian determinant of Alpoege's map is -2": _jacobian_determinant(ALPOEGE)
        == -2,
        "components agree with the published JSON": _agree(
            result, published_components
        ),
        "collision agrees with the published JSON": transported == published_points,
        "transported points have the padded common image": all(
            image == padded_image for image in result_images
        ),
        "dimension sequence is the reconstructed one": tuple(dimensions)
        == EXPECTED_DIMENSIONS,
        "degree sequence is the reconstructed one": tuple(degrees) == EXPECTED_DEGREES,
        "degree of the result is 3": degrees[-1] == 3,
        "dimension of the result is 19": dimensions[-1] == 19,
        "negative control rejects coefficient 8 in step 7": not _agree(
            tuple(broken_result[variable] for variable in VARIABLES),
            published_components,
        ),
    }

    print("Checks")
    for description, passed in checks.items():
        print(f"  [{'ok' if passed else 'FAILED'}] {description}")
    print()

    print("The introduction order is")
    print("  w1, w2, w4, w5, w8, w7, w9, w13,")
    print("  w16, w15, w14, w6, w12, w3, w11, w10.")
    print("Step 15 introduces w3 once and uses w3 + x*y**2 in both slots.")

    return 0 if all(checks.values()) else 1


def _degree(components: Components) -> int:
    variables = tuple(components)

    return int(
        max(
            sp.Poly(component, *variables).total_degree()
            for component in components.values()
        )
    )


def _evaluate(
    components: Components, point: tuple[sp.Expr, ...]
) -> tuple[sp.Expr, ...]:
    variables = tuple(variable for variable in VARIABLES if variable in components)
    substitution = dict(zip(variables, point, strict=True))

    return tuple(
        sp.expand(components[variable].xreplace(substitution)) for variable in variables
    )


def _jacobian_determinant(components: Components) -> sp.Expr:
    variables = tuple(components)
    matrix = sp.Matrix(
        [
            [sp.diff(components[row], column) for column in variables]
            for row in variables
        ]
    )

    return sp.expand(matrix.det())


def _agree(left: tuple[sp.Expr, ...], right: tuple[sp.Expr, ...]) -> bool:
    return all(sp.expand(a - b) == 0 for a, b in zip(left, right, strict=True))


if __name__ == "__main__":
    if len(sys.argv) > 2:
        raise SystemExit("usage: reconstruct_alpoege19.py [degree3_map.json]")
    argument = sys.argv[1] if len(sys.argv) == 2 else PUBLISHED_JSON
    raise SystemExit(main(argument))
