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

The same path is available from Python:

```python
from pathlib import Path

from banking_fraud_lab import create_minimal_banking_world_sqlite

connection = create_minimal_banking_world_sqlite(Path("data/sample/minimal_world.sqlite"))
```

Inspect the tables with any SQLite client:

```bash
sqlite3 data/sample/minimal_world.sqlite ".tables"
```

## Example Queries

The `sql/examples/` directory contains representative learner queries:

- `00_smoke_tables.sql` verifies that the core v0.1 tables are present.
- `01_alert_lifecycle_join.sql` joins Banking relationship, accounts,
  transactions, User, sessions, alerts, and cases through the alert lifecycle.
- `02_alert_review_window.sql` uses SQLite window functions to rank alerts
  within each Banking relationship for review-queue exercises.

These examples are smoke-tested against the generated SQLite database.

Run one example with the SQLite CLI:

```bash
sqlite3 data/sample/minimal_world.sqlite ".read sql/examples/00_smoke_tables.sql"
```

Or verify all representative examples through the project test suite:

```bash
uv run pytest tests/test_sqlite_loader.py::test_representative_sql_examples_execute_successfully
```
