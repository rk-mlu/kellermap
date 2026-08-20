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
- **WP 8** goes before the backward search because it reshapes how fixed data
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

**WP 7** is the forward search, under SEA-1 to SEA-14. It is given a pool of
values read off the target's carriers, because nothing in the source says what
a fresh coordinate may carry. It recovers a chain to `alpoege15` in 62 maps,
and only once the pool is handed the value coordinate 10 was introduced with:
the published component is the residue of a later step, so without that value
the chain is inexpressible rather than unfound. That failure looks exactly like
an empty space, which is why WP 9 exists.


**WP 8** sorts the fixed data by where it came from, which is a question of
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

**Work packages 1 to 9 are done.** The language of the repository, the gate
that holds it, `CONTRIBUTING.md`, `undo` in the ring, the coefficient ring as a
stated space, equality of algebraic numbers, the second source map, what an
untargeted enumerator may claim, and the untargeted search itself.

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
| 11 | 0.4.11 | Ranking |
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

**WP 7** adds the Gao map. Its licence is established, CC BY 4.0, so unlike the
nineteen-dimensional map it can be distributed with the library.

**WP 8** states what an untargeted enumerator may claim, before it exists, and
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

**WP 11** ranks candidates by the criteria WP 10 found to predict something.
Duplicated carrier values are tried first. They can be read directly off the
components, and they are what produced `alpoege15`. Ranking changes which chain
is found first and how long the search takes. It does not turn one chain into a
different chain, and the tests check this.

**WP 12** discards branches that cannot reach degree three within what is left.
This is the forward counterpart of REV-9, and it carries the same risk. A
bound that prunes too much reports a reachable chain as an exhausted space.
That result is wrong, not merely slow. The package needs a negative control:
every chain that the unpruned search of WP 9 finds must still be found.

**WP 13** compares. Reproducing published dimensions with machine-verifiable
certificates is the first correctness target. Improving them is the secondary
scientific goal. The two results are reported separately. Thompson's
twenty-four-variable result and Long's reduction, arXiv:2607.18186, are the
benchmarks named so far. Before any number leaves the repository the literature
is checked again, and `docs/references.md` states what the comparison
establishes and what it does not.

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

## The Reduction Theorem

Moved here from 0.4, where it stood beside a search and would have made that
milestone impossible to audit as a whole.

Implement

- degree reduction,
- elementary transformations,
- stable extension,
- homogenization and unipotent reduction,
- complete reduction pipeline.

This is Section 4 of the paper: the reduction of an arbitrary Keller map to a
cubic homogeneous one with nilpotent Jacobian. 0.2 to 0.4 build and search
chains for particular maps; this milestone reduces a map that is handed to it,
which needs the general construction rather than a sequence someone chose.

Goal:

Produce fully verified reductions for examples from the literature without
recomputing global invariants that follow from the certified local steps.

---

# Version 0.7

## Performance engineering

Profile the complete reduction pipeline and optimize only measured bottlenecks.

Possible work:

- power caching during repeated composition,
- further determinant strategies beyond the unipotent-block case of 0.1,
- fraction-free or modular determinant algorithms,
- parallel candidate evaluation,
- memory-aware term storage,
- reduced conversion at certificate boundaries.

Evaluate optional acceleration through python-flint or Singular only if the
PolyRing benchmarks demonstrate that pure SymPy cannot reach the target
problem sizes. Any accelerator must preserve the PolyRing-level mathematical
semantics and certificate format.

---

# Version 0.8

## Complete verification and benchmark framework

- large-scale regression tests,
- reproducible benchmark runner,
- machine-readable benchmark results,
- performance comparisons across releases,
- verified reduction certificates for large examples,
- independent certificate replay.

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
