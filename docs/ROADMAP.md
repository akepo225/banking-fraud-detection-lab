# Implementation Roadmap

This roadmap turns the v0.1 PRD into a staged development cycle for **Banking Fraud Detection Lab**.

The repo stays private until the v0.1 publication gate is met. The final version for this cycle is **v1.0: complete public core curriculum**.

## Development Principles

- Build deep modules first: stable, testable interfaces for data generation, scenario injection, schema validation, SQL loading, evaluation, and case metadata.
- Keep one **Realistic synthetic data model** and expose **Progressive data views** rather than creating incompatible toy schemas.
- Use **Alpine Crest Private Bank** for **Private-banking fraud detection** and **NovaBank Digital** for **Digital-banking fraud detection**.
- Keep SQL first-class and SQLite-first.
- Make governance, limitations, and careful metric interpretation visible from the beginning.
- Publish only educational material: no real client data, no real-bank affiliation claims, no legal advice, and no reconstruction claims for public cases.

## Release Sequence

### Phase 0: Private Skeleton

Status: complete.

Purpose: establish the private public-ready repo shape before implementation work begins.

Deliverables:

- [x] Repository skeleton.
- [x] Public name and two-track scope.
- [x] Split licensing posture.
- [x] ADR for scope broadening.
- [x] Local markdown issue tracker setup.
- [x] v0.1 PRD under `needs-triage`.
- [x] PRD broken into implementation issues.

Exit criteria:

- The PRD is accepted for implementation.
- Initial implementation issues are created and triaged.

### v0.1: Private MVP And Publication Gate

Purpose: make the repo credible enough to publish, while still small enough to finish.

Learner outcome:

A learner can install the repo, inspect the schema, generate data, run SQL feature extraction, complete one private-banking baseline, complete one digital **Scam-to-mule flow** baseline, and read initial case/regulatory notes.

Implementation workstreams:

- **Schema and Data Dictionary**: document the canonical tables, relationships, money fields, label semantics, and **Alert lifecycle**.
- **Synthetic Data Generator**: generate partners, roles, banking relationships, accounts, transactions, clients, users, sessions, payment beneficiaries, suspicious activities, alerts, cases, case outcomes, and protected scenario answer keys.
- **Scenario Injection**: support private-banking transaction fraud and digital scam-to-mule fraud through configurable scenario settings.
- **Progressive Data Views**: expose starter views for foundations, private-banking baseline, digital baseline, and governance exercises.
- **SQLite Loader**: load generated tables into a local SQLite database for SQL exercises.
- **Evaluation Utilities**: provide precision/recall, PR-AUC, alert capacity, cost curves, and limitation-aware summaries.
- **Notebooks**: build setup/data tour, SQL feature extraction, private-banking transaction fraud baseline, digital scam-to-mule baseline, and alert governance notebooks.
- **Case Library Seed**: add one source pack per v0.1 learning area.
- **Regulatory Source Index**: add Swiss AMLA, AMLO, FINMA, APP scam/payment guidance where relevant, FATF typologies, and model-risk/governance references.
- **Quality Gates**: add deterministic generator tests, referential-integrity tests, scenario-prevalence tests, schema/data-dictionary checks, SQL-loader tests, notebook smoke tests, and lightweight CI.

Exit criteria:

- The repo remains free of personal job-preparation material and real client data.
- README, disclaimer, split licensing, ADR, and contribution guidance are complete.
- The **Realistic synthetic data model** and data dictionary are documented.
- The deterministic generator produces tiny sample data and larger local datasets.
- SQLite loader supports the first SQL exercises.
- At least two featured notebooks run end-to-end on tiny sample data.
- Seeded case library and regulatory source index are present.
- Tests cover generator determinism, referential integrity, scenario prevalence ranges, schema/data-dictionary alignment, SQL loading, and notebook smoke execution.
- Lightweight CI runs linting and tests.

Publication decision:

- After v0.1 passes, decide whether to publish publicly or keep private for additional polish.

### v0.2: Foundations And Data Model Hardening

Purpose: make the shared foundation strong enough to support all later modules.

Learner outcome:

A learner understands the canonical data model, can write SQL against the core tables, can reason about alert lifecycle labels, and can generate datasets at multiple scales.

Deliverables:

