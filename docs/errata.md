# Errata

What this project reported wrongly, and what is true instead.

Split out of `docs/references.md` in work package 9 of milestone 0.6. That page
had accumulated a dozen paragraphs of the form "this said X until Y", which are
worth keeping and were making the page hard to read as a statement of what is
known. They are here, and `docs/references.md` states the current position
without the history.

What is *not* here is the reason a present sentence is worded as it is, even
where that reason came out of a correction. The eight hours behind SYM-7, the
timezone caveat on the announcement's timestamp, and the difference between
what `peel` divides and what the enumerator splits all stay where they are. A
page of rules without their reasons invites the next reader to question the
rule instead of finding the reason.

Each entry says what was written, what is true, how it was found, and where the
corrected statement lives now. They are in the order the errors were made.

---

## Proposition (1.1) and Section 4 were swapped

**Said, in 0.1 and 0.2:** the citation table gave Section 4 for the linear
normalization and Chapter II, Proposition (1.1) for the Reduction Theorem.

**True:** the other way round. Proposition (1.1), p. 303, is the linear
normalization; Section 4 is the proof of the Reduction Theorem.

**Found** by a source check in 0.2, which is why `AGENTS.md` now says to cite
the paper precisely and names this pair as the reason.

## `bcw17` was called somebody else's mathematics

**Said, before 0.4:** that for the seventeen-dimensional map "the other side is
someone else's mathematics", so the agreement of the library with it was
evidence about an external result.

**True:** the components are the maintainer's own hand computation, checked
against `scripts/reconstruct_bcw17.py`. They are external to the *library* and
not external to the *project*, which is the distinction `AGENTS.md` asks for
and the sentence collapsed.

**Consequence:** before 0.4 exactly two things in this repository were somebody
else's mathematics, Alpöge's three-dimensional map and the nineteen-dimensional
one. `docs/provenance.md` says which are which now.

## The `w`-numbering was read as a chronology

**Said, before 0.4:** that the `w`-numbering of the published nineteen-
dimensional map is not the order of introduction, on the evidence that the
component of `w2` mentions `w9` and `w13`.

**True:** the component of `w2` is the residue of a later step and not an
introduced value, so it says nothing about when `w2` arrived. With the
introduced value in its place, every dependency points to a smaller index.

**Where:** `tests/data.py` holds the values and `tests/test_alpoege19.py`
records both readings. The paragraph that made the claim is left standing in
`docs/roadmap.md`, withdrawn rather than deleted.

## One table row for three pages

**Said, until `0.4.0rc9`:** p. 304 for the filtration as well as for `EA_n(k)`
and the stable extension.

**True:** the filtration is on p. 303. Page 304 begins with the decomposition
of `GA_n(k)` and then defines the elementary automorphisms, and `MA_n(k)`
itself is p. 302.

**Found** by an audit reading the scan. The three are separate rows now, since
one row for three pages is how they were confused. It is the second time a
citation in that table had to be corrected against the source.

## Gao's licence was said to be undeterminable, and then to ask too little

Two errors about one map, one after the other.

**Said, first:** that the licence of arXiv:2608.00222v1 could not be
established.

**True:** the arXiv listing states CC BY 4.0. The sentence was written from a
habit formed on the nineteen-dimensional map, whose licence genuinely cannot be
established, and not from looking at the listing.

**Said, then:** that CC BY 4.0 asks for attribution and nothing more.

**True:** it asks for three things — attribution, a link to the licence, and an
indication of whether changes were made.

**Found:** both by an external audit, the first against the listing and the
second against the licence deed. All three are now given for every third-party
map, in `docs/provenance.md` and in the docstrings, and `docs/references.md`
states the terms without the history.

## The status line of `contracts.md` stood at `0.4.0` through a release

**Said, until milestone 0.6 opened:** "Status as of `0.4.0`".

**True:** the page had carried the UNT and DOM obligations of 0.5 through the
`0.5.0` release. The `[0.5]` markers were removed when the milestone closed and
the status line above them was not moved with them.

**Found** by reading while opening 0.6. Nothing checks the two against each
other and this correction did not add such a check.

## The last stage was said to double the dimension

**Said, in `references.md` and in the 0.5 section of `roadmap.md`:** that the
last of BCW's three stages roughly doubles the count.

