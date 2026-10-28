"""A LaTeX view of a certificate file, TEX-1 to TEX-6 of ``docs/contracts.md``.

``to_latex(text)`` checks the text with ``kellermap_check`` and, for the
verdict ``VERIFIED``, returns LaTeX that shows what the file holds: its maps,
its steps with their parameters, its collisions and its witness, and what the
checker's report says. The view checks nothing itself. It is a way to read a
file, and the file is the certificate.

The view is made from the text ``dumps`` writes for the certificate, TEX-3, so
it shows terms and points in the order of FMT-6 and FMT-12. The values are read
from that text with the reader of ``kellermap.certificate``, and only the form
of a witness is computed, from the lift, as TEX-2 allows.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable, Sequence
from typing import Any

import sympy as sp

import kellermap_check

from .certificate import (
    Certificate,
    Descriptor,
    Json,
    _build_domain,
    _encode_polynomial,
    _read_element,
)
from .errors import VerificationError

__all__ = ["MARKER", "to_latex"]

MARKER = "% A view of a kellermap certificate file that kellermap_check verified."
"""The first line of every view, TEX-4. It makes a view findable by its content."""

_SIMPLE_NAME = re.compile(r"([A-Za-z])([0-9]*)")

_BASES = {
    "ZZ": r"\mathbf{Z}",
    "QQ": r"\mathbf{Q}",
    "ZZ_I": r"\mathbf{Z}[\mathrm{i}]",
    "QQ_I": r"\mathbf{Q}(\mathrm{i})",
}

# The characters LaTeX reads as commands in text, TEX-6.
_TEXT_SPECIALS = {
    "\\": r"\textbackslash{}",
    "{": r"\{",
    "}": r"\}",
    "$": r"\$",
    "&": r"\&",
    "#": r"\#",
    "%": r"\%",
    "_": r"\_",
    "^": r"\^{}",
    "~": r"\~{}",
}


def to_latex(text: str, *, standalone: bool = True) -> str:
    """Return the LaTeX view of a certificate file, TEX-1 to TEX-6.

    The text is checked with ``kellermap_check`` first, and a file the checker
    refuses raises ``VerificationError`` with the identifier and the location
    of the refusal. With ``standalone=False`` the result is the body only, to
    be read into another document with ``\\input``.
    """
    try:
        report = kellermap_check.check(text)
    except kellermap_check.Refusal as refusal:
        raise VerificationError(
            refusal.obligation, refusal.message, location=refusal.location
        ) from refusal

    certificate = Certificate.loads(text)
    canonical = certificate.dumps()
    view = _View(json.loads(canonical), certificate, report)
    body = view.body()

    if not standalone:
        return f"{MARKER}\n{body}"

    return (
        f"{MARKER}\n"
        "\\documentclass{article}\n"
        "\\begin{document}\n"
        f"{body}"
        "\\end{document}\n"
    )


def name(identifier: str) -> str:
    """Return the LaTeX of one name, TEX-5.

    One letter and digits is the letter with the digits as a subscript. Any
    other name is itself in ``\\mathit``, its underscores escaped. The two
    shapes cannot meet: the first never holds an underscore or two letters.
    """
    simple = _SIMPLE_NAME.fullmatch(identifier)
    if simple:
        letter, digits = simple.groups()
        return f"{letter}_{{{digits}}}" if digits else letter

    return "\\mathit{" + identifier.replace("_", "\\_") + "}"


def text(words: str) -> str:
    """Return ``words`` with every character LaTeX reads as a command escaped."""
    return "".join(_TEXT_SPECIALS.get(character, character) for character in words)


def domain(descriptor: Descriptor) -> str:
    """Return the LaTeX of a coefficient domain as the file names it."""
    if isinstance(descriptor, str):
        return _BASES[descriptor]
    if "quadratic" in descriptor:
        return f"\\mathbf{{Q}}(\\sqrt{{{descriptor['quadratic']}}})"

    kind = "polynomial" if "polynomial" in descriptor else "fraction"
    parameters = ", ".join(name(entry) for entry in descriptor["parameters"])
    opening, closing = ("[", "]") if kind == "polynomial" else ("(", ")")

    return f"{_BASES[descriptor[kind]]}{opening}{parameters}{closing}"


def _normalizing(flag: bool) -> str:
    return "the step claims to normalize" if flag else "the step does not normalize"


def listing(entries: Iterable[str]) -> str:
    """Return entries separated by commas at which a line may break."""
    return ",\\allowbreak ".join(entries)


class _View:
    """The parts of one view, read from the canonical text of its file."""

    def __init__(self, document: Json, certificate: Certificate, report: Any) -> None:
        self.document = document
        self.certificate = certificate
        self.report = report
        self.symbols: dict[sp.Symbol, str] = {}
        for entry in document["maps"]:
            ring = entry["ring"]
            for identifier in ring["generators"]:
                self.symbols[sp.Symbol(identifier)] = name(identifier)
            if not isinstance(ring["domain"], str):
                for identifier in ring["domain"].get("parameters", ()):
                    self.symbols[sp.Symbol(identifier)] = name(identifier)

    # ----------------------------------------------------------------------
    # Values

    def value(self, descriptor: Descriptor, encoded: Json, location: str) -> str:
        """Return the LaTeX of one element of a domain, read as the file has it."""
        return self.number(self.coefficient(descriptor, encoded, location))

    def number(self, expression: sp.Expr) -> str:
        """Return the LaTeX of a coefficient, with the names of TEX-5."""
        return str(
            sp.latex(
                expression,
                symbol_names=self.symbols,
                imaginary_unit="ri",
                order="lex",
            )
        )

    def polynomial(
        self,
        terms: Json,
        generators: Sequence[str],
        descriptor: Descriptor,
        location: str,
    ) -> str:
        """Return a polynomial whose terms stand as the file writes them."""
        if not terms:
            return "0"

        written: list[str] = []
        for exponents, coefficient in terms:
            monomial = " ".join(
                name(generator) + (f"^{{{exponent}}}" if exponent > 1 else "")
                for generator, exponent in zip(generators, exponents, strict=True)
                if exponent
            )
            written.append(
                self.term(self.coefficient(descriptor, coefficient, location), monomial)
            )

        joined = written[0]
        for entry in written[1:]:
            joined += (
                f" - {entry[1:].lstrip()}" if entry.startswith("-") else f" + {entry}"
            )

        return joined

    def coefficient(
        self, descriptor: Descriptor, encoded: Json, location: str
    ) -> sp.Expr:
        """Return one element of a domain as a SymPy number, read by FMT-6."""
        built = _build_domain(descriptor)

        return built.to_sympy(_read_element(built, descriptor, encoded, location))

    def term(self, coefficient: sp.Expr, monomial: str) -> str:
        """Return one term: a coefficient and a monomial, signs written once."""
        if not monomial:
            return self.number(coefficient)
        if coefficient == 1:
            return monomial
        if coefficient == -1:
            return f"-{monomial}"
        if isinstance(coefficient, sp.Add):
            return f"\\left({self.number(coefficient)}\\right) {monomial}"

        return f"{self.number(coefficient)} {monomial}"

    # ----------------------------------------------------------------------
    # The document

    def body(self) -> str:
        # A group, so that ``\\sloppy`` ends with the view when it is read into
        # another document. It lets TeX break long lines of inline mathematics
        # at the breaks it has rather than run them past the margin.
        parts = [
            "\\begingroup\\sloppy\n",
            "\\section*{A certificate file}\n",
            "Indices count from zero, as in the file.\n\n",
            self.verdict(),
            self.maps(),
            self.steps(),
            self.collisions(),
            self.witness(),
            "\\par\\endgroup\n",
        ]

        return "".join(parts)

    def verdict(self) -> str:
        report = self.report
        lines = [
            "\\subsection*{What the checker verified}\n",
            "The verdict of \\texttt{kellermap\\_check} is "
            f"{text(report.verdict)}.\n",
        ]
        for heading, entries in (
            ("It confirmed", report.claims),
            ("The file does not claim", report.not_claimed),
            (
                "Not computed",
                [
                    f"{identifier}: {kellermap_check.NOT_COMPUTED[identifier]}"
                    for identifier in report.not_computed
                ],
            ),
        ):
            if entries:
                lines.append(f"\n{heading}:\n\\begin{{itemize}}\n")
                lines += [f"\\item {text(entry)}\n" for entry in entries]
                lines.append("\\end{itemize}\n")

        return "".join(lines) + "\n"

    def maps(self) -> str:
        lines = ["\\subsection*{Maps}\n"]
        for index, entry in enumerate(self.document["maps"]):
            ring = entry["ring"]
            generators = ring["generators"]
            location = f"map {index}"
            lines.append(
                f"\n\\paragraph{{Map {index}}} Generators "
                f"${listing(map(name, generators))}$, coefficients in "
                f"${domain(ring['domain'])}$, monomial order "
                f"{text(ring['order'])}.\n\n"
            )
            for position, terms in enumerate(entry["components"]):
                written = self.polynomial(terms, generators, ring["domain"], location)
                lines.append(f"\\noindent$F_{{{position}}} = {written}$\n\n")

        return "".join(lines)

    def steps(self) -> str:
        if not self.document["steps"]:
            return ""

        lines = ["\\subsection*{Steps}\n"]
        for index, entry in enumerate(self.document["steps"]):
            source = self.document["maps"][index]["ring"]
            lines.append(
                f"\n\\paragraph{{Step {index}}} A {text(entry['type'])} from map "
                f"{index} to map {index + 1}.\n"
                "\\begin{itemize}\n"
            )
            lines += [
                f"\\item {item}\n"
                for item in self.parameters(entry, source, f"step {index}")
            ]
            lines.append("\\end{itemize}\n")

        return "".join(lines)

    def parameters(self, entry: Json, source: Json, location: str) -> list[str]:
        """Return the parameters the file writes for one step, TEX-2."""
        generators = source["generators"]
        descriptor = source["domain"]

        def element(encoded: Json) -> str:
            return f"${self.value(descriptor, encoded, location)}$"

        def polynomial(terms: Json) -> str:
            return f"${self.polynomial(terms, generators, descriptor, location)}$"

        def names(identifiers: Iterable[str]) -> str:
            return f"${listing(map(name, identifiers))}$"

        kind = entry["type"]
        if kind == "BCWStep":
            items = [f"index {entry['index']}"]
            for side in ("left", "right"):
                slot = entry[side]
                if "carried" in slot:
                    items.append(f"{side} slot: carried, component {slot['carried']}")
                else:
                    fresh = slot["fresh"]
                    items.append(
                        f"{side} slot: fresh, variable ${name(fresh['variable'])}$, "
                        f"polynomial {polynomial(fresh['polynomial'])}"
                    )
            items.append(f"coefficient {element(entry['coefficient'])}")
            items.append(f"filtration level {entry['filtration_level']}")
            return items
        if kind == "LinearStep":
            items = [self.factor(factor, element) for factor in entry["transformation"]]
            return [*items, _normalizing(entry["normalizing"])]
        if kind == "TranslationStep":
            shift = listing(
                self.value(descriptor, value, location) for value in entry["shift"]
            )
            return [
                f"shift $({shift})$",
                _normalizing(entry["normalizing"]),
            ]
        if kind in ("UnipotentStep", "SymmetricLiftStep"):
            return [f"variables {names(entry['variables'])}"]
        if kind == "HomogenizationStep":
            return [f"variable ${name(entry['variable'])}$"]
        if kind == "CompressionStep":
            rows = [
                "$("
                + listing(self.value(descriptor, value, location) for value in row)
                + ")$"
                for row in entry["basis"]
            ]
            return [
                f"variables {names(entry['variables'])}",
                "basis " + ",\\allowbreak ".join(rows),
            ]

        # DescentStep, the last type of FMT-3; the checker refused any other.
        items = [f"index {entry['index']}"]
        for side in ("left", "right"):
            factors = entry[side]
            if not factors:
                items.append(f"{side}: no factor")
            for factor in factors:
                items.append(
                    f"{side}: index {factor['index']}, "
                    f"polynomial {polynomial(factor['polynomial'])}"
                )
        return items

    @staticmethod
    def factor(factor: Json, element: Any) -> str:
        """Return one factor of a linear transformation, as the file writes it."""
        if "transvection" in factor:
            entry = factor["transvection"]
            return (
                f"transvection: index {entry['index']}, source {entry['source']}, "
                f"coefficient {element(entry['coefficient'])}"
            )
        if "transposition" in factor:
            entry = factor["transposition"]
            return f"transposition: {entry['first']} and {entry['second']}"

        entry = factor["dilation"]
        return (
            f"dilation: index {entry['index']}, "
            f"coefficient {element(entry['coefficient'])}"
        )

    def collisions(self) -> str:
        if not self.document["collisions"]:
            return ""

        lines = ["\n\\subsection*{Collisions}\n"]
        for number, entry in enumerate(self.document["collisions"]):
            descriptor = entry["domain"]
            location = f"collision {number}"

            def point(
                values: Json,
                descriptor: Descriptor = descriptor,
                location: str = location,
            ) -> str:
                return (
                    "$("
                    + listing(
                        self.value(descriptor, value, location) for value in values
                    )
                    + ")$"
                )

            lines.append(
                f"\n\\paragraph{{Collision {number}}} Of map {entry['map']}, over "
                f"${domain(descriptor)}$.\n"
                "\\begin{itemize}\n"
            )
            lines += [f"\\item point {point(values)}\n" for values in entry["points"]]
            lines.append(f"\\item image {point(entry['image'])}\n")
            lines.append("\\end{itemize}\n")

        return "".join(lines)

    def witness(self) -> str:
        found = self.document.get("witness")
        if found is None:
            return ""

        witness = self.certificate.witness
        assert witness is not None  # noqa: S101 - the file holds one, FMT-9
        ring = self.document["maps"][found["step"] + 1]["ring"]
        target = self.certificate.maps[found["step"] + 1].ring
        form = _encode_polynomial(
            target.domain,
            ring["domain"],
            target.from_expr(sp.sympify(witness.form)),
        )
        written = self.polynomial(form, ring["generators"], ring["domain"], "witness")

        return (
            "\n\\subsection*{Witness}\n"
            f"The lift of step {found['step']}, collision {found['collision']}, "
            f"depth {found['depth']}.\n\n"
            "The form of the lift, derived from it by the library and not held by "
            "the file:\n\n"
            f"\\noindent$P = {written}$\n\n"
        )
