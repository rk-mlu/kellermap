# References

Sources this project builds on, and where the fixed data in the test suite
comes from.

Status note: the counterexample below has been checked publicly by many people
and reconstructed geometrically, but as of this writing it has not completed
journal peer review. This file records what is publicly documented, not a
verdict on it.

---

## The reduction

**Bass, H., Connell, E. H., Wright, D.** *The Jacobian conjecture: reduction of
degree and formal expansion of the inverse.* Bulletin of the American
Mathematical Society (New Series) **7** (1982), no. 2, 287–330.

- Project Euclid: <https://projecteuclid.org/euclid.bams/1183549636>
- DOI: <https://doi.org/10.1090/S0273-0979-1982-15032-7>

The paper this library implements. References in the source and tests give page
numbers from it:

| Cited as | Content |
| --- | --- |
| p. 304 | `MA_n(k)`, `EA_n(k)`, the filtration by `ord(F - X)`, stable extension |
| Proposition (3.1) | degree reduction to 3 by stabilization and two elementary automorphisms |
| Chapter II, Proposition (1.1), p. 303 | `F = (X + F(0)) o F_(1) o F'` with `F' in MA^1`: translation, then linear normalization |
| Chapter II, §4, p. 306 | proof of the Reduction Theorem; homogenization over `k[T]` |

---

## The counterexample

**Alpöge, L.** Announcement of an explicit counterexample to the Jacobian
conjecture. X, 20 July 2026.
<https://x.com/__alpoge__/status/2079028340955197566>

The map in `tests/test_polynomial_map.py` and the normalization input of
`examples.bcw17()` are this map:

    F(x, y, z) = ( (1+xy)^3 z + y^2 (1+xy) (4+3xy),
                   y + 3x (1+xy)^2 z + 3x y^2 (4+3xy),
                   2x - 3x^2 y - x^3 z )

with `det J(F) = -2` identically, and the three collision points

    (0, 0, -1/4),  (1, -3/2, 13/2),  (-1, 3/2, 13/2)

all mapping to `(-1/4, 0, 0)`. Degree 7, dimension 3. The test suite recomputes
the determinant and all three images rather than asserting them from the source.

Akhil Mathew suggested the problem; the announcement credits Anthropic's Claude
Fable 5 with finding the map. The conjecture is thereby false for every
dimension `n >= 3` — append identity coordinates — while `n = 2` remains open.

### Secondary accounts

- **Tao, T.** *A digestion of the Jacobian conjecture counterexample.* 21 July
  2026.
  <https://terrytao.wordpress.com/2026/07/21/a-digestion-of-the-jacobian-conjecture-counterexample/>
  A geometric reconstruction of how the map arises.
- **Buzzard, K.** *Human mathematicians are being outcounterexampled.* Xena
  Project, 20 July 2026.
  <https://xenaproject.wordpress.com/2026/07/20/human-mathematicians-are-being-outcounterexampled/>
  Records the provenance and a Lean formalization by Paul Lezeau.
- **Secret Blogging Seminar.** *The new counterexample to the Jacobian
  conjecture.* 20 July 2026.
  <https://sbseminar.wordpress.com/2026/07/20/the-new-counterexample-to-the-jacobian-conjecture/>
- **Wolfram MathWorld.** *Jacobian Conjecture.*
  <https://mathworld.wolfram.com/JacobianConjecture.html>
- **Archive of Formal Proofs.** *Jacobian_Counterexample.*
  <https://isa-afp.org/entries/Jacobian_Counterexample.html>
  An independent machine-checked verification of the three-dimensional map in
  Isabelle/HOL. It covers the published counterexample, not the
  seventeen-dimensional reduction of it used here.

### Historical note

**Rodríguez Díaz, L. O.** *On the Origin of the Jacobian Conjecture.* Comptes
Rendus Mathématique **364** (2026), 363–370.
<https://doi.org/10.5802/crmath.831>

The conjecture is conventionally attributed to Keller (*Ganze Cremona
Transformationen*, Monatshefte für Mathematik und Physik **47** (1939),
299–306). This study traces the statement to Ludwig Kraus in 1884 and finds a
gap in his attempted proof — so "87-year-old problem" understates it.

