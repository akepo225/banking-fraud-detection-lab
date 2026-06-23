# Case Template

<!-- HITL-REVIEW-REQUIRED -->

This is the canonical template for every case source pack in the Banking Fraud
Detection Lab case library. A source pack anchors a **Detection pattern** in
public material and turns it into a learner-facing exercise. v0.5 upgrades the
existing v0.1/v0.3/v0.4 packs onto this template in place; it does not create a
new module.

The section headings below are required for every v0.5 template-conformant
pack. The `## Summary` section is new in v0.5; the remaining sections were
already required by `tests/test_case_library_metadata.py` and stay mandatory as
packs migrate in #119/#120/#121. Keep the heading text exactly so the metadata
validators and the case index can parse them. Do not add headings between the
required ones.

## Source boundaries (apply to every section)

- Educational use only. This material is not legal, compliance, audit,
  investment, regulatory, or professional advice.
- Keep public material unaffiliated: public sources anchor learning at the level
  of **Detection patterns**, source discipline, and governance questions only.
- Do not reconstruct real events. Synthetic data uses **Alpine Crest Private
  Bank** (private-banking track) or **NovaBank Digital** (digital-banking
  track), never a real institution.
- Do not use real Client, account, or transaction data, and do not claim
  affiliation with banks, fintechs, regulators, vendors, or public case sources.
- Use glossary terms exactly: **Client** (legal customer), **User** (digital
  login identity), **Banking relationship** (Swiss-bank-style container),
  **Detection pattern**, **Partner**, **Alert lifecycle**.

## Front matter

Every source pack begins with simple key-value front matter between `---`
fences. Existing packs keep their current fields; v0.5 only **adds** fields. Do
not remove or rename existing fields.

Required fields (existing):

```yaml
---
title: Human-Readable Source Pack Title
status: draft-hitl
hitl_review_required: true
v0_1_area: private_banking_transaction_fraud | digital_scam_to_mule | regulatory_or_model_governance_method | graph_or_network_pattern
track: Private-banking fraud detection | Digital-banking fraud detection
detection_pattern: human-readable detection-pattern description
institution_type: private bank | payment service provider or digital bank | ...
source_authority: FINMA | Payment Systems Regulator | FATF | ...
geography: Switzerland / cross-border | United Kingdom / payments | ...
product: private-banking transactions | authorised push payments | ...
source_quality: official regulator source candidate | ...
linked_modules: notebooks/01_.../alpine_crest_baseline.ipynb, notebooks/04_.../alpine_crest_feature_engineering.ipynb
---
```

v0.5 structured fields (add to every pack during #119/#120/#121 migration):
preserve the human-readable `detection_pattern` field, and **add** the structured
`pattern_id` that references a value from `PATTERN_IDS` in
`src/banking_fraud_lab/schema/detection_patterns.py`:

- Private-banking packs: `pattern_id: pb_transaction_fraud` or
  `pattern_id: pb_high_value_movement`.
- Digital-banking packs: `pattern_id: digital_scam_to_mule` or
  `pattern_id: new_beneficiary_payment` or `pattern_id: session_payment_velocity`.
- Cross-track governance / graph packs may omit `pattern_id` or reference the
  most relevant pattern; never invent a new `pattern_id`.

The `linked_modules` field must contain only repository paths that exist at the
time the pack is added.

## Required sections

Each source pack uses these level-two sections in order.

### ## Summary

Two to four sentences. State the public source family, the **Detection
pattern** the pack supports, and the learner outcome. Name the institution slug
(`alpine_crest` or `novabank`) and the track. Do not summarize the public matter
in a way that could read as reconstructing it.

### ## Source Links

A bullet list of public HTTPS source URLs. Each link is the official regulator,
court, official disclosure, or reputable journalism page that anchors the pack.
Direct quote blocks (`>`) are not allowed in draft packs; paraphrase instead.

### ## Public Facts

Bulleted, verifiable facts about the **public source** only: who published it,
what it covers at a high level, and why it is relevant to a **Detection
pattern**. This section is intentionally separate from interpretation so
learners can see where evidence ends and analysis begins. Do not mix analytic
claims in here. Named institutions appear only because this is a sourced public
case-library draft, not a synthetic scenario or affiliation claim.

### ## Interpretation For Detection Patterns

Original learner-facing analysis. Reference the `pattern_id`(s) from
`PATTERN_IDS` directly (for example `pb_high_value_movement`,
`digital_scam_to_mule`). Explain what observable signal the pattern describes
and how it could be turned into analytics or model features. This section
supports the **Detection pattern** concept from the glossary; it must not claim
to reconstruct the public matter.

### ## Likely Data Signals

Bulleted candidate features or signals a learner could derive from the synthetic
data model. Use the track's feature prefix: `pb_` for private-banking packs,
`db_` for digital-banking packs. Tie each signal back to the `pattern_id`
narrative in the interpretation section. These are teaching candidates, not
definitive feature lists.

### ## Linked Modules And Exercises

List the existing notebook module paths that exercise this pack, then add at
least one **learner-output exercise** as a level-three subsection:

```markdown
### Exercise 1 — <short verb phrase>

- Pattern: `pb_transaction_fraud` (or the relevant `pattern_id`)
- Module: `notebooks/01_private_banking_transaction_fraud/alpine_crest_baseline.ipynb`
- Prompt: one or two sentences describing the investigation a learner performs
  on synthetic data only.
- Learner output: the concrete artifact the learner produces (a SQL result, a
  feature interpretation, a short investigation note, or a threshold tradeoff
  discussion). No right/wrong answer is encoded here; learners self-assess
  against the notebook's alert-aware metrics and discussion prompts. Note that
  learner-facing views do not expose the protected answer key.
```

Exercises must reference only existing notebooks and the existing synthetic data
model. No new generator scenarios, no new schema. Exercises may only reference
`pattern_id` values from the frozen `PATTERN_IDS` registry that exist at the
time the pack is created; never introduce a new `pattern_id`.

### ## Regulatory Hooks

Frame governance, documentation, and alert-handling questions the pack raises
for stakeholder discussion. Keep this educational and non-advisory: no
imperative compliance wording such as "you must", "must comply", "must report",
or "required to comply".

### ## Limitations

State what the pack does **not** do: it does not reconstruct the public matter,
does not use real Client/account/transaction data, does not claim affiliation,
and does not provide legal advice. Name the fictional institution. Flag that
human review is required before publication.

### ## Human Review

Begin with the `<!-- HITL-REVIEW-REQUIRED -->` marker, then a bullet list of
review questions for a human reviewer (source selection, source URL, framing
fairness, exercise appropriateness). This marker is also placed near the top of
the file body; both placements are enforced by the metadata tests.

## Worked example

`source_packs/private-banking-transaction-monitoring.md` is the v0.5 worked
example. It is fully upgraded to this template, including structured
learner-output exercises tied to `pb_transaction_fraud` and
`pb_high_value_movement`. Migrate every other pack to match it in #120
(private-banking) and #121 (digital-banking).
