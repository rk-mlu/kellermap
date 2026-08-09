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
that already carries the value (`Carried`). The number of `Fresh` slots is `m`,
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

**WP 3** covers transport. A point gains one coordinate per `Fresh` slot. The
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

**Status: in progress.** `docs/contracts.md` states the obligations, marked
`[0.4]`, and was written before the implementation as it was for 0.2 and 0.3.

## The step sequence of the 19-dimensional map

One release goal, and it is a search. The published nineteen-dimensional cubic
map has been fixed input since 0.2. 0.3 gave its reduction a language, by
admitting steps that reuse a carrier, but its step sequence is unpublished and
recovering it is the milestone.

An earlier plan for this milestone also carried the Reduction Theorem — degree
reduction, homogenization, unipotent reduction and a general pipeline. That is
Section 4 of the paper and a milestone of its own; putting it beside a search
would have made this one impossible to audit as a whole. It moves to 0.6, and
the milestones after it move down by one.

### What is known and what is not

Both ends are fixed. The source is Alpöge's three-dimensional map of degree 7,
the same map from which `bcw17` and `alpoege15` are derived; the target is the
published nineteen-dimensional map in `tests/test_alpoege19.py`. The source
describes seventeen elementary steps with sixteen carrier variables. Since the
dimension grows from 3 to 19, `sum(m) == 16` over seventeen steps, so at least
one step has `m = 0`. That is a constraint on the search and a check on its
result.

What is not known is the sequence. The source publishes the map but not its
factorization.

The numbering, on the other hand, is probably the introduction order after all.
This page said it was not, on the evidence that the fifth component uses `w13`
and `w9` and so cannot come fifth. That component is `w2`'s, and the `w2`
finding below shows it to be a residue rather than an introduced value. With
that corrected, every dependency points to a smaller index — `w6 <- w1`,
`w8 <- w4`, `w10 <- w2`, `w11 <- w3`, `w12 <- w6`, `w14 <- w7`, `w15 <- w8` —
so `w1` to `w16` is a valid introduction order and the only evidence against it
has been explained away.

That is a hypothesis and not a result: it is one valid order among some
7.26e10, and consistency is not proof. It is, however, the order an author
numbering carriers as they introduce them would produce, and nothing in the data
contradicts it. WP 7 tries it first.

What *is* readable is every factor. A `Fresh` slot introduces `X_u + P`, so the
sixteen carrier values `components[3 + j] - w_j` are the sixteen factors the
seventeen steps supplied. They are written out under SEA-8 in `contracts.md`.
The search therefore does not look for the factors. It looks for their order,
for the co-factor each was paired with, and for the component each step acted
on.

The carriers constrain the order, and less than this page assumed. Their
dependency graph is acyclic — `tests/test_alpoege19.py` already relies on that
when it reconstructs the collision by iterating `w_j = -P_j` from zero — so a
topological order of that graph is a necessary condition on the introduction
order. Whether it narrows the search to a handful of orders was left here as a
measurement. WP 5 made it, and the answer is no:

    12 108 096 000 topological orders.

That figure is superseded, and by the `w2` finding below rather than by a
recount. It was computed from the *published* carrier values, and the published
value of `w2` is not an introduced value. It names `w13` and `w9` only because
it is a residue; the value `w2` was introduced with, `x^3 y`, names no carrier
at all. With that corrected, `w2` is a root rather than a link in a chain:

    72 648 576 000 topological orders.

Nine of the sixteen values then depend on no other carrier, and the rest form
short chains: `w1 → w6 → w12`, `w4 → w8 → w15`, `w3 → w11`, `w7 → w14`, and
`w2 → w10`. The first number was wrong in the direction that flatters the
search, which is worth naming: a graph read off a published map over-constrains
wherever a step has rewritten a carrier.

Neither figure changes the conclusion, and the conclusion is what the
measurement was for. The order is a filter the search can apply and not a filter
the search can rest on. It is in fact not a filter the search applies at all: a
pool value naming `w1` does not convert into the ring until `w1` is a generator,
so the dependency enforces itself in the arithmetic. The graph is a property of
the answer rather than a lever on the way to it, which is the more useful
correction of the two.

