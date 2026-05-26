# Treat v1.1 Through v1.4 As Optional Advanced Extensions

Accepted.

## Context

The full roadmap includes digital assets, brokerage and market-abuse analytics,
NLP and communication monitoring, and advanced production infrastructure. These
topics are valuable, but making them part of the required v1.0 core would dilute
the core curriculum and increase setup complexity.

## Decision

Treat v1.1 through v1.4 as optional advanced extensions built on top of the v1.0
core curriculum:

- v1.1: digital assets and crypto fraud.
- v1.2: brokerage and market-abuse analytics.
- v1.3: NLP and communication monitoring.
- v1.4: advanced production infrastructure.

These extensions may add optional entities, features, dependencies, notebooks,
and tests, but they must preserve the v1.0 learner path.

## Consequences

- Advanced extensions must regression-test the v1.0 core path.
- Advanced dependencies must remain optional unless a later ADR changes the core
  scope.
- The capstone and v1.0 release gates should not require v1.1-v1.4 completion.
- Future issue breakdown should keep advanced-track work separate from core
  stability work.
