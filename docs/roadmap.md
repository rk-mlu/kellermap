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

**WP 2.1** answers an audit of WP 2 and is documentation only. It was added
when the audit asked for it before WP 3. The section "The audit of work
package 2" below says what changed.

**WP 2.2** is a restructuring that WP 2.1 made necessary. Every constructor
invariant that a file can break raises a `ValueError` that carries the
identifier of the obligation it enforces, and `VerificationError` gains a
`location`. Where `docs/contracts.md` names no obligation for an invariant, the
package names the one it serves and says so on that page. No check changes. It
comes before WP 3, because `loads` reads both, and it is a package of its own,
for the reason `AGENTS.md` gives for keeping a restructuring apart from an
extension.

**WP 3** is the exporter: a chain, a step and a witness to a file, and a file
back to the objects. Reading a file back and verifying it with the library is
the first control of the format.

*Done in WP 3.* `kellermap.certificate` holds `Certificate`, with `dumps`,
`loads` and `verify`. `tests/test_certificate.py` writes and reads back a
certificate of every step type and of every domain of FMT-5, and every
refusal of FMT-1 to FMT-12 has a control that names its identifier and its
place. Four things are worth stating.

The chains of the reconstruction scripts are built by `tests/chains.py`, from
the step data each script carries, with `build` for every step. Seven scripts
start from Alpoege's map. The eighth, `reconstruct_prellberg40.py`, compresses
and lifts Thompson's map, and that chain is built from `kellermap.examples`
with the fixtures of `tests/conftest.py`. All eight are written, read back and
verified. The ends of the seven are also compared with what each script
computes, which is the agreement CHK-8 will ask of the checker. That
comparison was not asked of WP 3. It is cheap, and it found nothing.

`BCWStep.build` takes the filtration level, and the scripts do not write it.
`tests/chains.py` declares the highest level the step attains, one where every
factor it introduces has order two and zero otherwise. A level that was too
high would fail BCW-6 when the chain is verified.

`dumps` refuses what it cannot write with a `VerificationError` and a
location, as `loads` does. The contract said "refused and cites" and did not
name the exception. The table of errors in `docs/contracts.md` now has the row.

`docs/api.md` gains a section on certificates. Its table of contents also gains
the section on the descent, which had been missing from it since 0.7.

**WP 4** is the independent checker. Plain Python and SymPy, as the
reconstruction scripts are. It reads a file and checks it, and a failure names
the obligation. Its controls are of two kinds. The eight reconstruction scripts
have to agree with it on their chains. And a file changed in one coefficient,
one slot or one point has to be refused, with the right identifier.

*Done in WP 4.* `src/kellermap_check` holds the checker: a reader of its own
for FMT-1 to FMT-9, the checks of CHK-4, and the command line of CHK-6.
`tests/test_checker.py` holds it to CHK-1 to CHK-8, and
`tests/test_packaging.py` finds it in the wheel and in the source archive. The
plan above predates the audit of WP 2. The controls follow CHK-8 as WP 2.1
amended it, not the last sentence of the plan. Five things are worth stating.

The determinant. On 2026-10-23, on the assistant's machine `vm` (two logical
processors, 7.8 GB, Python 3.10.20, SymPy 1.14.0), `DomainMatrix.det` of the
whole Jacobian did not finish within 240 seconds, on Thompson's map of 24
variables and on its compression of 20. The checker's Schur complement has
three rows on both, and its determinant took about a hundredth of a second
on each. Checking the whole file of each of the eight chains took less than a
second. The measurement ran from a script outside the tree. The size of the
complement is a property of the code, and a test holds it. So the checker
affords UNI-4, HOM-3, CHC-4 and SYM-4 on every chain, and nothing had to go to
the maintainer under CHK-4.

The two readers agree. The checker answers every refusal table of
`tests/test_certificate.py` with the identifier and the place the library
gives. The tables became module constants for that purpose, and the fixture of
the file with Thompson's witness moved to `tests/conftest.py`.

The negative controls of CHK-8 state their obligation, their place and their
reason in the test. One of them is cited differently by the two: a changed
dilation of a normalization is LIN-6 for the checker, which reads that clause
first, and LIN-1 for the library, which compares the identity first. The row
says so.

