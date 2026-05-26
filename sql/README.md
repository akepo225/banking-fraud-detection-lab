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
