"""The file of FMT-1 to FMT-9, read without ``kellermap``.

This module reads the text, refuses what the format refuses, and returns plain
objects: the maps as polynomials of SymPy rings, the steps as their fields,
the collisions as points of a SymPy domain, and the witness as three numbers.
It checks no obligation of a step, a collision or a witness. Those are in
``_checks``.

What it refuses, in the order it refuses it: the JSON itself, the keys and the
version, every map in the order of the file, the shape of every step, every
collision, and the witness. A refusal cites the rule of the format that failed
and the place in the file.
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from typing import Any, NoReturn

import sympy as sp
from sympy.polys.rings import PolyElement, PolyRing

from ._report import Refusal

MARKER = "kellermap-certificate"
BASES = {"ZZ": sp.ZZ, "QQ": sp.QQ, "ZZ_I": sp.ZZ_I, "QQ_I": sp.QQ_I}
ORDERS = ("lex", "grlex", "grevlex")
NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
NUMBER = re.compile(r"(-?)(0|[1-9][0-9]*)(?:/([1-9][0-9]*))?")

# Which base lies in which, FMT-8. A base lies in itself as well.
INSIDE = {
    "ZZ": {"ZZ", "QQ", "ZZ_I", "QQ_I"},
    "QQ": {"QQ", "QQ_I"},
    "ZZ_I": {"ZZ_I", "QQ_I"},
    "QQ_I": {"QQ_I"},
}

FIELDS = {
    "BCWStep": {"index", "left", "right", "filtration_level", "coefficient"},
    "LinearStep": {"transformation", "normalizing"},
    "TranslationStep": {"shift", "normalizing"},
    "UnipotentStep": {"variables"},
    "HomogenizationStep": {"variable"},
    "CompressionStep": {"basis", "variables"},
    "SymmetricLiftStep": {"variables"},
    "DescentStep": {"index", "left", "right"},
}


@dataclass(frozen=True)
class Domain:
    """A coefficient domain as the file names it, with its SymPy object."""

    kind: str  # "base", "quadratic", "polynomial" or "fraction"
    base: str  # one of BASES, or "QQ" for a quadratic field
    parameters: tuple[str, ...]
    order: str
    value: int  # d for a quadratic field, and 0 otherwise
    sympy: Any

    def contains(self, other: Domain) -> bool:
        """Return whether this domain contains ``other``, FMT-8."""
        if self.kind == "quadratic":
            return other.kind == "base" and other.base in ("ZZ", "QQ") or other == self
        if other.kind == "quadratic":  # pragma: no cover - FMT-5 keeps maps off it
            return False
        if self.kind == "base":
            return other.kind == "base" and self.base in INSIDE[other.base]
        same = (self.parameters, self.order) == (other.parameters, other.order)
        if other.kind == "base":
            return self.base in INSIDE[other.base]
        if self.kind == "polynomial" and other.kind == "fraction":
            return False

        return same and self.base in INSIDE[other.base]


@dataclass(frozen=True)
class Map:
    """A map of the file: its ring and its components."""

    names: tuple[str, ...]
    domain: Domain
    order: str
    ring: PolyRing
    components: tuple[PolyElement, ...]


@dataclass(frozen=True)
class Step:
    """A step of the file: its type and its fields, read but not checked."""

    kind: str
    fields: dict[str, Any]


@dataclass(frozen=True)
class Collision:
    """A collision of the file, over its own domain."""

    position: int
    domain: Domain
    points: tuple[tuple[Any, ...], ...]
    image: tuple[Any, ...]


@dataclass(frozen=True)
class Witness:
    step: int
    collision: int
    depth: int


@dataclass(frozen=True)
class Document:
    maps: tuple[Map, ...]
    steps: tuple[Step, ...]
    collisions: tuple[Collision, ...]
    witness: Witness | None


class _Reader:
    """Reads one part of the file and refuses it with that part's location."""

    def __init__(self, location: str) -> None:
        self.location = location

    def refuse(self, obligation: str, message: str) -> NoReturn:
        raise Refusal(obligation, self.location, message)

    def object(
        self, value: Any, keys: set[str], optional: frozenset[str] = frozenset()
    ) -> dict[str, Any]:
        if not isinstance(value, dict):
            self.refuse("FMT-1", f"an object was expected, not {type(value).__name__}")
        missing = keys - value.keys()
        unknown = value.keys() - keys - optional
        if missing or unknown:
            self.refuse(
                "FMT-1",
                f"missing keys {sorted(missing)}, unknown keys {sorted(unknown)}",
            )
        return value

    def list(self, value: Any) -> list[Any]:
        if not isinstance(value, list):
            self.refuse("FMT-1", f"a list was expected, not {type(value).__name__}")
        return value

    def integer(self, value: Any) -> int:
        # bool is a subclass of int in Python, and FMT-1 refuses it here.
        if type(value) is not int:
            self.refuse("FMT-1", f"an integer was expected, not {value!r}")
        return value

    def boolean(self, value: Any) -> bool:
        if type(value) is not bool:
            self.refuse("FMT-1", f"a boolean was expected, not {value!r}")
        return value

    def name(self, value: Any) -> str:
        if not isinstance(value, str):
            self.refuse("FMT-1", f"a name is a string, not {value!r}")
        if not NAME.fullmatch(value):
            self.refuse("FMT-7", f"{value!r} is not a name a file can hold")
        return value

    def names(self, value: Any) -> tuple[str, ...]:
        return tuple(self.name(entry) for entry in self.list(value))

    def order(self, value: Any) -> str:
        if value not in ORDERS:
            self.refuse("FMT-1", f"{value!r} is not one of the orders {ORDERS}")
        return str(value)

    def number(self, value: Any) -> sp.Rational:
        if not isinstance(value, str):
            self.refuse("FMT-1", f"a number is a string, not {value!r}")
        match = NUMBER.fullmatch(value)
        if match is None:
            self.refuse("FMT-6", f"{value!r} is not a number as a file writes one")
        sign, numerator, denominator = match.groups()
        if sign and numerator == "0":
            self.refuse("FMT-6", "zero is written 0")
        p = int(sign + numerator)
        q = int(denominator) if denominator else 1
        if denominator is not None and (q == 1 or math.gcd(p, q) != 1):
            self.refuse(
                "FMT-6", f"{value} is not in lowest terms with a denominator above one"
            )
        return sp.Rational(p, q)

    def domain(self, value: Any, quadratic: bool) -> Domain:
        if isinstance(value, str):
            if value not in BASES:
                self.refuse("FMT-5", f"{value!r} is not a domain a file can hold")
            return Domain("base", value, (), "", 0, BASES[value])
        if isinstance(value, dict) and "quadratic" in value:
            self.object(value, {"quadratic"})
            if not quadratic:
                self.refuse(
                    "FMT-5", "a quadratic field is admitted for a collision only"
                )
            d = self.number(value["quadratic"])
            if (
                d.q != 1
                or d in (0, 1, -1)
                or any(e > 1 for e in sp.factorint(abs(d.p)).values())
            ):
                self.refuse(
                    "FMT-5", f"{d} is not a square-free integer other than 0, 1 and -1"
                )
            return Domain(
                "quadratic", "QQ", (), "", int(d), sp.QQ.algebraic_field(sp.sqrt(d))
            )
        if not isinstance(value, dict):
            self.refuse("FMT-1", f"{value!r} is not a domain")
        kind = "polynomial" if "polynomial" in value else "fraction"
        entry = self.object(value, {kind, "parameters", "order"})
        base = entry[kind]
        if base not in BASES:
            self.refuse("FMT-5", f"{base!r} is not one of the bases {sorted(BASES)}")
        parameters = self.names(entry["parameters"])
        if not parameters or len(set(parameters)) != len(parameters):
            self.refuse(
                "FMT-7",
                "the parameters of a domain are distinct, and there is one at least",
            )
        order = self.order(entry["order"])
        symbols = [sp.Symbol(name) for name in parameters]
        built = (
            BASES[base].poly_ring(*symbols, order=order)
            if kind == "polynomial"
            else BASES[base].frac_field(*symbols, order=order)
        )
        return Domain(kind, base, parameters, order, 0, built)

    def element(self, domain: Domain, value: Any) -> Any:
        """Return an element of ``domain``, by the table of FMT-5."""
        target = domain.sympy
        if domain.kind == "base" and domain.base in ("ZZ", "QQ"):
            number = self.number(value)
            if domain.base == "ZZ" and number.q != 1:
                self.refuse("FMT-6", f"{value} is not an integer")
            return target.from_sympy(number)
        if domain.kind in ("base", "quadratic"):
            pair = self.list(value)
            if len(pair) != 2:
                self.refuse("FMT-1", "an element of this domain is a pair")
            a, b = self.number(pair[0]), self.number(pair[1])
            if domain.base == "ZZ_I" and (a.q != 1 or b.q != 1):
                self.refuse("FMT-6", f"{value} is not a Gaussian integer")
            root = sp.sqrt(domain.value) if domain.kind == "quadratic" else sp.I
            return target.from_sympy(a + b * root)
        base = Domain("base", domain.base, (), "", 0, BASES[domain.base])
        if domain.kind == "polynomial":
            return self.polynomial(target.ring, base, value)
        parts = self.object(value, {"numerator", "denominator"})
        field = target.field
        numerator = self.polynomial(field.ring, base, parts["numerator"])
        denominator = self.polynomial(field.ring, base, parts["denominator"])
        if not denominator:
            self.refuse("FMT-6", "a denominator is zero")
        return field.new(numerator, denominator)

    def polynomial(self, ring: PolyRing, domain: Domain, value: Any) -> PolyElement:
        """Return a polynomial of ``ring`` whose coefficients lie in ``domain``."""
        terms: dict[tuple[int, ...], Any] = {}
        for term in self.list(value):
            pair = self.list(term)
            if len(pair) != 2:
                self.refuse("FMT-1", "a term is an exponent vector and a coefficient")
            exponents = tuple(self.integer(entry) for entry in self.list(pair[0]))
            if len(exponents) != ring.ngens:
                self.refuse(
                    "FMT-6", f"{len(exponents)} exponents for {ring.ngens} generators"
                )
            if min(exponents, default=0) < 0:
                self.refuse("FMT-6", "an exponent is negative")
            if exponents in terms:
                self.refuse("FMT-6", "two terms have one exponent vector")
            coefficient = self.element(domain, pair[1])
            if not coefficient:
                self.refuse("FMT-6", "a term has the coefficient zero")
            terms[exponents] = coefficient
        return ring.from_dict(terms)