One step of the sequence is known. The component of `w2` is not an introduced
carrier value but the residue of a later step: with `w13` and `w9` in the two
slots, carrying `x^2` and `x y`, the formula leaves exactly
`-w13 w9 - w13 x y - w9 x^2` once `x^3 y` is removed, and `x^3 y` is the product
of those two carried values. So `w2` was introduced carrying `x^3 y`, and a
later step took it out again with two `Carried` slots. That step has `m = 0`,
which the arithmetic requires: the dimension grows by 16 over 17 steps. It is
also the only carrier of the published map that shows the signature of a
residue, a monomial in two carrier variables. `tests/test_alpoege19.py` verifies
the identity, a perturbation of it, and the uniqueness.

The finding has a consequence for the search. The value `x^3 y` is not in the
pool read off the target, so the step that introduced `w2` is reachable only
through its partner. The condition under which a read pool carries at all — that
every step has a factor no later step overwrites — is named under SEA-8 in
`contracts.md`, together with the degree bound that makes it plausible here and
the reason that bound does not generalize.

One further reading is *not* established and is recorded here so that it is not
assumed by accident. Fifteen of the sixteen carrier components of the published map have
two terms, `w2` has four, and every carrier value is a clean product. That is consistent
with no step ever having targeted a carrier component, hence with all seventeen
steps acting on components 0, 1 or 2 — which would narrow the search
considerably. It does not follow from the shapes alone, and `alpoege15` is a
counterexample to the general pattern: its step seven targets component 10. WP 6
tests it rather than presupposing it.

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

Eleven work packages, with internal version numbers `0.3.1` to `0.3.11` and
tags `wp/0.3.n`. None of them is a release. `pyproject.toml` stays at `0.3.0`
for the duration and moves to `0.4.0rc1` in one step at the end.

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
| 10 | 0.3.10 | `alpoege19` as a verified `Reduction` | no |
| 11 | 0.3.11 | Documentation and release | no |

The plan had seven, and four packages were inserted rather than appended. WP 4
came out of WP 3, which turned up the one breach of the ASCII agreement in the
tree and found no gate to attribute it to. WP 5 came out of the measurement WP 6
was to make: the enumerator the plan implied turned out to be unaffordable, and
the obligations that narrow it belong on the page before the code exists rather
than beside it afterwards. WP 9 came out of WP 7, whose forward search exhausts
its space without a chain and whose failure is not diagnosable from the inside.
WP 8 was agreed while WP 7 ran and had no place in this table until now; it goes
*before* the backward search because it reshapes how fixed data is reached and
the backward search is what would otherwise reach it the old way and be
rewritten. Each time the packages behind moved down by one and nothing about
their content changed.

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

**WP 7** is the forward search, under SEA-1 to SEA-13. It recovers a known chain
from its own endpoints before being pointed at the unknown one, and it reports
what it examined and whether it finished.

Two things it forced. The `w2` step of the published chain is recorded here
rather than in the package that runs the search, because it stands whether or
not the search succeeds. And
SEA-5 is amended: the published map is reached up to conjugation by a diagonal
`D` of ones and minus ones, which the search reports. `contracts.md` carries
the reason and the verified identity relating the two sign conventions.

It is done when it recovers a chain to `alpoege15` from Alpoege's normalized map
and the published fifteen-dimensional one. That criterion was met late: WP 7 was
first marked complete on the strength of small examples, and the reference
recovery only followed while preparing the run. It found a chain in 62 maps, with
`D` the identity, and the chain is *not* the recorded one — its degrees run
`7, 6, 5, 4, 4, 4, 4, 3` against the recorded `7, 7, 7, 7, 5, 4, 4, 3`. A chain,
not the chain, which is what "No optimality of the sequence" already says.

Two rules bound the walk, both decisions rather than facts: the degree never
rises, and the dimension never passes the target's. SEA-12 says so. Moves are
tried lower degree and fewer terms first, and that ordering is not what took the
reference recovery from "nothing at 400 maps" to "found at 62" — supplying the
missing carrier value did. A set of already-visited maps was tried alongside it
and removed again: two orders that introduce the same generators list them in
the order they arrived, so the maps differ and the set almost never fires.

SEA-11 and SEA-13 came out of it as well: the budget and the depth are
reported, and a fresh factor the pool does not hold takes a free name at the
cost of a counted rewrite. The second is measured rather than assumed to help:
recovering `alpoege15` costs 62 maps with `rewrites=0` and does not finish
within 400 with `rewrites=1`.

