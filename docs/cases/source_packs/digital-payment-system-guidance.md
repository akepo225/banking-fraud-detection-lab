---
title: Payment-System Beneficiary Guidance Source Pack
status: draft-hitl
hitl_review_required: true
v0_1_area: digital_scam_to_mule
track: Digital-banking fraud detection
detection_pattern: payment-system guidance on new-beneficiary confirmation
pattern_id: new_beneficiary_payment
institution_type: payment service provider or digital bank
source_authority: Pay.UK
source_type: payment_system_operator
geography: United Kingdom / payment rails
product: confirmation-of-payee and new-beneficiary controls
source_quality: official payment-system operator source candidate
linked_modules: notebooks/02_digital_scam_to_mule/novabank_scam_to_mule_baseline.ipynb, notebooks/05_digital_session_and_payment_fraud/novabank_feature_engineering.ipynb, notebooks/05_digital_session_and_payment_fraud/novabank_supervised_baseline.ipynb, notebooks/05_digital_session_and_payment_fraud/novabank_alert_triage.ipynb
---

# Payment-System Beneficiary Guidance Source Pack

<!-- HITL-REVIEW-REQUIRED -->

This is educational material for the Banking Fraud Detection Lab. It is not legal,
compliance, audit, investment, regulatory, or professional advice.

## Summary

This source pack anchors the `new_beneficiary_payment` **Detection pattern** — payment-system
guidance on new-beneficiary confirmation (for example confirmation-of-payee-style controls) —
using a Pay.UK publication as a public source candidate. It supports the digital-banking track
at **NovaBank Digital**. The learner outcome is to reason about new-beneficiary confirmation
and country-mismatch controls, and to produce feature-interpretation artifacts without
reconstructing the public matter.

## Source Links

- Pay.UK source candidate: https://www.wearepay.uk/

## Public Facts

- The source candidate is an official Pay.UK publication on payment-system
  controls, including confirmation-of-payee and new-beneficiary checking.
- The source describes how payment-system guidance frames beneficiary-confirmation
  failures as a key APP-scam and account-takeover enabler.
- Named authorities appear here only because this is a sourced public
  case-library draft, not a synthetic scenario.

## Interpretation For Detection Patterns

This source pack supports a **Detection pattern** around new-beneficiary payment:
payment-system guidance treats unconfirmed or newly added beneficiaries as a
control point, so detection should weigh beneficiary confirmation alongside
session and payment context. It maps to the existing `new_beneficiary_payment`
pattern.

## Likely Data Signals

- New or updated beneficiary with no prior confirmation history (`db_is_new_beneficiary`, `db_beneficiary_age_days`).
- Outbound payment immediately after beneficiary creation or update.
- Beneficiary bank-country or account-country mismatch with the paying account (`db_is_beneficiary_country_risky`).
- Mobile-app channel and high-value first payment to the new beneficiary (`db_is_mobile_app_channel`).

## Linked Modules And Exercises

- `notebooks/02_digital_scam_to_mule/novabank_scam_to_mule_baseline.ipynb`
- `notebooks/05_digital_session_and_payment_fraud/novabank_feature_engineering.ipynb`
- `notebooks/05_digital_session_and_payment_fraud/novabank_supervised_baseline.ipynb`
- `notebooks/05_digital_session_and_payment_fraud/novabank_alert_triage.ipynb`

### Exercise 1 — Interpret new-beneficiary control features across confirmed cases

- Pattern: `new_beneficiary_payment`
- Module: `notebooks/05_digital_session_and_payment_fraud/novabank_alert_triage.ipynb`
- Prompt: Using the alert-triage module, analyze how `db_is_new_beneficiary` and `db_is_beneficiary_country_risky` distribute across confirmed-fraud versus non-confirmed alerts. Note that confirmed-fraud is an imperfect, noisy label.
- Learner output: A short interpretation (counts or rates by flag) plus two or three sentences on what the flags add to triage and one limitation (for example, legitimate first-time payments to a new country).

## Regulatory Hooks

- Payment-system operator guidance and reimbursement rules are relevant context,
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
