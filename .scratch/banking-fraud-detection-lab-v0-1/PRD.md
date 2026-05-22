# PRD: Banking Fraud Detection Lab v0.1

Status: needs-triage

GitHub: https://github.com/akepo225/banking-fraud-detection-lab/issues/1

## Problem Statement

The user needs a private, public-ready product foundation for **Banking Fraud Detection Lab**: a portfolio-grade banking fraud detection curriculum that can eventually be published without exposing personal job-preparation context, implying affiliation with any real bank, or relying on real client data.

The current personal learning repo contains valuable ideas, notebooks, synthetic data generators, and financial-crime learning material, but it is deeply entangled with job-preparation framing, Julius Baer-specific naming, personal progress material, and a private-learning structure. That makes it unsuitable as the public source of truth for a credible training repo.

The user also needs the curriculum to serve a mixed **Target learner**: analytics, financial-crime, product, SQL/R, and junior data-science practitioners who want to become more hands-on in Python, SQL, model evaluation, alert interpretation, and banking fraud detection. The repo must cover both **Private-banking fraud detection** and **Digital-banking fraud detection**, because the user's public positioning and interview context include Swiss private banking as well as online-bank problems such as scams, mule accounts, e-banking telemetry, account takeover, digital assets, and brokerage fraud.

## Solution

Build **Banking Fraud Detection Lab v0.1** as a fresh, private local repo that is structured and polished enough to become public later.

The solution is a curriculum and synthetic-data lab with two first-class **Fraud detection tracks**:

- **Private-banking fraud detection**, using **Alpine Crest Private Bank** as the fictional institution.
- **Digital-banking fraud detection**, using **NovaBank Digital** as the fictional institution.

The v0.1 release should provide shared foundations, a **Realistic synthetic data model**, **Progressive data views**, first-class SQL exercises, Python modeling notebooks, a seeded public case library, a regulatory source index, split licensing, local issue-tracker setup, and quality gates.

The first useful learner path should let a learner understand the data model, run SQL feature extraction, train baseline models for one private-banking transaction-fraud scenario and one digital **Scam-to-mule flow**, then interpret alerts through governance and limitation-aware evaluation.

## User Stories