def _parse(text: str) -> Any:
    reader = _Reader("file")

    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        keys = [key for key, _ in items]
        if len(set(keys)) != len(keys):
            reader.refuse("FMT-1", "an object has one key twice")
        return dict(items)

    def constant(name: str) -> NoReturn:
        reader.refuse("FMT-1", f"{name} is not JSON")

    def floating(spelling: str) -> NoReturn:
        reader.refuse("FMT-6", f"{spelling} is a float, and a file writes no float")

    try:
        return json.loads(
            text, object_pairs_hook=pairs, parse_constant=constant, parse_float=floating
        )
    except json.JSONDecodeError as failure:
        raise Refusal("FMT-1", "file", f"the text is not JSON: {failure}") from failure


def _map(value: Any, location: str) -> Map:
    reader = _Reader(location)
    entry = reader.object(value, {"ring", "components"})
    ring_entry = reader.object(entry["ring"], {"generators", "order", "domain"})
    names = reader.names(ring_entry["generators"])
    domain = reader.domain(ring_entry["domain"], quadratic=False)
    order = reader.order(ring_entry["order"])
    every = names + domain.parameters
    if not names or len(set(every)) != len(every):
        reader.refuse(
            "FMT-7", "a ring has a generator, and its names and parameters are distinct"
        )
    ring = PolyRing([sp.Symbol(name) for name in names], domain.sympy, order)
    components = reader.list(entry["components"])
    if len(components) != len(names):
        reader.refuse("FMT-1", "a map has one component per generator")

    return Map(
        names,
        domain,
        order,
        ring,
        tuple(reader.polynomial(ring, domain, component) for component in components),
    )


