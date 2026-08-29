"""The driver scripts, as far as they can be checked without a search run.

``scripts/`` holds two kinds of thing. The ``reconstruct_*`` scripts are gates
and run as whole programs; they need nothing here. The ``search_*`` scripts are
long runs with printed progress, and up to 0.4.0rc9 they had no test at all. An
external audit remarked on it and found a hang in the process.

What is checked is what can be decided without a full run: the rounds of the
doubling budget, and that the mutation probe does not touch the repository. The
rest of the scripts run a search or twelve test runs and therefore do not
belong in the fast suite.

The scripts are not a package. They are loaded by path, the way
``scripts/_common.py`` loads the fixed input under ``tests/``.
"""

import hashlib
import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parent.parent


def load(name: str) -> ModuleType:
    """Return a module under ``scripts/`` by path.

    The entry in ``sys.modules`` comes before ``exec_module`` and not after.
    While building a class, ``dataclasses`` looks up
    ``sys.modules[__module__]`` to resolve the names of deferred annotations,
    and without the entry it finds ``None``. ``mutation_probe`` has such a
    class and the search drivers do not, so the defect appeared only with the
    second file loaded.
    """
    path = ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"{name}_script", path)

    assert spec is not None and spec.loader is not None

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    return module


@pytest.fixture(scope="module")
def driver() -> ModuleType:
    return load("search_alpoege19")


def test_the_budget_doubles_and_stops_at_the_ceiling(driver: ModuleType) -> None:
    """The round that exceeds the ceiling is no longer run."""
    assert list(driver.rounds(1, 8)) == [1, 2, 4, 8]
    assert list(driver.rounds(3, 10)) == [3, 6]
    assert list(driver.rounds(5, 5)) == [5]


def test_a_first_budget_of_zero_is_refused(driver: ModuleType) -> None:
    """The hang, and why the check stands here and not in the search.

    Zero doubles to zero, so ``while budget <= ceiling`` ran without end and
    without printing a line. Both drivers had the loop written out and both
    hung; an external audit had to stop a run after a second.

    For ``search`` and ``peel`` zero is an admissible budget, since it examines
    nothing and says so, so the check must not go there.
    """
    with pytest.raises(ValueError, match="at least one"):
        list(driver.rounds(0, 100))

    with pytest.raises(ValueError, match="at least one"):
        list(driver.rounds(-1, 100))


def test_a_ceiling_below_the_first_budget_is_refused(driver: ModuleType) -> None:
    """Otherwise the driver reports no chain under a ceiling never tried."""
    with pytest.raises(ValueError, match="must not lie below"):
        list(driver.rounds(100, 10))


def test_the_check_happens_before_the_first_round(driver: ModuleType) -> None:
    """A generator otherwise checks only when somebody asks it.

    That is benign here, because both callers iterate over it at once. The test
    records that it stays so: the error comes at the first ``next`` and not
    after a search run has been made.
    """
    rounds = driver.rounds(0, 100)

    with pytest.raises(ValueError, match="at least one"):
        next(rounds)


# --------------------------------------------------------------------------
# The mutation probe
#
# Up to 0.4.0rc13 it changed the real ``src/`` and put it back with ``rmtree``
# and ``copytree``. After a run reported as successful, an external audit found
# three mutations left in the tree. The tests here check the promise that came
# out of that: the repository is not written to.
# --------------------------------------------------------------------------


@pytest.fixture(scope="module")
def probe() -> ModuleType:
    return load("mutation_probe")


def source_hashes() -> dict[str, str]:
    """Return a hash per Python file of the repository, path and content."""
    return {
        str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(ROOT.rglob("*.py"))
        if ".venv" not in path.parts and "__pycache__" not in path.parts
    }


def test_a_whole_sweep_leaves_the_repository_untouched(probe: ModuleType) -> None:
    """The regression for the finding.

    A whole sweep over every probe, with a stub in place of the test
    suite: what it checks is the copying and the restoring and not the running.
    The same hash over every Python file of the repository before and after.

    The stub reports ``CAUGHT`` so that the sweep counts no miss. What it
    reports is immaterial for this test.
    """
    before = source_hashes()

    missed = probe.sweep(probe.PROBES, run=lambda root: (True, "stub"))

    assert missed == 0
    assert source_hashes() == before


