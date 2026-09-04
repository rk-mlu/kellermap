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

## Reserve the DOI first

Zenodo reserves a DOI on a draft, before anything is published. Doing that
first is worth an extra step: the DOI goes into `CITATION.cff` and `README.md`,
those go into the release commit, and the archive that is uploaded carries the
DOI of the record it goes into. An archive that cannot cite itself is a small
thing, and avoiding it costs one click in the right order.

This page said to write the DOI in afterwards, which would have meant a commit
after the tag, an archive naming no record, and a repository whose newest
commit is not the one that was deposited. The order below is the one used for
`0.6.0`.

That is the version DOI. The concept DOI, which resolves to the newest
version, is not reservable; it exists once the record is published, and it
belongs in `README.md` beside the other, described as what it is.

## What to upload

The `.tar.gz` from `dist/`, after a green `make release` on the commit that
carries the reserved DOI. Not the wheel: it carries the package and none of the
reconstruction scripts, the documentation or the tests, which is most of what
makes this repository worth citing.

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

*DOI:* the reserved one, `10.5281/zenodo.22299353` for `0.6.0`. It is already
in `CITATION.cff` and `README.md`; the form only has to keep it.

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

The version DOI is already in the repository, so what is left is the concept
DOI, which Zenodo assigns when the record is published. It is the one to cite
for "the software" rather than for a state, and it goes into `README.md` beside
the version DOI, said to be the concept one. `CITATION.cff` carries a version,
so it keeps the version DOI and not this one.

`tests/test_documentation.py` holds the version DOI in the two places that
carry it, with a control for the case where the label and the target of the
Markdown link disagree. It is not a fifth number in the test that holds the
version together: a version and a DOI do not have to agree with each other,
only each with itself, and one test comparing both would say that they do. The
concept DOI stands in one place, so nothing can compare it with a second copy;
what is checked is that it is not the version DOI, since a number pasted from a
browser after the release is the one that can end up as a duplicate.

For `0.6.0` the two are `10.5281/zenodo.22299353` for the version and
`10.5281/zenodo.22299351` for the concept. They differ in one digit, which is
the reason for the check above.
