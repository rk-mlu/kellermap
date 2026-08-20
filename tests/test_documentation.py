"""What the documentation says about the code is looked up here.

Every audit of this milestone has found contradictions in the documentation,
and every time they were repaired one at a time. The reason that does not
suffice: an obligation is rewritten, and the places that mention it stay as
they are. Nobody falls over them, because nothing recomputes them.

The tests here recompute them. They do not check whether a text is good, which
no test can do. They check whether the claims in it still hold: whether a cited
obligation exists, whether a summary such as ``REV-1 to REV-12`` gives the
actual number, whether a signature in the normative sketch matches the one
built, and whether a formula carries the coefficient ``G`` has had since
BCW-11.

They replace no audit. What they replace is the question of whether all the
places were found this time.

Since 0.4.0rc9 every check stands twice: once over the files of the project and
once over a text with the fault deliberately written into it. Without the
second part there is no telling whether a check establishes anything or merely
happens to pass. The first gap the negative controls found was their own:
``FAMILIES`` left a family out.

This module reads itself as well, because it falls under ``CODE``. An example
of the wrong shape may therefore not stand here verbatim, and the negative
controls assemble their texts.
"""

import inspect
import re
from pathlib import Path

import pytest

from kellermap.bcw import BCWStep

ROOT = Path(__file__).resolve().parent.parent
CONTRACTS = (ROOT / "docs" / "contracts.md").read_text(encoding="utf-8")

# ``CONTRIBUTING.md`` stands here because it cites obligations. A stale
# identifier in a guide is the same defect as one in ``contracts.md``, and the
# guide is what a newcomer reads.
PROSE = sorted(
    [
        ROOT / "README.md",
        ROOT / "CONTRIBUTING.md",
        ROOT / "AGENTS.md",
        *(ROOT / "docs").glob("*.md"),
    ],
    key=lambda path: path.name,
)
CODE = sorted(
    [
        *(ROOT / "src" / "kellermap").rglob("*.py"),
        *(ROOT / "scripts").glob("*.py"),
        *(ROOT / "tests").glob("*.py"),
    ],
    key=lambda path: path.name,
)

# An identifier such as ``BCW-11`` at the start of an obligation: in bold,
# with a dash after it. Withdrawn ones stay on the page and count, because a
# reference to them is not a defect.
DEFINED = re.compile("^\\*\\*([A-Z]{2,4}-\\d+) \u2014", re.MULTILINE)
CITED = re.compile(r"\b([A-Z]{2,4}-\d+)\b")

# A range ``X-1 to X-n`` counts as a summary of the whole family when one of
# the words of ``CLAIMING_WORD`` stands in the same sentence. The words stand
# here and not additionally in a docstring: two lists diverge as soon as
# somebody extends one of them. Up to 0.4.0rc8 there were two, and they had
# diverged: ``state`` stood in the docstring and not in the expression, and
# ``siehe`` and ``obligations of`` the other way round.
#
# The word boundaries are needed and not ornament: without the leading one,
# ``state`` matches inside ``overstated``, and the expression reported the call
# of a negative control below as a stale range.
CLAIMING_WORD = re.compile(
    r"\b(?:see|siehe|under|state[sd]?|cover(?:s|ed)?|obligations? of)\b",
    re.IGNORECASE,
)

# The range itself. ``\s+`` and not one space: the summaries in the docstrings
# are wrapped at 79 columns, and ``LIN-1 to\nLIN-6`` is one sentence.
WHOLE_FAMILY = re.compile(r"\b([A-Z]{2,4})-1\s+(?:to|bis)\s+([A-Z]{2,4})-(\d+)\b")

# End of sentence: a full stop with whitespace after it, or a blank line. The
# stop in ``docs/contracts.md`` is neither. Up to 0.4.0rc8 the search for the
# signal word ran over a window of forty characters containing no full stop,
# and that file name stood inside it: of eleven summaries in the repository the
# check reached two, and all three docstrings of the form
# "See ``docs/contracts.md``, X-1 to X-n" lay outside.
SENTENCE_END = re.compile(r"\.\s|\n\s*\n")