The package closes without reaching the nineteen-dimensional map, and the way it
fails is why WP 9 exists. Two runs on the maintainer's machine exhausted the
space without a chain, the second after the `spare` correction and with the same
count to the map, 68425, because the walk never got past six steps. A forward
search that exhausts an empty space cannot say which of its rules emptied it.
The scan that closed the pool question is the pattern to follow: rather than
searching harder, compute the thing directly. WP 9 does that from the other end.

**WP 8** sorts the fixed data by where it came from, which is a question of
licence and of what an audit can see, not of convenience.

`src/kellermap/examples.py` takes the maps the project may distribute: Alpoege's
three-dimensional map, which every chain starts from and which now has a
citable, licensed presentation; the seventeen- and fifteen-dimensional maps,
which are the maintainer's own hand computation; and the small maps that are
currently written out in more than one place. Each carries a line saying where
it came from.

Two criteria decide what goes in, and both are measured rather than judged: a
map belongs there if it is written out **more than once**, and if it **is a
Keller map**. The tree holds 119 distinct `PolynomialMap` constructions, 25 of
them written more than once, and the determinant sorts those 25 as follows.

Repeated and Keller, so in scope:

| uses | map | determinant |
| --- | --- | --- |
| 13 | `(x + y, x - y)` | -2 |
| 5 | `(X1 - X3 X4, X2, X3, X4)` | 1 |
| 4 | `(T x + y, x)` over `k[T]` | -1 |
| 3 | `(x1 + x2^2 x3^2, x2, x3)` | 1 |
| 3 | `(x + y^2, y)` | 1 |
| 3 | `(x + y^3, y)` | 1 |
| 2 | Alpoege's three-dimensional map | -2 |
| 2 | `(X1, X2, X3 + X2^2, X4 + X2^2)` | 1 |
| 2 | `(x, y + x^2)` | 1 |
| 2 | `(2 X1 + X2^2, X2)` | 2 |
| 2 | `(x + y, y)` | 1 |
| 2 | `(x + T y^2, y)` over `k[T]` | 1 |
| 2 | `(x1 + 1, x2, x3)` | 1 |

Repeated and *not* Keller, so out of scope:

| uses | map | determinant |
| --- | --- | --- |
| 6 | `(x + x^2 y^3, y)` | `1 + 2 x y^3` |
| 5 | `(x1^2, x2, x3)` | `2 x1` |
| 3 | `(X1 + X2^2, X2 + X1^2)` | `1 - 4 X1 X2` |
| 2 | `(x^2, y)` | `2 x` |
| 2 | `(x^2, y, z)` | `2 x` |
| 2 | `(X3 x, y)` | `X3` |

The second table is the point of the second criterion. Those maps are written
the way they are *because* they are not Keller maps -- they exercise degree
growth, non-injectivity and a non-constant determinant -- and a module named
`examples` next to a library about Keller maps would say otherwise. They stay
where they are used.

Two of them are worth tidying locally all the same, and that is a different
change from this one. All six uses of `(x + x^2 y^3, y)` are in
`tests/test_search.py` and want one fixture there. `(x1^2, x2, x3)` is written
five times across three modules; whether that earns a shared test helper is a
judgement, not a rule, and the package may leave it alone.

The identity map is a third case and belongs to neither table. It is not one
object repeated but a family, so what removes the repetition is a constructor
and not a constant: `PolynomialMap.identity(variables)`, added in this package.

The count that argues for it: forty-one places write the identity out, six of
them in `src/kellermap` itself, in two spellings. `PolynomialMap(V, V)` occurs
twenty-one times and repeats its own variable list, where a typo in the second
copy gives a map that is not the identity and still constructs.
`from_ring(ring, ring.gens)` occurs twenty times, repeats nothing and keeps its
ring explicit; it stays as it is, and the constructor covers only the spelling
that repeated something.

The entries are functions rather than module-level constants, so that importing
`kellermap` does not build a fifteen- and a seventeen-dimensional map nobody
asked for, and so that the caller decides the coefficient domain.

The package runs in two commits, and the repository is green after each. The
first adds `examples.py` with the small maps and Alpoege's, and changes no call
site, so that the naming can be read before forty places depend on it. Between
the two commits those maps stand in two places, which is what this package is
against; it is bounded, named here, and closed by the second commit. The
fifteen- and seventeen-dimensional maps are not duplicated even briefly: they
*move* in the second commit rather than appearing first and being removed
afterwards, because a seventeen-dimensional map written twice is a different
risk from `(x + y, y)` written twice.

