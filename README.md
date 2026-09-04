# KellerMap

A Python library for polynomial Keller maps — polynomial endomorphisms with a
nonzero constant Jacobian determinant — and for certified transformations of
them.

Whether every Keller map is an automorphism was the Jacobian conjecture, posed
by Ott-Heinrich Keller in 1939 — or, on a recent reading of the sources, by
Ludwig Kraus in 1884; see `docs/references.md`. It stood until July 2026 and is
now known to be false in every dimension `n >= 3`. The maps this library is
built to handle are therefore precisely those that need not be invertible,
which is why it is named after them rather than after automorphisms.

There is a local coincidence in that name. Keller held the second chair of
mathematics at the Martin-Luther-Universität Halle-Wittenberg from 1951 until
his emeritation in 1971, succeeding Heinrich W. E. Jung, and he lectured there
into the 1980s — the present-day academic home of this project. Sources differ
on the year; `docs/references.md` says which and why.

The first goal is the degree reduction introduced by

> H. Bass, E. H. Connell, D. Wright,
> *The Jacobian Conjecture: Reduction of Degree and Formal Expansion of the Inverse*,
> Bull. Amer. Math. Soc., 1982.

The implementation is intended as both

- a research tool for experiments related to the Jacobian Conjecture,
- and a faithful software implementation of the original mathematical proof.

Unlike a simple symbolic manipulation package, every reduction step is
represented explicitly as a mathematical object and carries its own
machine-checkable certificate.

---

## Project Status

Current version: **0.6.0rc6**

### What the library does

- **Polynomial maps** over a sparse `PolyRing`, with value semantics:
  composition, extension, reordering, Jacobian matrices and determinants.
- **Elementary and linear automorphisms**, `EA_n(k)` and `GL_n(k)`, the latter
  as an ordered product of Gauss operations.
- **Certified steps.** `BCWStep` is one application of Bass–Connell–Wright,
  Proposition (3.1), that verifies rather than asserts: it keeps the
  factorization it was given and checks it, and a failure names the obligation
  it broke. `LinearStep` and `TranslationStep` are the two factors of the
  linear normalization.
- **The second and third stages of the Reduction Theorem.** `UnipotentStep` is
  Section 4's second step, which doubles the dimension and makes the Jacobian
  of the displacement nilpotent; `HomogenizationStep` is the third, which adds
  one variable and makes the displacement cubic homogeneous. Not the whole of
  Theorem 2.1: the normal form there is also linear in each original variable,
  and that refinement is not implemented.
- **Compression and the gradient form.** `CompressionStep` restricts a
  homogeneous map to the subspace its collision generates, which is the one
  step that *lowers* the dimension; `SymmetricLiftStep` turns the result into
  the gradient of a quartic over `k(i)`, which is the object Zhao's Vanishing
  Conjecture is about.
- **Chains.** `Reduction` joins steps and checks the adjacency;
  `ReductionContext` checks that a naming policy stays consistent along one.
- **Collisions.** `Collision` is the evidence that a map is not injective, and
  it is transported across every step, so a reduction of a counterexample is
  still a counterexample. Two of the seven step types may refuse a collision
  rather than carry it, and say why.
- **Three searches.** `search` walks from a source towards a target and is told
  what a fresh coordinate may carry; `peel` walks back from a target and is
  told nothing else; `reduce_to_degree3` is given a source alone and reduces it
  to degree three.
- **Example maps** that recur, including four maps this project did not write
  and the reductions it derived from them.
- **Obligations, not conventions.** Every promise the verification surface
  makes is written in `docs/contracts.md` under a stable identifier, and the
  exception that fails cites it.

### This milestone, 0.6

The second and third stages of the Reduction Theorem, and the two constructions
that carry the result to the form the literature compares. Everything before
this milestone stopped at degree three, which is BCW's first stage; the
published figures are cubic homogeneous, which is the third, so the two could
not be set beside each other.

The whole pipeline, from the smallest degree-three map this project holds:

| | | |
| --- | ---: | --- |
| `examples.spacerat11` | 11 | degree three |
| `UnipotentStep` | 22 | Jacobian of the displacement nilpotent |
| `HomogenizationStep` | 23 | cubic homogeneous |
| `CompressionStep` | 19 | restricted to the collision hull |
| `SymmetricLiftStep` | 38 | the gradient of a quartic over `Q(i)` |

Every step verifies and the collision arrives at the far end.
`scripts/measure_pipeline.py` recomputes the table, and does the same for the
two larger maps.

Those are the smallest figures published at either stage, and they were
published elsewhere first, by a different route and a month earlier. What that
does and does not establish is in `docs/references.md`: the pipeline composes
published constructions, it claims no minimality and no priority, and the forms
it produces are denser than the published ones. `docs/errata.md` records that
this project claimed otherwise for a week.

### Next, 0.7

Performance, and two questions this milestone raised without answering: why the
chains `peel` finds are not chains the untargeted search offers, and whether
the dimension at degree three is the right thing for a search to minimize now
that the number after four more stages can be computed.

