---
title: Online-Bank Account Control Failure Source Pack
status: draft-hitl
hitl_review_required: true
v0_1_area: digital_scam_to_mule
track: Digital-banking fraud detection
detection_pattern: account-takeover with elevated session payment velocity
pattern_id: session_payment_velocity
institution_type: payment service provider or digital bank
source_authority: National Cyber Security Centre
source_type: cyber_authority
geography: United Kingdom / online banking
product: online and mobile-banking sessions
source_quality: official cyber-security authority source candidate
linked_modules: notebooks/05_digital_session_and_payment_fraud/novabank_feature_engineering.ipynb, notebooks/05_digital_session_and_payment_fraud/novabank_supervised_baseline.ipynb, notebooks/05_digital_session_and_payment_fraud/novabank_alert_triage.ipynb, notebooks/03_alert_governance/alert_governance_memo.ipynb
---

# Online-Bank Account Control Failure Source Pack

<!-- HITL-REVIEW-REQUIRED -->

## Source Links

- National Cyber Security Centre source candidate: https://www.ncsc.gov.uk/guidance/online-banking

## Public Facts

- The source candidate is an official NCSC publication on protecting online
  banking access, including account-takeover indicators and session control.
- The source describes how attackers take over a legitimate **User** session and
  authorise multiple payments at elevated velocity before the **Client** notices.
- Named authorities appear here only because this is a sourced public
  case-library draft, not a synthetic scenario.

## Interpretation For Detection Patterns

This source pack supports a **Detection pattern** around session payment
velocity: account-takeover surfaces when a single session authorises an elevated
number of payments to newly added beneficiaries from an unfamiliar device or
network. It maps to the existing `session_payment_velocity` pattern and overlaps
with `new_beneficiary_payment` for the beneficiary side.

## Likely Data Signals

- Elevated payment count within a single session for a User.
- New device fingerprint, VPN/proxy, or high ASN risk score on the session.
- Multiple new beneficiaries added in the same session.
- Authentication downgrade (for example password/SMS instead of stronger MFA).

## Linked Modules And Exercises

- `notebooks/05_digital_session_and_payment_fraud/novabank_feature_engineering.ipynb`
- `notebooks/05_digital_session_and_payment_fraud/novabank_supervised_baseline.ipynb`
- `notebooks/05_digital_session_and_payment_fraud/novabank_alert_triage.ipynb`
- `notebooks/03_alert_governance/alert_governance_memo.ipynb`

## Regulatory Hooks

- Operational-resilience and access-control expectations are relevant context,
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