def _slot(reader: _Reader, value: Any, source: Map) -> tuple[str, Any, Any]:
    if isinstance(value, dict) and "carried" in value:
        reader.object(value, {"carried"})
        return ("carried", reader.integer(value["carried"]), None)
    entry = reader.object(value, {"fresh"})
    fresh = reader.object(entry["fresh"], {"polynomial", "variable"})
    polynomial = reader.polynomial(source.ring, source.domain, fresh["polynomial"])

    return ("fresh", reader.name(fresh["variable"]), polynomial)


def _linear_factor(reader: _Reader, value: Any, source: Map) -> tuple[Any, ...]:
    if not isinstance(value, dict) or len(value) != 1:
        reader.refuse("FMT-1", "a linear factor is one object with one key")
    ((kind, fields),) = value.items()
    if kind == "transvection":
        entry = reader.object(fields, {"index", "source", "coefficient"})
        return (
            kind,
            reader.integer(entry["index"]),
            reader.integer(entry["source"]),
            reader.element(source.domain, entry["coefficient"]),
        )
    if kind == "transposition":
        entry = reader.object(fields, {"first", "second"})
        return (kind, reader.integer(entry["first"]), reader.integer(entry["second"]))
    if kind == "dilation":
        entry = reader.object(fields, {"index", "coefficient"})
        return (
            kind,
            reader.integer(entry["index"]),
            reader.element(source.domain, entry["coefficient"]),
        )

    reader.refuse("FMT-1", f"{kind!r} is not a linear factor")