# ``G`` in the shape ``X... |-> X... - A B``, that is with a *product* after
# the minus and no factor before it. A single quantity is the displacement of a
# ``TranslationStep`` and has no coefficient.
UNWEIGHTED_G = re.compile(
    r"X_?\{?\w*\}?\s*(?:\|--?>|->|\\mapsto|\u2192)\s*X_?\{?\w*\}?\s*-\s*"
    r"(?!coefficient\b|lambda\b|\\lambda\b|c\s+X|c\s*\*)"
    r"[A-Za-z]\w*\s*(?:\*|\s)\s*[A-Za-z]\w*"
)

# The families ``contracts.md`` carries. The list stands here and is not
# derived from the page: it is the promise of which families are checked, and a
# derived list could lose a family without anything showing. The step family
# was missing from it from 0.3 to 0.4.0rc8, and because both filters below
# sieve against ``FAMILIES``, every citation of that family went unchecked in
# that time.
FAMILIES = {
    "BCW",
    "COL",
    "DOM",
    "LIN",
    "RC",
    "RED",
    "REV",
    "SEA",
    "STEP",
    "TRA",
    "UNT",
}

# The version number stands in three places: in ``pyproject.toml``, in the
# project status of the README, and as the topmost heading of the changelog.
# The first is the binding one. ``tomllib`` does not exist on 3.10, and this
# one line needs no parser.
DECLARED_VERSION = re.compile(r'^version = "(.+)"$', re.MULTILINE)
README_VERSION = re.compile(r"^Current version: \*\*(.+)\*\*$", re.MULTILINE)
NEWEST_RELEASE = re.compile(r"^## (\S+)$", re.MULTILINE)

# A live marker such as ``[0.5]`` closing the bold title of an obligation the
# milestone has not implemented yet. ``AGENTS.md`` says it is removed when the
# milestone closes, and until now nothing said whether it had been.
#
# Closing the title, and not merely written somewhere: the page also talks
# about markers, and a sentence saying that 0.4 carried one is history rather
# than a marker. Those are written in backticks and this does not match them.
MILESTONE_MARKER = re.compile(r"(?<!`)\[(\d+)\.(\d+)\]\*\*")


def obligations() -> dict[str, set[int]]:
    """Return the numbers of every obligation the contract page defines."""
    found: dict[str, set[int]] = {}
    for identifier in DEFINED.findall(CONTRACTS):
        family, number = identifier.rsplit("-", 1)
        found.setdefault(family, set()).add(int(number))

    return found


DEFINITIONS = obligations()


def unknown_citations(text: str) -> set[str]:
    """Return every obligation ``text`` cites that the contract page lacks."""
    found = set()
    for identifier in CITED.findall(text):
        family, number = identifier.rsplit("-", 1)
        if family in FAMILIES and int(number) not in DEFINITIONS[family]:
            found.add(identifier)

    return found


def overstated_ranges(text: str) -> list[str]:
    """Return every range in ``text`` that claims a family and falls short.

    A sentence at a time, so that an enumeration is covered to its end: one
    ``See`` in front of four ranges makes a claim about all four, and a
    pattern anchored at the signal word reaches only the first.
    """
    found = []
    for sentence in SENTENCE_END.split(text):
        if not CLAIMING_WORD.search(sentence):
            continue
        found += [
            f"{first}-1 to {second}-{high}"
            for first, second, high in WHOLE_FAMILY.findall(sentence)
            if first == second
            and first in FAMILIES
            and int(high) != max(DEFINITIONS[first])
        ]

    return found


def unweighted_formulas(text: str) -> list[str]:
    """Return every occurrence of ``G`` in ``text`` written without a factor."""
    return UNWEIGHTED_G.findall(text)


