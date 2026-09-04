# Roadmap

The project follows an incremental development strategy. Every milestone should
leave the repository in a fully functional, typed, formatted, and tested state.

---

# Version 0.1 — complete

## Sparse polynomial core

Adopt `sympy.polys.rings.PolyRing` as the canonical internal representation.
General SymPy expressions remain the public input and output format.

### PolynomialMap

- expression-level constructor using `sring`
- direct `from_ring()` construction for internal algorithms
- private sparse `PolyElement` coordinates
- defensive copying at mutable boundaries
- simultaneous composition with `PolyElement.compose()`
- sparse partial derivatives
- determinant through `DomainMatrix`
- degree and order from monomial exponent tuples
- displacement and filtration degree (`MA^d`)
- stable extension without expression expansion
- collision-safe temporary variable names

### Backend validation

- preserve all existing `PolynomialMap` tests
- add tests for PolyRing construction and conversion
- add tests for symbolic coefficient domains such as `k[T]`
- test composition across compatible coefficient domains
- reject non-polynomial coordinate functions at construction
- test defensive copies of mutable `PolyElement` objects
- compare small Jacobians and determinants with expression-based results
- cross-check the Schur-complement path against `DomainMatrix` at full size

### Determinant strategy

Select the determinant algorithm from the structure of the Jacobian. Where a
subset of coordinates spans a unipotent block `I + L` -- which stable
extensions, elementary automorphisms and BCW-reduced maps always produce --
the determinant reduces to the Schur complement of that block.

The unipotence precondition is decided on the dependency graph, not by taking
powers, and it is checked rather than assumed: the block identity needs
`det(D) = 1`, and an empty head block would otherwise report determinant one
for any map at all.

`DomainMatrix` over the polynomial-ring domain remains the fallback and the
reference against which the optimized path is cross-checked.

### ElementaryAutomorphism

`ElementaryFactor` is a generator of `EA_n(k)` in the sense of BCW p. 304:
`X_j |-> X_j + P` with `P` free of `X_j`, no coefficient on `X_j`. The inverse
is `X_j |-> X_j - P`, read off the definition. `ElementaryAutomorphism` is an
element of the group, kept as the ordered product of its factors.

Every generator has determinant one, hence so does every element. Admitting a
scaling `a X_j + P` would put elements of other determinant into `EA_n(k)` and
break the argument that a reduction step preserves the Jacobian determinant;
scalings belong to the linear part that Proposition (1.1) separates, and if
they are ever needed they get their own type.

Both operate in an existing ring and avoid expression conversions inside
reduction loops: `apply_to()` touches the single coordinate that moves.

### VariableFactory

An injectable, collision-safe name generator for stable extensions, in
`kellermap.variables`. `PolynomialMap.extend()` takes one and falls back to
`DEFAULT_VARIABLE_FACTORY`.

A factory must be a pure function of ring and count. The monoid-homomorphism
invariant

    (F o G)^[m] = F^[m] o G^[m]

reaches `extend()` through three separate calls, and a factory that counted
upwards would name the sides differently and break the identity silently. The
invariant test passes a factory explicitly rather than relying on
equal-dimensional maps happening to agree.

`IndexedVariableFactory` reads the naming convention off the existing
generators, so `x1, ..., x17` extends by `x18, x19` instead of `X18, X19`.
`extend()` rechecks count, type, distinctness and collisions rather than
trusting the factory, because `PolyRing.clone()` accepts a duplicated
generator name without complaint.

The wider `ReductionContext` stays in 0.2, where the objects that determine
its requirements are built. It inherits the purity requirement: per-step
naming means handing out a fresh pure factory per step, not carrying one that
remembers.

### Release engineering

- a `LICENSE` file shipped in both wheel and sdist
- Python classifiers covering the whole supported range, not just the newest
- `make test-minimum` against the lowest permitted dependency versions
- `make build-test` running the suite against the installed wheel, so that
  packaging faults surface before a user meets them
- a CI matrix over both ends of `requires-python`

### Quality

- complete unit tests
- immutable SymPy objects across the whole public boundary, including
  `matrix` and `jacobian()`
- no mutable low-level object shared with a caller: rings are cloned on the
  way in and on the way out, through `clone_ring()` rather than SymPy's
  memoised `PolyRing.clone()`
- mypy strict mode, and a `py.typed` marker so that the annotations reach
  consumers rather than stopping at the project boundary
- ruff and mypy targeting the lower bound from `requires-python`, so that
  the static tools guard the oldest supported version rather than the
  newest; the test matrix covers the rest
- ruff (`ruff check` and `ruff format`; black was dropped in favour of a
  single formatter)
- a `slow` pytest marker so that long-running exact checks stay in the suite
  instead of being disabled by an environment variable
- API documentation in `docs/api.md`, with every example executed by the
  test suite so that the reference cannot drift from the implementation

---

# Version 0.2

**Status: released as `0.2.0`.** The milestone went through two external
audits between `0.2.0rc1` and the release. The first raised five findings, the
second one; none of the six required new functionality, and each is recorded in
`CHANGELOG.md` with what it changed.
`docs/contracts.md` states every obligation the surface below is held to.

## Verification framework

Introduce, at the top level,

- `Collision` and `VerificationError`
- `kellermap.linear`: dilations, transpositions, `LinearAutomorphism`
- `kellermap.reduction`: the `Step` protocol, `LinearStep`, `Reduction`
- `kellermap.context`: `ReductionContext` (building on the `VariableFactory`
  from 0.1)

and, in the `kellermap.bcw` subpackage,

- `BCWStep`

Only `BCWStep` is specific to the paper. A chain of certified identities is
not, and a second reduction method would reuse it, so `Reduction` stays at the
top level rather than becoming the misnomer the subpackage exists to avoid.
`LinearStep` composes an element of `GL_n(k)` on the left; that Chapter II,
Proposition (1.1) does so does not make the operation theirs.

Implement

```
BCWStep.verify()
```

Verification checks

- the polynomial identity

      F' = G ∘ F[m] ∘ H

- explicit invertibility of the elementary factors,
- required filtration levels,
- equality of Jacobian determinants as a consistency check.

All verification arithmetic is carried out in one shared `PolyRing` whenever
possible. At this point the project can produce machine-verifiable local proof
certificates.

`docs/contracts.md` states the obligations of `ReductionContext`, `BCWStep`
and `Reduction` normatively, with a stable identifier per obligation. It is
written before the implementation and binding on it, and is amended
deliberately rather than incidentally.

### The linear part is not elementary

The derivation begins with the linear normalization of BCW Chapter II,
Proposition (1.1).
Its transformation is a product of Gauss operations, and only some of them are
elementary in the sense of the paper. A transvection `X_i |-> X_i + a X_j` is
an `ElementaryFactor` already, in `EA^0`; a transposition and a dilation are
not, since a dilation displaces `X_j` by `(a - 1) X_j` and a transposition
moves two components and has determinant `-1`.

The shortest argument needs no factorization at all: every element of
`EA_n(k)` has determinant one, and the transformation normalizing Alpöge's map
has determinant `-1/2`. Over a field the transvections generate `SL_n`, so the
non-elementary content is exactly one dilation. This is why the linear part
gets its own type and its own kind of step, and why `LinearStep` is the only
step permitted to change the determinant.

### Collision tracking

The point of the project is a counterexample, so a step must move a collision,
not merely preserve degrees. From `F' = G ∘ F^[m] ∘ H` and `F(a) = F(b) = c`,

    a' = H^-1(a, u),  b' = H^-1(b, u),  F'(a') = F'(b') = G(c, u)

for one shared `u`. For Proposition (3.1) with `u = 0` this is
`a |-> (a, -P(a), -Q(a))` with the image unchanged. A `Collision` is a value
object verified by evaluation alone, which makes a transported collision the
cheapest certificate in the project and the one that carries its purpose.

### Two generalizations of Proposition (3.1)

The reference reduction of Alpöge's map to dimension 17 needs the step in a
form slightly wider than the paper states it, and `BCWStep` is specified for
that wider form in `contracts.md`.

`P * Q` is not the factorization of a single leading monomial `aM`. Formula (2)
holds for any subsum of the target component, and the reduction removes up to
four monomials in one step. Alpöge's map carries eight monomials of degree at
least four, so a monomial-by-monomial application needs at least eight steps
and so at least dimension 19 — at *least*, because the terms a step introduces
can themselves exceed degree three and call for further steps. That a published
19-dimensional reduction exists is not evidence for this count: it reaches 19
by sharing carrier variables, which is a different method (see
`references.md`).

The target component is not the first. Step seven acts on component 11, a
coordinate that step four introduced.

### Work packages

Development of 0.2 is split into seven work packages. They carry internal
version numbers 0.1.1 to 0.1.7 for orientation within the history; none of them
is a release. `pyproject.toml` stayed at `0.1.0` for the duration and moved to
`0.2.0rc1` in one step at the end; `0.2.0rc2` and `0.2.0rc3` carried the audit
fixes, and `0.2.0` followed once the release chain ran green. Git tags for work packages use the
`wp/` prefix, so that the release namespace `v*` stays clean.

| WP | Internal | Content | Done |
| --- | --- | --- | --- |
| 1 | 0.1.1 | `Collision`, `VerificationError` | yes |
| 2 | 0.1.2 | `kellermap.linear`: dilations, transpositions, `LinearAutomorphism` | yes |
| 3 | 0.1.3 | `kellermap.reduction`: `Step`, `LinearStep`, `Reduction` | yes |
| 4 | 0.1.4 | `BCWStep.verify()` | yes |
| 5 | 0.1.5 | `kellermap.context`: `ReductionContext` | yes |
| 6 | 0.1.6 | Integration: the eight steps from Alpöge to dimension 17 | yes |
| 7 | 0.1.7 | Documentation and release | yes |

Between 4 and 5 a further commit added the published 19-dimensional cubic
reduction as fixed input; see `references.md`. It is not a work package, and it
produced the one open question 0.2 leaves behind: BCW-2 fixes two fresh
variables per step, so a reduction that shares carrier variables across steps
cannot be expressed as a chain of `BCWStep`s at all.

Every work package leaves the repository green.

The order is not arbitrary. `Collision` and `kellermap.linear` depend on
nothing and settle the evaluation path early. `LinearStep` implements the
`Step` protocol before `BCWStep` does, so that the protocol is not shaped
around Proposition (3.1) alone. `ReductionContext` comes after `BCWStep`,
because only then is it known what the context has to guarantee — which is the
placement 0.1 already anticipated.

### Milestone target, and what was reached

The seventeen-dimensional map in `tests/test_bcw17.py` is derived rather than
asserted: a `Reduction` of eight steps from Alpöge's map, verified step by
step, transporting the three-point collision from `k^3` to `k^17`.

What that does and does not establish is worth stating precisely, since the
distinction is the central result of the milestone. The intermediate maps in dimensions
5 to 15 are published nowhere and therefore cannot be supplied; their steps
compare the implementation against itself, and the chain carries the weaker
provenance by RED-7. The external fact is the endpoint, where the last step is
given the fixed components as its target, and a negative control perturbs one
component, so that the test fails if the check does not work.
`scripts/reconstruct_bcw17.py`
carries the same chain in plain SymPy, as an independent second implementation
of formula (1).

---

# Version 0.3

**Status: released as `0.3.0`.** The milestone went through two external
audits. The first found no functional, algebraic or packaging blocker and four
text corrections, which `0.3.0rc2` carries; the second found two further
documentation corrections and recommended release.

## Carrier sharing, and `alpoege15`

A milestone of its own, and the line it falls on is the project's own: 0.2
verifies a factorization that is presented to it, and finding one is the
milestone after this. Carrier sharing is a *verification* capability — it
widens what a certificate can express and searches for nothing. What belongs
here is therefore everything needed to *check* a factorization of `alpoege15`
or of the published 19-dimensional map; producing one for the latter does not.

### The technique

After a step, the coordinate `X_u` carries `P` for good: its component stays
`X_u + P`, and no later step changes that unless it targets `u`. A step whose
factors are already carried therefore need not buy them again. With `X_u`
carrying `P` and `X_w` carrying `Q`,

    G = (…, X_i − X_u X_w, …),   F' = G ∘ F = (F_i − PQ) − X_u Q − P X_w − X_u X_w

which is the expansion of Proposition (3.1) with `X_w` in place of the second
fresh variable. `G` stays elementary, since `−X_u X_w` is free of `X_i` for
`i ∉ {u, w}`, and lies in `EA^1`. Three cases follow:

| carriers available | fresh variables | shape |
| --- | --- | --- |
| both | 0 | `F' = G ∘ F` |
| one | 1 | `F' = G ∘ F^[1] ∘ H` |
| neither | 2 | `F' = G ∘ F^[2] ∘ H`, the paper's own step |

None of this is in the paper, and taking it up is a deliberate extension.

### `alpoege15`

BCW17 carries two duplicated values: `x1²` in both `x5` and `x17`, and `x1x2`
in both `x8` and `x14`. That is not an accident of bookkeeping — steps 6 and 7
of the reference reduction each factor through a value an earlier step had
already bought. Each therefore needs one fresh variable instead of two, and the
chain lands in dimension 15:

- degree 3, Jacobian determinant 1, in `MA^0` and not in `MA^1`;
- the same three-point collision, with the first thirteen coordinates of each
  point identical to BCW17's, since the first five steps are unchanged;
- image `(0, 0, -1/4)` followed by twelve zeros.

Derived since this milestone: a `Reduction` of eight steps, verified one at a
time, carrying the collision. Both of its reusing steps are the `m = 1` case.
The last step is given the fixed components as its target, and those come from
`scripts/reconstruct_alpoege15.py`, which does not use this library.

No claim of minimality attaches to the number. The comparable published
reduction is the 19-dimensional one; the 24-variable map is cubic *homogeneous*
and a stricter normal form, and the 79-variable one is a conservative route.
Whether something smaller has appeared since should be rechecked before the
number is used anywhere outside this repository, and the customary disclaimer
of priority and global minimality applies.

