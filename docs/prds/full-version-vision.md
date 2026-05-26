# PRD: Full-Scope Banking Fraud Detection Lab

Status: draft for human review.

## Validation Role

This document is the final validation PRD for the full envisioned scope of
**Banking Fraud Detection Lab**. It should be used after v1.4 to decide whether
the project has delivered the complete intended curriculum.

The version-specific PRDs define how each release should be built. This PRD
defines what must be true when all releases are complete.

## Problem Statement

The project has a staged roadmap from v0.1 through v1.4. Without a final
validation PRD, each release could be locally successful while the complete lab
still fails to feel coherent, reproducible, source-disciplined, or useful as a
full banking fraud detection curriculum.

The final scope needs one acceptance document that validates the whole system:
core curriculum, advanced extensions, data model, notebooks, SQL exercises,
cases, regulatory notes, graph analytics, governance, production patterns,
quality gates, and public-facing boundaries.

## Solution

The full version is the completed v1.0 public core curriculum plus optional v1.1
through v1.4 advanced extensions. It must remain a local-first educational lab
that teaches practical banking fraud detection capability using deterministic
synthetic data, SQL, Python, notebooks, case interpretation, governance, graph
analytics, monitoring patterns, and optional advanced infrastructure.

The full version is not a production banking platform, not institution-sponsored
training, not legal or compliance advice, and not a reconstruction of real cases.

## Definition Of Done

The full version of **Banking Fraud Detection Lab** is the completed v1.0 public
core curriculum plus optional v1.1 through v1.4 advanced extensions.

The full version is done only when a reviewer can:

- Run the documented setup, linting, tests, notebook smoke checks, and data
  generation commands from a clean checkout.
- Complete the v1.0 core module sequence without hidden maintainer knowledge.
- Confirm that v1.1 through v1.4 are optional advanced extensions and do not
  destabilize the v1.0 core.
- Trace every module back to the same **Realistic synthetic data model**,
  **Progressive data views**, **Detection patterns**, and **Alert lifecycle**.
- Confirm that public-facing material uses synthetic-only data, careful source
  framing, no real-bank relationship claims, no legal-advice framing, and no real
  event reconstruction claims.

## Learner Experience

A learner should be able to start from the README, set up the environment, run
the tests, generate data, create the SQLite exercise database, and follow a clear
module sequence without hidden maintainer knowledge.

The complete learner journey should feel like this:

- Optionally use Python, pandas, SQL, and sklearn refresh material before the
  required module sequence, if the learner needs it.
- Understand the **Realistic synthetic data model** and the core entities:
  **Partner**, **Client**, **User**, **Banking relationship**, accounts,
  transactions, beneficiaries, sessions, alerts, cases, outcomes, and protected
  scenario answer keys.
- Move through **Progressive data views** that reveal complexity gradually instead
  of forcing learners into the full schema immediately.
- Learn the **Alert lifecycle** as an operational process, not as a single fraud
  label.
- Build SQL features against SQLite for joins, windows, cohorts, alert queues,
  feature extraction, and investigation workflows.
- Complete **Private-banking fraud detection** modules using Alpine Crest Private
  Bank relationship, ownership, account, counterparty, transaction, and
  relationship-manager context.
- Complete **Digital-banking fraud detection** modules using NovaBank Digital
  **Client**, **User**, session, device, beneficiary, payment, scam, mule, and
  account takeover context.
- Read public-source case material through **Detection pattern** templates that
  separate facts, interpretation, likely data signals, source quality,
  limitations, and learning exercises.
- Use regulatory source notes as educational anchors for analytics questions,
  documentation, explainability, alert handling, governance, and monitoring.
- Build graph features from existing tables and use network evidence in alert and
  case interpretation.
- Explain model, rule, and graph outputs through threshold analysis,
  false-positive review, model documentation, and governance memos.
- Run local production-pattern exercises for batch scoring, score tables, alert
  queues, reviewer actions, audit events, drift checks, and monitoring reports.
- Complete an end-to-end capstone that combines scenario briefing, synthetic data,
  SQL features, model scoring, alert review, limitations, governance, and
  communication.
- Optionally continue into digital assets, brokerage, NLP, and advanced
  production infrastructure without changing the v1.0 core path.

## User Stories

