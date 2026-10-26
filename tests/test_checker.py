"""The independent checker, CHK-1 to CHK-8 of ``docs/contracts.md``.

``kellermap_check`` reads a certificate file without ``kellermap``. What is
tested here, in the order of the contract:

- that it imports nothing of the library, CHK-1;
- that it refuses what the format refuses, with the identifier and the place
  the library's reader gives, CHK-3. The changes are the tables of
  ``tests/test_certificate.py``, so the two readers answer the same files;
- that its checks fail where the data is wrong, CHK-4, and leave out what a
  caller names, CHK-6;
- what its report and its command line say, CHK-6 and CHK-7;
- its controls, CHK-8: the eight chains of the reconstruction scripts verify,
  their maps and collisions are the ones the scripts compute, and each change
  made to break an obligation is refused for that obligation, by the checker
  and by the library.
"""

from __future__ import annotations

import ast
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
import sympy as sp

import kellermap_check
from kellermap import (
    Certificate,
    LinearStep,
    PolynomialMap,
    Reduction,
    SymmetricLiftStep,
    VerificationError,
    over_field,
)
from kellermap.bcw import HomogenizationStep
from kellermap_check import CHECKS, INCOMPLETE, VERIFIED, Refusal, check
from kellermap_check import _algebra as algebra
from kellermap_check.__main__ import main
from kellermap_check._reading import read

from . import chains
from .test_certificate import (
    COLLISION_EDITS,
    FOLD_TEXT,
    FRAME_EDITS,
    GAUSSIAN_VALUES,
    MAP_EDITS,
    SMALL,
    SMALL_TEXT,
    STEP_EDITS,
    TEXTS,
    WITNESS_EDITS,
    Edit,
    descent,
    edited,
    first_term,
    gao,
    pipeline,
    squared,
)

ROOT = Path(__file__).resolve().parent.parent
PACKAGE = ROOT / "src" / "kellermap_check"

x, y = sp.symbols("x y")


def refused(text: str, obligation: str, location: str) -> Refusal:
    """Check ``text`` and require a refusal with this identifier and place."""
    with pytest.raises(Refusal) as refusal:
        check(text)

    assert (refusal.value.obligation, refusal.value.location) == (
        obligation,
        location,
    ), str(refusal.value)

    return refusal.value


def library_refusal(text: str) -> VerificationError:
    """Read ``text`` with the library and verify it, and return the failure."""
    with pytest.raises(VerificationError) as failure:
        Certificate.loads(text).verify()

    return failure.value


# --------------------------------------------------------------------------
# CHK-1: independent of the library
# --------------------------------------------------------------------------


