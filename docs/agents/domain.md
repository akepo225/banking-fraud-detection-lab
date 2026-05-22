# Domain Docs

How engineering skills should consume this repo's domain documentation when exploring the codebase.

## Layout

This is a single-context repo.

Read these before producing architecture, PRD, triage, or implementation work:

- `CONTEXT.md` at the repo root
- repo-wide ADRs under `docs/adr/`

## Use The Glossary's Vocabulary

When output names a domain concept, use the term as defined in `CONTEXT.md`. Do not drift to synonyms the glossary explicitly avoids.

Important current terms include:

- **Banking Fraud Detection Lab**
- **Fraud detection track**
- **Private-banking fraud detection**
- **Digital-banking fraud detection**
- **Realistic synthetic data model**
- **Progressive data view**
- **Alert lifecycle**
- **Scam-to-mule flow**
- **Alpine Crest Private Bank**
- **NovaBank Digital**

## Flag ADR Conflicts

If output contradicts an existing ADR, surface it explicitly rather than silently overriding it.
