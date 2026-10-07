"""What the library's computations cost, recorded so that releases can be compared.

Work package 5 of milestone 0.8. Not part of the library.

Two kinds of figure
-------------------

**Counts** do not depend on the machine: the monomials at each stage, the maps
a walk examines, and the calls of the operations that dominate the cost. Two
runs of the same code give the same counts on any machine, so a changed count
means that the computation changed. ``--compare`` fails on any difference.

**Times** depend on the machine and the day. ``AGENTS.md`` does not document
runtimes, so they are recorded beside the counts, with the header of
``scripts/_report.py``, and compared only when both records come from the same
machine. ``--compare`` reports them and never fails on them.

The calls are counted by wrappers that are put in place for the run and taken
out again. The library carries no counting code.

Every item runs in a fresh interpreter. The library caches on objects, and a
count taken after other work in the same process could depend on what ran
before it.

The reference
-------------

``scripts/benchmark_counts.json`` holds the counts of the items marked
``reference``, which take seconds. ``tests/test_scripts.py`` runs them and
compares. So a change that doubles the calls of ``clone_ring`` on the walk from
Alpoege's map fails the suite without anybody measuring a time. A change that
is meant to alter a count rewrites the reference with ``--reference``, and the
diff of that file is part of the change.

The other items take minutes and belong to ``make benchmark``, which is the
maintainer's. Times are not kept in the repository.

Usage::

    python scripts/benchmark.py --output run.json            # every item
    python scripts/benchmark.py --only reference --output r.json
    python scripts/benchmark.py --compare old.json new.json
    python scripts/benchmark.py --reference                   # rewrite counts
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from collections import Counter
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _report import ROOT, describe_the_end, describe_the_run, facts, now  # noqa: E402

REFERENCE = Path(__file__).resolve().parent / "benchmark_counts.json"

COUNTED = (
    ("kellermap.polynomial_map", "clone_ring"),
    ("kellermap.vanishing", "laplacian"),
)
"""Module functions whose calls are counted, by the module that defines them.

Every module of the library that holds the same function under the same name
is patched as well, since ``from .polynomial_map import clone_ring`` binds a
second reference that a patch of the defining module would not reach.
"""

COUNTED_METHODS = (("kellermap.bcw", "BCWStep", "build"),)
"""Class methods whose calls are counted."""


@dataclass(frozen=True)
class Item:
    """One computation, and whether its counts are held in the reference."""

    name: str
    reference: bool
    run: Callable[[], dict[str, int]]


# --------------------------------------------------------------------------
# Counting
# --------------------------------------------------------------------------


@contextmanager
def counting() -> Iterator[Counter[str]]:
    """Count the calls of ``COUNTED`` and ``COUNTED_METHODS`` while inside."""
    import importlib

    calls: Counter[str] = Counter()
    undo: list[Callable[[], None]] = []

    def wrap(label: str, function: Callable[..., Any]) -> Callable[..., Any]:
        def counted(*arguments: Any, **keywords: Any) -> Any:
            calls[label] += 1
            return function(*arguments, **keywords)

        return counted

    for module_name, attribute in COUNTED:
        original = getattr(importlib.import_module(module_name), attribute)
        wrapped = wrap(attribute, original)
        for name, module in list(sys.modules.items()):
            if (
                name.startswith("kellermap")
                and getattr(module, attribute, None) is original
            ):
                setattr(module, attribute, wrapped)
                undo.append(partial(setattr, module, attribute, original))

    for module_name, class_name, method in COUNTED_METHODS:
        owner = getattr(importlib.import_module(module_name), class_name)
        original_method = owner.__dict__[method]
        function = original_method.__func__
        label = f"{class_name}.{method}"
        setattr(owner, method, classmethod(wrap(label, function)))
        undo.append(partial(setattr, owner, method, original_method))

    try:
        yield calls
    finally:
        for restore in reversed(undo):
            restore()


# --------------------------------------------------------------------------
# The items
# --------------------------------------------------------------------------


def untargeted_alpoege() -> dict[str, int]:
    """The walk without a target from Alpoege's map, UNT-1 to UNT-5."""
    from kellermap import examples, over_field, reduce_to_degree3

    source = over_field(examples.alpoege())
    with counting() as calls:
        outcome = reduce_to_degree3(source)
    assert outcome.reduction is not None

    return {
        "examined": outcome.examined,
        "steps": len(outcome.reduction.steps),
        "dimension reached": outcome.reduction.target.dimension,
        **calls,
    }


