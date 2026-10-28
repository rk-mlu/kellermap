"""The LaTeX view of a certificate file, TEX-1 to TEX-6 of ``docs/contracts.md``.

The view checks nothing itself. What is tested here is what it promises: it
is made only from a file the checker verifies, it shows what that file holds
in the order the file writes it, it is a document or a body that ``pdflatex``
compiles without a package, two names never look alike in it, and it is ASCII.

The compilation is the one test here that needs a program outside Python. It
runs where ``pdflatex`` is on the path and says that it was skipped where it
is not, so the rest of the suite does not depend on a TeX installation.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest
import sympy as sp

import kellermap
import kellermap_check
from kellermap import Certificate, PolynomialMap, VerificationError, over_field
from kellermap.latex import MARKER, name, text, to_latex

from . import chains
from .test_certificate import FOLD_TEXT, SKIPPED, SMALL, SMALL_TEXT, edited

ROOT = Path(__file__).resolve().parent.parent

x, y = sp.symbols("x y")


def single(*components: sp.Expr, variables: tuple[sp.Symbol, ...] = (x, y)) -> str:
    """Return the file of a certificate that holds one map and nothing else."""
    return Certificate(PolynomialMap(variables, components)).dumps()


# --------------------------------------------------------------------------
# TEX-1: only from a file the checker verifies
# --------------------------------------------------------------------------


def test_a_file_the_checker_refuses_has_no_view() -> None:
    """The refusal of the checker, with its identifier, place and cause."""

    def doubled(document: Any) -> None:
        term = document["maps"][3]["components"][1][0]
        term[1] = str(2 * sp.Rational(term[1]))

    bad = edited(chains.certificate("bcw17").dumps(), doubled)

    with pytest.raises(VerificationError) as failure:
        to_latex(bad)

    assert (failure.value.obligation, failure.value.location) == ("BCW-1", "step 2")
    assert isinstance(failure.value.__cause__, kellermap_check.Refusal)


def test_text_that_is_no_file_has_no_view() -> None:
    with pytest.raises(VerificationError) as failure:
        to_latex("not a file")

    assert (failure.value.obligation, failure.value.location) == ("FMT-1", "file")


def test_the_view_is_made_after_the_checker_and_not_after_the_library(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The checker decides. A checker that refuses stops the view, whatever the
    library would say about the same text."""

    def refuse(_: str) -> Any:
        raise kellermap_check.Refusal("CHK-6", "file", "refused for this test")

    monkeypatch.setattr(kellermap_check, "check", refuse)

    with pytest.raises(VerificationError, match="refused for this test"):
        to_latex(SMALL_TEXT)


# --------------------------------------------------------------------------
# TEX-2: it shows what the file holds
# --------------------------------------------------------------------------


@pytest.mark.parametrize("label", list(SMALL))
def test_every_part_of_a_file_stands_in_its_view(label: str) -> None:
    """Every map with every component, every step, every collision."""
    file = SMALL[label]().dumps()
    document = json.loads(file)
    view = to_latex(file)

    assert view.count("\\paragraph{Map ") == len(document["maps"])
    assert view.count("\\paragraph{Step ") == len(document["steps"])
    assert view.count("\\paragraph{Collision ") == len(document["collisions"])
    assert view.count("$F_{") == sum(len(m["components"]) for m in document["maps"])
    for index, step in enumerate(document["steps"]):
        assert f"\\paragraph{{Step {index}}} A {step['type']} from map {index}" in view
    for entry in document["collisions"]:
        assert view.count("\\item point ") >= len(entry["points"])


@pytest.mark.parametrize("label", list(SMALL))
def test_the_report_of_the_checker_stands_in_the_view(label: str) -> None:
    file = SMALL[label]().dumps()
    report = kellermap_check.check(file)
    view = to_latex(file)

    assert "is VERIFIED." in view
    for entry in (*report.claims, *report.not_claimed):
        assert text(entry) in view
    for identifier in report.not_computed:
        assert f"{identifier}: " in view


def test_the_parameters_of_every_step_type_stand_in_the_view(witness_text: str) -> None:
    """One file per group of step types, and the parameters each writes."""
    chain = to_latex(SMALL_TEXT)
    assert "shift $(1,\\allowbreak 2)$" in chain
    assert "the step claims to normalize" in chain
    assert "left slot: fresh, variable $u$, polynomial $y^{2}$" in chain
    assert "right slot: carried, component 1" in chain
    assert "coefficient $3$" in chain
    assert "filtration level 1" in chain
    assert "transvection: index 0, source 1, coefficient $\\frac{1}{3}$" in chain
    assert "transposition: 0 and 2" in chain
    assert "dilation: index 1, coefficient $2$" in chain
    assert "the step does not normalize" in chain

    pipeline = to_latex(SMALL["pipeline"]().dumps())
    assert "variables $X_{3},\\allowbreak X_{4}$" in pipeline
    assert "variable $X_{5}$" in pipeline

    descent = to_latex(SMALL["descent"]().dumps())
    assert "left: index 0, polynomial $-z^{2}$" in descent
    assert "right: no factor" in descent

    thompson = to_latex(witness_text)
    assert "basis $(" in thompson
    assert "\\subsection*{Witness}" in thompson
    assert "depth 2" in thompson