CHK-8 said that the two chains whose maps are in `tests/data.py` are skipped
where that file is absent. No chain needs that file, so nothing is skipped, and
the contract is amended. The sketch of `Report` gained `not_claimed`, which
CHK-7 asked for and the sketch did not hold.

Sixteen probes aim at the checker. They carry the checker's identifiers, so
`scripts/mutation_probe.py CHK` selects them. Two were missed on the first run
against `tests/test_checker.py`: a key twice in an otherwise valid file, and
the third clause of BCW-10. Both had no control in that file, and both have one
now.

Running the probes found a defect of the probe runner itself, which this
package does not repair. `tests/test_scripts.py` checks that the fragment of
every probe is in the code. Under a probe one fragment has been replaced, so
that test fails, and with it the fast suite. A whole sweep therefore reports
every probe as caught, whatever the other tests do. Two probes of WP 3 had no
control and were reported as caught for this reason: a key twice in an object,
FMT-1, and a witness on a step that is not a lift, FMT-9. Both have a control
now, in `tests/test_certificate.py` and `tests/test_checker.py`. The probes of
this package were run against the test files that hold their controls, which
do not include `tests/test_scripts.py`. The repair, and a control that the
runner can report a miss, are left to a work package of their own.

**WP 4.1** repairs the probe runner. It was added after WP 4, when the
maintainer asked for it before WP 5. It changes no obligation of
`docs/contracts.md` and nothing of the library.

*Done in WP 4.1.* The tests that read the probe set from the tree carry the
marker `probe_set`, and `scripts/mutation_probe.py` runs the fast suite without
them. Which tests those are was found by applying a probe that changes nothing
and running the whole fast suite: two failed, and nothing else. Every run now
starts with that probe as its control. It has to be missed, and a run whose
control is caught stops. `tests/test_scripts.py` holds the marker to those
tests, the runner's expression to the default of `pyproject.toml`, and, in a
project of its own, the runner to reporting a miss where there is one.
`docs/errata.md` records what the runs before reported.

The control found a third test on its first run. The test that a run stops
when its control is caught applies the control itself, so it fails under the
control. It carries the marker as well.

The repair does not say which probes of the set have a control. A whole sweep
says that, and it is the maintainer's. Each of its misses is a promise without
a control, and each is answered by a control or by a statement on the contract
page that the clause cannot fail on supplied data.

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

## The certificate file

Agreed when work package 2 was written. Four questions decided the shape of
the obligations, and the maintainer chose one answer to each.

- **How a file writes coefficients.** JSON, with every coefficient written in
  the structure of its domain: an integer or a rational as a string, an element
  of `QQ_I` as a pair, a polynomial as a list of exponent vectors and
  coefficients. Two alternatives were considered. Polynomials written as SymPy
  expressions are easier to read, but they need a parser, and the parser would
  be a second place for errors in a checker meant to have few. TOML needs
  `tomllib`, which Python has from 3.11, and the lower bound is 3.10.
- **Whether a chain writes every map or only its two ends.** Every map, once.
  With only the two ends, reading a file back would compute each target in the
  library. A step whose target the library computed is not `SUPPLIED` in the
  sense of BCW-9, so the label would be wrong. With every map written, the
  label is right, and BCW-1 and the other identities can fail on a file.
- **Where the checker lives.** In a package of its own, `kellermap_check`, in
  the wheel beside `kellermap`. A directory under `scripts/` would separate
  the two more visibly, but the command line of WP 6 could then not call the
  checker from an installed package. A module inside `kellermap` would make the
  independence a convention that nothing in the layout shows.
- **Which coefficient domains.** The ones the chains of this project use, and
  no others. Finite fields are left out: a chain over `GF(p)` carries no
  collision and no witness.

*Done in WP 2.* FMT-1 to FMT-12 and CHK-1 to CHK-8 stand in
`docs/contracts.md`, each with the marker of this milestone. Three things
differ from the plan or from the answers above.