**True:** the stage that doubles is the second, p. 306, where
`G(T) o E(T)^[n] o H(T)` is a map in `2n` variables. The third, p. 307, costs
one variable. Together `2n + 1`, and Long's 39 and 79 are that arithmetic
exactly.

**Found** while cutting milestone 0.6 into work packages, where which stage
costs what decides the packages. The total was right, so no comparison that had
been drawn was wrong. The entry under "Known limits" in the `0.5.0` section of
`CHANGELOG.md` carries the old wording and is left standing, because that
section records what was true at a release.

## Nothing was copied from that file, said the paragraph above the copy

**Said, until milestone 0.6:** that nothing from `anc/check_quartic_40.py` of
arXiv:2608.12543v1 is copied into this repository and that the figures were
recomputed from the manuscript. The next paragraph said that the map, the
restriction, the collision and `rho` are transcribed from it into
`scripts/reconstruct_prellberg40.py`.

**True:** the second. The transcription was made when that script was written
and the sentence above it was not withdrawn.

**Found** by reading while preparing work package 4. Two statements about one
fact will disagree eventually, and these did.

## Thompson's map was said to be unavailable after it had arrived

**Said:** that this project had not yet held Thompson's map, so the
intertwining identity in Prellberg's ancillary file could not be checked here.

**True** when it was written, and false from work package 4 of 0.6, which put
the map into `kellermap.examples`. The identity is still not recomputed, and
now for a reason rather than for want of the data.

**Found** by reading while preparing work package 7, five packages later.

## Fourteen years, where the gap is forty-four

**Said, in `contracts.md`:** that the compression is "fourteen years later than
the last thing in" `kellermap.bcw`.

**True:** that subpackage holds one paper, Bass, Connell and Wright of 1982,
and the compression is of 2026. Forty-four years.

**Found** by the maintainer asking where the number came from. It came from
nowhere: it was written for the rhythm of a sentence and never subtracted. The
page now gives the two years instead of the difference, since a derived number
can be derived wrongly twice and two dates can be checked against the
bibliography.

## Two days after the announcement, on the day of the announcement

**Said, as a section heading and in four other places:** that eleven variables
at degree three were reached two days after Alpöge's announcement.

**True:** the same day. The entry at the top of `references.md` dates the
announcement 20 July 2026 and the gist is dated 20 July 2026. Neither date
moved; the subtraction was never done.

**Found** immediately after the entry above, by checking the other date
arithmetic on the same page. Both errors have the same shape: a figure that
decorated a sentence rather than carrying it, and was therefore never checked.
`AGENTS.md` is about numbers leaving the repository and does not exempt the
ones that feel like prose.

## Three claims in the header of `kellermap.examples`

**Said:** that everything in the module except `alpoege` was written for this
project's own tests; that the tree holds 119 distinct `PolynomialMap`
constructions, 25 of them repeated, sorted into thirteen Keller maps and six
that are not; and that the coefficient domains are "mostly `ZZ`, and `ZZ[T]`
where a parameter appears".

**True:** the module has four kinds of provenance and two published
counterexamples and two published reductions among them; the count was measured
in work package 8 of 0.5 against a smaller module and stood in the present
tense; and six of the twenty maps are over `QQ`.

**Found** by the maintainer reading the header. None of the three is reachable
by a test, and the module had grown four times since the header was written.
The figures were removed rather than re-measured, and work package 9 of 0.6
reads every docstring in the tree for the same reason.

## Nineteen and thirty-eight were said to be below everything published

**Said, in work package 8 of milestone 0.6:** that at the cubic homogeneous
stage this project reaches 19 where the published figures are 24 and 20, that
at the quartic gradient form it reaches 38 where they are 40 and 48, and that
"the literature was searched again before this section was written and nothing
smaller was found at either stage". The section also claimed the composition
itself as the contribution, on the ground that nobody had put those five pieces
in a row.

**True:** both numbers were already published. A commit of 30 July 2026 in
`royvanrijn/jacobian-research` derives a twelve-variable degree-three map from
Macfarlane's `F13` and states three upper bounds together — 12 at degree three,
19 cubic homogeneous, 38 for the quartic gradient form — by a different route,
a month before this project reached them.

**Found** by the maintainer, a week after the section was written.

**How the search missed it.** The queries asked for the numbers and for the
names of the constructions, and the record is a Markdown file in a GitHub
repository that those queries do not reach. That is the second time: the
eleven-variable map was in a gist and was missed the same way, and the entry
above says a check made for a number one has just reached will not find a
smaller one. This adds a second lesson to that one. A search engine is not a
literature search when the literature is in repositories, and this project has
now been corrected twice by a person who looked where the searching did not.

