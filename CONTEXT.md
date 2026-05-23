# Banking Fraud Detection Lab

This context defines the core language for the public banking fraud detection curriculum.

## Language

**Banking Fraud Detection Lab**:
The public curriculum repository for banking fraud detection data science.
_Avoid_: Julius Baer training, job-preparation repo

**Target learner**:
An analytics, financial-crime, product, or junior data-science practitioner building hands-on fraud detection data science capability.
_Avoid_: absolute beginner, senior ML engineer only

**Fraud detection track**:
A curriculum path for a banking context with its own data model modules, fraud scenarios, and regulatory concerns.
_Avoid_: unrelated notebook collection

**Private-banking fraud detection**:
Fraud detection in wealth management and private banking contexts.
_Avoid_: treating private banking as the whole curriculum

**Digital-banking fraud detection**:
Fraud detection in online banks, fintech banks, digital brokerages, e-banking, payment platforms, and digital-asset services.
_Avoid_: treating digital banking as optional comparison material

**Public-domain banking case study**:
A real, publicly reported banking or financial-crime case used for educational analysis without implying institutional affiliation.
_Avoid_: proprietary case study, official bank training

**Detection pattern**:
A recurring observable signal, behavior, network structure, or control failure that can be translated into analytics or model features.
_Avoid_: famous scandal with no analytic lesson

**Realistic synthetic data model**:
A consistent fictional banking data model used across the curriculum to teach durable analytics habits without using real client data.
_Avoid_: toy-only dataset, actual bank reconstruction

**Progressive data view**:
A simplified extract from the canonical data model that exposes only the tables and columns needed at a learner's current stage.
_Avoid_: separate incompatible beginner schema

**Alert lifecycle**:
The path from suspicious activity through alert generation, case opening, investigation outcome, and confirmed fraud determination.
_Avoid_: single is_fraud flag as the whole truth

**Alpine Crest Private Bank**:
The fictional private bank used for private-banking scenarios.
_Avoid_: Julius Baer stand-in

**NovaBank Digital**:
The fictional online bank or digital brokerage used for digital-banking scenarios.
_Avoid_: Revolut or Swissquote stand-in

**Partner**:
A natural or legal person represented in the fictional bank's core data model.
_Avoid_: customer record

**Client**:
The bank's end customer in learner-facing explanations.
_Avoid_: customer

**User**:
The digital login identity that authenticates sessions and acts through e-banking or app channels.
_Avoid_: legal customer, partner

**Banking relationship**:
The Swiss-bank-style container that groups related partners, accounts, portfolios, and service arrangements.
_Avoid_: bare relationship, relationship manager

**Scam-to-mule flow**:
A digital-banking fraud scenario where a scam victim authorizes a payment that moves into a mule or rented account and is rapidly passed onward.
_Avoid_: treating scams and mule accounts as unrelated modules

## Relationships

- **Banking Fraud Detection Lab** has two first-class **Fraud detection tracks**: **Private-banking fraud detection** and **Digital-banking fraud detection**.
- **Alpine Crest Private Bank** supports private-banking scenarios; **NovaBank Digital** supports digital-banking scenarios.
- The **Realistic synthetic data model** should expose **Progressive data views** as learners advance.
- Public cases can inspire **Detection patterns**, but synthetic data must not claim to reconstruct real events.
- The **Alert lifecycle** should be modeled explicitly rather than reduced to a single fraud label.

## Example Dialogue

> **Dev:** "Should we use one flat transaction table for every lesson?"
> **Domain expert:** "No. Use a **Realistic synthetic data model**, then expose **Progressive data views** so early lessons stay approachable."

## Flagged Ambiguities

- "Fraud detection" was ambiguous between private-banking-only fraud and broader online-bank fraud; resolved: both are first-class tracks.
- "User" was ambiguous between a legal customer and a login identity; resolved: **Client** is the legal customer and **User** is the digital login identity.
- "Relationship" was ambiguous between **Banking relationship** and relationship manager; resolved: use **Banking relationship** for the client/account container.

## Agent Progress Log

### Issue #3: Trace Suspicious Activity Through The Alert Lifecycle — DONE

