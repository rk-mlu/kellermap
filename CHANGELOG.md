# Changelog

Notable changes per release. The milestone plan and its reasoning live in
`docs/roadmap.md`, the binding obligations of the verification surface in
`docs/contracts.md`.

## 0.6.0

The second and third stages of the Reduction Theorem, and the two constructions
that carry the result to the form the literature compares. Everything before
this milestone stopped at degree three, which is BCW's first stage, while the
published figures are cubic homogeneous, which is the third.

Two stages and not the whole theorem. Theorem 2.1(b) asks for a normal form
that is also linear in each original variable and quadratic only in `T`; this
milestone does not produce that refinement, and `(x + y^3, y)` homogenizes to a
verified five-dimensional target that still carries a `y^3`. The reduction the
usual corollary needs -- cubic homogeneous with nilpotent Jacobian -- is
unaffected, and `docs/references.md` says which is which.

The pipeline, from the smallest degree-three map this project holds, with every
step verified and the collision carried to the far end:
`examples.spacerat11` at 11 variables, 22 after the unipotent reduction, 23
cubic homogeneous, 19 after collision-hull compression, and 38 for the gradient
form of a quartic over `Q(i)`. `scripts/measure_pipeline.py` recomputes that
and the same for the two larger maps.

What that is worth and what it is not is in `docs/references.md`. Nineteen and
thirty-eight are the smallest figures published at either stage and they were
published elsewhere first, on 30 July 2026, by a different route. No priority
is claimed and no minimality. The forms this project produces are denser than
the published ones: 386 monomials against 350 at the quartic stage.

Three pages were split out of `docs/references.md`, which had grown to four
subjects at once. `docs/provenance.md` holds what an audit reads and
`docs/errata.md` what this project reported wrongly and corrected — eighteen
entries, five of them findings of the audits of this milestone's release
candidates.

### Added

- `kellermap.bcw.UnipotentStep` — Section 4's second step, which doubles the
  dimension and makes the Jacobian of the displacement nilpotent. Obligations
  UNI-1 to UNI-12.
- `kellermap.bcw.HomogenizationStep` — the third step, which adds one variable
  and makes the displacement cubic homogeneous. The first step type that is not
  a composition, and whose transport runs forward only. Obligations HOM-1 to
  HOM-10.
- `kellermap.CompressionStep` and `collision_hull` — Theorem 3 of
  arXiv:2608.12543v1. The one step that lowers the dimension, restricting to
  the subspace a collision generates. Obligations CHC-1 to CHC-10.
- `kellermap.SymmetricLiftStep` — part 3 of the same theorem: the gradient of a
  quartic over `k(i)`, which is the object Zhao's Vanishing Conjecture is
  about. The first step that changes the coefficient domain. Obligations SYM-1
  to SYM-12.
- `examples.thompson24_homogeneous` and `examples.spacerat11`, with their
  collisions — two published maps this project did not write, transcribed from
  the licensed presentations. `docs/provenance.md` records the terms.
- `scripts/reconstruct_spacerat11.py` and `scripts/measure_pipeline.py`, joined
  to `make reconstruct` and `make measure`.
- `docs/provenance.md` and `docs/errata.md`.
- `CITATION.cff`, shipped in the source archive, and `docs/deposit.md`, which
  holds the description text and the procedure of the Zenodo deposit rather
  than leaving the wording of a permanent record to a browser session. The
  version stands in four places now and `tests/test_documentation.py` holds
  the four together.
- The DOI of this version, `10.5281/zenodo.22299353`, in `CITATION.cff` and in
  `README.md`. Zenodo reserves a DOI on a draft, so it was written in before
  the archive was built and the archive carries the DOI of the record it goes
  into. `docs/deposit.md` had the two steps the other way round and now says
  to reserve first; a test holds the two places together, with a control for a
  Markdown link whose label and target disagree.

### Changed

- `examples.thompson24` is `examples.thompson24_homogeneous`. A map that is not
  at degree three carries its stage in its name, since `alpoege19` is nineteen
  variables at degree three and the compression reaches a cubic homogeneous map
  in nineteen by another route.
- `kellermap.bcw.grading` holds what the second and third steps share, which is
  reading a displacement by degree and asking whether a Jacobian is nilpotent
  through one determinant.
