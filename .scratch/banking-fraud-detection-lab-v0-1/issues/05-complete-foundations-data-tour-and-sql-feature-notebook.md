# Complete Foundations Data Tour And SQL Feature Notebook

Status: needs-triage

GitHub: https://github.com/akepo225/banking-fraud-detection-lab/issues/6

## Parent

GitHub issue #1: https://github.com/akepo225/banking-fraud-detection-lab/issues/1

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

- GitHub issue #4: https://github.com/akepo225/banking-fraud-detection-lab/issues/4
- GitHub issue #5: https://github.com/akepo225/banking-fraud-detection-lab/issues/5
