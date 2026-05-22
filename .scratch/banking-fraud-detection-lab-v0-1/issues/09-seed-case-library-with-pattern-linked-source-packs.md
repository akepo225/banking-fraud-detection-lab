# Seed Case Library With Pattern-Linked Source Packs

Status: needs-triage

## Parent

`.scratch/banking-fraud-detection-lab-v0-1/PRD.md`

## What to build

Seed the public case library with pattern-linked source packs that support the v0.1 learning areas. Each case document should separate public facts from interpretation and map the case to **Detection patterns**, likely data signals, modules, exercises, regulatory hooks, and limitations.

This is HITL because source selection and case framing should be reviewed before publication.

## Implementation order

Start after the v0.1 learning paths are concrete enough to know which cases support them.

## What needs to be implemented first

- Define the case document front matter and required section template.
- Add validation for the template before drafting multiple case documents.
- Draft one source pack per v0.1 learning area.
- Keep named institutions only in sourced case documents, never in synthetic scenarios.

## Acceptance criteria

- [ ] Case-library documents use detection-pattern-first organization with machine-readable metadata.
- [ ] At least one case or source pack supports private-banking transaction fraud.
- [ ] At least one case or source pack supports digital scam-to-mule fraud.
- [ ] At least one case or source pack supports regulatory or model-governance method learning.
- [ ] At least one case or source pack supports a graph or network pattern for future modules.
- [ ] Validation checks verify required case metadata and required sections.

## Blocked by

- `.scratch/banking-fraud-detection-lab-v0-1/issues/05-complete-foundations-data-tour-and-sql-feature-notebook.md`
- `.scratch/banking-fraud-detection-lab-v0-1/issues/06-detect-alpine-crest-private-banking-transaction-fraud.md`
- `.scratch/banking-fraud-detection-lab-v0-1/issues/07-detect-novabank-digital-scam-to-mule-flow.md`
