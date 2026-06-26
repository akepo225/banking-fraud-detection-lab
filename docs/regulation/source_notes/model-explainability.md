---
title: "Model explainability for fraud scoring"
status: draft-hitl
hitl_review_required: true
source_families:
  - model_risk_governance
pattern_ids:
  - pb_high_value_movement
  - pb_transaction_fraud
learning_use:
  - explainability
  - governance
track: cross-track governance
primary_official_sources:
  - https://www.federalreserve.gov/frrs/guidance/supervisory-guidance-on-model-risk-management.htm
linked_modules:
  - notebooks/04_private_banking_feature_engineering/alpine_crest_supervised_baseline.ipynb
---

# Model Explainability For Fraud Scoring

<!-- HITL-REVIEW-REQUIRED -->

Educational use only: this source note supports fraud-detection curriculum design and is not legal or compliance advice.

## Source Scope

This note uses Federal Reserve SR 11-7 as an official model-risk reference for the explainability
facet of model governance: the expectation that a model's behaviour can be connected back to its
inputs, data signals, and case notes so a reviewer can understand why a given score or alert was
produced. It complements the broader model-risk governance note by focusing on explanation rather
than documentation or validation. No direct quotations are used.

## Learning Prompt

When you read an alert score in the Alpine Crest Private Bank or NovaBank Digital notebooks, ask
which feature inputs drove it and whether those inputs map cleanly to a Detection pattern id.
Feature importance and partial-dependence explanations are inspection aids: they make behaviour
inspectable, they do not prove the model is correct.

## Official Sources

- [Federal Reserve SR 11-7: Guidance on Model Risk Management](https://www.federalreserve.gov/frrs/guidance/supervisory-guidance-on-model-risk-management.htm)

## Learning Implications

Explainability in this curriculum means turning a fitted score into a traceable story: per-alert
feature contributions mapped to a Detection pattern, a partial-dependence grid showing how one
feature moves the score, and a connection back to the case and graph evidence from earlier
modules. The habit to build is that a score without an explanation is incomplete for review, and
that an explanation is not the same as a guarantee. The v0.7 interpretability module provides the
utilities (feature-importance extraction, partial-dependence / ICE grids) that operationalise this
habit for both the private-banking and digital-banking tracks.

## Linked Exercises

- `notebooks/04_private_banking_feature_engineering/alpine_crest_supervised_baseline.ipynb`:
  connects fitted coefficients to Detection patterns as a first explainability step.
- `notebooks/05_digital_session_and_payment_fraud/novabank_supervised_baseline.ipynb`: applies
  the same coefficient-to-pattern reasoning for NovaBank Digital.

The forthcoming `notebooks/07_interpretability_model_risk/` module will build per-alert
explanations, feature importance, and partial-dependence grids tied to pattern ids.

## Human Review

HITL review should confirm that framing SR 11-7 around explainability is appropriate for an
educational curriculum and that the note does not imply the exercises meet a formal validation
standard.