- `docs/references.md` states the position and no longer tells the story of how
  it was corrected; `docs/errata.md` does that.
- `docs/provenance.md` gains "How this repository was written", which is the
  one place stating which generative models were used, in which roles, what
  the arrangement found, and who answers for the result. `CITATION.cff` and
  the Zenodo description point at it rather than repeating it.
- `AGENTS.md` gains the rule that a new way of distributing the repository is
  checked against the licence rule before it is used. It has now failed twice
  at a channel nobody checked, and `docs/deposit.md` records the check for the
  third.
- The `Documentation` list in `README.md` still described `references.md` as
  the page holding the provenance of the fixed data, which stopped being true
  when this milestone split it. It names all seven pages now.

### Fixed

- `scripts/reconstruct_macfarlane13.py` carried a transcription of Macfarlane's
  map, and the source archive ships `scripts/`. His repository carries no
  licence, so the archive was distributing mathematics whose terms could not be
  established. The script reads it from `tests/data.py` now, which is the
  pattern `reconstruct_alpoege19.py` has had since 0.5.
- A sentence in `docs/references.md` wrapped so that a number began a line, and
  Markdown read it as an ordered list. A test now covers the class.
- The source archive shipped a suite that failed: one test imported
  `tests/data.py`, which the archive excludes on purpose. It skips now, and
  `make sdist-test` unpacks the archive, installs it and runs the suite the
  archive ships. `build-test` never saw this, because it runs the tests of the
  working tree. The fault had stood since 0.5.

### Found in review

None of these reached a release. Every one was introduced inside this
milestone and found before it closed, by six external audits of the release
candidates and by the maintainer. They are listed because a defect that was
caught is evidence about the review and not an embarrassment, and because the
first of them is five defects that are one defect.

- **The orientation of the two lifted points went through five orderings.** A
  collision is a set, so `SymmetricLiftStep.transport` has to decide which of
  the two points is which. The first version took the order the tuple happened
  to carry, and two equal collisions transported to two unequal results that
  both verified. `str`, `srepr` and `Basic.compare` each replaced the one
  before and each failed on a pair the next audit produced: two symbols of one
  name with different assumptions, one symbol written two ways, two `Function`
  classes of one name. What they had in common is not the choice of key. Each
  was used instead of an equality test rather than after one, which asks a
  single key to agree on everything equal and separate everything unequal. The
  released version asks `==` first, then `Basic.compare`, then metadata of the
  class, and refuses under SYM-8 where all of that ties. `docs/errata.md`
  carries the five in full, and the fifth is the only one that did not replace
  the version before it.
- `collision_hull` and `CompressionStep` did field arithmetic over any
  coefficient domain, and the symmetric lift had no domain boundary at all.
  All three require a field of characteristic zero now, which is what Theorem 3
  assumes. A value the domain cannot represent raises the `ValueError` CHC-2
  promises rather than the domain's own error, and a source over `GF(5)` no
  longer reaches SymPy's `UnificationFailed`.
- `CompressionStep` stored basis entries as they arrived, so two spellings of
  one element gave two steps that verify alike and compare unequal. They go
  through the domain now.
- `SymmetricLiftStep.build` failed over an algebraic number field, because
  adjoining `i` there gives a field whose elements `convert` cannot unify with
  the source's. Coefficients go through SymPy now.
- SYM-8's residual was compared with `expand`, which does not decide equality
  for a rational function, so a collision that holds was refused.
  `canonical.agree` decides it now, and so do the two comparisons beside it.
- The two halves of SYM-4's domain check were one branch, so a finite field
  reached the characteristic alone and the field half had no control of its
  own. Two branches, two messages, two probes.
- `make release` deleted the wheel it had just checked, because `sdist-test`
  began by emptying `dist/`. The archive is built into its own directory now,
  and `make dist-complete` requires exactly one wheel and one archive before
  `dist-check` runs.
- A test asserted `hash(one) == hash(b and other)`, which is `hash(other)`
  because `b` is truthy. It checked the intended claim by accident.
- The contract page and the code disagreed four times about which obligation
  covers what. CHC-8 cited DOM-1 for characteristic zero, which DOM-1 does not
  say; CHC-2's error type was one thing on the page and another in the
  constructor; SYM-4 and a docstring cited CHC-4 for a boundary that is CHC-2
  and CHC-8; and SYM-8 claimed an order total on expressions, named an
  implementation two versions stale, and did not list its own refusal among
  what supplied data can fail.
