# Agent Instructions

> All agents follow four core principles (after Andrej Karpathy). These override speed defaults.
> Source: [andrej-karpathy-skills](https://github.com/multica-ai/andrej-karpathy-skills)

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing: read `CONTEXT.md` and `docs/adr/`. State assumptions explicitly. Present multiple interpretations. Stop and ask when unclear.

### Context First

- This is a pre-publication banking fraud detection **curriculum** repo, private until the v0.1 publication gate passes. Do not add public-release language that implies it is already published.
- Source of truth for current scope/status: `README.md`, `pyproject.toml`, `.github/workflows/ci.yml`, GitHub Issues, and `docs/ROADMAP.md`.
- ADR-0001 establishes two first-class fraud detection tracks; ADR-0005 makes GitHub Issues the operational source of truth (local `.scratch/` and `docs/prds/` are mirrors only).

### Domain Language (use exactly)

The glossary in `CONTEXT.md` is fixed. Terms that are easy to get wrong:

- **Client** = the legal customer; **User** = the digital login identity; **Banking relationship** = the Swiss-bank-style relationship container. Do not use "customer".
- **Alpine Crest Private Bank** for private-banking scenarios; **NovaBank Digital** for digital-banking scenarios. Never use real banks as synthetic institutions.
- Synthetic data may be inspired by public cases but must not claim to reconstruct real events. Do not add real client/account/transaction data, affiliation claims, legal advice, or job-preparation framing.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

No features beyond what was asked. No abstractions for single-use code. No premature "flexibility." If 200 lines could be 50, rewrite it.

### Schema Is Additive Only

ADR-0002: extend the one canonical **Realistic synthetic data model** additively. New modules expose **Progressive data views** rather than separate toy schemas. A breaking schema change needs a new ADR. Schema-contract tests (`tests/test_schema_contract.py`) fail if generated columns drift from `docs/schema/data_dictionary.md`.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

Don't "improve" adjacent code. Don't refactor working code. Match existing style even if you'd do it differently. Every changed line should trace to the request.

### Repo Shape

- Python package source: `src/banking_fraud_lab/` (package discovery `where = ["src"]` in `pyproject.toml`).
- Featured notebooks: `notebooks/00_foundations` through `notebooks/07_interpretability_model_risk`.
- `data/sample/` is the only committed data area — it is the seed-42 `tiny` profile. Medium/large generated datasets must stay out of git.
- `sql/` is SQLite-first; PostgreSQL is a later optional path only.
- Code style: ruff, line-length 100, target py311. No comments unless asked.

### Committed Sample Data

The `data/sample/` CSVs are deterministic seed-42 `tiny` output. If you change schema/generators, regenerate them (works in Bash and PowerShell):

```
uv run python -c "from pathlib import Path; from banking_fraud_lab import generate_minimal_banking_world; generate_minimal_banking_world(seed=42, output_dir=Path('data/sample'))"
```

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals: "fix the bug" → write a test that reproduces it, then make it pass. State step→verify plans for multi-step work.

### Commands (CI runs exactly these)

```
uv sync --extra dev
uv run ruff check .
uv run pytest
```

- `uv run pytest` is intentionally unfiltered — every test under `tests/` runs in CI.
- If `uv` is unavailable locally, install it; do not convert the repo to pip/poetry (CI uses `uv`).
- Branch naming: `feat/issue-<n>-<desc>` / `fix/issue-<n>-<desc>`.

### Optional Extras Are Out Of CI

`neo4j` and `shap` are optional extras (`uv sync --extra neo4j` / `uv sync --extra shap`). Their tests are availability-guarded and stay out of CI. Do not move them into core/dev dependencies.

### Verification Quirks

- Notebook smoke tests execute featured notebooks end-to-end via `nbconvert` on tiny data — slower than unit tests.
- Cross-version `regression_execution` marker tests re-run prior-version notebooks end-to-end.
- Many docs are test-covered: changing `docs/schema/`, `docs/cases/`, `docs/regulation/`, `docs/quality_gates/`, or `README.md` may break documentation-contract tests.

## Issue Tracker And Triage

- GitHub Issues for `akepo225/banking-fraud-detection-lab` are the source of truth. Use `gh issue view <number> --comments` before working an issue; do not rely on `.scratch/` status alone.
- Every triaged issue: exactly one category label (`bug`/`enhancement`) and one state label (`needs-triage`/`needs-info`/`ready-for-agent`/`ready-for-human`/`wontfix`).
- Non-role labels: `afk`, `hitl`, `blocked`, `parent`. Sprints via GitHub milestones.
- Triage comments must start with `> *This was generated by AI during triage.*`

## Agent Skills

### Issue Tracker

GitHub Issues for `akepo225/banking-fraud-detection-lab`. See `docs/agents/issue-tracker.md`.

### Triage Labels

See `docs/agents/triage-labels.md`.

### Domain Docs

Single-context repo with `CONTEXT.md` and repo-wide ADRs. See `docs/agents/domain.md`.
