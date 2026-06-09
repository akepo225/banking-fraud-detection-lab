# Track Extension Conventions

Status: draft for human review.

<!-- HITL-REVIEW-REQUIRED: repo-owner-approval-needed -->

This contract governs v0.3 **Private-banking fraud detection** extensions and
the v0.4 **Digital-banking fraud detection** work that will mirror the same
shape later. It extends the canonical data model and the stable Detection
pattern vocabulary instead of creating a parallel metadata registry.

Track extensions must reuse
`src/banking_fraud_lab/schema/detection_patterns.py`, including `PatternSpec`,
`PATTERN_IDS`, and `ACTIVITY_TYPE_TO_PATTERN`. Feature libraries, notebooks,
case source packs, regulatory source notes, SQL exercises, and evaluation
outputs should reference those symbols or their values directly.

## Feature Naming Conventions

Feature identifiers and SQL output columns must use `snake_case`.

Private-banking feature identifiers must start with `pb_`. The prefix marks the
Alpine Crest Private Bank track and keeps later NovaBank Digital features from
sharing ambiguous names. SQL exercises should expose the same learner-facing
column names that the Python feature library emits.

Required v0.3 private-banking feature families:

- Amount ratios: amount-to-AUM and amount-to-relationship-baseline features.
- Relationship context: Banking relationship, Partner role, authorized
  signatory, beneficial-owner, and relationship-manager context.
- Counterparty novelty: first-use, recently added, or unusual private-banking
  beneficiary or counterparty context.
- Temporal signals: off-hours activity and effective-dated responsibility at
  the time of activity.
- Velocity features: transaction count and value changes over defined windows.
- Relationship-manager concentration: alert or case concentration by
  relationship-manager responsibility.

Every feature family must map to at least one `pattern_id` value from
`PATTERN_IDS`. v0.3 private-banking features may map only to
`pb_high_value_movement` or `pb_transaction_fraud` unless a later issue extends
the registry first.

## Notebook Module Layout

Track notebooks must live in numbered module directories using the
`NN_track_name/` convention. The v0.3 private-banking module path is
`notebooks/04_private_banking_feature_engineering/`.

Notebook files must use `<institution_slug>_<module_role>.ipynb`. For Alpine
Crest Private Bank, the institution slug is `alpine_crest`.

Required module roles for private-banking track depth:

- `feature_engineering`
- `supervised_baseline`
- `threshold_tuning`
- `alert_interpretation`

The v0.3 module extends the existing v0.1 baseline at
`notebooks/01_private_banking_transaction_fraud/alpine_crest_baseline.ipynb`.
It does not replace that baseline.

## Feature-Family Metadata

Feature-family metadata must be structured and traceable to the Detection
pattern vocabulary. A private-banking feature-family spec should include:

- `family_id`
- `display_name`
- `description`
- `detection_pattern_id`
- `source_tables`
- `source_columns`
- `output_columns`

The `detection_pattern_id` value must reference a `PatternSpec.pattern_id` from
`PATTERN_IDS`. Feature families without a Detection pattern mapping are out of
scope for v0.3 and v0.4.

Feature-family documentation should use this table shape:

| Feature family | `pattern_id` | Rationale |
| --- | --- | --- |
| Amount ratios | `pb_high_value_movement` | Relates transaction value to relationship context instead of using raw amount alone. |
| Counterparty novelty | `pb_transaction_fraud` | Flags changes in payment destination behavior that can support investigation. |

## Evaluation Output Expectations

Track model notebooks must use `evaluate_alert_scores()` from
`src/banking_fraud_lab/evaluation.py`, or a documented wrapper that returns the
same fields.

Required evaluation report fields:

- `pr_auc`
- `threshold_summaries`
- `cost_curve`
- `lowest_cost_threshold`
- `limitation_summary`

Each item in `threshold_summaries` must include `alert_capacity` and
`capacity_utilization`. Threshold examples should discuss alert volume,
precision, recall, false positives, missed fraud, and cost tradeoffs.

Accuracy is out of scope for track evaluation reports. Notebook text should
explain sparse labels, operational outcomes, and protected answer-key
separation through `limitation_summary` instead of presenting headline accuracy.

## Case and Regulatory Link Structure

Case source-pack and regulatory-source metadata must link back to existing
notebook paths and to Detection pattern identifiers from `PATTERN_IDS`.

Case source packs should use a `pattern_id` metadata field when the approved
case-library validator adds that field. Existing human-readable
`detection_pattern` front matter may remain for backward compatibility, but new
private-banking v0.3 entries must also reference `pb_high_value_movement` or
`pb_transaction_fraud` wherever the contract requires an identifier.

The `linked_modules` metadata field must contain only paths that exist in the
repository at the time the case pack or regulatory note is added. Current
metadata can safely link to the existing v0.1 baseline:

- `notebooks/01_private_banking_transaction_fraud/alpine_crest_baseline.ipynb`

After #84 creates the v0.3 module, downstream v0.3 case and regulatory notes may
add the feature-engineering notebook path:

- `notebooks/04_private_banking_feature_engineering/alpine_crest_feature_engineering.ipynb`

After #85 creates the supervised baseline, downstream v0.3 case and regulatory
notes may also add:

- `notebooks/04_private_banking_feature_engineering/alpine_crest_supervised_baseline.ipynb`

Validators should build on `tests/test_case_library_metadata.py` and
`tests/test_regulatory_source_index.py` rather than creating one-off checks.
Source notes must keep facts, interpretation, learning implications, and human
review boundaries separate.

## v0.4 Digital-Banking Track Mirroring

v0.4 should follow the same conventions with NovaBank Digital substitutions.
NovaBank Digital scope is excluded from v0.3 implementation.

| Convention | v0.3 private-banking value | v0.4 digital-banking value |
| --- | --- | --- |
| Institution | Alpine Crest Private Bank | NovaBank Digital |
| Module path | `notebooks/04_private_banking_feature_engineering/` | Future numbered digital-banking module path |
| Feature prefix | `pb_` | Future digital-banking prefix defined by the v0.4 issue |
| Primary pattern IDs | `pb_high_value_movement`, `pb_transaction_fraud` | `digital_scam_to_mule`, `new_beneficiary_payment`, `session_payment_velocity` |
| Scenario focus | relationship, account, counterparty, and relationship-manager context | Client, User, session, device, beneficiary, and payment context |

## Human Approval

Approval marker: `PENDING-HUMAN-APPROVAL`.

Before downstream v0.3 implementation issues are treated as unblocked, a repo
owner should approve this contract in the #80 issue or pull-request discussion.
If the contract changes after approval, affected downstream feature, notebook,
case, and regulatory work should be checked against the updated sections above.

## Source Boundaries

This contract is educational material for the Banking Fraud Detection Lab. It is
not legal, compliance, audit, investment, regulatory, or professional guidance.

Track extensions must remain unaffiliated with banks, fintechs, regulators,
vendors, and public case sources. They must not use actual client, account, or
transaction records, and they must not represent actual events. Public sources
may anchor learning only at the level of Detection patterns, source discipline,
and governance questions.

Use glossary terms exactly: Partner, Client, User, Banking relationship, and
Detection pattern.
