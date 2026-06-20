# Private-Banking Feature Library

The v0.3 private-banking feature library defines reusable feature-family
metadata and deterministic pandas calculators for Alpine Crest Private Bank
analytics. The library lives in `src/banking_fraud_lab/features/` and is
intended to be consumed by notebooks, tests, and SQLite exercises rather than
duplicated in notebook cells.

Each feature family records:

- `family_id`: stable feature-family identifier.
- `detection_pattern_id`: Detection pattern from `PATTERN_IDS`.
- `source_tables`: canonical tables required to calculate the feature.
- `source_columns`: table-qualified lineage columns.
- `output_columns`: learner-facing feature columns produced by the calculator.

## Feature Families

| Family ID | Detection pattern ID | Source tables | Output columns |
| --- | --- | --- | --- |
| `amount_to_aum` | `pb_high_value_movement` | `transactions`, `accounts`, `banking_relationships` | `amount_to_aum_ratio` |
| `amount_to_relationship_baseline` | `pb_high_value_movement` | `transactions`, `accounts`, `banking_relationships` | `relationship_amount_baseline_chf`, `amount_to_relationship_baseline_ratio` |
| `new_counterparty` | `pb_transaction_fraud` | `transactions`, `payment_beneficiaries` | `counterparty_age_days`, `is_new_counterparty` |
| `off_hours_activity` | `pb_transaction_fraud` | `transactions` | `booked_hour`, `is_off_hours` |
| `cross_border_movement` | `pb_high_value_movement` | `transactions`, `accounts`, `banking_relationships`, `clients`, `partners`, `payment_beneficiaries` | `partner_country`, `beneficiary_account_country`, `beneficiary_bank_country`, `is_cross_border` |
| `velocity_change` | `pb_transaction_fraud` | `transactions`, `accounts`, `banking_relationships` | `relationship_txn_count_7d`, `relationship_amount_sum_7d_chf`, `relationship_txn_count_30d`, `relationship_amount_sum_30d_chf`, `txn_count_7d_to_30d_ratio`, `amount_7d_to_30d_ratio` |
| `rm_concentration` | `pb_transaction_fraud` | `alerts`, `cases`, `banking_relationships` | `rm_alert_count`, `rm_case_count`, `rm_alert_share` |

## Pattern Mapping Rationale

`amount_to_aum`, `amount_to_relationship_baseline`, and
`cross_border_movement` map to `pb_high_value_movement` because they explain
transaction size and destination context within a Banking relationship.

`new_counterparty`, `off_hours_activity`, `velocity_change`, and
`rm_concentration` map to `pb_transaction_fraud` because they describe first
observed or recently created counterparties, timing, repetition, and assignment
concentration that support transaction-fraud review.

## Digital-Banking Feature Families

The v0.4 digital-banking feature library mirrors the private-banking shape for
NovaBank Digital analytics. Every family uses the `db_` prefix and maps to one
of the three existing digital Detection pattern IDs (`digital_scam_to_mule`,
`new_beneficiary_payment`, or `session_payment_velocity`). No new pattern IDs
are introduced.

| Family ID | Detection pattern ID | Source tables | Output columns |
| --- | --- | --- | --- |
| `db_session_risk` | `session_payment_velocity` | `transactions`, `sessions`, `accounts`, `banking_relationships`, `users` | `db_is_vpn_or_proxy`, `db_asn_risk_score`, `db_is_high_risk_network`, `db_is_password_sms_auth` |
| `db_beneficiary_novelty` | `new_beneficiary_payment` | `transactions`, `payment_beneficiaries` | `db_beneficiary_age_days`, `db_is_new_beneficiary` |
| `db_payment_velocity` | `session_payment_velocity` | `transactions`, `suspicious_activities`, `sessions`, `accounts` | `db_session_payment_count`, `db_session_payment_amount_chf`, `db_session_max_payment_chf` |
| `db_account_age` | `digital_scam_to_mule` | `transactions`, `accounts` | `db_account_age_days`, `db_is_early_life_account` |
| `db_shared_device` | `digital_scam_to_mule` | `sessions`, `users`, `suspicious_activities`, `transactions` | `db_device_user_count`, `db_is_shared_device` |
| `db_pass_through` | `digital_scam_to_mule` | `transactions`, `accounts`, `payment_beneficiaries` | `db_prior_credit_amount_chf`, `db_hours_since_prior_credit`, `db_is_rapid_pass_through` |
| `db_risky_channel` | `new_beneficiary_payment` | `transactions`, `payment_beneficiaries` | `db_is_mobile_app_channel`, `db_is_beneficiary_country_risky` |