- Documentation claimed six step types where there are seven, or claimed of
  "every other step" something two of them no longer satisfy, in three rounds,
  and twice an entry of this file reported that cleanup as finished when it was
  not. `README.md` and this file called the milestone "the rest of the
  Reduction Theorem", where Theorem 2.1(b) asks in addition for a form linear
  in each original variable. `docs/provenance.md` did not list
  `examples.spacerat11` among the third-party maps, and the advice to use
  `over_field()` was wrong for a finite field, whose field of fractions is
  itself.

### Known limits

- SYM-7 is stated and not checked. The determinant of the gradient form follows
  from the identity and the source; computing it on the forty-variable lift did
  not finish in eight hours, where the same determinant at a random point takes
  22 seconds. `docs/roadmap.md` carries the measurement and milestone 0.7 the
  bottleneck.
- The chains `peel` finds are mostly not chains the untargeted search offers:
  none of six for `spacerat11`, two of seven for `macfarlane13`. Why is a
  measurement for 0.7.
- Nothing here computes `Delta^m(P^m)`, so the last link of the chain this
  project follows is not in the repository. It is milestone 0.8.
- `SymmetricLiftStep.transport` can refuse a collision that holds. It orients
  the pair itself, because a collision is a set, and two points that are
  unequal, compare equal and carry the same class metadata -- module, qualified
  name, declared assumptions and construction keywords -- cannot be ordered by
  anything it reads. No total order on SymPy expressions is claimed and the
  refusal is what stands in place of one. It is deterministic, and every
  collision this milestone produces is far from it.

## 0.5.0

Searching without a target. The question changes from "does this chain reach
that map" to "reduce this map to degree three", and the answer is a chain the
library found rather than one it was given.

`reduce_to_degree3` takes a source and nothing else. It reaches degree three
from Alpoege's normalized map in seven steps into dimension 13 and from Gao's
in twenty-nine into thirty-nine, and both chains verify. The chains computed by
hand take eight steps into fifteen and eight into seventeen.

What that is worth and what it is not is in `docs/references.md`. Thirteen
variables at degree three were reached a month earlier by A. Macfarlane, by a
route this library has no construction for, and no priority is claimed. A
seven-step BCW chain reaches his map from the same source, found by `peel`;
that chain is not one the untargeted enumerator can currently produce, and an
earlier draft of this entry said otherwise.
No minimality is claimed either, and the measurement behind that refusal is in
`docs/roadmap.md`.

The repository is English throughout since this milestone, tests included, and
a gate holds it there.

### Added

- `kellermap.untargeted` — an enumerator and a search that need no target.
  `untargeted_candidates` offers the steps Proposition (3.1) allows at a map,
  `ordered_steps` sorts them by what they remove, `remaining_weight` is the
  measure that bounds the walk, and `reduce_to_degree3` walks it. Obligations
  UNT-1 to UNT-11.
- `over=` on `search` and `peel`, so the coefficient ring is something a caller
  states rather than something inferred. `SearchOutcome` and `PeelOutcome`
  carry the ring they searched. Obligations DOM-1 to DOM-4.
- `examples.gao_quartic` and `gao_quartic_collision` — the second source map
  this project has, from arXiv:2608.00222 Section 3.5, licensed CC BY 4.0. Its
  collision is the only one here whose points are not rational.
- `examples.alpoege13` and `alpoege13_collision` — the thirteen-dimensional
  cubic reduction the search finds, with Alpoege's three points carried
  through.
- `scripts/reconstruct_alpoege13.py` and `scripts/reconstruct_macfarlane13.py`
  — two more independent renderings in plain SymPy, and
  `scripts/untargeted_space.py` and `scripts/search_cost.py`, which recompute
  the figures the UNT obligations rest on.
- `tests/test_language.py` — a gate that keeps the repository in English, with
  `scripts/foreign_words.py` as its audit instrument.

### Changed

- `kellermap.canonical` denests square roots, so two spellings of one algebraic
  number are one point. Without it a `Collision` could be built whose points
  coincide, which COL-4 forbids, and a correct image written as a nested
  radical was rejected. The module states what it does not claim: a radical of
  higher index.
