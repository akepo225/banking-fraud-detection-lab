---
title: Authorised Push Payment Scam Source Pack
status: draft-hitl
hitl_review_required: true
v0_1_area: digital_scam_to_mule
track: Digital-banking fraud detection
detection_pattern: authorised push payment scam to a newly added beneficiary
pattern_id: new_beneficiary_payment
institution_type: payment service provider or digital bank
source_authority: Payment Systems Regulator
source_type: regulator
geography: United Kingdom / payments
product: authorised push payments and digital banking
source_quality: official payment regulator source candidate
linked_modules: notebooks/02_digital_scam_to_mule/novabank_scam_to_mule_baseline.ipynb, notebooks/05_digital_session_and_payment_fraud/novabank_feature_engineering.ipynb, notebooks/05_digital_session_and_payment_fraud/novabank_supervised_baseline.ipynb, notebooks/05_digital_session_and_payment_fraud/novabank_alert_triage.ipynb
---

# Authorised Push Payment Scam Source Pack

<!-- HITL-REVIEW-REQUIRED -->

This is educational material for the Banking Fraud Detection Lab. It is not legal,
compliance, audit, investment, regulatory, or professional advice.

## Summary

This source pack anchors the `new_beneficiary_payment` **Detection pattern** — an authorised
push payment scam to a newly added beneficiary — using a Payment Systems Regulator publication
as a public source candidate. It supports the digital-banking track at **NovaBank Digital**.
The learner outcome is to design new-beneficiary scam detection around payment context
(beneficiary novelty, channel, country mismatch) rather than authentication alone, and to
produce SQL and feature-interpretation artifacts without reconstructing the public matter.

## Source Links

- Payment Systems Regulator source candidate: https://www.psr.org.uk/appscams/

## Public Facts

- The source candidate is an official Payment Systems Regulator publication on
  authorised push payment (APP) scam trends and reimbursement policy context.
- The source describes how scam victims authorise payments to fraudster-controlled
  accounts, often after the victim adds a new beneficiary under social-engineering
  pressure.
- Named authorities appear here only because this is a sourced public
  case-library draft, not a synthetic scenario.

## Interpretation For Detection Patterns

This source pack supports a **Detection pattern** around new-beneficiary
payment: an APP scam surfaces when a **User** adds a beneficiary and authorises
a payment under coercion or deception, so the signal is beneficiary novelty
combined with session context rather than the payment amount alone. It maps to
the existing `new_beneficiary_payment` pattern.

## Likely Data Signals

- Recently added or updated beneficiary immediately before an outbound payment (`db_is_new_beneficiary`, `db_beneficiary_age_days`).
- New device, high-risk network, or password/SMS authentication on the session (`db_is_vpn_or_proxy`, `db_is_high_risk_network`, `db_is_password_sms_auth`).
- Rapid outbound payment to a beneficiary with no prior history.
- Mobile-app channel and destination-country mismatch (`db_is_mobile_app_channel`, `db_is_beneficiary_country_risky`).

## Linked Modules And Exercises

- `notebooks/02_digital_scam_to_mule/novabank_scam_to_mule_baseline.ipynb`
- `notebooks/05_digital_session_and_payment_fraud/novabank_feature_engineering.ipynb`
- `notebooks/05_digital_session_and_payment_fraud/novabank_supervised_baseline.ipynb`
- `notebooks/05_digital_session_and_payment_fraud/novabank_alert_triage.ipynb`

### Exercise 1 — Identify new-beneficiary scam payments with SQL

- Pattern: `new_beneficiary_payment`
- Module: `notebooks/05_digital_session_and_payment_fraud/novabank_feature_engineering.ipynb`
- Prompt: Using `sql/examples/10_digital_beneficiary_passthrough_features.sql` as a pattern, write a SQLite query on the synthetic NovaBank Digital tables that joins session context to payments and returns rows where `db_is_new_beneficiary` is set together with a risky channel or country flag (`db_is_beneficiary_country_risky`), so the result is reviewable rather than headline-sized.
- Learner output: A runnable SQL result listing flagged payments with the beneficiary-age and channel context alongside, plus one sentence on why beneficiary novelty plus channel context changes which payments look scam-like. Compare your read against the notebook's alert-aware metrics; learner-facing views do not expose the protected answer key.

## Regulatory Hooks

- UK APP scam reimbursement and payment-system guidance are relevant context,
  but this draft does not provide legal advice.
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
