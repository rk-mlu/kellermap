# AGENTS.md

Working agreements for AI assistance on `kellermap`. They were settled over the
course of milestones 0.2 and 0.3 and are written down here so that a new
session starts where the last one left off.

This file describes how to work, not what the project is. For that, read
`README.md`, then `docs/architecture.md` for the design and its reasons, and
`docs/contracts.md` for what the verification surface must guarantee.

---

## Language

- **Conversation** with the maintainer is in German.
- **Everything in the repository is English**: source docstrings and comments,
  test docstrings and test comments, `docs/`, `README.md`, `CHANGELOG.md`,
  commit messages, release notes.

  Until milestone 0.5 there was one exception, for test docstrings and test
  comments. It is withdrawn. Every audit of milestone 0.4 read the tests, a
  test is the sharpest statement of what an obligation means, and half of them
  could not be read by a reviewer who does not read German.

  `tests/test_language.py` enforces the rule. It carried the remainder of the
  translation in `NOT_YET_TRANSLATED` while the work package ran; that list is
  empty since the package finished, and every file of the repository is under
  the rule. The list stays in place with the test that keeps it honest: a
  module that has been translated and left in it fails the suite.

  The check is a word list and therefore a net with holes. Three German lines
  got through it and were found by reading, so a green run is not a proof.
  `scripts/foreign_words.py` is the second instrument: it reports prose words
  that do not occur in the English part of the repository, and it is read once
  per file rather than used as a gate.
- **Python files are pure ASCII.** This is enforced by 
  `pytest tests/test_ascii.py` since WP 4 of version v0.4.0. Umlauts and
  typographic characters belong in `docs/` and `README.md`, not in `.py` files.
- **Documentation uses plain language.** Short sentences, one statement per
  sentence. No metaphors for technical facts, no rhetorical constructions, no
  sentences carrying two dashes and three subordinate clauses. The text has to
  work for readers who do not have English as a first language.

  Examples of what was removed: "two ways to say the same thing invite them to
  disagree", "the glue of the induction", "the check bites", "buys a carrier",
  "does not survive contact with the certificate". Each was replaced by the
  direct statement.

---

## Delivering changes

- **Deliver every changed file in full**, never a diff or a fragment. The
  maintainer applies files by hand, and a partial file invites a change to be
  filed in the wrong place.
- **Mirror the target paths** in the output directory, so nothing has to be
  sorted.
- **Draft a git commit message for every change.** Always, without being
  asked.

### Commit messages

Subject line in the imperative, body wrapped at 72 columns. The body says why,
not what — the diff already says what. It should record:

- The body of commit stays preferably below 50 lines. The body does not repeat
  what is already stated in a modified file. One paragraph for each major
  change, one line for a new or modified gate. 
- the reason for the change, and the finding or request that prompted it;
- every place where the implementation deviates from the plan or from
  `docs/contracts.md`, with the reason;
- anything deliberately left undone, and where it is recorded;
- the state of the gates: `ruff`, `mypy --strict`, the suite, coverage.

---

## How the work is organised

- A milestone is split into **work packages** with internal version numbers
  `0.(n-1).k` and tags `wp/0.(n-1).k`. None of them is a release, and
  `pyproject.toml` does not move until the milestone is complete.
- **Every work package leaves the repository green.**
- **Separate a restructuring from an extension.** If a change reshapes an
  interface and another changes what it can do, they are two work packages in
  that order. A failure in the second must not be able to have its cause in the
  first.
- **Contracts are written before the implementation.** New obligations go into
  `docs/contracts.md` first, marked `[0.n]` while unimplemented, and the marker
  is removed when the milestone closes.
- A milestone ends with release candidates and **external audits**. The version
  moves to the final number only after an audit and a green release chain.

### `docs/contracts.md`

- Every obligation has a stable identifier: `COL-3`, `BCW-10`, `RED-2`. The
  exception that fails cites it.
- **Identifiers are never reused.** A withdrawn obligation stays listed as
  withdrawn.
- Amendments are deliberate and visible in the wording. Where the
  implementation forced a change, the page says so.
- Each type states **which of its obligations can fail on supplied data** and
  which are self-checks of the library's own arithmetic. A review should weigh
  them differently.

---

## Quality gates

Everything below has to pass before a change is delivered:

```
ruff format --check .
ruff check .
mypy src                                  # strict
mypy --strict scripts
pytest                                    # fast suite
pytest -m ""                              # including the slow markers
pytest --cov                              # fail_under = 100
python scripts/reconstruct_bcw17.py
python scripts/reconstruct_alpoege15.py
python scripts/reconstruct_alpoege19.py
python scripts/reconstruct_alpoege13.py
python scripts/reconstruct_alpoege12.py
python scripts/reconstruct_spacerat11.py
python scripts/reconstruct_macfarlane13.py
python scripts/reconstruct_prellberg40.py
python scripts/untargeted_space.py
python scripts/measure_pipeline.py
```

`make check` runs the first five, `make check-full` adds the slow markers,
`make reconstruct` runs the eight reconstructions, and `make measure` the
figures behind the untargeted family and behind the pipeline of 0.6. Before a
tag, `make release` adds `lock-check`, `coverage`, `build-test`, `sdist-test`,
`dist-check` and `test-minimum`.

`build-test` and `sdist-test` are two gates and not one. The first installs the
wheel and runs the tests of the working tree; the second unpacks the source
archive, installs it, and runs the suite the archive ships from the archive.
Only the second sees what a user who runs the shipped tests sees, and an audit
of `0.6.0rc1` found a test there that had been failing since 0.5.

This list is not the authority. The Makefile is, and two tests in
`tests/test_documentation.py` hold the two against each other: every command
named here has to be one a target runs, and every `scripts/reconstruct_*.py`
in the tree has to be named here. The list stood at two of the three
reconstructions for a whole milestone before those tests existed.

