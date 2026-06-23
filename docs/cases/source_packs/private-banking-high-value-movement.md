---
title: Private-Banking High-Value Movement Source Pack
status: draft-hitl
hitl_review_required: true
v0_1_area: private_banking_transaction_fraud
track: Private-banking fraud detection
detection_pattern: high-value private-banking transaction movement
pattern_id: pb_high_value_movement
institution_type: private bank
source_authority: FINMA
source_type: regulator
geography: Switzerland / cross-border
product: private-banking relationships and transactions
source_quality: official regulator source candidate
linked_modules: notebooks/01_private_banking_transaction_fraud/alpine_crest_baseline.ipynb, notebooks/04_private_banking_feature_engineering/alpine_crest_feature_engineering.ipynb, notebooks/04_private_banking_feature_engineering/alpine_crest_supervised_baseline.ipynb
---

# Private-Banking High-Value Movement Source Pack

<!-- HITL-REVIEW-REQUIRED -->

## Source Links

- FINMA source candidate: https://www.finma.ch/en/news/2024/06/20240618-mm-hsbc/

## Public Facts

- The source candidate is an official FINMA publication about money-laundering prevention in a Swiss private-banking context.
- The source discusses high-risk Banking relationship activity, politically exposed persons, high-risk transactions, cross-border movement, and documentation of transaction background.
- Named institutions appear here only because this is a sourced public case-library draft, not a synthetic scenario or affiliation claim.

## Interpretation For Detection Patterns

This source pack supports the `pb_high_value_movement` **Detection pattern**: unusually large private-banking transactions need Banking relationship context, Client profile context, counterparty history, cross-border context, and prior relationship activity. The analytic lesson is to compare movement against relationship-scale baselines instead of using raw transaction amount alone.

## Likely Data Signals

- `amount_to_aum_ratio` and `amount_to_relationship_baseline_ratio` for relationship-scale context.
- `is_cross_border` for movement across account, beneficiary, or relationship countries.
- `counterparty_age_days` and `is_new_counterparty` for destination novelty.
- Seven-day and thirty-day velocity ratios for changes in relationship transaction behaviour.
- Effective-dated relationship-manager responsibility at the time of the transaction.

## Linked Modules And Exercises

- `notebooks/01_private_banking_transaction_fraud/alpine_crest_baseline.ipynb`
- `notebooks/04_private_banking_feature_engineering/alpine_crest_feature_engineering.ipynb`
- `notebooks/04_private_banking_feature_engineering/alpine_crest_supervised_baseline.ipynb`

## Regulatory Hooks

- Swiss supervisory source material can anchor questions about high-risk relationship context, transaction background, review evidence, and governance of analytic explanations.
- This draft frames analytics and documentation questions for the lab. It does not provide legal, compliance, audit, investment, regulatory, or professional advice.

## Limitations

- This source pack does not reconstruct any public matter and does not use public case amounts, parties, or chronology in the synthetic data.
- Synthetic examples use fictional **Alpine Crest Private Bank** and synthetic Clients, Partners, Banking relationships, accounts, and transactions.
- Human review is required before treating this as a publication-ready case note.

## Human Review

<!-- HITL-REVIEW-REQUIRED -->

- Verify source selection and source URL.
- Review whether the high-value movement framing is sufficiently distinct from transaction-monitoring control-failure framing.
- Confirm that the source pack connects to v0.3 feature and supervised-baseline modules without overclaiming.
