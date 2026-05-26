# v0.1/v0.2 Foundation Data Dictionary

This data dictionary defines the stable output contract for the datasets produced by `generate_minimal_banking_world(seed=42, scale="tiny")` and the larger deterministic `small`, `medium`, and `large` scale profiles. The tables are synthetic, deterministic, and educational. They do not contain real client data and do not reconstruct real events.

Money fields use exact decimal values. Where money is relevant, the model stores original amount and currency plus a CHF-normalized amount. Protected answer keys are intentionally separate from learner-facing lifecycle tables and are excluded from learner-facing generated outputs by default.

## Tables

| Table | Purpose |
| --- | --- |
| `partners` | Natural and legal persons represented in the fictional banking core model. |
| `clients` | Legal customer records that map client identity to a core partner. |
| `roles` | Controlled vocabulary of relationship roles used by `partner_roles`. |
| `partner_roles` | Effective-dated partner roles within a banking relationship. |
| `banking_relationships` | Swiss-bank-style containers grouping clients, partners, and accounts. |
| `accounts` | Deposit, custody, and payment accounts under banking relationships. |
| `transactions` | Money movement events used by both private-banking and digital-banking tracks. |
| `users` | Digital login identities that authenticate sessions for clients. |
| `sessions` | Digital session telemetry for e-banking and app behavior. |
| `payment_beneficiaries` | Saved payment beneficiaries used by digital-banking payments. |
| `suspicious_activities` | Suspicious activity observations before alert generation. |
| `alerts` | Alerts generated from suspicious activities that may trigger case investigations. |
| `cases` | Investigation cases opened from alerts in the alert lifecycle. |
| `case_outcomes` | Case decisions that separate confirmed fraud from other lifecycle states. |
| `protected_scenario_answer_keys` | Protected scenario labels excluded from learner-facing views. |

## Alert Lifecycle States

The foundation sample data keeps suspicious activity, alerts, cases, outcomes,
and confirmed fraud as separate concepts.

| Concept | Table | Meaning |
| --- | --- | --- |
| Suspicious activity | `suspicious_activities` | A detection-relevant observation linked to the underlying transaction and context, but not itself a fraud label. |
| Alert | `alerts` | A detection rule or model has generated an item for review from suspicious activity. |
| Case | `cases` | An alert has been opened for investigation with direct lifecycle references. |
| Outcome | `case_outcomes` | An investigator or process has assigned an outcome to a case. |
| Confirmed fraud determination | `case_outcomes` | Fraud confirmation is recorded only after a case outcome, not as a single transaction-level `is_fraud` flag. |
| Protected answer key | `protected_scenario_answer_keys` | Scenario labels excluded from normal learner-facing views. |

## `partners`

Natural and legal persons represented in the fictional banking core model.

| Column | Type | Nullable | References | Description |
| --- | --- | --- | --- | --- |
| `partner_id` | string | no |  | Stable synthetic partner identifier. |
| `institution_name` | string | no |  | Fictional institution that owns the partner record. |
| `partner_type` | string | no |  | Natural person or legal entity classification. |
| `display_name` | string | no |  | Synthetic display name. |
| `country` | string | no |  | Primary country code. |
| `created_at` | datetime64[ns] | no |  | Partner creation timestamp. |
| `risk_rating` | string | no |  | Low, medium, or high KYC risk band. |
| `kyc_risk_effective_from` | datetime64[ns] | no |  | Timestamp when the current KYC risk band became effective. |
| `kyc_risk_reviewed_at` | datetime64[ns] | no |  | Timestamp when the current KYC risk band was last reviewed. |

## `clients`

Legal customer records that map client identity to a core partner.

| Column | Type | Nullable | References | Description |
| --- | --- | --- | --- | --- |
| `client_id` | string | no |  | Stable synthetic client identifier. |
| `partner_id` | string | no | `partners.partner_id` | Partner that represents the legal customer. |
| `institution_name` | string | no |  | Fictional institution that owns the client record. |
| `client_segment` | string | no |  | Client segment used for progressive learner views. |
| `onboarded_at` | datetime64[ns] | no |  | Client onboarding timestamp. |
| `status` | string | no |  | Client status. |

## `roles`

Controlled vocabulary of relationship roles used by `partner_roles`.