def _step(value: Any, source: Map, location: str) -> Step:
    reader = _Reader(location)
    if not isinstance(value, dict) or value.get("type") not in FIELDS:
        reader.refuse("FMT-1", "a step names one of the step types")
    kind = value["type"]
    entry = reader.object(value, {"type", *FIELDS[kind]})
    fields: dict[str, Any] = {}

    if kind == "BCWStep":
        fields["index"] = reader.integer(entry["index"])
        fields["left"] = _slot(reader, entry["left"], source)
        fields["right"] = _slot(reader, entry["right"], source)
        fields["filtration_level"] = reader.integer(entry["filtration_level"])
        fields["coefficient"] = reader.element(source.domain, entry["coefficient"])
    elif kind == "LinearStep":
        fields["transformation"] = [
            _linear_factor(reader, factor, source)
            for factor in reader.list(entry["transformation"])
        ]
        fields["normalizing"] = reader.boolean(entry["normalizing"])
    elif kind == "TranslationStep":
        fields["shift"] = [
            reader.element(source.domain, value)
            for value in reader.list(entry["shift"])
        ]
        fields["normalizing"] = reader.boolean(entry["normalizing"])
    elif kind in ("UnipotentStep", "SymmetricLiftStep", "CompressionStep"):
        fields["variables"] = reader.names(entry["variables"])
        if kind == "CompressionStep":
            fields["basis"] = [
                [reader.element(source.domain, value) for value in reader.list(row)]
                for row in reader.list(entry["basis"])
            ]
    elif kind == "HomogenizationStep":
        fields["variable"] = reader.name(entry["variable"])
    else:
        fields["index"] = reader.integer(entry["index"])
        for side in ("left", "right"):
            factors = []
            for factor in reader.list(entry[side]):
                pair = reader.object(factor, {"index", "polynomial"})
                factors.append(
                    (
                        reader.integer(pair["index"]),
                        reader.polynomial(
                            source.ring, source.domain, pair["polynomial"]
                        ),
                    )
                )
            fields[side] = factors

    return Step(kind, fields)


def _collision(value: Any, maps: tuple[Map, ...], location: str) -> Collision:
    reader = _Reader(location)
    entry = reader.object(value, {"map", "domain", "points", "image"})
    position = reader.integer(entry["map"])
    if not 0 <= position < len(maps):
        reader.refuse("FMT-8", f"position {position} is not a map of the file")
    domain = reader.domain(entry["domain"], quadratic=True)
    if set(domain.parameters) & set(maps[position].names):
        reader.refuse(
            "FMT-7",
            "a parameter of the collision's domain is a generator of its map (COL-2)",
        )
    if not domain.contains(maps[position].domain):
        reader.refuse(
            "FMT-8", f"the domain does not contain the domain of map {position}"
        )

    def point(coordinates: Any) -> tuple[Any, ...]:
        return tuple(
            reader.element(domain, value) for value in reader.list(coordinates)
        )

    return Collision(
        position,
        domain,
        tuple(point(entry) for entry in reader.list(entry["points"])),
        point(entry["image"]),
    )


def read(text: str) -> Document:
    """Return the document a text holds, or raise ``Refusal``."""
    reader = _Reader("file")
    document = reader.object(
        _parse(text),
        {"format", "version", "maps", "steps", "collisions"},
        frozenset({"witness"}),
    )
    if document["format"] != MARKER:
        reader.refuse("FMT-1", f"the format is {document['format']!r}")
    if reader.integer(document["version"]) != 1:
        reader.refuse("FMT-1", f"version {document['version']} is not 1")

    entries = reader.list(document["maps"])
    plans = reader.list(document["steps"])
    if len(entries) != len(plans) + 1:
        reader.refuse("FMT-2", f"{len(entries)} maps and {len(plans)} steps")

    maps = tuple(_map(entry, f"map {index}") for index, entry in enumerate(entries))
    steps = tuple(
        _step(plan, maps[index], f"step {index}") for index, plan in enumerate(plans)
    )
    collisions = tuple(
        _collision(entry, maps, f"collision {number}")
        for number, entry in enumerate(reader.list(document["collisions"]))
    )

    witness = None
    if "witness" in document:
        found = _Reader("witness")
        entry = found.object(document["witness"], {"step", "collision", "depth"})
        step, number = found.integer(entry["step"]), found.integer(entry["collision"])
        depth = found.integer(entry["depth"])
        if not 0 <= step < len(steps) or steps[step].kind != "SymmetricLiftStep":
            found.refuse("FMT-9", f"step {step} is not a symmetric lift of the file")
        if not 0 <= number < len(collisions) or collisions[number].position != step + 1:
            found.refuse(
                "FMT-9",
                f"collision {number} is not attached to the target of step {step}",
            )
        witness = Witness(step, number, depth)

    return Document(maps, steps, collisions, witness)