**Keller, Eduard Ott-Heinrich** (1906–1990). Doctorate under Max Dehn in
Frankfurt, 1929; habilitation on Cremona transformations under Georg Hamel at
the TH Berlin, 1933 — the thread that leads to the 1939 paper. Professor in
Dresden from 1947, then holder of the second chair of mathematics at the
Martin-Luther-Universität Halle-Wittenberg from 1951, succeeding Heinrich W. E.
Jung, until his emeritation in 1971; he continued to lecture there into the
1980s and died in Halle.

- MacTutor: <https://mathshistory.st-andrews.ac.uk/Biographies/Keller/>
- Catalogus Professorum Halensis:
  <https://www.catalogus-professorum-halensis.de/keller-ott-heinrich.html>
- Chair succession at Halle:
  <https://disk.mathematik.uni-halle.de/history/allgemein/prof_hal_wb_45_69.html>

Sources differ on the year of the Halle appointment, and they differ within
Halle. The university archive's Catalogus Professorum states that Keller was
appointed on 1 November 1951, citing his personnel file, and that he held a
second appointment from 1 September 1969 until his emeritation in 1971.
MacTutor also gives 1951. The chair succession page of the mathematics
institute lists 1952–1971, as do the German Wikipedia and the anniversary
article in *Beiträge zur Algebra und Geometrie*.

The text above follows the archive, since it gives a precise date and names the
file it rests on. Nothing in this project depends on the year.

---

## Related cubic Keller-map benchmarks

Useful as comparison and as benchmark targets for milestone 0.5. Note that
these are *different* reductions, not alternative descriptions of
`examples.bcw17()`.

| Source | Dimension | Shape | Determinant | In the suite |
| --- | --- | --- | --- | --- |
| this project, `examples.alpoege15()` (derived) | 15 | degree 3 | 1 | yes |
| this project, `examples.bcw17()` (derived) | 17 | degree 3 | 1 | yes |
| <https://rhicksrad.github.io/jacobian-degree3/> | 19 | degree 3 | −2 | yes* |
| <https://github.com/wtho704/explicit-cubic-homogeneous-jacobian-counterexample> | 24 | cubic homogeneous | 1 | no |

\* The nineteen-dimensional map is in the suite from a checkout and not from
the source archive, which excludes `tests/data.py`: it is somebody else's
mathematics and its licence could not be established. Without the file the
tests that need it skip themselves and say why.

The two rows belonging to this project carry different standing, and the label
in the first column says which. The seventeen-dimensional map is *derived*
since version 0.2: the suite verifies a chain of eight steps from Alpöge's map
to it — the linear normalization and seven `BCWStep` — and transports the
collision along; the provenance section below says what in that is evidence and
what is a self-check. The fifteen-dimensional one is *derived* since 0.3, when
steps that reuse a carrier became expressible. What that does and does not
establish differs from the case above, and the section on it below says how.

Both maps moved into `kellermap.examples` in 0.4, which changes where they are
written and not who computed them.

The rows are not directly comparable. BCW reduce in two stages, first to
degree 3 and then to cubic homogeneous form; the 24-variable map has completed
both, the others only the first. A conservative Bass–Connell–Wright route on
the same source is reported at 79 variables. The dimension-19 map keeps the
determinant −2, so it has not been linearly normalized.

Comparing them meaningfully needs certificates, which 0.2 introduced.
Reproducing the dimension-19 map's own step sequence was the target of 0.4 and
is done: the suite holds it as a verified `Reduction`, `peel` finds a second
valid chain of seventeen steps in eighteen examined maps, and "The chain to the
nineteen-dimensional map" below records how and by whom. Reproducing published
dimensions more generally is the first target of 0.5, and improving them is
secondary.

### Where the counts come from

The published counts follow the same elementary step and differ in how it is
applied.