### Digital Pattern Mapping Rationale

`db_session_risk` and `db_payment_velocity` map to `session_payment_velocity`
because they describe session-level telemetry and payment velocity that support
elevated session review.

`db_beneficiary_novelty` and `db_risky_channel` map to `new_beneficiary_payment`
because they describe recently added or updated beneficiaries and risky channel
or destination-country context for new-beneficiary review.

`db_account_age`, `db_shared_device`, and `db_pass_through` map to
`digital_scam_to_mule` because they describe early-life accounts, shared device
usage, and rapid pass-through behavior typical of scam-to-mule flows.

## Python Path

Use `build_private_banking_features()` when a notebook needs the complete
transaction-level feature frame:

```python
from banking_fraud_lab import (
    build_private_banking_features,
    generate_private_banking_transaction_fraud_world,
)

tables = generate_private_banking_transaction_fraud_world(seed=42, scale="tiny")
features = build_private_banking_features(tables)
features.head()
```

Use individual calculators when an exercise focuses on one family:

```python
from banking_fraud_lab.features import calculate_amount_to_aum_features

amount_features = calculate_amount_to_aum_features(
    tables["transactions"],
    tables["accounts"],
    tables["banking_relationships"],
)
```

The merged private-banking feature frame is scoped to Alpine Crest Private Bank
and excludes `protected_scenario_answer_keys`.

The featured notebook at
`notebooks/04_private_banking_feature_engineering/alpine_crest_feature_engineering.ipynb`
uses this builder as the Python path for private-banking feature engineering.
The supervised-baseline notebook at
`notebooks/04_private_banking_feature_engineering/alpine_crest_supervised_baseline.ipynb`
uses the same builder as its model input path.

## SQLite Path

The SQLite examples calculate representative private-banking features directly
against the learner database:

- `sql/examples/06_private_banking_value_features.sql` covers
  `amount_to_aum` and `amount_to_relationship_baseline`.
- `sql/examples/07_private_banking_context_features.sql` covers
  `off_hours_activity`, `cross_border_movement`, and `velocity_change`.
- `sql/examples/08_private_banking_relationship_features.sql` covers
  `new_counterparty` and `rm_concentration`.

Create a learner database and run an exercise with:

```bash
uv run python -m banking_fraud_lab.create_sqlite data/sample/minimal_world.sqlite
uv run python -m banking_fraud_lab.run_sql data/sample/minimal_world.sqlite sql/examples/06_private_banking_value_features.sql
```

The feature-engineering notebook also runs these SQL examples against an
in-memory learner-facing SQLite database so the Python and SQL paths remain
aligned.

## Digital-Banking Python And SQLite Path

Use `build_digital_banking_features()` for the complete NovaBank Digital
transaction-level feature frame:

```python
from banking_fraud_lab import (
    build_digital_banking_features,
    generate_digital_fraud_scenarios_world,
)

tables = generate_digital_fraud_scenarios_world(seed=42, scale="tiny")
features = build_digital_banking_features(tables)
features.head()
```

Individual `db_` calculators (for example `calculate_db_session_risk_features`)
follow the same one-family-per-function shape as the private-banking library.

The merged digital feature frame is scoped to NovaBank Digital transactions and
excludes `protected_scenario_answer_keys`. The v0.4 digital-banking SQLite
exercises calculate representative features directly against the learner database:

- `sql/examples/09_digital_session_channel_features.sql` covers `db_session_risk`
  and `db_risky_channel`.
- `sql/examples/10_digital_beneficiary_passthrough_features.sql` covers
  `db_beneficiary_novelty` and `db_pass_through`.
- `sql/examples/11_digital_velocity_account_features.sql` covers
  `db_payment_velocity`, `db_account_age`, and `db_shared_device`.
