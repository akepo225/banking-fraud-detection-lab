# Banking Fraud Detection Lab

Portfolio-grade training material for banking fraud detection data science.

This repo teaches fraud detection through realistic synthetic banking data, SQL feature extraction, Python modeling notebooks, public case studies, and regulatory/governance exercises. It is designed for analytics, financial-crime, product, and junior data-science practitioners who want to become stronger hands-on fraud detection data scientists.

## What This Is

- A public curriculum for banking fraud detection analytics and data science.
- A synthetic-data lab with private-banking and digital-banking fraud tracks.
- A case-library-driven learning resource connected to public regulatory and enforcement sources.
- A portfolio project showing practical fraud analytics judgment, not just model training.

## What This Is Not

- Not official training from any bank, fintech, regulator, or vendor.
- Not legal, compliance, audit, investment, or regulatory advice.
- Not based on real client data.
- Not a claim to reconstruct real fraud cases.

## Tracks

### Shared Foundations

Learners start with the synthetic banking data model, SQL feature extraction, alert lifecycle concepts, and careful model evaluation for imbalanced fraud problems.

### Private-Banking Fraud Detection

Uses the fictional **Alpine Crest Private Bank** to teach relationship-manager context, partner/role/relationship structures, accounts, transactions, alerts, and cases.

### Digital-Banking Fraud Detection

Uses the fictional **NovaBank Digital** to teach scam-to-mule flows, digital users, sessions, devices, payment beneficiaries, e-banking telemetry, and investigation outcomes.

## v0.1 Curriculum Map

- `00_foundations`: setup, data tour, schema concepts, and SQL feature extraction.
- `01_private_banking_transaction_fraud`: private-banking transaction fraud baseline.
- `02_digital_scam_to_mule`: scam-to-mule digital fraud detection baseline.
- `03_alert_governance`: alert interpretation, limitations, explainability, and governance memo.

## Planned Repository Layout

```text
banking_fraud_detection_lab/
├── data/sample/              # tiny committed sample datasets only
├── docs/
│   ├── adr/                  # architectural decision records
│   ├── cases/                # pattern-driven public case library
│   ├── regulation/           # source-linked regulatory learning notes
│   └── schema/               # data dictionary and ERD notes
├── notebooks/
│   ├── warmups/              # optional Python, pandas, SQL, sklearn refreshers
│   ├── 00_foundations/
│   ├── 01_private_banking_transaction_fraud/
│   ├── 02_digital_scam_to_mule/
│   └── 03_alert_governance/
├── sql/                      # SQLite-first SQL exercises
├── src/banking_fraud_lab/    # deterministic synthetic data and helpers
└── tests/                    # generator, schema, and notebook smoke tests
```

## Quickstart

This skeleton does not yet include the generator or notebooks. The intended setup will be:

```bash
uv sync
uv run pytest
```

## Quality Bar

- Featured notebooks must run end-to-end from a clean setup.
- Synthetic data generation must be deterministic by seed.
- SQL exercises should be first-class, not optional decoration.
- Metrics should emphasize precision/recall tradeoffs, PR-AUC, cost curves, alert capacity, and limitations.
- Public cases must separate facts from interpretation and cite public sources.

## Licensing

Code is intended to be released under the MIT License. Educational content is intended to be released under CC BY-NC 4.0. See `LICENSE.md` and `LICENSES/`.
