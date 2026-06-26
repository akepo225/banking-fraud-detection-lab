---
title: "Independent model validation for fraud scoring"
status: draft-hitl
hitl_review_required: true
source_families:
  - model_risk_governance
pattern_ids:
  - pb_high_value_movement
  - pb_transaction_fraud
learning_use:
  - governance
  - documentation
track: cross-track governance
primary_official_sources:
  - https://www.federalreserve.gov/frrs/guidance/supervisory-guidance-on-model-risk-management.htm
linked_modules:
  - notebooks/03_alert_governance/alert_governance_memo.ipynb
  - notebooks/04_private_banking_feature_engineering/alpine_crest_supervised_baseline.ipynb
---

# Independent Model Validation For Fraud Scoring

<!-- HITL-REVIEW-REQUIRED -->

Educational use only: this source note supports fraud-detection curriculum design and is not legal or compliance advice.

## Source Scope

This note uses Federal Reserve SR 11-7 as an official reference for the independent-validation facet
of model-risk governance: the expectation that a model is challenged by a reviewer who did not
build it, asking whether its assumptions, inputs, and outputs hold up. It complements the broader
governance note by focusing on effective challenge rather than documentation. No direct quotations
are used.

## Learning Prompt

When you finish a fraud-scoring baseline, step back and act as an independent reviewer: are the
threshold, the cost parameters, and the feature assumptions defensible, or would a reviewer who did
not build the model push back? Write the questions you would expect such a reviewer to raise.

## Official Sources

- [Federal Reserve SR 11-7: Guidance on Model Risk Management](https://www.federalreserve.gov/frrs/guidance/supervisory-guidance-on-model-risk-management.htm)

## Learning Implications

Effective challenge is the habit of treating a model as something that can be wrong, stale, or
misused, and of staging a genuine second look. In the curriculum this surfaces as reviewing the
threshold rationale (why this threshold, given capacity and cost), the false-positive concentration
(which segment bears the burden), and the limitations section (what the model cannot do). The v0.7
monitoring checklist makes those review items explicit so a learner can rehearse the independent-
reviewer stance rather than only the builder stance.

## Linked Exercises

- `notebooks/03_alert_governance/alert_governance_memo.ipynb`: stages a threshold and cost review
  as a governance draft open to challenge.
- `notebooks/04_private_banking_feature_engineering/alpine_crest_supervised_baseline.ipynb`:
  exposes threshold, capacity, and cost choices for an independent reviewer.
- `notebooks/05_digital_session_and_payment_fraud/novabank_supervised_baseline.ipynb`: exposes
  the same choices for the NovaBank Digital track.

## Human Review

HITL review should confirm that framing effective challenge for an educational exercise is
appropriate and that the note does not claim the exercises undergo formal independent validation.
