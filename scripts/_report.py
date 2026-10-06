"""What a script says about itself.

Two things several scripts need and none should write a second time: the
header a measurement prints before it spends anything, and the exit a script
takes when the data it checks is not in this tree.

It imports nothing from ``kellermap``. The reconstructions are a second
implementation of what the library computes, and a helper that imported the
library would make them depend on the thing they check. The versions it prints
come from the installed metadata for that reason.

Not part of the library and not a gate of its own.
"""

from __future__ import annotations

import datetime
import os
import platform
import subprocess
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

DATA = ROOT / "tests" / "data.py"
"""The file the source archive does not carry. ``docs/provenance.md`` says why."""

NOT_CHECKED = 3
"""The exit code of a script whose data is absent.

Not 0, because nothing was checked, and not 1, because nothing failed.
``scripts/gate_outcome.py`` counts it apart from both.
"""

GIGABYTE = 1024**3


def installed(name: str) -> str:
    """Return the installed version of a distribution, or say that there is none."""
    try:
        return version(name)
    except PackageNotFoundError:
        return "not installed"


def installed_memory() -> float:
    """Return the physical memory of the machine in gigabytes, where it is known."""
    try:
        pages = os.sysconf("SC_PHYS_PAGES")
        size = os.sysconf("SC_PAGE_SIZE")
    except (ValueError, OSError, AttributeError):
        return float("nan")

    return float(pages * size) / GIGABYTE


def now() -> str:
    """Return the local time with its zone and its offset from UTC."""
    moment = datetime.datetime.now().astimezone()

    return f"{moment:%Y-%m-%d %H:%M} {moment:%Z} (UTC{moment:%z})"


def tree() -> str:
    """Return the state of the working tree, as ``git describe`` gives it.

    The version of the package moves only when a milestone closes, so two
    records from different work packages carry the same version. The tag of
    the last work package and the number of commits since it tell them apart,
    and ``-dirty`` says that the tree had uncommitted changes. An unpacked
    source archive has no repository of its own, and says so.
    """

    def git(*arguments: str) -> str | None:
        try:
            done = subprocess.run(
                ["git", "-C", str(ROOT), *arguments],
                capture_output=True,
                text=True,
                check=False,
            )
        except OSError:
            return None
        return done.stdout.strip() if done.returncode == 0 else None

    # git looks upwards for a repository. The source archive is unpacked inside
    # the repository by sdist-test, and without this it would report the
    # repository around it as its own.
    top = git("rev-parse", "--show-toplevel")
    if top is None or Path(top).resolve() != ROOT.resolve():
        return "not a git tree"

    return git("describe", "--tags", "--dirty", "--always") or "not a git tree"


def facts() -> dict[str, str]:
    """Return what the header prints, as data, for a record that is written out.

    ``scripts/benchmark.py`` stores this beside its figures. A time from a
    record without it could not be compared with any other.
    """
    return {
        "started": now(),
        "machine": platform.node(),
        "platform": platform.platform(),
        "processors": str(os.cpu_count()),
        "memory": f"{installed_memory():.1f} GB",
        "python": platform.python_version(),
        "sympy": installed("sympy"),
        "kellermap": installed("kellermap"),
        "tree": tree(),
    }


def describe_the_run(asked: str | None = None) -> None:
    """Print the machine, the date and the versions, before anything is spent.

    ``AGENTS.md`` requires a runtime that is the subject of a sentence to be
    dated and to name its machine. A figure printed by a script without this
    header cannot be dated afterwards. ``measure_lift_determinant.py`` learned
    that first: its first run printed neither and had to be repeated.

    ``asked`` is the script's own line about its budget or its arguments.
    """
    print(f"Started  {now()}")
    print(f"Machine  {platform.node()}, {platform.platform()}")
    print(
        f"         {os.cpu_count()} logical processors, "
        f"{installed_memory():.1f} GB installed"
    )
    print(
        f"Versions Python {platform.python_version()}, "
        f"SymPy {installed('sympy')}, kellermap {installed('kellermap')}"
    )
    print(f"Tree     {tree()}")
    if asked is not None:
        print(f"Asked    {asked}")
    print(flush=True)


def describe_the_end() -> None:
    """Print the time again, so that the length of the run can be read off."""
    print(f"Finished {now()}", flush=True)


def require_data(what: str) -> None:
    """Stop with ``NOT_CHECKED`` if ``tests/data.py`` is absent.

    Called first in ``main``, before anything is computed, so that a script
    without its data says so in one sentence and does not fail somewhere inside
    with a traceback. Until milestone 0.8 three scripts failed in three
    different ways here, and ``make reconstruct`` stopped at the first.
    """
    if DATA.exists():
        return

    print(
        f"Not checked: {DATA.relative_to(ROOT)} is not in this tree. {what} "
        "The file is in the repository and not in the source archive."
    )
    raise SystemExit(NOT_CHECKED)
