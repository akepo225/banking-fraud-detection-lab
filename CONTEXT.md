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
