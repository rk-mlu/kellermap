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
| §4 | linear normalization `F'' = F'_(1)^-1 o F'`, homogenization |

---

## The counterexample

**Alpöge, L.** Announcement of an explicit counterexample to the Jacobian
conjecture. X, 20 July 2026.
<https://x.com/__alpoge__/status/2079028340955197566>

The map in `tests/test_polynomial_map.py` and the normalization input in
`tests/test_bcw17.py` are this map:

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
  seventeen-dimensional candidate used here.

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
Martin-Luther-Universität Halle-Wittenberg from 1952, succeeding Heinrich W. E.
Jung, until his retirement in 1971; he continued to lecture there into the
1980s and died in Halle.

- MacTutor: <https://mathshistory.st-andrews.ac.uk/Biographies/Keller/>
- Catalogus Professorum Halensis:
  <https://www.catalogus-professorum-halensis.de/keller-ott-heinrich.html>
- Chair succession at Halle:
  <https://disk.mathematik.uni-halle.de/history/allgemein/prof_hal_wb_45_69.html>

Sources differ on the year of the Halle appointment: MacTutor gives 1951, while
Halle's own faculty history, the German Wikipedia and the anniversary article
in *Beiträge zur Algebra und Geometrie* give 1952. This file follows the
latter.

---

## Related cubic Keller-map benchmarks

Useful as comparison and as benchmark targets for milestone 0.4. Note that
these are *different* reductions, not alternative descriptions of the map in
`tests/test_bcw17.py`.

| Source | Dimension | Shape | Determinant | In the suite |
| --- | --- | --- | --- | --- |
| this project, `tests/test_bcw17.py` (candidate) | 17 | degree 3 | 1 | yes |
| <https://rhicksrad.github.io/jacobian-degree3/> | 19 | degree 3 | −2 | yes |
| <https://github.com/wtho704/explicit-cubic-homogeneous-jacobian-counterexample> | 24 | cubic homogeneous | 1 | no |

The first row is marked *candidate* on purpose: the map's own properties are
recomputed by the test suite, but that it arises from a BCW reduction of
Alpöge's map is asserted, not derived. See the provenance section below.

The three are not directly comparable. BCW reduce in two stages, first to
degree 3 and then to cubic homogeneous form; the 24-variable map has completed
both, the other two only the first. The dimension-19 map keeps the determinant
−2, so it has not been linearly normalized.

Comparing them meaningfully needs the certificates that milestone 0.2
introduces. Reproducing published dimensions with machine-verifiable
certificates is the first target of 0.4; improving them is secondary.

### The dimension-19 map

Retrieved 3 August 2026 from <https://rhicksrad.github.io/jacobian-degree3/>,
a research note posted by the GitHub user *rhicksrad* and dated 20 July 2026.
It is held in `tests/test_alpoege19.py`.

The note carries no authority here, and says as much about itself: it is
self-published, was worked out with an LLM, and states that it inherits the
under-review status of the announcement it builds on, which at the time was one
day old. What makes the data usable is that the test suite recomputes it.
Established there, from the components alone:

- dimension 19, degree 3, Jacobian determinant identically −2;
- the map lies in `MA^0` and not in `MA^1`, and its linear part is Alpöge's
  own bordered by the identity — so it has *not* been linearly normalized,
  which is the structural difference from the 17-dimensional candidate;
- three distinct points sharing one image, that image being Alpöge's
  `(-1/4, 0, 0)` padded with zeros, and the points extending Alpöge's in their
  first three coordinates.

The collision points are not taken from the note's table. The carrier
components have the form `w_j + P_j`, so a preimage satisfies `w_j = -P_j`; the
suite solves that system, whose termination it checks rather than assumes, and
compares the result with the published table afterwards. The two routes are
independent and agree.

The components in `tests/test_alpoege19.py` were transcribed from the note's
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

Its reduction is *not* a chain of `BCWStep`s. The note describes seventeen
elementary steps with sixteen carrier variables, so not two per step, and the
carriers `x^2`, `xy`, `y^2`, `yz`, `xz`, `x^2 y`, `xy^2`, `y^2 z` are shared
building blocks reused across steps. Such a step needs only one fresh variable
and stays elementary, which BCW-2 does not admit. Whether to widen it is a
question for 0.3. The `w`-numbering is also not the order of introduction —
the component of `w2` reads `w9` and `w13` — so the factorization cannot be
read off the way BCW17's can. The map is therefore fixed input, not a
`Reduction`.

The note arrives independently at the Schur-complement route this library uses
for the determinant. On this map the difference is not a nicety: the carrier
block reduces the 19×19 determinant to a 3×3 one in a fraction of a second,
while `sp.Matrix(F.jacobian()).det()` did not finish in a quarter of an hour.

---

## Provenance of the fixed test data

`tests/test_bcw17.py` contains a 17-dimensional map that this library did not
produce. It stays external input until this library can derive it: 0.2 lets a
`BCWStep` verify a factorization that is supplied to it, 0.3 searches for one.
What the test suite establishes on its own:

- the map has degree 3, determinant 1, and an explicit three-point collision;
- its collision points extend Alpöge's in their first three coordinates;
- the linear normalization of §4 turns Alpöge's determinant −2 into 1, moves
  the collision image from `(-1/4, 0, 0)` to `(0, 0, -1/4)`, and lands the map
  in `MA^1`, the precondition of Proposition (3.1).

Not established here: the stabilization to dimension 17 and the elementary
factors that reduce the degree from 7 to 3. Verifying such a factorization once
it is written down is milestone 0.2; finding one is 0.3.
