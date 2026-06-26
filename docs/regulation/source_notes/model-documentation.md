---
title: "Model documentation for fraud scoring"
status: draft-hitl
hitl_review_required: true
source_families:
  - model_risk_governance
pattern_ids:
  - pb_high_value_movement
  - pb_transaction_fraud
learning_use:
  - documentation
  - governance
track: cross-track governance
primary_official_sources:
  - https://www.federalreserve.gov/frrs/guidance/supervisory-guidance-on-model-risk-management.htm
linked_modules:
  - notebooks/03_alert_governance/alert_governance_memo.ipynb
  - notebooks/04_private_banking_feature_engineering/alpine_crest_feature_engineering.ipynb
  - notebooks/04_private_banking_feature_engineering/alpine_crest_supervised_baseline.ipynb
---

# Model Documentation For Fraud Scoring

<!-- HITL-REVIEW-REQUIRED -->

Educational use only: this source note supports fraud-detection curriculum design and is not legal or compliance advice.

## Source Scope

This note uses Federal Reserve SR 11-7 as an official reference for the documentation facet of
model-risk governance: the expectation that a model's intended use, inputs, assumptions,
limitations, and monitoring needs are written down so the model can be reviewed and handed off. It
extends the broader governance note by focusing on the documentation artifact itself. No direct
quotations are used.

## Learning Prompt

Before sharing a fraud-scoring result, draft the documentation a reviewer would need: what the
model is for, which data and features fed it, what you assumed, what it cannot do, and what should
be watched later. A score without that documentation is hard to challenge or hand off.

## Official Sources

- [Federal Reserve SR 11-7: Guidance on Model Risk Management](https://www.federalreserve.gov/frrs/guidance/supervisory-guidance-on-model-risk-management.htm)

## Learning Implications

Documentation turns a notebook into a reviewable artifact. The v0.7 model-documentation template
captures the five sections a fraud model should be documented against (purpose, data lineage,
assumptions, limitations, monitoring needs), filled deterministically from the fitted model so the
artifact is reproducible rather than hand-written prose. The habit is to treat documentation as
part of the model, not an afterthought: a stakeholder reading only the documentation should
understand both what the model does and where it should not be trusted.

## Linked Exercises

- `notebooks/03_alert_governance/alert_governance_memo.ipynb`: converts threshold tradeoffs into a
  documented governance draft.
- `notebooks/04_private_banking_feature_engineering/alpine_crest_feature_engineering.ipynb`:
  documents feature families, source columns, and Detection pattern mappings as model inputs.
- `notebooks/04_private_banking_feature_engineering/alpine_crest_supervised_baseline.ipynb`:
  documents intended use, inputs, and limitations for a fitted baseline.

## Human Review

HITL review should confirm the documentation framing is suitable for education and that the note
does not claim the template satisfies a formal documentation standard.