def test_no_module_of_the_checker_imports_the_library() -> None:
    """The first half of the test CHK-1 names: the source, statically."""
    found = []
    for path in sorted(PACKAGE.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0:
                names = [node.module or ""]
            found += [
                f"{path.name}: {name}"
                for name in names
                if name == "kellermap" or name.startswith("kellermap.")
            ]

    assert not found, found


def test_the_static_search_finds_an_import_of_the_library(tmp_path: Path) -> None:
    """The control of the test above: the same walk on a module that imports it."""
    module = tmp_path / "module.py"
    module.write_text("from kellermap.collision import Collision\n", encoding="utf-8")
    tree = ast.parse(module.read_text(encoding="utf-8"))

    assert any(
        isinstance(node, ast.ImportFrom)
        and (node.module or "").startswith("kellermap.")
        for node in ast.walk(tree)
    )


def test_checking_a_file_loads_no_module_of_the_library() -> None:
    """The second half: a fresh interpreter, a whole run, and its modules after.

    It sees an import through another module, which the static walk cannot.
    """
    program = (
        "import sys\n"
        "import kellermap_check\n"
        "from kellermap_check.__main__ import main\n"
        "report = kellermap_check.check(sys.stdin.read())\n"
        "print(report.verdict)\n"
        "print(sorted(m for m in sys.modules"
        " if m == 'kellermap' or m.startswith('kellermap.')))\n"
    )
    finished = subprocess.run(  # noqa: S603
        [sys.executable, "-c", program],
        input=pipeline().dumps(),
        capture_output=True,
        text=True,
        check=True,
    )

    assert finished.stdout.split("\n")[:2] == [VERIFIED, "[]"], finished.stdout


# --------------------------------------------------------------------------
# CHK-3: the same refusals as the library's reader
# --------------------------------------------------------------------------


@pytest.mark.parametrize(("text", "obligation"), TEXTS)
def test_text_that_is_no_file_is_refused(text: str, obligation: str) -> None:
    refused(text, obligation, "file")


def test_a_key_twice_in_a_valid_file_is_refused() -> None:
    """The second key would be read in place of the first, so it is refused.

    The table of texts has a key twice in an object that lacks every key of a
    file, so a reader that kept the last key would still refuse it under
    FMT-1. Here nothing else is wrong. Both readers are asked.
    """
    text = SMALL_TEXT.replace('"version":1}', '"version":1,"version":1}')

    assert text != SMALL_TEXT
    refused(text, "FMT-1", "file")
    with pytest.raises(VerificationError) as failure:
        Certificate.loads(text)
    assert (failure.value.obligation, failure.value.location) == ("FMT-1", "file")


@pytest.mark.parametrize(("edit", "obligation"), FRAME_EDITS)
def test_the_frame_of_a_file_is_refused_as_the_library_refuses_it(
    edit: Edit, obligation: str
) -> None:
    refused(edited(SMALL_TEXT, edit), obligation, "file")


@pytest.mark.parametrize(("edit", "obligation"), MAP_EDITS)
def test_a_map_is_refused_as_the_library_refuses_it(
    edit: Edit, obligation: str
) -> None:
    refused(edited(SMALL_TEXT, edit), obligation, "map 0")


@pytest.mark.parametrize(("value", "obligation"), GAUSSIAN_VALUES)
def test_a_gaussian_element_is_refused_as_the_library_refuses_it(
    value: Any, obligation: str
) -> None:
    text = squared((sp.I, 0), (-sp.I, 0)).dumps()

    refused(
        edited(text, lambda d: d["collisions"][0]["points"][0].__setitem__(0, value)),
        obligation,
        "collision 0",
    )


@pytest.mark.parametrize(("edit", "obligation", "location"), STEP_EDITS)
def test_a_step_is_refused_as_the_library_refuses_it(
    edit: Edit, obligation: str, location: str
) -> None:
    refused(edited(SMALL_TEXT, edit), obligation, location)


@pytest.mark.parametrize(("text", "edit", "obligation"), COLLISION_EDITS)
def test_a_collision_is_refused_as_the_library_refuses_it(
    text: str, edit: Edit, obligation: str
) -> None:
    refused(edited(text, edit), obligation, "collision 0")


@pytest.mark.parametrize(("edit", "obligation"), WITNESS_EDITS)
def test_a_witness_is_refused_as_the_library_refuses_it(
    witness_text: str, edit: Edit, obligation: str
) -> None:
    refused(edited(witness_text, edit), obligation, "witness")


@pytest.mark.parametrize("value", ["4", "1", "0", "-1", "1/2", "8"])
def test_a_quadratic_field_names_a_square_free_integer(value: str) -> None:
    def domain(document: Any) -> None:
        document["collisions"][0]["domain"] = {"quadratic": value}

    refused(edited(gao().dumps(), domain), "FMT-5", "collision 0")


@pytest.mark.parametrize(
    ("edit", "obligation"),
    [
        pytest.param(
            lambda d: d["collisions"][0]["points"][0][0].__setitem__("denominator", []),
            "FMT-6",
            id="a denominator of zero",
        ),
        pytest.param(
            lambda d: d["collisions"][0]["points"][0][0].pop("denominator"),
            "FMT-1",
            id="a fraction without a denominator",
        ),
    ],
)
def test_a_fraction_is_refused_as_the_library_refuses_it(
    edit: Edit, obligation: str
) -> None:
    refused(edited(FOLD_TEXT, edit), obligation, "collision 0")


def test_an_integer_domain_refuses_a_fraction() -> None:
    refused(
        edited(descent().dumps(), lambda d: first_term(d).__setitem__(1, "1/2")),
        "FMT-6",
        "map 0",
    )


@pytest.mark.parametrize(
    ("edit", "obligation"),
    [
        pytest.param(
            lambda d: d["steps"][0]["left"][0].__setitem__(
                "polynomial", [[[1, 0, 0], "1"]]
            ),
            "DSC-4",
            id="a factor on its own variable",
        ),
        pytest.param(
            lambda d: d["maps"][1]["components"][0].append([[0, 0], "1"]),
            "DSC-1",
            id="a written target the step does not derive",
        ),
        pytest.param(
            lambda d: d["steps"][0].__setitem__("left", []),
            "DSC-3",
            id="a coordinate that is not triangular",
        ),
    ],
)
def test_a_descent_is_refused_as_the_library_refuses_it(
    edit: Edit, obligation: str
) -> None:
    refused(edited(descent().dumps(), edit), obligation, "step 0")


@pytest.mark.parametrize(
    ("edit", "obligation", "location"),
    [
        pytest.param(
            lambda d: d["steps"][0]["variables"].pop(), "UNI-5", "step 0", id="UNI-5"
        ),
        pytest.param(
            lambda d: d["steps"][1].update(variable="x"), "HOM-4", "step 1", id="HOM-4"
        ),
        pytest.param(
            lambda d: d["steps"][2]["variables"].pop(), "SYM-5", "step 2", id="SYM-5"
        ),
    ],
)
def test_the_steps_of_section_4_are_refused_as_the_library_refuses_them(
    edit: Edit, obligation: str, location: str
) -> None:
    refused(edited(pipeline().dumps(), edit), obligation, location)


def test_a_basis_is_refused_as_the_library_refuses_it(witness_text: str) -> None:
    refused(
        edited(witness_text, lambda d: d["steps"][0]["basis"].pop()), "CHC-5", "step 0"
    )


def test_a_linear_factor_on_a_coordinate_past_the_map_is_refused() -> None:
    def far(document: Any) -> None:
        document["steps"][2]["transformation"][0]["transvection"].update(source=5)

    text = edited(SMALL_TEXT, far)

    refused(text, "LIN-2", "step 2")
    with pytest.raises(VerificationError) as failure:
        Certificate.loads(text)
    assert (failure.value.obligation, failure.value.location) == ("LIN-2", "step 2")


def test_a_normalization_with_a_transvection_is_verified() -> None:
    """LIN-6 multiplies out every kind of factor; the chains use two of three."""
    source = over_field(PolynomialMap((x, y), (x + y + y**3, y)))
    text = Certificate(Reduction((LinearStep.normalize(source),))).dumps()

    assert "transvection" in text
    assert check(text).verdict == VERIFIED


def test_a_collision_domain_that_dumps_would_not_choose_is_accepted() -> None:
    """FMT-8: a base lies in a polynomial ring over it, for this reader too."""

    def widen(document: Any) -> None:
        entry = document["collisions"][0]
        entry["domain"] = {"polynomial": "ZZ", "parameters": ["T"], "order": "lex"}
        for coordinates in [*entry["points"], entry["image"]]:
            for position, value in enumerate(coordinates):
                coordinates[position] = [] if value == "0" else [[[0], value]]

    assert check(edited(squared((1, 0), (-1, 0)).dumps(), widen)).verdict == VERIFIED


def test_a_polynomial_ring_does_not_contain_a_field_of_fractions() -> None:
    def narrow(document: Any) -> None:
        domain = document["collisions"][0]["domain"]
        domain["polynomial"] = domain.pop("fraction")

    refused(edited(SMALL["a map over ZZ(T)"]().dumps(), narrow), "FMT-8", "collision 0")


# --------------------------------------------------------------------------
# The rest of the format, which only this reader reaches
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("edit", "obligation", "location"),
    [
        pytest.param(
            lambda d: d["maps"][0]["ring"].update(domain=["QQ"]),
            "FMT-1",
            "map 0",
            id="a domain that is a list",
        ),
        pytest.param(
            lambda d: d["maps"][0]["ring"].update(
                domain={"polynomial": "QQ", "parameters": ["T"], "order": "ilex"}
            ),
            "FMT-1",
            "map 0",
            id="a domain in an order outside the list",
        ),
        pytest.param(
            lambda d: d["steps"][2]["transformation"].append({"rotation": {}}),
            "FMT-1",
            "step 2",
            id="an unknown kind of linear factor",
        ),
        pytest.param(
            lambda d: d.update(collisions={}),
            "FMT-1",
            "file",
            id="collisions not a list",
        ),
    ],
)
def test_the_reader_refuses_what_the_format_does_not_name(
    edit: Edit, obligation: str, location: str
) -> None:
    refused(edited(SMALL_TEXT, edit), obligation, location)


