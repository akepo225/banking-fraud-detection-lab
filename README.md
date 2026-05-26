# Banking Fraud Detection Lab

Private pre-publication curriculum for banking fraud detection data science,
built around realistic synthetic banking data, SQL feature extraction, Python
modeling notebooks, public-source case interpretation, and governance-aware
model evaluation.

The project is designed to become a public-ready learning resource, but the
repository remains private until the v0.1 publication gate is reviewed.

## Project Promise

**Banking Fraud Detection Lab** helps practitioners build hands-on fraud
detection data science capability without using real client data or claiming to
reconstruct real events. The curriculum uses one **Realistic synthetic data
model**, then exposes **Progressive data views** so early exercises stay
approachable while later modules still use realistic joins and labels.

The v0.1 path focuses on two first-class **Fraud detection tracks**:

- **Private-banking fraud detection**, using fictional **Alpine Crest Private
  Bank** scenarios for Banking relationship, Partner, account, transaction,
  alert, and case analysis.
- **Digital-banking fraud detection**, using fictional **NovaBank Digital**
  scenarios for Client, User, session, device, beneficiary, payment, alert, and
  Scam-to-mule flow analysis.

## Target Learner

The **Target learner** is an analytics, financial-crime, product, or junior
data-science practitioner who wants to become stronger at practical fraud
detection work. The repo assumes curiosity about Python, SQL, model evaluation,
alert interpretation, and banking-domain reasoning; it is not a full beginner
Python course.

## Boundaries

This project is educational only and unaffiliated with any bank, fintech,
regulator, vendor, or public case source. It does not use real client data, does
not reconstruct real events, and does not provide legal, compliance, audit,
investment, regulatory, or professional advice.

Public cases and regulatory sources are used only as learning anchors for
Detection patterns, source discipline, and governance questions.

## v0.1 Curriculum Map

Start with the [notebook guide](notebooks/README.md), then run the featured
modules in order:

- [`00_foundations`](notebooks/00_foundations/foundations_data_tour.ipynb):
  synthetic data tour, schema concepts, SQLite loading, SQL feature extraction,
  Alert lifecycle, and fraud-aware metrics.
- [`01_private_banking_transaction_fraud`](notebooks/01_private_banking_transaction_fraud/alpine_crest_baseline.ipynb):
  Alpine Crest Private Bank transaction-fraud baseline using relationship and
  account context.
- [`02_digital_scam_to_mule`](notebooks/02_digital_scam_to_mule/novabank_scam_to_mule_baseline.ipynb):
  NovaBank Digital Scam-to-mule flow baseline using Client, User, session,
  device, beneficiary, and payment signals.
- [`03_alert_governance`](notebooks/03_alert_governance/alert_governance_memo.ipynb):
  alert interpretation, threshold tradeoffs, limitations, and a governance memo
  draft.

## Quickstart

Install dependencies, run linting, and run the full test suite:

```bash
uv sync --extra dev
uv run ruff check .
uv run pytest
```

Regenerate the committed tiny sample CSVs:

```bash
uv run python - <<'PY'
from pathlib import Path

from banking_fraud_lab import generate_minimal_banking_world

generate_minimal_banking_world(seed=42, output_dir=Path("data/sample"))
PY
```

Generate a larger local dataset by passing a named scale profile. Keep medium
and large outputs outside git.

```bash
uv run python - <<'PY'
from pathlib import Path

from banking_fraud_lab import generate_minimal_banking_world

generate_minimal_banking_world(
    seed=42,
    scale="small",
    output_dir=Path("data/local/small"),
)
PY
```

| Scale | Use | Approximate row counts |
| --- | --- | --- |
| `tiny` | Committed sample data and CI smoke tests. | 6 Clients, 12 transactions, 3 alerts. |
| `small` | Local learner exercises with larger joins. | 24 Clients, 96 transactions, 24 alerts. |
| `medium` | Laptop-feasible richer SQL and validation checks. | 90 Clients, 600 transactions, 120 alerts. |
| `large` | Optional local stress testing. | 240 Clients, 2,400 transactions, 480 alerts. |

Create a local SQLite exercise database:

```bash
uv run python -m banking_fraud_lab.create_sqlite data/sample/minimal_world.sqlite
```

Use `--scale small`, `--scale medium`, or `--scale large` for larger local
SQLite databases.

## Repository Guide

- [Schema overview](docs/schema/README.md) and
  [data dictionary](docs/schema/data_dictionary.md)
- [ERD-backed schema tour](docs/schema/erd.md) and
  [module view maps](docs/schema/module_view_maps.md)
- [Progressive data views](docs/schema/progressive_views.md)
- [Dataset quality report](docs/data_quality/dataset_quality_report.md)
- [SQLite examples](sql/README.md)
- [Evaluation metrics guide](docs/evaluation/metrics.md)
- [Case library](docs/cases/index.md)
- [Regulatory source index](docs/regulation/index.md)
- [v0.1 CI quality gates](docs/quality_gates/v0.1-ci.md)
- [Implementation roadmap](docs/ROADMAP.md)
- [Scope ADR](docs/adr/0001-broaden-scope-to-banking-fraud-detection-lab.md)
- [Contribution guide](CONTRIBUTING.md)
- [v0.1 publication checklist](docs/release/v0.1-publication-checklist.md)
- [Split license model](LICENSE.md)

## Quality Bar

- Featured notebooks run end-to-end from a clean setup on tiny data.
- Synthetic data generation is deterministic by seed.
- SQLite exercises are first-class and tested.
- Metrics emphasize precision, recall, PR-AUC, alert volume, alert capacity,
  cost curves, and limitations rather than headline accuracy.
- Case and regulatory notes separate source facts from interpretation and avoid
  imperative compliance wording.

## Split License Model

Code in `src/`, `tests/`, and `sql/` is licensed under the MIT License. See
[LICENSES/CODE-MIT.md](LICENSES/CODE-MIT.md).

Educational content in `README.md`, `CONTEXT.md`, `docs/`, `notebooks/`, and
`data/sample/` is licensed under Creative Commons Attribution-NonCommercial 4.0
International. See
[LICENSES/CONTENT-CC-BY-NC-4.0.md](LICENSES/CONTENT-CC-BY-NC-4.0.md).

The publication decision is tracked through the
[v0.1 publication checklist](docs/release/v0.1-publication-checklist.md).
