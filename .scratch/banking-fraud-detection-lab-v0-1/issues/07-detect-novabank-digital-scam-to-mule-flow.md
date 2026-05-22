# Detect NovaBank Digital Scam-To-Mule Flow

Status: needs-triage

GitHub: https://github.com/akepo225/banking-fraud-detection-lab/issues/8

## Parent

GitHub issue #1: https://github.com/akepo225/banking-fraud-detection-lab/issues/1

## What to build

Add the first **NovaBank Digital** scenario: a **Scam-to-mule flow** where a scam victim authorizes a payment that moves into a mule or rented account and is rapidly passed onward.

This slice should generate digital users, devices, sessions, beneficiaries, payments, telemetry, mule-account behavior, alerts, cases, and a baseline detection notebook.

## Implementation order

Start after lifecycle, SQLite, and metrics are available. This can run in parallel with issue 06 after shared dependencies are complete.

## What needs to be implemented first

- Define the minimal **Scam-to-mule flow** event sequence.
- Add digital telemetry fields to generated users, sessions, devices, beneficiaries, and payments.
- Add mule-account behavior with protected answer keys and noisy outcomes.
- Build the baseline notebook only after scenario prevalence and referential-integrity tests pass.

## Acceptance criteria

- [ ] Scenario injection supports a digital scam-to-mule pattern with configurable prevalence.
- [ ] Generated data distinguishes **Client**, **User**, and **Partner**.
- [ ] Generated data includes user agent, app or browser version, device fingerprint hash, IP country, ASN risk, coarse geolocation, VPN or proxy flag, authentication method, session events, and beneficiary-change events.
- [ ] Generated mule-account behavior includes early-life accounts, incoming victim payments, rapid pass-through, new beneficiaries, shared devices, abnormal network position, and noisy outcomes.
- [ ] A notebook trains a baseline model or scoring rule for the scam-to-mule scenario.
- [ ] Tests verify scenario prevalence ranges and referential integrity for digital-banking scenario records.

## Blocked by

- GitHub issue #3: https://github.com/akepo225/banking-fraud-detection-lab/issues/3
- GitHub issue #4: https://github.com/akepo225/banking-fraud-detection-lab/issues/4
- GitHub issue #5: https://github.com/akepo225/banking-fraud-detection-lab/issues/5
