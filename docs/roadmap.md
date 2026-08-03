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
scalings belong to the linear part that Section 4 handles separately, and if
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

## Verification framework

Introduce, at the top level,

- `Collision` and `VerificationError`
- `kellermap.linear`: dilations, transpositions, `LinearAutomorphism`
- `kellermap.reduction`: the `Step` protocol, `LinearStep`, `Reduction`

and, in the `kellermap.bcw` subpackage,

- `BCWStep`
- `ReductionContext` (building on the `VariableFactory` from 0.1)

Only `BCWStep` is specific to the paper. A chain of certified identities is
not, and a second reduction method would reuse it, so `Reduction` stays at the
top level rather than becoming the misnomer the subpackage exists to avoid.
`LinearStep` composes an element of `GL_n(k)` on the left; that Section 4 opens
by doing so does not make the operation theirs.

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

The derivation begins with the normalization of BCW §4, `F'' = F'_(1)^-1 ∘ F'`.
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
is a release. `pyproject.toml` stays at `0.1.0` until the milestone is complete
and is then set to `0.2.0` in one step. Git tags for work packages use the
`wp/` prefix, so that the release namespace `v*` stays clean.

| WP | Internal | Content |
| --- | --- | --- |
| 1 | 0.1.1 | `Collision` |
| 2 | 0.1.2 | `kellermap.linear`: dilations, transpositions, `LinearAutomorphism` |
| 3 | 0.1.3 | `kellermap.reduction`: `Step`, `LinearStep`, `Reduction` |
| 4 | 0.1.4 | `BCWStep.verify()` |
| 5 | 0.1.5 | `ReductionContext` |
| 6 | 0.1.6 | Integration: the eight steps from Alpöge to dimension 17 |
| 7 | 0.1.7 | Documentation and release |

Every work package leaves the repository green.

The order is not arbitrary. `Collision` and `kellermap.linear` depend on
nothing and settle the evaluation path early. `LinearStep` implements the
`Step` protocol before `BCWStep` does, so that the protocol is not shaped
around Proposition (3.1) alone. `ReductionContext` comes after `BCWStep`,
because only then is it known what the context has to guarantee — which is the
placement 0.1 already anticipated.

### Milestone target

At the end of 0.2 the seventeen-dimensional map in `tests/test_bcw17.py` is
derived rather than asserted: a `Reduction` of eight steps from Alpöge's map,
verified step by step, transporting the three-point collision. The map then
stops being a regression candidate. `scripts/reconstruct_bcw17.py` holds the
factorization this has to reproduce.

---

# Version 0.3

## BCW reduction

Implement

- degree reduction,
- elementary transformations,
- stable extension,
- homogenization and unipotent reduction,
- complete reduction pipeline.

Goal:

Produce fully verified reductions for examples from the literature without
recomputing global invariants that follow from the certified local steps.

---

# Version 0.4

## Selection heuristics and scientific benchmarks

Develop heuristics for choosing reduction steps.

Tasks:

- candidate generation,
- ranking heuristics,
- search strategies,
- pruning,
- term-growth prediction,
- dimension-growth tracking.

Benchmark against published reductions of the current reference examples.
Reproducing known dimensions with machine-verifiable certificates is the first
correctness target. Improving them is a secondary scientific goal.

This milestone targets research results rather than user-interface features.

---

# Version 0.5

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

# Version 0.6

## Complete verification and benchmark framework

- large-scale regression tests,
- reproducible benchmark runner,
- machine-readable benchmark results,
- performance comparisons across releases,
- verified reduction certificates for large examples,
- independent certificate replay.

---

# Version 0.7

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