| Column | Type | Nullable | References | Description |
| --- | --- | --- | --- | --- |
| `role_id` | string | no |  | Stable synthetic role identifier. |
| `role_code` | string | no |  | Machine-readable role code. |
| `role_name` | string | no |  | Human-readable role name. |
| `description` | string | no |  | Role meaning in learner-facing language. |

## `partner_roles`

Effective-dated partner roles within a banking relationship.

| Column | Type | Nullable | References | Description |
| --- | --- | --- | --- | --- |
| `partner_role_id` | string | no |  | Stable synthetic partner-role identifier. |
| `partner_id` | string | no | `partners.partner_id` | Partner assigned to the role. |
| `role_id` | string | no | `roles.role_id` | Assigned role. |
| `banking_relationship_id` | string | no | `banking_relationships.banking_relationship_id` | Banking relationship where the role applies. |
| `effective_from` | datetime64[ns] | no |  | Role start timestamp. |
| `effective_to` | datetime64[ns] | yes |  | Role end timestamp, if closed. |

## `banking_relationships`

Swiss-bank-style containers grouping clients, partners, and accounts.

| Column | Type | Nullable | References | Description |
| --- | --- | --- | --- | --- |
| `banking_relationship_id` | string | no |  | Stable synthetic banking relationship identifier. |
| `primary_client_id` | string | no | `clients.client_id` | Primary legal client for the relationship. |
| `institution_name` | string | no |  | Fictional institution that owns the relationship. |
| `relationship_name` | string | no |  | Learner-readable relationship label. |
| `opened_at` | datetime64[ns] | no |  | Relationship opening timestamp. |
| `status` | string | no |  | Relationship status. |
| `relationship_manager_code` | string | no |  | Synthetic relationship manager assignment code. |
| `relationship_manager_assigned_at` | datetime64[ns] | no |  | Timestamp when the current relationship manager assignment became effective. |

## `accounts`

Deposit, custody, and payment accounts under banking relationships.

| Column | Type | Nullable | References | Description |
| --- | --- | --- | --- | --- |
| `account_id` | string | no |  | Stable synthetic account identifier. |
| `banking_relationship_id` | string | no | `banking_relationships.banking_relationship_id` | Owning banking relationship. |
| `institution_name` | string | no |  | Fictional institution that owns the account. |
| `account_type` | string | no |  | Account product type. |
| `currency` | string | no |  | Account currency. |
| `opened_at` | datetime64[ns] | no |  | Account opening timestamp. |
| `status` | string | no |  | Account status. |
| `status_effective_from` | datetime64[ns] | no |  | Timestamp when the current account status became effective. |
| `status_effective_to` | datetime64[ns] | yes |  | Timestamp when the account status ended, if closed or superseded. |
| `balance_original` | Decimal | no |  | Exact account balance in original currency. |
| `balance_currency` | string | no |  | Currency for `balance_original`. |
| `balance_chf` | Decimal | no |  | Exact CHF-normalized account balance. |

## `transactions`

Money movement events used by both private-banking and digital-banking tracks.

| Column | Type | Nullable | References | Description |
| --- | --- | --- | --- | --- |
| `transaction_id` | string | no |  | Stable synthetic transaction identifier. |
| `account_id` | string | no | `accounts.account_id` | Account where the transaction is booked. |
| `payment_beneficiary_id` | string | yes | `payment_beneficiaries.payment_beneficiary_id` | Payment beneficiary for outbound digital payments. |
| `booked_at` | datetime64[ns] | no |  | Transaction booking timestamp. |
| `transaction_type` | string | no |  | Wire, card, cash, FX, or fee type. |
| `channel` | string | no |  | Branch, relationship manager, web, app, or batch channel. |
| `direction` | string | no |  | Debit or credit from the account perspective. |
| `amount_original` | Decimal | no |  | Exact transaction amount in original currency. |
| `currency` | string | no |  | Original transaction currency. |
| `amount_chf` | Decimal | no |  | Exact CHF-normalized transaction amount. |
| `description` | string | no |  | Synthetic transaction description. |

## `users`

Digital login identities that authenticate sessions for clients.

| Column | Type | Nullable | References | Description |
| --- | --- | --- | --- | --- |
| `user_id` | string | no |  | Stable synthetic user identifier. |
| `client_id` | string | no | `clients.client_id` | Client that owns the login identity. |
| `institution_name` | string | no |  | Fictional institution that owns the user record. |
| `username_hash` | string | no |  | Synthetic hash-like username token. |
| `created_at` | datetime64[ns] | no |  | Digital user creation timestamp. |
| `status` | string | no |  | Digital user status. |
| `authorized_from` | datetime64[ns] | no |  | Timestamp when the current digital authorization became effective. |
| `authorized_to` | datetime64[ns] | yes |  | Timestamp when the digital authorization ended, if revoked. |