def witness40() -> dict[str, int]:
    """Thompson's map compressed, lifted and verified as a witness, VAN-1 to VAN-4."""
    from kellermap import (
        CompressionStep,
        SymmetricLiftStep,
        VanishingWitness,
        examples,
        over_field,
    )

    pair = examples.thompson24_homogeneous_collision()
    with counting() as calls:
        compressed = CompressionStep.build(
            over_field(examples.thompson24_homogeneous()), pair
        )
        lift = SymmetricLiftStep.build(compressed.target)
        witness = VanishingWitness(lift, lift.transport(compressed.transport(pair)))
        witness.verify()
    form = lift._form()  # noqa: SLF001

    return {
        "monomials of P": len(form),
        "monomials of P^2": len(form**2),
        **calls,
    }


def chain(name: str) -> Callable[[], dict[str, int]]:
    """Return the item for one chain of the pipeline of milestone 0.6."""

    def run() -> dict[str, int]:
        from kellermap import (
            Collision,
            CompressionStep,
            LinearStep,
            SymmetricLiftStep,
            VanishingWitness,
            examples,
            over_field,
        )
        from kellermap.bcw import HomogenizationStep, UnipotentStep

        counts: dict[str, int] = {}
        with counting() as calls:
            source = over_field(getattr(examples, name)())
            pair = getattr(examples, f"{name}_collision")()
            if not source.is_in_MA(1):
                normalized = LinearStep.normalize(source)
                source, pair = normalized.target, normalized.transport(pair)
            stages: list[Any] = [UnipotentStep, HomogenizationStep]
            for stage in stages:
                step = stage.build(source)
                source, pair = step.target, step.transport(pair)
                counts[f"{stage.__name__} dimension"] = source.dimension
            compressed = CompressionStep.build(source, pair)
            pair = compressed.transport(pair)
            counts["CompressionStep dimension"] = compressed.target.dimension
            lift = SymmetricLiftStep.build(compressed.target)
            # The lift carries a pair, SYM-9; spacerat11 collides in three
            # points, and the first two are the pair the pipeline lifts.
            narrowed = Collision(pair.points[:2], pair.image)
            witness = VanishingWitness(lift, lift.transport(narrowed))
            witness.verify()
        form = lift._form()  # noqa: SLF001

        return {
            **counts,
            "monomials of P": len(form),
            "monomials of P^2": len(form**2),
            **calls,
        }

    return run


ITEMS: tuple[Item, ...] = (
    Item("untargeted from alpoege", True, untargeted_alpoege),
    Item("witness of thompson24", True, witness40),
    Item("chain from spacerat11", False, chain("spacerat11")),
    Item("chain from alpoege12", False, chain("alpoege12")),
    Item("chain from alpoege13", False, chain("alpoege13")),
)


# --------------------------------------------------------------------------
# Running, recording and comparing
# --------------------------------------------------------------------------


def run_one(name: str) -> None:
    """Run one item in this interpreter and print its counts as JSON."""
    item = next(item for item in ITEMS if item.name == name)
    started = time.perf_counter()
    counts = item.run()
    seconds = time.perf_counter() - started
    print(json.dumps({"counts": counts, "seconds": round(seconds, 2)}))


def run_isolated(name: str) -> dict[str, Any]:
    """Run one item in a fresh interpreter and return what it printed."""
    finished = subprocess.run(  # noqa: S603
        [sys.executable, str(Path(__file__).resolve()), "--item", name],
        capture_output=True,
        text=True,
        check=False,
        cwd=ROOT,
    )
    if finished.returncode != 0:
        raise SystemExit(f"{name} failed:\n{finished.stderr}")

    result: dict[str, Any] = json.loads(finished.stdout.splitlines()[-1])
    return result


def record(selection: str) -> dict[str, Any]:
    """Run the selected items and return the record of the run."""
    chosen = [item for item in ITEMS if selection == "all" or item.reference]
    # The header is taken before the first item, so that "started" is the
    # start and "tree" the tree the items ran in. Until 0.8.0rc2 it was taken
    # after the last one; an audit of 0.8.0rc1 found it.
    header = facts()
    items = {}
    for item in chosen:
        items[item.name] = run_isolated(item.name)
        print(f"  {item.name:<26} {items[item.name]['seconds']:8.2f} s", flush=True)

    header["finished"] = now()

    return {"header": header, "items": items}


