# Roadmap

The project follows an incremental development strategy. Every milestone should
leave the repository in a fully functional, typed, formatted, and tested state.

---

# Version 0.1

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

### Performance baseline

Create a benchmark suite comparing the former `Expr` implementation with the
new PolyRing implementation.

Measure

- construction,
- composition,
- Jacobian construction,
- determinant computation,
- degree and order,
- stable extension.

Use the cubic Keller map in 19 variables from
`https://rhicksrad.github.io/jacobian-degree3/` as the first large reference
case. Benchmarks must record runtime, peak memory where practical, SymPy
version, Python version, and hardware information.

### ElementaryAutomorphism

Implement only after the PolyRing migration and benchmark baseline are stable.
It must operate in an existing ring and avoid expression conversions inside
reduction loops.

### Quality

- complete unit tests
- mypy strict mode
- ruff
- black
- API documentation
- migration notes from the expression implementation

---

# Version 0.2

## Verification framework

Introduce

- `BCWStep`
- `Reduction`
- `VariableFactory` or `ReductionContext`

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
- sparse determinant strategy selection,
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
