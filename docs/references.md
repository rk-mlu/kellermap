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

## Other reductions of the same map

Useful as comparison and as benchmark targets for milestone 0.4. Note that
these are *different* reductions, not alternative descriptions of the map in
`tests/test_bcw17.py`.

| Source | Dimension | Shape | Determinant |
| --- | --- | --- | --- |
| this project, `tests/test_bcw17.py` (candidate) | 17 | degree 3 | 1 |
| <https://rhicksrad.github.io/jacobian-degree3/> | 19 | degree 3 | −2 |
| <https://github.com/wtho704/explicit-cubic-homogeneous-jacobian-counterexample> | 24 | cubic homogeneous | 1 |

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

---

## Provenance of the fixed test data

`tests/test_bcw17.py` contains a 17-dimensional map that this library did not
produce. It is external input until `BCWStep` can generate it. What the test
suite establishes on its own:

- the map has degree 3, determinant 1, and an explicit three-point collision;
- its collision points extend Alpöge's in their first three coordinates;
- the linear normalization of §4 turns Alpöge's determinant −2 into 1, moves
  the collision image from `(-1/4, 0, 0)` to `(0, 0, -1/4)`, and lands the map
  in `MA^1`, the precondition of Proposition (3.1).

Not established here: the stabilization to dimension 17 and the elementary
factors that reduce the degree from 7 to 3. That is the content of milestone
0.2.

---

## A note on the local copy of the BCW paper

A scanned copy of the 1982 paper has been used during development. It is not
part of the repository and should not be committed: it is a 7.5 MB binary of
page images, it is not searchable, and its distribution is not ours to make.
Use the Project Euclid link above.
