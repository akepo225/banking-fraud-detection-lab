---
title: "Model-risk governance for fraud scoring"
status: draft-hitl
hitl_review_required: true
source_families:
  - model_risk_governance
track: cross-track governance
primary_official_sources:
  - https://www.federalreserve.gov/supervisionreg/srletters/sr1107.htm
linked_modules:
  - notebooks/00_foundations/foundations_data_tour.ipynb
  - notebooks/01_private_banking_transaction_fraud/alpine_crest_baseline.ipynb
  - notebooks/02_digital_scam_to_mule/novabank_scam_to_mule_baseline.ipynb
  - notebooks/03_alert_governance/alert_governance_memo.ipynb
---

# Model-Risk Governance For Fraud Scoring

<!-- HITL-REVIEW-REQUIRED -->

Educational use only: this source note supports fraud-detection curriculum design and is not legal or compliance advice.

## Source Scope

This note uses Federal Reserve SR 11-7 as an official model-risk governance reference for
documentation, validation, limitation statements, and effective challenge. It is included because
fraud scoring notebooks need governance habits even when the baseline model is deliberately
simple. No direct quotations are needed for the v0.1 exercises.

## Official Sources

- [Federal Reserve SR 11-7: Guidance on Model Risk Management](https://www.federalreserve.gov/supervisionreg/srletters/sr1107.htm)

## Learning Implications

The main learner habit is to document the model's intended use, input data, threshold choice,
known limitations, and monitoring questions. In v0.1, this means treating transparent scoring
rules as models for governance purposes: they process data into risk estimates and can be
wrong, stale, over-broad, or misused.

This source note connects directly to alert-aware metrics. Precision, recall, PR-AUC, alert
capacity, and cost summaries are not just performance numbers; they provide evidence for model
review, threshold rationale, and stakeholder communication.

## Linked v0.1 Exercises

- `notebooks/00_foundations/foundations_data_tour.ipynb`: introduces alert-aware metrics and
  limitation-aware summaries.
- `notebooks/01_private_banking_transaction_fraud/alpine_crest_baseline.ipynb`: documents a
  private-banking threshold choice for Alpine Crest Private Bank.
- `notebooks/02_digital_scam_to_mule/novabank_scam_to_mule_baseline.ipynb`: documents a
  digital scam-to-mule threshold choice for NovaBank Digital.
- `notebooks/03_alert_governance/alert_governance_memo.ipynb`: converts model outputs and
  threshold tradeoffs into a governance memo draft.

## Human Review

HITL review should confirm that SR 11-7 is a suitable model-risk reference for this public
curriculum and that the note does not overstate its applicability outside the exercise setting.
