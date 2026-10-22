"""A certificate written to a file, and read back.

``docs/contracts.md`` states the format under "The certificate file", FMT-1 to
FMT-12. A file holds every map of a chain once, every step as the parameters of
its public constructor, collisions attached to maps by position, and a witness
that names its parts. It holds nothing that can be derived from them.

Three entry points. ``Certificate.dumps`` writes the text, ``Certificate.loads``
reads it, and ``Certificate.verify`` verifies the parts. Reading builds every
step through its public constructor, so a certificate read back is
``SUPPLIED`` whatever wrote it (FMT-10). That is what makes reading back a
control: the identities of the steps then compare a target from outside the
library with the formula, and they can fail.

Every refusal of a file is a ``VerificationError`` that cites an obligation and
names where in the file it failed. A constructor invariant that a file breaks
is cited by the identifier the constructor carries since work package 2.2, and
the constructor's exception is attached as the cause.

This module does not verify while it reads. The one exception is the target of
a ``DescentStep``, which the step derives and the file writes: the two are
compared, under FMT-4, because the object read back cannot hold both.
"""

from __future__ import annotations

import json
import math
import re
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from functools import partial
from typing import Any, NoReturn, cast

import sympy as sp
from sympy.polys.polyerrors import CoercionFailed
from sympy.polys.rings import PolyElement, PolyRing

from .bcw.homogenization import HomogenizationStep
from .bcw.step import BCWStep, Carried, Fresh
from .bcw.unipotent import UnipotentStep
from .collision import Collision
from .compression import CompressionStep
from .descent import DescentStep
from .elementary import ElementaryAutomorphism, ElementaryFactor
from .errors import InvariantError, VerificationError
from .lift import SymmetricLiftStep
from .linear import (
    Dilation,
    LinearAutomorphism,
    LinearFactor,
    Transposition,
    Transvection,
)
from .polynomial_map import PolynomialMap
from .reduction import LinearStep, Reduction, Step, TranslationStep
from .vanishing import VanishingWitness

FORMAT = "kellermap-certificate"
"""The value of the key ``format``, FMT-1."""

VERSION = 1
"""The only version this module reads and writes, FMT-1."""

BASES = ("ZZ", "QQ", "ZZ_I", "QQ_I")
"""The four bases of FMT-5, in the order FMT-8 tries them."""

ORDERS = ("lex", "grlex", "grevlex")
"""The monomial orders a file can name."""

NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
"""A name of a generator or a parameter, FMT-7."""

NUMBER = re.compile(r"-?(0|[1-9][0-9]*)(/[1-9][0-9]*)?")
"""The spelling of a number, FMT-6. The rest of the rule is checked after it."""

_BASE_DOMAINS: dict[str, Any] = {
    "ZZ": sp.ZZ,
    "QQ": sp.QQ,
    "ZZ_I": sp.ZZ_I,
    "QQ_I": sp.QQ_I,
}

# The proper inclusions between the four bases, FMT-8. A quadratic field holds
# ZZ and QQ and neither of the Gaussian domains, because its value -1 is
# excluded by FMT-5 and every other value gives a field without i.
_BASE_INCLUSIONS = {
    ("ZZ", "QQ"),
    ("ZZ", "ZZ_I"),
    ("ZZ", "QQ_I"),
    ("QQ", "QQ_I"),
    ("ZZ_I", "QQ_I"),
}

_STEP_FIELDS: dict[str, tuple[str, ...]] = {
    "BCWStep": ("index", "left", "right", "filtration_level", "coefficient"),
    "LinearStep": ("transformation", "normalizing"),
    "TranslationStep": ("shift", "normalizing"),
    "UnipotentStep": ("variables",),
    "HomogenizationStep": ("variable",),
    "CompressionStep": ("basis", "variables"),
    "SymmetricLiftStep": ("variables",),
    "DescentStep": ("index", "left", "right"),
}
"""The fields of each step type besides ``type``, FMT-3."""

Descriptor = Any
"""A domain as the file writes it: one of ``BASES``, or an object of FMT-5."""

Json = Any
"""A value as ``json`` reads it."""


