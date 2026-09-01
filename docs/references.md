# References

Sources this project builds on, and what the figures in them mean beside this
project's own.

Two pages were split out of this one in work package 9 of milestone 0.6, when
it had grown to four subjects at once. `docs/provenance.md` says where each
fixed map came from, under what licence, and what an agreement with it is
evidence for. `docs/errata.md` says what this project reported wrongly and
corrected. This page states the position as it now stands.

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
| p. 302 | `MA_n(k)`, its monoid structure under composition and its grading |
| p. 303 | `MA_n^0(k)`, `MA_n^1(k)` and the filtration `MA_n^d(k)` by `ord(F - X)` |
| Chapter II, Proposition (1.1), p. 303 | `F = (X + F(0)) o F_(1) o F'` with `F' in MA^1`: translation, then linear normalization |
| p. 304 | elementary automorphisms, `EA_n(k)`, `EA_n^d(k)`, the stable extension `F -> F^[m]` |
| Proposition (3.1), p. 305 | degree reduction to 3 by stabilization and two elementary automorphisms |
| Chapter II, §4, p. 306 | proof of the Reduction Theorem; homogenization over `k[T]` |


---

## The counterexample

**Alpöge, L.** Announcement of an explicit counterexample to the Jacobian
conjecture. X, 20 July 2026.
<https://x.com/__alpoge__/status/2079028340955197566>

The post displays `4:19 · 20 July 2026` to a reader in Germany. X localizes a
timestamp to the reader, so that is 02:19 UTC if the reader's zone was CEST,
and the calendar date depends on where it is read. The date above is the one a
reader in central Europe sees. Nothing on this page rests on the time of day,
and the paragraph exists so that a later reader who sees a different date knows
why.

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

### A second family of counterexamples

Shuhong Gao, *Counterexamples to the Jacobian conjecture in dimensions greater
than two*, arXiv:2608.00222v1, 31 July 2026.

The paper gives a self-contained account of the tangent-sweep mechanism that
Speyer isolated in Alpöge's map, and generalizes it from plane curves to
direction fields on hypersurfaces, producing counterexamples in every dimension
above two and, in each dimension, of arbitrarily large geometric degree. Five
explicit maps are worked out. Its §3.5 gives a second three-dimensional one,
built on a rational quartic curve with two cusps and a node.

The paper carries an AI disclosure: the idea and framework are the author's,
and a language model assisted in the proofs and the writing. Recorded because
provenance is recorded, not because it changes what a verified identity is
worth.

That map, called `G` there, was checked here against the paper's own claims,
and the checks are worth listing because they are what a second source is for:

| Claim of Theorem 3.5 | Recomputed here |
| --- | --- |
| component degrees 4, 11, 12 | 4, 11, 12 |
| Jacobian determinant identically 2 | 2 |
| generic fiber of four points | a fiber of three exhibited, see below |

The fiber count itself was not recomputed. What was recomputed is a collision,
which is what makes the map a counterexample and what this project can check:
over the target `(0, 1, 1)` the three points

    (0, 1/2, -1/4),
    (±2√23·i/23, 1/6 ± 2√23·i/3, -253/6 ± √23·i/3)

