# The Zenodo deposit

What to upload, what to type into the form, and why not the obvious way. This
file exists so that the text of a permanent record is reviewed like everything
else here rather than written into a browser once.

`docs/provenance.md` is the source for the disclosure; the description below
summarises it and points at it. Two texts, one statement -- that is a shape
this project knows how to get wrong, so the description says as little as it
can and refers for the rest.

---

## Not through the GitHub integration

Zenodo can mint a DOI for every GitHub release automatically. It archives the
repository as GitHub packs it, which is everything under version control.

`tests/data.py` is under version control. It holds two maps whose licence could
not be established, and it is excluded from the source archive for exactly that
reason. The webhook would publish them under a DOI: permanent, citable and
irrevocable. That is the rule of `AGENTS.md` failing at a distribution channel
nobody checked, which has now happened twice -- the first time was
`scripts/reconstruct_macfarlane13.py` shipping the same map inside the source
archive, recorded in `docs/errata.md`.

So the deposit is manual, and what is uploaded is the built source archive.
`make release` produces it, `sdist-test` shows that the suite it ships passes
from inside it, and `dist-complete` shows that both artefacts exist. The
archive is the artefact this project checks; the repository tarball is not.

## What to upload

The `.tar.gz` from `dist/`, after a green `make release`. Not the wheel: it
carries the package and none of the reconstruction scripts, the documentation
or the tests, which is most of what makes this repository worth citing.

Before uploading, one check by hand, because it is the one that matters here:

    tar -tzf dist/kellermap-*.tar.gz | grep -c "tests/data.py"

must print `0`.

## Metadata for the form

*Upload type:* Software.

*Title:* kellermap: certified reductions of polynomial Keller maps

*Authors:* Raphael Kruse. No model is listed as an author; see the disclosure
below and `docs/provenance.md` for why.

*License:* MIT.

*Version:* the version of the archive, which is the number `pyproject.toml`
carries.

*Related identifiers:* the GitHub release tag, and the PyPI release of the same
version. Both are "is supplement to" or "is identical to" as the form's
vocabulary allows; what matters is that a reader can get from the record to the
code and to the package.

*Description:* the text below.

---

## Description

kellermap constructs and verifies reductions of polynomial maps with constant
Jacobian determinant. Every transformation is a certificate object that carries
its own obligations; verification names the obligation that failed rather than
returning a boolean, and a collision is transported across each step and
re-verified, so that a reduction of a counterexample is still a counterexample.

Version 0.6 implements the second and third stages of the Bass-Connell-Wright
Reduction Theorem, collision-hull compression, and the symmetric lift to the
gradient form of a quartic over a field containing i. Applied in sequence to
the smallest degree-three map this project holds, the chain runs 11, 22, 23,
19, 38 variables with every step verified and the collision arriving at the
far end.

The constructions are other people's. What this project contributes is the
composition of them, the certificates, and eight reconstruction scripts that
recompute the published results in plain SymPy without using the library. No
minimality and no priority is claimed for any figure: both figures this chain
reaches were published elsewhere first, by a different route, and the record
of what this project claimed too widely and corrected is in `docs/errata.md`.

Generative AI tools were used in two roles: one model wrote code, tests and
documentation in conversation with the maintainer, and a different model
audited the release candidates. `docs/provenance.md` names the tools, says what
each did, and records what the arrangement found -- six audits, of which the
first five each turned up faults that the test suite, the coverage requirement
and a forty-two-probe mutation sweep had all passed. Neither model is an
author. The maintainer set the tasks, ran the gates, read the deliveries and
decided what entered the repository.

---

## After the deposit

The DOI goes into `CITATION.cff` and into `README.md`. Zenodo mints two: one
for the record and one for the concept, which resolves to the newest version.
The concept DOI is the one to cite for "the software", the version DOI for a
specific state; `CITATION.cff` carries a version, so it carries the version
one.

That makes the DOI a fifth place holding a number that has to agree with the
others. `tests/test_documentation.py` already holds four of them together and
should hold this one too.
