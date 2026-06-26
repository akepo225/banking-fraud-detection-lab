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

The curriculum is organized around two first-class **Fraud detection tracks**,
each developed as a depth track beyond the foundations and alert-governance
modules:

- **Private-banking fraud detection**, using fictional **Alpine Crest Private
  Bank** scenarios for Banking relationship, Partner, account, transaction,
  alert, and case analysis.
- **Digital-banking fraud detection**, using fictional **NovaBank Digital**
  scenarios for Client, User, session, device, beneficiary, payment, alert, and
  Scam-to-mule flow analysis.

A **Detection-pattern-first case library** and a **learning-use-first
regulatory source index** provide supporting context and source discipline for
the exercises in every module.

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

## Curriculum Map

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
- [`04_private_banking_feature_engineering`](notebooks/04_private_banking_feature_engineering/alpine_crest_feature_engineering.ipynb):
  Private-banking feature engineering and supervised threshold tuning for Alpine
  Crest relationship, account, counterparty, and velocity context.
- [`05_digital_session_and_payment_fraud`](notebooks/05_digital_session_and_payment_fraud/novabank_feature_engineering.ipynb):
  NovaBank Digital session and payment fraud feature engineering, supervised
  baseline, and alert triage.
- [`06_graph_network_fraud`](notebooks/06_graph_network_fraud/alpine_crest_graph_investigation.ipynb):
  v0.6 graph and network analytics. Build a NetworkX graph from the canonical
  generated tables and investigate relationship and transaction networks
  (beneficial ownership, shared counterparties, related entities, circular
  funds movement). Graph evidence extends, not replaces, the tabular
  investigation.
- [`07_interpretability_model_risk`](notebooks/07_interpretability_model_risk/alpine_crest_interpretability.ipynb):
  v0.7 interpretability, governance, and model-risk. Explain model behaviour,
  choose thresholds, document limitations, and write governance-ready summaries
  (per-alert "why", feature importance, partial-dependence, threshold selection,
  false-positive concentration, model documentation).
- [`08_production_monitoring_patterns`](notebooks/08_production_monitoring_patterns/alpine_crest_monitoring.ipynb):
  v0.8 production-monitoring patterns. Turn a fitted score into the production
  monitoring tables (score, threshold, alert_decision, reviewer_action,
  audit_event), inspect an alert queue and its aging, summarise operational
  metrics, run score/feature drift and data-quality checks, and trace a
  monitoring anomaly back to Client / Banking relationship / Detection pattern
  records.

Optional canonical-data refreshers for Python, pandas, SQL, and sklearn live in
[`00_foundations/warmups`](notebooks/00_foundations/warmups/). They are outside
the required core module sequence.

## Quickstart

Install dependencies, run linting, and run the full test suite:

```bash
uv sync --extra dev
uv run ruff check .
uv run pytest
```

Regenerate the committed tiny sample CSVs with a command that works in Bash and
PowerShell:

```bash
uv run python -c "from pathlib import Path; from banking_fraud_lab import generate_minimal_banking_world; generate_minimal_banking_world(seed=42, output_dir=Path('data/sample'))"
```

Generate a larger local dataset by passing a named scale profile. Keep medium
and large outputs outside git.

```bash
uv run python -c "from pathlib import Path; from banking_fraud_lab import generate_minimal_banking_world; generate_minimal_banking_world(seed=42, scale='small', output_dir=Path('data/local/small'))"
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
- [Private-banking feature library](docs/schema/features.md)
- [Optional canonical-data warm-ups](notebooks/00_foundations/warmups/)
- [Dataset quality report](docs/data_quality/dataset_quality_report.md)
- [SQLite examples](sql/README.md)
- [Evaluation metrics guide](docs/evaluation/metrics.md)
- [Case library](docs/cases/index.md) (organized Detection-pattern-first)
- [Regulatory source index](docs/regulation/index.md) (organized by learning
  use: analytics question, control, documentation, explainability, alert
  handling, governance)
- [v0.1 CI quality gates](docs/quality_gates/v0.1-ci.md)
- [Implementation roadmap](docs/ROADMAP.md)
- [Scope ADR](docs/adr/0001-broaden-scope-to-banking-fraud-detection-lab.md)
- [Contribution guide](CONTRIBUTING.md)
- [v0.1 publication checklist](docs/release/v0.1-publication-checklist.md)
- [v0.5 acceptance review](docs/release/v0.5-acceptance-review.md)
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