- `undo` in `peeling` computes in the polynomial ring rather than in SymPy
  expressions. Measured by alternating runs: about a fifth off the peel.
- `Candidate` carries a coefficient and reports the filtration level a step
  reaches, in both directions.

### Found in review

None of these reached a release. Every one was introduced inside this
milestone and found before it closed, by five external audits of the
release candidates and by the maintainer. They are listed because a defect
that was caught is evidence about the review and not an embarrassment, and
because several of them were introduced by the fix for the one before.

- A grouped candidate could take the monomial equal to its divisor, leaving a
  constant cofactor, so `H` reached `EA^-1` and the chain that came back did
  not verify. Found by an external audit. The filtration level reported `0`
  there, which is why it stayed silent.
- `polynomials_over` treated an indeterminate of the coefficient domain as a
  later coordinate, so a pool value over `ZZ[T]` raised `GeneratorsError`
  where 0.4 had answered. Found by an external audit.
- `over` of the wrong type raised `VerificationError` where the error table
  promises `TypeError`, and `SearchOutcome.domain` shared a mutable domain
  with the caller. Both found by an external audit.
- `reduce_to_degree3` overran its budget: the check sat on entry to a frame
  and not between siblings, so at `budget=1` the walk descended into all
  twenty-two children of the root and reported one. All twenty-two are still
  built there, because ordering builds every candidate before choosing; what
  was wrong was descending into them. `examined` now says which of the two it
  counts, and it is the maps the walk descended into.
- `context` of the wrong type raised `AttributeError` from inside, and only
  when the source had degree above three. It raises `TypeError` at either
  degree.
- `SearchOutcome.domain` and the other two handed the same object out on
  every read, so a caller could reach into a frozen outcome. The accessor
  copies.
- The Gao attribution carried a title assembled from the abstract rather than
  the paper's own, which is the part CC BY asks for first.
- `docs/references.md` claimed that Macfarlane's map lies in the space the
  untargeted enumerator describes. Two of the seven steps do; the rest are
  outside it. `peel` searches a wider space, and the page says so now.
- `scripts/reconstruct_macfarlane13.py` still claimed the map lies in the
  space the untargeted enumerator describes. rc2 corrected that in
  `references.md` and here and left the script, which is a correction made in
  two places out of three.
- `references.md` cited the positions of the two matching candidates. A
  second audit reached different positions for the same steps, because no
  convention for matching a step against a proposal is written down. The
  positions are gone and which steps match stays.
- Four documentation leftovers: the docstring of `alpoege13` said the
  literature check was outstanding, a test comment said "no ranking",
  `architecture.md` opened its search section with "two directions", and the
  rc2 entry above said twenty-two maps were built where the defect was
  descending into them.
- The outcomes stored the copied ring in `_domain`, which put that name into
  the generated signature, the repr and `__match_args__`. The parameter is
  `domain` again, by `InitVar`, and the repr reports the ring by hand.
- The hash-seed test compared the step count and the dimension, which two
  different chains can share. It compares a fingerprint of the steps.
- The three outcome types ignored the coefficient ring in equality and
  hashing. Two results that agree on everything else and not on the ring are
  not the same result, which is the reason DOM-4 exists. Introduced in rc3 by
  the fix for the field name.
- `domain` looked optional: declaring it as an `InitVar` beside a property of
  the same name made the property object the parameter's default, so omitting
  it raised `AttributeError` from inside instead of `TypeError` at the call.
  The three constructors are written out by hand now.
- `references.md` explained the wrong candidate positions by a missing
  convention for matching. There is one, it gives 15 and 6, and the figures
  were simply wrong; the evasion is replaced by the correction.
- Two audit references named the wrong release candidate.
- `MACFARLANE_THIRD_POINT` in `tests/data.py` was cited by `references.md`
  and checked by nothing; the reconstruction script checked its own copy. A
  test compares the cited value against the chain the library computes.
- `dataclasses.replace` failed on all three outcome types: a hand-written
  constructor took `domain` while the field was `_domain`, so `fields()` and
  the signature disagreed. `domain` is a descriptor-typed field now, which is
  a field under that name and still copies the ring on read.
- The equality test required different hashes for different results, which
  asks more than Python promises. It requires inequality, and equal hashes
  for equal results.
- One audit reference named the wrong release candidate, and one line in
  `references.md` was not wrapped.

