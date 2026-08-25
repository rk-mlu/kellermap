# Contributing

Thank you for looking. This is a small research project with a narrow subject,
so the most useful thing to know first is what kind of change fits.

`AGENTS.md` holds the same working agreements written for an AI assistant. It
is more detailed on delivery and on the reasoning the project expects, and it
is worth reading whether or not you use one.

---

## What fits

- A defect, with the input that shows it. A reproduction is worth more than a
  patch, and a patch without one is hard to review.
- A missing negative control: a check that exists and that no test would miss
  if it were deleted. `scripts/mutation_probe.py` finds these; a report from it
  is a good issue.
- A correction to the documentation, especially a source that was cited wrongly.
  Page numbers and licences here rest on somebody having opened the source, and
  two were wrong in 0.4.
- An independent computation. `scripts/` holds plain SymPy renderings of the
  same reductions, without the library. A second one that disagrees with the
  first is the most valuable bug report this project can receive.

## What probably does not fit yet

- New mathematics beyond the milestone in progress. `docs/roadmap.md` says what
  each version is for. A change that belongs to a later milestone is not
  refused, but it will wait.
- Performance work without a measurement. `docs/roadmap.md` records where a
  peel spends its time, under `cProfile`. A change that is faster in principle
  is not yet a change that is faster.
- Anything that makes a certificate an assertion. The library stores
  factorizations rather than products, and raises named obligations rather than
  returning booleans, on purpose.

---

## Before you open a pull request

Everything below has to pass.

```
make check          # ruff, mypy --strict, the fast suite
make check-full     # the above, with the slow markers instead of the fast suite
make coverage       # the suite again, with fail_under = 100
make reconstruct    # the five independent reconstructions
make measure        # the figures the untargeted obligations rest on
```

`make check` does not run coverage and `make check-full` does not either.
Coverage is a target of its own, and so is `make reconstruct`. `make release`
runs all of them before a tag, together with `lock-check`, `build-test`,
`dist-check` and `test-minimum`.

`make coverage` is a superset of `make check`'s test run, so there is no reason
to run both. On a slow machine, `make check-full` and
`scripts/mutation_probe.py` are the two that dominate: 259 and 187 seconds
against 135 for everything else together. `AGENTS.md` records how that is
divided when the assistant and the maintainer work on one change.

Or the individual gates:

```
ruff format --check .
ruff check .
mypy src
mypy --strict scripts
pytest
pytest -m ""
pytest --cov          # fail_under = 100
python scripts/reconstruct_bcw17.py
python scripts/reconstruct_alpoege15.py
python scripts/reconstruct_alpoege19.py
python scripts/reconstruct_alpoege13.py
python scripts/reconstruct_macfarlane13.py
python scripts/untargeted_space.py
```

Setup is `uv sync`. Python 3.10 to 3.14 are supported and the CI runs both
ends.

### Coverage is one hundred per cent and enforced

A branch that cannot be reached, because an obligation checked earlier rules it
out, gets `# pragma: no cover` with the reason beside it. Do not write a test
that forces an object into a state it cannot reach.

If widening a guard makes an existing test stop reaching the branch it was
written for, rebuild the test rather than mark the branch unreachable. This
happened three times during 0.4, and each time the coverage gate is what said
so.

### Every check needs a negative control

A test that shows the check fails when the data is wrong. Without one there is
no way to tell whether a check verifies anything or merely happens to pass.
This applies to tests of the documentation and the packaging as much as to the
mathematics.

---

## Contracts come before implementation

`docs/contracts.md` states what the verification surface must guarantee, one
numbered obligation at a time: `COL-3`, `BCW-11`, `REV-9`. The exception that
fails cites its identifier.

If a change adds or alters a guarantee, the page is written first. Identifiers
are never reused; a withdrawn obligation stays listed as withdrawn. Where an
implementation forced an amendment, the page says so in its wording rather than
quietly reading as though it always said that.

`tests/test_documentation.py` checks that every cited obligation exists and
that a range presented as a whole family reaches its last member, so a stale
reference fails the suite rather than the next audit.

---

## Language and style

- **The repository is in English**, without exception: source docstrings and
  comments, test docstrings and test comments, assertion messages, `docs/`,
  `README.md`, `CHANGELOG.md`, commit messages, release notes.

  Test docstrings were German by convention until milestone 0.5, and that
  exception is withdrawn. `tests/test_language.py` enforces the rule. It is a
  word list and therefore a net with holes, so a green run is not a proof;
  `scripts/foreign_words.py` is the second instrument and is read once per
  file.
- **Python files are pure ASCII**, enforced by `tests/test_ascii.py`. Umlauts
  and typographic characters belong in `docs/` and `README.md`.
- **Documentation uses plain language.** Short sentences, one statement per
  sentence. No metaphors for technical facts and no sentences carrying two
  dashes and three subordinate clauses. The text has to work for readers who do
  not have English as a first language.

### Commit messages

Conventional prefixes (`fix:`, `feat:`, `docs:`, `build:`, `ci:`, `chore:`),
subject in the imperative, body wrapped at 72 columns. The body says why, not
what — the diff already says what. It should record the reason for the change
and the finding that prompted it, any place where the implementation deviates
from `docs/contracts.md` and why, anything deliberately left undone, and the
state of the gates.

---

## AI-assisted contributions

They are welcome, and they are disclosed. This project is itself developed in
collaboration with a large language model, so a policy that forbade them would
be dishonest.

**Disclose it in the pull request.** Say which tool, and how much of the change
it produced: a whole module reads differently from a docstring reworded, and a
reviewer allocating time should not have to guess. Editor autocompletion of a
single identifier does not need mentioning.

**You are the author.** By opening the pull request you take responsibility for
the contents, however they were produced. That is the same standard arXiv
applies to papers, and it is the only one that works: a model cannot answer a
review question, and it cannot agree to the licence.

**Understand what you are submitting.** The likeliest failure here is not bad
code. It is plausible code, submitted by somebody who cannot say why it is
correct, against a library whose whole subject is the difference between a
claim and a certificate. If you cannot explain what an obligation guarantees
and what would break if the change were wrong, the change is not ready.

**Check every citation yourself.** Page numbers, licences, statements about the
literature — open the source. Fabricated and misattributed references are the
characteristic failure of generated text, and this repository has already
produced two of them. `docs/references.md` records what each claim rests on;
add to it rather than around it.

**Do not open an issue that is a model's summary of the codebase.** Reports of
defects that a run reproduces are useful; a survey of possible improvements is
not.

Optional, and appreciated: a `Assisted-by:` or `Generated-by:` trailer in the
commit message naming the tool.

---

## Reporting something you cannot fix

Open an issue with the input that reproduces it, the output you saw, and the
output you expected. For a search or a peel, give the bounds you passed — a
budget that ran out is a different answer from an exhausted space, and the
distinction is the whole point of the outcome types.

If a reconstruction script disagrees with the library, say so first and ask
questions afterwards. Two implementations that disagree is the case this
project is built to catch.

---

## Licence

MIT. By contributing you agree that your contribution is licensed under it.