`docs/roadmap.md` carries the plan and the measurements behind it.
`CHANGELOG.md` lists what each release changed, and the milestones before this
one are there rather than here.

---

## Installation

```
pip install kellermap
```

Requires Python 3.10 or newer and SymPy 1.14 or newer.

## Quick start

```python
import sympy as sp
from kellermap import PolynomialMap

x, y = sp.symbols("x y")
F = PolynomialMap((x, y), (x + y**3, y))

F.determinant()  # 1 — a Keller map
F.degree()  # 3
F.filtration_degree()  # 2, from ord(F - X) = 3
F.extend(2).variables  # (x, y, X3, X4)
```

The first two steps of the reduction that this library exists for — Alpöge's
counterexample to the Jacobian conjecture, on its way down to degree three:

```python
import sympy as sp
from kellermap import Collision, PolynomialMap, Reduction, ReductionContext
from kellermap import over_field
from kellermap.bcw import BCWStep, Fresh
from kellermap.reduction import LinearStep

x1, x2, x3 = sp.symbols("x1 x2 x3")
R = sp.Rational

alpoege = over_field(
    PolynomialMap(
        (x1, x2, x3),
        (
            (1 + x1 * x2) ** 3 * x3 + x2**2 * (1 + x1 * x2) * (4 + 3 * x1 * x2),
            x2 + 3 * x1 * (1 + x1 * x2) ** 2 * x3 + 3 * x1 * x2**2 * (4 + 3 * x1 * x2),
            2 * x1 - 3 * x1**2 * x2 - x1**3 * x3,
        ),
    )
)
collision = Collision.at(
    alpoege,
    (
        (0, 0, R(-1, 4)),
        (1, R(-3, 2), R(13, 2)),
        (-1, R(3, 2), R(13, 2)),
    ),
)

normalization = LinearStep.normalize(alpoege)  # F_(1)^-1 o F, BCW II (1.1)
u, v = ReductionContext().variables(normalization.target.ring, 2)
first = BCWStep.build(  # Proposition (3.1): two new dimensions
    normalization.target,
    0,
    Fresh(-x1 * x3 / 2, u),
    Fresh(x1**2, v),
)
reduction = Reduction([normalization, first])

reduction.verify()  # None, or VerificationError naming the obligation that failed
reduction.dimensions()  # (3, 3, 5)
reduction.transport(collision).points[1]  # (1, -3/2, 13/2, 13/4, -1)
```

The counterexample is still a counterexample at the other end, and the chain
says so by carrying it rather than by asserting it.

`docs/api.md` covers the rest; every example in it is executed by the test
suite, as are both blocks above.

---

## How this project is built

The code in this repository is written in collaboration with a large language
model, Anthropic's Claude. `AGENTS.md` at the repository root holds the working
agreements: how a change is delivered, what a certificate is for, how claims
and sources are handled, and where the assistant is expected to push back
rather than comply. It is the same file the assistant works from.

The maintainer takes responsibility for everything here, whoever or whatever
produced a first draft of it. Each milestone since 0.2 has gone through
external audits before release, and every finding is recorded.

This is worth one distinction, because the two halves of the repository carry
different kinds of assurance.

The mathematics is machine-checkable and is checked. A reduction is a chain of
certified steps, each obligation has a number in `docs/contracts.md`, and the
exception that fails cites it. The reduction of the published
nineteen-dimensional map exists three times over by routes that share no code:
as a chain of verified steps, as an independent computation in plain SymPy, and
as a search result. `scripts/mutation_probe.py` breaks one promise at a time to
ask whether the suite would notice. None of that asks anyone to trust the
producer, which is the point of building it that way.

The prose is not machine-checkable in the same sense. Page numbers, licences
and statements about the literature rest on somebody having opened the source.
Two errors of that kind were made during 0.4 and both were found by reading a
scan page by page: a citation of the filtration `MA_n^d(k)` gave p. 304 where
it is p. 303, and the licence of arXiv:2608.00222 was recorded as
undeterminable when the listing states it. `docs/references.md` records what
each claim rests on, and `tests/test_documentation.py` checks what the prose
says about the code, which is the part of it that can be checked.

If you want to contribute, `CONTRIBUTING.md` says how, including what is
expected of AI-assisted contributions.

---

## Documentation

The documentation is located in

```
docs/
```

Most important documents:

```
api.md            public API, with examples the test suite executes
architecture.md   design decisions and the reasons for them
contracts.md      binding obligations of the verification surface
references.md     sources, and the comparisons with published figures
provenance.md     where the fixed data came from, and how this repository
                  was written
errata.md         what this project reported wrongly, and the correction
deposit.md        what goes into the Zenodo record, and why not the
                  automatic route
roadmap.md        milestones
```

`CHANGELOG.md` and `CITATION.cff` sit at the repository root.

---

## License

MIT License
