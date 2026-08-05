# Changelog

Notable changes per release. Dates are release dates; the milestone plan and
its reasoning live in `docs/roadmap.md`, the binding obligations of the
verification surface in `docs/contracts.md`.

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