**Campbell, L. A.**, *Reduction theorems for the strong real Jacobian
conjecture*, arXiv:1303.3853, Theorem 5, Step 1. States the step in the form
used here: `F` is stably equivalent to `(f_1 - (y + a)(z + b), f_2, …, f_n,
y + a, z + b)`, removing a term `ab` of a component at the cost of two new
variables. No reuse of an earlier variable.

**Long, C. D.**, *Small counterexamples to the Gaussian Moments Conjecture*,
arXiv:2607.18186, Proposition 2.1. Tracks the same reduction for the same
source map. With `c(d)` the number of degree-lowering steps for one monomial of
degree `d`, the recursion `c(d) ≤ 1 + c(p+1) + c(q+1) + c(p) + c(q)` gives
`c(4) = 1`, `c(5) ≤ 2`, `c(6) ≤ 3`, `c(7) ≤ 5`, and the support of the
normalized map needs at most 18 steps, hence `3 + 2·18 = 39` variables at
degree 3. The author calls the resulting figure a transparent upper bound and
not an optimization.

Set beside each other, at the same degree-≤3 stage:

| route | variables |
| --- | --- |
| tracked bound, one step per monomial | 39 |
| published explicit reduction | 19 |
| this project, without reusing carriers | 17 |
| this project, reusing two carriers | 15 |

The steps down from 39 to 17 come from choosing the factorization better —
`P · Q` may be any subsum of the target component, so one step can remove
several monomials. The step from 17 to 15 comes from reusing a carrier.

### Is reusing a carrier known?

We looked for prior art and did not find it in this literature. Campbell states
the step with two new variables. Long counts two per step. The Bass–Connell–
Wright proof itself introduces a variable for each of `P` and `Q`. None of them
discusses reusing a variable an earlier step introduced.

The underlying idea is not new elsewhere. Computing a polynomial by naming
intermediate results and using each name more than once is what a straight-line
program or an arithmetic circuit does, and eliminating repeated subexpressions
is standard practice in computer algebra. A carrier is the algebraic-geometry
form of such a name: `X_j + P` records `P` in a coordinate, and the reduction
is then a circuit for the map written as a stable extension. In that reading,
the number of variables a reduction needs measures the size of a circuit for
`F`, not the number of its monomials.

We make no claim of novelty. The absence of a reference here says only that a
serious search did not turn one up; the technique is simple enough that it may
well be folklore, and someone who knows the literature better may recognise it
at once. If a source is found, it belongs in this section.

### `alpoege15`

Not an external source: this project's own reduction of Alpöge's map, obtained
by letting two steps of the seventeen-dimensional chain share carrier variables
that earlier steps had already bought — `x1²` and `x1x2`, each of which BCW17
buys twice. Degree 3, Jacobian determinant 1, the same three-point collision,
with the first thirteen coordinates of each point identical to BCW17's.

It is held in `kellermap.examples`, with the chain in
`tests/test_alpoege15.py` and a second and independent rendering of it in
`scripts/reconstruct_alpoege15.py`, as
`reconstruct_bcw17.py` does for the seventeen-dimensional map.

Since 0.3 the suite derives it: a `Reduction` of eight steps, two of which
reuse a carrier and therefore introduce one generator instead of two. The last
step is given the fixed components as its target, so BCW-1 compares them
against `G ∘ F^[m] ∘ H`.

Those components are not output of this library. They come from
`scripts/reconstruct_alpoege15.py`, which uses SymPy alone, and its commit
predates the point at which `kellermap` could express the chain at all. In
that sense the target is supplied here exactly as it is for the
seventeen-dimensional map.

The difference from that case is what the agreement is evidence for, not
whether the check can fail. Here the other side is this project's own second
implementation, so the agreement says that two implementations of the same
formulas compute the same thing.

That sentence used to continue: for the seventeen-dimensional map the other
side is someone else's mathematics. **It was wrong, and is withdrawn in 0.4.**
The components of the seventeen-dimensional map are the maintainer's own hand
computation, checked against `scripts/reconstruct_bcw17.py`. They are external
to the *library* — the point BCW-9 and RED-7 are about — and not external to
the *project*. `AGENTS.md` asks for exactly that distinction and the sentence
collapsed it.

