# Schema Notes

The v0.1 data model will be realistic enough to teach durable banking analytics habits while remaining approachable through progressive views.

## Core Tables

The v0.1 tracer bullets implement the following generated CSV tables and the matching schema contract in `src/banking_fraud_lab/schema/tables.py`.

- `partners`
- `clients`
- `roles`
- `partner_roles`
- `banking_relationships`
- `accounts`
- `transactions`
- `users`
- `sessions`
- `payment_beneficiaries`
- `suspicious_activities`
- `alerts`
- `cases`
- `case_outcomes`
- `protected_scenario_answer_keys`

See `data_dictionary.md` for the v0.1 table purposes, columns, types, and relationships.

## Generator Scale Profiles

The canonical generator accepts named `tiny`, `small`, `medium`, and `large`
scale profiles. The `tiny` profile is the committed sample and CI smoke-test
surface. The `small` and `medium` profiles are deterministic local learner
profiles for larger joins and validation checks. The `large` profile is an
optional local stress-test profile and generated outputs should stay out of git.

Approximate row counts for `seed=42`:

| Scale | Clients | Transactions | Alerts |
| --- | ---: | ---: | ---: |
| `tiny` | 6 | 12 | 3 |
| `small` | 24 | 96 | 24 |
| `medium` | 90 | 600 | 120 |
| `large` | 240 | 2,400 | 480 |

## Design Rules

- Use exact decimal precision for money.
- Store original amount and currency plus CHF-normalized amount where relevant.
- Model the alert lifecycle explicitly.
- Keep scenario answer keys out of learner-facing views by default.
- Use SQLite-first SQL exercises, with optional PostgreSQL later.