`tests/data.py` takes the nineteen-dimensional map, which stays out of the
wheel. Its licence cannot be established, and `AGENTS.md` says not to vendor
such data. It is also the one datum whose externality the milestone's result
rests on, so having it visibly outside the distributed package costs nothing and
saves an auditor a question.

One thing has to be right in that package and is easy to get wrong. Shipping a
map does not change who computed it, so `SUPPLIED`, BCW-9 and SEA-5 mean exactly
what they meant before. But a reader who finds `bcw17` under `src/` sees the
library checking against itself unless the module says otherwise, so every
entry names its origin and points at `references.md`. `contracts.md` gains a
short statement that the module is fixed data, carries no obligations of its
own, and does not move the line between what this library derives and what is
given to it.

The scripts lose their `read()` detour for the two maps that move into the
package and keep it for the one that does not, which puts the distinction in the
code rather than only in a document.

**WP 9** searches backwards, and the measurement that motivates it is on this
page rather than in a commit message. A step that introduces a fresh coordinate
leaves it in exactly two components: its own, as `X_u + P`, and the residue of
the component it targeted. A coordinate occurring anywhere else was used by a
later step and cannot be the last one introduced. Six of the sixteen carriers of
the published map satisfy that, and `tests/test_alpoege19.py` records which.

Six candidates for the last step against the hundred and forty the forward
enumerator offers at a map of that size is the whole argument. Peeling also
needs no value pool: the factors fall out of the arithmetic instead of being
supplied, so SEA-8 and SEA-13 and the failure modes they carry do not apply to
it. Nor does it need a sign choice — the sign is decided by whether the
coordinate actually disappears.

An exploratory peel reaches dimension 14 from 19 and finds the `m = 0` step on
`w2` for the third time, by a third method. It also places that step four steps
before the end, which withdraws the assumption
`scripts/search_alpoege19.py` was making.

The measurement that shapes the surface is the sign. A step subtracts the
product of its two slot components, so undoing it adds that product back --
except that the published map is not in this library's sign convention, and the
difference is the `D` of SEA-5. Peeling with `+` alone stops at dimension 18,
with `-` alone at 17, and with both at 15. The signs are mixed and each one is
a linear equation over GF(2) for `D`, so peeling produces the constraints on it
while running, where the forward search had to solve for it at the end. REV-4
records this.

Peeling is a different operation from building, so it gets its own obligations.
A chain found backwards is rebuilt forwards and verified, and the endpoint
comparison of SEA-5 is unchanged.

What it cost and what it bought, measured. Recovering the fifteen-dimensional
map takes **8 maps and under a second**, against 62 maps forwards -- and,
which matters more, without a value pool: the forward search manages that
recovery only when handed a value the published map no longer carries.
Against the nineteen-dimensional map the space is **exhausted after 376 maps
in three minutes**, where the forward search needed 68425 maps and two and a
half hours to say the same thing about a different space. Neither holds a
chain. The direction did not find the sequence; it made the question cheap
enough to ask repeatedly.

Widening the backward space is cheap, and two widenings were tried. Computing
the product of a step's two slot components once per pair instead of once per
candidate takes the exhausted run from 196 to 74 seconds, which made a second
step that introduces no generator affordable: `spare=2` exhausts as well, 1100
maps in 297 seconds, and reaches exactly the same depth of six.

What blocks it at six is measured and is not a matter of budget. The map there
has dimension 14 and degree 7, and six of its coordinates satisfy REV-2 --
`w2`, `w9`, `w11`, `w13`, `w14`, `w15`. Not one of them has a partner: for
every carrier of that map and both signs, undoing leaves the coordinate
standing. The rules exclude the chain rather than the budget hiding it.

REV-2 is not the suspect. A coordinate introduced last is read by nobody, so it
occurs in its own component and in the residue of the one its step targeted,
and in no third. The condition is exact for the last coordinate rather than a
heuristic, and widening it would admit coordinates that cannot be last without
admitting any that can.

The suspect was SEA-5's diagonal, and it was the right suspect. `D` was
restricted to ones and minus ones, so undoing admitted the factors `+1` and
`-1` and nothing else. A diagonal change of coordinates with arbitrary non-zero
entries is just as much an isomorphism, and under it the product term picks up
`d_i / (d_u d_v)`, any non-zero constant. That constant is fixed by the
requirement that the dropped coordinates vanish, which is linear in it, so it
is solved rather than tried.