# --------------------------------------------------------------------------
# CHK-8: the controls
# --------------------------------------------------------------------------


@pytest.mark.parametrize("name", chains.NAMES)
def test_the_chain_of_a_reconstruction_script_is_verified(name: str) -> None:
    """``VERIFIED``, and the end of the file is what the script computes."""
    text = chains.certificate(name).dumps()

    assert check(text).verdict == VERIFIED

    document = read(text)
    end = document.maps[-1]
    symbols = [sp.Symbol(name) for name in end.names]
    components = [component.as_expr() for component in end.components]
    expected = chains.script_target(name)
    assert [str(symbol) for symbol in symbols] == [
        str(symbol) for symbol in sorted(symbols, key=lambda s: end.names.index(str(s)))
    ]
    assert len(components) == len(expected)
    assert all(sp.expand(a - b) == 0 for a, b in zip(components, expected, strict=True))

    collision = document.collisions[-1]
    domain = collision.domain.sympy
    points = {
        tuple(sp.nsimplify(domain.to_sympy(value)) for value in point)
        for point in collision.points
    }
    assert collision.position == len(document.maps) - 1
    assert points == chains.script_points(name)


def test_the_chain_of_thompson_is_verified_and_is_the_scripts(
    witness_text: str,
) -> None:
    """The eighth chain, ``reconstruct_prellberg40.py``.

    The compressed map, the pair of points, the lifted points and the lift are
    the ones the script transcribes and computes, after its variables are
    renamed to the file's.
    """
    report = check(witness_text)
    assert report.verdict == VERIFIED

    script = chains.script("prellberg40")
    document = read(witness_text)
    compressed, lifted = document.maps[1], document.maps[2]

    renamed = dict(zip(script.z, [sp.Symbol(n) for n in compressed.names], strict=True))
    displacement = [
        (component - generator).as_expr()
        for component, generator in zip(
            compressed.components, compressed.ring.gens, strict=True
        )
    ]
    assert displacement == [
        sp.expand(sp.sympify(h).xreplace(renamed)) for h in script.h
    ]

    first_point = tuple(sp.sympify(c) for c in script.P20)
    second_point = tuple(sp.sympify(c) for c in script.Q20)
    pair = document.collisions[0]
    assert {
        tuple(pair.domain.sympy.to_sympy(v) for v in point) for point in pair.points
    } == {first_point, second_point}

    rho = sp.Matrix(script.RHO)
    expected = {
        tuple(sp.nsimplify(v) for v in first_point + (0,) * 20),
        tuple(
            sp.nsimplify(v)
            for v in tuple(sp.Matrix(second_point) + rho) + tuple(sp.I * rho)
        ),
    }
    lifted_pair = document.collisions[1]
    assert {
        tuple(sp.nsimplify(lifted_pair.domain.sympy.to_sympy(v)) for v in point)
        for point in lifted_pair.points
    } == expected

    variables = list(script.x) + list(script.y)
    form = sp.expand(
        sp.I
        * sum(
            script.h[j].subs(
                {script.z[k]: script.x[k] + sp.I * script.y[k] for k in range(20)}
            )
            * script.y[j]
            for j in range(20)
        )
    )
    names = dict(zip(variables, [sp.Symbol(n) for n in lifted.names], strict=True))
    assert [c.as_expr() for c in lifted.components] == [
        sp.expand((v - sp.diff(form, v)).xreplace(names)) for v in variables
    ]


