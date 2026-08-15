"""The quickstart from the README.

The README is also the PyPI landing page. It is the first thing anyone sees of
this package and the only thing they read without installing it. An example
that no longer runs there is more expensive than a failed
Test.

What is checked is the code block itself and not a copy of it. Duplicating it
would allow exactly the divergence the test is meant to prevent.
"""

import re
from pathlib import Path
from typing import Any

import pytest
import sympy as sp

README = Path(__file__).resolve().parent.parent / "README.md"

# The values the quickstart claims in its comments. They stand here a second
# time, because no value can be extracted reliably from prose such as
# "# 2, from ord(F - X) = 3". Whoever changes one of them has to touch both
# places, and the test points at the other.
QUICKSTART_CLAIMS = {
    "determinant": sp.Integer(1),
    "degree": 3,
    "filtration_degree": 2,
    "variables": sp.symbols("x y X3 X4"),
}

# The same for the reduction block.
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
    """Run every block on its own, in a namespace of its own.

    On its own and not together. A reader copies one block and not the sum of
    all earlier ones, and a block that silently relies on an assignment from an
    earlier one does not run for them.
    """
    executed = []
    for block in blocks:
        namespace: dict[str, Any] = {}
        exec(compile(block, str(README), "exec"), namespace)  # noqa: S102
        executed.append(namespace)

    return executed


def test_every_readme_block_runs(namespaces: list[dict[str, Any]]) -> None:
    """Every block has to run without preparation.

    This catches a signature that changes while the README does not follow. It
    is the more common defect, because nobody who already knows the library
    notices it.
    """
    assert all(namespace for namespace in namespaces)


def test_the_readme_quickstart_says_the_truth(
    namespaces: list[dict[str, Any]],
) -> None:
    """And the values the first block claims have to be right."""
    F = namespaces[0]["F"]

    assert F.determinant() == QUICKSTART_CLAIMS["determinant"]
    assert F.degree() == QUICKSTART_CLAIMS["degree"]
    assert F.filtration_degree() == QUICKSTART_CLAIMS["filtration_degree"]
    assert F.extend(2).variables == QUICKSTART_CLAIMS["variables"]


def test_the_readme_reduction_says_the_truth(
    namespaces: list[dict[str, Any]],
) -> None:
    """The second as well: a chain that really verifies."""
    if len(namespaces) < 2:
        pytest.skip("The README carries no reduction block")

    namespace = namespaces[1]
    reduction = namespace["reduction"]

    assert reduction.verify() is None
    assert reduction.dimensions() == REDUCTION_CLAIMS["dimensions"]

    carried = reduction.transport(namespace["collision"])

    assert carried.points[1] == REDUCTION_CLAIMS["point"]


def test_the_blocks_import_the_installed_package(blocks: list[str]) -> None:
    """No block may rely on the repository.

    A reader installs the package and copies. A relative import or a path from
    the working tree would fail for them and not here.
    """
    for block in blocks:
        assert "kellermap" in block
        assert "src" not in block
        assert "sys.path" not in block
