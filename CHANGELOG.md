# Changelog

Notable changes per release. Dates are release dates; the milestone plan and
its reasoning live in `docs/roadmap.md`, the binding obligations of the
verification surface in `docs/contracts.md`.

## 0.4.0rc4

One release blocker, two functional findings and the documentation
contradictions from the audit of `0.4.0rc3`.

### Fixed

- `undo` rebuilt the reduced ring from the printed names of its generators, so
  `Symbol("x", positive=True)` came back as `Symbol("x")` and a component no
  longer converted, while `Symbol("x space")` was parsed into two generators.
  The ring is cloned with the generator objects.
- `factor` read the constant off the coefficient of the dropped coordinate to
  the first power only, so a step whose two slots are one fresh coordinate
  carrying zero -- where the coordinate appears only squared -- looked
  unreachable. Any monomial carrying the coordinate gives the same constant,
  and the one of highest degree is taken, chosen canonically so that the term
  order cannot decide it.
- The `m = 0` branch required undoing to shorten the target component. That is
  one case taken for all: undoing adds a product back, so the component usually
  grows, and the requirement only held where the forward step had grown it.
  Removed; it costs seven more moves at the root of the published map and
  changes neither run.
- `tests/data.py` holds SymPy constants and imports nothing from `kellermap`,
  so `scripts/reconstruct_alpoege19.py` reads the published map without the
  code it checks. The `PolynomialMap` is built in the test module.

### Added

- REV-10 states a bound the code had and the page did not: a step introducing
  no coordinate whose removed product cancelled its target's terms exactly
  leaves no monomial to read the constant from, so every constant fits and the
  peel would be guessing. Such a step is outside the space.

### Changed

- `contracts.md`, `roadmap.md`, `architecture.md` and the module text of
  `step.py` describe `m` as the number of distinct fresh variables, and the
  class sketch in `contracts.md` carries the coefficient. `step.py` names all
  three extensions beyond Proposition (3.1) and cites BCW-1 to BCW-12.
- The sentence saying the two derived rows carry different standing, with the
  label in the first column saying which. Both are labelled `derived` and both
  mean the same by it; what differs is when each became derivable, and what a
  derivation establishes is a separate question that the provenance section
  answers for each.
- `references.md` and the 0.5 plan record that the coefficient ring is part of
  the search space rather than a matter of presentation. The linear
  normalization divides by the determinant, so `bcw17` and `alpoege15` carry
  genuine fractions and live over `QQ`, while the nineteen-dimensional map was
  never normalized and is over `ZZ` throughout its chain. A step preserves the
  domain, so the source fixes what is reachable, and a benchmark figure has to
  say which space it belongs to.
- The benchmark table in `references.md` names the two derived maps by their
  functions in `kellermap.examples` rather than by the test modules they lived
  in before 0.4, marks the nineteen-dimensional row as present from a checkout
  and not from the source archive, and reports the step sequence of that map as
  reproduced rather than as the target of a milestone still running.

## 0.4.0rc3

One release blocker and the remaining findings from the audit of `0.4.0rc2`.

### Fixed

- The `m = 0` branch of `moves` computed in expressions rather than in the ring
  of the map, and was wrong in both directions. Over `ZZ` it offered a constant
  of `1/2`, which is not a constant there, and the peel then crashed on a map
  it could not build -- with the valid chain already in the space. Over
  `ZZ[S, T]` it measured the shortening with `sp.Add.make_args`, counting
  `S*a*x - T*a*x` as two summands where the ring sees one term with coefficient
  `S - T`, so a valid step looked like no shortening at all and the space was
  reported exhausted after one state. The branch now works on `PolyElement`
  throughout, converts every quotient into the coefficient domain and discards
  what does not lie there.
- The deduplicated constants were iterated straight out of a `set`, so
  `PYTHONHASHSEED` decided which move came first and, on a tight budget, which
  chain was found. They are sorted canonically.
- BCW-8 gave the transported image as `c_index - c_u * c_w` after introducing
  the coefficient, in the contract and in the docstring. Both now carry the
  weight.
- Documentation from before `0.4.0rc2`: `architecture.md` said no direction had
  found the chain and described `m` as the number of `Fresh` slots;
  `references.md` said the sequence was missing; `peeling.py` and
  `search_alpoege19.py` still spoke of the withdrawn diagonal, and the latter
  claimed a first round below 68425 maps was wasted, where eighteen now
  suffice. The README called three routes "the same seventeen steps", and the
  search finds a different valid seventeen-step chain.

## 0.4.0rc2