**Where the corrected statement lives:** `docs/references.md`, under "Against
the published figures". What it says now is that two routes reached 19 and 38
independently, which is evidence about the numbers and not about either route,
and that nothing here is first.

## Macfarlane's map was in the source archive after all

**Said, in `docs/provenance.md` and in the comment beside the exclusion list of
`pyproject.toml`:** that neither of the two maps whose licence could not be
established is in the distribution, and that Macfarlane's values "stay in
`tests/data.py`".

**True:** they were also transcribed into
`scripts/reconstruct_macfarlane13.py`, and the archive ships `/scripts`. So the
values were distributed, which is what `AGENTS.md` forbids and what the
exclusion of `tests/data.py` was put in place to prevent.

**Found** by reading the reconstruction scripts in work package 9 of milestone
0.6, while measuring something else.

**Corrected** by the pattern that already existed for the other map:
`reconstruct_alpoege19.py` reads the nineteen-dimensional map from
`tests/data.py` rather than holding it, since work package 8 of 0.5, and the
thirteen-variable one is read the same way now. The archive was rebuilt and
checked: the script it ships holds no components.

The shape is one this repository has met before, and the docstring of that very
script names it — a correction made in two places out of three. The rule about
not distributing unlicensed data was applied to one map, written into the
packaging comment, written into the provenance page, and not applied to the
second map that needed it.

## Seven findings of the audit of `0.6.0rc1`

An external audit ran the release chain, the mutation probe, sixty BCW
pipelines, forty lifts and eighty compressions, and found nothing wrong with
the BCW formulas. It found seven other things, and they fall into two groups.

**Three were faults in the code.**

`SymmetricLiftStep.transport` treated its two points asymmetrically, and
`Collision` compares its points as a *set* under COL-6. So two equal
collisions, with equal hashes, transported to two unequal ones — and both
results verified, which is the worst shape such a fault can have. The step
orients the pair itself now. Reproduced on the thirty-eight-variable pipeline
and not only on a small example.

`collision_hull` and `CompressionStep` did field arithmetic over any domain.
The elimination divides by a pivot and the polarization by `d!`. Over `ZZ` that
produced Python floats and judged independent vectors dependent; over `ZZ[T]`
it raised whatever the domain raised; a basis value outside the domain escaped
as `CoercionFailed` where CHC-2 promises `ValueError`. Both now require a field
of characteristic zero, which is the setting Theorem 3 of arXiv:2608.12543v1
works in. CHC-8 also cited DOM-1 for characteristic zero, which DOM-1 does not
say.

`SymmetricLiftStep.build` failed over an algebraic number field. Adjoining `i`
to `QQ<sqrt(2)>` gives `QQ<sqrt(2) + I>`, whose elements are algebraic numbers
over another minimal polynomial, and converting a coefficient with `convert`
tries to unify the two representations. Going through the expression they agree
on works. Nothing else in the suite had a source over such a field.

**Two were faults in what a value means.**

`CompressionStep` stored its basis entries as they arrived, so over a fraction
field `(T^2 - 1)/(T - 1)` and `T + 1` gave two steps that verify alike,
describe one restriction and compare unequal. STEP-5 asks for comparison by
mathematical content. The entries go through the coefficient domain now.

The source archive shipped a test suite that failed. `tests/data.py` is
excluded from the archive on purpose, and one test imported it unconditionally
where its neighbours use `pytest.importorskip`. `make release` did not see it,
because `build-test` installs the wheel and then runs the tests of the *working
tree*. A new gate, `make sdist-test`, unpacks the archive, installs it and runs
the suite the archive ships. The fault predates this milestone.

**Two were claims stated too widely.**

`README.md` and `CHANGELOG.md` called milestone 0.6 "the rest of the Reduction
Theorem". Theorem 2.1(b) asks in addition for a normal form linear in each
original variable, which Proposition (3.1) delivers in a second half this
library does not implement. The pages say "the second and third stages" now and
name the refinement they leave out.

`docs/provenance.md` ended by saying nothing else in the repository is somebody
else's, and did not list `examples.spacerat11`. Its own docstring carries the
attribution, the licence link and the statement of changes, so this was an
inventory gap and not a licence fault. Three documents also counted six step
types where there are seven, and several sentences of the form "every other
step" had been made false by the two step types added after them.