1. As the repo owner, I want a fresh public-ready repo separate from my personal learning repo, so that I can continue private learning without exposing job-preparation history.
2. As the repo owner, I want the repo to stay private until v0.1 is complete, so that I can polish the positioning before publication.
3. As the repo owner, I want the repo name to be **Banking Fraud Detection Lab**, so that the scope includes both private banking and digital banking.
4. As the repo owner, I want a portfolio-grade README, so that recruiters, peers, and future collaborators quickly understand the value of the project.
5. As the repo owner, I want a clear disclaimer, so that readers understand the repo is educational, unofficial, unaffiliated, and not legal or compliance advice.
6. As the repo owner, I want split licensing for code and educational content, so that code can be reused while curriculum material remains non-commercial.
7. As the repo owner, I want an ADR explaining the scope pivot, so that future readers understand why the repo covers both private banking and digital banking.
8. As a financial-crime analytics practitioner, I want fraud-domain material connected to hands-on data science, so that I can deepen my implementation skills without starting from absolute beginner content.
9. As a junior data scientist, I want fraud scenarios explained before modeling techniques, so that I can learn the domain context behind each model.
10. As a SQL/R-heavy practitioner, I want SQL to be first-class, so that I can use my existing strengths while building Python capability.
11. As a learner new to Python notebooks, I want optional warm-up material, so that I can refresh Python, pandas, SQL, and sklearn without slowing down the core curriculum.
12. As an advanced learner, I want the warm-up material to be optional, so that I can skip basics and go straight to fraud detection modules.
13. As a learner, I want one consistent synthetic banking world, so that I build durable analytics habits instead of relearning incompatible toy schemas.
14. As a learner, I want **Progressive data views**, so that early lessons stay approachable while the underlying model remains realistic.
15. As a learner, I want tiny sample datasets committed to the repo, so that I can inspect examples immediately.
16. As a learner, I want deterministic generation for larger datasets, so that I can reproduce notebook outputs locally.
17. As a learner, I want SQLite-first SQL exercises, so that I can run the curriculum without infrastructure setup.
18. As an advanced learner, I want optional room for PostgreSQL later, so that advanced modules can teach more realistic database behavior.
19. As a learner, I want a schema overview and data dictionary, so that I can understand the generated tables before modeling.
20. As a learner, I want an entity relationship explanation, so that joins across partners, relationships, accounts, users, sessions, alerts, and cases make sense.
21. As a learner, I want a realistic **Alert lifecycle**, so that I understand suspicious activity, generated alerts, opened cases, case outcomes, and confirmed fraud as separate concepts.
22. As a learner, I want labels to be delayed and imperfect, so that the curriculum reflects real financial-crime analytics rather than clean Kaggle-style targets.
23. As a private-banking learner, I want **Alpine Crest Private Bank** scenarios, so that I can study relationship-manager context without using real bank data.
24. As a private-banking learner, I want a Swiss-style **Partner**, **Role**, **Partner role**, and **Banking relationship** model, so that the data feels like real private-banking operations.
25. As a private-banking learner, I want accounts under banking relationships, so that I can practice realistic joins and account-level analysis.
26. As a private-banking learner, I want relationship-manager assignments to be effective-dated, so that I can reason about historical responsibility and insider-risk context.
27. As a private-banking learner, I want beneficial ownership and authorized signatory structures, so that I can analyze complex client relationships.
28. As a private-banking learner, I want private-banking transaction-fraud examples, so that I can build baseline detection models for high-value transaction anomalies.
29. As a digital-banking learner, I want **NovaBank Digital** scenarios, so that I can study online-bank fraud without implying affiliation with real fintechs.
30. As a digital-banking learner, I want **Client**, **User**, and **Partner** to be separate concepts, so that I understand the difference between legal customer identity and digital login identity.
31. As a digital-banking learner, I want users, sessions, devices, and beneficiaries in the model, so that I can analyze e-banking behavior.
32. As a digital-banking learner, I want **Digital session telemetry**, so that I can detect suspicious login and payment behavior.
33. As a digital-banking learner, I want a **Scam-to-mule flow** module, so that I can understand how authorized push-payment scams and mule accounts interact.
34. As a digital-banking learner, I want mule-account behavior to include early-life accounts, rapid pass-through, new beneficiaries, shared devices, and noisy outcomes, so that the scenario feels realistic.
35. As a digital-banking learner, I want APP scam scenarios to include victim journey, beneficiary setup, warning friction, payment authorization, and post-payment case outcome, so that I can connect product controls to detection data.
36. As a learner, I want first-class SQL feature extraction, so that I can create features with joins, windows, baselines, cohorts, and alert queues.
37. As a learner, I want Python modeling notebooks, so that I can train baseline fraud models using generated features.
38. As a learner, I want careful fraud metrics, so that I learn precision-recall tradeoffs, PR-AUC, alert capacity, cost curves, and limitations instead of headline accuracy claims.
39. As a learner, I want governance notes inside each module, so that explainability and model risk are not treated as afterthoughts.
40. As a learner, I want a dedicated governance and alert-interpretation module, so that I can practice explaining model output in operational language.
41. As a learner, I want public case studies linked to detection patterns, so that the curriculum connects real-world failures to data signals.
42. As a learner, I want case documents to separate facts from interpretation, so that I can trust the source discipline.
43. As a learner, I want source-quality ranking, so that I know whether a case is based on regulator sources, bank disclosures, journalism, or industry reports.
44. As a learner, I want regulatory notes to link to official sources, so that I can build **Regulatory skill** without copying large legal texts into the repo.
45. As a learner, I want regulatory learning to shape analytics questions and governance decisions, so that regulations become practical rather than abstract.
46. As a learner, I want Swiss AMLA, AMLO, FINMA, and MROS-related sources represented, so that the Swiss anchor remains visible.
47. As a learner, I want selected EU/UK payment and APP scam references where relevant, so that digital-banking fraud modules reflect online-bank realities.
48. As a learner, I want FATF typologies where relevant, so that financial-crime overlap is included only when it supports detection patterns.
49. As a learner, I want digital assets to be an optional advanced slice, so that v0.1 stays focused while future crypto scenarios are possible.
50. As a learner, I want brokerage fraud to be a later module, so that Swissquote-style concepts can be included without overloading v0.1.
51. As a contributor, I want a clear contribution policy for cases, so that I know what source discipline and pattern mapping are required.
52. As a contributor, I want machine-readable case metadata, so that cases can later be indexed by pattern, track, geography, product, regulator, and linked module.
53. As a maintainer, I want deterministic generator tests, so that dataset behavior does not drift unexpectedly.
54. As a maintainer, I want referential-integrity tests, so that generated tables stay joinable.
55. As a maintainer, I want schema and data-dictionary alignment tests, so that docs do not rot as the generator evolves.
56. As a maintainer, I want prevalence-range tests for injected scenarios, so that fraud examples stay realistic enough for teaching.
57. As a maintainer, I want notebook smoke tests on tiny data, so that featured learner paths keep running from a clean setup.
58. As a maintainer, I want lightweight CI, so that quality checks run before publication.
59. As a future module author, I want deep modules with stable interfaces, so that new curriculum modules can reuse data generation, schema validation, SQL loading, scenario injection, and evaluation utilities.
60. As a future module author, I want v0.1 to explicitly exclude Kafka, Neo4j, Spark, full crypto, full brokerage, and full beginner Python, so that the first release remains achievable.
61. As a recruiter or public reader, I want the repo to show practical judgment, so that I see more than model training notebooks.
62. As a public reader, I want the project to avoid real-bank affiliation claims, so that the educational purpose is clear and credible.
63. As the repo owner, I want publication to happen only after the skeleton, generator, sample data, schema docs, two runnable notebooks, disclaimer, and licenses are complete, so that the public launch feels intentional.
64. As the repo owner, I want the current PRD to enter `needs-triage`, so that the next step can be normal issue breakdown rather than more design drift.

