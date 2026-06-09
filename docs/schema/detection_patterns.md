# Detection Pattern Vocabulary

This document defines the stable detection pattern identifiers used across
the curriculum for cross-module references. Each pattern is a recurring
observable signal, behaviour, network structure, or control failure that can
be translated into analytics or model features.

## Foundation Patterns

The following patterns are the v0.2 foundation detection patterns. Each maps
to one or more `activity_type` values produced by the generators and is
associated with a curriculum track and a synthetic institution.

| Pattern ID | Display Name | Track | Institution | Activity Type(s) |
| --- | --- | --- | --- | --- |
| `pb_high_value_movement` | Private-banking high-value movement | Private-banking fraud detection | Alpine Crest Private Bank | `private_banking_high_value` |
| `new_beneficiary_payment` | New beneficiary payment | Digital-banking fraud detection | NovaBank Digital | `new_beneficiary_payment` |
| `session_payment_velocity` | Session payment velocity | Digital-banking fraud detection | NovaBank Digital | `session_payment_velocity` |
| `pb_transaction_fraud` | Private-banking transaction fraud | Private-banking fraud detection | Alpine Crest Private Bank | `private_banking_transaction_fraud` |
| `digital_scam_to_mule` | Digital scam-to-mule flow | Digital-banking fraud detection | NovaBank Digital | `digital_scam_to_mule_flow` |

## Relationships

### `pattern_id` to `activity_type`

A `pattern_id` is a stable, human-readable identifier that groups one or more
`activity_type` values. The `activity_type` field on `suspicious_activities`
records the specific generator-level signal that produced the observation. The
`pattern_id` provides a coarser, curriculum-level grouping that remains stable
even if individual `activity_type` values are renamed or split in future
versions.

The mapping is maintained in
`src/banking_fraud_lab/schema/detection_patterns.py` as the
`ACTIVITY_TYPE_TO_PATTERN` dictionary.

### `pattern_id` to `detection_signal`

The `detection_signal` column on `suspicious_activities` is a free-text
learner-readable summary of what was observed. It is produced by the
generators and varies per observation. Pattern identifiers do not replace
`detection_signal`; they provide a structured vocabulary for referencing
the pattern category across modules, case packs, and documentation.

## Cross-Module References

### Case packs

Case source packs in `docs/cases/source_packs/` carry a `detection_pattern`
field in their YAML front matter. Future versions should validate this field
against the `PATTERN_IDS` registry to ensure case packs reference known
patterns.

### Progressive data views

Progressive data views may filter or group by detection pattern to expose
pattern-specific learner exercises. The `PATTERN_IDS` tuple provides the
canonical set of pattern identifiers for view builders.

### Notebooks

Featured notebooks reference detection patterns through the `activity_type`
values in generated data. The vocabulary allows notebooks to map observed
activity types back to stable pattern identifiers for labelling and
comparison.

## Extension Conventions

New detection patterns should follow these conventions:

1. Add a `PatternSpec` constant in `detection_patterns.py` following the
   existing naming pattern (uppercase snake-case module constant).
2. Append the new constant to `FOUNDATION_DETECTION_PATTERNS` (or create a
   new collection tuple for a future version group).
3. Update `PATTERN_IDS` and `ACTIVITY_TYPE_TO_PATTERN` to include the new
   entry.
4. Add the new pattern to the table in this document.
5. Ensure the `track` value is one of `"private_banking"` or
   `"digital_banking"` and the `institution` value matches one of the
   existing synthetic institution constants.
6. Add corresponding tests to `tests/test_detection_patterns.py`.

Track-specific feature, notebook, case, and regulatory extensions should follow
the shared contract in `track-extension-conventions.md`. That contract defines
how v0.3 private-banking and future v0.4 digital-banking work should reference
`PatternSpec`, `PATTERN_IDS`, and `ACTIVITY_TYPE_TO_PATTERN` without creating a
parallel Detection pattern metadata layer.

## Glossary Alignment

- **Detection pattern**: A recurring observable signal that can be translated
  into analytics or model features. See `CONTEXT.md`.
- **Client**: The bank's end customer in learner-facing explanations.
- **User**: The digital login identity that authenticates sessions.
- **Banking relationship**: The Swiss-bank-style container that groups
  related partners, accounts, and service arrangements.
- **Partner**: A natural or legal person represented in the fictional bank's
  core data model.
