---
title: Private-Banking Transaction Monitoring Source Pack
status: draft-hitl
hitl_review_required: true
v0_1_area: private_banking_transaction_fraud
track: Private-banking fraud detection
detection_pattern: relationship and transaction monitoring control failure
institution_type: private bank
source_authority: FINMA
geography: Switzerland / cross-border
product: private-banking transactions
source_quality: official regulator source candidate
linked_modules: notebooks/01_private_banking_transaction_fraud/alpine_crest_baseline.ipynb, notebooks/03_alert_governance/alert_governance_memo.ipynb
---

# Private-Banking Transaction Monitoring Source Pack

<!-- HITL-REVIEW-REQUIRED -->

## Source Links

- FINMA source candidate: https://www.finma.ch/en/~/media/finma/dokumente/dokumentencenter/8news/medienmitteilungen/2016/05/20160524-mm-verfahren-bsi_de.pdf?hash=57206ED044C99556B86C4BBA1F68174C&sc_lang=en

## Public Facts

- The source candidate is an official FINMA publication related to a private-banking enforcement matter.
- The source discusses monitoring and governance weaknesses in relation to high-risk **Banking relationship** activity and transactions.
- Named institutions appear here only because this is a sourced public case-library draft, not a synthetic scenario.

## Interpretation For Detection Patterns

This source pack supports a **Detection pattern** around private-banking transaction monitoring: high-value account movement should be interpreted with Banking relationship context, Partner roles, relationship-manager assignment, and prior activity rather than as an isolated transaction amount.

## Likely Data Signals

- High transaction amount relative to account or Banking relationship context.
- Relationship-manager concentration or repeated exceptions.
- Cross-border movement involving higher-risk relationship context.
- Weak linkage between alert explanation and case outcome documentation.

## Linked Modules And Exercises

- `notebooks/01_private_banking_transaction_fraud/alpine_crest_baseline.ipynb`
- `notebooks/03_alert_governance/alert_governance_memo.ipynb`

## Regulatory Hooks

- Swiss AML and supervisory expectations are relevant context, but this draft does not provide legal advice.
- The final framing should be reviewed alongside the regulatory source index before publication.

## Limitations

- This draft does not claim to reconstruct the public matter.
- Synthetic data in the curriculum uses **Alpine Crest Private Bank**, not the named institution in the source.
- Human review is required before treating this as a publication-ready case note.

## Human Review

<!-- HITL-REVIEW-REQUIRED -->

- Verify source selection and source URL.
- Confirm whether this source pack should be a case note or a shorter source pack.
- Review the detection-pattern framing for fairness and accuracy.
