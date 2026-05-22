# Triage Labels

The skills speak in terms of canonical triage roles. This file maps those roles to the actual label strings used in this repo's GitHub issue tracker.

## Category Roles

Every triaged issue should have exactly one category role.

| Role | Label in our tracker | Meaning |
| ---- | -------------------- | ------- |
| `bug` | `bug` | Something is broken |
| `enhancement` | `enhancement` | New feature or improvement |

## State Roles

Every triaged issue should have exactly one state role.

| Label in mattpocock/skills | Label in our tracker | Meaning                                  |
| -------------------------- | -------------------- | ---------------------------------------- |
| `needs-triage`             | `needs-triage`       | Maintainer needs to evaluate this issue  |
| `needs-info`               | `needs-info`         | Waiting on reporter for more information |
| `ready-for-agent`          | `ready-for-agent`    | Fully specified, ready for an AFK agent  |
| `ready-for-human`          | `ready-for-human`    | Requires human implementation            |
| `wontfix`                  | `wontfix`            | Will not be actioned                     |

When a skill mentions a role, use the corresponding label string from this table.

## Non-Role Labels

These labels can be combined with the category and state roles when useful.

| Label | Meaning |
| ----- | ------- |
| `afk` | Can be implemented by an AFK agent |
| `hitl` | Requires human-in-the-loop review or decision |
| `blocked` | Has unresolved issue dependencies |
| `parent` | Parent planning or tracking issue |

## Sprints

Sprint membership is tracked with GitHub milestones, not labels.