### To build

`docs/contracts.md` states the obligations, marked `[0.3]`, and was written
before the implementation as it was for 0.2.

A step is given two *factor slots*. Each slot supplies one factor, either by
introducing a new generator (`Fresh`) or by reusing a coordinate of the source
that already carries the value (`Carried`). The number of distinct fresh
variables is `m`,
so `m ∈ {0, 1, 2}`, and two `Fresh` slots are exactly the step of 0.2.

Two things in the earlier plan for this milestone were dropped during
implementation, and both are recorded where they were decided.

A `BCWStep.classic()` constructor was to keep the call form of 0.2. It does not
exist. `Fresh(P, u), Fresh(Q, v)` is no longer than `P, Q, (u, v)` and shows
which factor belongs to which variable, so a second entry point earned nothing;
`contracts.md` states this. The constructor change is therefore breaking, and
`CHANGELOG.md` gives the migration.

The second is the separate step type for `m = 0`. Writing the contract led to a different
conclusion. A step `F' = G ∘ F` with `G` elementary is more general, but it
records only that some elementary automorphism was composed on the left. It
does not record which product was removed, from which component, or through
which two carriers. The slot form records all three and reduces to
`F' = G ∘ F` by itself when both slots are `Carried`. See "Why one type and not
two" in `contracts.md`.

### Work packages

Five work packages, with internal version numbers `0.2.1` to `0.2.5` and tags
`wp/0.2.n`. None of them is a release. `pyproject.toml` stayed at `0.2.0` for
the duration, moved to `0.3.0rc1` at the end, and reached `0.3.0` after two
audits.

| WP | Internal | Content | Done |
| --- | --- | --- | --- |
| 1 | 0.2.1 | `Fresh`, `Carried`, and `BCWStep` restated in terms of factor slots | yes |
| 2 | 0.2.2 | `m ∈ {0, 1, 2}` in the derivation and in `verify()`, and BCW-10 | yes |
| 3 | 0.2.3 | Collision transport for every `m` (BCW-8) | yes |
| 4 | 0.2.4 | `alpoege15` as a verified `Reduction` | yes |
| 5 | 0.2.5 | Documentation and release | yes |

Every work package leaves the repository green.

**WP 1** changes the shape of `BCWStep` without changing what it can do. `m`
stays fixed at 2, `BCWStep.classic()` keeps the call form of 0.2, and every
existing caller moves to it. It is done when the suite passes unchanged. The
point of separating this from WP 2 is that a failure in WP 2 then cannot have
its cause in the restructuring.

**WP 2** derives `m` from the slots. BCW-1 and BCW-2 use `m`; BCW-5 and BCW-6
handle the case where `H` is the identity; BCW-10 is added. It is done when a
step with one fresh variable and a step with none both build and verify, and
when the three clauses of BCW-10 have failing cases in the tests.

**WP 3** covers transport. A point gains one coordinate per fresh generator,
which was one per `Fresh` slot until BCW-12 made the two differ. The
image moves only at `m = 0`, and then to `c_index - c_u * c_w`. That case did
not exist in 0.2 and is the most likely place for an error, so it is tested on
its own.

**WP 4** builds the eight steps of `alpoege15` as a `Reduction`, with the
target supplied in the last step, and turns `tests/test_alpoege15.py` from
fixed input into a derivation. `test_the_chain_is_not_yet_expressible` is
removed. The provenance of the chain is `CONSTRUCTED` throughout, because this
library produced the target, and the tests say so — unlike BCW17, whose
endpoint came from outside.

**WP 5** removes the `[0.3]` markers from `contracts.md`, adds the factor slots
to `architecture.md`, marks `alpoege15` as derived in `references.md`, updates
`CHANGELOG.md`, and sets the version to `0.3.0`.

The 19-dimensional map appears in no work package. 0.3 gives its reduction a
language, but the step sequence remains unknown, and finding it is 0.4.

### Contract amendments

BCW-2 fixes `target.dimension == source.dimension + 2`. Changing it to a
derived `m ∈ {0, 1, 2}` is an amendment to `docs/contracts.md`, made
deliberately and visible in the wording, not an extension around it. It is the
only obligation this milestone weakens. BCW-10 is added.

### Not here

Finding a factorization. The published 19-dimensional map stays fixed input
after this milestone: carrier sharing gives the language in which its reduction
could be written down, but its step sequence is unpublished, and recovering it
is search. `alpoege15` is different only because we produced its sequence
ourselves.

---

# Version 0.4

**Status: released as `0.4.0`.** The milestone went through fifteen release
candidates and a series of external audits; the last found no blocker. What
each candidate changed is in the history of `CHANGELOG.md`, which carries one
consolidated entry for the release. `docs/contracts.md` states the obligations,
written before the implementation as for 0.2 and 0.3.

This page is the plan and the reasons for it. It says what each work package
was for and why the ones that were inserted exist. What an obligation requires
is in `contracts.md`, and why a piece of code is shaped as it is belongs in its
module; repeating either here would put one thing in two places.

## The step sequence of the 19-dimensional map

One release goal, and it is a search. The published nineteen-dimensional cubic
map has been fixed input since 0.2. 0.3 gave its reduction a language, by
admitting steps that reuse a carrier, but its step sequence is unpublished and
recovering it is the milestone.

It ends with the factorization certified, by three routes: a chain of `BCWStep`
in the test suite, an independent rendering in plain SymPy, and the backward
search, which reaches the map in eighteen examined maps. An external audit
reconstructed a chain first, and `references.md` records the order of events
and what may be claimed because of it.

An earlier plan for this milestone also carried the Reduction Theorem — degree
reduction, homogenization, unipotent reduction and a general pipeline. That is
Section 4 of the paper and a milestone of its own; putting it beside a search
would have made this one impossible to audit as a whole. It moves to 0.6, and
the milestones after it move down by one.

### What is known and what is not

Both ends are fixed. The source is Alpoege's three-dimensional map of degree 7,
the same map from which `bcw17` and `alpoege15` are derived; the target is the
published nineteen-dimensional map, held in `tests/data.py`. The source
describes seventeen elementary steps with sixteen carrier variables, so
`sum(m) == 16` over seventeen steps.

That is more of a constraint than it looks. Write `a` for the steps introducing
two generators, `b` for those introducing one and `c` for those introducing
none: `2a + b = 16` and `S = 16 - a + c`. Alpoege's map has no carriers, so a
`Carried` slot has nothing to point at and the first step must introduce two --
`a >= 1`, and a seventeen-step chain then needs `c = a + 1 >= 2`. With
`spare = 2` the structure is pinned: `a = 1`, `b = 14`, `c = 2`. The chain has
exactly that shape.

The carrier values are readable off the target, as they were for `bcw17` and
`alpoege15`. What the search has to find is their order, the co-factor each was
paired with, the component each step acted on, and -- since WP 10 -- the
constant each step scaled its product by.

**The numbering is not the introduction order.** Settled in work package 10 by
an external audit that reconstructed a chain, and verified here. The order is
`w1, w2, w4, w5, w8, w7, w9, w13, w16, w15, w14, w6, w12, w3, w11, w10`. This
page argued the opposite for several packages, on grounds that were sound and a
conclusion that was not; `references.md` records both readings and which one
the data settled.

### Three decisions taken before the implementation

**Fresh generators are given to the search, not allocated by it.** BCW-2 puts
the generators of a target in introduction order. A search allocating its own
names through a `ReductionContext` would therefore produce a map whose generator
order is not `w1` to `w16`, and the comparison against the published map would
need a second notion of equality. Instead the search is handed the sixteen names
and searches their assignment to steps. This is SEA-3.

What remains is a difference of presentation, and
`PolynomialMap.reordered()` settles it: the same map with its generators listed
in a given order, permuting the component tuple by the same permutation. It
changes no polynomial, it is not a `Step`, and it certifies nothing. This is
SEA-4, and "No claim from reordering" in `contracts.md` says the same from the
other side.

**A found chain is `CONSTRUCTED`, so the chain is not the evidence.** By BCW-9
every step the search builds compares the implementation against itself. The
external facts are two, and both live outside `verify()`: the reordered target
equals the published map, and the transported three-point collision equals the
published table. SEA-5 states them. This is the same distinction 0.2 drew at
`bcw17`, where only the endpoint could be supplied, and it is what an audit of
this milestone should look at first.

**The value pool is data too.** Taken in WP 5, after the measurement, and for the
same reason as the first decision: the factors are readable off the target, and
an enumerator that searched for them instead would be enumerating a space that
is infinite before SEA-9 normalizes it and exponential after. SEA-8 to SEA-10
state what the enumerator claims and what it does not. The price is that a step
outside the pool is unreachable rather than merely unfound, which
`contracts.md` records under "No completeness of the enumerator either".

## Open from 0.2 and 0.3

**The translation.** BCW Chapter II, Proposition (1.1) splits a map with
invertible linear part as `F = (X + F(0)) ∘ F_(1) ∘ F'` with `F' ∈ MA^1`.
`LinearStep.normalize` builds the last factor and therefore requires
`F(0) = 0`; a map that does not fix the origin is refused, naming the missing
step. The step itself is small, and worth noting: unlike the dilation, a
translation *is* elementary in the sense of the paper — `X_i ↦ X_i - c_i`
displaces `X_i` by a constant, which is free of `X_i` — so it needs no new
non-elementary type. It lies in no `EA^d` for `d ≥ 0` all the same, since
`EA^d` is defined inside `MA^d` and a translation leaves `MA^0`; its filtration
degree is `-1`.

It is not required for either driving example: Alpöge's map fixes the origin,
so neither `alpoege15` nor the 19-dimensional reduction ever needs it. That is
why it waits here rather than travelling with 0.3, and why it is the second work
package rather than the fifth: it extends the step surface, and it is better
done while that surface is otherwise quiet.

`TranslationStep` reports `filtration_level` as `math.inf`, not as `-1`. The
filtration degree `-1` belongs to the transformation; the step establishes no
`EA` bound on its target, exactly as a `LinearStep` does not. Reporting `-1`
would make `Reduction.filtration_level()` return `-1` for every chain that
begins with a translation, which says nothing about that chain's target. TRA-5
and the note under the `Step` protocol in `contracts.md` carry the reasoning.

## Work packages

Twelve work packages, with internal version numbers `0.3.1` to `0.3.12` and
tags `wp/0.3.n`. None of them is a release. `pyproject.toml` stayed at `0.3.0`
for the duration and moved to `0.4.0rc1` in one step at the end.

| WP | Internal | Content | Done |
| --- | --- | --- | --- |
| 1 | 0.3.1 | Plan and contracts | yes |
| 2 | 0.3.2 | `TranslationStep`, TRA-1 to TRA-8 | yes |
| 3 | 0.3.3 | `PolynomialMap.reordered()` | yes |
| 4 | 0.3.4 | A gate for the ASCII agreement | yes |
| 5 | 0.3.5 | SEA-8 to SEA-10, and the measurement behind them | yes |
| 6 | 0.3.6 | Candidate enumeration | yes |
| 7 | 0.3.7 | The forward search against a given target | yes |
| 8 | 0.3.8 | `examples.py` and `tests/data.py`: fixed data by provenance | yes |
| 9 | 0.3.9 | The backward search: peeling a chain off a target | yes |
| 10 | 0.3.10 | The coefficient and the repeated fresh slot | yes |
| 11 | 0.3.11 | `alpoege19` as a verified `Reduction` | yes |
| 12 | 0.3.12 | Documentation and release | yes |

The plan had seven, and five were inserted rather than appended. Each time the
packages behind moved down by one and nothing about their content changed.

- **WP 4** came out of WP 3, which turned up the one breach of the ASCII
  agreement in the tree and found no gate to attribute it to.
- **WP 5** came out of the measurement WP 6 was to make. The enumerator the
  plan implied was unaffordable, and the obligations narrowing it belong on the
  page before the code exists.
- **WP 9** goes before the backward search because it reshapes how fixed data
  is reached, and the backward search is what would otherwise reach it the old
  way and be rewritten.
- **WP 9** came out of WP 7, whose forward search exhausts its space without a
  chain and whose failure is not diagnosable from the inside.
- **WP 10** came from an external audit, which reconstructed a chain and showed
  that the certificate language could not express it.

Every work package leaves the repository green.

**WP 1** is this plan and the contract obligations. Its purpose is that an
external audit can hold intention and implementation against each other, which
requires the intention to be on record before the implementation exists. It
carries four corrections to `contracts.md`, listed under "Contract amendments"
below.

It is not quite `docs/`-only, and the exception is worth naming rather than
hiding. Moving selection from 0.5 to 0.4 leaves three milestone numbers stale
elsewhere: one sentence in `architecture.md`, one in `references.md`, and one
line of the module docstring of `kellermap.context`. They are corrected here
rather than in the documentation package at the end, because a number that
contradicts `contracts.md` for the rest of the milestone is the drift this
package exists to prevent. No behaviour, no
signature and no test changes.

**WP 2** implements `TranslationStep`. Independent of everything else in the
milestone: it needs no search, and no search needs it, since Alpöge's map fixes
the origin. It is done when a map outside `MA^0` can be carried into `MA^0` by a
`Reduction` of two steps, when `LinearStep.normalize` names the step that now
exists, and when TRA-1 and the first clause of TRA-6 have failing cases in the
tests.

The completion criterion is narrower than it was written. It asked for failing
cases for TRA-3, TRA-4 and both clauses of TRA-6 as well; writing the
implementation showed that three of those cannot be reached, because TRA-1 runs
first and rules them out. They carry `# pragma: no cover` with the reason, and
`contracts.md` says so under "Which of these can fail on supplied data". A test
for them would have to force the object into a state it cannot reach, which the
project does not do.

