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

This is educational material for the Banking Fraud Detection Lab. It is not legal,
compliance, audit, investment, regulatory, or professional advice.

## Summary

This source pack anchors the `session_payment_velocity` **Detection pattern** —
account-takeover with elevated payment velocity within a single session — using a National
Cyber Security Centre publication as a public source candidate. It supports the digital-banking
track at **NovaBank Digital**. The learner outcome is to detect account-control failure from
session telemetry (network risk, ASN risk, authentication downgrade, in-session payment
velocity) and to produce SQL and feature-interpretation artifacts without reconstructing the
public matter.

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

- Elevated payment count within a single session for a User (`db_session_payment_count`, `db_session_payment_amount_chf`, `db_session_max_payment_chf`).
- New device fingerprint, VPN/proxy, or high ASN risk score on the session (`db_is_vpn_or_proxy`, `db_asn_risk_score`, `db_is_high_risk_network`).
- Multiple new beneficiaries added in the same session (`db_is_new_beneficiary`).
- Authentication downgrade (for example password/SMS instead of stronger MFA) (`db_is_password_sms_auth`).

## Linked Modules And Exercises

- `notebooks/05_digital_session_and_payment_fraud/novabank_feature_engineering.ipynb`
- `notebooks/05_digital_session_and_payment_fraud/novabank_supervised_baseline.ipynb`
- `notebooks/05_digital_session_and_payment_fraud/novabank_alert_triage.ipynb`
- `notebooks/03_alert_governance/alert_governance_memo.ipynb`

### Exercise 1 — Identify high-risk sessions with elevated payment velocity

- Pattern: `session_payment_velocity`
- Module: `notebooks/05_digital_session_and_payment_fraud/novabank_feature_engineering.ipynb`
- Prompt: Using `sql/examples/09_digital_session_channel_features.sql` as a pattern, write a SQLite query that returns sessions where elevated payment velocity (`db_session_payment_count`) combines with a network-risk signal (`db_is_high_risk_network` or `db_is_vpn_or_proxy`) or a high `db_asn_risk_score`. Join to the session context so the result is reviewable.
- Learner output: A runnable SQL result listing flagged sessions with the velocity and network-risk context alongside, plus one sentence on why velocity alone is not enough and the network signal adds review evidence. Compare your read against the notebook's alert-aware metrics; learner-facing views do not expose the protected answer key.

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
