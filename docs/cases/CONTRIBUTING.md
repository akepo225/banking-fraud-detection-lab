# Contributing Case Source Packs

<!-- HITL-REVIEW-REQUIRED -->

This checklist is for anyone adding or upgrading a case source pack in the
Banking Fraud Detection Lab case library. It operationalizes the source-quality
rubric (`docs/cases/source_quality_rubric.md`) and the canonical template
(`docs/cases/TEMPLATE.md`). The repo-wide contributor guide is the root
`CONTRIBUTING.md`; this file is scoped to case-library contributions.

This is educational material for the Banking Fraud Detection Lab. It is not
legal, compliance, audit, investment, regulatory, or professional guidance.

## Before you start

- Confirm the case maps to an existing **Detection pattern** from `PATTERN_IDS`
  in `src/banking_fraud_lab/schema/detection_patterns.py`. Do not invent a new
  `pattern_id`.
- Confirm the target institution is the fictional **Alpine Crest Private Bank**
  (private-banking track) or **NovaBank Digital** (digital-banking track). Never
  use a real bank name.
- Pick a primary source from the highest tier available in the
  [source-quality rubric](source_quality_rubric.md).

## Required sections checklist

Every source pack must include, in order, the level-two sections from
`TEMPLATE.md`:

- [ ] `## Summary`
- [ ] `## Source Links` (official HTTPS URLs, tier 1–2 preferred)
- [ ] `## Public Facts` (public-source facts only, no analysis)
- [ ] `## Interpretation For Detection Patterns` (references `pattern_id`)
- [ ] `## Likely Data Signals` (`db_`-prefixed digital-banking features, or
      unprefixed private-banking features — verify exact names against
      `src/banking_fraud_lab/features/`)
- [ ] `## Linked Modules And Exercises` (existing notebook paths + ≥1 exercise)
- [ ] `## Regulatory Hooks` (educational, non-advisory)
- [ ] `## Limitations`
- [ ] `## Human Review` (begins with `<!-- HITL-REVIEW-REQUIRED -->`)

## Source discipline checklist

- [ ] Primary source is the highest tier available; tier noted in `source_quality`.
- [ ] Every source URL is HTTPS and resolves.
- [ ] For regulatory notes, every domain is on the allowed official-source list
      (`fedlex.admin.ch`, `finma.ch`, `psr.org.uk`, `fatf-gafi.org`,
      `federalreserve.gov`). This list may change; verify the current values
      against `docs/cases/source_quality_rubric.md` and the authoritative set in
      `tests/test_regulatory_source_index.py` before relying on it.
- [ ] Facts and interpretation are separated into their own sections.
- [ ] No direct quote blocks (`>`) in the draft.

## Non-reconstruction checklist

- [ ] The pack does not claim to reconstruct the public matter.
- [ ] The synthetic data uses **Alpine Crest Private Bank** or **NovaBank
      Digital**, never the named institution from the source.
- [ ] No real Client, account, or transaction data is used or implied.
- [ ] Amounts, parties, and chronology from the public matter are not mapped
      onto synthetic records.

## Non-affiliation checklist

- [ ] The pack states that named institutions appear only because this is a
      sourced public case-library draft.
- [ ] No claim that the synthetic institution is based on, stands in for, or is
      affiliated with a real bank, fintech, regulator, vendor, or case source.
- [ ] No legal, compliance, audit, investment, or professional advice.

## Official-source linking checklist

- [ ] Front matter `source_authority` matches the publishing body of the
      primary source.
- [ ] Front matter `source_type` is a value from the machine-readable vocabulary
      in the [source-quality rubric](source_quality_rubric.md) (it classifies the
      source body; `source_authority` is the human-readable publishing-body name).
- [ ] Front matter `source_quality` falls under the correct tier's value family
      in the [source-quality rubric](source_quality_rubric.md) (a family name,
      not a single exact string; preserve existing source-specific phrases).
- [ ] Front matter `pattern_id` (when present) is a value from `PATTERN_IDS`.
- [ ] Front matter `linked_modules` lists only repository paths that exist when
      the pack is added.
- [ ] Preserve the human-readable `detection_pattern` field alongside the
      structured `pattern_id`.

## Learner-output exercise checklist

- [ ] At least one `### Exercise N` subsection under
      `## Linked Modules And Exercises`.
- [ ] Each exercise names a `pattern_id`, an existing notebook module path, a
      one-to-two-sentence prompt, and a concrete learner output.
- [ ] Exercises use only existing notebooks and the existing synthetic data
      model. No new generator scenarios, no new schema, no new `pattern_id`.

## Before opening a PR

- [ ] `uv sync --extra dev`
- [ ] `uv run ruff check .`
- [ ] `uv run pytest` (metadata validators in
      `tests/test_case_library_metadata.py` must pass)
- [ ] The case index (`docs/cases/index.md`) links the new or upgraded pack.
- [ ] The pack keeps the `<!-- HITL-REVIEW-REQUIRED -->` marker near the top of
      the body and in `## Human Review` until a human reviewer approves it for
      publication.

## Glossary

Use glossary terms exactly throughout: **Client** (legal customer), **User**
(digital login identity), **Banking relationship** (Swiss-bank-style container),
**Detection pattern**, **Partner**, **Alert lifecycle**. See `CONTEXT.md` for
the full glossary.
