"""Measure the two eliminations on the complement SYM-7 rests on.

SYM-7 departs from UNI-10, HOM-7 and CHC-6 and does not compute the
determinant of the symmetric lift. The departure rests on a measurement: on
the thirty-eight-variable lift of ``spacerat11``, ``determinant()`` was
stopped after nineteen hours and forty-eight minutes without returning. That
run used the fraction-free elimination of ``DomainMatrix.det()``, and SYM-7
itself lists the elimination among the properties of the complement that were
never isolated.

``0.7.0rc12`` replaces that elimination with a division-free one, because the
old one divides and a residue ring has zero divisors. So the figure behind
SYM-7 belongs to a route the library no longer takes, and this script is what
settles whether that matters. It does not answer the question by itself: a run
that returns nothing after a long budget is evidence about that budget and not
a proof of anything.

Printed in order of cost, so that a run which never reaches the expensive part
still reports something:

* the three routes on dense polynomial blocks of growing size, which is where
  the ratio between them can be seen at all;
* the shape of the complement -- its size, its monomials, and what forming it
  costs;
* each route on the complement, under its own budget of time and of memory.

Three routes and not two. The division-free determinant is taken twice: once
by an algorithm that produces only the determinant, and once through the
characteristic polynomial, of which the determinant is the last coefficient.
The difference is not academic on this complement. Its determinant is ``1``,
a single term, and the coefficients in the middle of its characteristic
polynomial are the expensive ones: on the six-by-six complement of the same
chain, the determinant has one term and the largest middle coefficient has
147. Asking for the whole polynomial to read one coefficient off the end is
what made the first version of this script exhaust the maintainer's machine,
and ``docs/roadmap.md`` has the dated run that shows the difference.

The parts on the complement run in a forked child, because none of the three
can be interrupted from inside. The child inherits the complement rather than
receiving it, so nothing large is pickled; it limits its own address space, so
a route that runs away is stopped by a number this script chose rather than by
the machine; and it sends back a summary rather than the polynomial.

The limit is on the child's whole address space, and a forked child starts out
holding what the parent holds. So it has to clear what building the lift
already costs, which this script prints before it spends anything.

Usage: ``python scripts/measure_lift_determinant.py [--budget SECONDS]
[--memory GIGABYTES]``. Both apply to each route separately. The defaults are
small enough to be a smoke test and too small to answer anything; the run that
answers something is the maintainer's.
"""

from __future__ import annotations

import argparse
import datetime
import multiprocessing
import os
import platform
import resource
import sys
import time
from importlib.metadata import version
from pathlib import Path
from typing import Any

import sympy as sp
from sympy.polys.matrices import DomainMatrix

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from kellermap import (  # noqa: E402
    CompressionStep,
    LinearStep,
    PolynomialMap,
    SymmetricLiftStep,
    examples,
    over_field,
)
from kellermap.bcw import HomogenizationStep, UnipotentStep  # noqa: E402

DEFAULT_BUDGET = 60.0

DEFAULT_MEMORY = 8.0

LADDER = (4, 5, 6)
"""The default sizes of the synthetic part. ``--ladder`` replaces them.

Seven is left out of the default because the fraction-free elimination spends
minutes there, which is the point of the comparison and too much for a smoke
test. A run meant to be recorded passes it.
"""

GIGABYTE = 1024**3


def bird(block: Any, zero: Any) -> Any:
    """Return the determinant without dividing and without anything else.

    Bird's algorithm. ``mu(X)`` keeps the strict upper triangle of ``X`` and
    puts minus the trailing diagonal sum on the diagonal; ``n - 1`` rounds of
    ``X -> mu(X) A`` leave the determinant in the corner, up to the sign of
    ``n``. Only ring operations, so a domain with zero divisors is not a case.

    It holds ``n**2`` ring elements at a time and produces one polynomial at
    the end, where the characteristic polynomial holds and produces ``n + 1``.
    Checked against the Leibniz expansion on 160 integer matrices of sizes two
    to five and on 30 blocks over ``GF(4)[x,y,z]``, and against the
    characteristic polynomial on the ladder this script prints.
    """
    size = len(block)
    current = [list(row) for row in block]

    for _ in range(size - 1):
        shaped = [[zero] * size for _ in range(size)]
        for row in range(size):
            trailing = zero
            for index in range(row + 1, size):
                trailing = trailing - current[index][index]
            shaped[row][row] = trailing
            for column in range(row + 1, size):
                shaped[row][column] = current[row][column]
        current = [
            [
                sum((shaped[row][k] * block[k][column] for k in range(size)), zero)
                for column in range(size)
            ]
            for row in range(size)
        ]

    return (-1) ** (size + 1) * current[0][0]