That last cleanup was reported as finished and was not. The audit of
`0.6.0rc2` found three more places: `kellermap.linear`, which I had *rewritten*
in the same pass and given the wrong count again; `kellermap.bcw.unipotent` and
`kellermap.bcw.homogenization`, whose claims about "every other step" I had
narrowed to "in this package" without checking that the package had gained two
more step types. A count corrected by hand in six places out of nine is the
same defect as a rule applied in two places out of three.

**What the audit says about the controls.** The mutation probe caught 34 of 34
and the coverage is 100 per cent, and neither contradicts the findings: the
domains, the interaction between `transport` and equality, and the installed
archive all lie outside what those controls examine. Two of the three code
faults are about a *value* rather than a *branch*, and a branch-based control
cannot see them.

## Five findings of the audit of `0.6.0rc2`

**`make release` deleted the wheel it had just checked.** `sdist-test` began
with `rm -rf dist` and rebuilt only the archive, so after a green release the
only artefact left was the archive and `dist-check` had seen nothing else. The
archive is built into its own directory now, and `make dist-complete` requires
exactly one wheel and one archive before `dist-check` runs.

**`SYM-8` refused a collision that holds.** The residual of `rho`'s defining
equation was compared with `expand`, which does not decide equality for
rational functions: over `QQ(a, b)` a residual that is zero did not expand to
zero. `canonical.agree` decides it now, and so do the two comparisons beside
it -- the determinant of the matrix and of the source, where `1.0` over `RR`
is not `1` to `!=`.

**The orientation by `str` was not total.** `Symbol("a", positive=True)` and
`Symbol("a", negative=True)` print alike, so both sort keys were equal and a
stable sort kept the order the tuple carried: the fault of `0.6.0rc1` returned
for exactly those points, hidden by the `rho` fault above. The key is `srepr`
now, which writes the assumptions out.

**The symmetric lift had no domain boundary.** The compression got one in
`0.6.0rc2` and the lift did not, so a source over `GF(5)` reached `unify` and
ended in SymPy's `UnificationFailed`. SYM-4 now asks for the same field of
characteristic zero, which is the setting Theorem 3 states for both.

**CHC-2 and the code disagreed about an error type.** The page called it a
constructor invariant raising `ValueError` and the new field check raised
`VerificationError`. The constructor raises `ValueError` like every other
invariant of that type; `collision_hull`, which is a function that verifies its
arguments, raises `VerificationError` citing CHC-8.

Two of the five were introduced by the fixes for the previous audit, which is
worth recording as its own observation: a repair made under time pressure is
where the next fault goes in, and the second audit found more faults in the
first audit's repairs than in the code they repaired.

## Four findings of the audit of `0.6.0rc3`

**The orientation by `srepr` was not a function of equality.** The fix for the
previous audit replaced `str`, which is not injective, with `srepr`, which is
injective on *representations*: `Symbol("a", finite=True, positive=True)` and
`Symbol("a", positive=True, finite=True)` are one symbol written two ways, and
a third symbol sorts between them, so one set of points got two orientations
again. SymPy's cache hides this by reusing symbols, and every test in the suite
passed with `SYMPY_USE_CACHE=no` as well, so no control could have seen it. The
order is `Basic.compare` now, which returns zero exactly for equal expressions,
and two regression tests run in a fresh process with the cache off.

That is the third orientation and the third audit to find it, which is worth
saying plainly: `str` was wrong because printing loses information, `srepr` was
wrong because it keeps information that equality does not. Both looked
structural. The property needed was never "distinguishes different things" but
"agrees on equal things", and only the third attempt was chosen for it.

**The two halves of the lift's domain check were one branch.** Joined by `or`,
the test over `GF(5)` reached the characteristic alone, and a mutation dropping
the field half was caught by the wrong test. They are two branches with two
messages now, and two probes.

**The advice to use `over_field` was wrong for a finite field**, whose field of
fractions is itself. The compression had separated the two messages; the lift
had not.

**Three texts.** SYM-4 and the docstring of `lift._field` cited CHC-4 for the
compression's domain boundary, which is CHC-2 and CHC-8; CHC-4 is about the
source being a Keller map. `AGENTS.md` listed the release gates without
`dist-complete`, which the previous release candidate had added. And a sentence
in `CHANGELOG.md` had lost its verb.