## `sessions`

Digital session telemetry for e-banking and app behavior.

| Column | Type | Nullable | References | Description |
| --- | --- | --- | --- | --- |
| `session_id` | string | no |  | Stable synthetic session identifier. |
| `user_id` | string | no | `users.user_id` | Digital login identity for the session. |
| `started_at` | datetime64[ns] | no |  | Session start timestamp. |
| `channel` | string | no |  | Web or mobile app channel. |
| `user_agent` | string | no |  | Synthetic browser or app user-agent family. |
| `app_or_browser_version` | string | no |  | Synthetic app or browser version observed in the session. |
| `device_fingerprint_hash` | string | no |  | Synthetic device fingerprint token. |
| `ip_country` | string | no |  | Country inferred from IP address. |
| `asn_risk_score` | int64 | no |  | Coarse ASN/network risk score from 0 to 100. |
| `coarse_geolocation` | string | no |  | Coarse city or region-level geolocation signal. |
| `is_vpn_or_proxy` | bool | no |  | Whether the session used VPN or proxy signals. |
| `auth_method` | string | no |  | Authentication method used. |
| `session_event` | string | no |  | Main event observed during the session. |

## `payment_beneficiaries`

Saved payment beneficiaries used by digital-banking payments.

| Column | Type | Nullable | References | Description |
| --- | --- | --- | --- | --- |
| `payment_beneficiary_id` | string | no |  | Stable synthetic payment beneficiary identifier. |
| `client_id` | string | no | `clients.client_id` | Client that owns the beneficiary. |
| `added_by_user_id` | string | no | `users.user_id` | User that added the beneficiary. |
| `beneficiary_name` | string | no |  | Synthetic beneficiary name. |
| `beneficiary_account_country` | string | no |  | Country code for the beneficiary account. |
| `beneficiary_bank_country` | string | no |  | Country code for the beneficiary bank. |
| `beneficiary_change_event` | string | no |  | Beneficiary lifecycle event such as creation or update. |
| `created_at` | datetime64[ns] | no |  | Beneficiary creation timestamp. |
| `status` | string | no |  | Beneficiary status. |

## `suspicious_activities`

Suspicious activity observations that sit before generated alerts in the alert lifecycle.

| Column | Type | Nullable | References | Description |
| --- | --- | --- | --- | --- |
| `suspicious_activity_id` | string | no |  | Stable synthetic suspicious activity identifier. |
| `institution_name` | string | no |  | Fictional institution that owns the observation. |
| `banking_relationship_id` | string | no | `banking_relationships.banking_relationship_id` | Banking relationship where the suspicious activity was observed. |
| `account_id` | string | no | `accounts.account_id` | Account linked to the suspicious activity. |
| `transaction_id` | string | no | `transactions.transaction_id` | Transaction that carried the observed suspicious activity. |
| `user_id` | string | yes | `users.user_id` | Digital login identity linked to the activity, where applicable. |
| `session_id` | string | yes | `sessions.session_id` | Digital session linked to the activity, where applicable. |
| `payment_beneficiary_id` | string | yes | `payment_beneficiaries.payment_beneficiary_id` | Payment beneficiary linked to the activity, where applicable. |
| `activity_type` | string | no |  | Detection pattern observed. |
| `detected_at` | datetime64[ns] | no |  | Time the activity was detected. |
| `detection_signal` | string | no |  | Learner-readable signal summary. |
| `suspected_amount_chf` | Decimal | no |  | CHF-normalized amount under review. |
| `review_priority` | string | no |  | Low, medium, or high review priority. |

## `alerts`

Alerts generated from suspicious activities that may trigger case investigations.

