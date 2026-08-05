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

**Status: complete, released as `0.3.0rc2`.** An external audit of `0.3.0rc1`
found no functional, algebraic or packaging blocker; rc2 carries its four text
corrections. The final version number is held back until the release chain has
run against this tree.

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
the duration and moved to `0.3.0rc1` at the end.

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
why it waits here rather than travelling with 0.3.

## BCW reduction

Implement

- degree reduction,
- elementary transformations,
- stable extension,
- homogenization and unipotent reduction,
- complete reduction pipeline.

Goal:

Produce fully verified reductions for examples from the literature without
recomputing global invariants that follow from the certified local steps. The
first target is the published 19-dimensional map, whose step sequence 0.3
leaves unrecovered.

---

# Version 0.5

## Selection heuristics and scientific benchmarks

Develop heuristics for choosing reduction steps.

Tasks:

- candidate generation,
- ranking heuristics,
- search strategies,
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

# Version 0.7

## Complete verification and benchmark framework

- large-scale regression tests,
- reproducible benchmark runner,
- machine-readable benchmark results,
- performance comparisons across releases,
- verified reduction certificates for large examples,
- independent certificate replay.

---

# Version 0.8

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
