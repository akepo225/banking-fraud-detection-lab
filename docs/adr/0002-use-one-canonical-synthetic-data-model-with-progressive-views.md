# Use One Canonical Synthetic Data Model With Progressive Views

Accepted.

## Context

The curriculum needs to support foundations, **Private-banking fraud detection**,
**Digital-banking fraud detection**, case interpretation, graph analytics,
governance, monitoring, capstone work, and optional advanced extensions. Each
module needs an approachable learning surface, but separate toy schemas would make
later modules inconsistent and would weaken learner transfer.

## Decision

Use one **Realistic synthetic data model** as the canonical source for generated
data. Expose module-specific **Progressive data views** for learner-facing tasks
instead of creating incompatible schemas per module.

The canonical model owns the meanings of **Partner**, **Client**, **User**,
**Banking relationship**, **Detection pattern**, and the **Alert lifecycle**.
Progressive views may simplify, join, or filter the canonical model, but they
must remain traceable back to it.

## Consequences

- New modules should extend the canonical model additively unless a later ADR
  approves a breaking schema change.
- Progressive views need documented purpose, contracts, and tests.
- Case packs, graph features, governance outputs, and monitoring tables should
  reference canonical entities or documented views.
- Learners can start simple while still building habits that transfer to later
  modules.