**WP 3** adds `PolynomialMap.reordered()` and nothing else. A restructuring,
separated from the search deliberately: the comparison SEA-5 rests on has to be
in place and tested on maps whose reordering is known before a search produces a
map whose reordering is not. A failure in WP 7 then cannot have its cause here.
It is done when reordering `bcw17` and `alpoege15` into a shuffled variable order
and back returns the original, when the determinant, the degree and the
filtration degree survive it, and when a non-permutation raises.

**WP 4** makes the ASCII agreement checkable. `AGENTS.md` requires Python files
to be pure ASCII, and until now nothing enforced it: `ruff` reports confusable
characters under RUF001 to RUF003, which a ring operator is not, and one had sat
in the docstring of `PolynomialMap.compose` since 0.3. `tests/test_ascii.py`
walks `src`, `tests` and `scripts` and names file, line, column and character.

It is a test rather than a `Makefile` target, so that it runs in every `pytest`
invocation — including the one `make build-test` fires against the installed
wheel. It names the three directories rather than walking from the root, because
`make build-test` and `make test-minimum` leave virtual environments in the
working tree, and a third party's files are neither ours nor covered by this
agreement.

**WP 5** states what the enumerator may claim, before it exists. The plan gave
WP 6 one sentence and left the affordability of free enumeration open; measuring
it first showed that the unrestricted enumerator is infinite before
normalization and exponential after, and that every factor the target needs is
readable off the target. SEA-8 to SEA-10 record that, with the numbers beside
them. `docs/` only.

The measurement is also what corrects the paragraph on topological orders above.
It was written as a measurement precisely so that it could come out the other
way, and it did. WP 7 then corrected the measurement itself, once the published
value of `w2` turned out not to be an introduced one.

**WP 6** enumerates candidates: for a given map and a given value pool, which
products can be removed from which component through which factor slots.
Deterministic and independent of any strategy, under SEA-8 to SEA-10. The
control is the reason it is its own package: the seven steps of `alpoege15` and
the seven of `bcw17` are known, and the enumerator contains each of them at the
map that precedes it, with the final map supplying the pool, and derives the
filtration level each of the fourteen declares.

It amended SEA-8. The pool bounds one factor of a candidate, not both: the
anchor comes from the pool or from a carrier, and the co-factor is obtained by
division and is free. The stronger reading was measured and gives zero
candidates at the first map. `contracts.md` carries the measurement and the
reason — a pool read off a final map is not the set of factors its chain used
wherever a later step rewrote a carrier, which is exactly what step seven of
`alpoege15` does to component 10.

The reading recorded above — that all seventeen steps of the published chain
acted on components 0, 1 or 2 — moves to WP 7, where a search either uses it or
does not.

**WP 8** is the forward search, under SEA-1 to SEA-14. It is given a pool of
values read off the target's carriers, because nothing in the source says what
a fresh coordinate may carry. It recovers a chain to `alpoege15` in 62 maps,
and only once the pool is handed the value coordinate 10 was introduced with:
the published component is the residue of a later step, so without that value
the chain is inexpressible rather than unfound. That failure looks exactly like
an empty space, which is why WP 9 exists.


**WP 9** sorts the fixed data by where it came from, which is a question of
licence and of what an audit can see rather than of convenience.
`kellermap.examples` takes the maps the project may distribute; `tests/data.py`
takes the nineteen-dimensional one, whose licence could not be established, and
the source archive excludes it.

Two counted criteria decide what is an example: written out more than once, and
a Keller map. The tree held 119 distinct `PolynomialMap` constructions, 25 of
them repeated, and the determinant sorted those into thirteen Keller maps and
six that are not. The six stay where they are used -- they are written the way
they are *because* they are not Keller maps, and a module named `examples`
beside this library would say otherwise about them.

Distributing a map does not change who computed it, so `SUPPLIED`, BCW-9 and
SEA-5 keep their meaning. A reader who finds `bcw17` under `src/` would see the
library checking against itself unless the module says otherwise, so every
entry names its origin and points at `references.md`.


**WP 9** searches backwards, and exists because a forward search that empties
its own space cannot say which of its rules emptied it.

A step leaves its fresh coordinate in exactly two components: its own, as
`X_u + P`, and the residue of the one it targeted. A coordinate occurring
anywhere else was read by a later step and cannot be the last introduced. That
is REV-2, and it is what makes the direction cheap -- six candidates for the
last step of the published map against the hundred and forty the forward
enumerator offers. Peeling needs no value pool and no names: the factors fall
out of the arithmetic, and so does the coefficient, which a linear condition
fixes rather than a search. REV-1 to REV-12 state the rest.

A peel is not a certificate. What it produces is a structure, named rather than
indexed; the chain is rebuilt forwards with `BCWStep.build`, verified, and only
then a `Reduction`. It recovers `alpoege15` in eight maps against sixty-two
forwards, and without the value the forward search cannot do without.


**WP 10** widens the certificate language to what the published chain uses. An
external audit reconstructed that chain while WP 9 ran, and this repository
verified it independently: seventeen steps reproducing all nineteen components
and all fifty-seven coordinates of the three collision points.

Two things in it no `BCWStep` could express. Its steps carry coefficients, and
its fifteenth step puts one fresh coordinate in both slots. BCW-11 and BCW-12
state them, BCW-1 and BCW-2 are amended, and both are marked as extensions
beyond Proposition (3.1) as carrier reuse already is. The coefficients cannot
be moved into a change of coordinates: the diagonal that would absorb them
needs `1/7` at step seven where the earlier steps force `1/9`.

The package removes as much as it adds. With the coefficient in the step, the
family is closed under conjugation by a diagonal, so a chain reaching a target
only up to `D` is expressible as one reaching it exactly. SEA-5 returns to
plain equality and the diagonal is withdrawn from it. That also settles a
question 0.5 would have inherited: searching without a target leaves nothing to
compare against, and the benchmark half of 0.5 compares the dimension reached,
which is invariant under a diagonal and a reordering anyway.


**WP 11** points the searches at the nineteen-dimensional map and records the
chain as a verified `Reduction`, with the collision transported through all
seventeen steps and a negative control on the coefficients. It adds
`scripts/reconstruct_alpoege19.py`, the second independent rendering of a
reduction this repository holds.

The peel reaches the map in eighteen examined maps, though not while this
package ran. The driver built its source with `over_field`, over `QQ`, while
the published
map is over `ZZ`, and `PolynomialMap` counts the coefficient domain as part of
its identity, so the search could not have arrived however long it ran. The
audit of `0.4.0rc1` found that; `references.md` records what may and may not be
claimed as a result.


**WP 12** removes the milestone markers from `contracts.md`, brings
`architecture.md` and `references.md` up to date, writes the changelog entry and
moves the version.

It also carries a test group that neither WP 10 nor WP 11 would have produced.
Two faults of this milestone were found by an audit and by an assembly rather
than by a test: `peeling.moves` never offered two `Carried` slots on one
coordinate, which BCW-6 has admitted since 0.3, and `BCWStep.transport`
appended a coordinate per `Fresh` slot rather than per fresh generator. Each
time every obligation of the step type had a test and nothing asked whether the
*rest* of the library admits the same shapes.
`tests/test_admissible_shapes.py` asks that, and a new admissible shape goes in
its list.


## Contract amendments

Four, all corrections rather than changes of obligation, and all visible in the
wording of `contracts.md`:

- RC-7 said selection was 0.5 while "No search" said searching was 0.4. The
  first is corrected; 0.4 searches against a known target, 0.5 without one.
- "No progress measure" carried the same wrong number and is corrected the same
  way.
- The error table row `filtration_level outside {0, 1}` was stated without a
  type. It is BCW-6 and belongs to `BCWStep`; read as a statement about
  `Step.filtration_level` it was already wrong in 0.3, since `LinearStep`
  reports `math.inf`.
- "No search" is withdrawn, in the shape of the entry 0.3 withdrew, and three
  narrower non-obligations take its place: no completeness, no optimality of
  the sequence, no claim from reordering.

WP 5 added rather than corrected: SEA-8, SEA-9 and SEA-10, with the measurements
that justify them beside them on the page. No obligation was withdrawn or
narrowed, and no identifier was reused.

BCW-10 is *not* amended. The search relies on a reused factor being carried by
a coordinate of the immediate source, which is how the obligation already reads.
Should the recovered sequence need a factor carried by an earlier map in the
chain, that amendment gets its own work package rather than being folded into
the search.

## Not here

The Reduction Theorem, and general selection. Degree reduction, homogenization,
unipotent reduction and a pipeline that reduces an arbitrary Keller map are 0.6.
Ranking, pruning and term-growth prediction for maps whose target is *not*
known are 0.5. The search of this milestone is bounded on both ends, and that
boundedness is what makes it a milestone rather than a research programme.

---

# Version 0.5

**The milestone is closed.** The language of the repository, the gate that
holds it, `CONTRIBUTING.md`, `undo` in the ring, the coefficient ring as a
stated space, equality of algebraic numbers, the second source map, what an
untargeted enumerator may claim, the untargeted search itself, what it spends,
the widened offer, the order over it, a bound that turned out not to be worth
writing, the comparison with the literature, and the release.

The list ran to work package 13 and named twelve things: the comparison was
missing from it while its number was in the count.

The measurement behind work package 8 is on the contract page under "The
untargeted search", because it is the reason the obligations read as they do
and not a separate finding. The short version: the space is small and empty at
degree three, BCW's own induction measure is too coarse for a search, and the
bound that works is exponential in the degree and proved only for the steps
that introduce a generator. What each of them
changed is in the history of the repository; the numbers work package 4
produced are under "Where the time goes" below.

## Untargeted search, and what a result without a target establishes

0.4 searched between two fixed endpoints. This made its result checkable. The
chain could be compared with a map published by someone else, and the
transported collision with a published table. Here the endpoint is not given.
A sequence has to be chosen rather than recovered. The first thing that changes
is not the algorithm. It is what a result means.

Candidate enumeration against a known target is 0.4's, under SEA-1 to SEA-14.
What is added is the search that has no target to read from, and the criteria
by which it chooses.

### What is known and what is not

Two external facts anchored 0.4, and both are gone here. The reordered target
equalled the published map, and the transported three-point collision equalled
the published table. Neither has a counterpart when the endpoint is whatever
the search arrives at.

Four statements remain. They are listed here in full.

- Every step the search builds compares the implementation against itself,
  under BCW-9. A chain is `CONSTRUCTED`, so the chain is not evidence about
  anyone else's mathematics.
- The endpoint has degree at most three. This is checkable, and it is the goal
  of the search.
- The collision still collides at the far end, transported through every step.
  This is a property of the source and the chain together and needs no
  published table.
- The chain has a length and the endpoint has a dimension.

A result is therefore the statement: there is a certified chain from this
Keller map to a cubic map in `n` dimensions. The statement is verifiable, and
it is a statement about this library's own arithmetic. The dimension `n` is an
upper bound. It is not a minimum.

### Three decisions taken before the implementation

**The endpoint is a property, not a map.** The search stops when the degree
reaches three. It follows that `n` is an upper bound: a search that stops at
the first cubic endpoint has found one chain, not the shortest. Exhausting a
bounded space does not change this, because the bound is a decision. SEA-12
already states this for the targeted search, and the untargeted search
inherits the clause unchanged. Every number published from this repository
states which space it belongs to. `docs/references.md` states what a comparison
with the literature does and does not establish.

**The enumerator is a new construction, and SEA-14 does not simply move.**
SEA-14 names two shapes the forward search does not build: a step with a
coefficient other than one, and a step whose two slots name one fresh
coordinate. Its reasons are specific to having a target. `enumerate_candidates`
divides a *displacement*, read off the difference between two known maps, and a
division has no place to put a weight. SEA-8 gives each of the two factors a
name from a pool that the target fixes. Without a target there is no
displacement to divide. The search chooses a factorization rather than
recovering one, so neither reason transfers, and neither does the boundary
automatically.

This is not an amendment to SEA. It is a second enumerator with its own
obligations, and it gets a family of its own on the contract page. That
family's obligations are written before the code exists, after a measurement,
for the same reason WP 5 of 0.4 was inserted. The enumerator that the plan
implies may be too expensive to run. If this is found out afterwards, the
obligations have to be written twice.

**The coefficient ring is part of the search space.** A step preserves the
domain of its source, so the source fixes what is reachable, and the ring is
not a matter of presentation. It becomes an explicit parameter before any
figure is compared with anything. A dimension reached over `QQ` and a dimension
reached over a number field are results about different search spaces.

## Open from 0.4

**The carrier.** A reused factor must be carried by a coordinate of the source
of that step, not by an earlier map in the chain. Unchanged since 0.3, and
stated in `docs/contracts.md`.

**The boundary of the forward search.** SEA-14 reaches a proper subset of the
chains `BCWStep` admits. `peel` has neither restriction. Whether the untargeted
search needs the step shapes that SEA-14 excludes is an open question. It is
answered by the measurement in WP 8 and not by assumption.

**The language of the repository.** `AGENTS.md` has said since 0.2 that
everything here is English, with test docstrings and test comments as the one
exception, German by existing convention. Two things are now known about that
sentence.

The exception should go. Every milestone since 0.2 has ended in external
audits, and 0.4 alone went through fifteen release candidates. Each audit read
the tests. A test is the sharpest statement of what an obligation means, and
half of the tests cannot be read by a reviewer who does not read German. The
exception was acceptable while the tests were an internal check. It is no
longer acceptable.

And the exception is not where the German is. Counted before this plan was
written: fifteen files outside `tests/` carry German comments, including
`src/kellermap/peeling.py` with forty-seven German function words,
`pyproject.toml`, the `Makefile` and the CI workflow. These files are not
covered by the exception. The rule forbids German there, and no gate checks it:
`tests/test_ascii.py` checks the characters and not the language. There are
therefore two changes and not one. The first repairs a breach of the existing
rule. The second changes the rule. They are two work packages, in that
order.