def test_every_fragment_still_matches_the_code_it_aims_at(probe: ModuleType) -> None:
    """A probe whose fragment has gone checks nothing any more.

    ``apply`` stops the run in that case, and because the sweep above applies
    every one of the probes, it is at the same time the freshness check
    of the whole set. This test says it once more on its own, so that a failure
    is readable.
    """
    for entry in probe.PROBES:
        text = (ROOT / entry.path).read_text(encoding="utf-8")

        assert entry.old in text, f"{entry.obligation}: {entry.what}"


def test_a_fragment_that_is_gone_stops_the_run(probe: ModuleType, tmp_path) -> None:  # type: ignore[no-untyped-def]
    """And reports which probe has to be brought up to date."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "thing.py").write_text("kept = 1\n", encoding="utf-8")
    gone = probe.Probe("COL-1", "a promise", "src/thing.py", "absent", "broken")

    with pytest.raises(SystemExit, match="not in src/thing.py any more"):
        probe.apply(gone, tmp_path)


def test_a_fragment_is_written_back_exactly(probe: ModuleType, tmp_path) -> None:  # type: ignore[no-untyped-def]
    """The one file is put back, and no directory is removed."""
    (tmp_path / "src").mkdir()
    path = tmp_path / "src" / "thing.py"
    path.write_text("kept = 1\nchecked = True\n", encoding="utf-8")
    entry = probe.Probe("COL-1", "a promise", "src/thing.py", "checked = True", "pass")

    original = probe.apply(entry, tmp_path)

    assert path.read_text(encoding="utf-8") == "kept = 1\npass\n"

    probe.restore(entry, tmp_path, original)

    assert path.read_text(encoding="utf-8") == "kept = 1\nchecked = True\n"


def test_the_working_copy_carries_what_the_suite_reads(
    probe: ModuleType,
    tmp_path,  # type: ignore[no-untyped-def]
) -> None:
    """The suite reads more than ``src/``.

    ``test_documentation.py`` reads ``docs/`` and ``README.md``,
    ``test_readme.py`` runs the blocks of the README, and the fixed input lies
    under ``tests/``. If one of them is missing from the copy, every probe
    reports ``CAUGHT`` for the wrong reason.
    """
    copy = probe.working_copy(tmp_path)

    for needed in ("src", "tests", "docs", "scripts", "README.md", "pyproject.toml"):
        assert (copy / needed).exists(), needed

    assert not (copy / ".venv").exists()
    assert copy.resolve() != ROOT.resolve()


# --------------------------------------------------------------------------
# The code fingerprint
#
# It is the control of work packages 1 and 2 of 0.5: a translation may touch
# no instruction. A tool that establishes a promise needs evidence of its own
# that it fires.
# --------------------------------------------------------------------------


@pytest.fixture(scope="module")
def fingerprints() -> ModuleType:
    return load("code_fingerprint")


def written(directory: Path, body: str) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "sample.py"
    path.write_text(body, encoding="utf-8")

    return path


def test_a_changed_docstring_leaves_the_fingerprint_alone(
    fingerprints: ModuleType,
    tmp_path: Path,
) -> None:
    """The case the work package produces."""
    first = written(
        tmp_path / "a",
        '"""Ein deutscher Docstring."""\n\n\ndef f(x: int) -> int:\n'
        '    """Gibt x zurueck."""\n    return x\n',
    )
    second = written(
        tmp_path / "b",
        '"""An English docstring."""\n\n\ndef f(x: int) -> int:\n'
        '    """Return x."""\n    return x\n',
    )

    assert fingerprints.fingerprint(first) == fingerprints.fingerprint(second)


def test_a_changed_comment_leaves_the_fingerprint_alone(
    fingerprints: ModuleType,
    tmp_path: Path,
) -> None:
    """Comments are not in the syntax tree and drop out by themselves."""
    first = written(tmp_path / "a", "# Ein Kommentar.\nvalue = 1\n")
    second = written(tmp_path / "b", "# A comment.\nvalue = 1\n")

    assert fingerprints.fingerprint(first) == fingerprints.fingerprint(second)


def test_a_changed_instruction_changes_the_fingerprint(
    fingerprints: ModuleType,
    tmp_path: Path,
) -> None:
    """The negative control. Without it a tool would be conceivable that
    always gives the same value and clears every translation.
    """
    first = written(tmp_path / "a", "def f(x: int) -> bool:\n    return x > 0\n")
    second = written(tmp_path / "b", "def f(x: int) -> bool:\n    return x >= 0\n")

    assert fingerprints.fingerprint(first) != fingerprints.fingerprint(second)


def test_a_string_that_is_not_a_docstring_is_kept(
    fingerprints: ModuleType,
    tmp_path: Path,
) -> None:
    """Only the first statement of a body is dropped.

    An error message is a value the code uses. Removing it would mean passing
    over a changed message rather than ignoring it.
    """
    first = written(tmp_path / "a", 'def f() -> None:\n    raise ValueError("one")\n')
    second = written(tmp_path / "b", 'def f() -> None:\n    raise ValueError("two")\n')

    assert fingerprints.fingerprint(first) != fingerprints.fingerprint(second)


def test_a_body_of_only_a_docstring_stays_valid(
    fingerprints: ModuleType,
    tmp_path: Path,
) -> None:
    """An empty body would no longer be valid Python."""
    only = written(tmp_path / "a", 'def f() -> None:\n    """Nur ein Docstring."""\n')
    passed = written(tmp_path / "b", "def f() -> None:\n    pass\n")

    assert fingerprints.fingerprint(only) == fingerprints.fingerprint(passed)


def test_the_report_names_what_changed(fingerprints: ModuleType) -> None:
    """A report that gives the number only is no help in searching."""
    before = {"a.py": "1", "b.py": "2", "c.py": "3"}
    after = {"a.py": "1", "b.py": "9", "d.py": "4"}

    assert fingerprints.differences(before, after) == [
        "changed  b.py",
        "removed  c.py",
        "added    d.py",
    ]

    assert not fingerprints.differences(before, before)


def test_the_repository_is_covered(fingerprints: ModuleType) -> None:
    """``src``, ``tests`` and ``scripts``, and nothing from ``__pycache__``."""
    covered = {str(path.relative_to(ROOT)) for path in fingerprints.sources()}

    assert "src/kellermap/peeling.py" in covered
    assert "tests/test_scripts.py" in covered
    assert "scripts/code_fingerprint.py" in covered
    assert not [name for name in covered if "__pycache__" in name]


# --------------------------------------------------------------------------
# The vocabulary instrument
#
# It reports prose words that do not occur in the English part of the
# repository. It is not a gate: over the translated modules it reports about a
# hundred words, all of them English. What it is good for is a list a reader
# scans once per module, and it is what found twenty-eight German lines that
# the word list of tests/test_language.py missed.
# --------------------------------------------------------------------------


@pytest.fixture(scope="module")
def foreign() -> ModuleType:
    return load("foreign_words")


def test_the_default_file_set_is_the_remainder(foreign: ModuleType) -> None:
    """The path that was never tried, and therefore never ran.

    Called without arguments the script examines the modules that
    ``tests/test_language.py`` still lists. That branch held a nested
    ``__import__`` call which raised ``AttributeError`` on every invocation.
    Nothing caught it, because every run during development passed a file name.

    The remainder is empty since work package 2 finished, so what is checked
    here is that the branch runs and reads the list, not what the list holds.
    An empty remainder is the expected state and not a reason to delete the
    test: the list is the record for the next language that gets one.
    """
    listed = foreign.remainder()

    assert all(path.parent.name == "tests" for path in listed)
    assert all(path.exists() for path in listed)


def test_the_script_runs_without_arguments(
    foreign: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """``main`` itself, and not only the function it calls.

    The defect was in ``main``, so a test of ``remainder`` alone would have
    passed while the script kept raising. It is driven here the way the
    maintainer drove it.
    """
    monkeypatch.setattr(foreign.sys, "argv", ["foreign_words.py"])

    assert foreign.main() == 0

    printed = capsys.readouterr().out
    listed = {path.name for path in foreign.remainder()}

    if not listed:
        assert "Nothing to examine" in printed

        return

    assert all(f"{name}:" in printed for name in listed)


def test_the_script_reports_on_a_named_module(
    foreign: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The other entry point, which is the one that stays useful.

    With the remainder empty, the test above no longer exercises a report. This
    one names a module and requires the report to appear, so that the reporting
    path keeps a test of its own.
    """
    monkeypatch.setattr(
        foreign.sys, "argv", ["foreign_words.py", "tests/test_peeling.py"]
    )

    assert foreign.main() == 0
    assert "test_peeling.py:" in capsys.readouterr().out


