# Source Quality Rubric

<!-- HITL-REVIEW-REQUIRED -->

This rubric defines how case-library source packs weigh their public source
material. It supports the v0.5 **Case Library And Regulatory Skill Layer** and is
the canonical reference for the `source_quality` front-matter field. The goal is
to anchor learning at the level of **Detection patterns**, source discipline,
and governance questions — never to reconstruct real events.

This rubric is educational material for the Banking Fraud Detection Lab. It is
not legal, compliance, audit, investment, regulatory, or professional guidance.

## Weighting tiers (highest to lowest authority)

Assign the `source_quality` field from the highest tier the primary source
qualifies for. When a pack cites several sources, weight by the **primary**
source and note the others in the Source Links section.

| Tier | Source type | `source_quality` value family | What it can anchor |
| --- | --- | --- | --- |
| 1 | Regulator publication | `official regulator source candidate` (and the source-specific phrases already in use, e.g. `official payment regulator source candidate`, `official supervisory guidance source candidate`, `official cyber-security authority source candidate`, `official law-enforcement source candidate`) | Supervisory expectations, control-failure framing, governance and documentation questions, and **Detection patterns** at the level of behavior classes. |
| 1 | Court record | `court record source candidate` | Procedural facts on the public record, charge/adjudication framing, and observable signal classes. |
| 2 | Official regulatory disclosure (bank/issuer annual report, enforcement notice, regulator data page, payment-system operator data) | `official disclosure source candidate` (incl. `official payment-system operator source candidate`) | Official aggregate data (for example APP scam performance figures), disclosed control posture, and documentation expectations. |
| 3 | Reputable journalism | `reputable journalism source candidate` | Public narrative context and chronology for framing — always corroborated against a tier 1–2 source where possible. |
| 4 | Industry research / typology report | `industry research source candidate` (incl. `reputable industry report candidate`) | Cross-sector typologies, common control gaps, and feature-design inspiration. |

Each cell lists the canonical phrase for the tier plus the existing source-specific
phrases already used in the case library. The `source_quality` value is a family
name, not a single exact string: when migrating a pack, keep its existing
human-readable phrase (which names the specific source body) and confirm it falls
under the correct tier above. The metadata tests do not enforce an exact
`source_quality` vocabulary, so existing phrases stay stable during v0.5 migration.

## How each tier anchors learning without reconstructing events

The principle is the same for every tier: extract the **Detection pattern** (the
recurring observable signal, behavior, network structure, or control failure)
and leave the specific parties, amounts, and chronology behind.

### Tier 1 — Regulator publication and court record

Use these for the strongest source discipline. A regulator publication or court
record lets the pack assert "an official supervisor addressed this behavior
class" without asserting anything about a specific Client or transaction. Anchor
governance, documentation, and control-failure questions here. Do not quote at
length and do not reproduce case chronology in the synthetic data.

### Tier 2 — Official regulatory disclosure

Official disclosures (aggregate performance data, enforcement notices) support
quantitative framing and control-posture questions. Use aggregate figures only
as published; do not map them onto synthetic Clients or accounts.

### Tier 3 — Reputable journalism

Journalism provides narrative context that helps learners recognize a behavior
class. It must not be the sole basis for a Detection pattern. Prefer it as a
secondary link beside a tier 1–2 source, and never use it to reconstruct named
parties or transactions in the synthetic data.

### Tier 4 — Industry research and typology reports

Typology reports (for example FATF-style money-mule typologies) are useful for
feature design and for naming cross-sector patterns. They anchor learning at the
level of signal families and are explicitly non-specific to any institution.

## Selection rules

1. Prefer the highest tier available. If only journalism exists, say so in
   Limitations and keep the pack framing conservative.
2. Always link the official HTTPS URL directly. For regulatory notes, the domain
   must be on the allowed official-source domain list maintained by
   `tests/test_regulatory_source_index.py`
   (`fedlex.admin.ch`, `finma.ch`, `psr.org.uk`, `fatf-gafi.org`,
   `federalreserve.gov`). Case-library source packs may cite regulator, court,
   or reputable-journalism domains appropriate to their tier.
3. Cite the source family, not the outcome. Describe the behavior class and the
   **Detection pattern** it maps to; do not assert that synthetic data reproduces
   the matter.
4. Separate facts from interpretation. Public-source facts go in
   `## Public Facts`; analytic interpretation goes in
   `## Interpretation For Detection Patterns`. See `TEMPLATE.md`.
5. One primary `pattern_id` per pack where the pack supports a single
   **Detection pattern**. Cross-track governance or graph packs may reference
   more than one but must never invent a new `pattern_id`.

## Prohibited content

The first three bullets are enforced by automated metadata tests
(`tests/test_case_library_metadata.py`); the remaining bullets are
review-enforced and must be checked by a human reviewer during HITL review
before publication.

Automated checks block:

- Direct quote blocks (`>`) in draft packs.
- Imperative compliance wording: "you must", "must comply", "must report",
  "required to comply", "legal requirement for learners".
- Reconstruction claims: "reconstructs the", "reproduces the", "recreation of",
  "based on actual", "replicate the", "exact case".

Human review must also confirm:

- No real Client, account, or transaction data.
- No real-bank affiliation claims, and no framing that implies the synthetic
  institution is a stand-in for a named firm.

## Contributor checklist

See `docs/cases/CONTRIBUTING.md` for the contributor workflow checklist that
operationalizes this rubric.