def counts_of(record_: dict[str, Any]) -> dict[str, dict[str, int]]:
    """Return the counts of a record, item by item."""
    return {name: entry["counts"] for name, entry in record_["items"].items()}


def differences(
    old: dict[str, dict[str, int]], new: dict[str, dict[str, int]]
) -> list[str]:
    """Return one line per count that differs, is missing, or is new.

    Only items present in both are compared, so a run of the reference items
    can be held against a record of every item.
    """
    lines = []
    for item in sorted(set(old) & set(new)):
        before, after = old[item], new[item]
        for key in sorted(set(before) | set(after)):
            if before.get(key) != after.get(key):
                lines.append(
                    f"{item}: {key} was {before.get(key, 'absent')}, "
                    f"is {after.get(key, 'absent')}"
                )

    return lines


def machine(record_: dict[str, Any]) -> str | None:
    """Return the machine a record was taken on, or ``None`` for the reference."""
    header = record_.get("header")
    return None if header is None else str(header["machine"])


def compare(old: dict[str, Any], new: dict[str, Any]) -> int:
    """Print the differences of two records; fail on counts, never on times.

    The reference carries counts only. Against it, times are not compared at
    all, which is the point of keeping it free of them.

    Only the items both records carry are compared, so that the reference can
    be held against a record of every item. The items left out are named.

    A comparison fails where nothing was compared, because saying "counts
    agree" would then report a comparison that did not happen. That holds at
    two levels: two records with no item in common, and an item both records
    carry with no count in either. Every item of this runner produces counts,
    so the second case is a record written or edited by hand. A count of zero
    is a count. The audit of 0.8.0rc1 found the first case and the audit of
    0.8.0rc2 the second.
    """
    common = sorted(set(old["items"]) & set(new["items"]))
    if not common:
        print("  no item in common, so no count was compared")
        return 1

    old_counts, new_counts = counts_of(old), counts_of(new)
    sizes = {
        name: len(set(old_counts[name]) | set(new_counts[name])) for name in common
    }
    empty = [name for name in common if not sizes[name]]
    if empty:
        print(
            f"  no count in either record for {', '.join(empty)}, so nothing "
            "was compared there"
        )
        return 1

    print(
        "  compared: "
        + ", ".join(
            f"{name} ({sizes[name]} count{'s' if sizes[name] != 1 else ''})"
            for name in common
        )
    )
    for label, record_, other in (("old", old, new), ("new", new, old)):
        left_out = sorted(set(record_["items"]) - set(other["items"]))
        if left_out:
            print(f"  only in the {label} record: {', '.join(left_out)}")

    changed = differences(old_counts, new_counts)
    for line in changed:
        print(f"  count changed  {line}")

    before_machine, after_machine = machine(old), machine(new)
    if before_machine is None or after_machine is None:
        print("  times not compared: one of the two records has none")
    elif before_machine != after_machine:
        print(
            f"  times not compared: {before_machine} and {after_machine} are "
            "different machines"
        )
    else:
        for name in sorted(set(old["items"]) & set(new["items"])):
            before = old["items"][name]["seconds"]
            after = new["items"][name]["seconds"]
            print(f"  time {name:<26} {before:8.2f} s -> {after:8.2f} s")

    print("counts agree" if not changed else f"{len(changed)} counts changed")
    return 1 if changed else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--item", help=argparse.SUPPRESS)
    parser.add_argument("--only", choices=("all", "reference"), default="all")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--compare", nargs=2, type=Path, metavar=("OLD", "NEW"))
    parser.add_argument("--reference", action="store_true")
    arguments = parser.parse_args(argv)

    if arguments.item:
        run_one(arguments.item)
        return 0

    if arguments.compare:
        old, new = (json.loads(path.read_text()) for path in arguments.compare)
        return compare(old, new)

    selection = "reference" if arguments.reference else arguments.only
    describe_the_run(f"{selection} items")
    result = record(selection)
    describe_the_end()

    if arguments.reference:
        reference = {
            "items": {
                name: {"counts": counts} for name, counts in counts_of(result).items()
            }
        }
        REFERENCE.write_text(
            json.dumps(reference, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(f"wrote {REFERENCE.relative_to(ROOT)}")
    if arguments.output:
        arguments.output.write_text(json.dumps(result, indent=2) + "\n")
        print(f"wrote {arguments.output}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
