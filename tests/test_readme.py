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

# Ebenso fuer den Reduktionsblock.
REDUCTION_CLAIMS = {
    "dimensions": (3, 3, 5),
    "point": (
        sp.Integer(1),
        sp.Rational(-3, 2),
        sp.Rational(13, 2),
        sp.Rational(13, 4),
        sp.Integer(-1),
    ),
}


def python_blocks(text: str) -> list[str]:
    """Return the fenced ``python`` blocks of a Markdown document."""
    return re.findall(r"```python\n(.*?)```", text, re.DOTALL)


@pytest.fixture(scope="module")
def blocks() -> list[str]:
    if not README.is_file():
        pytest.skip("README.md is not available in this layout")

    found = python_blocks(README.read_text(encoding="utf-8"))

    assert found, "The README has no Python block left to check."

    return found


@pytest.fixture(scope="module")
def namespaces(blocks: list[str]) -> list[dict[str, Any]]:
    """Jeden Block einzeln ausfuehren, in einem eigenen Namensraum.

    Einzeln und nicht gemeinsam: ein Leser tippt einen Block ab, nicht die
    Summe aller vorherigen, und ein Block, der stillschweigend auf einer
    Zuweisung aus einem frueheren beruht, laeuft bei ihm nicht.
    """
    executed = []
    for block in blocks:
        namespace: dict[str, Any] = {}
        exec(compile(block, str(README), "exec"), namespace)  # noqa: S102
        executed.append(namespace)

    return executed


def test_every_readme_block_runs(namespaces: list[dict[str, Any]]) -> None:
    """Jeder Block muss ohne Vorbereitung durchlaufen.

    Faengt den Fall, dass eine Signatur sich aendert und das README es nicht
    mitbekommt -- der haeufigere Fehler, weil er niemandem auffaellt, der die
    Bibliothek schon kennt.
    """
    assert all(namespace for namespace in namespaces)


def test_the_readme_quickstart_says_the_truth(
    namespaces: list[dict[str, Any]],
) -> None:
    """Und die Werte muessen stimmen, die der erste Block behauptet."""
    F = namespaces[0]["F"]

    assert F.determinant() == QUICKSTART_CLAIMS["determinant"]
    assert F.degree() == QUICKSTART_CLAIMS["degree"]
    assert F.filtration_degree() == QUICKSTART_CLAIMS["filtration_degree"]
    assert F.extend(2).variables == QUICKSTART_CLAIMS["variables"]


def test_the_readme_reduction_says_the_truth(
    namespaces: list[dict[str, Any]],
) -> None:
    """Ebenso der zweite: eine Kette, die wirklich verifiziert."""
    if len(namespaces) < 2:
        pytest.skip("The README carries no reduction block")

    namespace = namespaces[1]
    reduction = namespace["reduction"]

    assert reduction.verify() is None
    assert reduction.dimensions() == REDUCTION_CLAIMS["dimensions"]

    carried = reduction.transport(namespace["collision"])

    assert carried.points[1] == REDUCTION_CLAIMS["point"]


def test_the_blocks_import_the_installed_package(blocks: list[str]) -> None:
    """Kein Block darf sich auf das Repository stuetzen.

    Ein Leser installiert das Paket und tippt ab; ein relativer Import oder
    ein Pfad aus dem Arbeitsbaum wuerde bei ihm scheitern und hier nicht.
    """
    for block in blocks:
        assert "kellermap" in block
        assert "src" not in block
        assert "sys.path" not in block