- Branch: feat/issue-3-implementation
- PR: #16
- Tests added: 5 focused lifecycle/protected-key/prevalence tests plus expanded schema-derived FK coverage; all local tests passing
- Key files changed: `src/banking_fraud_lab/generators/minimal_world.py`, `src/banking_fraud_lab/schema/tables.py`, `tests/test_generator_entities.py`, `data/sample/`, `docs/schema/`, `.github/workflows/ci.yml`
- Notes: Implemented explicit suspicious activity, alert, case, outcome, confirmed-fraud, and protected-answer-key lifecycle. Applied narrow CI workflow hardening from review feedback without changing the configured CI commands. Local `uv run ruff check .`, `uv run pytest` (49 passed), and CodeRabbit local review passed after PR review fixes. GitHub PR checks passed after Actions budget became available.

### Issue #4: Query Generated Data Through SQLite — DONE

- Branch: feat/issue-4-implementation
- PR: #17
- Tests added: 5 SQLite loader/schema/query tests; all local tests passing
- Key files changed: `src/banking_fraud_lab/sqlite_loader.py`, `src/banking_fraud_lab/create_sqlite.py`, `src/banking_fraud_lab/__init__.py`, `tests/test_sqlite_loader.py`, `sql/examples/`, `sql/README.md`
- Notes: Added a schema-driven SQLite loader with primary-key and foreign-key DDL, learner-facing default views, full replacement behavior that removes protected tables, a module CLI, representative joins, and a window-function query. Local `uv run ruff check .` and `uv run pytest` passed after CodeRabbit review fixes; GitHub CI and CodeRabbit passed before merge.

### Issue #5: Produce An Alert-Aware Metrics Report — DONE

- Branch: feat/issue-5-implementation
- PR: #18
- Tests added: 6 focused evaluation tests covering 8 cases; all local tests passing
- Key files changed: `src/banking_fraud_lab/evaluation.py`, `src/banking_fraud_lab/__init__.py`, `tests/test_evaluation_metrics.py`, `tests/test_package_import.py`, `docs/evaluation/metrics.md`
- Notes: Added `evaluate_alert_scores()` for precision, recall, PR-AUC, alert volume, capacity utilization, threshold summaries, cost curves, and a limitation-aware summary that keeps simplistic accuracy claims out of scope. Local `uv run ruff check .` and `uv run pytest` passed after review fixes; GitHub CI passed and CodeRabbit's actionable findings were addressed before merge.

### Issue #6: Complete Foundations Data Tour And SQL Feature Notebook — DONE

- Branch: feat/issue-6-implementation
- PR: #20
- Tests added: 1 notebook execution smoke test; all local tests passing
- Key files changed: `notebooks/00_foundations/foundations_data_tour.ipynb`, `tests/test_foundations_notebook.py`, `notebooks/README.md`
- Notes: Added the shared foundations path through deterministic tiny data generation, Progressive data views, SQLite loading, SQL feature extraction, Alert lifecycle inspection, and `evaluate_alert_scores()`. Local `uv run ruff check .`, notebook smoke execution, and `uv run pytest` (63 passed) succeeded; GitHub CI passed before merge.

### Issue #7: Detect Alpine Crest Private-Banking Transaction Fraud — DONE

- Branch: feat/issue-7-implementation
- PR: #21
- Tests added: 5 private-banking scenario/notebook tests; all local tests passing
- Key files changed: `src/banking_fraud_lab/generators/private_banking.py`, `notebooks/01_private_banking_transaction_fraud/alpine_crest_baseline.ipynb`, `tests/test_private_banking_scenario.py`, `tests/test_private_banking_notebook.py`, package exports
- Notes: Added configurable Alpine Crest Private Bank transaction-fraud injection with protected answer keys, learner-facing views, relationship-manager and Partner/Role/Banking relationship context, one operational false-positive case, and a transparent scoring-rule notebook with alert-aware threshold metrics. Local `uv run ruff check .` and `uv run pytest` (68 passed) succeeded; GitHub CI passed before merge.

### Issue #8: Detect NovaBank Digital Scam-To-Mule Flow — DONE