def term(document: Any, position: int, component: int, index: int = 0) -> Any:
    return document["maps"][position]["components"][component][index]


def scaled(value: str) -> str:
    return str(sp.Rational(value) * 2)


NEGATIVE: list[Any] = [
    pytest.param(
        "bcw17",
        lambda d: term(d, 3, 1).__setitem__(1, scaled(term(d, 3, 1)[1])),
        "BCW-1",
        "step 2",
        "a coefficient of map 3, the target of step 2, is doubled; the identity "
        "of that step no longer holds, and nothing before it reads map 3",
        "BCW-1",
        id="a coefficient of a target",
    ),
    pytest.param(
        "alpoege15",
        lambda d: d["steps"][3]["left"]["fresh"]["polynomial"][0].__setitem__(1, "5"),
        "BCW-1",
        "step 3",
        "the coefficient of a fresh slot changes; its order does not, so BCW-6 "
        "holds and only the identity fails",
        "BCW-1",
        id="a coefficient of a slot",
    ),
    pytest.param(
        "alpoege12",
        lambda d: d["steps"][2]["left"].__setitem__("carried", 2),
        "BCW-10",
        "step 2",
        "a carried slot moves to the target component of the step",
        "BCW-10",
        id="a slot on the target component",
    ),
    pytest.param(
        "alpoege12",
        lambda d: d["steps"][2]["left"].__setitem__("carried", 0),
        "BCW-10",
        "step 2",
        "a carried slot moves to component 0, which is not x0 plus a term free "
        "of x0; the constructor accepts the index, and the third clause fails",
        "BCW-10",
        id="a slot on a component that carries nothing",
    ),
    pytest.param(
        "spacerat11",
        lambda d: d["collisions"][1]["points"][0].__setitem__(0, "7"),
        "COL-3",
        "collision 1",
        "one coordinate of a point at the end of the chain changes; the steps do "
        "not read collisions, so the first check to fail is the image",
        "COL-3",
        id="a coordinate of a point",
    ),
    pytest.param(
        "bcw17",
        lambda d: d["steps"][0]["transformation"][0]["dilation"].__setitem__(
            "coefficient", "1/3"
        ),
        "LIN-6",
        "step 0",
        "the dilation of the normalization changes, so the transformation is no "
        "longer the inverse of the linear part; the checker reads LIN-6 before "
        "LIN-1, and the library reads the identity first",
        "LIN-1",
        id="a coefficient of a normalization",
    ),
]