# --------------------------------------------------------------------------
# The certificate
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Certificate:
    """A chain, the collisions of its maps, and a witness, as one object.

    Parameters
    ----------
    chain
        A ``Reduction``, or a single ``PolynomialMap`` when the certificate
        holds no step.
    collisions
        Pairs of a position and a collision. Position ``0`` is the source of
        the chain and position ``i + 1`` the target of step ``i``.
    witness
        A ``VanishingWitness`` whose lift is a step of the chain and whose
        collision is attached to the target of that step, or ``None``.

    FMT-9 is checked here: a witness that is not part of the certificate, and a
    position that is not a map of it, raise ``InvariantError``.
    """

    chain: Reduction | PolynomialMap
    collisions: tuple[tuple[int, Collision], ...] = ()
    witness: VanishingWitness | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.chain, Reduction | PolynomialMap):
            raise TypeError("The chain must be a Reduction or a PolynomialMap.")

        pairs = tuple(tuple(pair) for pair in self.collisions)
        for pair in pairs:
            if len(pair) != 2 or not isinstance(pair[1], Collision):
                raise TypeError(
                    "Each collision is a pair of a position and a Collision."
                )
            position = pair[0]
            if isinstance(position, bool) or not isinstance(position, int):
                raise TypeError("A position must be an integer.")
            if not 0 <= position < len(self.maps):
                raise InvariantError(
                    "FMT-8",
                    f"Position {position} is not a map of this certificate, "
                    f"which has {len(self.maps)}.",
                )
        object.__setattr__(self, "collisions", pairs)

        if self.witness is not None:
            if not isinstance(self.witness, VanishingWitness):
                raise TypeError("The witness must be a VanishingWitness.")
            if self._witness_indices() is None:
                raise InvariantError(
                    "FMT-9",
                    "The witness is not part of this certificate: its lift has "
                    "to be a step of the chain, and its collision has to be "
                    "attached to the target of that step.",
                )

    @property
    def steps(self) -> tuple[Step, ...]:
        """Return the steps of the chain, none for a single map."""
        if isinstance(self.chain, Reduction):
            return self.chain.steps

        return ()

    @property
    def maps(self) -> tuple[PolynomialMap, ...]:
        """Return the source of the chain followed by the target of every step."""
        if isinstance(self.chain, PolynomialMap):
            return (self.chain,)

        return (self.chain.source,) + tuple(step.target for step in self.steps)

    def _witness_indices(self) -> tuple[int, int] | None:
        """Return the step and the collision the witness is, or ``None``."""
        witness = self.witness
        assert witness is not None  # noqa: S101 - only called with a witness
        for index, step in enumerate(self.steps):
            if step != witness.lift:
                continue
            for number, (position, collision) in enumerate(self.collisions):
                if position == index + 1 and collision == witness.collision:
                    return index, number

        return None

    def verify(self) -> None:
        """Verify the chain, each collision against its map, and the witness.

        FMT-11. Nothing is computed beyond what the parts verify. A failure
        keeps the obligation of the part and names where it failed: the step
        by RED-4, or the collision, or the witness.
        """
        if isinstance(self.chain, Reduction):
            self.chain.verify()

        maps = self.maps
        for number, (position, collision) in enumerate(self.collisions):
            try:
                collision.verify(maps[position])
            except VerificationError as failure:
                raise VerificationError(
                    failure.obligation,
                    failure.message,
                    location=f"collision {number}",
                ) from failure

        if self.witness is not None:
            try:
                self.witness.verify()
            except VerificationError as failure:
                raise VerificationError(
                    failure.obligation, failure.message, location="witness"
                ) from failure

    def dumps(self) -> str:
        """Return the text of the file, FMT-12.

        A map or a collision over a domain FMT-5 does not admit, and a name
        FMT-7 does not admit, is refused with a ``VerificationError``.
        """
        maps = self.maps
        document: dict[str, Json] = {
            "format": FORMAT,
            "version": VERSION,
            "maps": [
                _encode_map(polynomial_map, f"map {index}")
                for index, polynomial_map in enumerate(maps)
            ],
            "steps": [
                _encode_step(step, f"step {index}")
                for index, step in enumerate(self.steps)
            ],
            "collisions": [
                _encode_collision(
                    position, maps[position], collision, f"collision {number}"
                )
                for number, (position, collision) in enumerate(self.collisions)
            ],
        }

        if self.witness is not None:
            indices = self._witness_indices()
            assert indices is not None  # noqa: S101 - FMT-9, checked on construction
            document["witness"] = {
                "step": indices[0],
                "collision": indices[1],
                "depth": self.witness.depth,
            }

        return _text(document)

    @classmethod
    def loads(cls, text: str) -> Certificate:
        """Read a certificate from the text of a file.

        Every step is built through its public constructor and is
        ``SUPPLIED``, FMT-10. Nothing is verified, except that the target a
        ``DescentStep`` derives is compared with the map the file writes,
        FMT-4. Call ``verify()`` on the result.
        """
        return _read(text)


# --------------------------------------------------------------------------
# Writing
# --------------------------------------------------------------------------


def _text(document: Json) -> str:
    """Return the text of FMT-12: sorted keys, no whitespace, a final newline."""
    return (
        json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        + "\n"
    )


def _refuse(obligation: str, location: str, message: str) -> NoReturn:
    raise VerificationError(obligation, message, location=location)


def _name(symbol: sp.Symbol, location: str) -> str:
    """Return the name of a symbol, or refuse it under FMT-7."""
    name = str(symbol.name)
    if not NAME.fullmatch(name):
        _refuse("FMT-7", location, f"The name {name!r} is not one a file can hold.")
    if symbol != sp.Symbol(name):
        _refuse(
            "FMT-7",
            location,
            f"The symbol {name} carries assumptions. It would be read back as a "
            "plain symbol, and the map read back would not equal the map written.",
        )

    return name


def _order(order: Any, location: str) -> str:
    alias = getattr(order, "alias", None)
    if alias not in ORDERS:
        _refuse(
            "FMT-1", location, f"The monomial order {order} is not one a file can name."
        )

    return cast(str, alias)


def _describe(domain: Any, location: str) -> Descriptor:
    """Return the domain of a map as the file writes it, or refuse it, FMT-5.

    A quadratic field is not among them: FMT-5 admits it for collisions only,
    and ``_collision_domain`` chooses that one.
    """
    for name, base in _BASE_DOMAINS.items():
        if domain == base:
            return name

    if domain.is_PolynomialRing or domain.is_FractionField:
        base = _describe(domain.domain, location)
        if base not in BASES:
            _refuse(
                "FMT-5", location, f"The domain {domain} is not over one of {BASES}."
            )
        inner = domain.ring if domain.is_PolynomialRing else domain.field
        return {
            "polynomial" if domain.is_PolynomialRing else "fraction": base,
            "parameters": [_name(symbol, location) for symbol in domain.symbols],
            "order": _order(inner.order, location),
        }

    _refuse("FMT-5", location, f"The domain {domain} is not one a file can hold.")


