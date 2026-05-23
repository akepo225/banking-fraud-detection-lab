---
title: Model Governance Method Source Pack
status: draft-hitl
hitl_review_required: true
v0_1_area: regulatory_or_model_governance_method
track: Cross-track governance
detection_pattern: model-output governance and threshold documentation
geography: United States / cross-border method
source_quality: official supervisory guidance source candidate
linked_modules: notebooks/03_alert_governance/alert_governance_memo.ipynb
---

# Model Governance Method Source Pack

<!-- HITL-REVIEW-REQUIRED -->

## Source Links

- Federal Reserve SR 11-7 page: https://www.federalreserve.gov/supervisionreg/srletters/sr1107.htm

## Public Facts

- The source candidate is official supervisory guidance on model risk management.
- It is included as a governance-method source pack for model purpose, limitations, validation, monitoring, and documentation concepts.
- It is not included as legal advice or as a complete model-risk framework for this curriculum.

## Interpretation For Detection Patterns

This source pack supports the governance **Detection pattern** behind the alert-governance notebook: model scores need threshold rationale, limitation statements, monitoring evidence, and clear communication to stakeholders.

## Likely Data Signals

- Alert volume and capacity at selected thresholds.
- Precision and recall tradeoffs.
- Documented assumptions and limitations.
- Evidence that case outcomes are not reduced to headline accuracy.

## Linked Modules And Exercises

- `notebooks/03_alert_governance/alert_governance_memo.ipynb`

## Regulatory Hooks

- Model-risk concepts can help learners structure governance memo language.
- Human review must decide whether SR 11-7 is the right anchor for a v0.1 educational method note.

## Limitations

- This draft is a source pack, not a regulatory interpretation.
- It does not instruct any bank on compliance requirements.
- Human review is required before publication.

## Human Review

<!-- HITL-REVIEW-REQUIRED -->

- Confirm whether SR 11-7 should be paired with another model-risk or AI-governance source.
- Review for overreach in governance wording.
- Decide whether this belongs in the case library or only in the regulatory source index.
