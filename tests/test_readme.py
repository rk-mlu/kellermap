"""Der Quickstart aus dem README.

Das README ist zugleich die PyPI-Landeseite: es ist das Erste, was jemand von
diesem Paket sieht, und das Einzige, was er ohne Installation liest. Ein
Beispiel, das dort nicht mehr laeuft, ist teurer als ein fehlgeschlagener
Test.

Geprueft wird der Codeblock selbst, nicht eine Kopie davon. Duplizieren wuerde
genau die Abweichung erlauben, gegen die der Test schuetzen soll.
"""

import re
from pathlib import Path
from typing import Any

import pytest
import sympy as sp

README = Path(__file__).resolve().parent.parent / "README.md"

# Die Werte, die der Quickstart in seinen Kommentaren behauptet. Sie stehen
# hier ein zweites Mal, weil sich aus Prosa wie "# 2, from ord(F - X) = 3"
# kein Wert zuverlaessig herausloesen laesst. Wer einen davon aendert, muss
# beide Stellen anfassen -- der Test verweist auf die andere.
QUICKSTART_CLAIMS = {
    "determinant": sp.Integer(1),
    "degree": 3,
    "filtration_degree": 2,
    "variables": sp.symbols("x y X3 X4"),
}


def python_blocks(text: str) -> list[str]:
    """Return the fenced ``python`` blocks of a Markdown document."""
    return re.findall(r"```python\n(.*?)```", text, re.DOTALL)


@pytest.fixture(scope="module")
def quickstart() -> str:
    if not README.is_file():
        pytest.skip("README.md is not available in this layout")

    blocks = python_blocks(README.read_text(encoding="utf-8"))

    assert len(blocks) == 1, (
        "The README gained or lost a Python block; this test covers exactly one."
    )

    return blocks[0]


def test_the_readme_quickstart_runs(quickstart: str) -> None:
    """Der Block muss ohne Vorbereitung durchlaufen.

    Faengt den Fall, dass eine Signatur sich aendert und das README es nicht
    mitbekommt -- der haeufigere Fehler, weil er niemandem auffaellt, der die
    Bibliothek schon kennt.
    """
    namespace: dict[str, Any] = {}

    exec(compile(quickstart, str(README), "exec"), namespace)  # noqa: S102

    assert "F" in namespace


def test_the_readme_quickstart_says_the_truth(quickstart: str) -> None:
    """Und die Werte muessen stimmen, die er in den Kommentaren nennt."""
    namespace: dict[str, Any] = {}

    exec(compile(quickstart, str(README), "exec"), namespace)  # noqa: S102

    F = namespace["F"]

    assert F.determinant() == QUICKSTART_CLAIMS["determinant"]
    assert F.degree() == QUICKSTART_CLAIMS["degree"]
    assert F.filtration_degree() == QUICKSTART_CLAIMS["filtration_degree"]
    assert F.extend(2).variables == QUICKSTART_CLAIMS["variables"]


def test_the_quickstart_imports_the_installed_package(quickstart: str) -> None:
    """Der Block darf sich nicht auf das Repository stuetzen.

    Ein Leser installiert das Paket und tippt ab; ein relativer Import oder
    ein Pfad aus dem Arbeitsbaum wuerde bei ihm scheitern und hier nicht.
    """
    assert "from kellermap import" in quickstart
    assert "src" not in quickstart
    assert "sys.path" not in quickstart
