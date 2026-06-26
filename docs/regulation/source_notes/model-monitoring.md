---
title: "Ongoing model monitoring for fraud scoring"
status: draft-hitl
hitl_review_required: true
source_families:
  - model_risk_governance
pattern_ids:
  - pb_high_value_movement
  - pb_transaction_fraud
learning_use:
  - alert_handling
  - governance
track: cross-track governance
primary_official_sources:
  - https://www.federalreserve.gov/frrs/guidance/supervisory-guidance-on-model-risk-management.htm
linked_modules:
  - notebooks/03_alert_governance/alert_governance_memo.ipynb
  - notebooks/04_private_banking_feature_engineering/alpine_crest_supervised_baseline.ipynb
---

# Ongoing Model Monitoring For Fraud Scoring

<!-- HITL-REVIEW-REQUIRED -->

Educational use only: this source note supports fraud-detection curriculum design and is not legal or compliance advice.

## Source Scope

This note uses Federal Reserve SR 11-7 as an official reference for the ongoing-monitoring facet of
model-risk governance: the expectation that a model is watched after it is built, so drift,
instability, and concentration are detected rather than discovered late. It extends the broader
governance note by focusing on monitoring rather than documentation. No direct quotations are used.

## Learning Prompt

After a fraud-scoring baseline is tuned, list what you would watch over time: does the score
distribution drift, do precision and recall stay stable, and do false positives pile up on one
segment? Monitoring is how a model stays trustworthy after the tuning notebook closes.

## Official Sources

- [Federal Reserve SR 11-7: Guidance on Model Risk Management](https://www.federalreserve.gov/frrs/guidance/supervisory-guidance-on-model-risk-management.htm)

## Learning Implications

Monitoring closes the loop between building and operating a model. The v0.7 monitoring checklist
covers the dimensions a reviewer should track: score drift, metric stability, false-positive
concentration, segment review, and data quality. Each draws on a concrete utility (alert scores,
evaluate_alert_scores, concentrate_false_positives, generate_dataset_quality_report) so monitoring
is not a slogan but a set of measurable checks. The habit is to decide, at build time, what would
trigger a re-review, rather than waiting for an alert to degrade silently.

## Linked Exercises

- `notebooks/03_alert_governance/alert_governance_memo.ipynb`: frames alert capacity, cost, and
  noisy labels as monitoring questions.
- `notebooks/04_private_banking_feature_engineering/alpine_crest_supervised_baseline.ipynb`:
  exposes precision, recall, and cost summaries that a monitoring review would track.
- `notebooks/05_digital_session_and_payment_fraud/novabank_supervised_baseline.ipynb`: exposes
  the same summaries for the digital track.

## Human Review

HITL review should confirm the monitoring framing fits an educational curriculum and that the note
does not claim the exercises meet a formal ongoing-monitoring standard.
