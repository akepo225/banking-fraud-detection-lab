# Sample Data

Tiny sample datasets are committed here for quick starts and CI smoke tests.

Medium and large generated datasets should be created locally and kept out of git.

## Scale Profiles

The generator supports named scale profiles through the `scale` parameter:

| Scale | Intended use | Approximate rows |
| --- | --- | --- |
| `tiny` | Committed sample data and CI smoke tests. | 6 Clients, 12 transactions, 3 alerts. |
| `small` | Local learner exercises with larger joins. | 24 Clients, 96 transactions, 24 alerts. |
| `medium` | Laptop-feasible richer SQL and validation checks. | 90 Clients, 600 transactions, 120 alerts. |
| `large` | Optional local stress testing. | 240 Clients, 2,400 transactions, 480 alerts. |

Use the larger profiles for local experimentation only, for example:

```bash
uv run python -c "from pathlib import Path; from banking_fraud_lab import generate_minimal_banking_world; generate_minimal_banking_world(seed=42, scale='small', output_dir=Path('data/local/small'))"
```

## Canonical Sample

These CSV files were generated with `generate_minimal_banking_world(seed=42, scale="tiny")`.

| File | Rows | Purpose |
| --- | ---: | --- |
| `partners.csv` | 8 | Core natural and legal persons. |
| `clients.csv` | 6 | Client records mapped to partners. |
| `roles.csv` | 4 | Controlled role vocabulary. |
| `partner_roles.csv` | 12 | Effective-dated partner roles in banking relationships. |
| `banking_relationships.csv` | 6 | Swiss-bank-style relationship containers. |
| `relationship_manager_history.csv` | 6 | Effective-dated relationship-manager assignment history. |
| `accounts.csv` | 8 | Accounts under banking relationships. |
| `transactions.csv` | 12 | Money movement events. |
| `users.csv` | 6 | Digital login identities. |
| `sessions.csv` | 7 | Digital session telemetry. |
| `payment_beneficiaries.csv` | 10 | Saved beneficiaries and private-banking counterparties. |
| `suspicious_activities.csv` | 3 | Suspicious activity observations before alert generation. |
| `alerts.csv` | 3 | Alerts generated from suspicious activities. |
| `cases.csv` | 2 | Investigation cases opened from alerts. |
| `case_outcomes.csv` | 2 | Case outcome examples. |
| `protected_scenario_answer_keys.csv` | 3 | Protected labels excluded from learner-facing views. |

Regenerate the sample data from the repository root with:

```bash
uv run python -c "from pathlib import Path; from banking_fraud_lab import generate_minimal_banking_world; generate_minimal_banking_world(seed=42, scale='tiny', output_dir=Path('data/sample'))"
```