**`CONTRIBUTING.md`** was written before `v0.4.0` was tagged and did not make
the tag. It is a work package here and not a single commit, because adding a file at
the repository root now requires entries in two other files. The positive list
in `pyproject.toml` enforces this.

## Work packages

Fourteen work packages, with internal version numbers `0.4.1` to `0.4.14` and
tags `wp/0.4.n`. None of them is a release. `pyproject.toml` stays at `0.4.0`
for the duration and moves to `0.5.0rc1` in one step at the end.

| WP | Internal | Content |
| --- | --- | --- |
| 1 | 0.4.1 | German out of `src/`, `scripts/` and the configuration |
| 2 | 0.4.2 | The test docstrings, `AGENTS.md`, and a gate for the language |
| 3 | 0.4.3 | `CONTRIBUTING.md` |
| 4 | 0.4.4 | `undo` in the ring |
| 5 | 0.4.5 | The coefficient ring as an explicit parameter |
| 6 | 0.4.6 | Collisions over a number field, and the second source map |
| 7 | 0.4.7 | The Gao map as an example |
| 8 | 0.4.8 | What an untargeted enumerator may claim, and the measurement behind it |
| 9 | 0.4.9 | The untargeted search, without ranking |
| 10 | 0.4.10 | What a search spends: term growth and dimension growth, measured |
| 11 | 0.4.11 | Widening the offer |
| 11.1 | 0.4.11.1 | Choosing from it |
| 12 | 0.4.12 | Pruning |
| 13 | 0.4.13 | Benchmarks, and what they establish |
| 14 | 0.4.14 | Documentation and release |

Every work package leaves the repository green.

**WP 1 and WP 2** are the language, split because they are different changes.
WP 1 repairs a breach of a rule that has stood since 0.2. WP 2 changes the
rule. Neither package alters a single statement. Where a formulation is poor,
it is recorded and left to a package of its own. Translating and improving are
two different tasks. If they are mixed, the diff can no longer be reviewed as
a translation.

Both carry a mechanical control. Before and after each package, every `.py`
file is dumped as an abstract syntax tree with its docstrings removed, and the
dumps have to be identical. A green suite would not establish this. It would
only establish that the tests that exist still pass. An identical tree
establishes that no instruction was touched. WP 2 adds the gate that keeps the
rule true afterwards: a list of German function words, checked over every file,
in the form of `tests/test_ascii.py`. The check is a heuristic and needs a list
of allowed words. It is still better than a rule that nothing checks.

**WP 3** adds `CONTRIBUTING.md`, and with it the entry in the positive list of
`pyproject.toml` and in the shipped set of `tests/test_packaging.py`. It also
joins `PROSE` in `tests/test_documentation.py`, because it cites obligations.
A stale identifier in the page that new contributors read is the same defect as
one in `contracts.md`.

**WP 4** moves `undo` to `PolyElement`. Measured before the milestone began: a
peel against the published nineteen-dimensional map costs about 3.8 seconds
under `cProfile`, of which `undo` is 1.30 and `from_expr` is half of that. The
`m = 0` branch of `moves` has worked in the ring since `0.4.0rc3`. `undo` still
goes through expressions and rebuilds a `PolynomialMap` from them at every
step. This is a restructuring and changes no result. It comes before every
package that makes the search wider, because a wider search costs more.

**WP 5** makes the coefficient ring an explicit parameter of a search rather
than something read off whatever was passed in. No figure from this milestone
is comparable with anything until this exists.

**WP 6** admits a collision whose points are not rational, and it turned out
to be a different package from the one planned here.

The plan said a `Collision` holds points over the coefficient domain of its
map, which would put the second family of counterexamples, arXiv:2608.00222
§3.5, out of reach. That was an idea about the code and not a measurement. A
collision holds SymPy expressions and is evaluated as expressions, so its
points may live over an extension while the map lies over `QQ`. Built from the
paper and measured: the collision verifies, and it transports through a linear
step, a BCW step and a chain.

What was out of reach was equality. `kellermap.canonical` decided rational
functions and treated a radical as an atom, so two spellings of one algebraic
number were two points -- COL-4 read backwards -- and a correct image written
as a nested radical was rejected. `sqrtdenest` runs first now. The module says
what it claims, rational functions and square roots, and what it does not, a
radical of higher index.

A second source is more useful than a second example: agreement with it is
evidence about mathematics external to this project, and not about this
library's own arithmetic.

**WP 8** adds the Gao map. Its licence is established, CC BY 4.0, so unlike the
nineteen-dimensional map it can be distributed with the library.

**WP 9** states what an untargeted enumerator may claim, before it exists, and
makes the measurement that decides it. It answers two questions. How large is
the space for maps of the sizes this project already handles? Are the step
shapes that SEA-14 excludes needed to reach degree three? The obligations of
the new family are
written from the answers. `tests/test_documentation.py` compares its family
list with the contract page for equality, so a new family cannot be added to
one and forgotten in the other.

**WP 9** is the untargeted search itself, with no ranking and no pruning: the
enumerator of WP 8, a stopping criterion of degree three, and an outcome that
reports what it examined. It will be slow. That is intended: WP 11 and WP 12
need a measured baseline to be compared against.

Done, and the baseline is this. `reduce_to_degree3` reaches degree three from
Alpöge's normalized map in 21 steps into dimension 20, examining 21 maps in
0.3 seconds, and from Gao's in 177 steps into dimension 86, examining 177 maps
in 40 seconds. Both chains verify. Against those, the chain computed by hand
takes 8 steps into dimension 17, and `alpoege15` 8 into 15.

Neither search backtracked: examined equals the number of steps in both cases,
so taking the first candidate every time worked and the cost is the length of
what it found rather than the width of what it tried. That is what WP 11 has to
improve, and it says where to look.

It also puts a number on the theorem. BCW prove that every polynomial map
reduces to degree three, and their proof is an induction that never has to
choose: any step of the shape of Proposition (3.1) makes progress. A search
that only takes such steps therefore terminates and arrives, and that is what
the two runs show rather than something they were lucky to find. What is open
is not whether a chain exists but how short it is.

### The shape the later packages need

The measurement above says why ranking alone will not be enough. A search that
never backtracks cannot be improved by preferring one candidate over another
within a descent that already succeeds; it has to be made to look sideways.

Two things do that, and they belong together.

A bound on the dimension makes the space finite in the direction that matters.
`reduce_to_degree3` may buy a coordinate at every step, and both runs did; a
search told that it has at most `k` of them is forced to reuse carriers
instead, which is the extension that puts `alpoege15` two dimensions below
`bcw17`.

Dimension as a cost, beside the measure, turns the walk into a shortest-path
problem. The measure says how far there is to go and the dimension says what
has been spent, so a search can exhaust every chain in dimension `k` before it
buys the `k + 1`-st variable, the way Dijkstra's algorithm exhausts a distance
before it grows. Depth first with no cost does the opposite: it spends a
dimension whenever that is the first thing offered.

Neither is written here as an obligation, because neither has been measured.
WP 10 is what measures them.

**WP 10** measures what a search spends. Term growth per step, dimension growth
per step, and the points at which the two diverge. This package contains no
heuristic. It produces numbers and a way of reproducing them, like the profile
below and `scripts/mutation_probe.py`. Both are scripts that answer a question.
Neither is a gate.

Done. `scripts/search_cost.py` prints the per-step table for every chain this
repository can build. Three things came out of it, and the third changes what
WP 11 and WP 12 are.

**Term growth is a function of the dimension bought, so it measures nothing on
its own.** For the untargeted search, `terms` grows by exactly `2 + 2m` at
every one of the 21 steps, with no exception: the step removes the monomial it
acts on, puts three in its place, and each fresh coordinate brings a component
of two terms. The two quantities do not diverge because they are the same
quantity. Where the hand chains break the law, it is because a factor has
several terms, five times in `bcw17` and five in `alpoege15`, or because a new
term cancels one already there, once in `alpoege19`.

**The measure falls in very unequal amounts.** Along the untargeted chain, the
first step removes 45 and most later ones remove 3, which is one monomial of
degree four. Along `bcw17` one step removes 102. That is the quantity worth
ranking by, and `terms` is not.

**The gap is coverage and not ranking.** The high-yield steps all use a factor
with several terms: `bcw17` takes five such steps of seven, and its 102 comes
from a factor with four. The untargeted enumerator uses none, because it splits
a leading monomial and a product of polynomials is a monomial only when both
are. A ranking over the candidates it offers cannot reach those steps, because
they are not in the space.

That is the finding to act on. WP 11 as planned ranks what is offered; the
measurement says the offer is what wants widening first.

**WP 11** widens the offer, and it was planned to rank it. WP 10 found that
ranking cannot help: the high-yield steps use a factor with several terms and
the enumerator offers none, so they are not in the space to be ranked.

UNT-6 to UNT-9 state the wider space. Measured on a prototype, greedily on the
normalized Alpöge map: seven steps into dimension 13, against the eight into 15
of `alpoege15` and the 21 into 20 of the narrow enumerator. The chain has degree
three and determinant one, and Alpöge's three points transport through it and
verify.

Implemented. The offer at the normalized Alpöge map is 22 candidates, twelve
narrow and ten wide, and it contains the step that removes 102 of the measure,
against 66 before. Over both long chains, 272 candidates build, verify and
lower the measure.

`reduce_to_degree3` still took 21 steps into dimension 20 after this package,
because it walked in the order the enumerator fixed. WP 11.1 is what changed
that.

What that shows and what it does not is on the contract page under the
obligations. It is not a claim of minimality, the search being greedy, and not
a claim of priority, the literature not having been checked again. The divisor
degree `d // 2` is measured on one map, and the same rule did not finish on
Gao's in twenty-five minutes.
Duplicated carrier values are tried first. They can be read directly off the
components, and they are what produced `alpoege15`. Ranking changes which chain
is found first and how long the search takes. It does not turn one chain into a
different chain, and the tests check this.

**WP 11.1** chooses from the offer. WP 11 put the step worth 102 into the
space and the search still does not take it, because it walks in the order the
enumerator fixes and never backtracks.

Choosing is not pruning and the two are separate packages for the reason WP 12
gives about itself. An order discards nothing: every chain the search of WP 9
can reach stays reachable, and a wrong order costs length and not correctness.
A bound can be wrong, and a failure in the second must not be able to have its
cause in the first.

The table said "Ranking" for WP 11 while the prose said the offer was widened
instead. That is corrected here rather than left standing.

Done. UNT-10 orders by what a step removes and breaks ties by what it buys.
Measured over the widened offer, every chain verified:

| | Alpöge | Gao |
| --- | --- | --- |
| the order the enumerator happened to fix | 21 steps, dimension 20 | 177, 86 |
| largest removal, then fewest coordinates | 7, 13 | 29, 39 |

`reduce_to_degree3` now finds `alpoege13` by itself, which is what
`scripts/reconstruct_alpoege13.py` holds and what the three packages together
were for. The walk still never backtracks and discards nothing, UNT-11, so what
changed is which chain it walks into and not how much of the space it saw.

### How wide the space is below a bound

Measured before deciding what WP 12 should attempt, because the obvious hope
was that a bound on the dimension would force the search sideways and yield a
statement about what is not there.

Every distinct map reachable from Alpöge's normalized map under a bound of
twelve coordinates, by depth, after merging the paths that arrive at the same
map:

| depth | distinct maps | seconds |
| --- | --- | --- |
| 1 | 22 | 0 |
| 2 | 485 | 3 |
| 3 | 7736 | 62 |

The branching is about sixteen per level and does not fall: at depth three not
one map has reached degree three. The chain that exists has seven steps, so
depth four is around 120 000 maps, depth five around two million, and depth
seven past 10^8. That is a lower bound on the work, because the time grows
faster than the count as the maps themselves grow.

So a statement that no chain reaches degree three in dimension twelve is not
available from this direction. Not by pruning and not by shortest paths: both
have to exhaust the same space below the bound, and ordering the walk does not
make it smaller. Dijkstra's algorithm would decide which map to open next, and
there are 10^8 of them.

Two things follow. `alpoege13` stays a find and does not become a claim of
minimality, which `docs/references.md` already says and which now rests on a
number rather than on caution. And WP 12 is what it says below and no more: it
makes the search faster and says nothing about what does not exist. A statement
about dimension twelve would have to come from an argument about the structure,
or a bound showing that seven steps are needed. That is mathematics and not a
work package.

**WP 12** discards branches that cannot reach degree three within what is left.
This is the forward counterpart of REV-9, and it carries the same risk. A
bound that prunes too much reports a reachable chain as an exhausted space.
That result is wrong, not merely slow. The package needs a negative control:
every chain that the unpruned search of WP 9 finds must still be found.

Measured, and no code written. Two bounds were derived and both are provable
from the construction rather than observed.

The degree bound. A step replaces a monomial of degree `d` by terms of degree
at most `max(deg P, deg Q) + 1`, and `deg P + deg Q = d` forces
`max >= ceil(d/2)`, so the degree falls at most to `ceil(d/2) + 1`. Iterating
that to three is a lower bound on the steps still needed.

The component bound. A step acts on exactly one component, so it can clear at
most one of the components still carrying a monomial of degree four or more.
Their number is a lower bound on the steps still needed.

Both are correct and neither cuts anything worth having. Along the chains the
search finds, with a step limit set to the length the chain actually has:

| | steps offered | cut by the bound |
| --- | --- | --- |
| alpoege | 73 | 5, seven per cent |
| gao_quartic | 914 | 0, none |

The reason is that both bounds are local. They read one map and say how many
steps it needs at least, while what makes a chain long is that every step
removes one monomial or one group, which neither quantity sees. On Gao's map
the component bound *rises* over the first thirteen steps, from 3 to 10,
because each step creates two components that may themselves carry high
monomials; a bound that grows during the search cannot cut early. It becomes
exact only over the last three maps, where nothing is left to decide.