def class_sketch(name: str) -> str:
    """Return the normative code block for ``name`` from the contract page."""
    sketch = CONTRACTS[CONTRACTS.index(f"class {name}") :]

    return sketch[: sketch.index("```")]


def unmentioned_parameters(sketch: str, parameters: set[str]) -> set[str]:
    """Return the parameters of a constructor that ``sketch`` does not name.

    The second form covers ``filtration_level``, which the sketch carries as
    the field ``level``.
    """
    return {
        parameter
        for parameter in parameters
        if parameter not in sketch
        and parameter.replace("filtration_", "") not in sketch
    }


def only_match(pattern: "re.Pattern[str]", path: Path) -> str:
    """Return the one group ``pattern`` finds in ``path``, or fail saying so."""
    found = pattern.findall(path.read_text(encoding="utf-8"))

    assert found, f"{path.name} does not carry {pattern.pattern}"

    return str(found[0])


def releases(path: Path) -> list[str]:
    """Return every release heading of a changelog, newest first."""
    found = NEWEST_RELEASE.findall(path.read_text(encoding="utf-8"))

    assert found, f"{path.name} carries no release heading"

    return [str(name) for name in found]


def formula(arrow: str, subtracted: str) -> str:
    """Build one line of the form ``X_index <arrow> X_index - <subtracted>``.

    Assembled rather than written out. This module is one of the files the
    scan below reads, so a literal example of the wrong form would make the
    module fail its own check.
    """
    return f"X_index {arrow} X_index - {subtracted}"


# --------------------------------------------------------------------------
# Over the files of the project
# --------------------------------------------------------------------------


def test_the_page_defines_exactly_the_families_that_are_checked() -> None:
    """Equality and not inclusion.

    Written as inclusion, ``contracts.md`` was allowed to carry a family that
    ``FAMILIES`` does not know, and that was exactly the case: the step family
    stood on the page from 0.3 and in no filter. The test ran green, because
    ``FAMILIES <= set(DEFINITIONS)`` is not violated by a missing family. A new
    family now forces this line to be maintained with it.
    """
    assert FAMILIES == set(DEFINITIONS)
    assert all(numbers for numbers in DEFINITIONS.values())


@pytest.mark.parametrize("path", PROSE + CODE, ids=lambda path: path.name)
def test_every_cited_obligation_exists(path: Path) -> None:
    """A reference to an obligation that does not exist is a defect.

    It arises from renumbering and from inventing from memory, and both have
    happened in this milestone.
    """
    unknown = unknown_citations(path.read_text(encoding="utf-8"))

    assert not unknown, f"{path.name} cites {sorted(unknown)}, which do not exist"


@pytest.mark.parametrize("path", PROSE + CODE, ids=lambda path: path.name)
def test_every_open_ended_range_reaches_the_last_obligation(path: Path) -> None:
    """A range that means to name *all* of them has to reach the last.

    Exactly these summaries go stale when an obligation is added: the sentence
    still looks right and is wrong.

    Not every range means to name all of them. ``verify`` checks the first
    seven of the twelve BCW obligations and no more, and that is a statement
    and not an oversight. What is caught is therefore only the ranges whose
    surroundings present them as complete. The words this is recognised by
    stand in ``CLAIMING_WORD``. Whoever means a selection writes it without
    those words, and whoever does not is caught here.
    """
    stale = overstated_ranges(path.read_text(encoding="utf-8"))

    assert not stale, (
        f"{path.name} presents {stale} as the whole family, which now runs to "
        f"{ {family: max(numbers) for family, numbers in DEFINITIONS.items()} }"
    )


def fenced_blocks(path: Path, heading: str) -> list[list[str]]:
    """Return the fenced blocks that follow ``heading`` in ``path``.

    Trailing comments are dropped from each line, because they explain and do
    not run. The blocks end at the next heading of the same level.
    """
    text = path.read_text(encoding="utf-8")
    after = text[text.index(heading) + len(heading) :]
    level = heading.split(" ")[0]
    section = after.split(f"\n{level} ")[0]

    blocks = []
    parts = section.split("```")
    for index in range(1, len(parts), 2):
        blocks.append(
            [
                line.split("#")[0].strip()
                for line in parts[index].splitlines()
                if line.strip()
            ]
        )

    return blocks


