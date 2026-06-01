# Schema Notes

The v0.1/v0.2 foundation data model is realistic enough to teach durable
banking analytics habits while remaining approachable through Progressive data
views.

## Core Tables

The v0.1/v0.2 foundation implements the following generated CSV tables and the
matching schema contract in `src/banking_fraud_lab/schema/tables.py`.

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

See `data_dictionary.md` for the v0.1/v0.2 foundation table purposes, columns,
types, and relationships.

See `erd.md` for the v0.2 ERD-backed schema tour across canonical tables and
key relationships.

See `progressive_views.md` for the foundation Progressive data view contracts,
learner purposes, source tables, and SQLite view surfaces.

See `module_view_maps.md` for the `00_foundations` view map that traces
Progressive data views back to canonical tables.

See `detection_patterns.md` for the stable detection pattern identifiers
used across the curriculum for cross-module references, case-pack linking,
and Progressive data view grouping.

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

## Temporal Semantics

v0.2 generated data is bounded by a fixed dataset snapshot timestamp and keeps
foundation lifecycle timestamps ordered:

- KYC risk dates start with `partners.kyc_risk_effective_from` and are reviewed
  at `partners.kyc_risk_reviewed_at`.
- Relationship-manager assignment is effective at
  `banking_relationships.relationship_manager_assigned_at`.
- User authorization windows use `users.authorized_from` and
  `users.authorized_to`.
- Account status windows use `accounts.status_effective_from` and
  `accounts.status_effective_to`.
- Alert, case, and outcome ordering follows transaction booking, suspicious
  activity detection, alert generation, case opening, case closure, outcome
  decision, and outcome recording.

## Design Rules

- Use exact decimal precision for money.
- Store original amount and currency plus CHF-normalized amount where relevant.
- Model the alert lifecycle explicitly.
- Keep historical timestamps on or before the dataset snapshot timestamp.
- Keep scenario answer keys out of learner-facing views by default.
- Use SQLite-first SQL exercises, with optional PostgreSQL later.
