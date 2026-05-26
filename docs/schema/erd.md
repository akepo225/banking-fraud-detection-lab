# ERD-Backed Schema Tour

This tour shows the v0.2 foundation schema as one **Realistic synthetic data
model**. It is intentionally foundation-level: it explains how **Partner**,
**Client**, **User**, **Banking relationship**, accounts, sessions, **Detection
pattern** observations, and the **Alert lifecycle** connect before later modules
add deeper private-banking or digital-banking features.

The canonical schema remains the source of truth in
`src/banking_fraud_lab/schema/tables.py`. This page is a learner-facing ERD tour
and is tested against that contract.

## Foundation ERD

```mermaid
erDiagram
    partners {
        string partner_id PK
    }
    clients {
        string client_id PK
        string partner_id FK
    }
    roles {
        string role_id PK
    }
    partner_roles {
        string partner_role_id PK
        string partner_id FK
        string role_id FK
        string banking_relationship_id FK
    }
    banking_relationships {
        string banking_relationship_id PK
        string primary_client_id FK
    }
    accounts {
        string account_id PK
        string banking_relationship_id FK
    }
    transactions {
        string transaction_id PK
        string account_id FK
        string payment_beneficiary_id FK
    }
    users {
        string user_id PK
        string client_id FK
    }
    sessions {
        string session_id PK
        string user_id FK
    }
    payment_beneficiaries {
        string payment_beneficiary_id PK
        string client_id FK
        string added_by_user_id FK
    }
    suspicious_activities {
        string suspicious_activity_id PK
        string banking_relationship_id FK
        string account_id FK
        string transaction_id FK
        string user_id FK
        string session_id FK
        string payment_beneficiary_id FK
    }
    alerts {
        string alert_id PK
        string suspicious_activity_id FK
        string banking_relationship_id FK
        string account_id FK
        string triggered_transaction_id FK
        string user_id FK
        string session_id FK
        string payment_beneficiary_id FK
    }
    cases {
        string case_id PK
        string alert_id FK
        string suspicious_activity_id FK
        string banking_relationship_id FK
        string account_id FK
        string transaction_id FK
        string user_id FK
        string session_id FK
        string payment_beneficiary_id FK
    }
    case_outcomes {
        string case_outcome_id PK
        string case_id FK
    }
    protected_scenario_answer_keys {
        string answer_key_id PK
    }

    partners ||--o{ clients : represents
    partners ||--o{ partner_roles : has_role
    roles ||--o{ partner_roles : assigned_as
    clients ||--o{ banking_relationships : primary_client
    banking_relationships ||--o{ partner_roles : contains_role
    banking_relationships ||--o{ accounts : owns
    accounts ||--o{ transactions : books
    clients ||--o{ users : authenticates_as
    users ||--o{ sessions : opens
    clients ||--o{ payment_beneficiaries : saves
    users ||--o{ payment_beneficiaries : adds
    payment_beneficiaries ||--o{ transactions : receives_payment
    banking_relationships ||--o{ suspicious_activities : observed_in
    accounts ||--o{ suspicious_activities : observed_on
    transactions ||--o{ suspicious_activities : carries_pattern
    users ||--o{ suspicious_activities : digital_actor
    sessions ||--o{ suspicious_activities : digital_session
    payment_beneficiaries ||--o{ suspicious_activities : beneficiary_context
    suspicious_activities ||--o{ alerts : generates
    banking_relationships ||--o{ alerts : alert_context
    accounts ||--o{ alerts : account_context
    transactions ||--o{ alerts : triggered_by
    users ||--o{ alerts : user_context
    sessions ||--o{ alerts : session_context
    payment_beneficiaries ||--o{ alerts : beneficiary_context
    alerts ||--o{ cases : opens
    suspicious_activities ||--o{ cases : investigated_activity
    banking_relationships ||--o{ cases : relationship_context
    accounts ||--o{ cases : account_context
    transactions ||--o{ cases : transaction_context
    users ||--o{ cases : user_context
    sessions ||--o{ cases : session_context
    payment_beneficiaries ||--o{ cases : beneficiary_context
    cases ||--o{ case_outcomes : receives
```

## How To Read The Foundation Model

- **Partner** records are natural or legal persons in the core model.
- **Client** records identify the legal customer and point back to a Partner.
- **User** records are digital login identities owned by a Client.
- A **Banking relationship** groups the Client's service arrangement, accounts,
  Partner roles, and downstream Alert lifecycle context.
- Suspicious activities record observed **Detection pattern** signals before an
  alert is generated.
- The **Alert lifecycle** flows from suspicious activity to alert, optional case,
  and optional case outcome.
- `protected_scenario_answer_keys` is intentionally outside learner-facing
  Progressive data views.

## Contract Table Map

| Table | Primary key | Relationship references |
| --- | --- | --- |
| `partners` | `partner_id` | None |
| `clients` | `client_id` | `partners.partner_id` |
| `roles` | `role_id` | None |
| `partner_roles` | `partner_role_id` | `partners.partner_id`, `roles.role_id`, `banking_relationships.banking_relationship_id` |
| `banking_relationships` | `banking_relationship_id` | `clients.client_id` |
| `accounts` | `account_id` | `banking_relationships.banking_relationship_id` |
| `transactions` | `transaction_id` | `accounts.account_id`, `payment_beneficiaries.payment_beneficiary_id` |
| `users` | `user_id` | `clients.client_id` |
| `sessions` | `session_id` | `users.user_id` |
| `payment_beneficiaries` | `payment_beneficiary_id` | `clients.client_id`, `users.user_id` |
| `suspicious_activities` | `suspicious_activity_id` | `banking_relationships.banking_relationship_id`, `accounts.account_id`, `transactions.transaction_id`, `users.user_id`, `sessions.session_id`, `payment_beneficiaries.payment_beneficiary_id` |
| `alerts` | `alert_id` | `suspicious_activities.suspicious_activity_id`, `banking_relationships.banking_relationship_id`, `accounts.account_id`, `transactions.transaction_id`, `users.user_id`, `sessions.session_id`, `payment_beneficiaries.payment_beneficiary_id` |
| `cases` | `case_id` | `alerts.alert_id`, `suspicious_activities.suspicious_activity_id`, `banking_relationships.banking_relationship_id`, `accounts.account_id`, `transactions.transaction_id`, `users.user_id`, `sessions.session_id`, `payment_beneficiaries.payment_beneficiary_id` |
| `case_outcomes` | `case_outcome_id` | `cases.case_id` |
| `protected_scenario_answer_keys` | `answer_key_id` | None |

## Learner Path

Start with `foundation_client_relationships` when the lesson needs a compact
Client, Partner, and Banking relationship anchor. Move to canonical tables when
the lesson needs role history, account detail, transaction detail, or digital
User/session context.

Start with `foundation_alert_lifecycle` when the lesson needs the Alert lifecycle
in one surface. Move to `suspicious_activities`, `alerts`, `cases`, and
`case_outcomes` when the lesson needs to explain each lifecycle transition.
