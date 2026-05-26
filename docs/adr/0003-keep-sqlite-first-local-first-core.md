# Keep SQLite-First Local-First Core

Accepted.

## Context

The lab should be runnable by learners from a clean checkout without heavy
infrastructure. Later modules may discuss PostgreSQL, Neo4j, Kafka, Spark,
dashboards, APIs, or streaming concepts, but the v1.0 core path must remain
approachable and reproducible.

## Decision

Keep the required core curriculum SQLite-first and local-first. SQLite is the
required SQL exercise surface for v1.0. Heavier infrastructure can appear only as
optional advanced material or advanced extensions after the core path is stable.

## Consequences

- Core modules must run without PostgreSQL, Neo4j, Kafka, Spark, Redis, external
  dashboards, cloud services, or deployed APIs.
- SQL exercises should target SQLite unless a module explicitly documents an
  optional alternative path.
- v1.4 advanced production infrastructure must not become a dependency of the
  v1.0 core learner path.
- Tests and docs should preserve the clean local setup as a release gate.
