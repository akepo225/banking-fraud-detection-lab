# 05_digital_session_and_payment_fraud

NovaBank Digital session and payment-fraud feature engineering, supervised
threshold tuning, and alert triage. It also hosts the v0.5 case-narrative notebook.

## Case library and regulatory context

Source packs that anchor the Detection patterns exercised here:

- [Digital scam-to-mule](../../docs/cases/source_packs/digital-scam-to-mule.md) — `digital_scam_to_mule`.
- [Digital money mule behavior](../../docs/cases/source_packs/digital-money-mule-behavior.md) — `digital_scam_to_mule`.
- [Authorised push payment scam to a newly added beneficiary](../../docs/cases/source_packs/digital-app-scam-payments.md) — `new_beneficiary_payment`.
- [Payment-system beneficiary guidance](../../docs/cases/source_packs/digital-payment-system-guidance.md) — `new_beneficiary_payment`.
- [Online-bank account control failure](../../docs/cases/source_packs/digital-online-bank-control-failures.md) — `session_payment_velocity`.
- [Graph network money mules](../../docs/cases/source_packs/graph-network-money-mules.md) — `digital_scam_to_mule` (network level).

Regulatory source notes:

- [UK APP scam reimbursement guidance](../../docs/regulation/source_notes/uk-app-scam-payment-guidance.md)
- [FATF typologies for money-mule networks](../../docs/regulation/source_notes/fatf-money-mule-typologies.md)

See the full catalog:

- [Case library index](../../docs/cases/index.md)
- [Regulatory source index](../../docs/regulation/index.md)
