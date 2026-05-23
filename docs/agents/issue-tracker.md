# Issue Tracker: GitHub Issues

Issues and PRDs for this repo live in GitHub Issues for `akepo225/banking-fraud-detection-lab`.

The local `.scratch/` files are mirrors of the initial planning artifacts only. Use GitHub Issues as the source of truth for triage state, comments, and implementation work.

## Conventions

- Use `gh issue list`, `gh issue view`, `gh issue edit`, and `gh issue comment` for issue operations.
- Every triaged issue should have exactly one category role label: `bug` or `enhancement`.
- Every triaged issue should have exactly one state role label: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, or `wontfix`.
- Additional non-role labels such as `afk`, `hitl`, `blocked`, or `parent` may be used when helpful.
- Sprint membership is tracked with GitHub milestones.

## When A Skill Says "Publish To The Issue Tracker"

Create or update a GitHub issue with `gh issue create` or `gh issue edit`.

## When A Skill Says "Fetch The Relevant Ticket"

Read the GitHub issue with `gh issue view <number> --comments`.

## Pull Request Review Comments

Before treating a PR as complete, inspect both PR conversation comments and inline review comments. Use `gh pr view <number> --comments` for conversation context and `gh api repos/akepo225/banking-fraud-detection-lab/pulls/<number>/comments --paginate` for inline comments.

For closed or stacked follow-up PRs, compare every actionable comment against current code before deciding whether to patch it. Fix still-valid comments, and record a short reason for anything intentionally skipped, already fixed, or no longer applicable.