### Known limits

- `reduce_to_degree3` recurses once per step, so a chain longer than about 970
  steps raises `RecursionError` rather than reporting that it was cut off. The
  longest chain produced here is twenty-nine.
- No figure at BCW's third stage. The homogenization is not implemented, so
  nothing here compares with a cubic-homogeneous count.

## 0.4.0

Searching for a reduction rather than verifying one that is presented, and the
certified factorization of the published nineteen-dimensional Keller map of
degree three. `TranslationStep` completes the linear normalization, `search()`
walks from the source and `peel()` from the target, and the published chain is
a verified `Reduction` in the test suite, an independent rendering in plain
SymPy, and a search result.

What that factorization is worth is stated precisely in `docs/references.md`.
A chain was reconstructed by an external audit of this project and verified
here twice and independently. The backward search then found a second one, of
seventeen steps like the first, in eighteen examined maps. It is a chain and
not the chain, and no minimality is claimed for it.

The milestone went through fifteen release candidates and a series of external
audits. What each candidate changed is in the history of this file; the
candidates carry no public tag.

### Added

- `TranslationStep` — the first factor of Chapter II, Proposition (1.1), which
  completes the linear normalization for maps outside `MA^0`. Obligations TRA-1
  to TRA-8.
- `search(source, target, pool)` — a forward search for a step sequence, under
  SEA-1 to SEA-14, with `enumerate_candidates`, `anchors` and `Candidate`. It
  is told what a fresh coordinate may carry.
- `peel(source, target)` — a backward search, taking a chain off the target,
  under REV-1 to REV-12. It needs neither a value pool nor supplied names, and
  recovers the fifteen-dimensional reduction in eight examined maps where the
  forward search needs sixty-two and a value the published map no longer
  carries. `PeelOutcome`, `SearchOutcome` and `Undo` come with it.
- `BCWStep` takes a `coefficient` (BCW-11) and admits two `Fresh` slots naming
  one variable (BCW-12). Both are extensions beyond Proposition (3.1), marked
  as such, and the published chain needs both.
- `PolynomialMap.reordered()` — the generator order of a chain is the order its
  steps introduced them, and a target may name them differently.
- `PolynomialMap.identity()` — the identity was written out forty-one times,
  twenty-one of them repeating their own variable list.
- `kellermap.examples` — the Keller maps this repository writes out more than
  once, chosen by two counted criteria.
- `tests/test_alpoege19.py` and `scripts/reconstruct_alpoege19.py` — the chain
  as a verified `Reduction` and as an independent rendering.
- Gates for the agreements that had none: `tests/test_admissible_shapes.py` for
  every admissible shape of a step through every operation,
  `tests/test_ascii.py` for pure-ASCII Python files,
  `tests/test_documentation.py` for what the prose claims about the code,
  `tests/test_packaging.py` for what the source archive ships, and
  `tests/test_scripts.py` for the drivers.
- `scripts/mutation_probe.py` — it breaks one fragment of the source in a copy
  of the project, runs the suite, and reports whether anything noticed. Full
  statement coverage says a line ran; it does not say that removing the line
  would be caught, and those are different questions.

### Changed

- `Collision.transport` appends one coordinate per fresh generator rather than
  one per `Fresh` slot, which matters once two slots may name one variable.
- `m` counts distinct fresh variables, for the same reason. BCW-1 and BCW-2 are
  amended for the coefficient and for the shared name.
- The fixed maps moved to where their provenance puts them: `kellermap.examples`
  for the ones this project may distribute, `tests/data.py` for the
  nineteen-dimensional map, whose licence could not be established. The source
  archive does not carry that file.
- The source archive is defined by a positive list of what it ships rather than
  by a list of what it does not. A list of exclusions cannot be completed
  against names nobody has chosen yet, and the promise above it was that the
  archive does not depend on the state of the working directory.
- `docs/contracts.md` names a third gap beside the two it already named. Full
  statement coverage is not full obligation coverage; and full obligation
  coverage is not the same as every obligation being pinned by something.
- The release chain runs the coverage gate, the three reconstructions and the
  distribution metadata check automatically rather than by hand, on both ends
  of the supported Python range.

### Fixed