def gate_commands() -> list[str]:
    """Return the commands of the quality gate block in ``AGENTS.md``."""
    return fenced_blocks(ROOT / "AGENTS.md", "## Quality gates")[0]


def makefile_targets() -> set[str]:
    """Return every target the Makefile declares."""
    return {
        line.split(":")[0]
        for line in (ROOT / "Makefile").read_text(encoding="utf-8").splitlines()
        if line and not line[0].isspace() and ":" in line and not line.startswith("#")
    }


def makefile_recipes() -> list[str]:
    """Return every command the Makefile runs, without the ``uv run`` prefix."""
    return [
        line.strip().removeprefix("uv run ")
        for line in (ROOT / "Makefile").read_text(encoding="utf-8").splitlines()
        if line.startswith("\t")
    ]


def test_every_gate_of_the_agreements_is_a_command_the_makefile_runs() -> None:
    """Otherwise the list is a wish and the Makefile is the truth.

    A command in the block that no target runs is a gate nobody can fail. The
    comparison ignores the ``uv run`` prefix, which the Makefile carries and
    the prose does not.
    """
    recipes = makefile_recipes()
    unknown = [
        command
        for command in gate_commands()
        if not any(recipe.startswith(command) for recipe in recipes)
    ]

    assert not unknown, f"AGENTS.md names commands no target runs: {unknown}"


def test_the_gates_of_the_contributing_guide_exist() -> None:
    """The same for the guide, which said something the Makefile does not do.

    It stated that ``make check`` runs coverage and that ``make check-full``
    covers it as well. Coverage is a target of its own. The prose is corrected;
    what is checked here is narrower and mechanical: every target it names has
    to exist, and every command in its second block has to be one a target
    runs. A wrong sentence about what a target contains is not caught by this,
    and a reader has to keep noticing those.
    """
    blocks = fenced_blocks(
        ROOT / "CONTRIBUTING.md", "## Before you open a pull request"
    )
    targets = makefile_targets()
    recipes = makefile_recipes()

    named = [line.removeprefix("make ").strip() for line in blocks[0]]
    unknown_targets = [target for target in named if target not in targets]

    assert not unknown_targets, (
        f"CONTRIBUTING.md names no such target: {unknown_targets}"
    )

    unknown_commands = [
        command
        for command in blocks[1]
        if not any(recipe.startswith(command) for recipe in recipes)
    ]

    assert not unknown_commands, (
        f"CONTRIBUTING.md names commands no target runs: {unknown_commands}"
    )


def test_every_reconstruction_script_is_named_in_the_agreements() -> None:
    """The list went stale exactly here, and quietly.

    ``scripts/reconstruct_alpoege19.py`` has been a gate since 0.4 and
    ``make reconstruct`` has run it since 0.4.0rc9. ``AGENTS.md`` named two of
    the three, and nothing said so.
    """
    listed = " ".join(gate_commands())
    missing = [
        path.name
        for path in sorted((ROOT / "scripts").glob("reconstruct_*.py"))
        if path.name not in listed
    ]

    assert not missing, f"AGENTS.md does not name {missing}"


def test_the_class_sketch_matches_the_constructor() -> None:
    """The normative sketch in ``contracts.md`` against the signature built.

    The field ``coefficient`` was missing there for two release candidates
    after BCW-11 introduced it.
    """
    built = set(inspect.signature(BCWStep.build).parameters) - {"cls", "source"}
    missing = unmentioned_parameters(class_sketch("BCWStep"), built)

    assert not missing, f"the class sketch does not mention {sorted(missing)}"