Three release blockers and four further findings from the audit of `0.4.0rc1`.

### Fixed

- `BCWStep.transport` scaled the removed product by the coefficient in `G` but
  not in the image, so a transported collision image was wrong whenever a
  carried coordinate had a non-zero image. Every collision image in the suite
  had zeros there, and a product with a zero does not remember a factor.
- `scripts/search_alpoege19.py` built its source over `QQ` while the published
  map is over `ZZ`, so the search could not reach it however long it ran. Over
  `ZZ` the peel reaches it in eighteen examined maps. The claim that this
  repository had not found the chain is withdrawn.
- The source archive no longer carries `tests/data.py`. Distributing it
  contradicted this project's own rule while the documentation said otherwise.
- `peel` carries the coefficient domain and the monomial order of the target
  into every intermediate map instead of re-inferring them, and admits a
  parameter of that domain as a coefficient, which BCW-11 always allowed.
- BCW-12 compares its two factors canonically, so two spellings of one
  polynomial are one polynomial.
- `moves` offers one candidate per distinct constant rather than one per shared
  monomial, and `peel` walks a state once. Thirty-six candidates at the root of
  the published map became sixteen.

### Added

- SEA-14 names the boundary of the forward search: no coefficient other than
  one, and no step whose two slots are one fresh coordinate. Reporting no
  result for either is SEA-6 and not a deferral under SEA-7. Peeling has
  neither restriction.
- `mypy --strict scripts` is a gate.

## 0.4.0rc1

The linear part completed, two searches for a step sequence, and the certified
factorization of the published nineteen-dimensional Keller map of degree three.

That factorization is the result of the milestone, and what it is worth is
stated precisely in `docs/references.md`. A chain was reconstructed by an
external audit of this project and verified here twice and independently, once
in plain SymPy and once as a chain of `BCWStep`. The backward search then found
a second one, of seventeen steps like the first, in eighteen examined maps.

### Added

- `TranslationStep` — the first factor of Chapter II, Proposition (1.1),
  which completes the linear normalization for maps outside `MA^0`.
  Obligations TRA-1 to TRA-8.
- `search(source, target, pool)` — a forward search for a step sequence,
  under SEA-1 to SEA-13, with `enumerate_candidates`, `anchors` and
  `Candidate`.
- `peel(source, target)` — a backward search, taking a chain off the target.
  It needs neither a value pool nor supplied names, and recovers the
  fifteen-dimensional reduction in eight maps where the forward search needs
  sixty-two and a value the published map no longer carries. Obligations REV-1
  to REV-9.
- `BCWStep` takes a `coefficient` (BCW-11) and admits two `Fresh` slots naming
  one variable (BCW-12). Both are extensions beyond Proposition (3.1), marked
  as such, and both are needed by the published chain.
- `PolynomialMap.reordered()` — the generator order of a chain is the order
  its steps introduced them, and a target may name them differently.
- `PolynomialMap.identity()` — the identity was written out forty-one times,
  twenty-one of them repeating their own variable list.
- `kellermap.examples` — the Keller maps this repository writes out more than
  once, chosen by two counted criteria.
- `tests/test_alpoege19.py` and `scripts/reconstruct_alpoege19.py` — the
  chain as a verified `Reduction` and as an independent rendering.
- `tests/test_admissible_shapes.py` — every admissible shape of a step
  through every operation. Two faults of this milestone were found by an audit
  and by an assembly rather than by a test, and both were of that kind.
- `tests/test_ascii.py` — a gate for the agreement that Python files are pure
  ASCII, which had one breach in the tree and no gate to attribute it to.

### Changed

- SEA-5 compares the endpoint by plain equality again. It allowed a diagonal
  `D` between work packages 7 and 10, first of signs and then of arbitrary
  non-zero constants; BCW-11 made it unnecessary, because a scalar the step
  can carry needs nowhere else to live.
- `m` counts distinct fresh variables, which matters only once two slots may
  name one.
- `Collision.transport` appends one coordinate per fresh generator rather than
  per `Fresh` slot.
- The fixed maps moved to where their provenance puts them:
  `kellermap.examples` for the ones this project may distribute, `tests/data.py`
  for the nineteen-dimensional map, whose licence could not be established.

### Withdrawn

- The reading that the numbering `w1` to `w16` of the published map is the
  order the coordinates were introduced in. It is a topological order of the
  final carrier values and not a chronology; the chain settled it, and the
  paragraph that argued otherwise stays in `docs/roadmap.md`, withdrawn rather
  than deleted.

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
