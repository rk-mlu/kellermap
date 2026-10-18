# Roadmap

The project follows an incremental development strategy. Every milestone should
leave the repository in a fully functional, typed, formatted, and tested state.

This page carries the open milestone and the long-term goals. The plans of the
milestones that have been released, 0.1 to 0.8, are in `docs/milestones.md`.
They were moved there in work package 1 of milestone 0.9. From then on a
milestone moves there in its release commit, and a test in
`tests/test_documentation.py` holds the two pages to the declared version.

---

# Version 0.9

Certificates outside the running process.

This section was rewritten when the milestone opened. The version before it was
a list of five items that had stood unchanged since the early milestones. Two
of them no longer fitted: there was no command line to improve, and the problem
with the documentation is its size and not its extent. The table under "What
the old list had" says where each item went.

## Why this milestone

A certificate exists today only as an object in the memory of one Python
process. When the process ends, what is left is the code that can build it
again. An independent check of it exists in one form: eight reconstruction
scripts, written by hand, one for each chain. Each repeats the reduction in
plain SymPy without the library. A new chain needs a new script.

Milestone 0.9 gives a certified chain and its witness a file. The file holds
what a reader needs to check the chain and nothing that can be derived from it.
A checker that does not import the library reads such a file and checks it.
The eight reconstruction scripts stay. They become the controls of the checker:
for each of the eight chains the checker and the script have to agree.

A file is also what a reader outside this project can use. A chain in a paper
can then point to a file and to a checker of a few hundred lines, rather than
to this library.

## The packages

Internal versions `0.8.k`, tags `wp/0.8.k`.

**WP 1** is this plan and a restructuring. It changes no `verify()` and adds no
check.

- The completed milestones move out of this page into `docs/milestones.md`.
  This page had grown past 3 600 lines, and a copy of a whole milestone in work
  package 1 of 0.8 passed every gate except a reader. The tests that read
  sections by their headings read the new page. The test against repeated
  milestones reads both pages as one, and a new test requires each milestone
  on the page its state asks for.
- The fast suite is profiled again, as at `0.7.0rc6`. The coverage run passes
  the assistant's limit per command since 0.8 and is run in two halves. The
  profile says whether a test should take the slow marker under the rule
  "What the fast suite costs" in `docs/milestones.md` states, and if not, what
  else helps. The section
  "What the fast suite costs at 0.8.0" below has the result.
- The convention for milestone markers in `docs/contracts.md` changes, as
  agreed below. The test that holds the markers to the version changes with it.
- LIN-7, TRA-9 and UNI-13 are stated in `docs/contracts.md`, marked `[0.9]`.
  The section below says what they are.

**WP 1.1** implements what WP 1 decided. LIN-7, TRA-9 and UNI-13 are checked in
`verify()`. A slow test holds the two new rows of the table below. Numbered 1.1
and not 2, as WP 2.1 of 0.7 was, because the packages behind it keep the
numbers they were agreed under.

**WP 1.2** draws the line between the changelog, the README and the pages of
the milestones. It was added after WP 1, when the maintainer asked whether
`docs/milestones.md` and `CHANGELOG.md` say the same things twice. It comes
before WP 1.1 because it is documentation and one test, and it is numbered
1.2 because 1.1 was already planned. The section "One home for a statement"
below says what it decided.

**WP 2** states the obligations of the file format in `docs/contracts.md`,
marked `[0.9]`, before anything is written. Documentation only. What the
obligations have to settle:

- which objects a file holds: maps, the steps of each type with their factor
  slots, collisions, a chain, and a witness;
- how coefficients are written. The chains here run over `ZZ`, over `QQ`, over
  `QQ(i)` after the lift, and over `ZZ[T]` in the parametric examples. A
  collision of Gao's map lives over `QQ(sqrt(-23))`;
- what a file holds and what the checker derives. The rule is the one of the
  certificates: exhibit, and derive rather than store twice. `G` and `H` are
  not stored;
- provenance. A file read back is `SUPPLIED`, whatever wrote it;
- which obligations the checker checks, by identifier, and which it leaves to
  the library. SYM-7 and VAN-5 are not computed by the library and are not
  computed by the checker;
- where the checker lives, and whether it ships in the wheel. It must not
  import `kellermap`, and `tests/test_scripts.py` already holds the
  reconstruction scripts to that.

**WP 3** is the exporter: a chain, a step and a witness to a file, and a file
back to the objects. Reading a file back and verifying it with the library is
the first control of the format.

**WP 4** is the independent checker. Plain Python and SymPy, as the
reconstruction scripts are. It reads a file and checks it, and a failure names
the obligation. Its controls are of two kinds. The eight reconstruction scripts
have to agree with it on their chains. And a file changed in one coefficient,
one slot or one point has to be refused, with the right identifier.

**WP 5** is a LaTeX export, as the first view of a certificate: a chain with
its steps, and a witness with its form. It is a view. Nothing in it is checked
beyond being generated from a file the checker accepts.

**WP 6** is a small command line: `kellermap verify FILE` and
`kellermap latex FILE`. It adds an entry point to `pyproject.toml` and no
behaviour that WP 3 to WP 5 do not already have.