What follows from the correction is worth stating plainly, because it changes
what this repository could claim before 0.4. Two things in it are somebody
else's mathematics: Alpöge's three-dimensional map, which every chain starts
from, and the nineteen-dimensional map. Everything else is the project's own,
including both endpoints that the `bcw17` and `alpoege15` chains are held
against. So until the search reaches the nineteen-dimensional map, the only
external datum a chain is compared against is its *source*, and the endpoint
comparison — the one the last step's BCW-1 performs — is against data this
project produced by hand. That is a real check and it can fail; it is not
agreement with a third party, and this page said it was.

No claim of minimality attaches to it, following the practice of the sources
above — the author of the 24-variable map states plainly that he claims neither
priority nor global minimality. Whether something smaller has appeared should
be rechecked before the number is used outside this repository.

### The dimension-19 map

Retrieved 3 August 2026 from <https://rhicksrad.github.io/jacobian-degree3/>,
a research note posted by the GitHub user *rhicksrad* and dated 20 July 2026.
It is held in `tests/data.py`, which the source archive does not carry; see
below.

The note carries no authority here, and says as much about itself: it is
self-published, was worked out with an LLM, and states that it inherits the
under-review status of the announcement it builds on, which at the time was one
day old. What makes the data usable is that the test suite recomputes it.
Established there, from the components alone:

- dimension 19, degree 3, Jacobian determinant identically −2;
- the map lies in `MA^0` and not in `MA^1`, and its linear part is Alpöge's
  own bordered by the identity — so it has *not* been linearly normalized,
  which is the structural difference from the 17-dimensional map;
- three distinct points sharing one image, that image being Alpöge's
  `(-1/4, 0, 0)` padded with zeros, and the points extending Alpöge's in their
  first three coordinates.

The collision points are not taken from the note's table. The carrier
components have the form `w_j + P_j`, so a preimage satisfies `w_j = -P_j`; the
suite solves that system, whose termination it checks rather than assumes, and
compares the result with the published table afterwards. The two routes are
independent and agree.