| Column | Type | Nullable | References | Description |
| --- | --- | --- | --- | --- |
| `alert_id` | string | no |  | Stable synthetic alert identifier. |
| `suspicious_activity_id` | string | no | `suspicious_activities.suspicious_activity_id` | Suspicious activity that generated the alert. |
| `banking_relationship_id` | string | no | `banking_relationships.banking_relationship_id` | Banking relationship linked to the alert. |
| `account_id` | string | no | `accounts.account_id` | Account linked to the alert. |
| `triggered_transaction_id` | string | no | `transactions.transaction_id` | Transaction that triggered the alert. |
| `user_id` | string | yes | `users.user_id` | Digital login identity linked to the alert, where applicable. |
| `session_id` | string | yes | `sessions.session_id` | Digital session linked to the alert, where applicable. |
| `payment_beneficiary_id` | string | yes | `payment_beneficiaries.payment_beneficiary_id` | Payment beneficiary linked to the alert, where applicable. |
| `institution_name` | string | no |  | Fictional institution that owns the alert. |
| `generated_at` | datetime64[ns] | no |  | Alert generation timestamp. |
| `alert_type` | string | no |  | Alert typology or rule family. |
| `alert_status` | string | no |  | Generated, triaged, escalated, or closed. |
| `status_updated_at` | datetime64[ns] | no |  | Timestamp when the current alert status was assigned. |
| `severity` | string | no |  | Low, medium, or high alert severity. |
| `reason` | string | no |  | Learner-readable alert reason. |

## `cases`

Investigation cases opened from alerts in the alert lifecycle.

| Column | Type | Nullable | References | Description |
| --- | --- | --- | --- | --- |
| `case_id` | string | no |  | Stable synthetic case identifier. |
| `alert_id` | string | no | `alerts.alert_id` | Alert that opened the case. |
| `suspicious_activity_id` | string | no | `suspicious_activities.suspicious_activity_id` | Suspicious activity being investigated. |
| `banking_relationship_id` | string | no | `banking_relationships.banking_relationship_id` | Banking relationship linked to the case. |
| `account_id` | string | no | `accounts.account_id` | Account linked to the case. |
| `transaction_id` | string | no | `transactions.transaction_id` | Primary transaction under investigation. |
| `user_id` | string | yes | `users.user_id` | Digital login identity linked to the case, where applicable. |
| `session_id` | string | yes | `sessions.session_id` | Digital session linked to the case, where applicable. |
| `payment_beneficiary_id` | string | yes | `payment_beneficiaries.payment_beneficiary_id` | Payment beneficiary linked to the case, where applicable. |
| `opened_at` | datetime64[ns] | no |  | Case opening timestamp. |
| `assigned_team` | string | no |  | Investigation team assignment. |
| `case_status` | string | no |  | Open, closed, or escalated case status. |
| `closed_at` | datetime64[ns] | yes |  | Case closure timestamp, populated for closed cases. |
| `investigation_summary` | string | no |  | Brief synthetic investigation note. |

## `case_outcomes`

Case decisions that separate confirmed fraud from other lifecycle states.

| Column | Type | Nullable | References | Description |
| --- | --- | --- | --- | --- |
| `case_outcome_id` | string | no |  | Stable synthetic case outcome identifier. |
| `case_id` | string | no | `cases.case_id` | Case that received the outcome. |
| `decided_at` | datetime64[ns] | no |  | Outcome decision timestamp. |
| `recorded_at` | datetime64[ns] | no |  | Timestamp when the outcome was recorded in the case lifecycle. |
| `outcome_type` | string | no |  | confirmed-fraud, false-positive, or unresolved. |
| `confirmed_fraud` | bool | no |  | Whether the case outcome confirmed fraud. |
| `loss_amount_original` | Decimal | no |  | Exact loss amount in original currency. |
| `loss_currency` | string | no |  | Currency for `loss_amount_original`. |
| `loss_amount_chf` | Decimal | no |  | Exact CHF-normalized loss amount. |
| `notes` | string | no |  | Learner-readable outcome note. |

## `protected_scenario_answer_keys`

Protected scenario labels that are excluded from normal learner-facing views.

The canonical generated dataset includes protected answer keys for maintainers and tests. The learner-facing generator helper omits this table by default so exercises can inspect the lifecycle without exposing answer labels.

| Column | Type | Nullable | References | Description |
| --- | --- | --- | --- | --- |
| `answer_key_id` | string | no |  | Stable synthetic answer-key identifier. |
| `scenario_name` | string | no |  | Scenario that produced the protected label. |
| `entity_table` | string | no |  | Generated table containing the labeled entity. |
| `entity_id` | string | no |  | Identifier of the labeled entity. |
| `label_type` | string | no |  | Type of protected label. |
| `label_value` | string | no |  | Protected label value. |
| `available_to_learners` | bool | no |  | Always false for protected answer keys. |
