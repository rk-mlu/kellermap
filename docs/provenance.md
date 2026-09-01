# Provenance

Where the fixed data in this repository came from, under what terms, and what
an agreement with it is evidence for. Split out of `docs/references.md` in work
package 9 of milestone 0.6, when that page had grown to four subjects at once.

The distinction this page turns on is the one `AGENTS.md` asks for and is easy
to lose: data external to the *library*, and data external to the *project*.
Both make a check able to fail. Only the second makes the agreement evidence
about somebody else's mathematics.

`docs/references.md` says what the sources are and what the figures mean.
`docs/errata.md` says what this project reported wrongly about them and
corrected.

---

## Third-party material

The library is MIT. Several pieces of mathematics in it are not this project's
and carry their own terms.

`kellermap.examples.gao_quartic` and `gao_quartic_collision` are from Shuhong
Gao, arXiv:2608.00222v1, licensed CC BY 4.0. Attribution, the licence link and
a statement of changes are in the docstring of the map and in
`docs/references.md` under "A second family of counterexamples".

Thompson's twenty-four-variable map, its twenty-dimensional restriction, the
collision and the vector `rho` are transcribed from the ancillary file
`anc/check_quartic_40.py` of arXiv:2608.12543v1, which is licensed CC BY 4.0
with the rest of that submission. Attribution, the licence link and a statement
of changes are in the docstring of every place that holds them. The formulas
are not altered; the checks around them are this project's, are a subset of the
ancillary file's eleven, and add one it does not make.

Two places hold Thompson's map. `scripts/reconstruct_prellberg40.py` has the
displacement in the source's own shape, and
`kellermap.examples.thompson24_homogeneous` has it as a map, which is what a
caller of this library needs. Work package 4 of
milestone 0.6 put it there, and `tests/test_examples.py` compares the two so
that a transcription cannot drift from a transcription.

The twenty-dimensional restriction the same file prints is deliberately in only
one of them. It is the answer the compression of work package 5 has to arrive
at, and an answer stored beside the code that computes it is not a control: a
change to the compression could then be repaired by editing the expected value.
It stays in the script, which does not import this library. The same subspace
was found independently by Macfarlane; those values are a different source with
no licence and stay in `tests/data.py`.

`tests/data.py` holds the published nineteen-dimensional map and
`macfarlane13`. Neither source carries a licence file, so neither is in the
distribution: `pyproject.toml` excludes that one file from an archive that
otherwise ships `/src`, `/tests`, `/docs` and `/scripts`.

Both reconstruction scripts therefore *read* their target rather than holding
it, and say so when the file is absent. That is a rule about every place a
value could sit and not about one place: until work package 9 of 0.6,
`scripts/reconstruct_macfarlane13.py` carried its own transcription and the
archive shipped it. `docs/errata.md` records it.

`kellermap.examples.spacerat11` and `spacerat11_collision` are the
eleven-variable map of Section 6 of arXiv:2608.05392v1, licensed CC BY 4.0.
Attribution, the licence link and a statement of changes are in the docstring
of the map. That paper credits a GitHub gist for the calculation; the gist
carries no licence, so every value here comes from the paper.

It is reachable from `examples.alpoege()` by six `BCWStep`s, which
`scripts/reconstruct_spacerat11.py` replays without the library. That does not
make it this project's: `peel` is given its target, so deriving the map needs
the map. It is somebody else's, and the reconstruction is a check and not a
claim of authorship.

Nothing else in the repository is somebody else's. This list was one entry
short until an audit of `0.6.0rc1`: `spacerat11` arrived in work package 6 with
its attribution in its docstring, and this page was not extended with it, which
is an inventory gap and not a licence fault.

---

## The fixed test data

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