The answer on domains named algebraic fields. FMT-5 admits quadratic fields
only, and only for collisions. Two measurements made while the obligation was
written are the reason, and the paragraph under FMT-5 gives both. In short,
SymPy compares algebraic fields by the expression that generated them, and
`kellermap.canonical` does not decide coordinates written through `CRootOf`. A
quadratic field avoids both problems and covers the one collision that needs an
extension.

The plan said documentation only. One test changed with it:
`tests/test_documentation.py` lists the families it checks and requires the
list to be the families the page defines, so FMT and CHK entered that list.

Four obligations the checker checks take a determinant. The library affords
them through the Schur complement of MAP-4, and whether the checker can is not
known. WP 4 measures it, and CHK-4 says what happens if it cannot.

The format is a new way for values to leave the repository, so it was checked
against the licence rule before anything was written. The result stands in
`docs/contracts.md` under "Files and the licence rule": the repository holds no
certificate file, and a test of WP 3 holds it to that.

### The audit of work package 2

An external audit read FMT-1 to FMT-12 and CHK-1 to CHK-8 before any of them
was implemented. It found no mathematical error and asked for nothing in the
four decisions above to change. It found two things to correct before WP 3 and
four to make precise. WP 2.1 answers all six, and each amendment in
`docs/contracts.md` says so where it stands.

- **CHK-8 promised a refusal for every change of one coefficient, slot or
  point.** That is false, and `docs/errata.md` records it. The finding is
  narrower than it reads: the next sentence of the paragraph already asked each
  control to name its obligation in advance. CHK-8 now asks for exactly that,
  and adds positive controls.
- **A check the checker cannot afford would still have ended in an
  acceptance.** CHK-6 now has three verdicts, `VERIFIED`, `INCOMPLETE` and
  `REFUSED`, and CHK-8 requires `VERIFIED` on the eight chains. `INCOMPLETE`
  needs a cause that a test can reach, so the checker takes a list of checks to
  leave out. Without one, the verdict would be code that no file reaches.
- **Errors of `loads` were of two kinds.** FMT-10 now has every refusal of a
  file cite an obligation and a location. The audit asked for a translation of
  the recognisable cases. Today no exception of a constructor carries its
  identifier, so `loads` would recognise none of them except by its message.
  That is why WP 2.2 exists. A copy of the invariants inside `loads` would also
  have answered the finding, with two implementations of each invariant in one
  library. It was not chosen.
- **The domain of a collision was not determined.** FMT-8 now fixes an order,
  and FMT-5 fixes the root that `sqrt(d)` names.
- **Edge cases of the syntax.** FMT-1 and FMT-6 now refuse a repeated key, a
  boolean where an integer belongs, `NaN`, a negative exponent and a vector of
  the wrong length, and they spell the zero polynomial. FMT-12 fixes the text
  byte by byte and the order of terms and of points.
- **Packaging and coverage.** CHK-2 now names the wheel, the source archive
  and the coverage threshold, and CHK-1 says what its test does.

The audit also asked what a file with one map certifies. Nothing, and CHK-7
now requires the report to say so.

*Done in WP 2.2.* `InvariantError` is a `ValueError` with an `obligation`, and
every constructor invariant of a step, a collision, a reduction and a witness
raises it. `VerificationError` has a `location`. `tests/test_errors.py` holds
one row per invariant, with the identifier the refusal has to carry. Some
invariants had no obligation named for them, and `docs/contracts.md` says
under its section on errors which one each now cites. Four things differ from
the plan or are worth stating.

The factor types and `PolynomialMap` keep a plain `ValueError`. They have no
obligations of their own, and FMT-10 already has `loads` cite LIN-2 or DSC-4
for a factor by its context. A name check of `PolynomialMap` is FMT-7, which
`loads` checks before it builds a map.

Refusals outside a constructor keep a plain `ValueError`: the refusals of
`LinearStep.normalize`, of `Collision.at` with no points, and of
`Collision.extended`. A file never reaches them.

The basis of a compression is converted by a helper that the hull and the
transport use as well. A point outside the domain is not a fault of a basis
there, so the constructor cites CHC-2 around the call and the helper raises
what it raised before.

Three examples of `docs/api.md` showed the traceback of a refused
construction, and they now show `InvariantError`. One example was added for
the new class, as every public feature has one.


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
