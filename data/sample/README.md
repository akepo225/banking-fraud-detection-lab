# Sample Data

Tiny sample datasets are committed here for quick starts and CI smoke tests.

Medium and large generated datasets should be created locally and kept out of git.

## Canonical Sample

These CSV files were generated with `generate_minimal_banking_world(seed=42)`.

| File | Rows | Purpose |
| --- | ---: | --- |
| `partners.csv` | 8 | Core natural and legal persons. |
| `clients.csv` | 6 | Legal customer records mapped to partners. |
| `roles.csv` | 4 | Controlled role vocabulary. |
| `partner_roles.csv` | 12 | Effective-dated partner roles in banking relationships. |
| `banking_relationships.csv` | 6 | Swiss-bank-style relationship containers. |
| `accounts.csv` | 8 | Accounts under banking relationships. |
| `transactions.csv` | 12 | Money movement events. |
| `users.csv` | 4 | Digital login identities. |
| `sessions.csv` | 7 | Digital session telemetry. |
| `payment_beneficiaries.csv` | 4 | Saved payment beneficiaries. |
| `alerts.csv` | 3 | Alert lifecycle examples. |
| `cases.csv` | 2 | Investigation cases opened from alerts. |
| `case_outcomes.csv` | 2 | Case outcome examples. |
| `protected_scenario_answer_keys.csv` | 0 | Header-only protected placeholder for future scenario labels. |

Regenerate the sample data from the repository root with:

```bash
uv run python - <<'PY'
from pathlib import Path

from banking_fraud_lab import generate_minimal_banking_world

generate_minimal_banking_world(seed=42, output_dir=Path("data/sample"))
PY
```
