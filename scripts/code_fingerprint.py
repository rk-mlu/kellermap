"""Fingerprint the code of every Python file, ignoring comments and docstrings.

Work packages 1 and 2 of milestone 0.5 translate comments and docstrings from
German into English. Neither changes a single instruction. A green test suite
does not establish that: it establishes only that the tests which exist still
pass, and a translation that changed a comparison operator inside an untested
branch would leave it green.

This script establishes it directly. It parses every Python file, removes the
docstrings, and prints a hash of the remaining syntax tree. Comments are not
part of a syntax tree, so they drop out by themselves. If the hashes before and
after a translation are equal, no instruction was touched.

It is not a gate. It compares one state of the tree with another, so it needs
both, and it is run by hand around a package rather than on every commit.

Usage::

    python scripts/code_fingerprint.py --save before.txt
    ...  translate  ...
    python scripts/code_fingerprint.py --check before.txt

``--check`` exits with 1 and names every file whose code changed.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

DIRECTORIES = ("src", "tests", "scripts")


def without_docstrings(tree: ast.Module) -> ast.Module:
    """Return the tree with every docstring removed.

    A docstring is the first statement of a module, class or function when that
    statement is a bare string. Only that position is removed. A string in any
    other position is a value the code uses, and removing it would hide a
    change rather than ignore one.
    """
    holders = (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)

    for node in ast.walk(tree):
        if not isinstance(node, holders) or not node.body:
            continue

        first = node.body[0]
        if (
            isinstance(first, ast.Expr)
            and isinstance(first.value, ast.Constant)
            and isinstance(first.value.value, str)
        ):
            node.body = node.body[1:]

            # A body must not become empty, otherwise the tree is no longer
            # valid Python and ``ast.dump`` reads differently from the code.
            # ``pass`` is the neutral replacement.
            if not node.body:
                node.body = [ast.Pass()]

    return tree


def fingerprint(path: Path) -> str:
    """Return a hash of the code in ``path``, without comments or docstrings."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    dumped = ast.dump(without_docstrings(tree), annotate_fields=True)

    return hashlib.sha256(dumped.encode("utf-8")).hexdigest()


def sources() -> list[Path]:
    """Return every Python file of the project, in a stable order."""
    found: list[Path] = []
    for directory in DIRECTORIES:
        found += [
            path
            for path in (ROOT / directory).rglob("*.py")
            if "__pycache__" not in path.parts
        ]

    return sorted(found)


def report() -> dict[str, str]:
    """Return the fingerprint of every Python file, keyed by relative path."""
    return {str(path.relative_to(ROOT)): fingerprint(path) for path in sources()}


def write(target: Path, prints: dict[str, str]) -> None:
    lines = [f"{digest}  {name}" for name, digest in prints.items()]
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")


def read(source: Path) -> dict[str, str]:
    prints = {}
    for line in source.read_text(encoding="utf-8").splitlines():
        digest, name = line.split("  ", 1)
        prints[name] = digest

    return prints


def differences(before: dict[str, str], after: dict[str, str]) -> list[str]:
    """Return one line per file whose code changed, was added or was removed."""
    lines = []
    for name in sorted(set(before) | set(after)):
        was, now = before.get(name), after.get(name)
        if was == now:
            continue

        if was is None:
            lines.append(f"added    {name}")
        elif now is None:
            lines.append(f"removed  {name}")
        else:
            lines.append(f"changed  {name}")

    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--save", type=Path, help="write the fingerprints to a file")
    parser.add_argument("--check", type=Path, help="compare against a saved file")
    arguments = parser.parse_args()

    prints = report()

    if arguments.save is not None:
        write(arguments.save, prints)
        print(f"{len(prints)} files fingerprinted, written to {arguments.save}")

        return 0

    if arguments.check is not None:
        changed = differences(read(arguments.check), prints)

        if changed:
            print(f"The code of {len(changed)} files is not what it was:")
            for line in changed:
                print(f"  {line}")

            return 1

        print(f"{len(prints)} files, code unchanged.")

        return 0

    for name, digest in prints.items():
        print(f"{digest}  {name}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