1. As a new learner, I want one documented start path, so that I can set up the lab and complete the core curriculum independently.
2. As a learner, I want one coherent synthetic banking world, so that concepts learned in early modules still apply in advanced modules.
3. As a learner, I want **Progressive data views**, so that complexity increases deliberately across the curriculum.
4. As a learner, I want **Private-banking fraud detection** and **Digital-banking fraud detection** to be equally first-class, so that the curriculum does not collapse into one context.
5. As a learner, I want SQL, Python, cases, governance, and monitoring to connect, so that the lab teaches the full analytic workflow.
6. As a learner, I want optional advanced tracks to be clearly marked, so that I can complete v1.0 before choosing deeper specialization.
7. As a maintainer, I want stable data and view contracts, so that modules can evolve without breaking the full curriculum.
8. As a maintainer, I want final quality gates, so that delivery can be validated objectively.
9. As a reviewer, I want clear public-facing boundaries, so that synthetic data, source discipline, and non-advice framing are preserved.
10. As a future contributor, I want extension rules, so that new work builds on the canonical entities, views, and lifecycle instead of creating disconnected modules.

## Complete Module Map

The full version should expose a stable core sequence:

- `00_foundations`: setup, schema tour, SQL feature extraction, **Alert lifecycle**,
  and metric basics.
- `01_private_banking_transaction_fraud`: Alpine Crest Private Bank baseline.
- `02_digital_scam_to_mule`: NovaBank Digital **Scam-to-mule flow** baseline.
- `03_alert_governance`: early alert interpretation, limitations, and governance
  memo, deepened by `07_interpretability_model_risk`.
- `04_private_banking_feature_engineering`: relationship, account, counterparty,
  ownership, signatory, and relationship-manager features.
- `05_digital_session_and_payment_fraud`: session, device, beneficiary, payment,
  account takeover, and mule-risk features.
- `06_graph_network_analytics`: NetworkX-first graph fraud patterns.
- `07_interpretability_model_risk`: explainability, validation, thresholding, and
  model documentation.
- `08_production_monitoring_patterns`: batch scoring, score tables, alert queues,
  reviewer actions, audit events, drift checks, and monitoring.
- `09_capstone`: end-to-end private-banking and digital-banking capstone variants.

The full version should also include unnumbered cross-cutting learning layers:

- Optional warm-up material for Python, pandas, SQL, and sklearn using the same
  synthetic data.
- Case and regulatory skill enrichment that links source packs, source quality,
  regulatory notes, and learner tasks into modules `00` through `09`.

The full version should also expose optional advanced modules:

- `10_digital_assets_crypto_fraud`: fiat on/off-ramp risk, wallet withdrawal risk,
  scam-to-crypto patterns, destination-risk scoring, and crypto governance notes.
- `11_brokerage_market_abuse_analytics`: instruments, orders, executions,
  holdings, suitability anomalies, account takeover trading, coordinated behavior,
  and trading-alert review.
- `12_nlp_communication_monitoring`: synthetic messages, support chats,
  relationship notes, complaint text, NLP features, summaries, and human-review
  limits.
- `13_advanced_production_infrastructure`: optional event contracts, micro-batch or
  streaming simulation, common scoring interfaces, dashboards, rollback, degraded
  mode, audit trails, and service-level monitoring concepts.

## End-State Architecture

The full version should be built around deep modules with stable interfaces:

- Synthetic data generator: deterministic datasets by seed, scale, and scenario
  configuration.
- Scenario injection: configurable **Detection patterns** with protected answer
  keys and realistic prevalence ranges.
- Schema contract: required tables, columns, relationships, data types, and
  documentation alignment.
- **Progressive data views**: module-specific learning surfaces that remain
  derived from the canonical model.
- SQL loader: SQLite-first loading with optional later exports.
- Evaluation utilities: precision, recall, PR-AUC, threshold summaries, alert
  volume, alert capacity, cost curves, and limitation-aware outputs.
- Case and regulatory validators: source discipline, front matter, linked modules,
  limitations, and no-advice wording checks.
- Graph utilities: NetworkX graph construction, features, and joins back to
  tabular views.
- Interpretability and governance utilities: explanations, threshold review,
  model documentation, monitoring requirements, and governance memo templates.
- Production-pattern utilities: batch scoring, score tables, alert decision tables,
  reviewer actions, audit events, drift checks, and monitoring summaries.
- Optional infrastructure adapters: advanced v1.4 services that never become
  mandatory for the v1.0 core curriculum.

