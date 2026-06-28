# SQL Exercises

SQL exercises are SQLite-first for zero-friction setup. The generated banking
world can be loaded into a local SQLite database with the same table names and
foreign key relationships used by the Python schema contract.

## Create A Learner Database

From the repository root:

```bash
uv run python -m banking_fraud_lab.create_sqlite data/sample/minimal_world.sqlite
```

This creates a learner-facing database that excludes
`protected_scenario_answer_keys` by default. To include protected scenario
answer keys for internal validation, pass `--include-protected`.

Pass `--scale small`, `--scale medium`, or `--scale large` to create a larger
local learner database from the same canonical data model.

The same path is available from Python:

```python
from pathlib import Path

from banking_fraud_lab import create_minimal_banking_world_sqlite

connection = create_minimal_banking_world_sqlite(
    Path("data/sample/minimal_world.sqlite"),
    scale="tiny",
)
```

Inspect the tables through the project SQL runner, which uses Python's built-in
SQLite support and does not require a separate `sqlite3` command-line install:

```bash
uv run python -m banking_fraud_lab.run_sql data/sample/minimal_world.sqlite sql/examples/00_smoke_tables.sql
```

Generated SQLite databases also expose foundation Progressive data views:
`foundation_client_relationships` and `foundation_alert_lifecycle`. Their
source tables, columns, and learner purposes are documented in
`docs/schema/progressive_views.md`.

## Example Queries

The `sql/examples/` directory contains representative learner queries:

- `00_smoke_tables.sql` verifies that the core v0.1 tables are present.
- `01_alert_lifecycle_join.sql` joins Banking relationship, accounts,
  transactions, User, sessions, alerts, and cases through the alert lifecycle.
- `02_alert_review_window.sql` uses SQLite window functions to rank alerts
  within each Banking relationship for review-queue exercises.
- `03_client_relationship_cohorts.sql` performs cohort-style analysis by
  Client segment and KYC risk band through the
  `foundation_client_relationships` Progressive data view.
- `04_progressive_alert_queue.sql` inspects an alert queue through the
  `foundation_alert_lifecycle` Progressive data view.
- `05_transaction_feature_extraction.sql` covers feature extraction by building
  transaction-level features from canonical tables plus foundation Progressive
  data views.
- `06_private_banking_value_features.sql` calculates Alpine Crest Private Bank
  amount-to-AUM and amount-to-relationship-baseline features for the
  `pb_high_value_movement` Detection pattern.
- `07_private_banking_context_features.sql` calculates off-hours,
  cross-border, and velocity features for `pb_transaction_fraud` and
  `pb_high_value_movement` Detection patterns.
- `08_private_banking_relationship_features.sql` calculates new-counterparty
  and relationship-manager concentration features for the
  `pb_transaction_fraud` Detection pattern.
- `09_digital_session_channel_features.sql` calculates NovaBank Digital session
  risk, risky channel, and beneficiary-country features for the
  `session_payment_velocity` and `new_beneficiary_payment` Detection patterns.
- `10_digital_beneficiary_passthrough_features.sql` calculates NovaBank Digital
  beneficiary-novelty and rapid pass-through features for the
  `digital_scam_to_mule` and `new_beneficiary_payment` Detection patterns.
- `11_digital_velocity_account_features.sql` calculates NovaBank Digital
  session-velocity, account-age, and shared-device features for the
  `digital_scam_to_mule` and `session_payment_velocity` Detection patterns.
- [`12_capstone_private_banking.sql`](examples/12_capstone_private_banking.sql) is the
  v0.9 capstone private-banking
  investigation view: relationship / account / counterparty / relationship-manager
  / velocity context for Alpine Crest Private Bank debits, tied to
  `pb_high_value_movement` / `pb_transaction_fraud` Detection patterns and Alert
  lifecycle lineage. Generate the matching capstone dataset first:

  ```bash
  uv run python -m banking_fraud_lab.capstone --track private_banking --seed 42 \
    --scale tiny --learner-facing --output data/capstone/private_banking
  ```
- [`13_capstone_digital_banking.sql`](examples/13_capstone_digital_banking.sql) is the
  v0.9 capstone digital-banking
  investigation view: session / device / beneficiary / pass-through / account-age
  context for NovaBank Digital debits, tied to `digital_scam_to_mule` /
  `new_beneficiary_payment` Detection patterns and Alert lifecycle lineage. Generate
  the matching capstone dataset first:

  ```bash
  uv run python -m banking_fraud_lab.capstone --track digital_banking --seed 42 \
    --scale tiny --learner-facing --output data/capstone/digital_banking
  ```

The capstone CSVs are generated as flat files. Load them into a learner-facing
SQLite database before running the capstone SQL examples — for example, from
Python:

```python
from pathlib import Path
from banking_fraud_lab import load_tables_to_sqlite
from banking_fraud_lab.capstone import generate_learner_facing_capstone_private_banking_world

tables = generate_learner_facing_capstone_private_banking_world(seed=42, scale="tiny")
load_tables_to_sqlite(tables, Path("data/capstone/private_banking.sqlite"))
```

The v0.3 feature-engineering notebook at
`../notebooks/04_private_banking_feature_engineering/alpine_crest_feature_engineering.ipynb`
loads examples 06-08 into an in-memory learner-facing SQLite database and
compares representative SQL outputs with the Python feature library. The v0.4
digital-banking notebooks under
`../notebooks/05_digital_session_and_payment_fraud/` consume examples 09-11
alongside the `db_`-prefixed Python feature library.

These examples are smoke-tested against the generated SQLite database and return
meaningful rows against the default learner-facing tiny data.

Run one example with the cross-platform project SQL runner:

```bash
uv run python -m banking_fraud_lab.run_sql data/sample/minimal_world.sqlite sql/examples/04_progressive_alert_queue.sql
```

If the SQLite CLI is installed locally, the same example can also be run with
`sqlite3`:

```bash
sqlite3 data/sample/minimal_world.sqlite ".read sql/examples/04_progressive_alert_queue.sql"
```

Or verify all representative examples through the project test suite:

```bash
uv run pytest tests/test_sqlite_loader.py::test_representative_sql_examples_execute_successfully
```