def _number(value: Any) -> str:
    """Return a rational number in the spelling of FMT-6."""
    rational = sp.Rational(int(value.numerator), int(value.denominator))
    if rational.q == 1:
        return str(rational.p)

    return f"{rational.p}/{rational.q}"


def _encode_element(domain: Any, descriptor: Descriptor, element: Any) -> Json:
    """Return an element of a domain as the table of FMT-5 writes it."""
    if descriptor == "ZZ":
        return str(int(element))
    if descriptor == "QQ":
        return _number(element)
    if descriptor in ("ZZ_I", "QQ_I"):
        return [_number(sp.QQ.convert(element.x)), _number(sp.QQ.convert(element.y))]
    if "quadratic" in descriptor:
        coefficients = [sp.QQ.convert(value) for value in element.to_list()]
        b, a = ([sp.QQ.zero] * (2 - len(coefficients)) + coefficients)[-2:]
        return [_number(a), _number(b)]
    base = _BASE_DOMAINS[
        descriptor["polynomial" if "polynomial" in descriptor else "fraction"]
    ]
    if "polynomial" in descriptor:
        return _encode_polynomial(base, descriptor["polynomial"], element)

    return {
        "numerator": _encode_polynomial(base, descriptor["fraction"], element.numer),
        "denominator": _encode_polynomial(base, descriptor["fraction"], element.denom),
    }


def _encode_polynomial(
    domain: Any, descriptor: Descriptor, polynomial: PolyElement
) -> Json:
    """Return the terms of a polynomial, sorted as FMT-12 asks."""
    terms = sorted(polynomial.terms(), key=lambda term: tuple(term[0]), reverse=True)

    return [
        [list(monomial), _encode_element(domain, descriptor, coefficient)]
        for monomial, coefficient in terms
    ]


def _element_of(domain: Any, value: Any) -> Any:
    """Return an expression a step reports as an element of ``domain``.

    Every coefficient, shift and basis entry a step reports is an expression,
    since the steps hand out expressions at their public boundary.
    """
    return domain.from_sympy(sp.sympify(value))


def _encode_ring(ring: PolyRing, location: str) -> Json:
    return {
        "generators": [_name(symbol, location) for symbol in ring.symbols],
        "order": _order(ring.order, location),
        "domain": _describe(ring.domain, location),
    }


def _encode_map(polynomial_map: PolynomialMap, location: str) -> Json:
    ring = polynomial_map.ring
    encoded = _encode_ring(ring, location)
    descriptor = encoded["domain"]

    return {
        "ring": encoded,
        "components": [
            _encode_polynomial(ring.domain, descriptor, component)
            for component in polynomial_map.to_polynomials()
        ],
    }


def _encode_step(step: Step, location: str) -> Json:
    """Return a step as the parameters of its public constructor, FMT-3."""
    ring = step.source.ring
    domain = ring.domain
    descriptor = _describe(domain, location)

    def element(value: Any) -> Json:
        return _encode_element(domain, descriptor, _element_of(domain, value))

    def polynomial(expression: sp.Expr) -> Json:
        return _encode_polynomial(
            domain, descriptor, ring.from_expr(sp.sympify(expression))
        )

    def names(symbols: Iterable[sp.Symbol]) -> Json:
        return [_name(symbol, location) for symbol in symbols]

    fields: dict[str, Json]
    if isinstance(step, BCWStep):
        slots: list[Json] = []
        for slot in (step.left, step.right):
            if isinstance(slot, Fresh):
                slots.append(
                    {
                        "fresh": {
                            "polynomial": polynomial(slot.polynomial),
                            "variable": _name(slot.variable, location),
                        }
                    }
                )
            else:
                slots.append({"carried": slot.index})
        fields = {
            "index": step.index,
            "left": slots[0],
            "right": slots[1],
            "filtration_level": int(step.filtration_level),
            "coefficient": element(step.coefficient),
        }
    elif isinstance(step, LinearStep):
        fields = {
            "transformation": [
                _encode_linear_factor(factor, element)
                for factor in step.transformation.factors
            ],
            "normalizing": step.is_normalizing,
        }
    elif isinstance(step, TranslationStep):
        fields = {
            "shift": [element(value) for value in step.shift],
            "normalizing": step.is_normalizing,
        }
    elif isinstance(step, UnipotentStep | SymmetricLiftStep):
        fields = {"variables": names(step.variables)}
    elif isinstance(step, HomogenizationStep):
        fields = {"variable": _name(step.variable, location)}
    elif isinstance(step, CompressionStep):
        fields = {
            "basis": [[element(value) for value in row] for row in step.basis],
            "variables": names(step.variables),
        }
    elif isinstance(step, DescentStep):
        fields = {
            "index": step.index,
            "left": [
                {"index": factor.index, "polynomial": polynomial(factor.polynomial)}
                for factor in step.left.factors
            ],
            "right": [
                {"index": factor.index, "polynomial": polynomial(factor.polynomial)}
                for factor in step.right.factors
            ],
        }
    else:
        _refuse("FMT-3", location, f"A {type(step).__name__} has no form in a file.")

    return {"type": type(step).__name__, **fields}


