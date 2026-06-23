---
title: "FATF typologies for money-mule networks"
status: draft-hitl
hitl_review_required: true
source_families:
  - fatf_typologies
pattern_ids:
  - digital_scam_to_mule
learning_use:
  - analytics_question
  - control
  - governance
track: digital-banking fraud detection
primary_official_sources:
  - https://www.fatf-gafi.org/en/publications/Methodsandtrends/Professional-money-laundering.html
linked_modules:
  - notebooks/02_digital_scam_to_mule/novabank_scam_to_mule_baseline.ipynb
  - notebooks/03_alert_governance/alert_governance_memo.ipynb
  - notebooks/05_digital_session_and_payment_fraud/novabank_feature_engineering.ipynb
  - notebooks/05_digital_session_and_payment_fraud/novabank_supervised_baseline.ipynb
  - notebooks/05_digital_session_and_payment_fraud/novabank_alert_triage.ipynb
---

# FATF Typologies For Money-Mule Networks

<!-- HITL-REVIEW-REQUIRED -->

Educational use only: this source note supports fraud-detection curriculum design and is not legal or compliance advice.

## Source Scope

This note uses FATF's professional money-laundering typology page as a global methods and
trends anchor for mule and proxy-network analytics. The note treats the source as typology
context, not as a synthetic reconstruction brief. No direct quotations are needed for the v0.1
exercises.

## Learning Prompt

When building `digital_scam_to_mule` features in the NovaBank Digital notebooks, use this
typology source to design multi-account analytics questions (shared devices, shared
beneficiaries, pass-through chains, clustered incoming-to-outgoing flow) instead of scoring
accounts in isolation. Consider how a repeatable movement pattern shapes the analytics
question, the controls you can describe from tabular features, and how you would document the
evidence and limitations of a network-style indicator for governance review.

## Official Sources

- [FATF Professional Money Laundering](https://www.fatf-gafi.org/en/publications/Methodsandtrends/Professional-money-laundering.html)

## Learning Implications

FATF typology material helps learners move beyond single-account scoring. In the digital track,
the key analytic step is to ask whether several accounts, beneficiaries, devices, or counterparties
form a repeatable movement pattern. Even when v0.1 uses tabular features, the same source family
prepares learners for later graph work: shared devices, shared beneficiaries, pass-through chains,
and clustered incoming-to-outgoing flow.

For governance exercises, the learning implication is that a high-risk network pattern still needs
clear evidence and limitations. The notebook memo should explain what is observed in NovaBank
Digital synthetic data and avoid claims about criminal intent.

## Linked Exercises

- `notebooks/02_digital_scam_to_mule/novabank_scam_to_mule_baseline.ipynb`: introduces mule
  behavior through account age, beneficiary novelty, shared-device signals, and payment velocity.
- `notebooks/03_alert_governance/alert_governance_memo.ipynb`: frames network-like indicators
  as review evidence and documents uncertainty.
- `notebooks/05_digital_session_and_payment_fraud/novabank_feature_engineering.ipynb`:
  builds the `db_` shared-device, account-age, and pass-through features that connect mule
  typologies to the `digital_scam_to_mule` Detection pattern.
- `notebooks/05_digital_session_and_payment_fraud/novabank_supervised_baseline.ipynb`:
  tunes alert thresholds with investigation capacity and cost tradeoffs.
- `notebooks/05_digital_session_and_payment_fraud/novabank_alert_triage.ipynb`: reviews
  alerts where confirmed-fraud is an imperfect, noisy label.

## Human Review

HITL review should confirm that the FATF source is the right typology anchor for v0.1, especially
while deeper graph/network notebooks remain future work.