Why this order. WP 1 is a restructuring and WP 1.1 an extension, and they are
two packages for the reason `AGENTS.md` gives. The obligations come before the
exporter for the reason the contracts always come first. The exporter comes
before the checker, because the checker needs files to read and the library
needs to read them back first. LaTeX and the command line come last, because
they only use what the earlier packages provide.

## Milestone markers

Agreed when the milestone opened. A marker such as `[0.9]` tells a reader of
`docs/contracts.md` on GitHub that an obligation belongs to a release that has
not been published. Release candidates are not published on PyPI or Zenodo. So
a marker now stays until the release itself and is removed in the release
commit, and not at the first release candidate.

Two things follow. An obligation added during the release-candidate cycle
carries the marker as well, which settles the question that
`docs/contracts.md` left open since `0.7.0rc10`. And a marker no longer means
that an obligation is unimplemented. It means that no published release has it.
The milestone paragraph of `docs/contracts.md` says which of the marked
obligations are implemented.

The test that holds the markers to the version read `0.8.0rc1` as `0.8.0`, and
that is why the markers of 0.8 went at the first candidate. It now reads a
candidate as below its release, so that `[0.9]` passes at `0.9.0rc2` and fails
at `0.9.0`. Both sides have a control.

## The conditional chain of Theorem 2.1(b)

Agreed when the milestone opened. HOM-12 says that a multi-affine source gives
a multi-affine target. It is conditional, and that is why it is safe on every
chain. But between `reduce_to_multi_affine`, which reaches the property under
UNT-12, and the homogenization lie the normalization and the unipotent step. If
one of them squared a variable, HOM-12 would pass silently. Today a test on one
chain covers this, and `docs/contracts.md` says under HOM-12 that the two steps
preserve the property by inspection.

The decision is to state it, because an obligation is visible to a reader
outside this project and a test is not. Three obligations, one for each step
type that can lie between the two ends:

- **LIN-7.** A multi-affine source gives a multi-affine target. Each component
  of the target is a linear combination of components of the source.
- **TRA-9.** The same. The target differs from the source by a constant.
- **UNI-13.** The same. The target is `(F_(2) + Y, -F_(3))` up to the
  elementary factors, built from homogeneous parts of the source and one linear
  block.

The decision named two of these. `TranslationStep` is the first factor of the
normalization, so a chain can carry one between the two ends, and leaving it
out would move the gap one step back rather than close it.

All three are self-checks in the sense `docs/contracts.md` uses. None of them
can fail after the identity of its step: LIN-1, TRA-1 and UNI-1 each fix the
target from the source and data the step derives or checks. So they get
`# pragma: no cover` with the argument beside it, and no probe, as HOM-11 and
HOM-12 did. The control is the one HOM-12 has: `squared_terms` on a map that
squares a coordinate. Each family's ranges in the docstrings of the package
move to the new last obligation, and the open-range test will find any that do
not.

*Done in WP 1.1.* One thing differs from this plan. LIN-7 and TRA-9 read
`squared_terms` through a helper in `kellermap.reduction` that imports it
inside the function. The function lives in `kellermap.bcw.grading`, importing
that package runs the step types there, and they import `Provenance` from
`kellermap.reduction`. A copy of the function would remove the cycle and add a
second implementation, so the import is local and says why. Moving the
function to a module outside `kellermap.bcw` would be the clean fix; it is a
restructuring and not part of this package. The hypothesis of the two checks
is code, so it has a control of its own that calls the helper directly.

## Two more rows through the four stages

Since 0.6 the roadmap had named a measurement as the next step and never run
it: `alpoege15` and `bcw17` through the four stages of the pipeline. It ran
while 0.8 was being closed:

| map | degree three | unipotent | homogeneous | compressed | lift |
| --- | ---: | ---: | ---: | ---: | ---: |
| `spacerat11` | 11 | 22 | 23 | 19 | 38 |
| `alpoege12` | 12 | 24 | 25 | 20 | 40 |
| `alpoege13` | 13 | 26 | 27 | 22 | 44 |
| `alpoege15` | 15 | 30 | 31 | 23 | 46 |
| `bcw17` | 17 | 34 | 35 | 23 | 46 |

The first three rows are those of `scripts/measure_pipeline.py`. The last two
are new. Both lifts have 46 variables and a form of 440 monomials, and both
witnesses verify.

Two maps that differ by two variables at degree three reach the same 23 after
compression. That weakens the assumption of 0.6 that the dimension at degree
three is a good proxy for the dimension of the lift. It is a hint and not a
result. Whether the two 23-dimensional maps are the same map has not been
checked.

The two rows do not go into `scripts/measure_pipeline.py`. Each takes about
half a minute on the assistant's machine, most of it in the compression, which
would double the script. They become one slow test in WP 1.1, which holds the
five dimensions of each row and the 440 monomials. It runs in `pytest -m ""`
and in `make release`, and not in the fast suite, so not in any mutation probe.