- Expanded schema documentation with ERD diagrams and module-specific views.
- Data dictionary coverage for all v0.1 tables and columns.
- Stronger generator configuration for small, medium, and large datasets.
- More realistic temporality for KYC risk, relationship-manager assignment, user authorizations, account status, alerts, and case outcomes.
- SQL foundations exercises for joins, windows, cohorts, alert queues, and feature extraction.
- Optional warm-up notebooks for Python, pandas, SQL, and sklearn using the same synthetic data.
- Dataset quality report generated from tests or validation scripts.

Exit criteria:

- Learners can complete the shared foundations without needing the private-banking or digital-banking modules.
- All schema docs match generated outputs.
- Medium dataset generation remains deterministic and performant on a laptop.

### v0.3: Private-Banking Fraud Detection Track

Purpose: deepen **Private-banking fraud detection** around high-value transaction monitoring and relationship context.

Learner outcome:

A learner can detect, explain, and investigate private-banking transaction anomalies using relationship, account, counterparty, and relationship-manager context.

Deliverables:

- Expanded Alpine Crest private-banking scenario set.
- Relationship-manager assignment and effective-dated responsibility exercises.
- Beneficial ownership and authorized signatory joins.
- Account and transaction typology expansion for wires, FX, fees, and investment-related flows.
- Private-banking feature library for amount-to-AUM ratios, new counterparty behavior, off-hours activity, cross-border movement, velocity changes, and relationship-manager concentration.
- Notebook for private-banking feature engineering.
- Notebook for private-banking supervised baseline and threshold tuning.
- Case-library entries for private-banking transaction fraud and control failures.
- Regulatory notes connecting Swiss AMLA, AMLO, FINMA, and model governance to analytics decisions.

Exit criteria:

- The private-banking track has a coherent path from data model to features, baseline model, alert interpretation, and governance memo.
- Learners can explain why each feature is tied to a detection pattern.

### v0.4: Digital-Banking Fraud Detection Track

Purpose: deepen **Digital-banking fraud detection** around scams, mule accounts, account takeover, and e-banking telemetry.

Learner outcome:

A learner can model online-bank fraud using **Client**, **User**, device, session, beneficiary, payment, alert, and case data.

Deliverables:

- Expanded NovaBank Digital scenario set for **Scam-to-mule flow**, account takeover, onboarding abuse, and suspicious beneficiary changes.
- Device/session telemetry exercises using user agent, app/browser version, device fingerprint hash, IP country, ASN risk, coarse geolocation, VPN/proxy flag, authentication method, session events, and beneficiary-change events.
- SQL feature extraction for session risk, beneficiary novelty, payment velocity, account age, shared devices, pass-through behavior, and network position.
- Notebook for digital scam-to-mule feature engineering.
- Notebook for account takeover and suspicious session detection.
- Notebook for alert triage and noisy case outcomes.
- Case-library entries for APP scams, mule-account behavior, online-bank control failures, and payment-fraud guidance.
- Regulatory notes for Swiss anchors plus selected EU/UK APP scam, strong customer authentication, and operational-resilience references.

Exit criteria:

- The digital-banking track has a coherent path from data model to features, baseline model, alert interpretation, and governance memo.
- Learners can explain the difference between APP scams, account takeover, and mule-account behavior.

### v0.5: Case Library And Regulatory Skill Layer

Purpose: turn the repo from a notebook collection into a pattern-driven learning resource.

Learner outcome:

A learner can read public cases, extract **Detection patterns**, identify likely data signals, and connect regulatory sources to analytics and governance tasks.

Deliverables:

- Detection-pattern-first case index.
- YAML front matter for case metadata: pattern, track, regulator, product, geography, source quality, and linked modules.
- Case templates with summary, source links, facts vs interpretation, detection patterns, data signals, exercises, regulatory hooks, and limitations.
- Source-quality rubric and contributor checklist.
- Regulatory source index organized by learning use: analytics question, control, documentation, explainability, alert handling, governance.
- Validation checks for required case metadata and regulatory-source structure.

Exit criteria:

- Every core module links to at least one public case or source pack.
- Case documents clearly avoid reconstructing real events.
- Regulatory notes avoid legal advice and use official-source links.

### v0.6: Graph And Network Analytics

Purpose: introduce relationship and transaction networks after learners understand core tabular fraud analytics.

Learner outcome:

A learner can represent clients, partners, accounts, beneficiaries, counterparties, devices, and transactions as networks and detect connected fraud patterns.

Deliverables:

- NetworkX-first graph module.
- Private-banking network exercises for beneficial ownership, shared counterparties, related entities, and circular structures.
- Digital-banking network exercises for mule rings, shared devices, shared beneficiaries, and pass-through clusters.
- Graph feature extraction for connected components, degree, centrality, community, path length, and suspicious bridge nodes.
- Notebook for graph-based fraud-ring detection.
- Optional Neo4j export, explicitly not required for core learning.
- Case-library entries for graph/network detection patterns.

Exit criteria:

- Learners can build graph features from the existing data model without needing a separate graph-only dataset.
- NetworkX examples run locally without infrastructure.

### v0.7: Interpretability, Governance, And Model Risk

Purpose: make governance and interpretability a dedicated competency rather than scattered notes.

Learner outcome:

A learner can explain model behavior, document limitations, choose thresholds, and write governance-ready fraud model summaries.

Deliverables:

- Dedicated interpretability module using feature importance, partial dependence or equivalent explanations, and optional SHAP where appropriate.
- Threshold selection exercises based on alert capacity, false-positive costs, investigation costs, and missed-fraud costs.
- Model documentation template for fraud detection systems.
- Validation and monitoring checklist for drift, stability, false-positive concentration, segment fairness, and data quality.
- Governance memo notebook that converts technical outputs into stakeholder language.
- Regulatory source notes for model risk, explainability, documentation, and validation.

Exit criteria:

- Every featured model notebook links to an interpretability or governance exercise.
- Learners can explain why a model should not be judged by headline accuracy.

### v0.8: Production Patterns And Monitoring

Purpose: teach production concepts through lightweight runnable patterns before heavy infrastructure.

Learner outcome:

A learner can move from notebook scoring to batch scoring, simple APIs, monitoring tables, and production-style alert review without needing Kafka, Spark, or Neo4j.

Deliverables:

- Batch scoring pipeline over generated datasets.
- Simple scoring service or command interface.
- Monitoring tables for model scores, thresholds, alert decisions, reviewer actions, and audit events.
- Drift and data-quality monitoring notebook.
- Alert-review queue exercise.
- Optional advanced notes for PostgreSQL deployment.
- Clear boundary for what full real-time infrastructure would add later.

Exit criteria:

- Learners can run a local batch scoring flow and inspect generated alerts.
- Monitoring outputs are tied to governance and alert lifecycle concepts.

### v0.9: Capstone And Public Beta

Purpose: integrate the curriculum into a complete capstone project and prepare for public release.

Learner outcome:

A learner completes an end-to-end banking fraud detection lab from scenario brief through synthetic data, SQL features, model, alert review, interpretability, governance memo, and presentation.

Deliverables:

- Capstone scenario brief with private-banking and digital-banking variants.
- Capstone datasets generated from hidden scenario answer keys.
- Capstone rubric for technical analysis, fraud-domain reasoning, SQL quality, model evaluation, alert interpretation, governance, and communication.
- Capstone presentation template.
- Full README polish with screenshots or schema previews.
- Public issue templates and contributor guidance.
- Documentation pass for all modules.
- CI hardening for featured notebooks.

Exit criteria:

- A learner can complete the capstone without hidden maintainer knowledge.
- Public-facing docs make the repo understandable to readers, learners, and contributors.
- All core notebooks run from a clean setup.

### v1.0: Complete Public Core Curriculum

Purpose: deliver the complete public core curriculum for **Banking Fraud Detection Lab**.

Learner outcome:

A learner can move from foundations to private-banking fraud detection, digital-banking fraud detection, case interpretation, graph analytics, interpretability, production patterns, and capstone delivery.

Required modules:

- `00_foundations`: setup, schema tour, SQL feature extraction, alert lifecycle, and metric basics.
- `01_private_banking_transaction_fraud`: Alpine Crest private-banking transaction fraud baseline.
- `02_digital_scam_to_mule`: NovaBank Digital scam-to-mule baseline.
- `03_alert_governance`: alert interpretation, limitations, and governance memo.
- `04_private_banking_feature_engineering`: relationship, account, counterparty, and RM-context features.
- `05_digital_session_and_payment_fraud`: session, device, beneficiary, and payment-risk features.
- `06_graph_network_analytics`: NetworkX-first graph fraud patterns.
- `07_interpretability_model_risk`: explainability, validation, thresholding, and model documentation.
- `08_production_monitoring_patterns`: batch scoring, score tables, alert queues, and monitoring.
- `09_capstone`: end-to-end capstone project.