@pytest.mark.parametrize(
    ("name", "edit", "obligation", "location", "reason", "library"), NEGATIVE
)
def test_a_change_made_to_break_an_obligation_is_refused_for_it(
    name: str,
    edit: Edit,
    obligation: str,
    location: str,
    reason: str,
    library: str,
) -> None:
    """CHK-8, the negative controls, each stated with its reason in advance.

    The checker has to cite the obligation the change breaks, at its place.
    The library has to refuse the same file as well; where it cites another
    obligation, the row says which and the reason says why.
    """
    text = edited(chains.certificate(name).dumps(), edit)

    assert reason
    refused(text, obligation, location)
    assert library_refusal(text).obligation == library


def test_a_change_to_a_basis_is_refused_for_the_identity(witness_text: str) -> None:
    """One entry of the basis changes and stays independent, so CHC-1 fails."""

    def change(document: Any) -> None:
        row = document["steps"][0]["basis"][0]
        row[-1] = "7" if row[-1] == "0" else "0"

    text = edited(witness_text, change)

    refused(text, "CHC-1", "step 0")
    assert library_refusal(text).obligation == "CHC-1"


def test_a_change_to_the_lift_is_refused_for_the_identity(witness_text: str) -> None:
    def change(document: Any) -> None:
        entry = term(document, 2, 0)
        entry[1] = [scaled(entry[1][0]), scaled(entry[1][1])]

    text = edited(witness_text, change)

    refused(text, "SYM-1", "step 1")
    assert library_refusal(text).obligation == "SYM-1"


@pytest.mark.parametrize(
    ("build", "obligation"),
    [
        pytest.param(
            lambda: HomogenizationStep.build(
                over_field(PolynomialMap((x, y), (x + y**2 + x * y, y)))
            ),
            "HOM-3",
            id="a source whose displacement is not nilpotent",
        ),
        pytest.param(
            lambda: SymmetricLiftStep.build(
                over_field(PolynomialMap((x, y), (x + x**2, y)))
            ),
            "SYM-4",
            id="a lift of a source that is not Keller",
        ),
    ],
)
def test_a_determinant_that_is_not_one_is_refused(
    build: Callable[[], Any], obligation: str
) -> None:
    """The negative controls of the determinant, on steps the library built.

    ``build`` forms the target by the formula and checks nothing, so the step
    holds its identity and fails the obligation about its source.
    """
    text = Certificate(Reduction((build(),))).dumps()

    refused(text, obligation, "step 0")
    assert library_refusal(text).obligation == obligation


def test_a_unipotent_step_from_a_source_that_is_not_keller_is_refused() -> None:
    """UNI-4. Map 0 gains ``x * y``, which keeps it in ``MA^1`` and cubic."""

    def change(document: Any) -> None:
        document["maps"][0]["components"][0].append([[1, 1], "1"])

    text = edited(pipeline().dumps(), change)

    refused(text, "UNI-4", "step 0")
    assert library_refusal(text).obligation == "UNI-4"