## Implementation Decisions

- Keep the full curriculum local-first and reproducible.
- Keep SQLite first-class for the v1.0 core.
- Keep advanced infrastructure optional and isolated from the core path.
- Keep one canonical **Realistic synthetic data model** with additive advanced
  entities, not unrelated datasets per module.
- Keep **Progressive data views** as the learner-facing complexity-management
  mechanism.
- Keep the **Alert lifecycle** as the common investigation process across all
  modules.
- Keep **Detection pattern** metadata as the bridge between cases, data signals,
  features, graph evidence, models, alerts, governance, and monitoring.
- Keep case and regulatory material educational, source-disciplined, and
  limitation-aware.
- Keep protected scenario answer keys excluded from learner-facing outputs by
  default.
- Keep v1.1 through v1.4 as optional advanced extensions that regression-test the
  v1.0 core.
- Require every optional advanced extension to pass the full v1.0 test suite and
  all v1.0 core notebook smoke tests without changing the v1.0 learner path.

## End-State Data Model

The full data model should remain one coherent fictional banking world, not a set
of unrelated toy datasets.

The core model should include:

- Identity and relationship entities: **Partner**, **Client**, **User**, roles,
  partner roles, **Banking relationship**, and relationship-manager assignment.
- Banking entities: accounts, balances or balance snapshots where needed,
  transactions, counterparties, beneficiaries, and product or channel fields.
- Digital entities: sessions, devices, authentication events, beneficiary changes,
  payment events, IP and channel risk attributes, and account lifecycle signals.
- Alert entities: suspicious activities, alerts, cases, case outcomes, reviewer
  actions, and protected scenario answer keys.
- Learning entities: **Detection patterns**, scenario metadata, progressive views,
  feature definitions, model outputs, score records, and monitoring records.

Advanced extensions can add optional entities:

- Digital assets: wallets, exchanges, token transfers, chain transactions,
  on-ramp and off-ramp events, wallet-risk signals, and destination-risk records.
- Brokerage: instruments, orders, executions, holdings, positions, suitability
  attributes, market events, and trading alerts.
- Communications: conversations, messages, channels, participants, complaints,
  interaction notes, summaries, and communication-derived signals.
- Production infrastructure: event contracts, feature records, model deployment
  metadata, scoring events, drift events, rollback events, service-health records,
  and audit trails.

All advanced entities must connect back to the core model through **Client**,
**User**, **Partner**, **Banking relationship**, account, transaction, alert,
case, or **Detection pattern** relationships.

## Quality Bar

The full version is acceptable only if it remains reproducible, coherent, and
source-disciplined.

Required quality properties:

- Clean setup and test commands work from a fresh checkout.
- Tiny sample data is committed and deterministic.
- Medium and larger datasets can be generated locally without committing bulky
  data.
- SQLite exercises remain first-class for core modules.
- Featured notebooks run end-to-end on tiny data.
- Schema docs, data dictionary, generated data, SQL examples, and notebooks remain
  aligned.
- Case and regulatory docs remain source-disciplined, educational, and linked to
  learning tasks.
- Protected answer keys are excluded from learner-facing outputs by default.
- Metrics avoid simplistic headline accuracy and explain alert-volume and
  capacity tradeoffs.
- Governance content explains limitations and review boundaries without claiming
  certification or legal authority.
- Optional advanced modules regression-test the v1.0 core path.

## Testing And Validation Decisions

Final validation should combine automated gates and human review.

Automated gates:

- Clean setup, linting, and full test suite pass.
- Featured notebook smoke tests pass for every required v1.0 core module.
- Optional advanced-module smoke tests pass when their extras are installed.
- Deterministic sample regeneration matches committed tiny data.
- Medium dataset generation remains deterministic and laptop-feasible.
- SQLite loader and representative SQL examples pass.
- Schema contract, data dictionary, and **Progressive data view** docs remain
  aligned.
- Scenario prevalence, protected answer-key exclusion, referential integrity, and
  temporal invariants pass.
- Evaluation, threshold, cost, alert-capacity, graph, governance, and monitoring
  utilities pass behavior tests.
- Case metadata and regulatory-source validation pass.
- Public-facing terminology guardrails pass.

Human review gates:

- The learner path is coherent from foundations through capstone.
- Alpine Crest Private Bank and NovaBank Digital remain distinct but comparable.
- Advanced modules feel optional and additive, not required for v1.0.
- Case and regulatory material remains careful, source-disciplined, and
  educational.
- Governance and production-pattern language does not imply real-world deployment
  readiness.
- The capstone validates synthesis rather than repeating earlier exercises.

## Full-Scope Acceptance Criteria

- v1.0 core modules `00` through `09` are complete, documented, and runnable from
  a clean setup.
- v1.1 through v1.4 advanced modules are complete enough to demonstrate their
  intended advanced learning outcomes without changing the core path.
- The canonical data model supports all modules through documented tables,
  relationships, **Progressive data views**, and optional advanced entities.
- All modules tie learner work to **Detection patterns** and the **Alert
  lifecycle**.
- Private-banking modules use Alpine Crest Private Bank and relationship-led
  features.
- Digital-banking modules use NovaBank Digital and user/session/payment-led
  features.
- Graph, interpretability, governance, monitoring, and production-pattern modules
  reuse outputs from earlier track modules.
- The capstone requires scenario briefing, SQL features, model or rule scoring,
  alert review, limitations, governance, and communication.
- Optional advanced modules cover digital assets, brokerage, NLP communication
  monitoring, and advanced production infrastructure.
- The repository contains no real client data, no real-bank relationship claims,
  no real event reconstruction claims, and no legal or compliance advice.

## Validation Matrix

| Scope area | Must be true at final delivery | Evidence |
| --- | --- | --- |
| Foundation | Data model, SQLite path, generated data, docs, and tests are stable. | Setup commands, schema tests, data-dictionary tests, SQL tests, sample-regeneration evidence. |
| Private banking | Alpine Crest Private Bank modules cover relationship-led fraud detection end to end. | Track notebooks, feature tests, case links, regulatory notes, governance outputs. |
| Digital banking | NovaBank Digital modules cover user/session/payment-led fraud detection end to end. | Track notebooks, feature tests, case links, regulatory notes, governance outputs. |
| Cases and regulation | Source material maps to **Detection patterns** and learning tasks. | Case metadata validation, source-note validation, linked exercises, HITL review markers where needed. |
| Graph analytics | Graph features derive from canonical data and join back to alerts and cases. | NetworkX tests, graph notebooks, graph-feature joins, graph evidence in cases. |
| Governance | Explanations, thresholds, limitations, and model documents support alert decisions. | Interpretability tests, threshold tests, model-card templates, governance memo notebooks. |
| Monitoring | Batch scoring, alert queues, reviewer actions, audit events, and drift checks are local-first. | Production-pattern tests, monitoring notebooks, audit lineage checks. |
| Capstone | Learners synthesize the full core path without hidden guidance. | Capstone notebooks, rubric, protected answer-key checks, beta/v1.0 release checklist. |
| Advanced extensions | v1.1-v1.4 add optional depth without destabilizing v1.0. | Optional-module tests, core-regression tests, advanced docs, isolated dependencies. |
| Public boundaries | Public-facing material remains educational and synthetic-only. | Publication-language tests, source-discipline checks, human review. |

## What Good Looks Like

The finished lab should feel coherent to three audiences:

- Learners should see a practical path from data model to SQL features, modeling,
  alert review, governance, monitoring, and capstone synthesis.
- Maintainers should see a testable architecture where generator, schema, SQL,
  evaluation, cases, graph, governance, and monitoring modules can evolve without
  breaking each other.
- Reviewers should see a careful educational project with consistent terminology,
  synthetic-only data, clear disclaimers, source discipline, and no real-bank
  relationship claims.

## Non-Goals

The full version should not become:

- A real bank fraud platform.
- A legal or compliance advice source.
- A real case reconstruction project.
- Institution-sponsored training.
- A heavy infrastructure project where Kafka, Spark, Neo4j, PostgreSQL, or
  dashboards are required for the core learner path.
- A disconnected notebook collection with inconsistent schemas.
- A model-performance showcase detached from alert review, cases, and governance.

## Final Acceptance Picture

At full maturity, a reviewer should be able to run the documented quality gates,
walk the core learner path, inspect the capstone, and verify that optional
advanced modules extend the same model. If a module cannot explain how it uses
the canonical entities, **Detection patterns**, **Progressive data views**, and
the **Alert lifecycle**, it does not belong in the full version without redesign.
