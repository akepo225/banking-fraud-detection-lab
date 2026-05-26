# Cross-Version Coherence Review

Status: draft self-review.

This review checks the v0.2 through v1.4 PRD drafts as one sequence. It is a
planning artifact for human review before any PRD is promoted to GitHub Issues.

## Sequence Check

| Version | Primary role | Depends on | Hands off to | Self-review result |
| --- | --- | --- | --- | --- |
| v0.2 | Shared foundation hardening | v0.1 MVP artifacts | v0.3, v0.4, and all later modules | Coherent if it remains foundation-only and avoids track depth. |
| v0.3 | Alpine Crest Private Bank depth | v0.2 schema, temporal logic, views | v0.5 case layer, v0.6 graph, v0.7 governance, v0.8 monitoring | Coherent if relationship context drives features. |
| v0.4 | NovaBank Digital depth | v0.2 foundation and v0.3 track conventions | v0.5 case layer, v0.6 graph, v0.7 governance, v0.8 monitoring | Coherent if **Client** and **User** stay distinct. |
| v0.5 | Cross-cutting case and regulatory skill layer | v0.3 and v0.4 track content | v0.6 graph narratives and v0.7 governance templates | Coherent if it enriches existing modules and turns sources into exercises, not passive reading. |
| v0.6 | Graph and network analytics | v0.2 entities, v0.3/v0.4 track data, v0.5 cases | v0.7 graph explanations and v0.8 graph monitoring | Coherent if NetworkX remains required and graph databases stay optional. |
| v0.7 | Interpretability, governance, and model risk | v0.3/v0.4 models, v0.5 cases, v0.6 graph evidence | v0.8 thresholds, model docs, and monitoring baselines | Coherent if it deepens `03_alert_governance` and explanations support alert decisions rather than replace judgment. |
| v0.8 | Production patterns and monitoring | v0.7 governance artifacts plus earlier models and views | v0.9 capstone and v1.0 production-pattern module | Coherent if local-first patterns do not imply production readiness. |
| v0.9 | Capstone and public beta | v0.2 through v0.8 | v1.0 hardening and release checklist | Coherent if it integrates rather than expands. |
| v1.0 | Complete public core curriculum | v0.9 beta review | v1.1 through v1.4 optional advanced tracks | Coherent if it locks and hardens the core. |
| v1.1 | Digital assets and crypto fraud | v1.0 core foundations | v1.2 event-risk patterns, v1.3 scam communications, v1.4 event contracts | Coherent if banking on/off-ramp context stays central. |
| v1.2 | Brokerage and market-abuse analytics | v1.0 core and optional v1.1 patterns | v1.3 trading communications and v1.4 order events | Coherent if it stays connected to banking fraud detection. |
| v1.3 | NLP and communication monitoring | v1.0 core, optional v1.1/v1.2 scenarios | v1.4 NLP serving and drift monitoring | Coherent if synthetic text stays support evidence, not automated decisions. |
| v1.4 | Advanced production infrastructure | v1.0 production patterns plus optional v1.1-v1.3 event types | Future resilience or deployment templates | Coherent if it remains optional and service dependencies do not leak backward. |

## Dependency Integrity

- v0.2 is the last place broad shared schema and temporal semantics should change without explicit review.
- v0.3 and v0.4 are deliberately symmetrical track releases but use different feature logic.
- v0.3 adds `04_private_banking_feature_engineering` on top of the v0.1 `01` baseline, and v0.4 adds `05_digital_session_and_payment_fraud` on top of the v0.1 `02` baseline.
- v0.5 waits until both tracks exist so cases and regulatory notes can be cross-track.
- v0.6 waits until case context exists so graph analytics has investigation purpose.
- v0.7 waits until models, cases, and graph features exist so governance can explain real artifacts.
- v0.8 waits until v0.7 creates threshold and model documentation artifacts.
- v0.9 and v1.0 avoid new conceptual layers and focus on integration, beta review, and hardening.
- v1.1 through v1.4 are explicitly optional and must regression-test the v1.0 core path.
- Optional warm-up material is owned by v0.2 and remains outside the required numbered module sequence.

## Terminology Review

- **Partner**, **Client**, **User**, and **Banking relationship** are used with the glossary meanings.
- **Alpine Crest Private Bank** remains the private-banking setting.
- **NovaBank Digital** remains the digital-banking setting.
- **Detection pattern**, **Alert lifecycle**, **Realistic synthetic data model**, and **Progressive data view** are present across the sequence.
- Retired personal-positioning terms were scanned and removed from PRD content.

## Scope Risks To Watch During Issue Breakdown

- v0.2 can sprawl if medium/large generation, ERDs, SQL exercises, and data-quality reports are not sliced carefully.
- v0.3 and v0.4 can diverge if they do not share pattern metadata and notebook conventions.
- v0.5 can become documentation-only if each source pack does not produce a concrete learner task.
- v0.6 can become too abstract if graph features do not join back to alerts and cases.
- v0.7 can become too theoretical if model documentation is not generated from actual notebook outputs.
- v0.8 can become too infrastructural if batch scoring and local tables are not the default.
- v0.9 and v1.0 can slip into new features unless beta findings are triaged as blockers or follow-ups.
- v1.1 through v1.4 can destabilize the core unless they are optional extras with regression tests.

## Audit Mitigations Incorporated

- v0.5 is now explicitly cross-cutting enrichment, not a standalone numbered module.
- v0.3 and v0.4 now state how they build on the v0.1 baseline notebooks and add modules `04` and `05`.
- v0.2 now owns optional warm-up material and includes a v0.1 state assessment.
- v0.7 now owns deepening of `03_alert_governance` while adding `07_interpretability_model_risk`.
- v0.3 now defines the shared track convention contract and v0.4 imports it.
- v0.9 explicitly excludes new scenario families, new **Detection patterns**, and new data model entities.
- v1.0 now triages beta findings as blockers or follow-ups and rejects new features.
- v1.1 through v1.4 now share a concrete v1.0 regression-test contract.
- The PRD index now links the canonical glossary and ADR reference.

## Review Outcome

The draft PRDs form a coherent sequence. The main design constraint is to keep
each release focused on its role in the chain: foundation, track depth, source
skill, graph evidence, governance, production patterns, capstone, core hardening,
then optional advanced extensions.