### Who runs which

The suite has outgrown the assistant's machine. Measured there, one delivery
at the end of milestone 0.5:

| gate | seconds |
| --- | --- |
| `ruff format --check`, `ruff check`, both `mypy` runs | 9 |
| `pytest --cov` | 97 |
| `make reconstruct` | 3 |
| `make measure` | 19 |
| `uv build` and `twine check` | 6 |
| `pytest -m ""` | 259 |
| `scripts/mutation_probe.py` | 187 |

The first five are the assistant's, every delivery, about 135 seconds. The last
two are the maintainer's.

`pytest` and `pytest --cov` are not both run. The second is a superset of the
first and costs 97 seconds against 54, so running both spends 151 seconds to
learn what 97 already say.

`pytest -m ""` moves because the slow markers are most of it: three tests take
181 of the 259 seconds. The assistant runs the fast suite through `--cov` and
says so; a claim about the slow markers that was not run does not go into a
commit message.

`scripts/mutation_probe.py` moves for a different reason, and with an
exception. It re-runs the suite twelve times, so it grows with the suite and is
the second-largest cost. But it is the only thing that catches an obligation
added without a control, so the assistant runs it whenever a change adds or
alters an obligation, a check, or a negative control, and not otherwise.

The commit message says what was run. Where a gate was left to the maintainer,
it is named as such rather than omitted, so that a green list is a list of
things somebody actually ran.

**An exploratory computation that runs longer than ten minutes is the
maintainer's.** Not because the assistant's machine is slower -- the two are
within a fifth of each other on the same determinant -- but because the
assistant's is cut off by a tool-usage limit rather than by a decision, and a
run that ends that way produces no figure at all. Milestone 0.6 has the case:
two runs of about fifteen and about twelve minutes were reaped by the
environment and could not be reported as anything, and the maintainer then
stopped the same computation after eight hours, which is what SYM-7 rests on.

The assistant writes the measurement as a script that takes a budget, prints
the cheap figures first so that a run which never reaches the expensive one
still reports something, and prints either the time or the budget it exceeded.
It goes into the delivery beside the change that needs it.

- **Coverage is 100 per cent and enforced.** A branch that cannot be reached,
  because an obligation checked earlier rules it out, gets
  `# pragma: no cover` with the reason written beside it. Never write a test
  that forces an object into a state it cannot reach.
- **Every example in `docs/api.md` is a doctest** and is executed by the suite.
  Adding a public feature means adding an example.
- **Every Python block in `README.md` is executed** by `tests/test_readme.py`,
  each in its own namespace, and the values it claims are checked.
- Verify claims by running them before writing them down. If a check turns out
  to have been the wrong check, say so plainly rather than quietly replacing
  it.

---

## What a certificate is for

These are the ideas the verification surface rests on. Changes that touch it
should keep them intact.

- **A certificate certifies correctness, not progress.** Nothing requires a
  step to lower the degree. Whether a step is a good step is a question for the
  search.
- **Verification raises and names the obligation.** A boolean would collapse
  several distinct obligations into one bit.
- **Exhibit, do not assert.** Keep the factorization rather than the product.
  "Invertible" is a claim; "here are the generators and their inverses" is
  something a reader can check.
- **Derive rather than store twice.** `G` and `H` come from the factor slots.
  Storing both a factorization and the automorphisms built from it would allow
  the two to disagree.
- **Provenance is recorded and not settable.** `SUPPLIED` means the target was
  not produced by this library in this run, and nothing about who computed it.
  `build()` is the only route to `CONSTRUCTED`. It is an integrity marker
  against mislabelling by accident, not a security boundary.
- **Do not recompute global invariants** that follow from the local
  certificates. Where a test does so anyway, it is an independent cross-check
  and says so.
- **Every check needs a negative control.** A test that shows the check fails
  when the data is wrong. Without one, there is no way to tell whether a check
  verifies anything or merely happens to pass.
- **Two independent implementations beat one.** `scripts/` carries plain SymPy
  computations of the same reductions, without the library.
- **Defer honestly.** A case that is not implemented raises
  `NotImplementedError` naming the work package, rather than computing
  something plausible and wrong.

---

## Claims, sources and data

- **Cite the paper precisely.** `Chapter II, Proposition (1.1), p. 303` is the
  linear normalization; `Section 4` is the proof of the Reduction Theorem. The
  two were confused once and it took a source check to notice.
- **Mark extensions as extensions.** Reusing a carrier is not in
  Bass–Connell–Wright. Where the library goes beyond the paper, the
  documentation says so.
- **Claim no minimality and no priority.** Before a number leaves the
  repository, check the literature again, and say what a comparison does and
  does not establish.
- **Record the provenance of fixed test data**, and distinguish two things that
  are easy to confuse: data external to the *library*, and data external to the
  *project*. Both make a check able to fail; only the second makes the
  agreement evidence about someone else's mathematics.
- **Do not vendor third-party data** whose licence cannot be established. If
  the values are already held in the repository in its own idiom, a second copy
  in the source's format adds only a closed-loop check.
- If an attachment is clearly not meant for this project — personal data, for
  instance — do not process it, and say so.

---

## Judgement

- **Flag every deviation** from the plan or the contract, with the reason,
  rather than following the plan into something worse.
- **Push back on an inconsistent instruction.** A plan that asks for a supplied
  target and for `CONSTRUCTED` provenance is asking for two incompatible
  things; say which one gives way and why.
- **Correct yourself in the open.** If a test or an argument was wrong, the
  correction goes into the answer and into the commit message.
- Prefer the smaller change. Several findings in the audits were narrower than
  they first appeared, and saying so is more useful than fixing more than is
  broken.