*Done in WP 1.1.* `tests/test_lift.py` reads the table from this section and
holds the last two rows by computing them, with every step and both witnesses
verified. The first three rows repeat figures of the references page, so a
fast test holds them against the table of `scripts/measure_pipeline.py`, with
a control that changes one cell.

## One home for a statement

Agreed after WP 1, when the move to `docs/milestones.md` made the overlap with
`CHANGELOG.md` visible. The overlap was older than the move. For 0.8 the
changelog repeats five figures of the milestone, and only the copy in the
milestone is held by a test. The README repeated one of them a third time.

Two ways were considered. One keeps both pages and gives each kind of
statement one home. The other dissolves `docs/milestones.md`: the measurements
would go to a page of their own, the reasons to `docs/architecture.md`, and
the plans would stay reachable through the tags. The second is the cleaner
cut, but it means reading 3 600 lines section by section and repointing many
references, in a milestone whose subject is something else. The first was
chosen. The second can come back after 0.9.

The rules are in `AGENTS.md` under "Where a statement lives". A figure lives
where a test holds it, and other pages point to it. The changelog says what
changed and carries no figure a table holds; a test checks the large ones in
every entry from 0.9 on, and its control is the entry of 0.8, which repeats
the count of the Laplacian table. A released milestone is not edited, and a
correction goes to `docs/errata.md`. The README section on 0.8 lost its two
figures to a pointer.

The entries and sections written before 0.9 stay as they were released.

## What the fast suite costs at 0.8.0

Profiled when the milestone opened, on 11 October 2026, on the assistant's
machine `vm`, with two processors and seven gigabytes. `AGENTS.md` says under
"Timings are not figures" why seconds stand only in such a profile. They are a
record of these runs and not a statement about the present. What matters is
the comparison, and every run below is on the same machine on the same
evening.

| tree | fast suite, seconds |
| --- | ---: |
| `v0.7.0` | 204 |
| `v0.8.0` | 265 |
| this work package | 222 |

The profile of `0.7.0rc6` gave 84 seconds for the fast suite. The machine has
probably changed since: the three multi-affine chains took 8.4 seconds in that
profile and 18 seconds on `v0.7.0` here. A comparison across days is not worth
making. The machine also varies within a day. Two coverage runs of trees that
differed only in their documentation took 238 and 417 seconds this afternoon. A
figure from one run says little, and the table above compares runs taken one
after another.

Milestone 0.8 added nearly a third to the suite. Most of it is in three
places: the example of the witness in `docs/api.md`, the fixture of the witness
in `tests/test_vanishing.py`, and the gate on the benchmark counts.

| | seconds | what was done |
| --- | ---: | --- |
| the doctests of `docs/api.md` | 29 | stays; every public feature has an example |
| the three multi-affine chains | 19 | stays, as at `0.7.0rc6` |
| the gate on the benchmark counts | 18 | stays; `CHANGELOG.md` promises it as a gate of the suite |
| the two weighted cases of SEA-14 | 18 | stays, as at `0.7.0rc6` |
| Thompson's map compressed, three times | 21 | built once per session in `tests/conftest.py` |
| the corpus checks of `scripts/` | 35 | the whole vocabulary is read once per module, not five times |

The last two rows were repeated work. The compression of Thompson's map was
built in `test_compression.py`, `test_lift.py` and `test_vanishing.py`, and
each is the same value. The corpus tests read the whole tree four times for
each of four files, and one of the four reads was always the same. Neither
change alters what a test checks.

No test earns the slow marker under the rule of `0.7.0rc6`. The largest is the
file of doctests, which cannot be marked in part. The next three are each the
only check of something a page states. The doctest of the witness and the
fixture of `tests/test_vanishing.py` still verify the same witness twice, once
as an example a reader runs and once as the subject of VAN-1 to VAN-5. They
stay apart, because an example in `docs/api.md` has to run without a fixture.

The coverage run is now taken in three parts and not in two. `AGENTS.md` says
how it is cut.

## What the old list had

| item | where it went |
| --- | --- |
| history and certificate inspection | the file of WP 2 and the checker of WP 4 |
| LaTeX export | WP 5 |
| visualization | not planned; first it has to be clear which object it shows |
| command-line improvements | WP 6, a command line where there was none |
| extended documentation | WP 1, which makes this page shorter |

## What is not planned

No new mathematics. No new step type, no new search, and no figure that
changes. The research questions 0.7 and 0.8 left open go to a milestone of
their own, because mixing them with a milestone about files would make both
hard to audit. They are:

- a search that may go up in dimension;
- proposals for `DescentStep`;
- pairs of levers;
- SYM-7 in full, for instance through a determinant modulo primes;
- whether this project's 19 and van Rijn's 19 are linearly equivalent, and
  denser against sparser bases, 386 against 340 monomials;
- whether the two 23-dimensional maps above are the same.

No format for intermediate results of a search. A file holds a certificate,
and a search that has not finished has none.

No minimality and no priority, as in every milestone before.

---

# Long-term Goals

- dimensions well beyond the current benchmark,
- reproducible and independently replayable reduction certificates,
- publishable heuristic and benchmark results,
- optional accelerated arithmetic without changing certificate semantics,
- automated verification of complete BCW reductions.