@pytest.mark.parametrize(
    "edit",
    [
        pytest.param(
            lambda d: d["collisions"][0]["points"].reverse(), id="the points reordered"
        ),
        pytest.param(
            lambda d: [
                part.__setitem__(1, scaled(part[1]))
                for entry in d["collisions"][0]["points"][0]
                for key in ("numerator", "denominator")
                for part in entry[key]
            ],
            id="a fraction scaled",
        ),
    ],
)
def test_a_change_that_keeps_a_file_valid_is_accepted(edit: Edit) -> None:
    """CHK-8, the positive controls. The library reads the same certificate."""
    text = edited(FOLD_TEXT, edit)

    assert text != FOLD_TEXT
    assert check(text).verdict == VERIFIED
    assert Certificate.loads(text).collisions == Certificate.loads(FOLD_TEXT).collisions


# --------------------------------------------------------------------------
# CHK-6: verdicts, skips and the command line
# --------------------------------------------------------------------------


@pytest.mark.parametrize("name", list(SMALL))
def test_a_small_certificate_is_verified_and_survives_every_skip(name: str) -> None:
    """Every check left out at once: ``INCOMPLETE``, and nothing breaks."""
    text = SMALL[name]().dumps()

    assert check(text).verdict == VERIFIED
    report = check(text, CHECKS)
    assert report.verdict == INCOMPLETE
    assert report.skipped


def test_the_witness_survives_every_skip(witness_text: str) -> None:
    report = check(witness_text, CHECKS)

    assert report.verdict == INCOMPLETE
    assert dict(report.skipped)["witness"] == ("VAN-1", "VAN-2", "VAN-3")


def test_a_skip_that_is_not_a_check_is_a_wrong_call() -> None:
    with pytest.raises(ValueError, match="FMT-1"):
        check(SMALL_TEXT, {"FMT-1"})


def test_a_skipped_determinant_leaves_its_step_incomplete() -> None:
    """A source that is not Keller passes once UNI-4 is left out, and says so."""

    def change(document: Any) -> None:
        document["maps"][0]["components"][0].append([[1, 1], "1"])

    text = edited(pipeline().dumps(), change)

    with pytest.raises(Refusal):
        check(text, {"UNI-4"})
    report = check(text, {"UNI-4", "UNI-1"})
    assert report.verdict == INCOMPLETE
    assert dict(report.skipped)["step 0"] == ("UNI-4", "UNI-1")


def test_a_skipped_shape_check_is_made_up_for_by_the_identity() -> None:
    """With BCW-2 left out, a target with the wrong generators fails BCW-1."""

    def rename(document: Any) -> None:
        document["maps"][2]["ring"]["generators"][-1] = "w"

    text = edited(SMALL_TEXT, rename)

    refused(text, "BCW-2", "step 1")
    with pytest.raises(Refusal) as refusal:
        check(text, {"BCW-2"})
    assert refusal.value.obligation == "BCW-1"


@pytest.fixture
def file(tmp_path: Path) -> Callable[[str], str]:
    def write(text: str) -> str:
        path = tmp_path / "certificate.json"
        path.write_text(text, encoding="utf-8")
        return str(path)

    return write


def test_the_command_line_exits_with_the_verdict(
    file: Callable[[str], str], capsys: pytest.CaptureFixture[str]
) -> None:
    """0 for ``VERIFIED``, 3 for ``INCOMPLETE``, 1 for ``REFUSED``, 2 otherwise."""
    assert main([file(SMALL_TEXT)]) == 0
    assert capsys.readouterr().out.startswith(VERIFIED)

    assert main([file(SMALL_TEXT), "--skip", "BCW-1"]) == 3
    assert "skipped  step 1: BCW-1" in capsys.readouterr().out

    assert main([file("not json")]) == 1
    assert "[FMT-1] in file" in capsys.readouterr().out

    assert main([file(SMALL_TEXT), "--skip", "FMT-1"]) == 2
    assert main([str(Path(file(SMALL_TEXT)).parent / "missing.json")]) == 2
    assert main([]) == 2
    assert main(["--help"]) == 0