The other half of it was measured under WP 11: with a step limit one below the
chain that exists, pruning saved 22 of 4067 examined maps on Alpöge's.

So this package is a measurement and not an implementation. The requirement it
set itself is met in its strongest form: every chain the unpruned search finds
is still found, because nothing is pruned. Code that cuts nothing is surface
that wants maintaining.

A bound that would cut has to be non-local -- something about how much a single
step can remove, not about the state of one map. Nothing here suggests one, and
guessing would produce a heuristic where UNT-4 requires a stated rule.

**WP 13** compares. Reproducing published dimensions with machine-verifiable
certificates is the first correctness target. Improving them is the secondary
scientific goal. The two results are reported separately. Thompson's
twenty-four-variable result and Long's reduction, arXiv:2607.18186, are the
benchmarks named so far. Before any number leaves the repository the literature
is checked again, and `docs/references.md` states what the comparison
establishes and what it does not.

Done, and the check changed what the comparison says. `docs/references.md`
carries it; the three findings are these.

Thompson's twenty-four variables were named here as a benchmark and recorded on
the references page nowhere at all. They are now, together with a correction
another group made to the nilpotence index.

The figures are not at the same stage. BCW prove the Reduction Theorem in three
steps and every number in this project's table is at the first of them, degree
three. Thompson's 24 is cubic homogeneous, which is the third, and Long reports
39 at the first stage and 79 after the third for the same reduction. A figure
from after the first stage does not sit beside one from before it. This project
had carried out neither of the two later stages when the milestone closed and
therefore had no figure at either.

This paragraph said that the last stage roughly doubles the count. The doubling
is the second stage and the third costs one variable; the 0.6 section below has
the correction and the reason it matters for the cut into work packages.

The first target is met and the second is stated narrowly. The published
nineteen-variable reduction is reproduced with a machine-verifiable certificate.

Thirteen variables at degree three were reached a month earlier, by a different
route. The maintainer found the repository after the first pass of this package
and both of its maps were recomputed here and hold. `alpoege13` is therefore not
first, and `docs/references.md` says so and says who was.

That is the value of the wording the page already carried. The claim not made
is the claim that would now be wrong, and the correction cost a paragraph.
Reaching the same count twice by routes that share no construction is evidence
about the number and not about either method.

**WP 14** removes the milestone markers from `contracts.md`, brings the
documentation up to date, and prepares the release.

### Why the order

WP 1 to WP 3 change text only and touch nothing that computes. They come
first because they touch every file. A large text diff mixed with a change in
behaviour cannot be attributed to either of the two. WP 4 is a restructuring
that makes every later package cheaper. WP 5 to WP 7 widen what can be searched
over. WP 8 to WP 12 then widen how it is searched. WP 13 draws no comparison
until the earlier packages have fixed what is being compared.

The first sketch had one package for the heuristics. It is now WP 8 to WP 12,
split along three rules that 0.4 established. The obligations of an enumerator
are written before it exists and after a measurement. A baseline is built
before anything is compared against it. A bound that can discard a reachable
chain is a separate package from a ranking that cannot.

## Where the time goes

Measured before 0.5 began, so that the effort goes where it pays, and measured
again after work package 4. The table below is the state before it. A peel
against the published nineteen-dimensional map cost about 3.8 seconds under
`cProfile`. The profile is flat: no single call dominates.

| | share |
| --- | --- |
| `undo`, of which `from_expr` is half | 1.30 s |
| `_forward`, of which `verify` is most | 1.33 s |
| `moves` | 0.75 s |
| SymPy's expression cache, 150 730 calls | 0.94 s |
| `expand` | 0.67 s |

The time is spent in SymPy expression work, that is in `expand`, `from_expr`
and the cache. It is not spent in the arithmetic of individual coefficients. `from_expr` runs 2840 times
and `expand` 4378 times for eighteen examined maps.

The change that matters is therefore to work in the ring throughout. This is
WP 4.

### After work package 4

`undo` computes in the ring. The two versions were run alternately in one
session, because a single absolute number does not reproduce: the same
measurement on the same machine varied by a third between two sittings. What
compares is a pair taken back to back.

Four pairs, best of three runs each, on the nineteen-dimensional map:

| | before | after |
| --- | --- | --- |
| 1 | 0.956 s | 0.773 s |
| 2 | 0.919 s | 0.729 s |
| 3 | 0.893 s | 0.751 s |
| 4 | 0.904 s | 0.757 s |

About four fifths of the time, and the result is unchanged in every pair:
eighteen examined maps at depth seventeen, seventeen steps.

Two pairs under `cProfile`, where the shares are readable:

| | before | after |
| --- | --- | --- |
| `undo`, cumulative | 1.00 s and 1.10 s | 0.31 s and 0.32 s |
| calls to `from_expr` | 2840 | 0 |

The call count is the number that does not depend on the machine, and it is
the one to check first if this is ever measured again.

What is left of the expression work is not in `undo`. `to_polynomials` clones
the view ring on every call, and `clone_ring` is the largest single cost in
the profile after `verify`. That is the price of the value semantics several
audits examined, and it is not touched here. If a later example forces the
question, it is answered with a fresh measurement and not with this one.

What does not help is `gmpy2`. SymPy uses it for `ZZ` and `QQ` when it is
installed, and the maintainer asked whether it would help. Measured with and without,
on the same machine. `peel` on the fifteen-dimensional map: 0.73 s against
0.67 s. On the nineteen-dimensional map: 0.94 s against 0.89 s. The full suite
varies more between two runs of one configuration than between the two
configurations. The coefficients here are `1/2`, `-3`, `7`, `9`, and Python
is already fast on numbers of that size. `gmpy2` is faster on large ones.

It is also not free to adopt. `GROUND_TYPES` is global and not per ring. A test computing over `QQ` would
therefore run through different code depending on the environment. The three
reconstruction scripts use exact rational arithmetic, and several audits have
examined their independence. The release chain would double
its configurations for a gain in the noise.

## Not here

The Reduction Theorem, and a pipeline that reduces an arbitrary Keller map:
degree reduction, homogenization and unipotent reduction are 0.6.

Profiling the complete pipeline is 0.7. WP 4 belongs here and not there for
two reasons. It is a single measured change to this project's own code, and
every package from WP 9 on is more expensive without it. 0.7 profiles the
complete pipeline, which exists only after 0.6.

Minimality. Nothing in this milestone establishes that a dimension is the
smallest one reachable. No work package assumes otherwise.

---

# Version 0.6

**Status: released as `0.6.0`.** The milestone went through six release
candidates and six external audits; the last found no blocker. The first five
each found something the fast suite, the coverage requirement and the mutation
probe had all passed, and twice the finding was in a repair made for the
previous audit. `docs/errata.md` carries them under the candidate that carried
them, and `CHANGELOG.md` one consolidated entry for the release.

Ten work packages, and the plan below is what they were for. It lists nine; the
tenth prepares the Zenodo deposit, was not in the plan when the milestone was
cut, and says so where it stands. What is not here is the multi-affine
refinement of Theorem 2.1(b), which is stated under "What is not planned", and
the last link of the chain, which is 0.8.

The second and third stages of the Reduction Theorem, and the compression that
follows them.

Every figure this project has is at the first stage, degree three. The
published figures that are easiest to compare against are cubic homogeneous,
which is the third, so nothing here can be set beside them. That is the gap
0.6 closes.

The plan changed twice while it was being written. Compression was to be an
open question, measured and then designed; arXiv:2608.12543v1 makes it a
construction with a proof, and one that is short to implement. Then Section 4
was read again, for the cut into work packages, and the reading moved the
boundary between the first two of them. What stands below is the second
version.

## Which stage costs which dimensions

The first version of this plan gave the homogenization one work package and
said that it roughly doubles the dimension. Those are two statements about two
different steps, and the source separates them.

The second step, p. 306, is the one that doubles. Put

    E(T) = X + T F_(2) + T^2 F_(3)
    G(T) = (X + TY, Y)
    H(T) = (X, Y - T F_(3))

Then `G(T) o E(T)^[n] o H(T)` is `(X, Y) + N T` with `N = (F_(2) + Y, -F_(3))`,
and Lemma (4.1) gives that `J(N)` is nilpotent. At `T = 1` the result is a map
in `2n` variables. Dimension `n -> 2n`.

The third step, p. 307, costs one variable. With
`N(T) = N_(1) T^2 + N_(2) T + N_(3)` the map `L = (X + N(T), T)` is cubic
homogeneous in `n + 1` variables and `J(L)` is unipotent. Dimension
`n -> n + 1`.

Together `2n + 1`. Long's two figures are that arithmetic: 39 at degree three
and 79 after the homogeneous reduction, and `2 * 39 + 1 = 79`. The 0.5 section
above and `docs/references.md` both said that the last stage roughly doubles
the count. The total was right and the attribution was not, and both are
corrected. The entry under "Known limits" in the `0.5.0` section of
`CHANGELOG.md` carries the same wording and is left standing, because it
records what was true at that release.

## The input the second step needs

BCW start Section 4 from `F in MA^1_n(k)`, and `alpoege13` is not in it: the
linear part of its displacement has two non-zero entries, 7 and 6. They are
nilpotent, so the map is Keller all the same, but a term that carries no `T`
leaves the graded ring of Lemma (4.1) and the nilpotence argument does not
reach it.

The normalization is `LinearStep.normalize`, which this library has had since
0.3. The dimension does not move, and the collision points do not move either,
because `F(p) = F(q)` gives `A^(-1) F(p) = A^(-1) F(q)`. So the chain grows by
one step and nothing else. What matters for WP 1 is that the precondition is an
obligation the step checks and names, not an assumption about its input.

The determinant has to be one and not merely a non-zero constant, and writing
UNI-4 showed that this is not a second precondition. A map in `MA^1` has
Jacobian `I + J(N)` with every entry of `J(N)` free of a constant term, so its
determinant is a polynomial with constant term one; if that determinant is a
constant, it is one. `MA^1` already forces it. What the obligation excludes is
a source whose determinant is not constant at all, which is a map with no
Reduction Theorem to be part of. Alpoege's map has determinant `-2` and a
linear part of determinant `-2`, so it fails the `MA^1` clause rather than a
separate one, and the linear normalization repairs both at once.

## The figure this milestone is for

Measured before the packages were cut, in plain SymPy and without the library,
so that the cut is made against a number rather than against an expectation.

| | dimension | |
| --- | --- | --- |
| `alpoege13` | 13 | degree 3 |
| linear normalization | 13 | `ord(F - X) >= 2` |
| unipotent reduction | 26 | `J(N)` nilpotent |
| homogenization | 27 | cubic homogeneous, 78 monomials |
| collision-hull compression | 22 | sequence 3, 9, 20, 22, 22 |

Checked: the degrees, the homogeneity, that all three of Alpoege's points
survive every stage and keep one image, that the hull is invariant, that the
determinant of the restriction is one at three random points of the hull, and
that the Jacobian of its displacement is nilpotent there. Not checked: the
determinant as a polynomial. That is what the library is for, and the
measurement exists to be independent of it.

So this route lands below Thompson's 24 and above Macfarlane's 20. Three
things about the number.

Taken two points at a time the sequence begins `2, 4, 11`, which are the first
three of Thompson's `2, 4, 11, 20, 20`, and then stabilizes at 22 rather than
at 20. That is an observation and not yet a statement about anything.

The same measurement was made again on `alpoege12`, which WP 2 adds, and it is
the one the packages should be held to:

| | dimension | |
| --- | --- | --- |
| `alpoege12` | 12 | degree 3, already in `MA^1` |
| unipotent reduction | 24 | `J(N)` nilpotent |
| homogenization | 25 | cubic homogeneous, 65 monomials |
| collision-hull compression | 20 | sequence 3, 9, 19, 20, 20 |

One variable at the start is four at the end. Taken two points at a time the
sequence is `2, 4, 11, 20, 20`, which is Thompson's exactly, where `alpoege13`
gave `2, 4, 11, 22, 22`. Whether the two twenty-dimensional maps are the same
map is a different question and this project has not asked it; equal hull
dimensions are not an isomorphism. The symmetric lift would give 40 against
Prellberg's 40.

Dimension is not the only figure. The displacement has 78 cubic monomials
before the compression and 5370 after it, against Thompson's 54. The count
depends on the basis the elimination happens to produce, so it is a figure to
report and not one to compare, but a dense map is more expensive for everything
downstream.

The symmetric lift doubles again: 22 gives 44 quartic variables against
Prellberg's 40, and 20 gives 40. Arriving above a published figure is a result
and the plan does not assume otherwise; arriving at one exactly is not a claim
either.

The measurement is exploratory and stands here as a target. WP 1, WP 3 and
WP 5 have to reproduce it under the verification surface. If they do not, the
measurement was wrong and this section is corrected rather than the packages
argued with.

## The packages

**WP 1** implements the unipotent reduction, Chapter II, Section 4, second
step. Obligations first, as always.

The shape `G o F^[n] o H` is the shape `BCWStep` already carries, so the stable
extension and the elementary automorphisms are reused rather than rebuilt. Two
things are new. The factors are computed from the map itself and not supplied
or searched for, which makes this the first step type whose transformation is
determined by its source. And the target leaves `MA^1`: its displacement has
linear part `(Y, 0)`, so `filtration_level` has to say so rather than be
assumed.

The collision transports through `H(1)^(-1) = (X, Y + F_(3)(X))`: a point `p`
of the source lifts to `(p, F_(3)(p))`. Two distinct points stay distinct,
because they already differ in the first block.

