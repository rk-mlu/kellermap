"""Report prose words that do not occur in the English part of the repository.

``tests/test_language.py`` is a word list, and a word list only knows the words
somebody put in it. This script knows none, and that is its use. It collects
the English vocabulary the project already writes, and reports every word of a
comment or docstring that is not in it.

It is not a gate and cannot be one. Run over the modules translated in work
package 2 it reports 133 words, every one of them English: ``lengthens``,
``refutation``, ``quickstart``. A gate with 133 false reports is a gate nobody
reads.

Read once per module it is the sharpest instrument this project has for the
defect. It found twenty-eight German lines that the word list missed and that
two readings had missed as well, among them ``# Randfaelle``,
``# RC-1: Determinismus`` and ``# Komposition``. A German word stands out in a
list of English ones at a glance, which is exactly what a reader is good at and
a regular expression is not.

The English vocabulary is taken from ``docs/``, ``README.md``,
``CONTRIBUTING.md``, ``AGENTS.md``, ``src/``, ``scripts/``, the configuration
files, and the test modules already translated. Code identifiers are added from
every Python file, because ``xreplace`` is not a German word whatever a list
says. Text inside double backticks is dropped, because it quotes code.

Usage::

    python scripts/foreign_words.py tests/test_bcw17.py
    python scripts/foreign_words.py            # every module not yet translated
"""

from __future__ import annotations

import importlib.util
import io
import re
import sys
import tokenize
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

WORD = re.compile(r"[A-Za-z][A-Za-z]{2,}")
QUOTED_CODE = re.compile(r"``[^`]*``")


def prose(path: Path) -> str:
    """Return the comments and docstrings of ``path``, without quoted code."""
    text = path.read_text(encoding="utf-8")

    if path.suffix != ".py":
        return QUOTED_CODE.sub(" ", text)

    parts = []
    tokens = list(tokenize.generate_tokens(io.StringIO(text).readline))
    for index, token in enumerate(tokens):
        if token.type == tokenize.COMMENT:
            parts.append(token.string)
        elif token.type == tokenize.STRING:
            previous = tokens[index - 1].type if index else tokenize.NEWLINE
            if previous in (
                tokenize.INDENT,
                tokenize.NEWLINE,
                tokenize.NL,
                tokenize.DEDENT,
                tokenize.ENCODING,
            ):
                parts.append(token.string)

    return QUOTED_CODE.sub(" ", "\n".join(parts))


def identifiers(path: Path) -> set[str]:
    """Return every name the code of ``path`` uses, and its parts."""
    found: set[str] = set()
    for token in tokenize.generate_tokens(io.StringIO(path.read_text()).readline):
        if token.type == tokenize.NAME:
            found.add(token.string.lower())
            found |= {part for part in token.string.lower().split("_") if len(part) > 2}

    return found


def english(examined: set[Path]) -> set[str]:
    """Return the English vocabulary of the repository, excluding ``examined``.

    The paths are resolved before they are compared. A relative path never
    equals an absolute one, and the first version compared them directly: every
    module under review entered its own corpus, and the report came back empty.
    """
    left_out = {path.resolve() for path in examined}
    sources = [
        *sorted((ROOT / "docs").glob("*.md")),
        ROOT / "README.md",
        ROOT / "AGENTS.md",
        ROOT / "pyproject.toml",
        ROOT / "Makefile",
        ROOT / ".github" / "workflows" / "ci.yml",
        *sorted((ROOT / "src").rglob("*.py")),
        *sorted((ROOT / "scripts").glob("*.py")),
        *sorted(
            path
            for path in (ROOT / "tests").glob("*.py")
            if path.resolve() not in left_out
        ),
    ]

    known: set[str] = set()
    for path in sources:
        if not path.exists():
            continue
        known |= {word.lower() for word in WORD.findall(prose(path))}

    for path in sorted((ROOT / "src").rglob("*.py")) + sorted(
        (ROOT / "scripts").glob("*.py")
    ):
        known |= identifiers(path)

    return known


def remainder() -> list[Path]:
    """Return the modules ``tests/test_language.py`` still lists as untranslated.

    Loaded by path rather than imported, because ``tests`` is not a package.
    The first version of this function wrote the import as a nested
    ``__import__`` call to avoid a module-level import, and the call returned
    ``importlib.util`` where the code then asked for ``.util`` again. It never
    ran, because the default path was never tried.
    """
    path = ROOT / "tests" / "test_language.py"
    spec = importlib.util.spec_from_file_location("kellermap_language", path)

    if spec is None or spec.loader is None:  # pragma: no cover - the path exists
        raise SystemExit(f"{path} cannot be loaded.")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    listed: frozenset[str] = module.NOT_YET_TRANSLATED

    return [ROOT / "tests" / name for name in sorted(listed)]


def main() -> int:
    if len(sys.argv) > 1:
        examined = [Path(name).resolve() for name in sys.argv[1:]]
    else:
        examined = remainder()

    if not examined:
        print("Nothing to examine: the remainder is empty.")

        return 0

    known = english(set(examined))

    for path in examined:
        counted: Counter[str] = Counter()
        for word in WORD.findall(prose(path)):
            if word.lower() not in known:
                counted[word.lower()] += 1

        print(f"\n{path.name}: {len(counted)} words not used in English here")
        for word, count in sorted(counted.items()):
            print(f"  {count:3}  {word}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
