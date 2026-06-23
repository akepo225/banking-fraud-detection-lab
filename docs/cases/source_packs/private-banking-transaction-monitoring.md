---
title: Private-Banking Transaction Monitoring Source Pack
status: draft-hitl
hitl_review_required: true
v0_1_area: private_banking_transaction_fraud
track: Private-banking fraud detection
detection_pattern: relationship and transaction monitoring control failure
pattern_id: pb_transaction_fraud
institution_type: private bank
source_authority: FINMA
geography: Switzerland / cross-border
product: private-banking transactions
source_quality: official regulator source candidate
linked_modules: notebooks/01_private_banking_transaction_fraud/alpine_crest_baseline.ipynb, notebooks/03_alert_governance/alert_governance_memo.ipynb, notebooks/04_private_banking_feature_engineering/alpine_crest_feature_engineering.ipynb, notebooks/04_private_banking_feature_engineering/alpine_crest_supervised_baseline.ipynb
---

# Private-Banking Transaction Monitoring Source Pack

<!-- HITL-REVIEW-REQUIRED -->

This is the v0.5 worked example for the case template in `docs/cases/TEMPLATE.md`.
It is educational material for the Banking Fraud Detection Lab. It is not legal,
compliance, audit, investment, regulatory, or professional advice.

## Summary

This source pack anchors a **Detection pattern** around private-banking
transaction-monitoring control failure using an official FINMA enforcement
publication as a public source candidate. It supports the `pb_transaction_fraud`
pattern (and overlaps with `pb_high_value_movement`) for the private-banking
track at **Alpine Crest Private Bank**. The learner outcome is to read a public
supervisory source, separate facts from interpretation, and translate the
monitoring-control-failure behavior class into relationship-aware analytics and
governance questions without reconstructing the matter.

## Source Links

- FINMA source candidate: https://www.finma.ch/en/~/media/finma/dokumente/dokumentencenter/8news/medienmitteilungen/2016/05/20160524-mm-verfahren-bsi_de.pdf?hash=57206ED044C99556B86C4BBA1F68174C&sc_lang=en

## Public Facts

- The source candidate is an official FINMA publication related to a private-banking enforcement matter.
- The source discusses monitoring and governance weaknesses in relation to high-risk **Banking relationship** activity and transactions.
- Named institutions appear here only because this is a sourced public case-library draft, not a synthetic scenario.

## Interpretation For Detection Patterns

This source pack supports the `pb_transaction_fraud` **Detection pattern**: an
injected private-banking transaction-fraud scenario where relationship-manager-
assisted or self-initiated payments exhibit structural fraud signals detectable
through feature engineering and scoring rules. It also overlaps with the
`pb_high_value_movement` pattern, where high-value movement should be read with
Banking relationship context. The analytic lesson is that high-value account
movement should be interpreted with Banking relationship context, Partner roles,
relationship-manager assignment, and prior activity rather than as an isolated
transaction amount. The pack does not reconstruct the public matter; it extracts
the behavior class and turns it into relationship-aware features and
investigation questions.

## Likely Data Signals

- High transaction amount relative to account or Banking relationship context (`pb_amount_to_aum_ratio`, `pb_amount_to_relationship_baseline_ratio`).
- Relationship-manager concentration or repeated exceptions (effective-dated relationship-manager responsibility at the time of the transaction).
- Cross-border movement involving higher-risk relationship context (`pb_is_cross_border`).
- Counterparty novelty against relationship history (`pb_counterparty_age_days`, `pb_is_new_counterparty`).
- Weak linkage between alert explanation and case outcome documentation (governance, not a feature).

## Linked Modules And Exercises

- `notebooks/01_private_banking_transaction_fraud/alpine_crest_baseline.ipynb`
- `notebooks/03_alert_governance/alert_governance_memo.ipynb`
- `notebooks/04_private_banking_feature_engineering/alpine_crest_feature_engineering.ipynb`
- `notebooks/04_private_banking_feature_engineering/alpine_crest_supervised_baseline.ipynb`

### Exercise 1 — Quantify relationship-scale movement

- Pattern: `pb_transaction_fraud` (overlaps `pb_high_value_movement`)
- Module: `notebooks/01_private_banking_transaction_fraud/alpine_crest_baseline.ipynb`
- Prompt: On the synthetic Alpine Crest Private Bank data, select a transaction and compare its amount against the relationship-scale baseline rather than treating the raw amount as the signal. Use a progressive view or the SQLite learner path.
- Learner output: A short table or query result comparing one transaction's amount to its Banking relationship baseline, plus one sentence on why relationship-scale context changes the read. Compare your read against the notebook's alert-aware metrics; learner-facing views do not expose the protected answer key.

### Exercise 2 — Interpret a feature against the control-failure pattern

- Pattern: `pb_transaction_fraud`
- Module: `notebooks/04_private_banking_feature_engineering/alpine_crest_feature_engineering.ipynb`
- Prompt: Pick one feature the feature-engineering module emits (for example `amount_to_aum_ratio`, `amount_to_relationship_baseline_ratio`, `is_new_counterparty`, or `is_cross_border`) and explain, in learner-facing terms, how it operationalizes a monitoring-control-failure signal from this source pack. Connect the feature to relationship-manager responsibility or counterparty novelty.
- Learner output: Two or three sentences naming the feature, the signal it captures, and one limitation of using it alone.

### Exercise 3 — Write a monitoring investigation note

- Pattern: `pb_transaction_fraud` (overlaps `pb_high_value_movement`)
- Module: `notebooks/03_alert_governance/alert_governance_memo.ipynb`
- Prompt: Draft a short investigation note for an alert that could connect to a monitoring-control-failure behavior class. Frame the note for business, risk, and compliance stakeholder discussion and avoid headline accuracy claims.
- Learner output: A four-to-six-sentence note referencing the relationship context, the candidate data signal, the limitation, and a follow-up question. Educational framing only; no compliance instruction.

## Regulatory Hooks

- Swiss AML and supervisory expectations are relevant context, but this draft does not provide legal advice.
- The final framing should be reviewed alongside the regulatory source index before publication.
- Governance and documentation questions (linkage between alert explanation and case outcome) are in scope; compliance instructions are not.

## Limitations

- This draft does not claim to reconstruct the public matter.
- Synthetic data in the curriculum uses **Alpine Crest Private Bank**, not the named institution in the source.
- No real Client, account, or transaction data is used or implied.
- Human review is required before treating this as a publication-ready case note.

## Human Review

<!-- HITL-REVIEW-REQUIRED -->

- Verify source selection and source URL.
- Confirm whether this source pack should be a case note or a shorter source pack.
- Review the detection-pattern framing for fairness and accuracy.
- Review the three learner-output exercises for appropriateness and for reliance on existing notebooks only.
