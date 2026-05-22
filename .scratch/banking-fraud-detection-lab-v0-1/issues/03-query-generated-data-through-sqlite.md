# Query Generated Data Through SQLite

Status: needs-triage

GitHub: https://github.com/akepo225/banking-fraud-detection-lab/issues/4

## Parent

GitHub issue #1: https://github.com/akepo225/banking-fraud-detection-lab/issues/1

## What to build

Create the SQLite-first learner path for querying generated data. A learner should be able to load the generated banking world into SQLite and run representative joins and window queries across the core tables.

This slice proves SQL is first-class before modeling notebooks are built.

## Implementation order

Start after issues 01 and 02 establish generated entities and lifecycle semantics.

## What needs to be implemented first

- Implement a loader that creates a SQLite database from generated tables.
- Add a minimal SQL smoke query before adding learner exercises.
- Add representative joins across core entities.
- Add one window-function query that can later become a notebook exercise.

## Acceptance criteria

- [ ] Generated tables can be loaded into a local SQLite database.
- [ ] The SQLite database includes the core v0.1 tables and relationships needed for foundations exercises.
- [ ] Representative SQL examples cover joins across relationships, accounts, transactions, users, sessions, alerts, and cases.
- [ ] Representative SQL examples include at least one window-function query for feature extraction or alert review.
- [ ] SQL smoke tests verify that the database loads and representative queries execute successfully.
- [ ] Documentation explains how learners should create and inspect the SQLite database.

## Blocked by

- GitHub issue #2: https://github.com/akepo225/banking-fraud-detection-lab/issues/2
- GitHub issue #3: https://github.com/akepo225/banking-fraud-detection-lab/issues/3
