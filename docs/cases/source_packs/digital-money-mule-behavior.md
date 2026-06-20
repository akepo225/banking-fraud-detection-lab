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
geography: United Kingdom / cross-border payments
product: digital current accounts and instant payments
source_quality: reputable industry report candidate
linked_modules: notebooks/02_digital_scam_to_mule/novabank_scam_to_mule_baseline.ipynb, notebooks/05_digital_session_and_payment_fraud/novabank_feature_engineering.ipynb, notebooks/05_digital_session_and_payment_fraud/novabank_supervised_baseline.ipynb, notebooks/05_digital_session_and_payment_fraud/novabank_alert_triage.ipynb
---

# Digital Money Mule Behavior Source Pack

<!-- HITL-REVIEW-REQUIRED -->

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
  payments.
- Incoming credit followed by a rapid outbound debit to a new beneficiary.
- Shared device fingerprint across multiple Users.
- High-risk network or VPN/proxy on the onward-payment session.

## Linked Modules And Exercises

- `notebooks/02_digital_scam_to_mule/novabank_scam_to_mule_baseline.ipynb`
- `notebooks/05_digital_session_and_payment_fraud/novabank_feature_engineering.ipynb`
- `notebooks/05_digital_session_and_payment_fraud/novabank_supervised_baseline.ipynb`
- `notebooks/05_digital_session_and_payment_fraud/novabank_alert_triage.ipynb`

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