The obligations are UNI-1 to UNI-12, and the step is implemented against them.
Two were decided by a measurement rather than by argument. UNI-9 requires the
nilpotence of the target's displacement, which is the property the step exists
for, and it is checked as the determinant of `(X + T * (target - X), T)`, one
coordinate wider than the target, rather than as a matrix power: that
determinant costs 0.72 seconds on the 26-variable target of `alpoege13`
normalized, against 0.65 seconds for the plain determinant of the same map
under UNI-10, while `J**26` did not finish in twenty-five minutes.
`det(I + T A) = 1` says that the characteristic polynomial of `A` is
`lambda^m`, and Cayley-Hamilton over a commutative ring gives `A^m = 0`, so the
cheap route proves the same thing.

The obligation first put the parameter in the coefficient domain, over `k[T]`.
That is correct and costs 2.06 seconds, and it also needs a fresh *parameter*,
which nothing in this repository allocates: RC-1 to RC-7 name generators. The
obligation was amended when the step was implemented and its wording says so.

The whole step, source checks included, verifies in 1.39 seconds at that
dimension, and building it takes 0.08.

**WP 2** takes `alpoege12` into the repository. It is the twelve-dimensional
cubic reduction of Alpoege's map that an external search driver found on 28
August 2026, and it is one dimension below `alpoege13`.

The package is not in the plan because a smaller number is worth having. It is
in the plan because the number changes what every package after it is measured
on, and because the check it carries changed what this milestone may claim.

*The literature first.* The check that `AGENTS.md` requires before a number
leaves the repository found that eleven variables at degree three were reached
on 20 July 2026, the day of Alpoege's announcement, in a GitHub gist, and
that the same map is printed in Section 6 of arXiv:2608.05392v1. So twelve is
not a record, thirteen was not one either when it was found, and
`docs/references.md` now says both. The section there also says why the earlier
check missed it: it searched for the number thirteen and for the phrase "cubic
homogeneous", and a gist titled for eleven variables was outside both. A check
made for a number one has just reached will not find a smaller one.

That is the finding of this package and it is recorded before anything else in
it, because everything else in it reads differently afterwards.

*What goes into the tree.* `examples.alpoege12` and
`examples.alpoege12_collision`, with the tests every example carries. The
driver and its result file are external to the library and internal to the
project, which is the distinction `AGENTS.md` draws: the agreement of the two
is a check that can fail, and it is not evidence about anybody else's
mathematics. `docs/references.md` records the provenance in those terms.

The map is already in `MA^1`, which `alpoege13` is not, so WP 1 applies to it
without a normalization first. Its chain is ten steps against seven, and it was
found under a hard dimension bound of twelve by a beam search that examined
404117 states in about two hours. A negative result from such a run says
nothing; this one is not negative.

*The second half of the package, now done.*
`scripts/reconstruct_alpoege12.py` replays the ten steps in plain SymPy,
seventeen checks in 0.7 seconds, and `AGENTS.md` and the `Makefile` name it.
Every other reference reduction has one, and a map without a reconstruction is
a map this project verified only with the code that produced it.

Writing it turned up a shape the thirteen-dimensional chain does not have. Two
of the ten steps take *both* factors from coordinates that earlier steps
bought, so they introduce no coordinate at all; one of those squares a single
coordinate against itself. Buying neither factor is the far end of the
extension that buying one already is, and the script names it where it is used.

It also turned up a gap in what a reconstruction checks. The scripts check the
dimension, the degree, the determinant and the carried points against values
written into them, and nothing in them compares the components with the example
in `kellermap.examples`. Two renderings could drift apart in a coordinate that
none of those figures sees. `tests/test_examples.py` now closes that for
`alpoege12` by loading the script and comparing. The same gap is open for the
other five reconstructions and is not closed here.

*What the package does not do.* It does not retarget the search. The driver
found twelve under a bound of twelve; whether the same enumerator reaches
eleven is not known, and the open question at the end of this section is where
that belongs.

### The move that takes eleven out of twelve

Worth its own heading because it is a design question and not a number. The
published eleven-variable construction passes through a twelve-variable map of
its own, and reaches eleven by a move this library has no form for.

Two coordinates `f` and `g` occur in the other components only through `f + g`.
After the determinant-one change `f = t`, `g = s - t` on the source and
`(Y_s, Y_t) = (Phi_f + Phi_g, Phi_f)` on the target, `t` survives only in its
own component, as `t + A(rest)`. A coordinate of that shape can be deleted. The
determinant does not change, because the deleted component contributes a one on
the diagonal and nothing off it, and the collision survives whole, because two
points that collide cannot differ in `t` alone.

Every step type in this library raises the dimension or leaves it alone. This
one lowers it, and it is not a `BCWStep` with different arguments; it is a
different kind of certificate, in the shape the compression of WP 5 also has.
Two candidates for one shape is a reason to design them together and a reason
not to design either in a hurry.

`alpoege12` does not admit the move in either cheap form. No coordinate is
deletable on its own, because the untargeted search buys a coordinate in order
to use it and each occurs in some other component; and no pair of coordinates
occurs elsewhere only through its sum. `tests/test_examples.py` holds the first
check and `docs/references.md` records both. They are narrow: a linear change
that manufactures such a pair out of something else is ruled out by neither.

Nothing here is a package of milestone 0.6. It is written down because WP 5
will build the first dimension-lowering certificate this library has, and
whoever designs it should know that a second one is waiting.

**WP 3** implements the homogenization, third step. One variable, cubic
homogeneous, and the collision transports by appending `1`. The obligations are
HOM-1 to HOM-10, and the step is implemented against them. Two of the ten
carried more than their wording suggested. HOM-3 rules out a source that is
Keller but not nilpotent, which is a map that exists and which no other
obligation would have caught. HOM-8, the slice, catches a source with a
constant term, since the formula has three slots and a part of degree zero has
none; `TranslationStep` is what removes one.

The package began with a restructuring and not with the step. Both the second
step and the third read a displacement by degree, and both ask whether a
Jacobian is nilpotent by the same determinant, so `kellermap.bcw.grading` holds
what they share. That is a separate change from the one that adds a step type,
in the order the working agreement gives. The first figure at
that stage is `alpoege13` homogenized, 27 against Thompson's 24 and
Macfarlane's 20, so it lands above both. The reason to carry on is WP 5 and
not this figure.

Separate from WP 1 because they are two constructions. A failure in the
homogenization must not be able to have its cause in the unipotent reduction.

**WP 4** takes Thompson's map into the repository, which WP 5 needs for its
control. This package is smaller than the first version of the plan made it.
The licence question is settled: the submission is CC BY 4.0 and that covers
the ancillary file, `docs/references.md` records it, and the values are already
transcribed into `scripts/reconstruct_prellberg40.py`.

What was left was where a map that two packages need should live, and the
answer splits the file rather than moving it.

`kellermap.examples.thompson24_homogeneous` and `thompson24_homogeneous_collision` hold the input:
twenty-four variables, cubic homogeneous, determinant one, a two-point
collision whose image is the first of the two points. It meets both criteria WP
8 of 0.5 set for an example, being a Keller map written out in more than one
place, and a caller of this library needs it as a map rather than as a
displacement.

The twenty-dimensional restriction stays in the script and only there. It is
the answer the compression has to arrive at, and an answer stored beside the
code that computes it is not a control: a change to the compression could then
be repaired by editing the expected value. The script does not import this
library, so what WP 5 is measured against sits outside it. The embedding stays
with it for the same reason.

Two transcriptions of one source can drift apart in a coefficient, so
`tests/test_examples.py` compares the map and the collision against the
script's, in the shape WP 2 used for `alpoege12`.

**WP 5** implements collision-hull compression. For `F = id + h` with `h`
homogeneous of degree `d` and a collision `F(p) = F(q)`, iterate

    W_0     = span{p, q}
    W_(v+1) = W_v + span{ T(w_1, ..., w_d) : w_j in W_v }

with `T` the symmetric polarization, and restrict. The restriction is Keller
again by Lemma 2 of that paper, and this project has a verification surface
that can check that rather than assume it: determinant, degree, and the
collision transported.

The negative control writes itself. Applied to Thompson's twenty-four-variable
map the sequence has to come out `2, 4, 11, 20, 20` and the subspace has to be
Macfarlane's. Those numbers were recomputed here from the manuscript's data
before this plan was written, so the package has a target it did not set
itself.

It came out stronger than that. The restriction is the published map `h`
component for component, and the basis is the published embedding row for row.
The reason is not a coincidence and is worth stating: a reduced row echelon
form is unique, and the embedding printed in the ancillary file is in one, so
agreement of the subspaces forces agreement of the bases. What is checked is
therefore the subspace, and no choice of basis could have repaired a wrong one.

Two measurements changed the implementation.

`PolyElement.evaluate` on a list of generators substitutes one at a time and
builds a polynomial at every step. The hull evaluates the displacement tens of
thousands of times, and through `evaluate` it did not finish on Thompson's map
in ten minutes. Reading the terms once and multiplying in the coefficient
domain brings it to 3.6 seconds.

The basis is kept in *reduced* row echelon form and not merely triangular. Both
span the same subspace; the unreduced one gives a restriction with 21988
monomials and the reduced one 49, which is what the published map has.
Verification falls from not finishing to 0.05 seconds with it. A basis is a
choice, and this is the choice that makes every figure downstream tractable.

The whole chain on `alpoege12` is then 12, 24, 25, 20, every step verified,
with the three points carried through. The number the milestone was cut for is
no longer exploratory.

A restriction is a new kind of step, and the obligations settle what kind. It
is a `Step`: nothing in STEP-1 to STEP-5 asks a target to extend its source, so
a `Reduction` can hold the whole chain from twelve variables to twenty. CHC-1
to CHC-10 state it, and three things in them are new to this page.

The target shares no generator with the source, where every step before it
extends one. `build` takes a collision as well as a source, because a different
collision generates a different hull; no other step needs the thing the others
merely carry. And `transport` can refuse a collision that genuinely holds for
the source, when its points leave the subspace, which no other transport can.

The type lives at the top level and not in `kellermap.bcw`. That subpackage
holds what Bass, Connell and Wright wrote.

One obligation came out shorter than the homogenization's counterpart, and the
reason is worth having on the page. CHC-4 asks only that the source is Keller,
where HOM-3 has to check nilpotence separately: under a homogeneous
displacement, `J(h)(lambda x) = lambda^(d-1) J(h)(x)` turns a constant
determinant into `det(I + s J(h)) = 1` for every `s`, so nilpotence follows.
The homogenization's source is not homogeneous and cannot borrow the argument.

**WP 6** takes `spacerat11` into the repository, and the pipeline through it
is the reason the package exists rather than the map.

Eleven variables at degree three, published on the day of Alpoege's
announcement and printed as `Phi` in Section 6 of arXiv:2608.05392v1. Run
through WP 1, WP 3 and WP 5 it gives 22, 23 and then **19** cubic homogeneous
variables, which is below the smallest cubic homogeneous figure this project
knows of. That number is why the map is here and not merely cited.

*What the pipeline gives, on the three maps this project can start from.*

| at degree three | unipotent | homogeneous | compressed |
| ---: | ---: | ---: | ---: |
| `alpoege13`, 13 | 26 | 27 | 22 |
| `alpoege12`, 12 | 24 | 25 | 20 |
| `spacerat11`, 11 | 22 | 23 | 19 |

Monotone on three points, which is evidence and not a law. It also makes the
open question at the end of this section look less urgent: minimizing the
dimension at degree three does appear to be a proxy for the number that gets
compared.

*The nineteen has to carry its stage wherever it appears.* `alpoege19` is
nineteen variables at degree *three* and has been in this repository since 0.4.
The two are different objects from different routes, and a bare nineteen names
neither.

*The map is not a source this library cannot reach.* `peel` finds six
`BCWStep`s from `examples.alpoege()` to it, examining seven maps in about a
third of a second, and the endpoint is the published map after reordering the
generators. The chain runs from Alpoege's map and not from its normalization,
which is forced: a step preserves the determinant, this map has `-2` and the
normalized source has one.

It is in `examples` all the same. `peel` is given its target, so deriving the
map needs the map, and the six steps say where it lies rather than how it was
found. `scripts/reconstruct_spacerat11.py` replays them in plain SymPy,
twenty-four checks, and compares the result against its own copy of Section 6.

*And it lies outside what the forward search offers.* Of the six steps, none
matches any candidate `untargeted_candidates` produces at the map before it.
The comparison is the one an external audit made for `macfarlane13`, where two
of seven matched, and it was validated first on the ten steps of the
`alpoege12` chain, which come from the enumerator by construction and match ten
of ten at the positions the driver's result file records. Without that control
a broken comparison and a real gap look alike.

That is a statement about the search and not about the map, and what to do
about it is not this milestone's business.

**WP 7** is the symmetric lift, SYM-1 to SYM-12. Theorem 3 part 3 of that
paper: over `Q(i)`,

    P_W(x, y) = i * sum_j y_j * hbar_j(x + i*y)

homogeneous of degree `d + 1`, with `id - grad(P_W)` a noninjective Keller map
and the second point at `rho = (I + J hbar(q)^T)^(-1) (p - q)`.

This is the step recorded here for two milestones as architecturally absent,
and the reason it was absent is that it needs `Q(i)`. The coefficient ring
became something a caller states in 0.5 and `canonical` learned to decide
algebraic numbers, so the two obstacles named at the time are gone.

The obligations are written and the step is implemented against them. Three
things in them are new to the contract page, and each was measured before it
was worded.

*The coefficient domain grows.* A source over `QQ` gives a target over `QQ(i)`,
where every other step keeps the domain and `guards.settled` uses equality of
domains as an invariant no BCW chain crosses. Measured on the compressed
twenty: the lift lands in `QQ_I`.

*Transport takes a pair and is asymmetric in it.* `p` goes to `(p, 0)` and `q`
to `(q + rho, i rho)`, so which point is which changes both. Every collision
this milestone produces has three points, so a caller has to narrow one, and
SYM-9 refuses rather than choosing.

*The determinant is not checked, and that is a first.* The figures:

