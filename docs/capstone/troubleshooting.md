# Capstone Troubleshooting

This is an educational troubleshooting guide for the v0.9 capstone. It covers
the most common setup and execution failures a learner hits, with self-recovery
steps. It is not legal, compliance, or professional advice, and the repository
remains private until the v0.1 publication gate is accepted.

<!-- HITL-REVIEW-REQUIRED -->

For the canonical command set, see
[`docs/quality_gates/v0.1-ci.md`](../quality_gates/v0.1-ci.md) and the
[main README](../../README.md).

## Environment And Dependency Failures

### `uv: command not found`

`uv` is the package manager this project uses in CI and locally. Install it
per the official instructions (e.g. via the standalone installer or your OS
package manager), then re-run `uv sync --extra dev`.

> Do not convert the repo to pip or poetry. CI runs `uv` and `AGENTS.md` fixes
> it. If `uv` is unavailable, install it rather than switching managers.

### `uv sync --extra dev` fails or resolves nothing

- Confirm you are at the repository root (the directory containing
  `pyproject.toml`).
- Confirm the Python version matches the target (Python 3.11+; `pyproject.toml`
  pins `requires-python`). Use `uv python list` to check available interpreters.
- If a lockfile drift is suspected, run `uv sync --extra dev` again on a clean
  checkout; the committed `uv.lock` is authoritative.

### Optional extras (`neo4j`, `shap`) errors

`neo4j` and `shap` are **optional** extras and are intentionally out of CI.
Their tests are availability-guarded and skip when the extra is missing. Install
them only if you want that optional path:

```bash
uv sync --extra neo4j
uv sync --extra shap
```

Do not move them into the core/dev dependencies (AGENTS.md forbids this).

## Notebook Execution Failures

### A capstone notebook raises `ModuleNotFoundError` or `ImportError`

Re-run `uv sync --extra dev` so the editable `banking_fraud_lab` package is
installed into the notebook kernel environment, then restart the kernel. The
notebooks import `banking_fraud_lab` directly.

### A capstone notebook times out or is slow

The notebook smoke tests use generous nbconvert timeouts (180-300s per cell).
On a cold start or a slow machine, the synthesis notebook (which builds the
graph and runs the monitoring flow for both tracks) can take a few minutes. This
is expected, not a failure. Re-run once the kernel is warm.

### `nbconvert`/`jupyter` not found

The notebook smoke tests run `jupyter nbconvert`. Install the dev extras
(`uv sync --extra dev`); `nbconvert`/`nbclient` are part of the dev dependency
set.

## SQLite Loading Failures

### `no such table` when running a capstone SQL example

The capstone SQL examples (`sql/examples/12_capstone_private_banking.sql`,
`13_capstone_digital_banking.sql`) run against a **capstone** dataset loaded
into SQLite, not the default minimal world. Load the learner-facing capstone
tables first:

```python
from pathlib import Path
from banking_fraud_lab import load_tables_to_sqlite
from banking_fraud_lab.capstone import generate_learner_facing_capstone_private_banking_world

tables = generate_learner_facing_capstone_private_banking_world(seed=42)
load_tables_to_sqlite(tables, Path("data/capstone/private_banking.sqlite"))
```

### Progressive views missing

`load_tables_to_sqlite` builds the progressive views by default
(`include_progressive_views=True`). If you loaded tables with a custom loader,
ensure the progressive views are created or the capstone SQL examples will
report unknown relations.

## Protected-Key Confusion

### "I need the labels to score the model" / protected keys seem missing

By design, the **learner-facing** capstone export **excludes** the
`protected_scenario_answer_keys` table and its columns
(`available_to_learners`, `label_type`, `label_value`). The supervised label for
the capstone scoring notebooks comes from generated `case_outcomes`
(`confirmed_fraud`), **not** the protected answer keys. The grading export
(`generate_capstone_*_world`, without the learner-facing wrapper) includes the
protected keys and is for maintainers/graders only.

- Investigation work must **not** be solved by inspecting protected labels.
- If a notebook references `protected_scenario_answer_keys`, it should only be
  in an `assert ... not in learner_tables` exclusion check, never as a feature.

## Scale-Profile Selection

### Generating a "medium" or "large" dataset hangs or fills the disk

The committed sample data is the deterministic seed-42 `tiny` profile
(`data/sample/`). The capstone defaults to `tiny` (`CAPSTONE_SCALE`). Medium
and large profiles are generated locally on demand and must **stay out of git**.
Use them only for local load testing; do not commit generated CSVs.

```bash
# tiny (default, committed, fast) — what the capstone and CI use
uv run python -m banking_fraud_lab.capstone --track both --seed 42 --scale tiny --learner-facing --output data/capstone
```

If you need a larger scale for local exploration, generate it into a gitignored
directory and do not commit it.

### `Unknown scale profile` error

The named scale profiles are `tiny`, `small`, `medium`, `large`. An unknown
value raises a clear `ValueError`. Check the spelling against
`SCALE_PROFILES` / `CAPSTONE_SCALE`.

## Reproduction Of Capstone Output

### My regenerated output differs from another learner's

The capstone is deterministic for a fixed seed and scale. Always pass
`--seed 42 --scale tiny` (the documented recipe in the scenario briefs) to
reproduce the shared capstone substrate. Different seeds or scales are
expected to differ.