def berkowitz(block: Any, domain: Any) -> Any:
    """Return the determinant as the last coefficient of the characteristic
    polynomial."""
    matrix = DomainMatrix.from_list([list(row) for row in block], domain)

    return (-1) ** len(block) * matrix.charpoly()[-1]


def fraction_free(block: Any, domain: Any) -> Any:
    """Return the determinant the way ``0.7.0rc11`` took it."""
    return DomainMatrix.from_list([list(row) for row in block], domain).det()


def installed_memory() -> float:
    """Return the physical memory of the machine in gigabytes, where it is known."""
    try:
        pages = os.sysconf("SC_PHYS_PAGES")
        size = os.sysconf("SC_PAGE_SIZE")
    except (ValueError, OSError, AttributeError):
        return float("nan")

    return float(pages * size) / GIGABYTE


def describe_the_run(arguments: argparse.Namespace) -> None:
    """Print what ``AGENTS.md`` requires a recorded runtime to carry.

    A runtime in this repository has to say when it was taken and on which
    machine, and ``docs/roadmap.md`` is where the profile lives. The first run
    of this script printed neither, and its figures could not be dated
    afterwards with certainty, so the run had to be repeated. The script now
    prints both before it spends anything, and the time again at the end.
    """
    started = datetime.datetime.now(datetime.timezone.utc)
    print(f"Started  {started:%Y-%m-%d %H:%M} UTC")
    print(f"Machine  {platform.node()}, {platform.platform()}")
    print(
        f"         {os.cpu_count()} logical processors, "
        f"{installed_memory():.1f} GB installed"
    )
    print(
        f"Versions Python {platform.python_version()}, SymPy {sp.__version__}, "
        f"kellermap {version('kellermap')}"
    )
    print(
        f"Asked    budget {arguments.budget:.0f} s and {arguments.memory:.1f} GB "
        f"per route, ladder {', '.join(str(size) for size in arguments.ladder)}"
    )
    print()


def measure_ladder(sizes: tuple[int, ...] = LADDER) -> None:
    """Report the three routes on dense blocks of growing size.

    Synthetic and not the complement. What it shows is whether they differ by
    a constant factor or by something that grows, which is the only part of
    the question a cheap run can reach.
    """
    print("Dense quadratic blocks over QQ, all three routes:")
    for size in sizes:
        ring = sp.ring(",".join(f"v{index}" for index in range(size)), sp.QQ)[0]
        generators = list(ring.gens)
        block = [
            [
                generators[(row + column) % size] * generators[(row * column) % size]
                + ring(row + column + 1)
                for column in range(size)
            ]
            for row in range(size)
        ]
        domain = ring.to_domain()

        started = time.monotonic()
        alone = bird(block, ring.zero)
        only = time.monotonic() - started

        started = time.monotonic()
        through = berkowitz(block, domain)
        polynomial = time.monotonic() - started

        started = time.monotonic()
        divided = fraction_free(block, domain)
        with_division = time.monotonic() - started

        mark = "ok " if alone == through == divided else "!! "
        print(
            f"  [{mark}] {size}x{size}: determinant only {only:7.3f} s, "
            f"characteristic polynomial {polynomial:7.3f} s, "
            f"fraction-free {with_division:8.3f} s"
        )


def lifted_map() -> PolynomialMap:
    """Return the symmetric lift of ``spacerat11``, by the route the pipeline takes."""
    source = over_field(examples.spacerat11())
    collision = examples.spacerat11_collision()

    normalization = LinearStep.normalize(source)
    source = normalization.target
    collision = normalization.transport(collision)

    unipotent = UnipotentStep.build(source)
    collision = unipotent.transport(collision)

    homogenized = HomogenizationStep.build(unipotent.target)
    collision = homogenized.transport(collision)

    compression = CompressionStep.build(homogenized.target, collision)

    return SymmetricLiftStep.build(compression.target).target


def complement_of(lift: PolynomialMap) -> Any:
    """Return the Schur complement of the unipotent block the lift carries."""
    carrier = lift.carrier_indices
    block = lift._schur_complement(carrier)  # noqa: SLF001

    if block is None:
        raise SystemExit("the carrier does not induce a unipotent block")

    return carrier, block