def test_the_form_of_a_witness_is_shown_and_labelled_as_derived(
    witness_text: str,
) -> None:
    """The one thing TEX-2 allows that the file does not hold."""
    view = to_latex(witness_text)
    form = view[view.index("$P = ") :].split("$")[1]

    # One term per summand of the form. A coefficient that is a sum stands in
    # brackets and is taken out before the signs between terms are counted.
    # The sign of the first term is no separator.
    outside = re.sub(r"\\left\(.*?\\right\)", "", form.removeprefix("P = "))
    outside = outside.removeprefix("- ")
    witness = Certificate.loads(witness_text).witness
    assert witness is not None

    assert "not held by the file" in view
    assert outside.count(" + ") + outside.count(" - ") + 1 == len(
        sp.Add.make_args(sp.expand(witness.form))
    )


def test_a_file_without_steps_or_collisions_shows_neither_heading() -> None:
    view = to_latex(single(x, y))

    assert "\\subsection*{Steps}" not in view
    assert "\\subsection*{Collisions}" not in view
    assert "\\subsection*{Witness}" not in view
    assert "this file makes no mathematical claim" in view


# --------------------------------------------------------------------------
# TEX-3: as the file writes it
# --------------------------------------------------------------------------


def test_terms_stand_in_the_order_of_the_file() -> None:
    """Descending lexicographic order of the exponents, FMT-6, signs written once."""
    view = to_latex(single(y**3 + x - 2 * x * y, -y))

    assert "$F_{0} = -2 x y + x + y^{3}$" in view
    assert "$F_{1} = -y$" in view


def test_a_zero_component_is_shown_as_zero() -> None:
    assert "$F_{1} = 0$" in to_latex(single(x, sp.Integer(0)))


@pytest.mark.parametrize(
    "edit",
    [
        pytest.param(lambda d: d["collisions"][0]["points"].reverse(), id="points"),
        pytest.param(
            lambda d: [
                part.__setitem__(1, str(2 * int(part[1])))
                for entry in d["collisions"][0]["points"][0]
                for key in ("numerator", "denominator")
                for part in entry[key]
            ],
            id="a common factor",
        ),
    ],
)
def test_two_files_of_one_certificate_have_one_view(edit: Any) -> None:
    """The positive controls of CHK-8, read as views."""
    other = edited(FOLD_TEXT, edit)

    assert other != FOLD_TEXT
    assert to_latex(other) == to_latex(FOLD_TEXT)


def test_coefficients_of_every_domain_are_shown() -> None:
    """A Gaussian coefficient in brackets, a parameter, a fraction and a root."""
    assert "\\left(1 + 2 \\mathrm{i}\\right) x" in to_latex(
        single((1 + 2 * sp.I) * x, y)
    )
    assert "\\frac{1}{T}" in to_latex(SMALL["a map over ZZ(T)"]().dumps())
    assert "\\mathbf{Z}(T)" in to_latex(SMALL["a map over ZZ(T)"]().dumps())
    assert "\\mathbf{Q}(\\sqrt{-23})" in to_latex(SMALL["gao"]().dumps())
    assert "\\sqrt{23}" in to_latex(SMALL["gao"]().dumps())
    assert "\\mathbf{Z}[\\mathrm{i}]" in to_latex(SMALL["gaussian points"]().dumps())
    assert "\\mathbf{Q}(\\mathrm{i})" in to_latex(SMALL["pipeline"]().dumps())


# --------------------------------------------------------------------------
# TEX-4: two forms, and no package
# --------------------------------------------------------------------------


def test_the_document_is_the_body_inside_a_class() -> None:
    document = to_latex(SMALL_TEXT)
    body = to_latex(SMALL_TEXT, standalone=False)

    assert document.splitlines()[0] == MARKER
    assert body.splitlines()[0] == MARKER
    assert document == (
        f"{MARKER}\n\\documentclass{{article}}\n\\begin{{document}}\n"
        + body.removeprefix(f"{MARKER}\n")
        + "\\end{document}\n"
    )
    assert "\\usepackage" not in document


PDFLATEX = shutil.which("pdflatex")


def compiled(source: str, directory: Path, stem: str) -> None:
    """Compile ``source`` with ``pdflatex`` and fail with its first error."""
    (directory / f"{stem}.tex").write_text(source, encoding="ascii")
    finished = subprocess.run(  # noqa: S603
        [str(PDFLATEX), "-interaction=nonstopmode", "-halt-on-error", f"{stem}.tex"],
        cwd=directory,
        capture_output=True,
        text=True,
        check=False,
    )
    errors = [line for line in finished.stdout.splitlines() if line.startswith("!")]

    assert finished.returncode == 0, errors or finished.stdout[-2000:]
    assert (directory / f"{stem}.pdf").exists()


