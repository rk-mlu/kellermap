# Changelog

Notable changes per release. The milestone plan and its reasoning live in
`docs/roadmap.md`, the binding obligations of the verification surface in
`docs/contracts.md`.

## 0.5.0rc3

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

### Fixed

- A grouped candidate could take the monomial equal to its divisor, leaving a
  constant cofactor, so `H` reached `EA^-1` and the chain that came back did
  not verify. Found by an external audit. The filtration level reported `0`
  there, which is why it stayed silent.
- `polynomials_over` treated an indeterminate of the coefficient domain as a
  later coordinate, so a pool value over `ZZ[T]` raised `GeneratorsError` where
  0.4 had answered. Found by an external audit.
- `over` of the wrong type raised `VerificationError` where the error table
  promises `TypeError`, and `SearchOutcome.domain` shared a mutable domain with
  the caller. Both found by an external audit.

### Fixed in rc2

- `reduce_to_degree3` overran its budget: the check sat on entry to a frame and
  not between siblings, so at `budget=1` the walk descended into all twenty-two
  children of the root and reported one. All twenty-two are still built there,
  because ordering builds every candidate before choosing; what was wrong was
  descending into them. `examined` now says which of the two it counts, and it is
  the maps the walk descended into.
- `context` of the wrong type raised `AttributeError` from inside, and only
  when the source had degree above three. It raises `TypeError` at either
  degree.
- `SearchOutcome.domain` and the other two handed the same object out on every
  read, so a caller could reach into a frozen outcome. The accessor copies.
- The Gao attribution carried a title assembled from the abstract rather than
  the paper's own, which is the part CC BY asks for first.
- `docs/references.md` claimed that Macfarlane's map lies in the space the
  untargeted enumerator describes. Two of the seven steps do; the rest are
  outside it. `peel` searches a wider space, and the page says so now.

All six found by an external audit of rc1.

### Fixed in rc3

- `scripts/reconstruct_macfarlane13.py` still claimed the map lies in the space
  the untargeted enumerator describes. rc2 corrected that in `references.md`
  and here and left the script, which is a correction made in two places out of
  three.
- `references.md` cited the positions of the two matching candidates. A second
  audit reached different positions for the same steps, because no convention
  for matching a step against a proposal is written down. The positions are
  gone and which steps match stays.
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

All five found by an external audit of rc2.

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
