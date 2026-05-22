# Produce An Alert-Aware Metrics Report From Generated Cases

Status: needs-triage

GitHub: https://github.com/akepo225/banking-fraud-detection-lab/issues/5

## Parent

GitHub issue #1: https://github.com/akepo225/banking-fraud-detection-lab/issues/1

## What to build

Build an evaluation utility that turns generated case and score data into a fraud-appropriate metrics report. The report should emphasize alert capacity, precision/recall, PR-AUC, cost curves, and limitations rather than headline accuracy.

This slice gives later notebooks a shared, tested way to discuss model performance and operational tradeoffs.

## Implementation order

Start after issue 02 defines alert and case outcome semantics. This can run in parallel with issue 03 after issue 02 is complete.

## What needs to be implemented first

- Define the minimal score/input format expected by the metrics utility.
- Implement deterministic metric calculations on small in-memory examples.
- Add threshold and alert-capacity summaries before notebook integration.
- Add limitation-summary output so notebooks do not invent their own language.

## Acceptance criteria

- [ ] The evaluation utility can consume generated labels, alert/case outcomes, and model-like scores.
- [ ] The output includes precision, recall, PR-AUC, alert volume, alert capacity, and threshold summaries.
- [ ] The output includes cost-curve or cost-summary fields for investigation cost, false positives, and missed fraud.
- [ ] The output includes a limitation-aware summary suitable for notebooks.
- [ ] Tests verify metric outputs on known confusion-matrix or score-distribution cases.
- [ ] Documentation states why simplistic accuracy claims are out of scope.

## Blocked by

- GitHub issue #3: https://github.com/akepo225/banking-fraud-detection-lab/issues/3