v1.0 acceptance criteria:

- All required modules have runnable featured notebooks.
- The **Realistic synthetic data model** supports all required modules through **Progressive data views**.
- Tiny sample data is committed and medium/large data can be generated locally.
- SQLite exercises exist for core feature extraction and investigation workflows.
- Case library covers private banking, digital banking, regulatory/governance, and graph/network patterns.
- Regulatory source index covers Swiss anchors and selected EU/UK/global references where they support detection patterns.
- Tests cover generator behavior, schema contracts, SQL loading, evaluation utilities, case metadata, regulatory source structure, and notebook smoke execution.
- CI passes on a clean checkout.
- README, roadmap, contribution guide, disclaimers, licenses, and ADRs are consistent.
- The repo contains no real client data, no job-preparation material, no real-bank affiliation claims, and no legal advice.

## Post-1.0 Advanced Tracks

These are intentionally outside the v1.0 core curriculum.

### v1.1: Digital Assets And Crypto Fraud

- Fiat on/off-ramp risk.
- Wallet withdrawal risk.
- Scam and mule overlap.
- Destination-risk scoring.
- Crypto regulatory source notes.

### v1.2: Brokerage And Market-Abuse Analytics

- Instruments, orders, executions, and suitability.
- Unauthorized trading patterns.
- Market-abuse indicators.
- Cash and digital-asset withdrawals from brokerage accounts.

### v1.3: NLP And Communication Monitoring

- Synthetic communications linked to employees, clients, cases, and scenarios.
- Insider-risk and collusion indicators.
- Case-note summarization and investigation support.

### v1.4: Advanced Production Infrastructure

- Optional PostgreSQL deployment.
- Optional Neo4j graph export.
- Optional Kafka or stream-processing lab.
- Optional dashboard or API deployment.

## Deep Modules To Build Early

These modules should be designed as stable interfaces because many curriculum modules will depend on them.

### Synthetic Data Generator

Responsibility: produce deterministic banking datasets by seed, scale, and scenario configuration.

Why deep: it hides schema complexity while giving notebooks a simple way to request realistic data.

### Scenario Injection

Responsibility: inject private-banking transaction fraud, digital scam-to-mule fraud, and later scenarios with configurable prevalence and protected answer keys.

Why deep: it lets modules teach different detection patterns without rewriting the generator.

### Schema Contract

Responsibility: define required tables, columns, relationships, data types, and documented meanings.

Why deep: it keeps generated data, docs, SQL exercises, and notebooks aligned.

### SQL Loader

Responsibility: load generated data into SQLite and later optional PostgreSQL.

Why deep: it gives every module the same SQL exercise surface.

### Evaluation And Governance Utilities

Responsibility: calculate fraud-appropriate metrics, alert-capacity summaries, cost curves, and limitation-aware outputs.

Why deep: it prevents every notebook from reinventing metric logic.

### Case Metadata Validator

Responsibility: validate case-library front matter and required sections.

Why deep: it protects the public credibility of the case library as it grows.

## Suggested Issue Breakdown

Start by creating implementation issues in this order:

1. Generate and inspect a minimal banking world.
2. Trace suspicious activity through the alert lifecycle.
3. Query generated data through SQLite.
4. Produce an alert-aware metrics report from generated cases.
5. Complete foundations data tour and SQL feature notebook.
6. Detect Alpine Crest private-banking transaction fraud.
7. Detect NovaBank Digital scam-to-mule flow.
8. Interpret alerts and produce a governance memo.
9. Seed case library with pattern-linked source packs.
10. Connect regulatory source index to v0.1 exercises.
11. Enforce v0.1 quality gates in CI.
12. Polish publication-ready README and release checklist.
13. Run v0.1 publication gate review.

## Roadmap Governance

- Update this roadmap whenever a release boundary changes.
- Record hard-to-reverse scope or architecture changes as ADRs.
- Current roadmap-shaping ADRs are ADR-0001 through ADR-0005, covering scope,
  canonical data model and **Progressive data views**, SQLite-first local-first
  core, optional advanced extensions, and GitHub Issues as the operational source
  of truth.
- Keep implementation issues linked back to the PRD and this roadmap.
- Do not add advanced tracks into the v1.0 core without explicitly changing this roadmap.