are distinct and share their image. The paper's own sample point `(0, 1/2,
-1/4)` over `(0, 1, 1)` is the first of them.

Two properties matter for how this map could be used, and neither is a defect:

- Its coefficients include `3/8`, `9/4` and `43/2`, so it is over `QQ`, and its
  determinant is 2, so it is not normalized. Alpöge's map is over `ZZ` with
  determinant −2, and the two derived reductions are over `QQ` with determinant
  one. This is a third combination, and since a step preserves the coefficient
  domain it is a different search space again.
- The collision above is not rational: two of its three points live over
  `Q(√-23)`. Alpöge's collision is rational, and every `Collision` in this
  repository so far has been.

  This page said that carrying it would need the coefficient domain to be a
  number field. That was wrong, and it was written from an idea about how the
  code works rather than from trying it. A collision holds SymPy expressions
  and is evaluated as expressions, so its points may live over an extension
  while the map lies over `QQ`: COL-2 forbids a variable of the map, and an
  algebraic number is a constant. Work package 6 of 0.5 built the map from
  §3.5, put the three points into a `Collision` and transported them through a
  linear step, a BCW step and a two-step chain. All of it held on the tree as
  it stood.

  What did not hold was the normal form. `cancel` treats a radical as an atom,
  so two spellings of one algebraic number were reported as two points, which
  is COL-4 read backwards, and a correct image written as a nested radical was
  rejected, which is the false negative COL-3 warns about one class of number
  earlier. `kellermap.canonical` denests square roots since 0.5 and says what
  it does not claim. The points above are inside that class; a cube root would
  not be.

Gallagher's family, reference [12] of the same paper, contains an instance of
geometric degree four as well; the author states that the map above was
obtained independently.

Licensed CC BY 4.0, as the arXiv listing states. The map is in the repository
since work package 7 of 0.5, as `kellermap.examples.gao_quartic`, with its
collision beside it. The licence asks for three things, and all three are given
here and in the docstring of the map.

- **Attribution.** Shuhong Gao, *Counterexamples to the Jacobian conjecture in
  dimensions greater than two*, arXiv:2608.00222v1, Section 3.5.
- **Licence.** CC BY 4.0, <https://creativecommons.org/licenses/by/4.0/>.
- **Changes.** Yes. The map is transcribed into SymPy from the closed form the
  paper gives, and the two quotients are carried out rather than left standing.
  The collision is built from the three points the paper records, and its image
  is computed here rather than copied. Nothing about the mathematics is
  altered; the presentation is.

It is written as the paper writes it, from the closed form of `p`, `q` and
`gamma`, and the two divisions are the paper's own. That they come out exact is
its claim and this project's check: `PolynomialMap` refuses a component that is
not a polynomial, so a division that did not divide would fail at construction.

The name says geometric degree and not dimension. `bcw17` and `alpoege15` are
reductions and their dimension is what distinguishes them; this paper carries
two maps in three variables, the cuspidal cubic of §3.4 and the quartic here,
and the geometric degree is what tells them apart.

---

## Whose conjecture, and whose chair

Where the name comes from, which is not where the conjecture comes from. This
sits after the counterexample rather than at the end of the page because it
belongs to the same subject: what was refuted, by whom it was posed, and why
that is a longer story than the attribution suggests.

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

## What the pipeline reaches

Milestone 0.6 built the second and third stages of the Reduction Theorem, the
collision-hull compression and the symmetric lift. Running all four on every
degree-three map this project holds gives the table below.
`scripts/measure_pipeline.py` recomputes it, checks every step through the
library's verification surface, and fails if a figure here changes without the
script changing with it.

| from | unipotent | cubic homogeneous | compressed | gradient form |
| --- | ---: | ---: | ---: | ---: |
| `spacerat11`, 11 | 22 | 23, 60 monomials | 19, 56 | 38, `P` of 386 |
| `alpoege12`, 12 | 24 | 25, 60 monomials | 20, 55 | 40, `P` of 398 |
| `alpoege13`, 13 | 26 | 27, 73 monomials | 22, 68 | 44, `P` of 506 |

Every step is verified: the identity of each certificate, the determinant where
it is affordable, the homogeneity, and the collision carried through. The
exception is the determinant of the gradient form, which SYM-7 states as a
consequence and does not compute, for the reason measured under work package 7
of `docs/roadmap.md`.

### Against the published figures

Both numbers this pipeline reaches were published before it reached them, by
one source, and this page said otherwise for a week. `docs/errata.md` records
what it said.

**van Rijn, R.** *A twelve-variable degree-three Keller counterexample.*
`royvanrijn/jacobian-research`, commit of 30 July 2026.
<https://github.com/royvanrijn/jacobian-research>

That record derives a twelve-variable degree-three map from Macfarlane's `F13`
by what it calls a coordinate-pair restriction, and states three upper bounds
together: 12 at degree three, 19 cubic homogeneous, and 38 for the quartic
gradient form. It says of itself that it is an upper-bound theorem and not a
minimality or priority claim.

So 19 and 38 are its figures as well as this project's, by a different route
and a month earlier. What was new here is neither number.

The other figures at those stages are Thompson's 24 and Macfarlane's 20 for the
cubic homogeneous form; Prellberg's 40 for the quartic, from Thompson's 24 by
compressing first; and 48 from the same 24 by the de Bondt-van den Essen
construction applied directly, recorded in

**Santibáñez Leal, F.** *The consequence cascade of the Jacobian
counterexample, with an explicit dimension-48 witness against the Hessian
conjecture.* Zenodo, 23 July 2026. <https://zenodo.org/records/21504303>

which reports a quartic potential in 48 variables with 382 monomials over
`Q(i)` and a two-point collision, and which corrects the nilpotency index of
Thompson's map from 17 to 18. Nothing here rests on that index; this page has
never asserted it and the Prellberg reconstruction does not recompute it.

### What that does and does not establish

It establishes that composing published constructions reaches the smallest
figures anybody has published at those two stages, and that every step of the
composition carries a machine-checkable certificate. Two routes arriving at 19
and 38 independently is evidence about the numbers and not about either route.

What it does not establish is that anything here is first. It is not: those two
bounds were stated on 30 July 2026, and this project reached them on 30 August
by a chain of five constructions none of which is its own.

It establishes nothing about minimality. The number depends on the map the
pipeline starts from, and `spacerat11` is the smallest degree-three map this
project knows of rather than the smallest that exists. `docs/roadmap.md`
records the open question of whether the dimension at degree three is even the
right thing to minimize; three data points say it is monotone and three data
points are not a theorem.

It establishes no new mathematics. The eleven-variable map is Spacerat's, the
two stages are Bass, Connell and Wright's, the compression and the lift are
Prellberg's. What this project contributed is the composition and the
certificates. It once said it had also contributed the observation that nobody
had put these five pieces in a row; somebody had reached the same two numbers
by a different route a month earlier.

The density goes the other way and the table says so. Prellberg's `P` at 40
variables has 350 monomials; this project's at 38 has 386, and at 40 -- the
same dimension by a different route -- 398. Smaller in dimension is not smaller
in every sense, and which of the two matters depends on what a reader wants the
witness for.

---

## Collision-hull compression, and the fortieth variable

**Thomas Prellberg**, *Collision-Hull Compression for Homogeneous Keller Maps
and a Forty-Variable Counterexample to Zhao's Vanishing Conjecture*,
arXiv:2608.12543v1, 12 August 2026, School of Mathematical Sciences, Queen Mary
University of London. The submission is licensed CC BY 4.0,
<https://creativecommons.org/licenses/by/4.0/>, which covers the ancillary file
`anc/check_quartic_40.py` as part of it.

This is the most directly relevant reference this page carries after Alpöge's
own, and it settles two questions that stood open here.

### What it says

Theorem 3 gives compression as a canonical construction rather than a device.
For `F = id + h` Keller with `h` homogeneous of degree `d`, and a collision
`F(p) = F(q)` with `p != q`, let `T` be the symmetric `d`-linear polarization
of `h` and put

    W_0     = span{p, q}
    W_(v+1) = W_v + span{ T(w_1, ..., w_d) : w_j in W_v }.

The stable value `W` is the smallest linear subspace containing both points and
invariant under `h`. The restriction to it is again Keller, its Jacobian is
nilpotent, and the collision survives.

Theorem 1 and Proposition 6 apply that to Thompson's twenty-four-variable map.
The sequence of dimensions is `2, 4, 11, 20, 20`, and the subspace it generates
is exactly Macfarlane's twenty-dimensional invariant subspace. So the
twenty-four to twenty compression recorded above is not a fortunate choice of
four linear forms: it is what the collision itself generates.

Part 3 of Theorem 3 is the symmetric lift. Over `K = k(i)`,

    P_W(x, y) = i * sum_j y_j * hbar_j(x + i*y)

is homogeneous of degree `d + 1` with nilpotent Hessian, and `id - grad(P_W)`
is a noninjective Keller map, with the second point given explicitly by
`rho = (I + J hbar(q)^T)^(-1) (p - q)`. For `d = 3` the result is a
counterexample to the quartic case of Zhao's Vanishing Conjecture.

The paper claims no global minimality. Corollary 7 states a route-specific one:
forty is minimal among examples obtained by restricting Thompson's map to an
invariant subspace containing the collision and then applying the lift
unchanged.

### What was recomputed here

Recomputed by `scripts/reconstruct_prellberg40.py`, which make reconstruct runs,
in plain SymPy and without this library:

| | reported | recomputed |
| --- | --- | --- |
| `h` is cubic homogeneous | yes | agrees |
| `F(p) = F(q) = p`, `p != q` | yes | agrees |
| polarization dimensions | 2, 4, 11, 20, 20 | agrees |
| `P` homogeneous of degree 4 | yes | agrees |
| monomials of `P` | 350 | 350 |
| `id - grad(P)` has the stated collision | yes | agrees |
| Thompson's `H` is cubic homogeneous, four relations | yes | agrees |
| `H` restricted along the embedding is `h` | yes | agrees |

Not recomputed: the nilpotency index of `J h`, which costs matrix powers over a
polynomial ring, and the term count of `Delta(P^2)`. The ancillary file checks
both.


### What it means for this project

The compression is now a construction with a name, a proof and an algorithm,
where it was an open design question. It is also implementable in a few lines:
iterate the polarization on the span of the collision points until the
dimension stops growing.

It applies to homogeneous maps. Everything this project produces at degree
three is not homogeneous — the maps carry quadratic terms as well — so the
construction sits after the homogenization and not before it. That is the order
`docs/roadmap.md` had already chosen for 0.6, and this is the reason for it
rather than a preference.

Part 3 also writes out the step that has been recorded here as architecturally
absent: the symmetric lift over `Q(i)` is the de Bondt–van den Essen gradient
form, with the image of the collision given explicitly. The chain this project
follows — Jacobian Conjecture, BCW reduction, gradient form, Zhao's Vanishing
Conjecture — is closed end to end in one paper.

---

## alpoege13, the first chain a search found

Seven steps from Alpöge's normalized map into dimension 13, degree three,
determinant one, carrying the three points of Alpöge's collision. Found in work
package 11 of milestone 0.5 by a greedy walk over the widened offer of UNT-6 to
UNT-9, not by hand.

`scripts/reconstruct_alpoege13.py` recomputes it in plain SymPy without the
library, as the other three reconstructions do for their chains. It is the one
where that matters most: the other three write down a computation somebody did
by hand, and this one writes down a computation a program did.

The determinant is checked at three sample points rather than as a polynomial.
Thirteen variables over `QQ` are past what expression-level elimination
manages, and the technique the library uses to get past it is the
implementation the script exists to be independent of. A value other than one
falsifies the claim; agreement at three points does not prove it, and the
script says so.

### What it establishes

Three distinct preimages of one image, in dimension 13, at degree three. That
is against the eight steps into 15 of `alpoege15` and the eight into 17 of
`bcw17`.

### What it does not establish

Not minimality. The walk that found it takes the best single step at every map
and never looks sideways, and a search that spent dimension as a cost might do
better.

Not priority, and this is now settled rather than pending. The literature was
checked under work package 13 and thirteen variables at degree three were
reached a month earlier by A. Macfarlane; the section above says so. The number
appears in `README.md` and `CHANGELOG.md` with that sentence beside it. This
paragraph said the check was still outstanding until an audit of `0.5.0rc1`
read it after the check had been made.

The rule that produced it is measured on this map alone. The same rule did not
finish on Gao's in twenty-five minutes.

## Related counterexamples, by stage

BCW reduce in three stages, and a dimension means nothing without saying which
stage it is at. The tables are sorted by stage for that reason. Within a stage
the rows are comparable; across stages they are not, and the same map appears
at two stages if two of its forms are published.

These are *different* reductions of the same source, not alternative
descriptions of one another.

### Degree three

| Source | Dimension | Determinant | In the suite |
| --- | --- | ---: | --- |
| <https://gist.github.com/Spacerat/08b4a43f6b6ca57178efabc220170ce8> | 11 | −2 | yes |
| <https://github.com/royvanrijn/jacobian-research> | 12 | 1 | no |
| this project, `examples.alpoege12()` (derived) | 12 | 1 | yes |
| A. Macfarlane, `F13` | 13 | 1 | no |
| this project, `examples.alpoege13()` (derived) | 13 | 1 | yes |
| this project, `examples.alpoege15()` (derived) | 15 | 1 | yes |
| this project, `examples.bcw17()` (derived) | 17 | 1 | yes |
| <https://rhicksrad.github.io/jacobian-degree3/> | 19 | −2 | yes* |
| A. Long, arXiv:2607.18186 | 39 | | no |

### Cubic homogeneous

| Source | Dimension | In the suite |
| --- | --- | --- |
| <https://github.com/royvanrijn/jacobian-research> | 19 | no |
| this project, from `spacerat11` | 19 | derived, not stored |
| A. Macfarlane, `G20` | 20 | no |
| this project, from `alpoege12` | 20 | derived, not stored |
| <https://github.com/wtho704/explicit-cubic-homogeneous-jacobian-counterexample> | 24 | yes |
| A. Long, arXiv:2607.18186 | 79 | no |

### Quartic gradient form

| Source | Dimension | In the suite |
| --- | --- | --- |
| <https://github.com/royvanrijn/jacobian-research> | 38 | no |
| this project, from `spacerat11` | 38 | derived, not stored |
| arXiv:2608.12543v1 | 40 | derived, not stored |
| Zenodo 21504303 | 48 | no |

\* The nineteen-dimensional map at degree three is in the suite from a checkout
and not from the source archive, which excludes `tests/data.py`: it is somebody
else's mathematics and its licence could not be established. Without the file
the tests that need it skip themselves and say why.

"derived, not stored" means the suite builds the map from a stored one and
verifies every step, and holds no copy of the result.
`scripts/measure_pipeline.py` recomputes all six of those rows.

Two rows entered the suite in milestone 0.6. Thompson's map came in with work
package 4 as `examples.thompson24_homogeneous`, because the compression is
checked against it; Spacerat's came in with work package 6 as
`examples.spacerat11`, because the pipeline through it reaches nineteen. Both
are transcribed from the licensed presentation and not from the link in the
row, which `docs/provenance.md` records.

Macfarlane's `F13` and `G20` and the twelve-variable map above are not in the
suite and cannot be: neither repository carries a licence. They are cited and
not copied, and `tests/data.py` holds the one earlier case of the same kind.

The two rows belonging to this project are both marked *derived*, and both mean
the same thing by it: the suite builds each of them from Alpöge's map and
verifies the chain. They differ in when that became possible. The
seventeen-dimensional map has been derived since version 0.2, by a chain of
eight steps — the linear normalization and seven `BCWStep` — with the collision
transported along. The fifteen-dimensional one has been derived since 0.3, when
steps that reuse a carrier became expressible.

What a derivation does and does not establish is a separate question from
whether there is one, and the two cases differ there. The provenance section
below says what is evidence and what is a self-check, for each.

Both maps moved into `kellermap.examples` in 0.4, which changes where they are
written and not who computed them.

The rows are not directly comparable. BCW reduce in two stages, first to
degree 3 and then to cubic homogeneous form; the 24-variable map has completed
both, the others only the first. A conservative Bass–Connell–Wright route on
the same source is reported at 79 variables.

The determinant column also records a difference in the coefficient ring, and
it is not a matter of presentation. The two derived maps begin with the linear
normalization of Chapter II, Proposition (1.1), which divides by the
determinant, so they carry genuine fractions — `1/2`, `-1/2`, `-3/2` — and live
over `QQ`. The dimension-19 map keeps the determinant −2, so it was never
normalized, and it and its whole chain are over `ZZ` with integer coefficients
throughout.

Since a `BCWStep` preserves the coefficient domain, the domain of the source
fixes the domain of everything reachable from it. Normalizing first is
therefore a choice about the search space and not only about the shape of the
first step: over `ZZ` a step coefficient must be an integer, over `QQ` it need
not. Milestone 0.5 searches without a fixed target and has to make that choice
deliberately; `roadmap.md` records it.

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
| this project, found by search | 13 |

The steps down from 39 to 17 come from choosing the factorization better —
`P · Q` may be any subsum of the target component, so one step can remove
several monomials. The step from 17 to 15 comes from reusing a carrier, and
the step from 15 to 13 from letting a search choose both, which is what work
packages 11 and 11.1 of milestone 0.5 built.

### Degree three is not cubic homogeneous

The table above is one milestone of the Reduction Theorem and not its end. BCW
prove it in three steps: reduction to degree three, making `J(F)` unipotent,
and homogenization. Every figure in the table is at the first of those.

That matters for reading any other number against them, because the published
figures that are easiest to find are at the third. Long, arXiv:2607.18186,
tracks the same reduction of the same map and reports 39 variables at degree
three and 79 after the homogeneous reduction, which he describes as
conservative rather than optimized. So a figure from after the first stage is
not comparable with a figure from before it.

Which stage costs what: the second, p. 306, is the one that doubles, where
`G(T) o E(T)^[n] o H(T)` is a map in `2n` variables. The third, p. 307, costs
one variable, `L = (X + N(T), T)`. Together `2n + 1`, and Long's two figures
are that arithmetic exactly, since `2 * 39 + 1 = 79`.

What this project builds is those two stages and not the whole of Theorem 2.1.
Part (b) of that theorem asks for a normal form that is in addition linear in
each of the original variables and quadratic only in `T`, which Proposition
(3.1) delivers in a second half this library does not implement. The map a
chain reaches here is cubic homogeneous with nilpotent Jacobian and need not be
multi-affine: `(x + y^3, y)` homogenizes to a verified five-dimensional target
that still carries a `y^3`.

Nothing on this page rests on the refinement. The corollary the literature uses
-- and every figure compared below -- needs the cubic homogeneous form and not
the multi-affine one. An audit of `0.6.0rc1` found the claim stated too widely
in `README.md` and `CHANGELOG.md`, and `docs/errata.md` records it.

### Thompson's twenty-four variables

W. Thompson, posted to the Secret Blogging Seminar on 20 July 2026 and archived
at https://github.com/wtho704/explicit-cubic-homogeneous-jacobian-counterexample.
Following Alpöge's counterexample, an explicit Bass–Connell–Wright reduction to
a map in 24 variables in which every non-zero component of the displacement is
a homogeneous cubic. Reported alongside it: 54 cubic monomials, Jacobian
determinant identically one, an explicit rational collision, two independently
written exact verifiers, and a nilpotence certificate.

Two things about it belong here rather than in a comparison.

It is cubic homogeneous, so it is at BCW's third stage and not the first. It is
therefore comparable with Long's 79 and not with the 13 of `alpoege13`.

The library carries out neither of the two stages that lead there, so it has no
certified figure at that stage and claims none. What exists is a measurement
made while milestone 0.6 was being cut, in plain SymPy and outside the library:
`alpoege13` normalized, made unipotent and homogenized is 27 variables, and
compressed by Theorem 3 of arXiv:2608.12543v1 it is 22. Below 24 and above
Macfarlane's 20. `docs/roadmap.md` states what that computation checks and what
it does not, and the determinant is among the things it does not check as a
polynomial. It is a target for the packages of 0.6 and not a figure this
repository claims; until a certificate stands behind it, no comparison is drawn
from it.

The nilpotence index was corrected. Thompson reports `(JN)^17 = 0`; an
independent verification, Zenodo record 21504303 of 23 July 2026, reports the
index as 18 rather than 17 while confirming the map itself. That correction is
recorded because a page that cites a result should cite its state and not its
first announcement.

Thompson states plainly that he claims neither priority nor global minimality,
and asks whether an earlier explicit cubic-homogeneous reduction is known. This
project takes the same position for the same reason, and it is worth saying
that the posture is shared rather than borrowed.

### Thirteen variables were reached a month earlier

A. Macfarlane, https://github.com/Amacfa/keller-counterexamples-13-20,
timestamped 22 July 2026. An explicit thirteen-variable Keller map of degree
three with determinant one and a two-point collision, obtained by restricting
Thompson's twenty-four-variable cubic-homogeneous form to an invariant
subspace. The same repository carries a twenty-variable cubic-homogeneous map
by the same construction, four below Thompson's.

Both were recomputed here from the published coefficients, in SymPy and
without this library, on 25 August 2026:

| | reported | recomputed |
| --- | --- | --- |
| `F13`: dimension, degree | 13, 3 | agrees |
| `F13`: Jacobian determinant | 1 | 1 at three sample points |
| `F13`: `F(p) = F(q) = p`, `p ≠ q` | yes | agrees |
| `G20`: dimension, every non-linear term cubic | 20 | agrees |
| `G20`: Jacobian determinant | 1 | 1 at two sample points |
| `G20`: collision, and `gamma(q)` | as printed | agrees exactly |

The map is held in `tests/data.py` as `MACFARLANE_COMPONENTS` and not in
`kellermap.examples`, for the reason the nineteen-dimensional map is: the
repository carries no licence file, so the values are not taken into the
package. It is called `macfarlane13` here and not `F13`, because `alpoege13`
already names Alpöge's map in dimension 13 and the author of the reduction is
what tells the two apart.

So thirteen variables at degree three were reached a month before this project
reached them, by a different route, and `alpoege13` is not first. The two maps
are not the same map: `alpoege13` carries 58 terms and a three-point collision
and comes from Alpöge's map directly, `F13` carries a two-point collision and
comes from compressing Thompson's normal form. Neither is a refinement of the
other.

This is why the wording of the section above was written as it was, and it is
worth saying what that was worth. The claim not made was the claim that would
now be wrong. What survives is a statement about a search on one day, and the
correction cost nothing but this paragraph.

### Eleven variables were reached on the day of the announcement

The smallest published dimension at degree three is not thirteen, and this
project noticed that only while cutting the work package for `alpoege12`, a
month after the entry above was written. The check that found it is the same
one, run again.

Spacerat, "11 variable cubic Jacobian conjecture counterexample", GitHub Gist,
created 20 July 2026, one revision,
https://gist.github.com/Spacerat/08b4a43f6b6ca57178efabc220170ce8
An explicit eleven-variable map of degree three with 52 non-zero monomials,
Jacobian determinant −2, and three rational points in one fibre. Its header
states that the construction, the simplification and the verification code in
it were generated by ChatGPT.


The two records can be put in an order, and this page does not put any weight
on it. The gist header gives 06:58 UTC. The announcement displays 4:19 on 20
July to a reader in central Europe, which is 02:19 UTC under the reading above,
so the announcement comes first by some hours and both fall on 20 July UTC.
Whether the gist's author had seen the announcement, and whose local calendar
said what, is not something these two timestamps establish, and no claim here
needs it: what matters is that a smaller published dimension existed and this
project's check did not find it.

The same map is printed in full as `Phi` in Section 6 of arXiv:2608.05392v1,
Castañeda, Honorato and Valenzuela-Henriquez, 5 August 2026, which cites the
gist as the source of the calculation and adds a block-determinant proof and a
polynomial section of the fibres. That paper is CC BY 4.0. The gist carries no
licence, so where a value is needed it comes from the paper and not from the
gist.

Recomputed here from Section 6, in SymPy and without this library:

| | reported | recomputed |
| --- | --- | --- |
| dimension, degree | 11, 3 | agrees |
| Jacobian determinant | −2 | −2 over `QQ[x1..x11]` |
| three rational points in one fibre | yes | agrees, image `(−1/4, 0, ..., 0)` |

Two things follow for this project, and neither is comfortable.

`alpoege13` was already behind when it was found. The entry above says thirteen
was reached a month earlier and names Macfarlane; the gist above is dated the
same day as Alpöge's announcement, 20 July 2026, and the check that should
have found it did not.
What went wrong is not the rule but its scope: the search was for the number
thirteen and for the phrase "cubic homogeneous", and a gist titled for eleven
variables was outside both. A check for a number one has just reached will not
find a smaller one.

`alpoege12` is not a record either, and the work package that adds it says so
before it says anything else.

### A chain of six steps reaches it, and it is not an untargeted chain

Asked because the number matters and answered by running the backward search at
it, as for `macfarlane13`. `peel` reaches the map from `examples.alpoege()` in
six steps, examining seven maps in about a third of a second. The chain
verifies and its endpoint is the published map after reordering the generators,
component for component.

It runs from Alpoege's map and not from its normalization, and that is forced
rather than chosen. A `BCWStep` preserves the Jacobian determinant; this map
has `-2`, the normalized source has one, and REV-11 rules the pairing out
before any search. Against the normalized pair the peel is exhausted after
ninety-eight maps.

`scripts/reconstruct_spacerat11.py` recomputes the six steps in plain SymPy
without the library, together with the published map and its three points, and
checks the chain against them. Twenty-four checks. One of the six steps names
one bought coordinate in both factor slots, so it subtracts a square; that is
the extension of Proposition (3.1) this project marks wherever it uses it.

**None of the six steps is one the untargeted enumerator offers.** Each
transition was compared against everything `untargeted_candidates` produces at
the map before it, building each candidate with the names the step actually
uses:

| step | matches a candidate |
| ---: | :--- |
| 1 to 6 | no |

Zero of six, where `macfarlane13` gave two of seven. The comparison was
validated before it was believed, on the ten steps of the `alpoege12` chain,
which came out of the enumerator by construction: ten of ten match, at exactly
the candidate positions the driver's result file records. Without that control,
a broken comparison and a real gap are the same output.

So the correct statement is again the narrow one. A six-step chain reaches this
map from Alpoege's, and that chain is not one the untargeted enumerator can
produce. Whether the map is reachable by some other untargeted chain is open
and was not tested.

### What the pipeline of milestone 0.6 makes of it

Nineteen cubic homogeneous variables, by the three stages this milestone
built: 11, then 22 after the unipotent reduction, 23 after the homogenization,
19 after collision-hull compression. Every step is verified by the library and
the three points arrive.

That is one below the smallest cubic homogeneous figure this page records,
Macfarlane's 20, which is also what Prellberg's hull makes of Thompson's 24.
The literature was checked again before this paragraph was written and nothing
smaller was found.

What it is not is new mathematics. It composes two published constructions,
the eleven-variable reduction and the two stages of Section 4 with Theorem 3 of
arXiv:2608.12543v1. What this project contributed is the composition and the
certificates. No minimality is claimed, here or anywhere.

The number needs its stage attached wherever it is used. `alpoege19` is
nineteen variables at degree *three* and has been in this repository since 0.4;
Terence Tao's comment thread carries the same figure for the same kind of
object. Two nineteens from two routes at two stages, and a bare nineteen names
neither.

### What the eleven-variable construction does that this library cannot

Worth separating from the count, because it is the part that bears on the
roadmap. The gist lists four moves. Three of them this library has: reducing
shared factors simultaneously, reusing an already introduced coordinate
(BCW-10), and cancelling `x^2 y^2` against the square of an existing one
(BCW-12). Its own intermediate map has twelve variables, which is where
`alpoege12` also is.

The fourth is a move this library has no form for. Two coordinates `f` and `g`
occur in the other components only through `f + g`; after the
determinant-one change `f = t`, `g = s - t` on the source and
`(Y_s, Y_t) = (Phi_f + Phi_g, Phi_f)` on the target, the coordinate `t`
survives only in its own component, as `t + A(rest)`. A triangular coordinate
of that shape can be deleted: the determinant does not change, and two
colliding points cannot differ in `t` alone, so the collision survives with all
its points.

That is a step which *lowers* the dimension, and every step type here raises it
or leaves it alone. Whether it belongs in this library is a question for the
roadmap and not for this page.

`alpoege12` does not admit it, in either of the two forms that are cheap to
test. No coordinate is deletable on its own — the untargeted search buys a
coordinate in order to use it, so each occurs in some other component — and no
pair of coordinates occurs elsewhere only through its sum. Both checks are
narrow and both come out empty; a linear change that creates such a pair from
something else is not ruled out by either.

### A chain reaches it, and it is not an untargeted chain

Asked because the derivation is unlike anything here, and answered by running
the backward search at it. `peel` reaches `macfarlane13` from Alpöge's
normalized map in seven steps, examining eight maps, in about a second. The
chain verifies and its endpoint is his map after reordering the generators.

`scripts/reconstruct_macfarlane13.py` carries those seven steps and recomputes
them in plain SymPy without the library, together with his map from the
published coefficients. Seventeen checks.

The chain also extends his collision. His map is published with two preimages
of one image; carrying Alpöge's three through the chain gives three, and the
first two are his, coordinate for coordinate. The third is recorded in
`tests/data.py` as `MACFARLANE_THIRD_POINT`, separately from his two, because
it is this project's and they are not.

The two derivations account for the difference. His restricts Thompson's
twenty-four-variable form, and what arrives there is what Thompson carried, two
points; Alpöge's map has three and the chain brings all three. The agreement on
the first two is also the sharpest confirmation the chain could get: two
independently computed points matching in thirteen coordinates would not
survive a transcription error.

**This page claimed more than that and was wrong.** It said the map lies inside
the space the untargeted search describes and that only the order of the steps
differs. An external audit of `0.5.0rc1` compared each of the seven transitions
against everything `untargeted_candidates` offers at the map before it:

| step | matches a candidate |
| ---: | :--- |
| 1 to 5 | no |
| 6 | yes |
| 7 | yes |

Two of seven. This table carried the positions of the two matching candidates,
17 and 9. They were wrong: building each candidate with the names the step
actually uses and comparing the resulting step gives 15 and 6, zero-based, and
that comparison is unambiguous. A first correction blamed a missing convention
for matching rather than the figures, which was an evasion. The positions are
left out because they are an artefact of the enumeration order and say nothing
a reader needs, not because they cannot be determined.

Already the first step removes a term that is not a leading monomial of its
component, which is what UNT-1 requires and what `peel` does not. All seven
lower `Phi`, and `peel` searches a wider space than `untargeted.py` offers.

So the correct statement is the narrow one: a seven-step BCW chain reaches
`macfarlane13` from the same source, and that chain is not one the untargeted
enumerator can currently produce. Whether the map is reachable by some other
untargeted chain is open and was never tested; the claim conflated `peel`
finding a chain with the map lying in the offer.

The error is instructive about its own kind. `peel` divides a displacement and
so is bounded by the target; `untargeted_candidates` splits a leading monomial
and is bounded by nothing but the map. That the two spaces differ is stated in
UNT-1 and in the docstring of `enumerate_candidates`, and the sentence was
written anyway.

The twenty-variable map also fills the gap this page left open. The best
cubic-homogeneous count recorded here is 20 and not 24, and this project still
has no figure at that stage, having never carried out the homogenization.

### What the comparison establishes

At the degree-≤3 stage, 13 is the smallest count recorded, and it is reached
independently twice: by Macfarlane on 22 July 2026 from Thompson's normal form,
and by this project on 24 August 2026 from Alpöge's map by search. Against 15
and 17 of this project's own earlier chains, 19 published, and 39 tracked as a
bound.

It is not a claim of priority, and the section above says who was earlier. It
is not a claim of minimality either; the reasons are under "What it does not
establish" in the section on `alpoege13`, and the measurement behind them is in
`docs/roadmap.md` under WP 12.

What the second arrival is worth is a different thing and worth stating: two
routes that share no construction reached the same count, one by compressing a
larger normal form and one by searching upward from the original map. That is
evidence about the number 13 rather than about either method.

What it does establish is narrower and is the first target the roadmap set for
this comparison: the published nineteen-variable reduction is reproduced here
with a machine-verifiable certificate, seventeen steps each checked against
BCW-1 to BCW-12, and the endpoint compared against data this project did not
compute. Reproducing a published figure and improving on one are separate
results and are reported separately.

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

For the seventeen-dimensional map it is the same: those components are the
maintainer's own hand computation, external to the *library* and not to the
*project*. `docs/provenance.md` sorts every fixed map by which of the two it
is, and `docs/errata.md` records that this page once said otherwise.

So at that stage the only external datum a chain is compared against is its
*source*. The endpoint comparison, the one the last step's BCW-1 performs, is
against data this project produced by hand: a real check that can fail, and not
agreement with a third party.

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


The note arrives independently at the Schur-complement route this library uses
for the determinant. On this map the difference is not a nicety: the carrier
block reduces the 19×19 determinant to a 3×3 one in a fraction of a second,
while `sp.Matrix(F.jacobian()).det()` did not finish in a quarter of an hour.

---
