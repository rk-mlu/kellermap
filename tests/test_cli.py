"""The program ``kellermap``, CLI-1 to CLI-4 of ``docs/contracts.md``.

The command line adds no behaviour. What is tested is that it passes on what
the checker and the view do: ``verify`` gives the checker's output and status,
``latex`` writes the view, and a refused file writes nothing.
"""

from __future__ import annotations

import importlib
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import pytest

import kellermap_check.__main__
from kellermap.cli import main
from kellermap.latex import to_latex

from .test_certificate import SMALL_TEXT, edited

Write = Callable[[str, str], Path]


@pytest.fixture
def file(tmp_path: Path) -> Write:
    """Write a text into the temporary directory and return its path."""

    def write(text: str, stem: str = "certificate.json") -> Path:
        path = tmp_path / stem
        path.write_text(text, encoding="utf-8")
        return path

    return write


REFUSED_TEXT = edited(SMALL_TEXT, lambda d: d.update(version=2))
"""A file the checker refuses under FMT-1, in the file."""


# --------------------------------------------------------------------------
# CLI-1: verify is the checker
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "extra", "status"),
    [
        pytest.param(SMALL_TEXT, [], 0, id="verified"),
        pytest.param(SMALL_TEXT, ["--skip", "BCW-1"], 3, id="incomplete"),
        pytest.param(REFUSED_TEXT, [], 1, id="refused"),
        pytest.param("not json", [], 1, id="not json"),
        pytest.param(SMALL_TEXT, ["--skip", "FMT-1"], 2, id="a skip that is no check"),
    ],
)
def test_verify_gives_the_output_and_status_of_the_checker(
    file: Write,
    capsys: pytest.CaptureFixture[str],
    text: str,
    extra: list[str],
    status: int,
) -> None:
    path = str(file(text))

    assert kellermap_check.__main__.main([path, *extra]) == status
    expected = capsys.readouterr()

    assert main(["verify", path, *extra]) == status
    assert capsys.readouterr() == expected


def test_verify_names_itself_in_its_usage(capsys: pytest.CaptureFixture[str]) -> None:
    """The one difference CLI-1 allows."""
    assert main(["verify"]) == 2
    assert "usage: kellermap verify" in capsys.readouterr().err

    assert main(["verify", "--help"]) == 0
    assert capsys.readouterr().out.startswith("usage: kellermap verify")


def test_verify_of_a_missing_file_exits_with_two(tmp_path: Path) -> None:
    assert main(["verify", str(tmp_path / "missing.json")]) == 2


# --------------------------------------------------------------------------
# CLI-2: latex is the view
# --------------------------------------------------------------------------


def test_latex_writes_the_view_to_the_standard_output(
    file: Write, capsys: pytest.CaptureFixture[str]
) -> None:
    path = str(file(SMALL_TEXT))

    assert main(["latex", path]) == 0
    assert capsys.readouterr().out == to_latex(SMALL_TEXT)

    assert main(["latex", path, "--body"]) == 0
    assert capsys.readouterr().out == to_latex(SMALL_TEXT, standalone=False)


def test_latex_writes_the_view_to_a_file(
    file: Write, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    output = tmp_path / "view.tex"

    assert main(["latex", str(file(SMALL_TEXT)), "--output", str(output)]) == 0
    assert output.read_text(encoding="ascii") == to_latex(SMALL_TEXT)
    assert capsys.readouterr().out == ""


# --------------------------------------------------------------------------
# CLI-3: exit status, and nothing written on failure
# --------------------------------------------------------------------------


def test_latex_of_a_refused_file_says_why_and_writes_nothing(
    file: Write, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The line ``verify`` prints for the refusal, and no file."""
    path = str(file(REFUSED_TEXT))
    output = tmp_path / "view.tex"

    assert kellermap_check.__main__.main([path]) == 1
    checker = capsys.readouterr().out.splitlines()

    assert main(["latex", path, "--output", str(output)]) == 1
    assert capsys.readouterr().out.splitlines() == checker
    assert not output.exists()


def test_latex_of_a_file_that_cannot_be_read_exits_with_two(
    file: Write, tmp_path: Path
) -> None:
    assert main(["latex", str(tmp_path / "missing.json")]) == 2

    binary = tmp_path / "binary.json"
    binary.write_bytes(b"\xff\xfe")
    assert main(["latex", str(binary)]) == 2


def test_latex_to_an_output_that_cannot_be_written_exits_with_two(
    file: Write, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    output = tmp_path / "no such directory" / "view.tex"

    assert main(["latex", str(file(SMALL_TEXT)), "--output", str(output)]) == 2
    assert "cannot be written" in capsys.readouterr().err


@pytest.mark.parametrize(
    ("arguments", "status"),
    [
        pytest.param([], 2, id="no command"),
        pytest.param(["check"], 2, id="an unknown command"),
        pytest.param(["latex"], 2, id="latex without a file"),
        pytest.param(["--help"], 0, id="help"),
        pytest.param(["latex", "--help"], 0, id="help of latex"),
    ],
)
def test_a_wrong_call_exits_with_two(arguments: list[str], status: int) -> None:
    assert main(arguments) == status


def test_the_help_names_both_commands(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--help"]) == 0
    printed = capsys.readouterr().out

    assert "verify" in printed
    assert "latex" in printed


# --------------------------------------------------------------------------
# CLI-4: one program, two ways in
# --------------------------------------------------------------------------


def test_python_m_kellermap_is_the_program(file: Write) -> None:
    path = str(file(SMALL_TEXT))
    finished = subprocess.run(  # noqa: S603
        [sys.executable, "-m", "kellermap", "verify", path],
        capture_output=True,
        text=True,
        check=False,
    )

    assert finished.returncode == 0, finished.stderr
    assert finished.stdout.startswith("VERIFIED")


def test_the_module_runs_the_same_function() -> None:
    """``python -m kellermap`` imports ``main`` from ``kellermap.cli``.

    The subprocess above runs the module and is not measured by the coverage
    run, so the import is taken here once more.
    """
    module = importlib.import_module("kellermap.__main__")

    assert module.main is main


def test_main_reads_the_arguments_of_the_process(
    file: Write, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The entry point calls ``main()`` with no argument."""
    monkeypatch.setattr(sys, "argv", ["kellermap", "latex", str(file(SMALL_TEXT))])

    assert main() == 0
    assert capsys.readouterr().out == to_latex(SMALL_TEXT)


def test_the_entry_point_names_main() -> None:
    """The line of ``pyproject.toml`` that installs the program, CLI-4."""
    text = (Path(__file__).resolve().parent.parent / "pyproject.toml").read_text(
        encoding="utf-8"
    )

    assert '\n[project.scripts]\nkellermap = "kellermap.cli:main"\n' in text
