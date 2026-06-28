# Contributing

<!-- HITL-REVIEW-REQUIRED: Public-facing contributor guidance. Repo owner should review wording, scope, and boundary framing before public feedback begins. -->

Contributions should preserve the repo's educational scope and source discipline.

The project is educational only, unaffiliated with any bank, fintech, regulator,
vendor, or public case source, and does not provide legal, compliance, audit,
investment, regulatory, or professional advice. Do not add real client data,
real-bank affiliation claims, or claims that synthetic data reconstructs real
events.

> The repository remains private until the v0.1 publication gate is accepted.
> v0.9 is a beta review point, not a shipped release. The contributor guidance
> below is framed for the future public post-beta state; it is not a claim that
> the repo is public now.

See `LICENSE.md` for the split license model and
`docs/release/v0.1-publication-checklist.md` for the publication-review gate.

## Reporting Issues

Prefer the issue templates under `.github/ISSUE_TEMPLATE/` (bug report or
enhancement). They apply the repo's triage-label vocabulary
(`docs/agents/triage-labels.md`) automatically. When filing:

- Use the fixed glossary (Client / User / Banking relationship; Alpine Crest
  Private Bank / NovaBank Digital). Do not use "customer" or real-bank names.
- Include the exact reproduction commands and your environment.
- Keep reports free of real client data and real-event reconstruction claims.

## Making Changes

All contributions run through the fixed CI gate from a clean checkout:

```bash
uv sync --extra dev
uv run ruff check .
uv run pytest
```

Do not convert the repo off `uv`, filter the test suite, or add new CI commands
(`AGENTS.md` fixes these). Use `uv` for local setup; do not switch to pip/poetry.

## Case Contributions

New cases must include:

- Public sources.
- Detection-pattern mapping.
- No confidential or proprietary information.
- Separation of facts from interpretation.
- Explicit limitations.
- Links to relevant modules or exercises.

## Code Contributions

- Keep synthetic data deterministic by seed.
- Avoid real client data or realistic reconstruction claims.
- Add tests for generator behavior and referential integrity.
- Keep notebooks runnable from a clean setup.
- Schema is additive only (ADR-0002): extend the canonical model additively. A
  *breaking* schema change requires a new ADR; an ordinary additive
  table/column does not.
- Optional extras (`neo4j`, `shap`) stay optional and out of CI.

## Notebook Contributions

- Code-generated notebooks commit the `_build_*.py` generator; the `.ipynb` is
  the tested artifact (v0.6–v0.8 convention).
- Notebooks reuse the existing feature/evaluation/interpretability/governance
  surfaces — they do not reimplement them.

## Glossary And Public-Facing Text

- Fixed glossary terms: Client (legal customer; avoid "customer"), User (digital
  login identity), Banking relationship, Detection pattern, Alert lifecycle.
- Fictional institutions only: Alpine Crest Private Bank, NovaBank Digital.
  Never real banks.
- Keep pre-publication framing. No job-preparation, public-release, or
  reconstruction language in any public-facing text.