def peak() -> float:
    """Return the peak resident memory of this process, in gigabytes."""
    return float(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) * 1024 / GIGABYTE


def summarize(
    block: Any, domain: Any, zero: Any, route: str, limit: int, channel: Any
) -> None:
    """Take the determinant in a child and send back what it was, not the value.

    The child limits its own address space first. A route that runs away is
    then stopped by a number this script chose rather than by the machine, and
    it is stopped as a ``MemoryError`` this script can report rather than as a
    process the kernel removes.
    """
    resource.setrlimit(resource.RLIMIT_AS, (limit, limit))
    try:
        if route == "determinant only":
            value = bird(block, zero)
        elif route == "characteristic polynomial":
            value = berkowitz(block, domain)
        else:
            value = fraction_free(block, domain)
    except MemoryError:
        channel.send(("memory", peak()))
        return
    except Exception as failure:  # noqa: BLE001
        channel.send(("raised", type(failure).__name__))
        return

    terms = len(value.to_dict()) if hasattr(value, "to_dict") else 1
    channel.send(("returned", (terms, peak())))


def under_budget(
    block: Any, domain: Any, zero: Any, route: str, budget: float, memory: float
) -> None:
    """Run one route on the complement and stop it at the budget or the limit.

    None of the three can be interrupted from inside, so each runs in a forked
    child. The child inherits the complement instead of receiving it, which is
    why nothing here is pickled, and it sends back a summary rather than a
    polynomial with an unknown number of terms in it.
    """
    label = route
    context = multiprocessing.get_context("fork")
    here, there = context.Pipe()
    child = context.Process(
        target=summarize,
        args=(block, domain, zero, route, int(memory * GIGABYTE), there),
        daemon=True,
    )

    started = time.monotonic()
    child.start()
    child.join(budget)
    spent = time.monotonic() - started

    if child.is_alive():
        child.terminate()
        child.join()
        print(f"  [   ] {label}: nothing after the budget of {budget:.0f} s")
        return

    if not here.poll():
        print(
            f"  [!! ] {label}: the child ended without an answer after {spent:.1f} s, "
            f"which is what the kernel removing it looks like"
        )
        return

    outcome, detail = here.recv()
    if outcome == "memory":
        print(
            f"  [   ] {label}: reached the limit of {memory:.1f} GB after {spent:.1f} s"
        )
        return
    if outcome == "raised":
        print(f"  [!! ] {label}: {detail} after {spent:.1f} s")
        return

    terms, used = detail
    print(
        f"  [ok ] {label}: returned {terms} terms in {spent:.1f} s, peak {used:.2f} GB"
    )


def main() -> int:
    """Run the three parts in order of cost and report each as it finishes."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--budget", type=float, default=DEFAULT_BUDGET)
    parser.add_argument("--memory", type=float, default=DEFAULT_MEMORY)
    parser.add_argument("--ladder", type=int, nargs="+", default=list(LADDER))
    arguments = parser.parse_args()

    describe_the_run(arguments)

    started = time.monotonic()
    measure_ladder(tuple(arguments.ladder))
    print(f"  {time.monotonic() - started:.1f} s\n")

    started = time.monotonic()
    lift = lifted_map()
    building = time.monotonic() - started
    carrier, block = complement_of(lift)
    monomials = sum(len(entry.to_dict()) for row in block for entry in row)
    print("The complement of the symmetric lift of spacerat11:")
    print(f"  the lift has {lift.dimension} coordinates, built in {building:.1f} s")
    print(f"  the carrier holds {len(carrier)} of them")
    print(f"  the complement is {len(block)} by {len(block)}, {monomials} monomials")
    print(f"  building it left this process at {peak():.2f} GB")
    print(f"  {time.monotonic() - started:.1f} s\n")

    domain = lift.ring.to_domain()
    zero = lift.ring.zero
    print(
        f"Each route on it, {arguments.budget:.0f} s and "
        f"{arguments.memory:.1f} GB each:"
    )
    for route in ("determinant only", "characteristic polynomial", "fraction-free"):
        under_budget(block, domain, zero, route, arguments.budget, arguments.memory)
    print()
    print("A budget that runs out is evidence about the budget and not a proof.")
    finished = datetime.datetime.now(datetime.timezone.utc)
    print(f"Finished {finished:%Y-%m-%d %H:%M} UTC")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
