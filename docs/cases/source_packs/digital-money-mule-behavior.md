---
title: Digital Money Mule Behavior Source Pack
status: draft-hitl
hitl_review_required: true
v0_1_area: digital_scam_to_mule
track: Digital-banking fraud detection
detection_pattern: early-life account receiving and rapidly passing funds onward
pattern_id: digital_scam_to_mule
institution_type: payment service provider or digital bank
source_authority: UK Finance
source_type: industry_report
geography: United Kingdom / cross-border payments
product: digital current accounts and instant payments
source_quality: reputable industry report candidate
linked_modules: notebooks/02_digital_scam_to_mule/novabank_scam_to_mule_baseline.ipynb, notebooks/05_digital_session_and_payment_fraud/novabank_feature_engineering.ipynb, notebooks/05_digital_session_and_payment_fraud/novabank_supervised_baseline.ipynb, notebooks/05_digital_session_and_payment_fraud/novabank_alert_triage.ipynb
---

# Digital Money Mule Behavior Source Pack

<!-- HITL-REVIEW-REQUIRED -->

This is educational material for the Banking Fraud Detection Lab. It is not legal,
compliance, audit, investment, regulatory, or professional advice.

## Summary

This source pack anchors the `digital_scam_to_mule` **Detection pattern** — an early-life
account receiving and rapidly passing funds onward — using a UK Finance industry report as a
public source candidate. It supports the digital-banking track at **NovaBank Digital**. The
learner outcome is to detect mule pass-through behavior from account age, prior-credit timing,
and shared-device signals, and to translate that into feature-interpretation artifacts without
reconstructing the public matter.

## Source Links

- UK Finance source candidate: https://www.ukfinance.org.uk/policy-and-guidance/reports-and-publications

## Public Facts

- The source candidate is a UK Finance industry report on money-mule typologies,
  including accounts used to receive and rapidly onward funds from scam victims.
- The source describes early-life account abuse, shared devices, and rapid
  pass-through as recurring mule behaviour indicators.
- Named authorities appear here only because this is a sourced public
  case-library draft, not a synthetic scenario.

## Interpretation For Detection Patterns

This source pack supports a **Detection pattern** around digital scam-to-mule:
mule behaviour surfaces when an early-life account receives an incoming payment
and rapidly moves funds onward to a new beneficiary, often through a shared
device. It maps to the existing `digital_scam_to_mule` pattern.

## Likely Data Signals

- Account opened recently (early-life account) relative to incoming and outgoing
  payments (`db_is_early_life_account`, `db_account_age_days`).
- Incoming credit followed by a rapid outbound debit to a new beneficiary
  (`db_is_rapid_pass_through`, `db_prior_credit_amount_chf`, `db_hours_since_prior_credit`).
- Shared device fingerprint across multiple Users (`db_is_shared_device`, `db_device_user_count`).
- High-risk network or VPN/proxy on the onward-payment session (`db_is_vpn_or_proxy`, `db_is_high_risk_network`).

## Linked Modules And Exercises

- `notebooks/02_digital_scam_to_mule/novabank_scam_to_mule_baseline.ipynb`
- `notebooks/05_digital_session_and_payment_fraud/novabank_feature_engineering.ipynb`
- `notebooks/05_digital_session_and_payment_fraud/novabank_supervised_baseline.ipynb`
- `notebooks/05_digital_session_and_payment_fraud/novabank_alert_triage.ipynb`

### Exercise 1 — Measure rapid pass-through for early-life accounts

- Pattern: `digital_scam_to_mule`
- Module: `notebooks/05_digital_session_and_payment_fraud/novabank_feature_engineering.ipynb`
- Prompt: Using the feature-engineering module, compare the rate of `db_is_rapid_pass_through` for accounts flagged `db_is_early_life_account` versus older accounts. Consider how `db_hours_since_prior_credit` and `db_prior_credit_amount_chf` change the read.
- Learner output: A short comparison (counts or rates) plus two or three sentences naming which features drive the pass-through signal and one limitation (for example, legitimate rapid payments by a new business).

## Regulatory Hooks

- Money-laundering and mule-typology guidance are relevant context, but this
  draft does not provide legal advice.
- The final framing should be reviewed alongside the regulatory source index
  before publication.

## Limitations

- This draft does not claim to reconstruct any specific public matter.
- Synthetic data in the curriculum uses **NovaBank Digital**, not any named
  institution or customer in the source.
- Human review is required before treating this as a publication-ready case note.

## Human Review

<!-- HITL-REVIEW-REQUIRED -->

- Verify source selection and source URL.
- Confirm whether this source pack should be a case note or a shorter source pack.
- Review the detection-pattern framing for fairness and accuracy.