def _encode_linear_factor(factor: LinearFactor, element: Callable[[Any], Json]) -> Json:
    if isinstance(factor, Transvection):
        return {
            "transvection": {
                "index": factor.index,
                "source": factor.source,
                "coefficient": element(factor.coefficient),
            }
        }
    if isinstance(factor, Transposition):
        first, second = factor.indices
        return {"transposition": {"first": first, "second": second}}

    dilation = cast(Dilation, factor)
    return {
        "dilation": {
            "index": dilation.index,
            "coefficient": element(dilation.coefficient),
        }
    }


def _encode_collision(
    position: int, polynomial_map: PolynomialMap, collision: Collision, location: str
) -> Json:
    """Return a collision over the domain FMT-8 chooses, its points sorted."""
    descriptor, domain = _collision_domain(polynomial_map, collision, location)

    def point(coordinates: Iterable[sp.Expr]) -> Json:
        return [
            _encode_element(domain, descriptor, domain.from_sympy(value))
            for value in coordinates
        ]

    points = sorted((point(entry) for entry in collision.points), key=_text)

    return {
        "map": position,
        "domain": descriptor,
        "points": points,
        "image": point(collision.image),
    }


def _collision_domain(
    polynomial_map: PolynomialMap, collision: Collision, location: str
) -> tuple[Descriptor, Any]:
    """Return the first domain of FMT-8 that holds the map and the coordinates."""
    inner = _describe(polynomial_map.ring.domain, location)
    coordinates = [value for entry in collision.points for value in entry]
    coordinates += list(collision.image)

    for descriptor in _candidates(inner, coordinates):
        if not _contains(descriptor, inner):
            continue
        domain = _build_domain(descriptor)
        if all(_converts(domain, value) for value in coordinates):
            return descriptor, domain

    _refuse(
        "FMT-5",
        location,
        "No domain a file can hold contains the coordinates of this collision "
        f"and the domain {polynomial_map.ring.domain} of its map.",
    )


def _candidates(inner: Descriptor, coordinates: list[sp.Expr]) -> list[Descriptor]:
    """Return the domains of FMT-8 in the order ``dumps`` tries them."""
    if isinstance(inner, str):
        quadratic: list[Descriptor] = [
            {"quadratic": str(d)}
            for d in sorted(
                {d for value in coordinates for d in _square_free_candidates(value)}
            )
        ]
        return list(BASES) + quadratic

    rest = {"parameters": inner["parameters"], "order": inner["order"]}

    return [{"polynomial": base, **rest} for base in BASES] + [
        {"fraction": base, **rest} for base in BASES
    ]


def _square_free_candidates(value: sp.Expr) -> set[int]:
    """Return every square-free ``d`` whose root could write ``value``.

    The square roots of rationals in ``value``, read as integers, and their
    negatives where ``i`` occurs. Excluded are ``0``, ``1`` and ``-1``, which
    FMT-5 does not admit as a quadratic field.
    """
    expression = sp.sympify(value)
    radicands = set()
    for power in expression.atoms(sp.Pow):
        if power.exp == sp.Rational(1, 2) and power.base.is_Rational:
            radicand = sp.Rational(power.base)
            radicands.add(int(radicand.p * radicand.q))
    if expression.has(sp.I):
        radicands |= {-r for r in radicands} | {-1}

    return {d for d in (_square_free_part(r) for r in radicands) if d not in (0, 1, -1)}


def _square_free_part(value: int) -> int:
    sign = -1 if value < 0 else 1
    part = 1
    for prime, exponent in sp.factorint(abs(value)).items():
        if exponent % 2:
            part *= prime

    return sign * part


def _converts(domain: Any, value: sp.Expr) -> bool:
    try:
        domain.from_sympy(sp.sympify(value))
    except (CoercionFailed, ValueError, TypeError):
        return False

    return True


# --------------------------------------------------------------------------
# Domains, shared by writing and reading
# --------------------------------------------------------------------------


def _contains(outer: Descriptor, inner: Descriptor) -> bool:
    """Return whether ``outer`` contains ``inner`` by the rules of FMT-8."""
    if outer == inner:
        return True

    if isinstance(inner, str):
        if isinstance(outer, str):
            return (inner, outer) in _BASE_INCLUSIONS
        if "quadratic" in outer:
            return inner in ("ZZ", "QQ")
        base = outer.get("polynomial", outer.get("fraction"))
        return base == inner or (inner, base) in _BASE_INCLUSIONS

    if isinstance(outer, str) or "quadratic" in outer or "quadratic" in inner:
        return False
    if (outer["parameters"], outer["order"]) != (inner["parameters"], inner["order"]):
        return False

    outer_kind = "polynomial" if "polynomial" in outer else "fraction"
    inner_kind = "polynomial" if "polynomial" in inner else "fraction"
    if outer_kind == "polynomial" and inner_kind == "fraction":
        return False

    outer_base, inner_base = outer[outer_kind], inner[inner_kind]

    return outer_base == inner_base or (inner_base, outer_base) in _BASE_INCLUSIONS


