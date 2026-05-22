# Enforce v0.1 Quality Gates In CI

Status: needs-triage

GitHub: https://github.com/akepo225/banking-fraud-detection-lab/issues/12

## Parent

GitHub issue #1: https://github.com/akepo225/banking-fraud-detection-lab/issues/1

## What to build

Wire the v0.1 quality gates into a lightweight CI path. CI should run fast checks by default and prove that generated data, schema contracts, SQL loading, case/regulatory validation, and featured notebooks remain healthy on tiny sample data.

## Implementation order

Start after all v0.1 generated-data, notebook, case-library, and regulatory-source validation paths exist.

## What needs to be implemented first

- Make the local test command pass before expanding CI.
- Add CI for linting and Python tests first.
- Add notebook smoke checks only after featured notebooks are stable.
- Keep CI fast by using tiny sample data.

## Acceptance criteria

- [ ] CI runs linting and Python tests on a clean checkout.
- [ ] CI covers generator determinism and required entity generation.
- [ ] CI covers referential integrity and scenario prevalence ranges.
- [ ] CI covers schema/data-dictionary alignment and SQLite loading smoke tests.
- [ ] CI covers case-library and regulatory-source validation.
- [ ] CI runs notebook smoke tests for the featured v0.1 notebooks on tiny sample data, including the alert-governance notebook.

## Blocked by

- GitHub issue #7: https://github.com/akepo225/banking-fraud-detection-lab/issues/7
- GitHub issue #8: https://github.com/akepo225/banking-fraud-detection-lab/issues/8
- GitHub issue #9: https://github.com/akepo225/banking-fraud-detection-lab/issues/9
- GitHub issue #10: https://github.com/akepo225/banking-fraud-detection-lab/issues/10
- GitHub issue #11: https://github.com/akepo225/banking-fraud-detection-lab/issues/11