@pytest.mark.skipif(PDFLATEX is None, reason="pdflatex is not on the path")
def test_pdflatex_compiles_every_view(witness_text: str, tmp_path: Path) -> None:
    """Every small certificate, a chain and Thompson's witness, in both forms.

    The body is read into a document that loads no package either, which is
    the claim TEX-4 makes of it.
    """
    files = {
        f"small{number}": SMALL[label]().dumps() for number, label in enumerate(SMALL)
    }
    files["alpoege19"] = chains.certificate("alpoege19").dumps()
    files["thompson"] = witness_text

    for stem, file in files.items():
        compiled(to_latex(file), tmp_path, stem)

    (tmp_path / "body.tex").write_text(
        to_latex(SMALL_TEXT, standalone=False), encoding="ascii"
    )
    compiled(
        "\\documentclass{article}\n\\begin{document}\n\\input{body}\n\\end{document}\n",
        tmp_path,
        "reader",
    )


@pytest.mark.skipif(PDFLATEX is None, reason="pdflatex is not on the path")
def test_the_compilation_fails_on_a_broken_view(tmp_path: Path) -> None:
    """The control of the test above: an error in the source is seen."""
    with pytest.raises(AssertionError):
        broken = to_latex(SMALL_TEXT).replace("\\section*", "\\undefined\\section*")
        compiled(broken, tmp_path, "broken")


# --------------------------------------------------------------------------
# TEX-5: two names are never shown alike
# --------------------------------------------------------------------------


def test_sympy_shows_two_names_alike() -> None:
    """Why TEX-5 does not use SymPy's rendering of a name."""
    assert sp.latex(sp.Symbol("x1")) == sp.latex(sp.Symbol("x_1"))


@pytest.mark.parametrize(
    ("identifier", "shown"),
    [
        ("x", "x"),
        ("x12", "x_{12}"),
        ("X0", "X_{0}"),
        ("x_1", "\\mathit{x\\_1}"),
        ("alpha", "\\mathit{alpha}"),
        ("x__", "\\mathit{x\\_\\_}"),
        ("_x", "\\mathit{\\_x}"),
        ("i", "i"),
    ],
)
def test_a_name_is_shown_by_its_shape(identifier: str, shown: str) -> None:
    assert name(identifier) == shown


def test_names_that_sympy_confuses_are_shown_apart() -> None:
    names = ["x1", "x_1", "x10", "x_10", "x1_0", "xx", "x", "x_", "x__", "i", "I"]

    assert len({name(entry) for entry in names}) == len(names)


def test_a_generator_named_i_is_not_the_imaginary_unit() -> None:
    i = sp.Symbol("i")
    view = to_latex(over_field_gaussian(i))

    assert "\\mathrm{i}" in view
    assert re.search(r"\$F_\{0\} = i\b", view)


def over_field_gaussian(i: sp.Symbol) -> str:
    """A map over ``QQ_I`` with a generator named ``i`` and the unit in it."""
    polynomial_map = over_field(PolynomialMap((i, y), (i + sp.I * y**2, y)))

    return Certificate(polynomial_map).dumps()


def test_a_map_with_names_sympy_confuses_shows_both() -> None:
    first, second = sp.symbols("x1 x_1")
    view = to_latex(single(first + second**2, second, variables=(first, second)))

    assert "Generators $x_{1},\\allowbreak \\mathit{x\\_1}$" in view
    assert "$F_{0} = x_{1} + \\mathit{x\\_1}^{2}$" in view


# --------------------------------------------------------------------------
# TEX-6: plain ASCII, and text is escaped
# --------------------------------------------------------------------------


@pytest.mark.parametrize("label", list(SMALL))
def test_every_view_is_ascii(label: str) -> None:
    assert to_latex(SMALL[label]().dumps()).isascii()


def test_text_escapes_every_character_latex_reads_as_a_command() -> None:
    assert text("a_b %c $d &e #f {g} ^h ~i \\j") == (
        "a\\_b \\%c \\$d \\&e \\#f \\{g\\} \\^{}h \\~{}i \\textbackslash{}j"
    )


# --------------------------------------------------------------------------
# The licence rule, and the public surface
# --------------------------------------------------------------------------


def view_files(root: Path) -> list[str]:
    """Return every file under ``root`` whose first line is the marker of TEX-4."""
    found = []
    for path in root.rglob("*"):
        if not path.is_file() or SKIPPED & set(path.relative_to(root).parts):
            continue
        try:
            first = path.read_text(encoding="utf-8").split("\n", 1)[0]
        except (UnicodeDecodeError, OSError):
            continue
        if first == MARKER:
            found.append(str(path.relative_to(root)))

    return found


def test_the_repository_holds_no_view() -> None:
    """A view holds the values of its maps, as the file does."""
    assert view_files(ROOT) == []


def test_the_search_finds_a_view_under_any_name(tmp_path: Path) -> None:
    (tmp_path / "notes.txt").write_text(to_latex(SMALL_TEXT), encoding="ascii")

    assert view_files(tmp_path) == ["notes.txt"]


def test_the_view_is_part_of_the_public_surface() -> None:
    assert kellermap.to_latex is to_latex
    assert "to_latex" in kellermap.__all__