The widening took the peel from **depth six to depth eleven** against the
published map, and the space is no longer exhausted. Recovering the
fifteen-dimensional map still costs 8 maps. SEA-5 and REV-4 record the change;
REV-2 is untouched.

`spare` was then corrected, and the correction came from the maintainer rather
than from a measurement. Write `a` for the steps introducing two generators,
`b` for those introducing one and `c` for those introducing none. Then
`2a + b = 16` and the chain has `S = 16 - a + c` steps. Alpoege's map has no
carriers, so a `Carried` slot has nothing to point at and the first step must
introduce two: `a >= 1`. A seventeen-step chain therefore needs `c = a + 1 >= 2`.

`spare=1` could not have found a seventeen-step chain whatever the budget, and
the reason I chose it -- sixteen generators over seventeen steps, so at least
one step introduces none -- silently assumed every other step introduces
exactly one. With `spare=2` the structure is pinned: `a = 1`, `b = 14`,
`c = 2`, and the peel reaches **depth sixteen** of the seventeen.

One coordinate short, and the shortfall has a shape. At depth sixteen the map
has four coordinates and only `w3` is removable, with no carrier left to pair
it with. A last step introducing one coordinate has a `Carried` slot whose
component is unchanged by that step, which makes it a carrier of the source as
well -- so a source without carriers cannot be reached that way, and a peel
standing at one coordinate more than the source is finished. That prune is in
`peeling.py`, and it is a statement about the source that was handed in rather
than a rule about Keller maps.

The move order decides more than anything else here. With coordinate-removing
steps offered one at a time first, the fifteen-dimensional recovery does not
come through in 1500 maps; with the steps that remove two offered first, it
takes 8. A step that removes two coordinates gets twice as far for the same
depth.

**WP 10** points it at the nineteen-dimensional map.
`scripts/search_alpoege19.py` drives the run: it reads Alpoege's map and the
published one from the test modules rather than copying them, builds the pool
with `w2` corrected, and searches with a doubling budget so that a long run
prints a trail. It is not a gate and not a second independent computation, and
its docstring says so — the two `reconstruct_` scripts stand apart from the
library on purpose, and this one drives it.

Its exit status distinguishes the three outcomes SEA-6 and SEA-11 keep apart:
a chain found, a space exhausted without one, and a budget that ran out. Only
the middle one says anything about what does not exist, and only about the
space this search covers.

The run costs about 1.5 maps per second, against 6 for the fifteen-dimensional
recovery, so it belongs on a machine rather than in a session.

If a chain is found, it becomes a `Reduction` in `tests/test_alpoege19.py`, the
transported collision replaces the `lift` reconstruction as the primary route to
the three points, and `scripts/reconstruct_alpoege19.py` carries the recovered
sequence in plain SymPy as the independent second computation, joining the gates
in `Makefile` and `AGENTS.md`.

If none is found, WP 10 records what was searched and what was ruled out, and the
milestone ships the search without the result. SEA-6 exists so that this outcome
can be reported without being overstated. It would not be a successful milestone,
and it would not be a false one either.

One thing the run cannot tell us by failing: whether `w2` is the only carrier a
later step rewrote. If another was, its introduced value is missing from the
pool and the chain is inexpressible rather than unfound — the same failure
`alpoege15` shows when its own missing value is withheld, and it looks identical
from outside.

**WP 11** removes the `[0.4]` markers from `contracts.md`, adds the translation
and the search to `architecture.md`, records the provenance of the recovered
sequence in `references.md`, updates `CHANGELOG.md`, and sets the version.

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

## Selection heuristics and scientific benchmarks

Search without a known target. 0.4 searches between two fixed endpoints, which
is what makes its result checkable; here the endpoint is not given, and a
sequence has to be chosen rather than recovered.

Candidate enumeration is already 0.4's, under SEA and WP 4 of that milestone.
What is added:

- ranking heuristics,
- pruning,
- term-growth prediction,
- dimension-growth tracking,
- duplicated carrier values as a cheap first criterion, since they are readable
  straight off the components and were what produced `alpoege15`.

Benchmark against published reductions of the current reference examples.
Reproducing known dimensions with machine-verifiable certificates is the first
correctness target. Improving them is a secondary scientific goal.

This milestone targets research results rather than user-interface features.

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
