-- Verify that the learner-facing SQLite database contains the core v0.1 tables.
SELECT
  name AS table_name
FROM sqlite_master
WHERE type = 'table'
  AND name IN (
    'partners',
    'clients',
    'roles',
    'partner_roles',
    'banking_relationships',
    'accounts',
    'transactions',
    'users',
    'sessions',
    'payment_beneficiaries',
    'suspicious_activities',
    'alerts',
    'cases',
    'case_outcomes'
  )
ORDER BY name;