| | |
| --- | --- |
| `P`, on the compressed twenty | 350 monomials, 0.2 s |
| the lifted map | 40 variables, degree 3, 1316 monomials, 1.6 s |
| `rho` | 0.2 s |
| the determinant at dimension six | one, under 0.01 s |
| the determinant at a random point of the forty | one, 25 s, twice |
| the determinant as a polynomial at forty | not in eight hours |

The last row is the one that decided SYM-7, and it took two machines to state
it. Two runs here were given about fifteen and about twelve minutes and neither
returned, and both were cut off by the environment rather than by a decision,
so neither was a figure. The maintainer then ran
`exploration/measure_lift_determinant.py` and stopped it after eight hours
without a result. That is the row.

The same run puts the sample-point determinant at 21.7 and 22.3 seconds against
25.0 and 25.6 here, so the two machines are within a fifth of each other and
the eight hours are not an artefact of a slow one.

That is why the obligation is worded around what the affordable route gives.
Twenty-five seconds and a value of one at a random point is the check the
`reconstruct_*` scripts make, and it falsifies without proving.

Implemented, the step is cheap everywhere the determinant is not: on the
compressed twenty it builds in 0.1 seconds, verifies in 0.3, transports in 0.5,
and its form has the 350 monomials Theorem 3 reports. That figure is the
control, and it is the same ancillary file the compression is checked against.

The chain from `spacerat11` runs 11, 22, 23, 19, 38, every step verified. Two
of the three collision points reach the end; the third is dropped at the lift,
where SYM-9 requires a pair and the caller chooses which.

**WP 8** compares, as WP 13 of 0.5 did, and reports what a comparison
establishes and what it does not. It is done, and the literature check that
opens it turned up a figure this project did not have.

The comparison is a table in `docs/references.md` under "What the pipeline
reaches", and `scripts/measure_pipeline.py` produces it: all three
degree-three maps through all four stages, every step verified, joined to
`make measure`. The two tie together in both directions, as the untargeted
figures already do -- the script fails when the page states a figure it does
not measure, and `tests/test_documentation.py` fails when the page stops
stating one it does.

The literature check found a second published quartic figure, and missed a
third record that has both of this project's. Prellberg's 40 comes from
Thompson's 24 by compressing first; a Zenodo record of 23 July 2026 reports 48
from the same 24 by applying de Bondt-van den Essen directly. A commit of
30 July 2026 in `royvanrijn/jacobian-research` states 19 cubic homogeneous and
38 quartic together, from a twelve-variable map derived from Macfarlane's
`F13`, and the maintainer found it a week after this package closed.

So neither number here is first, and `docs/references.md` says so.
`docs/errata.md` records what the section claimed and how the search missed a
Markdown file in a repository, which is the second time: the eleven-variable
map was in a gist. A search engine is not a literature search when the
literature is in repositories.

The same record corrects the nilpotency index of Thompson's map from 17 to 18.
Nothing here rests on it: the reconstruction does not recompute that index and
`docs/references.md` has never asserted it.

The density goes the other way, and the section says so rather than leaving it
out. Prellberg's `P` at 40 variables has 350 monomials; this project's at 38
has 386, and at 40 by the other route 398. Smaller in dimension is not smaller
in every sense. At that stage the numbers to beat are 24 and
20 for the cubic homogeneous form and 40 for the quartic gradient form, and
this project will have arrived by a different route. The literature is checked
again before any number leaves the repository. The last two times that check
was made it found a smaller published dimension than this project had: thirteen
a month earlier, and then eleven, on the day of the announcement. That is what
the rule is for, and WP 2 records what the second finding says about how the
check has to be made.

**WP 9** removes the `[0.6]` markers from `contracts.md`, brings the
documentation up to date and prepares the release.

It closes the gap WP 2 found and closed for one map only, and the measurement
that was to decide where the comparison goes settled it: loading the three
remaining scripts that hold a chain and rebuilding it costs 0.2 seconds
together, so `tests/test_examples.py` compares all four in the fast suite and
no slow marker is needed. Two scripts need no comparison, since
`reconstruct_alpoege19.py` and `reconstruct_macfarlane13.py` read their target
from `tests/data.py` rather than holding one.

That measurement is also where the package found that
`reconstruct_macfarlane13.py` was carrying a transcription of an unlicensed map
into the source archive. `docs/errata.md` records it.

*The pages first, and as a restructuring of its own.* `docs/references.md` has
grown to 1149 lines and 32 sections, and it now mixes four things: the
bibliography, the provenance and licences of third-party data, the comparisons
of figures, and the record of what this project reported wrongly and corrected.
The package splits the last two off.

`docs/errata.md` takes the corrections: the fourteen years that were
forty-four, the two days that were the same day, the sentence saying nothing
was copied from an ancillary file while the next paragraph said it was, the
claim that this project had no figure at a stage it had since reached, the
status line of `contracts.md` that said `0.4.0` through a release, and the
duplicated paragraph that WP 4 had made false. About a dozen paragraphs, which
is a tenth of the page.

`docs/provenance.md` takes what an audit reads: where each fixed map came from,
under what licence, what was changed, and what may be distributed.

What does *not* move is the reason a present sentence is worded as it is, even
where that reason came out of a correction. The eight hours behind SYM-7, the
timezone caveat on the announcement's timestamp, and "peel divides a
displacement and the enumerator splits a leading monomial" all stay. A page of
rules without their reasons invites the next reader to question the rule
instead of finding the reason.

Two things move with the split and belong in the same commit.
`tests/test_documentation.py` anchors on headings of `references.md`, including
the one the pipeline figures are tied to, and `AGENTS.md` points at that page
for the provenance of fixed test data.

*Then every docstring in the tree, read once against the question whether it is
still true.* Three claims in the header of `kellermap.examples` were false when
WP 6 looked at it, two of them since 0.5: a sentence about provenance that the
maps' own docstrings contradicted, a count measured in WP 8 of 0.5 and left in
the present tense, and a list of coefficient domains that omitted one. None of
them is reachable by a test, all three were found by reading, and the module
had grown four times since the header was written.

`README.md` is a third. Its feature list stops at the three step types of 0.5
and its "This milestone" section is 0.5's, while the section after it reports
what 0.6 finished. Two of those are release work and one is not: the list of
what the library does has been behind since the first package of this
milestone.

`docs/architecture.md` is the other half of that reading and the larger half.
It is 955 lines, it was not touched in this milestone, and it demonstrably
describes the architecture before it: its package diagram lists neither
`compression.py` nor `lift.py` and gives `bcw/` as "BCWStep", and it names none
of the four step types this milestone added. Three of its standing statements
are what 0.6 broke -- that a step is a composition, that a step does not lower
the dimension, and that a step keeps the coefficient domain -- and each is
still true of some steps and no longer of all.

That is a known shape rather than an accident. A docstring is written when a
thing is made and is not revisited when the thing around it changes, and
`tests/test_documentation.py` checks that citations exist and that ranges are
current, not that a sentence is still true. The reading is the instrument, and
the package that closes a milestone is when the tree is small enough to have
stopped moving.

The shape is the one WP 12 of 0.5 had. Two faults of that milestone were found
by an audit rather than by a test, and the package that closed the milestone
carried the test group neither of the packages before it would have produced.

### WP 10, which was not in this plan

**WP 10** prepares the Zenodo deposit: `CITATION.cff`, `docs/deposit.md`, the
disclosure section of `docs/provenance.md`, and the rule in `AGENTS.md` that a
new way of distributing the repository is checked against the licence rule
before it is used.

It is not in the list above because the deposit was not part of the plan when
the milestone was cut. It joins the milestone rather than waiting for 0.7
because a record is minted from a released archive and the release is here, and
because the check it carries belongs to this milestone: the automatic GitHub
integration would have published `tests/data.py`, which the source archive
excludes because its licence could not be established. That is the second time
this milestone that a distribution channel would have shipped an unlicensed
map, and `docs/errata.md` holds the first.

Nothing is minted by the package. The deposit happens after a green
`make release`, by hand, and `docs/deposit.md` carries the one check to run
before uploading.

### Why the order

WP 2 comes second because every package after it should be measured on the
smallest map this project has, and because the literature check it carries
changes what WP 8 may say. WP 1 and WP 3 come before WP 5 because compression
applies to homogeneous maps and nothing this project produces at degree three
is homogeneous. WP 4 comes before WP 5 because it is what WP 5 checks itself
against. WP 6 comes after WP 5 and not with WP 2, although both add a map,
because the reason to add this one is a number the pipeline produces and the
pipeline has to exist first. WP 7 comes after WP 6 because lifting from
nineteen and lifting from twenty are different answers. WP 8 draws no
comparison until the packages before it have fixed what is being compared.

## An open question this milestone raises and does not answer

The untargeted search minimizes the dimension at degree three. The number that
gets compared is the one after the second stage, the third and the compression.
That the smallest map at degree three minimizes the second is not shown and
does not follow from the first.

The first two stages are monotone in the dimension, `2n + 1`, and the
compression is not: the hull depends on the collision points and on the map,
and a chain ending at 15 could compress further than one ending at 12. The
three measurements above are three points and no more: 13 gave 22, 12 gave 20
and 11 gave 19, which is monotone on everything tried. That is weak evidence
that the dimension at degree three is a proxy for the number at the end, and it
is the reason this question is recorded here rather than acted on. Running
`alpoege15` and `bcw17` through the same four stages is cheap and is the next
measurement to make. Whether `reduce_to_degree3` should then be given a
different objective is not decided here, is not a package of this milestone,
and would be a milestone of its own.

## What is not planned

No claim about Zhao's Vanishing Conjecture beyond what the construction gives.
The quartic gradient form is a counterexample to it when the input is, and that
is a consequence and not a new result.

No minimality, at any stage. The measurement in the 0.5 section under WP 12
says why a statement about what does not exist is out of reach from this
direction, and neither the homogenization nor the compression changes that.
The compression is minimal along one route by Corollary 7 of that paper, and
that is a statement about the route and not about the number.

---

# Version 0.7

What BCW still owes, the two things milestone 0.6 measured and could not
finish, and the first question about the search that is worth asking in that
order.

Milestone 0.6 built the second and third stages of the Reduction Theorem and
the compression that follows them, so a map goes from degree three to a quartic
gradient form with every step certified. Two things it left behind. The
Reduction Theorem is not finished: Theorem 2.1(b) asks for more than a cubic
homogeneous form. And one obligation of the symmetric lift is worded around a
computation that did not finish, so it is argued rather than checked.

The plan below puts those two first, then the link this project has never had,
then the search.

## What BCW still owes

Theorem 2.1(b) asks for a form linear in each original variable and quadratic
only in `T`. This project produces the cubic homogeneous form and stops there,
which is enough for the corollary the literature usually quotes and is not the
theorem.

The case is small and stored: `(x + y^3, y)` homogenizes to a verified
five-dimensional target that still carries a `y^3`. Every obligation on that
target holds. It is the refinement that is missing and not a defect in what
exists, and `docs/references.md` says which is which.

What the refinement costs in dimensions is not known here, and the first
figure the work package should produce is that one.

## What the two published eleven- and twelve-variable maps have in common

Two reductions at degree three were published from different sources by
different people, and they use the same four moves.

The eleven-variable map comes from Alpoege's three-variable map of degree
seven. A monomial-by-monomial BCW reduction of it needs 39 variables. The
published derivation reaches 11 by: eliminating several products against one
shared coordinate; reusing a coordinate already introduced rather than
introducing the same factor twice; cancelling `x^2 y^2` against the square of a
coordinate that is already an output; and deleting a triangular coordinate
after a determinant-one change on a pair of them.

The twelve-variable map comes from Macfarlane's `F13` and is described in quite
different language, as a coordinate-pair restriction. Written out, its two
automorphisms are a source graph `x_13 + x_2^2` and a target completion
`y_4 - y_8^2`. The completion cancels the quartic the graph creates, and it
cancels it because `F13` has a component `x_8 + x_1 x_2`. That is the third
move above, and the restriction to the level set is the fourth.

The first two moves are carrier reuse, which this library has had since 0.3 and
which `AGENTS.md` marks as an extension beyond the paper. The third is an
elementary automorphism on the target and may already be expressible; that is a
question for a work package and not something to assume here. The fourth has no
step type.

**What that does not mean.** It does not mean the library cannot reach these
maps. `examples.spacerat11` is reached from `alpoege()` by six `BCWStep`s,
which `scripts/reconstruct_spacerat11.py` replays, and none of the six is a
descent. So the fourth move is a route this library cannot express and not a
map it cannot produce. Whether the twelve-variable map is also reachable
without it is open, and is one of the things WP 4 should settle.

The reason to care is the search rather than the certificates. Both published
derivations pass through a dimension they then leave, and a search that only
ever goes down cannot follow either.

## The packages

**WP 1** measures the bottleneck of SYM-7. The Jacobian determinant of the
symmetric lift of Thompson's compressed twenty -- 40 variables, cubic
homogeneous, over `QQ(i)` -- did not finish in eight hours. The same
determinant at a random rational point takes 22 seconds, and the same size over
`QQ` is seconds. Nothing is optimized in this package; the deliverable is which
factor carries the cost, and the specification below is written before the run
so that the figures do not pick the question.

The package owes `docs/contracts.md` one amendment, and it is stated here
rather than left to the end. The second paragraph of SYM-7 names two dimensions
and nothing else, so it reads as a statement about size. After WP 1 it names
the factor that was measured. If none is isolated it says so, and names the
factors that were separated. No new obligation and no new identifier: this
package builds no step type, changes no `verify()` and adds no check to the
verification surface.

**WP 2** implements the multi-affine refinement of Theorem 2.1(b), as a step
type with its obligations written first. `(x + y^3, y)` is the smallest case
and the first test. The package also states what the refinement costs in
dimensions on the maps already in the suite, because a stage that is not
measured cannot be set beside the tables in `docs/references.md`.

**WP 3** adds the de Bondt-van den Essen step, which is the one link of the
published chain this repository has never had. It needs a field containing
`i` throughout, which the symmetric lift already requires, so the domain
question is settled before the package starts.