def _build_domain(descriptor: Descriptor) -> Any:
    """Return the SymPy domain a valid descriptor names."""
    if isinstance(descriptor, str):
        return _BASE_DOMAINS[descriptor]
    if "quadratic" in descriptor:
        return sp.QQ.algebraic_field(sp.sqrt(int(descriptor["quadratic"])))

    kind = "polynomial" if "polynomial" in descriptor else "fraction"
    base = _BASE_DOMAINS[descriptor[kind]]
    symbols = [sp.Symbol(name) for name in descriptor["parameters"]]
    if kind == "polynomial":
        return base.poly_ring(*symbols, order=descriptor["order"])

    return base.frac_field(*symbols, order=descriptor["order"])


# --------------------------------------------------------------------------
# Reading
# --------------------------------------------------------------------------


def _read(text: str) -> Certificate:
    document = _parse(text)
    _keys(
        document,
        {"format", "version", "maps", "steps", "collisions"},
        {"witness"},
        "file",
    )
    if document["format"] != FORMAT:
        _refuse(
            "FMT-1", "file", f"The format is {document['format']!r}, not {FORMAT!r}."
        )
    if _integer(document["version"], "file") != VERSION:
        _refuse("FMT-1", "file", f"Version {document['version']} is not {VERSION}.")

    entries = _list(document["maps"], "file")
    plans = _list(document["steps"], "file")
    if len(entries) != len(plans) + 1:
        _refuse(
            "FMT-2",
            "file",
            f"The file has {len(entries)} maps and {len(plans)} steps; it needs "
            "one map more than steps.",
        )

    read = [_read_map(entry, f"map {index}") for index, entry in enumerate(entries)]
    maps = [polynomial_map for polynomial_map, _ in read]
    descriptors = [descriptor for _, descriptor in read]

    steps: list[Step] = []
    for index, plan in enumerate(plans):
        location = f"step {index}"
        step = _read_step(plan, maps[index], maps[index + 1], location)
        if isinstance(step, DescentStep):
            try:
                derived = step.target
            except VerificationError as failure:
                raise VerificationError(
                    failure.obligation, failure.message, location=location
                ) from failure
            if derived != maps[index + 1]:
                _refuse(
                    "DSC-1",
                    location,
                    f"The target the descent derives is not map {index + 1} of "
                    "the file.",
                )
        steps.append(step)

    collisions = [
        _read_collision(entry, maps, descriptors, f"collision {number}")
        for number, entry in enumerate(_list(document["collisions"], "file"))
    ]

    chain: Reduction | PolynomialMap = Reduction(steps) if steps else maps[0]
    witness = None
    if "witness" in document:
        witness = _read_witness(document["witness"], steps, collisions)

    return Certificate(chain, tuple(collisions), witness)


def _parse(text: str) -> Json:
    """Read JSON and refuse what FMT-1 and FMT-6 exclude at that level."""

    def pairs(items: list[tuple[str, Json]]) -> dict[str, Json]:
        found: dict[str, Json] = {}
        for key, value in items:
            if key in found:
                _refuse("FMT-1", "file", f"The key {key!r} occurs twice in one object.")
            found[key] = value
        return found

    def constant(name: str) -> NoReturn:
        _refuse(
            "FMT-1", "file", f"{name} is not a value of JSON and not one of a file."
        )

    def number(spelling: str) -> NoReturn:
        _refuse(
            "FMT-6",
            "file",
            f"The number {spelling} is a float. A file writes every coefficient "
            "as a string, and a float would be a different number.",
        )

    try:
        document = json.loads(
            text, object_pairs_hook=pairs, parse_constant=constant, parse_float=number
        )
    except json.JSONDecodeError as failure:
        raise VerificationError(
            "FMT-1", f"The text is not JSON: {failure}.", location="file"
        ) from failure

    return _object(document, "file")


def _object(value: Json, location: str) -> dict[str, Json]:
    if not isinstance(value, dict):
        _refuse("FMT-1", location, f"Expected an object, got {type(value).__name__}.")

    return value


def _list(value: Json, location: str) -> list[Json]:
    if not isinstance(value, list):
        _refuse("FMT-1", location, f"Expected a list, got {type(value).__name__}.")

    return value


def _string(value: Json, location: str) -> str:
    if not isinstance(value, str):
        _refuse("FMT-1", location, f"Expected a string, got {type(value).__name__}.")

    return value


def _integer(value: Json, location: str) -> int:
    """Return a JSON integer. A boolean is refused, although Python reads it as one."""
    if isinstance(value, bool) or not isinstance(value, int):
        _refuse("FMT-1", location, f"Expected an integer, got {type(value).__name__}.")

    return value


def _boolean(value: Json, location: str) -> bool:
    if not isinstance(value, bool):
        _refuse("FMT-1", location, f"Expected a boolean, got {type(value).__name__}.")

    return value


def _keys(
    value: Json, required: set[str], optional: set[str], location: str
) -> dict[str, Json]:
    """Return an object whose keys are the required ones and some optional ones."""
    found = _object(value, location)
    missing = required - set(found)
    unknown = set(found) - required - optional
    if missing or unknown:
        _refuse(
            "FMT-1",
            location,
            f"The object misses {sorted(missing)} and has the unknown keys "
            f"{sorted(unknown)}.",
        )

    return found


def _names(value: Json, location: str) -> list[str]:
    names = [_string(name, location) for name in _list(value, location)]
    for name in names:
        if not NAME.fullmatch(name):
            _refuse("FMT-7", location, f"The name {name!r} is not one a file can hold.")

    return names


