# Use GitHub Issues As PRD And Implementation Source Of Truth

Accepted.

## Context

The repo now has local PRD drafts under `docs/prds/` and published GitHub PRD
issues for v0.2 through v1.4 plus the full-scope validation PRD. Implementation
work is broken down into GitHub child issues with triage labels and milestones.
Agents and maintainers need one operational source of truth for current scope and
status.

## Decision

Use GitHub Issues as the operational source of truth for PRDs, implementation
issues, triage state, blockers, comments, and milestone membership. Local PRD
files are durable planning artifacts and mirrors, but implementation agents must
read the relevant GitHub issue body and comments before starting work.

## Consequences

- Future agents should use GitHub issue bodies, comments, labels, and milestones
  to determine current implementation state.
- Local PRD files should be updated when they materially diverge from accepted
  GitHub issue scope.
- Parent PRD issues should not be closed or modified by child issue generation.
- Triage labels remain the workflow vocabulary for deciding whether work is
  ready for human review, ready for an AFK agent, blocked, or still needs triage.