@pytest.mark.parametrize(
    "name",
    [
        "tests/test_peeling.py",
        "src/kellermap/peeling.py",
        "scripts/mutation_probe.py",
        "docs/contracts.md",
    ],
)
def test_the_file_under_review_is_not_its_own_corpus(
    foreign: ModuleType,
    name: str,
) -> None:
    """Two defects, and the second was hidden by a test that covered one case.

    The first version compared a relative path with an absolute one, so every
    file under review entered the vocabulary it was measured against and the
    report came back empty. The second resolved the paths and then dropped the
    file from the test modules alone, so a file under ``src/`` or ``scripts/``
    was still in its own corpus. The maintainer measured all three directories;
    the test written for the first defect used a test module and passed.

    Parametrised over the directories for that reason. One case is not the
    rule.
    """
    relative = Path(name)
    absolute = ROOT / name

    assert foreign.english({relative}) == foreign.english({absolute})

    # Taking the file out of the corpus has to remove words, otherwise the line
    # above compares two equal defects.
    assert foreign.english({absolute}) < foreign.english(set())

    # The report on an examined file is therefore not empty.
    known = foreign.english({relative})
    words = {word.lower() for word in foreign.WORD.findall(foreign.prose(absolute))}

    assert words - known


def test_the_corpus_holds_every_english_source(foreign: ModuleType) -> None:
    """The module says which files it reads, and it left one out.

    ``CONTRIBUTING.md`` is named in the description and was not in the list.
    """
    known = foreign.english(set())
    contributing = {
        word.lower()
        for word in foreign.WORD.findall(foreign.prose(ROOT / "CONTRIBUTING.md"))
    }

    assert contributing <= known