def _read_order(value: Json, location: str) -> str:
    order = _string(value, location)
    if order not in ORDERS:
        _refuse(
            "FMT-1", location, f"The monomial order {order!r} is not one of {ORDERS}."
        )

    return order


def _read_descriptor(value: Json, location: str, quadratic: bool) -> Descriptor:
    """Return a domain descriptor after checking it against FMT-5 and FMT-7."""
    if isinstance(value, str):
        if value not in BASES:
            _refuse("FMT-5", location, f"The domain {value!r} is not one of {BASES}.")
        return value

    found = _object(value, location)
    if "quadratic" in found:
        _keys(found, {"quadratic"}, set(), location)
        if not quadratic:
            _refuse(
                "FMT-5",
                location,
                "A quadratic field is admitted for the coordinates of a "
                "collision only, not for a map.",
            )
        p, q = _read_number(found["quadratic"], location)
        if q != 1 or p in (0, 1, -1) or _square_free_part(p) != p:
            _refuse(
                "FMT-5",
                location,
                f"The value {found['quadratic']} is not a square-free integer "
                "other than 0, 1 and -1.",
            )
        return {"quadratic": str(p)}

    kind = "polynomial" if "polynomial" in found else "fraction"
    _keys(found, {kind, "parameters", "order"}, set(), location)
    base = _string(found[kind], location)
    if base not in BASES:
        _refuse("FMT-5", location, f"The base {base!r} is not one of {BASES}.")
    parameters = _names(found["parameters"], location)
    if not parameters or len(set(parameters)) != len(parameters):
        _refuse(
            "FMT-7", location, "The parameters of a domain are distinct and not none."
        )

    return {
        kind: base,
        "parameters": parameters,
        "order": _read_order(found["order"], location),
    }


def _read_number(value: Json, location: str) -> tuple[int, int]:
    """Return ``(p, q)`` for a ``NUMBER`` of FMT-6, or refuse it."""
    spelling = _string(value, location)
    if not NUMBER.fullmatch(spelling) or spelling.startswith("-0"):
        _refuse(
            "FMT-6",
            location,
            f"{spelling!r} is not a number in the spelling of a file.",
        )

    numerator, _, denominator = spelling.partition("/")
    p, q = int(numerator), int(denominator or "1")
    if denominator and (q < 2 or math.gcd(p, q) != 1):
        _refuse(
            "FMT-6",
            location,
            f"{spelling} is not in lowest terms with a denominator above one.",
        )

    return p, q


def _read_rational(value: Json, location: str) -> sp.Rational:
    p, q = _read_number(value, location)

    return sp.Rational(p, q)


def _read_element(
    domain: Any, descriptor: Descriptor, value: Json, location: str
) -> Any:
    """Return an element of ``domain``, read by the table of FMT-5."""
    if descriptor == "ZZ":
        p, q = _read_number(value, location)
        if q != 1:
            _refuse("FMT-6", location, f"{value} is not an integer.")
        return domain(p)
    if descriptor == "QQ":
        p, q = _read_number(value, location)
        return domain(p, q)
    if isinstance(descriptor, str) or "quadratic" in descriptor:
        pair = _list(value, location)
        if len(pair) != 2:
            _refuse("FMT-1", location, "An element of this domain is a pair.")
        a, b = (_read_rational(entry, location) for entry in pair)
        if descriptor == "ZZ_I" and not (a.is_integer and b.is_integer):
            _refuse("FMT-6", location, f"{value} is not a Gaussian integer.")
        root = (
            sp.I
            if isinstance(descriptor, str)
            else sp.sqrt(int(descriptor["quadratic"]))
        )
        return domain.from_sympy(a + b * root)

    kind = "polynomial" if "polynomial" in descriptor else "fraction"
    base_name = descriptor[kind]
    base = _BASE_DOMAINS[base_name]
    if kind == "polynomial":
        return _read_polynomial(domain.ring, base, base_name, value, location)

    parts = _keys(value, {"numerator", "denominator"}, set(), location)
    field = domain.field
    numerator = _read_polynomial(
        field.ring, base, base_name, parts["numerator"], location
    )
    denominator = _read_polynomial(
        field.ring, base, base_name, parts["denominator"], location
    )
    if not denominator:
        _refuse("FMT-6", location, "A denominator of zero is refused.")

    return field.new(numerator, denominator)


def _read_polynomial(
    ring: PolyRing, domain: Any, descriptor: Descriptor, value: Json, location: str
) -> PolyElement:
    """Return a polynomial of ``ring`` with coefficients in ``domain``, FMT-6."""
    terms: dict[tuple[int, ...], Any] = {}
    for term in _list(value, location):
        pair = _list(term, location)
        if len(pair) != 2:
            _refuse(
                "FMT-1", location, "A term is an exponent vector and a coefficient."
            )
        exponents = tuple(
            _integer(entry, location) for entry in _list(pair[0], location)
        )
        if len(exponents) != ring.ngens:
            _refuse(
                "FMT-6",
                location,
                f"An exponent vector has {len(exponents)} entries for {ring.ngens} "
                "generators or parameters.",
            )
        if any(exponent < 0 for exponent in exponents):
            _refuse(
                "FMT-6", location, f"The exponent vector {list(exponents)} is negative."
            )
        if exponents in terms:
            _refuse(
                "FMT-6", location, f"Two terms have the exponents {list(exponents)}."
            )
        coefficient = _read_element(domain, descriptor, pair[1], location)
        if not coefficient:
            _refuse("FMT-6", location, "A term has the coefficient zero.")
        terms[exponents] = coefficient

    return cast(PolyElement, ring.from_dict(terms))