- `docs/references.md` attributed the filtration `MA_n^d(k)` to p. 304 of the
  paper. It is on p. 303; p. 304 opens with the decomposition of `GA_n(k)`.
  Read off the scan page by page, and the pages are separate rows now, since
  one row covering three pages is how they came to be confused.
- One Python file in the tree was not pure ASCII, against the project's own
  agreement, with no gate to attribute it to.

### Withdrawn

- The reading that the numbering `w1` to `w16` of the published map is the
  order the coordinates were introduced in. It is a topological order of the
  final carrier values and not a chronology; the chain settled it, and the
  paragraph that argued otherwise stays in `docs/roadmap.md`, withdrawn rather
  than deleted.

### Known limitations

- A reused factor must be carried by a coordinate of the source of that step,
  not by an earlier map in the chain.
- The forward search has a stated boundary, SEA-14: no coefficient other than
  one, and no step whose two slots are one fresh coordinate. Reporting no
  result for either is an exhausted space and not a deferral. Peeling has
  neither restriction.
- A `Collision` holds points over the coefficient domain of its map. The second
  family of counterexamples recorded in `docs/references.md`, arXiv:2608.00222
  §3.5, has a collision that is not rational, so reaching it needs a collision
  over a number field. It is named as a second source for 0.5.
- The coefficient ring is part of the search space and not a matter of
  presentation. A step preserves the domain, so the source fixes what is
  reachable, and a benchmark figure has to say which space it belongs to.
- No minimality and no priority is claimed for any dimension reached here.
  `docs/references.md` says what a comparison with the literature does and does
  not establish.
- A peel spends its time in SymPy expression work rather than in coefficient
  arithmetic, measured under `cProfile`. Working in the ring throughout, which
  `undo` still does not, is the lever, and it is 0.5 work.

## 0.3.0

Steps that reuse a carrier. A step no longer always introduces two new
generators, and a reduction that reuses them reaches a lower dimension:
`alpoege15`, this project's own reduction of Alpöge's map to dimension 15, is
derived and verified.

### Added

- `Fresh` and `Carried` — the two kinds of factor slot. `Fresh(P, u)`
  introduces a new generator whose component becomes `u + P`. `Carried(j)`
  reuses coordinate `j` of the source, which already has the form `X_j + P`.
- `BCWStep.m` — the number of generators the step introduces, which is 2, 1
  or 0.
- `BCW-10` — a reused slot must name a carrier. Its first two clauses are
  constructor invariants; the third is checked by `verify()` and gives the
  step its meaning, since the identity holds without it.
- `tests/test_alpoege15.py` and `scripts/reconstruct_alpoege15.py` — the
  fifteen-dimensional map, derived by the library and computed independently
  in plain SymPy.

### Changed

- `BCWStep` takes two factor slots instead of `P`, `Q` and a pair of
  variables. This is a breaking change to the constructor and to `build()`.
  Migration from 0.2:

  ```python
  # 0.2
  BCWStep.build(F, i, P, Q, (u, v), level)
  BCWStep(F, target, i, P, Q, (u, v), level)

  # 0.3
  BCWStep.build(F, i, Fresh(P, u), Fresh(Q, v), level)
  BCWStep(F, target, i, Fresh(P, u), Fresh(Q, v), level)
  ```

  Two `Fresh` slots are exactly the earlier step. `P`, `Q` and `variables`
  remain readable as properties.
- `BCW-2` allows `target.dimension == source.dimension + m`. This is the only
  binding obligation the milestone weakens rather than extends, and the reason
  0.3 is a minor release.
- `BCW-8` covers every `m`. A point gains one coordinate per `Fresh` slot. For
  `m ≥ 1` the image is unchanged apart from padding; at `m = 0` it moves to
  `c_index - c_u * c_w`.
- `BCW-9` states what `SUPPLIED` claims: the target was not produced by this
  library in this run, and nothing about who computed it.
- Documentation uses plainer language throughout. Metaphors for technical
  facts, rhetorical constructions and long sentences were removed, so that the
  text is easier for readers who do not have English as a first language.

### Known limitations

- The translation `(X − F(0))` is still not implemented, so a map must already
  fix the origin. Neither driving example needs it.
- A reused factor must be carried by a coordinate of the source of that step,
  not by an earlier map in the chain.
- Searching for a factorization rather than verifying one that is presented is
  the next milestone.

## 0.2.0

