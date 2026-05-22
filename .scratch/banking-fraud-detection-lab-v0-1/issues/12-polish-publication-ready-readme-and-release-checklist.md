# Polish Publication-Ready README And Release Checklist

Status: needs-triage

## Parent

`.scratch/banking-fraud-detection-lab-v0-1/PRD.md`

## What to build

Polish the public-facing repo experience so **Banking Fraud Detection Lab** is credible as a private pre-publication portfolio project and ready for final publication review.

This is HITL because positioning, disclaimers, and publication-readiness language should be reviewed by the repo owner.

## Implementation order

Start after the learner path, case library, regulatory source index, and CI quality gates exist.

## What needs to be implemented first

- Update README around the actual implemented v0.1 path, not aspirational future modules.
- Check disclaimers and split licensing language across public-facing docs.
- Link to the roadmap, ADR, schema docs, case library, regulatory source index, and notebooks.
- Convert the PRD publication gate into a checklist suitable for final review.

## Acceptance criteria

- [ ] README clearly explains the project promise, **Target learner**, two **Fraud detection tracks**, quickstart, curriculum map, and roadmap.
- [ ] README and license docs clearly explain the split license model.
- [ ] README and docs include educational-only, unaffiliated, no-real-data, no-reconstruction, and no-legal-advice disclaimers.
- [ ] README links to schema docs, case library, regulatory source index, notebooks, roadmap, ADR, and contribution guide.
- [ ] Publication checklist reflects the v0.1 PRD publication gate.
- [ ] The repo remains private and contains no personal job-preparation material or real client data.

## Blocked by

- `.scratch/banking-fraud-detection-lab-v0-1/issues/08-interpret-alerts-and-produce-governance-memo.md`
- `.scratch/banking-fraud-detection-lab-v0-1/issues/09-seed-case-library-with-pattern-linked-source-packs.md`
- `.scratch/banking-fraud-detection-lab-v0-1/issues/10-connect-regulatory-source-index-to-v0-1-exercises.md`
- `.scratch/banking-fraud-detection-lab-v0-1/issues/11-enforce-v0-1-quality-gates-in-ci.md`