def _read_map(value: Json, location: str) -> tuple[PolynomialMap, Descriptor]:
    entry = _keys(value, {"ring", "components"}, set(), location)
    ring_entry = _keys(
        entry["ring"], {"generators", "order", "domain"}, set(), location
    )
    generators = _names(ring_entry["generators"], location)
    descriptor = _read_descriptor(ring_entry["domain"], location, quadratic=False)
    parameters = [] if isinstance(descriptor, str) else descriptor["parameters"]
    if not generators or len(set(generators + parameters)) != len(
        generators + parameters
    ):
        _refuse(
            "FMT-7",
            location,
            "The generators of a ring and the parameters of its domain are "
            "distinct by name, and a ring has at least one generator.",
        )
    domain = _build_domain(descriptor)
    ring = PolyRing(
        [sp.Symbol(name) for name in generators],
        domain,
        _read_order(ring_entry["order"], location),
    )
    components = _list(entry["components"], location)
    if len(components) != len(generators):
        _refuse("FMT-1", location, "A map has one component per generator.")

    polynomial_map = PolynomialMap.from_ring(
        ring,
        [
            _read_polynomial(ring, domain, descriptor, component, location)
            for component in components
        ],
    )

    return polynomial_map, descriptor


def _built(location: str, build: Callable[[], Any], context: str | None = None) -> Any:
    """Call a constructor and translate its refusal, FMT-10.

    An ``InvariantError`` keeps its identifier. A plain ``ValueError`` comes
    from a factor type, which has no obligations of its own, and takes the
    identifier ``context`` names for it.
    """
    try:
        return build()
    except InvariantError as refusal:
        raise VerificationError(
            refusal.obligation, refusal.message, location=location
        ) from refusal
    except ValueError as refusal:
        if context is None:  # pragma: no cover - see below
            # Every ValueError of the constructor of a step, a collision and
            # a witness is an InvariantError since work package 2.2, and
            # tests/test_errors.py holds each of them to it. A plain one here
            # would be an invariant without an identifier, and it is raised
            # as it is rather than given one it does not have.
            raise
        raise VerificationError(context, str(refusal), location=location) from refusal


def _read_step(
    value: Json, source: PolynomialMap, target: PolynomialMap, location: str
) -> Step:
    found = _object(value, location)
    kind = _string(found.get("type"), location) if "type" in found else None
    if kind not in _STEP_FIELDS:
        _refuse(
            "FMT-1", location, f"The step type {kind!r} is not one a file can hold."
        )
    plan = _keys(found, {"type", *_STEP_FIELDS[kind]}, set(), location)

    ring = source.ring
    domain = ring.domain
    descriptor = _describe(domain, location)

    def element(entry: Json) -> sp.Expr:
        return domain.to_sympy(_read_element(domain, descriptor, entry, location))

    def polynomial(entry: Json) -> sp.Expr:
        return _read_polynomial(ring, domain, descriptor, entry, location).as_expr()

    def symbols(entry: Json) -> tuple[sp.Symbol, ...]:
        return tuple(sp.Symbol(name) for name in _names(entry, location))

    if kind == "BCWStep":
        slots = [
            _read_slot(plan[side], polynomial, location) for side in ("left", "right")
        ]
        index = _integer(plan["index"], location)
        level = _integer(plan["filtration_level"], location)
        coefficient = element(plan["coefficient"])
        return cast(
            Step,
            _built(
                location,
                lambda: BCWStep(
                    source, target, index, slots[0], slots[1], level, coefficient
                ),
            ),
        )
    if kind == "LinearStep":
        factors = [
            _read_linear_factor(entry, ring, element, location)
            for entry in _list(plan["transformation"], location)
        ]
        normalizing = _boolean(plan["normalizing"], location)
        return cast(
            Step,
            _built(
                location,
                lambda: LinearStep(
                    source, target, LinearAutomorphism(factors), normalizing
                ),
            ),
        )
    if kind == "TranslationStep":
        shift = [element(entry) for entry in _list(plan["shift"], location)]
        normalizing = _boolean(plan["normalizing"], location)
        return cast(
            Step,
            _built(
                location, lambda: TranslationStep(source, target, shift, normalizing)
            ),
        )
    if kind == "UnipotentStep":
        names = symbols(plan["variables"])
        return cast(
            Step, _built(location, lambda: UnipotentStep(source, target, names))
        )
    if kind == "HomogenizationStep":
        (variable,) = symbols([plan["variable"]])
        return cast(
            Step, _built(location, lambda: HomogenizationStep(source, target, variable))
        )
    if kind == "CompressionStep":
        basis = [
            tuple(element(entry) for entry in _list(row, location))
            for row in _list(plan["basis"], location)
        ]
        names = symbols(plan["variables"])
        return cast(
            Step,
            _built(
                location, lambda: CompressionStep(source, target, tuple(basis), names)
            ),
        )
    if kind == "SymmetricLiftStep":
        names = symbols(plan["variables"])
        return cast(
            Step, _built(location, lambda: SymmetricLiftStep(source, target, names))
        )

    index = _integer(plan["index"], location)
    sides = [
        _read_elementary(plan[side], ring, polynomial, location)
        for side in ("left", "right")
    ]
    return cast(
        Step, _built(location, lambda: DescentStep(source, index, sides[0], sides[1]))
    )