## Implementation Decisions

- Build in the fresh **Banking Fraud Detection Lab** repo, not by transforming the personal learning repo.
- Keep the repo private until the v0.1 publication bar is met.
- Use **Banking Fraud Detection Lab** as the canonical public name.
- Use `banking_fraud_lab` as the Python package name.
- Use **Alpine Crest Private Bank** as the fictional institution for the private-banking track.
- Use **NovaBank Digital** as the fictional institution for the digital-banking track.
- Preserve the two-track scope from ADR-0001: **Private-banking fraud detection** and **Digital-banking fraud detection** are both first-class.
- Use shared foundations before learners branch into the two tracks.
- Use Python and SQL as the first-class implementation languages.
- Use `uv` and project metadata for environment management, with a plain requirements export optional later.
- Use SQLite by default for SQL exercises and leave PostgreSQL as an advanced option.
- Commit only tiny sample datasets; generate medium and large datasets locally through deterministic scripts.
- Keep a split license model: permissive software license for code and CC BY-NC for educational content.
- Link to official regulatory sources, quote only short excerpts where necessary, and summarize learning implications in original wording.
- Use a **Realistic synthetic data model** with **Progressive data views** instead of separate incompatible beginner schemas.
- Model the private-banking side with **Partner**, **Role**, **Partner role**, **Banking relationship**, accounts, transactions, employees or relationship managers, alerts, cases, and case outcomes.
- Model the digital-banking side with **Client**, **User**, accounts, devices and sessions, payment beneficiaries, money movement, alerts, cases, and case outcomes.
- Include digital telemetry fields for user agent, app or browser version, device fingerprint hash, IP country, ASN risk, coarse geolocation, VPN or proxy flag, authentication method, session events, and beneficiary-change events.
- Treat **Client** as the legal customer in learner-facing explanations and **User** as the digital login identity.
- Model the **Alert lifecycle** explicitly rather than using a single `is_fraud` concept as the whole truth.
- Keep protected scenario answer keys outside normal learner-facing views.
- Implement a deep synthetic-data generator module with a stable interface for producing deterministic datasets by seed, scale, and scenario configuration.
- Implement a deep scenario-injection module that encapsulates private-banking transaction fraud and digital **Scam-to-mule flow** generation behind simple scenario configuration.
- Implement a deep schema-contract module that validates generated tables, required columns, relationships, and data-dictionary alignment.
- Implement a SQL-loading module that turns generated tables into a local SQL exercise database.
- Implement evaluation and governance utilities that expose fraud-appropriate metrics, alert-capacity views, cost curves, and limitation notes.
- Implement a case-library module based on detection-pattern-first documents with machine-readable metadata.
- Implement a seeded case library with at least one case or source pack for each v0.1 learning area: private-banking transaction fraud, digital scam-to-mule fraud, regulatory or model-governance method, and graph or network pattern.
- Implement regulatory source notes as educational mappings from official sources to analytics, governance, documentation, controls, explainability, and alert handling.
- Implement a regulatory source index covering Swiss AMLA, AMLO, FINMA, APP scam or payment guidance from EU or UK where relevant, FATF typologies, and model-risk or governance references.
- Build v0.1 modules for foundations, private-banking transaction fraud, digital scam-to-mule detection, and alert governance.
- Reuse ideas from the personal learning repo but rewrite public code cleanly, without Julius Baer branding or flat label semantics.
- Keep full production infrastructure optional and out of v0.1 unless later advanced modules need it.
- Add lightweight CI for linting, tests, and optional notebook smoke checks on tiny data.
- Treat the README as portfolio-grade, not merely technical setup documentation.