- Branch: feat/issue-8-implementation
- PR: #22
- Tests added: 6 digital scenario/notebook tests; all local tests passing
- Key files changed: `src/banking_fraud_lab/generators/digital_banking.py`, `src/banking_fraud_lab/schema/tables.py`, `src/banking_fraud_lab/generators/minimal_world.py`, `notebooks/02_digital_scam_to_mule/novabank_scam_to_mule_baseline.ipynb`, `tests/test_digital_scam_to_mule_scenario.py`, `tests/test_digital_scam_to_mule_notebook.py`, `data/sample/`, `docs/schema/data_dictionary.md`
- Notes: Added configurable NovaBank Digital Scam-to-mule flow generation with Client/User/Partner separation, user-agent and app/browser telemetry, device/IP/ASN/geolocation/VPN/auth/session fields, beneficiary-change events, early-life mule accounts, incoming victim payments, rapid pass-through, shared-device signals, noisy digital outcomes, protected labels, and a scoring-rule notebook with alert-aware metrics. Local `uv run ruff check .` and `uv run pytest` (74 passed) succeeded; GitHub CI passed before merge.

### Issue #9: Interpret Alerts And Produce A Governance Memo — DONE

- Branch: feat/issue-9-implementation
- PR: #24
- Tests added: 1 notebook execution smoke test; all local tests passing
- Key files changed: `notebooks/03_alert_governance/alert_governance_memo.ipynb`, `tests/test_alert_governance_notebook.py`, `notebooks/README.md`
- Notes: Added the alert-governance integration notebook consuming tiny private-banking and digital-banking baseline equivalents, summarizing alert volume, precision/recall tradeoffs, PR-AUC, investigation capacity, threshold rationale, cost, limitations, and a governance memo draft. The notebook avoids headline accuracy claims and frames outputs for business, risk, and compliance stakeholder discussion. Local `uv run ruff check .`, notebook smoke execution, and `uv run pytest` (75 passed) succeeded; GitHub CI passed before merge.

### Issue #10: Seed Case Library With Pattern-Linked Source Packs — HITL-PENDING

- Branch: feat/issue-10-implementation
- PR: #26
- Tests added: 4 case-library metadata/source-pack validation tests; all local tests passing
- Key files changed: `docs/cases/source_packs/`, `docs/cases/index.md`, `tests/test_case_library_metadata.py`
- Notes: Opened a draft HITL PR with detection-pattern-first source packs for private-banking transaction monitoring, digital scam-to-mule flow, model-governance method, and graph/network mule patterns. Each source pack carries draft HITL metadata and `<!-- HITL-REVIEW-REQUIRED -->` markers. Validator coverage was strengthened to require structured Source Links URLs and existing linked notebook paths. Local `uv run ruff check .`, focused metadata tests, and `uv run pytest` (79 passed) succeeded; GitHub CI passed and CodeRabbit skipped because the PR is draft. Human review is still required for source selection and framing.

### Issue #11: Connect Regulatory Source Index To v0.1 Exercises — HITL-PENDING

- Branch: feat/issue-11-implementation
- PR: #27
- Tests added: 5 regulatory source-index validation tests; all local tests passing
- Key files changed: `docs/regulation/index.md`, `docs/regulation/source_notes/`, `tests/test_regulatory_source_index.py`
- Notes: Opened a draft HITL PR with regulatory source notes for Swiss AMLA/AMLO/FINMA anchors, UK APP scam payment guidance, FATF typology context, and model-risk governance. Each note links to official HTTPS sources, connects to existing v0.1 notebooks, states the educational/non-advice boundary, and includes `<!-- HITL-REVIEW-REQUIRED -->` markers. Local `uv sync --extra dev`, `uv run ruff check .`, focused regulatory tests, and `uv run pytest` (80 passed) succeeded; GitHub CI passed and CodeRabbit skipped because the PR is draft. Human review is still required for regulatory framing.

### Issue #12: Enforce v0.1 Quality Gates In CI — BLOCKED

- Branch: not started
- PR: not opened
- Tests added: 0
- Key files changed: none
- Notes: Wave 6 is blocked by issues #10 and #11. The goal requires strict dependency order and says not to start a wave until blocking issues are complete and merged. Issues #10 and #11 are intentionally open draft HITL PRs (#26 and #27) pending human review, so issue #12 cannot be implemented as a mergeable `main`-targeted PR yet. Unblock by completing human review and merging #26 and #27.