The verification framework. A reduction is now a chain of certified
identities rather than a computation one has to trust, and the
seventeen-dimensional cubic counterexample in the test suite is *derived* from
Alpöge's map instead of being asserted.

### Added

- `Collision` — distinct points sharing one image, verified by evaluation and
  carried across steps. It holds no map, since the same points are a collision
  of every map that identifies them.
- `VerificationError` — carries the identifier of the obligation that failed
  and, inside a chain, the index of the step.
- `kellermap.linear` — `GL_n(k)` as an ordered product of Gauss generators:
  `Transvection`, which is elementary in the sense of the paper, and
  `Transposition` and `Dilation`, which are not. `over_field()` widens a
  coefficient domain explicitly, since a dilation needs a unit.
- `kellermap.reduction` — the `Step` protocol, `LinearStep` for the linear
  normalization of BCW Chapter II, Proposition (1.1), and `Reduction`, which
  verifies every step and every join and nothing else.
- `Provenance` — whether a step's target was supplied or computed. For a
  supplied target the identity check compares an externally computed map
  against the formula and can fail; for a constructed one it compares the
  implementation against itself. The distinction is recorded rather than
  averaged away.
- `kellermap.bcw.BCWStep` — one certified application of Proposition (3.1),
  with `G` and `H` derived from `(index, P, Q, variables)` rather than stored
  beside them. Two things are wider than the paper states them: `P·Q` may be
  any subsum of the target component, and the target component may be any
  component.
- `ReductionContext` — checks that a `VariableFactory` keeps its promises
  across a chain, rechecking purity and composition on every call.
- `kellermap.canonical` — the single normal form the package compares in.
- `docs/contracts.md` — every obligation of the verification surface, stated
  normatively before the implementation, with a stable identifier that the
  exception cites when it fails.
- `scripts/reconstruct_bcw17.py` — the same reduction in plain SymPy, without
  this library, as an independent second implementation of formula (1).
- A published cubic Keller map in dimension 19 as a second regression example,
  recomputed rather than trusted.

### Changed

- `tests/test_bcw17.py` derives its map: a `Reduction` of eight steps from
  Alpöge's map, verified step by step, carrying the three-point collision from
  `k³` to `k¹⁷`. Only the last step is supplied, because the intermediate maps
  are published nowhere; a negative control shows the check there bites.
- The linear normalization is cited as Chapter II, Proposition (1.1), p. 303,
  not as §4. Section 4 carries the same formula but with the linear part
  already in `EA⁰`; the step this library performs is the other one.
- Full statement coverage is enforced (`fail_under = 100`), and `make release`
  gained the coverage and `twine check` gates.

### Fixed

Findings from two external audits of the release candidates, none of which
required new functionality.

- `Collision` compared coordinates with `expand`, which does not clear a
  denominator; over `k(T)` two spellings of one point were accepted as two
  points. Coordinates are now put into normal form on entry, which also keeps
  equality and hashing consistent.
- `BCWStep` checked its factors by symbol name, which refused a valid `T·x`
  over `k[T]`, accepted a fresh variable named `T`, accepted two symbols of one
  name, and accepted non-polynomials. `P` and `Q` now pass through the source's
  ring.
- `provenance` was a public, unchecked constructor argument, so a supplied step
  could claim to be constructed. It is no longer settable, and it is part of
  equality and hashing.
- `LinearStep.normalize()` accepted a map with `F(0) ≠ 0` and built a step that
  then failed its own verification. Proposition (1.1) puts a translation first;
  such a source is now refused with that reason.
- `BCWStep.build()` consumed its `variables` argument twice, so a generator was
  consumed by the first construction.

### Known limitations

- The translation `(X − F(0))` is not implemented, so a map must already fix
  the origin. It is elementary in the sense of the paper and needs no new
  non-elementary type.
- `BCWStep` fixes two fresh variables per step, so a reduction that shares
  carrier variables across steps cannot be expressed as a chain of them.
- Searching for a factorization rather than verifying a presented one is a
  later milestone; see `docs/roadmap.md`.

## 0.1.0

The algebraic foundations: polynomial maps over a sparse `PolyRing` with value
semantics, simultaneous composition, Jacobian matrices and determinants via the
unipotent carrier block, stable extension with an injectable variable factory,
and elementary automorphisms with the filtration of `EA_n(k)`.