@pytest.mark.parametrize("path", PROSE + CODE, ids=lambda path: path.name)
def test_no_formula_writes_G_without_its_coefficient(path: Path) -> None:
    """``G`` has scaled the removed product since BCW-11.

    After the change the unweighted formula still stood in four places, and
    three audits found it one after another.
    """
    unweighted = unweighted_formulas(path.read_text(encoding="utf-8"))

    assert not unweighted, f"{path.name} writes G unweighted: {unweighted[:3]}"


def test_no_milestone_marker_outlives_its_milestone() -> None:
    """``AGENTS.md`` says the marker goes when the milestone closes.

    It said so and nothing checked it. A marker names a milestone that has not
    been released, so the declared version has to be below it. Once
    ``pyproject.toml`` moves to ``0.5.0``, every ``[0.5]`` on this page fails
    here, which is what makes the removal a step somebody has to take rather
    than one somebody has to remember.
    """
    declared = only_match(DECLARED_VERSION, ROOT / "pyproject.toml")
    released = tuple(int(part) for part in declared.split("rc")[0].split("."))

    outlived = sorted(
        {
            f"[{major}.{minor}]"
            for major, minor in MILESTONE_MARKER.findall(CONTRACTS)
            if (int(major), int(minor), 0) <= released
        }
    )

    assert not outlived, f"the page still carries {outlived} at version {declared}"


def test_every_marker_closes_the_title_of_an_obligation() -> None:
    """A marker on nothing is a marker that will never be removed.

    Removing them at the end of a milestone is a walk down the list of
    obligations, so every one of them has to sit in an obligation's title. A
    marker in running prose would be missed by that walk and outlive the
    milestone in silence.
    """
    stray = [
        paragraph.splitlines()[0][:70]
        for paragraph in CONTRACTS.split("\n\n")
        if MILESTONE_MARKER.search(paragraph)
        and not DEFINED.match(paragraph.replace("\n", " "))
    ]

    assert not stray, f"a milestone marker stands outside an obligation: {stray}"


def test_the_three_places_that_carry_the_version_agree() -> None:
    """``pyproject.toml``, the project status in the README, the top heading.

    Three copies of one number, maintained by hand, and up to 0.4.0rc8 nothing
    compared them. ``pyproject.toml`` is the binding one and the other two have
    to follow it.
    """
    declared = only_match(DECLARED_VERSION, ROOT / "pyproject.toml")

    assert only_match(README_VERSION, ROOT / "README.md") == declared
    assert only_match(NEWEST_RELEASE, ROOT / "CHANGELOG.md") == declared


def test_no_release_appears_twice_in_the_changelog() -> None:
    """Comparing the version does not suffice when it stands there twice.

    In 0.4.0rc9 the heading ``## 0.4.0rc9`` stood on the page twice: a first
    section with the findings made internally and a second that merged them
    with the audit findings. The comparison above stayed green, because it
    takes the first heading it finds. An external audit saw it.
    """
    headings = releases(ROOT / "CHANGELOG.md")

    assert headings[0] == only_match(DECLARED_VERSION, ROOT / "pyproject.toml")
    assert len(headings) == len(set(headings)), (
        f"these releases appear more than once: "
        f"{sorted({name for name in headings if headings.count(name) > 1})}"
    )


# --------------------------------------------------------------------------
# The negative controls
#
# Each checks that the check above it fires when the fault is there, and that
# it leaves the permitted shape alone. A check without a negative control can
# be empty without anybody noticing.
# --------------------------------------------------------------------------


@pytest.mark.parametrize("family", sorted(FAMILIES))
def test_an_invented_obligation_is_caught_in_every_family(family: str) -> None:
    """In every one of them, and not only in those that came to mind.

    An invented number of the step family went through this gate up to
    0.4.0rc8, because the family did not stand in ``FAMILIES``. Parametrising
    over the families makes leaving a single one out impossible.
    """
    invented = f"{family}-99"

    assert 99 not in DEFINITIONS[family]
    assert unknown_citations(f"See {invented} for the rest.") == {invented}


