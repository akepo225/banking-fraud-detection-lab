# Generate And Inspect A Minimal Banking World

Status: needs-triage

GitHub: https://github.com/akepo225/banking-fraud-detection-lab/issues/2

## Parent

GitHub issue #1: https://github.com/akepo225/banking-fraud-detection-lab/issues/1

## What to build

Build the first end-to-end **Realistic synthetic data model** tracer bullet: a deterministic generator path that creates a tiny banking world, documents the schema contract, writes sample outputs, and lets a maintainer inspect the generated entities.

This slice should prove the repo can produce and validate the core entities needed by both **Private-banking fraud detection** and **Digital-banking fraud detection** without implementing fraud scenarios yet.

## Implementation order

This is the first implementation issue. Start here before any scenario, notebook, SQL, or CI work.

## What needs to be implemented first

- Define the v0.1 table list and stable output contract.
- Implement the smallest deterministic generator entrypoint that returns or writes all required empty/minimal tables.
- Add data dictionary entries at the same time as generated tables so schema docs do not lag implementation.
- Add tests before adding scenario complexity.

## Acceptance criteria

- [ ] A deterministic generator can create a tiny sample dataset from a fixed seed.
- [ ] Generated sample data includes partners, roles, banking relationships, accounts, transactions, clients, users, sessions, payment beneficiaries, alerts, cases, and protected answer-key placeholders.
- [ ] The generated sample data is written to the expected sample-data location and is small enough to commit.
- [ ] A schema contract or data dictionary documents each generated table and its purpose.
- [ ] Tests verify deterministic output for a fixed seed.
- [ ] Tests verify the generated dataset includes the required v0.1 entities.

## Blocked by

None - can start immediately.