def test_the_module_runs_from_the_command_line(file: Callable[[str], str]) -> None:
    finished = subprocess.run(  # noqa: S603
        [sys.executable, "-m", "kellermap_check", file(SMALL_TEXT)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert finished.returncode == 0, finished.stderr
    assert finished.stdout.startswith(VERIFIED)


# --------------------------------------------------------------------------
# CHK-7: what a report says
# --------------------------------------------------------------------------


def test_a_report_names_what_was_not_computed(witness_text: str) -> None:
    report = check(witness_text)

    assert report.not_computed == ("SYM-7", "VAN-5")
    assert dict(report.checked)["step 1"] == ("SYM-3", "SYM-4", "SYM-5", "SYM-1")
    assert dict(report.checked)["file"][0] == "FMT-1"
    assert any("witness" in claim for claim in report.claims)
    assert report.not_claimed == ()
    assert "not computed SYM-7" in "\n".join(report.lines())


def test_a_file_that_claims_nothing_says_so() -> None:
    """A single map passes every check and confirms nothing."""
    report = check(Certificate(PolynomialMap((x, y), (x, y))).dumps())

    assert report.verdict == VERIFIED
    assert report.claims == ()
    assert report.not_claimed == ("this file makes no mathematical claim",)


def test_a_chain_does_not_claim_that_its_source_is_keller() -> None:
    report = check(chains.certificate("bcw17").dumps())

    assert any("Keller" in item for item in report.not_claimed)
    assert len(report.claims) == len(chains.certificate("bcw17").steps) + 2


def test_a_collision_alone_claims_only_itself() -> None:
    report = check(squared((1, 0), (-1, 0)).dumps())

    assert report.claims == (
        "collision 0 is a collision of map 0, 2 distinct points with one image",
    )
    assert any("Keller" in item for item in report.not_claimed)


# --------------------------------------------------------------------------
# The determinant
# --------------------------------------------------------------------------


def test_the_complement_on_thompsons_maps_has_three_rows(witness_text: str) -> None:
    """Why the checker affords CHC-4 and SYM-4, which ``docs/roadmap.md`` measured.

    The determinant left to compute is that of a matrix of three rows, on the
    map of 24 variables and on the compressed map of 20.
    """
    document = read(witness_text)
    for polynomial_map in document.maps[:2]:
        ring = polynomial_map.ring
        jacobian = [
            [component.diff(generator) for generator in ring.gens]
            for component in polynomial_map.components
        ]
        kept, _ = algebra._block(jacobian, ring.one)

        assert len(ring.gens) - len(kept) == 3


def test_the_determinant_needs_no_block() -> None:
    """A Jacobian without a diagonal one: the whole matrix is the complement."""
    ring, gx, gy = sp.ring("x y", sp.QQ)

    assert algebra.determinant_is_one(ring, [gy, gx + gy]) is False
    assert algebra.determinant_is_one(ring, [gy, -gx + gy]) is True


def test_the_determinant_breaks_a_cycle_of_dependencies() -> None:
    """Two coordinates that depend on each other: one stays, one goes."""
    ring, gx, gy = sp.ring("x y", sp.QQ)

    assert algebra.determinant_is_one(ring, [gx + gy, gy + gx]) is False
    assert algebra.determinant_is_one(ring, [gx + gy**2, gy]) is True
    assert algebra.determinant_is_one(ring, [gx + gy, gy - gx]) is False


def test_a_unit_is_decided_in_the_domain() -> None:
    assert algebra.is_unit(sp.ZZ, sp.ZZ(-1))
    assert not algebra.is_unit(sp.ZZ, sp.ZZ(2))
    assert not algebra.is_unit(sp.QQ, sp.QQ(0))
    assert algebra.is_unit(sp.QQ, sp.QQ(2))


def test_the_package_states_what_skip_may_name() -> None:
    """``CHECKS`` is the table of CHK-4 in ``docs/contracts.md``."""
    contracts = (ROOT / "docs" / "contracts.md").read_text(encoding="utf-8")
    table = contracts[contracts.index("**CHK-4 ") : contracts.index("**CHK-5 ")]
    rows = [line for line in table.splitlines() if line.startswith("| ")][2:]
    named = {
        identifier
        for row in rows
        for identifier in __import__("re").findall(r"[A-Z]{3}-\d+", row)
    }

    assert named == set(CHECKS)
    assert kellermap_check.__all__