## Testing Decisions

- Good tests should verify external behavior and data contracts, not implementation details.
- Generator tests should assert deterministic output for a fixed seed and configuration.
- Generator tests should assert that required entities are produced for v0.1: partners, roles, banking relationships, accounts, transactions, users, sessions, payment beneficiaries, alerts, cases, and protected answer keys.
- Referential-integrity tests should verify that generated identifiers join correctly across relationships, accounts, transactions, users, sessions, beneficiaries, alerts, and cases.
- Scenario-prevalence tests should verify that injected fraud scenarios fall within expected ranges rather than exact row-by-row expectations.
- Alert-lifecycle tests should verify that suspicious activity, alerts, cases, outcomes, and confirmed fraud are represented as distinct states.
- Schema-contract tests should verify alignment between generated tables and the documented data dictionary.
- SQL-loader tests should verify that generated tables load into the local SQL database and support representative joins and window queries.
- Evaluation utility tests should verify metric outputs for known confusion-matrix and score-distribution cases.
- Case-library validation should verify required metadata fields and required sections in case documents.
- Regulatory source validation should verify that source notes include official links, an educational-only disclaimer, learning implications in original wording, and no imperative compliance instruction wording such as telling readers what they legally must do.
- Notebook smoke tests should run featured notebooks against tiny sample data and assert successful execution, not specific chart rendering details.
- CI should run fast checks by default and reserve heavier notebook or larger-data checks for optional workflows.
- Prior art exists in the personal learning repo's synthetic-data generator tests and validation-style checks; these should inspire coverage, not be copied directly.
- The first modules that should receive tests are the synthetic-data generator, scenario injection, schema validation, SQL loader, evaluation utilities, and notebook smoke path.

## Out of Scope

- Publishing the repo publicly before the v0.1 publication bar is met.
- Transforming the personal learning repo in place.
- Using real client data.
- Claiming synthetic data reconstructs real public cases.
- Official training, endorsement, or affiliation with any bank, fintech, regulator, or vendor.
- Legal, compliance, audit, regulatory, investment, or professional advice.
- Full Kafka, Neo4j, Spark, or production infrastructure in v0.1.
- Full beginner Python instruction as part of the core curriculum.
- Full crypto or digital-asset module in v0.1.
- Full brokerage or market-abuse module in v0.1.
- Full graph analytics module in v0.1.
- NLP or communication-monitoring datasets in v0.1 core.
- Headline model-performance claims such as simplistic accuracy targets.
- Copying large regulatory texts into the repo.
- Building a legal-rule engine for AMLA, AMLO, FINMA, PSD2, APP scams, MiCA, or other regulatory sources.

## Further Notes

The highest-risk design choice is the **Realistic synthetic data model**. It must be realistic enough to teach durable banking analytics habits but not so normalized or broad that every learner task becomes schema archaeology. The mitigation is to keep one canonical model while exposing **Progressive data views** by module.

The first digital-banking module should stay anchored on the **Scam-to-mule flow** because it naturally connects APP scams, mule or rented accounts, payment beneficiaries, session telemetry, alerts, cases, and noisy outcomes.

The first private-banking module should stay anchored on transaction fraud rather than complex insider, graph, or relationship-manager misconduct scenarios, because it provides a tractable baseline while still using the Swiss-style **Partner** and **Banking relationship** model.

The next appropriate workflow is to break this PRD into implementation issues after triage. The likely first implementation slice is the synthetic-data schema and generator because it is the deepest module and unlocks sample data, SQL exercises, tests, notebooks, and documentation.

v0.1 is ready for publication when:

- The repo remains free of personal job-preparation material and real client data.
- The README, disclaimer, split licensing, ADR, and contribution guidance are complete.
- The **Realistic synthetic data model** and data dictionary are documented.
- The deterministic generator produces tiny sample data and larger local datasets.
- The SQLite loader supports the first SQL exercises.
- At least two featured notebooks run end-to-end on tiny sample data.
- The seeded case library and regulatory source index are present.
- Tests cover generator determinism, referential integrity, scenario prevalence ranges, schema/data-dictionary alignment, SQL loading, and notebook smoke execution.
- Lightweight CI runs linting and tests.
