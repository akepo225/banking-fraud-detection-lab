# Detect Alpine Crest Private-Banking Transaction Fraud

Status: ready-for-agent

GitHub: https://github.com/akepo225/banking-fraud-detection-lab/issues/7

## Parent

GitHub issue #1: https://github.com/akepo225/banking-fraud-detection-lab/issues/1

## What to build

Add the first **Alpine Crest Private Bank** scenario: private-banking transaction fraud detection using relationship, account, counterparty, transaction, and relationship-manager context.

This slice should generate the scenario, expose learner-facing views, build features, train a baseline model, and interpret alerts with fraud-appropriate metrics.

## Implementation order

Start after lifecycle, SQLite, and metrics are available. This can run in parallel with issue 07 after shared dependencies are complete.

## What needs to be implemented first

- Define the smallest private-banking transaction-fraud pattern to inject.
- Add scenario metadata and protected answer keys before learner-facing features.
- Add learner-facing **Progressive data views** for private-banking features.
- Build the baseline notebook only after scenario prevalence and referential-integrity tests pass.

## Acceptance criteria

- [ ] Scenario injection supports a private-banking transaction-fraud pattern with configurable prevalence.
- [ ] Generated data includes the relevant **Partner**, **Role**, **Banking relationship**, account, transaction, and relationship-manager context.
- [ ] Learner-facing views expose enough fields to build private-banking transaction-fraud features without exposing protected answer keys.
- [ ] A notebook trains a baseline model or scoring rule for the scenario.
- [ ] The notebook reports alert-aware metrics and threshold tradeoffs.
- [ ] Tests verify scenario prevalence ranges and referential integrity for private-banking scenario records.

## Blocked by

- GitHub issue #3: https://github.com/akepo225/banking-fraud-detection-lab/issues/3
- GitHub issue #4: https://github.com/akepo225/banking-fraud-detection-lab/issues/4
- GitHub issue #5: https://github.com/akepo225/banking-fraud-detection-lab/issues/5