**WP 4** is a measurement and decides the rest of the milestone. Two parts.

The first was specified in 0.6 and not run. Milestone 0.6 twice compared a
chain `peel` found against what `untargeted_candidates` offers, and twice the
answer was mostly no: two of seven steps matched for `macfarlane13`, none of
six for `spacerat11`. Sorted by shape, the six steps of the `spacerat11` chain
are:

| step | terms in the two factors | carried |
| ---: | --- | --- |
| 1 | 1, 3 | no |
| 2 | 1, 1 | no |
| 3 | 3, 1 | left |
| 4 | 1, 2 | left |
| 5 | 1, 1 | no |
| 6 | 1, 6 | left |

Three of them use only monomials and carried coordinates, which is exactly what
the enumerator deals in, and none of the three is offered. So there are two
independent gaps and the shape accounts for one of them. The first is known:
`peel` divides a displacement and can produce a factor with several terms, and
the enumerator splits a leading monomial and cannot. Steps 1, 4 and 6 are that,
with 3, 2 and 6 terms. The second is a hypothesis: the enumerator is anchored
to the *leading* monomial of a component, and the products of steps 2, 3 and 5
may sit elsewhere in theirs. That would make the anchor and not the shape the
reason. For each of the thirteen steps in the two chains, record which of the
two reasons applies, or a third if neither does.

The second part is new. Take the four moves of the section above and, for each,
say which step type of this library expresses it, or that none does. The third
move is the interesting one, because an elementary automorphism on the target
is available and whether it reaches that particular shear is a question with an
answer. The fourth is the one expected to be missing, and "expected" is the
word: it is a reading of two derivations and not a measurement.

**WP 5** is conditional on WP 4 and is written when WP 4 has run. If the
descent is missing and wanted, it is a certificate first: a step that
verifies a *supplied* claim that a map is a triangular extension of a
smaller one, with
the pair of determinant-one changes exhibited rather than asserted. The search
for the pair is a separate thing and comes after, which is the same division
`BCWStep` and `peel` already stand on.

**WP 6** is the target the milestone is for, and it is a search question and
not a construction question. The chain from Alpoege's map to `spacerat11`
exists: six steps, found by `peel`, which is given the target. Deriving the map
that way needs the map. The question is whether a search that is *not* given
the target finds those six steps, or any six, under a budget.

The deliverable is that answer and not a success. If the search does not get
there, the package says at which of the four moves it stopped and what the
budget was when it stopped, in the shape WP 1 uses. A measured failure at a
named step is worth more here than an unbounded run, and 0.6 has the precedent:
SYM-7 rests on a computation that was stopped after eight hours and reported as
having been stopped.

The twelve-variable map is the second probe of the same machinery, from
`macfarlane13` rather than from Alpoege. It is worth stating what that does and
does not need: the derivation is published and the map need not be transcribed,
because a chain that produces it produces its coefficients. Neither repository
that carries it has a licence, so a transcription is not available anyway, and
`docs/references.md` records both as cited and not copied.

### The measurement of WP 1

The point of the package is not one more timing. It is to replace a single
negative with a ladder of positives.

"Did not finish in eight hours" has no witness. A search result has one: the
external driver that found `alpoege12` in milestone 0.5 ran for hours, was not
taken into the repository, and did not need to be, because the map it produced
verifies in seconds. A computation that does not terminate produces nothing to
put beside it, which is why this one line of SYM-7 rests on a measurement where
everything else in the contract rests on an object.

So the deliverable is shaped by which of two outcomes the run has.

*If the cost is the method*, the result is positive and the question dissolves.
The determinant completes, SYM-7 becomes an obligation that is checked rather
than argued, and the check is its own reproduction.

*If the cost is not the method*, the result stays negative, and the
reproducible form is not the cell that failed. It is the ladder that did not:
a sequence of dimensions that each completed, with their times, from which
forty is an extrapolation rather than a single abandoned run. Every cell of
that ladder is cheap and terminates. The claim then lives in the slope, and a
slope can be recomputed.

**Four factors and not three.** The plan said dimension, domain and density.
The **method** is a fourth and was missing. `Matrix.det` chooses between
Bareiss, Berkowitz and LU, and a `DomainMatrix` over `QQ_I[x1..x40]` does
fraction-free arithmetic in the domain instead of generic `Expr` arithmetic. At
40 by 40 with polynomial entries those differ by more than a constant. A
measurement that separates three causes where there are four does not fail to
find the fourth; it distributes it over the three.

That is also the arm with the largest consequence, and the expectation is
written down here so that it can be wrong on record: the method is where this
is expected to land.

**Dimension.** The suite has no ladder. Six is where a lift's determinant costs
under a hundredth of a second; the next cubic homogeneous forms it can reach
are 19, 20, 22 and 24, whose lifts are 38, 40, 44 and 48, and 40 already does
not finish. There is nothing between 6 and 38, so the ladder has to be built:
pad a small map with identity coordinates, which raises the dimension and
leaves the nonlinear content alone.

What that measures is the cost of matrix size at fixed nonlinear content, and
that is a lower bound on the effect of dimension rather than the effect itself.
Padding adds rows that are unit vectors, and an elimination that exploits them
pays little for them. If padding is cheap, the honest conclusion is that size
alone is not the cost, not that dimension is free.

**Domain.** Two arms, and they measure different things. The first replaces `i`
by a rational constant in the same matrix. Sparsity and degree are kept and the
object is not: the result is not a lift, its determinant need not be one, and
the check below does not apply to it. The second keeps the field and changes
how it is written, `QQ_I` against an explicit `QQ(a)` with `a^2 + 1`. That one
is arguably part of the method and is recorded under both.

**Density.** Monomials per entry. The two natural points are close together --
Thompson's compressed twenty gives a `P` of 350 monomials and `spacerat11`
gives 386, at 40 and 38 -- and ten per cent apart separates nothing. The axis
therefore has to be synthetic: at one padded dimension, vary the number of
nonlinear terms of the map underneath. Synthetic, and the page says so.

**Method.** `Matrix.det` with each of `bareiss`, `berkowitz` and `lu`, the
default, and `DomainMatrix.det` over the polynomial ring. Fixed dimension,
fixed domain, fixed density.

**Two kinds of figure, and only one of them can be a gate.** This is where the
first draft of this page overreached, and the correction belongs in it.

The structural figures are machine-independent: the dimension of each rung of
the ladder, the monomials in each arm, that a determinant which completes on a
lift arm is one, and that the perturbed control is not one. Those are figures
of the same kind `scripts/measure_pipeline.py` already holds against
`docs/references.md`, and they are gated the same way -- recomputed, compared
with the number on the page, and a mismatch stops the run.

The timings are not. A second is a statement about a machine, a Python version
and a SymPy version, and no assertion about one belongs in a suite that runs
elsewhere. They are recorded on this page beside the three, and what makes them
checkable is a rerun and a comparison rather than a gate. One cell is a
calibration cell that any second machine runs, in the way `0.6` used the
sample-point determinant to show that two machines were within a fifth of each
other before letting the eight hours stand.

An answer is therefore a ratio per factor with the other three held fixed, and
"no single factor" is an allowed outcome, declared allowed here because a
specification that only admits a winner will find one.

**Where each part runs.** The cheap cells go into
`scripts/measure_determinant.py`, in the shape of `measure_pipeline.py`: it
recomputes the structural figures, checks them against this page, and prints
the timings without asserting them. It joins `make measure`, the gate list of
`AGENTS.md` and the two tests in `tests/test_documentation.py` that hold the
list and the Makefile against each other.

An earlier draft of this section said such a script would be the first thing in
`scripts/` that is not a gate. That was wrong. `measure_pipeline.py` and
`untargeted_space.py` are measurements and are gates, and what makes them gates
is exactly this: a measurement becomes a gate by checking its own figures
against the page that states them.

The expensive cell stays in `experiments/`, which is local and outside version
control, and produces the one line that does not terminate. A file that runs
for hours and whose statement is carried by the ladder does not belong in the
archive, on the same reasoning that kept the `alpoege12` search driver out of
it in `0.5`.

**The budget, and what an overrun prints.** The script takes a budget per cell,
prints the cheap cells first, and prints the budget it exceeded rather than a
time. A cell that runs out is recorded as over the budget and never as a
number. Milestone 0.6 has the case that made this a rule: two runs of about
fifteen and about twelve minutes were cut off by the environment and could be
reported as nothing at all.

Cells over ten minutes are the maintainer's. Each run records the machine, the
Python version and the SymPy version, not so that anyone repeats the number but
so that a later run can be compared with it.

**The one check, and its control.** Where a determinant completes on an arm
that is still a lift, it must be one. A timing of a computation that is allowed
to be wrong measures nothing. The control is a perturbed matrix whose
determinant is not one, on which the script says so and does not report a time.
Without it there is no way to tell whether the check runs.

**One thing to settle by looking, early.** If any construction the measurement
needs is more than a call to the existing API -- padding a map with identity
coordinates is the candidate -- it belongs in the library or the suite and not
in a local script. That is a question the first hour of the package answers,
and it is written here so that it is answered rather than assumed.

### Why the order

WP 1 before WP 2 although WP 2 is the more important of the two. WP 2 makes the
chain longer, and a determinant that does not finish at 40 variables will not
finish at whatever the refinement produces. Knowing which of the three costs
dominates is worth more before the input grows than after.

WP 4 before WP 5 and WP 6 because it decides both. If the enumerator's gap is
the anchor rather than the shape, the widening is small and WP 6 may need
nothing new. If the descent is missing and needed, WP 5 exists and WP 6 waits
for it. Writing either package now would be writing it against a guess.

WP 3 is independent of all of them and can go anywhere. It is placed third
because it is the one package whose result is a new link rather than a better
version of an existing one, and a milestone that ends with only measurements
and a search would be a thin one.

## An open question this milestone raises and does not answer

Both published derivations pass through a larger dimension before reaching the
smaller one: 12 before 11, 13 before 12. Every search this project has goes
down and never up. Whether a search that may go up finds anything the present
one does not is a real question and is not this milestone's: it changes the
shape of the search and not one of its steps, and the measurement that would
justify it is WP 4.

## What is not planned

No minimality, at any stage, for the same reason 0.6 gives.

No priority claim, and in particular none about eleven against twelve. The
degree-three table in `docs/references.md` carries a determinant column because
its rows are not normalized alike: the eleven-variable map has determinant `-2`
and a linear part that is not the identity, the twelve-variable ones have
determinant one. Whether the normalization preserves the dimension is a
calculation nobody here has done, and until it is done the two numbers are not
a comparison.

No claim about Zhao's Vanishing Conjecture. `Delta^m(P^m)` is 0.8 and stays
there.

---

# Version 0.8

This section was a list of six engineering items until milestone 0.6 closed.
Two of them are done, two belong to 0.7, and the list left out the one thing
0.6 made possible. It is rewritten here rather than ticked off, and what it
said is in `docs/errata.md`.

## The last link of the chain

`docs/references.md` states the chain this project follows: Jacobian
Conjecture, BCW reduction, gradient form, Zhao's Vanishing Conjecture.
Milestone 0.6 built everything up to the gradient form. The last link is not in
this repository at all, and nothing in the roadmap asked for it.

For a quartic `P` with nilpotent Hessian, the Vanishing Conjecture says that
`Delta^m(P^m) = 0` for all large `m`. A counterexample is a `P` where it is
not, and this project now produces such a `P` in 38 variables without ever
looking at the Laplacian.

The work is to compute `Delta^m(P^m)` for the smallest `m` that decides it, and
to say what the computation shows and at what cost. The ancillary file of
arXiv:2608.12543v1 checks the term count of `Delta(P^2)` for the
forty-variable form and this project has never recomputed it, which is the
obvious first target and a figure that already exists to be checked against.

Two things to settle before any of it. Whether the check belongs in the library
or in a script -- it is one polynomial identity about one object and not a step
of a chain, so a `reconstruct_`-style script is the likelier home. And what
happens at 38 variables where a determinant already needed eight hours: `P^2`
has on the order of a hundred thousand terms before the Laplacian touches it,
so a run belongs to the maintainer under the rule in `AGENTS.md` and the first
job is a budgeted measurement, not an implementation.

## A benchmark runner

What the old list asked for that is still missing, and now with a reason.

Two measurement scripts exist, `untargeted_space.py` and `measure_pipeline.py`,
both tied to a page in both directions. Neither produces machine-readable
output and neither compares across releases, so a regression in cost is
invisible until somebody notices a gate taking longer. The timing tables in
`AGENTS.md` are maintained by hand and were last measured at the end of 0.5,
against a suite that has since grown by a quarter.

The runner is worth building only after 0.7 has profiled the pipeline, because
until then there is no agreed list of what to measure.

## What the old list had that is done

Independent certificate replay: eight `reconstruct_*` scripts, none of which
imports the library, and after WP 9 of 0.6 each compared against the example it
denotes.

Verified reduction certificates for large examples: `measure_pipeline.py`
verifies every step of three chains up to 44 variables, and the suite carries
the 38-variable gradient form behind a slow marker.

Large-scale regression tests are the suite, which is at 1760 tests and 100 per
cent coverage; what is missing there is the *cost* side, which is the runner
above.

Performance comparisons across releases and a reproducible benchmark runner
overlap with milestone 0.7, which profiles and optimizes. They stay here rather
than moving, because 0.7 asks what is slow and 0.8 asks whether it got slower.

---

# Version 0.9

## User experience

- history and certificate inspection,
- LaTeX export,
- visualization,
- command-line improvements,
- extended documentation.

---

# Long-term Goals

- dimensions well beyond the current benchmark,
- reproducible and independently replayable reduction certificates,
- publishable heuristic and benchmark results,
- optional accelerated arithmetic without changing certificate semantics,
- automated verification of complete BCW reductions.
