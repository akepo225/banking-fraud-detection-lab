# Trace Suspicious Activity Through The Alert Lifecycle

Status: needs-triage

## Parent

`.scratch/banking-fraud-detection-lab-v0-1/PRD.md`

## What to build

Extend the generated banking world so suspicious activity can flow through the **Alert lifecycle**: suspicious activity, generated alert, opened case, case outcome, and confirmed fraud determination.

This slice should make the labels realistic enough for later notebooks while keeping protected scenario answer keys outside normal learner-facing views.

## Implementation order

Start after issue 01 creates the minimal generated banking world.

## What needs to be implemented first

- Add alert and case lifecycle fields to the schema contract.
- Add learner-facing lifecycle tables or views before introducing protected answer keys.
- Add protected answer-key tables only after normal learner-facing outputs are clear.
- Add lifecycle tests before scenario-specific fraud injection.

## Acceptance criteria

- [ ] Generated data represents suspicious activity, alerts, cases, case outcomes, and confirmed fraud as distinct concepts.
- [ ] Protected scenario answer keys exist but are excluded from learner-facing views by default.
- [ ] Alert and case records can reference relevant accounts, transactions, users, sessions, payment beneficiaries, and banking relationships.
- [ ] Tests verify referential integrity for alert and case links.
- [ ] Tests verify that the alert lifecycle is not reduced to a single `is_fraud` flag.
- [ ] Tests verify scenario prevalence ranges rather than exact row-level outputs.

## Blocked by

- `.scratch/banking-fraud-detection-lab-v0-1/issues/01-generate-and-inspect-minimal-banking-world.md`
