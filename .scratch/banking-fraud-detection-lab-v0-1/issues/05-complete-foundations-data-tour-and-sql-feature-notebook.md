# Complete Foundations Data Tour And SQL Feature Notebook

Status: needs-triage

## Parent

`.scratch/banking-fraud-detection-lab-v0-1/PRD.md`

## What to build

Deliver the first learner-facing notebook path through setup, data generation, schema tour, SQLite loading, SQL feature extraction, and alert-aware metric interpretation.

This slice should be demoable as the shared foundation before the private-banking and digital-banking tracks branch.

## Implementation order

Start after generated data, SQLite loading, and alert-aware metrics exist. This is the first learner-facing notebook issue.

## What needs to be implemented first

- Create the notebook outline around learner tasks, not code internals.
- Use tiny sample data first so notebook smoke tests stay fast.
- Demonstrate generated data inspection, SQLite loading, SQL feature extraction, and alert-aware metric interpretation in one path.
- Add the smoke test before expanding narrative content.

## Acceptance criteria

- [ ] A foundations notebook runs end-to-end from a clean checkout using tiny sample data or deterministic generation.
- [ ] The notebook explains the **Realistic synthetic data model** and **Progressive data views**.
- [ ] The notebook demonstrates SQLite loading and SQL feature extraction.
- [ ] The notebook introduces the **Alert lifecycle** with generated examples.
- [ ] The notebook uses the shared alert-aware metrics utility for at least one simple scoring example.
- [ ] A notebook smoke test verifies successful execution on tiny sample data.

## Blocked by

- `.scratch/banking-fraud-detection-lab-v0-1/issues/03-query-generated-data-through-sqlite.md`
- `.scratch/banking-fraud-detection-lab-v0-1/issues/04-produce-alert-aware-metrics-report-from-generated-cases.md`