def test_prose_excludes_code_and_quoted_code(foreign: ModuleType) -> None:
    """Identifiers are not words, whichever language they look like."""
    text = foreign.prose(ROOT / "src" / "kellermap" / "guards.py")

    assert "bound" in text
    assert "raise TypeError" not in text
    assert not foreign.QUOTED_CODE.search(text)


# --------------------------------------------------------------------------
# The cost measurement
#
# Not a gate. It answers a question, like the mutation probe, and nothing in
# it is a promise. What is checked is that it runs and that the law it reports
# is the one the roadmap states.
# --------------------------------------------------------------------------


@pytest.fixture(scope="module")
def cost() -> ModuleType:
    return load("search_cost")


def test_the_term_law_holds_exactly_where_both_factors_are_monomials(
    cost: ModuleType,
) -> None:
    """The finding of work package 10, and the boundary work package 11 crossed.

    Terms grow by exactly ``2 + 2m`` when both factors are monomials: the step
    removes the monomial it acts on, puts three in its place, and each fresh
    coordinate brings a component of two terms. That is why term growth
    measured nothing on its own for the narrow enumerator.

    A factor with several terms puts more than three in place and breaks it,
    which is what the widened offer buys. The law is stated here as the
    condition it holds under rather than deleted, because it is what said that
    the gap was coverage and not order.
    """
    from kellermap import LinearStep, examples, over_field, reduce_to_degree3

    normalized = LinearStep.normalize(over_field(examples.alpoege())).target
    chain = reduce_to_degree3(normalized, budget=2000).reduction

    assert chain is not None

    monomial_steps = 0
    for step in chain.steps:
        grew = cost.terms(step.target) - cost.terms(step.source)
        if max(cost.factor_terms(step)) > 1:
            continue
        monomial_steps += 1

        assert grew == 2 + 2 * step.m, step

    assert monomial_steps, "no step has monomial factors; this test says nothing"


def test_the_untargeted_search_now_uses_multi_term_factors(
    cost: ModuleType,
) -> None:
    """What work packages 11 and 11.1 were for, as a number.

    Work package 10 found that the high-yield steps of the chains computed by
    hand all use a factor with several terms and that the narrow enumerator
    offered none, so no order over what it offered could reach them. UNT-6
    widened the offer and UNT-10 ordered it, and the chain the search finds now
    uses such factors.
    """
    from kellermap import LinearStep, examples, over_field, reduce_to_degree3

    normalized = LinearStep.normalize(over_field(examples.alpoege())).target
    chain = reduce_to_degree3(normalized, budget=2000).reduction

    assert chain is not None

    several = [step for step in chain.steps if max(cost.factor_terms(step)) > 1]

    assert several
    assert len(chain.steps) == 7


def test_the_cost_script_runs(
    cost: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """It is a report, so what is checked is that it produces one."""
    monkeypatch.setattr(cost.sys, "argv", ["search_cost.py"])

    assert cost.main() == 0

    printed = capsys.readouterr().out

    assert "bcw17, by hand" in printed
    assert "found without a target" in printed