@pytest.mark.parametrize("family", sorted(FAMILIES))
def test_a_real_obligation_is_not_caught(family: str) -> None:
    """Otherwise the check would find everything and establish nothing."""
    real = f"{family}-{min(DEFINITIONS[family])}"

    assert not unknown_citations(f"See {real} for the rest.")


def test_an_identifier_outside_the_families_is_not_examined() -> None:
    """An obligation looks different from an encoding or a standard."""
    assert not unknown_citations("Encoded as UTF-8, and see RFC-3629.")


@pytest.mark.parametrize("family", sorted(FAMILIES))
def test_a_range_that_stops_short_is_caught(family: str) -> None:
    """The case an addition of obligations produces."""
    last = max(DEFINITIONS[family])
    short = f"See {family}-1 to {family}-{last - 1}."

    assert overstated_ranges(short) == [f"{family}-1 to {family}-{last - 1}"]
    assert not overstated_ranges(f"See {family}-1 to {family}-{last}.")


def test_a_range_without_a_claiming_word_is_left_alone() -> None:
    """A selection is allowed and is to stay allowed.

    ``verify`` checks seven of the twelve BCW obligations, and a sentence about
    that is a statement and not a stale range.
    """
    last = max(DEFINITIONS["BCW"])

    assert not overstated_ranges(f"Check BCW-1 to BCW-{last - 5} and no more.")


def test_the_claiming_words_of_both_languages_are_recognised() -> None:
    """The expression carries both, and both occur in the repository."""
    short = max(DEFINITIONS["REV"]) - 1

    for phrasing in (
        f"See REV-1 to REV-{short}",
        f"Siehe REV-1 bis REV-{short}",
        f"under REV-1 to REV-{short}",
        f"It states REV-1 to REV-{short}",
        f"which covers REV-1 to REV-{short}",
        f"the obligations of REV-1 to REV-{short}",
    ):
        assert overstated_ranges(phrasing), phrasing


def test_a_file_name_between_the_word_and_the_range_does_not_hide_it() -> None:
    """The sentence the summaries of the source files stand in.

    ``docs/contracts.md`` carries two full stops, and a window without full
    stops ended before them. Three docstrings went unchecked that way.
    """
    short = max(DEFINITIONS["REV"]) - 1
    sentence = f"See ``docs/contracts.md``, REV-1 to REV-{short}, for the rest."

    assert overstated_ranges(sentence) == [f"REV-1 to REV-{short}"]


def test_an_enumeration_is_covered_to_its_end() -> None:
    """One signal word before four ranges says something about all four.

    ``reduction.py`` carries exactly one such enumeration. An expression
    anchored at the signal word reaches the first range of it.
    """
    last = max(DEFINITIONS["RED"])
    sentence = (
        f"See the obligations, STEP-1 to STEP-{max(DEFINITIONS['STEP'])}, "
        f"LIN-1 to LIN-{max(DEFINITIONS['LIN'])} and RED-1 to RED-{last - 1}."
    )

    assert overstated_ranges(sentence) == [f"RED-1 to RED-{last - 1}"]


def test_a_range_wrapped_across_a_line_is_still_one_range() -> None:
    """The docstrings are wrapped at 79 columns, in the middle of a range."""
    short = max(DEFINITIONS["LIN"]) - 1

    assert overstated_ranges(f"See LIN-1 to\n    LIN-{short}.") == [
        f"LIN-1 to LIN-{short}"
    ]


def test_a_claiming_word_in_another_sentence_does_not_reach_over() -> None:
    """Otherwise a single ``see`` colours a whole file."""
    short = max(DEFINITIONS["SEA"]) - 1

    assert not overstated_ranges(f"See the page. Here SEA-1 to SEA-{short} is meant.")