def _read_slot(
    value: Json, polynomial: Callable[[Json], sp.Expr], location: str
) -> Fresh | Carried:
    found = _object(value, location)
    if "carried" in found:
        _keys(found, {"carried"}, set(), location)
        index = _integer(found["carried"], location)
        return cast(Carried, _built(location, lambda: Carried(index)))

    _keys(found, {"fresh"}, set(), location)
    fresh = _keys(found["fresh"], {"polynomial", "variable"}, set(), location)
    (name,) = _names([fresh["variable"]], location)

    return Fresh(polynomial(fresh["polynomial"]), sp.Symbol(name))


def _read_linear_factor(
    value: Json, ring: PolyRing, element: Callable[[Json], sp.Expr], location: str
) -> LinearFactor:
    found = _object(value, location)
    kinds = {"transvection", "transposition", "dilation"} & set(found)
    if len(found) != 1 or not kinds:
        _refuse("FMT-1", location, "A linear factor is one of three kinds.")
    (kind,) = kinds

    if kind == "transvection":
        fields = _keys(found[kind], {"index", "source", "coefficient"}, set(), location)
        index = _integer(fields["index"], location)
        other = _integer(fields["source"], location)
        coefficient = element(fields["coefficient"])
        return cast(
            LinearFactor,
            _built(
                location, lambda: Transvection(ring, index, other, coefficient), "LIN-2"
            ),
        )
    if kind == "transposition":
        fields = _keys(found[kind], {"first", "second"}, set(), location)
        first = _integer(fields["first"], location)
        second = _integer(fields["second"], location)
        return cast(
            LinearFactor,
            _built(location, lambda: Transposition(ring, first, second), "LIN-2"),
        )

    fields = _keys(found[kind], {"index", "coefficient"}, set(), location)
    index = _integer(fields["index"], location)
    coefficient = element(fields["coefficient"])
    return cast(
        LinearFactor,
        _built(location, lambda: Dilation(ring, index, coefficient), "LIN-2"),
    )


def _read_elementary(
    value: Json, ring: PolyRing, polynomial: Callable[[Json], sp.Expr], location: str
) -> ElementaryAutomorphism:
    factors = []
    for entry in _list(value, location):
        fields = _keys(entry, {"index", "polynomial"}, set(), location)
        index = _integer(fields["index"], location)
        expression = polynomial(fields["polynomial"])
        factors.append(
            _built(
                location, partial(ElementaryFactor, ring, index, expression), "DSC-4"
            )
        )

    return ElementaryAutomorphism(factors)


def _read_collision(
    value: Json,
    maps: list[PolynomialMap],
    descriptors: list[Descriptor],
    location: str,
) -> tuple[int, Collision]:
    entry = _keys(value, {"map", "domain", "points", "image"}, set(), location)
    position = _integer(entry["map"], location)
    if not 0 <= position < len(maps):
        _refuse("FMT-8", location, f"Position {position} is not a map of the file.")

    descriptor = _read_descriptor(entry["domain"], location, quadratic=True)
    parameters = [] if isinstance(descriptor, str) else descriptor.get("parameters", [])
    taken = set(parameters) & {str(name) for name in maps[position].variables}
    if taken:
        _refuse(
            "FMT-7",
            location,
            f"The parameters {sorted(taken)} of the collision's domain are "
            "generators of its map. That is COL-2 in the terms of the file.",
        )
    if not _contains(descriptor, descriptors[position]):
        _refuse(
            "FMT-8",
            location,
            "The domain of the collision does not contain the domain of map "
            f"{position}.",
        )

    domain = _build_domain(descriptor)

    def point(coordinates: Json) -> tuple[sp.Expr, ...]:
        return tuple(
            domain.to_sympy(_read_element(domain, descriptor, coordinate, location))
            for coordinate in _list(coordinates, location)
        )

    points = [point(coordinates) for coordinates in _list(entry["points"], location)]
    image = point(entry["image"])

    return position, cast(Collision, _built(location, lambda: Collision(points, image)))


def _read_witness(
    value: Json, steps: list[Step], collisions: list[tuple[int, Collision]]
) -> VanishingWitness:
    entry = _keys(value, {"step", "collision", "depth"}, set(), "witness")
    index = _integer(entry["step"], "witness")
    number = _integer(entry["collision"], "witness")
    depth = _integer(entry["depth"], "witness")

    if not 0 <= index < len(steps) or not isinstance(steps[index], SymmetricLiftStep):
        _refuse(
            "FMT-9", "witness", f"Step {index} is not a SymmetricLiftStep of the file."
        )
    if not 0 <= number < len(collisions) or collisions[number][0] != index + 1:
        _refuse(
            "FMT-9",
            "witness",
            f"Collision {number} is not attached to the target of step {index}.",
        )

    lift = cast(SymmetricLiftStep, steps[index])
    collision = collisions[number][1]

    return cast(
        VanishingWitness,
        _built("witness", lambda: VanishingWitness(lift, collision, depth)),
    )
