# Draft PRDs

Status: draft local review artifacts.

These PRDs expand the roadmap from v0.2 through v1.4. They are not GitHub
issues yet. The intended workflow is human review first, then issue-tracker
publication and triage after scope is accepted.

The [full-scope validation PRD](full-version-vision.md) defines what the completed
curriculum must look like and how final delivery should be validated after the
v1.0 core and v1.1-v1.4 optional advanced extensions are in place.

Terminology follows the glossary in `CONTEXT.md` and ADR-0001. PRD issue
breakdown should preserve those definitions unless a new ADR changes them.

## Review Order

1. [v0.2 Foundations And Data Model Hardening](v0.2-foundations-data-model-hardening.md) ([GitHub #45](https://github.com/akepo225/banking-fraud-detection-lab/issues/45))
2. [v0.3 Private-Banking Fraud Detection Track](v0.3-private-banking-fraud-detection-track.md) ([GitHub #46](https://github.com/akepo225/banking-fraud-detection-lab/issues/46))
3. [v0.4 Digital-Banking Fraud Detection Track](v0.4-digital-banking-fraud-detection-track.md) ([GitHub #47](https://github.com/akepo225/banking-fraud-detection-lab/issues/47))
4. [v0.5 Case Library And Regulatory Skill Layer](v0.5-case-library-regulatory-skill-layer.md) ([GitHub #48](https://github.com/akepo225/banking-fraud-detection-lab/issues/48))
5. [v0.6 Graph And Network Analytics](v0.6-graph-network-analytics.md) ([GitHub #49](https://github.com/akepo225/banking-fraud-detection-lab/issues/49))
6. [v0.7 Interpretability, Governance, And Model Risk](v0.7-interpretability-governance-model-risk.md) ([GitHub #50](https://github.com/akepo225/banking-fraud-detection-lab/issues/50))
7. [v0.8 Production Patterns And Monitoring](v0.8-production-patterns-monitoring.md) ([GitHub #51](https://github.com/akepo225/banking-fraud-detection-lab/issues/51))
8. [v0.9 Capstone And Public Beta](v0.9-capstone-public-beta.md) ([GitHub #52](https://github.com/akepo225/banking-fraud-detection-lab/issues/52))
9. [v1.0 Complete Public Core Curriculum](v1.0-complete-public-core-curriculum.md) ([GitHub #53](https://github.com/akepo225/banking-fraud-detection-lab/issues/53))
10. [v1.1 Digital Assets And Crypto Fraud](v1.1-digital-assets-crypto-fraud.md) ([GitHub #54](https://github.com/akepo225/banking-fraud-detection-lab/issues/54))
11. [v1.2 Brokerage And Market-Abuse Analytics](v1.2-brokerage-market-abuse-analytics.md) ([GitHub #55](https://github.com/akepo225/banking-fraud-detection-lab/issues/55))
12. [v1.3 NLP And Communication Monitoring](v1.3-nlp-communication-monitoring.md) ([GitHub #56](https://github.com/akepo225/banking-fraud-detection-lab/issues/56))
13. [v1.4 Advanced Production Infrastructure](v1.4-advanced-production-infrastructure.md) ([GitHub #57](https://github.com/akepo225/banking-fraud-detection-lab/issues/57))
14. [Full-Scope Validation PRD](full-version-vision.md) ([GitHub #58](https://github.com/akepo225/banking-fraud-detection-lab/issues/58))

See also the [cross-version coherence review](cross-version-coherence-review.md) and the
[cross-version coherence audit](cross-version-coherence-audit.md) (2026-05-26).

## Coherence Rules

- v0.2 hardens shared foundations only; it should not implement full track depth.
- v0.3 and v0.4 are sibling track releases built on v0.2, not parallel schemas.
- v0.5 turns cases and regulatory sources into a cross-cutting skill layer after
  both tracks exist; it is not a standalone numbered core module.
- v0.6 uses v0.5 cases to introduce graph evidence, not graph infrastructure first.
- v0.7 turns model, rule, graph, and case evidence into governance-ready explanations.
- v0.8 teaches production patterns locally and should not imply production readiness.
- v0.9 integrates the full core path as beta; v1.0 hardens it rather than expanding scope.
- v1.1 through v1.4 are optional advanced extensions and must not destabilize v1.0.

## Shared Advanced Regression Contract

Every optional advanced PRD from v1.1 through v1.4 must preserve the v1.0 core.
At implementation time, that means the advanced release must pass the full v1.0
test suite and all v1.0 core notebook smoke tests without requiring changes to the
v1.0 learner path. Optional dependencies may add extra checks, but they must not
be required for core setup.

## Self-Review Standard

Each PRD includes a self-review checklist. A PRD should not be converted into
implementation issues until the checklist is still true after review against all
other PRDs in this directory.
