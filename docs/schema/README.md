# Schema Notes

The v0.1 data model will be realistic enough to teach durable banking analytics habits while remaining approachable through progressive views.

## Planned Core Tables

- `partners`
- `roles`
- `partner_roles`
- `banking_relationships`
- `accounts`
- `transactions`
- `users`
- `sessions`
- `payment_beneficiaries`
- `alerts`
- `cases`
- `case_outcomes`
- protected scenario answer-key tables

## Design Rules

- Use exact decimal precision for money.
- Store original amount and currency plus CHF-normalized amount where relevant.
- Model the alert lifecycle explicitly.
- Keep scenario answer keys out of learner-facing views by default.
- Use SQLite-first SQL exercises, with optional PostgreSQL later.