def test_a_claiming_word_inside_another_word_does_not_count() -> None:
    """The word boundary in the expression, with the case that forced it.

    ``overstated`` contains ``state``. Without the leading word boundary the
    expression reported the call of a negative control as a finding, and the
    module fell over its own check.
    """
    short = max(DEFINITIONS["REV"]) - 1

    assert not overstated_ranges(f"overstated_ranges REV-1 to REV-{short}")
    assert not overstated_ranges(f"understood REV-1 to REV-{short}")


def test_an_unweighted_G_is_caught() -> None:  # noqa: N802
    """The shape three audits found one after another."""
    assert unweighted_formulas(formula("|-->", "A * B"))
    assert unweighted_formulas(formula("->", "P Q"))
    assert unweighted_formulas(formula("\u2192", "P*Q"))


def test_a_weighted_G_is_not_caught() -> None:  # noqa: N802
    """The two ways of writing it that the repository uses."""
    assert not unweighted_formulas(formula("|-->", "coefficient * A * B"))
    assert not unweighted_formulas(formula("|->", "c X_u X_v"))


def test_a_translation_is_not_a_G() -> None:  # noqa: N802
    """A single quantity after the minus is the displacement.

    ``TranslationStep`` displaces by a constant, and that carries no
    coefficient. If the expression found it, TRA-1 could no longer be written
    down.
    """
    assert not unweighted_formulas(formula("|->", "c_index"))
    assert not unweighted_formulas(formula("|->", "shift"))


def test_a_missing_field_in_the_class_sketch_is_caught() -> None:
    """The case from the end of 0.4: BCW-11 came and the sketch lacked the field."""
    assert unmentioned_parameters("class BCWStep: source target", {"coefficient"})
    assert not unmentioned_parameters("class BCWStep: coefficient", {"coefficient"})


def test_the_sketch_carries_the_filtration_level_as_level() -> None:
    """The second spelling is a promise and not a lucky hit."""
    assert not unmentioned_parameters("level: int", {"filtration_level"})
    assert unmentioned_parameters("level: int", {"coefficient"})


def test_each_version_pattern_reads_its_own_file_and_not_another() -> None:
    """The three expressions must not find the same line.

    If ``README_VERSION`` found nothing and the comparison still gave a result,
    the check above would be empty.
    """
    assert DECLARED_VERSION.findall('version = "9.9.9"\nother = "1"') == ["9.9.9"]
    assert not DECLARED_VERSION.findall('python_version = "3.10"')
    assert README_VERSION.findall("Current version: **9.9.9**") == ["9.9.9"]
    assert NEWEST_RELEASE.findall("## 9.9.9\n\n## 9.9.8") == ["9.9.9", "9.9.8"]


def test_a_changelog_with_one_release_twice_is_caught(tmp_path: Path) -> None:
    """The control for the check that would have found the case of 0.4.0rc9."""
    doubled = tmp_path / "CHANGELOG.md"
    doubled.write_text("## 9.9.9\n\nfirst\n\n## 9.9.9\n\nsecond\n", encoding="utf-8")
    single = tmp_path / "single.md"
    single.write_text("## 9.9.9\n\n## 9.9.8\n", encoding="utf-8")

    names = releases(doubled)

    assert names == ["9.9.9", "9.9.9"]
    assert len(names) != len(set(names))

    other = releases(single)

    assert other == ["9.9.9", "9.9.8"]
    assert len(other) == len(set(other))


def test_a_changelog_without_a_release_heading_fails_loudly(tmp_path: Path) -> None:
    """Otherwise both checks above run against an empty list."""
    empty = tmp_path / "CHANGELOG.md"
    empty.write_text("# Changelog\n\nNotable changes per release.\n", encoding="utf-8")

    with pytest.raises(AssertionError, match="no release heading"):
        releases(empty)


def test_a_version_pattern_that_finds_nothing_fails_loudly(tmp_path: Path) -> None:
    """And not silently, because the comparison would then run against an
    empty list."""
    empty = tmp_path / "pyproject.toml"
    empty.write_text("[project]\n", encoding="utf-8")

    with pytest.raises(AssertionError):
        only_match(DECLARED_VERSION, empty)