The components in `tests/data.py` were transcribed from the note's
rendered text, which loses exponents — `w32` is `w3^2`. On 3 August 2026 the
transcription was checked against the machine-readable
[degree3_map.json](https://rhicksrad.github.io/jacobian-degree3/degree3_map.json)
the note links: all nineteen components agree as polynomials, as do the
variable order and all three points in all nineteen coordinates. That file is
deliberately *not* vendored here. Its coefficients are already held in the
test, in this repository's own idiom, so a second copy in the source's format
would add no check that is not closed-loop — it would compare the test against
a copy rather than against the source — while adding a third-party file of
unclear licence.

Its reduction reuses carriers. The note describes seventeen elementary steps
with sixteen carrier variables, so not two per step, and the carriers `x^2`,
`xy`, `y^2`, `yz`, `xz`, `x^2 y`, `xy^2`, `y^2 z` are building blocks used by
more than one step. Since 0.3 a `BCWStep` can express such a step.

What the note does not publish is the sequence. It gives the map but not its
factorization, so the factorization cannot be read off the way BCW17's can.
Reconstructing it was the work of 0.4, and "The chain to the
nineteen-dimensional map" below records how it was done and by whom.

This paragraph used to add that the `w`-numbering is not the order of
introduction, on the evidence that the component of `w2` reads `w9` and `w13`.
That is withdrawn in 0.4: the component of `w2` is the residue of a later step
and not an introduced value, so it says nothing about when `w2` arrived. With
the introduced value in its place, every dependency points to a smaller index.
`tests/data.py` holds the values and `tests/test_alpoege19.py` records both.

The note arrives independently at the Schur-complement route this library uses
for the determinant. On this map the difference is not a nicety: the carrier
block reduces the 19×19 determinant to a 3×3 one in a fraction of a second,
while `sp.Matrix(F.jacobian()).det()` did not finish in a quarter of an hour.

---

## Provenance of the fixed test data

`examples.bcw17()` returns a 17-dimensional map whose components this
library did not produce. Since version 0.2 the suite derives it: a `Reduction`
of eight steps from Alpöge's map — the linear normalization of Chapter II,
Proposition (1.1), then seven
applications of Proposition (3.1) — verified step by step, carrying the
three-point collision from `k^3` to `k^17`.

What in that is evidence, and what is a self-check:

- The intermediate maps in dimensions 5 to 15 are published nowhere. They
  therefore *cannot* be supplied, and their steps are `CONSTRUCTED`: BCW-1
  compares the implementation against itself there. By RED-7 the whole chain
  carries the weaker provenance.
- The external fact is the endpoint. The last step is given the fixed
  components as its target, so its BCW-1 compares an externally computed map
  against `G ∘ F^[2] ∘ H` and can fail — a test perturbs one component to show
  that it does. The transported collision is likewise held against the fixed
  one, and the fresh variable names come from a `ReductionContext` rather than
  from the table, so a different naming would fail the last step too.
- The factorization is not searched for. It was read off the fixed components,
  whose entries 4 to 17 have the form `X_j + P`; those `P` are the factors.
  Searching is 0.4.

`scripts/reconstruct_bcw17.py` carries the same chain in plain SymPy, without
this library. The duplication is deliberate: two independent implementations of
formula (1) agreeing on all seventeen components and all three collision points
says more than one implementation checked against itself.

Recomputed independently of the chain, as cross-checks rather than as part of
the certificate: degree 3, determinant 1, the unipotent carrier block, and the
three images.

### The chain to the nineteen-dimensional map

Reconstructed by an external audit of this project in August 2026, and verified
here before it was written down. What that verification consisted of, and what
it is worth:

- `scripts/reconstruct_alpoege19.py` applies the step formula in plain SymPy,
  without this library, and checks the seventeen step identities, the
  dimensions, the degrees, the nineteen components and the fifty-seven
  coordinates of the three transported points.
- `tests/test_alpoege19.py` builds the same chain with `BCWStep`, verifies it
  under BCW-1 to BCW-12, and compares the endpoint with the published map and
  the transported collision with the published points.
- A negative control changes one coefficient. The chain still builds and still
  verifies; it arrives somewhere else. That is what makes the endpoint the
  evidence rather than `verify()`.

The audit is a source and not an authority, the same way the published map is.
Nothing here rests on its having been right; what it did was hand this project
a chain to check, and the checking is recorded above.

The chain needs three things that Chapter II, Proposition (3.1) does not have,
and all three are marked as extensions in `contracts.md`: a factor taken from a
coordinate an earlier step introduced (BCW-10, in the library since 0.3), a
coefficient on the removed product (BCW-11), and a step whose two slots name one
fresh coordinate (BCW-12). The coefficients cannot be moved into a change of
coordinates: the diagonal that would absorb them needs `1/7` at step seven where
the earlier steps force `1/9`, and `1` at step nine where they force `1/2`.

The search finds a chain too, and this paragraph said the opposite until an
external audit of `0.4.0rc1` showed why. `scripts/search_alpoege19.py` built its
source with `over_field`, over `QQ`, while the published map is over `ZZ`;
`PolynomialMap` counts the coefficient domain as part of its identity and every
step preserves it, so the search could not have arrived however long it ran.
Over `ZZ` the peel reaches the published map in **eighteen examined maps**.

What it finds is not the audited chain but another of seventeen steps, with the
coordinates introduced in a different order. Both are chains and neither is
*the* chain, which is what "No optimality of the sequence" has said since the
first milestone.

So two things may be claimed and one may not. The factorization is certified
here, and it is also reachable by this library's own search. That the search
would have found it without the audit is *not* claimed: the audit came first,
and the ordering of events is a fact about this project rather than about the
mathematics.

The order the coordinates were introduced in is

    w1, w2, w4, w5, w8, w7, w9, w13, w16, w15, w14, w6, w12, w3, w11, w10,

which is not the numbering of the published map. That numbering is a valid
topological order of the final carrier values and not a chronology; this page
said otherwise until the chain settled it, and the paragraph that did is left
standing in `roadmap.md`, withdrawn rather than deleted.
