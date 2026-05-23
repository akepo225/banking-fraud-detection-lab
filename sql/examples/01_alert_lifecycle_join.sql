-- Join suspicious activity through the alert lifecycle for review exercises.
SELECT
  br.banking_relationship_id,
  br.relationship_name,
  accounts.account_id,
  transactions.transaction_id,
  transactions.booked_at,
  transactions.amount_chf,
  users.user_id,
  sessions.session_id,
  alerts.alert_id,
  alerts.alert_status,
  cases.case_id,
  cases.case_status
FROM alerts
JOIN suspicious_activities
  ON suspicious_activities.suspicious_activity_id = alerts.suspicious_activity_id
JOIN banking_relationships AS br
  ON br.banking_relationship_id = alerts.banking_relationship_id
JOIN accounts
  ON accounts.account_id = alerts.account_id
JOIN transactions
  ON transactions.transaction_id = alerts.triggered_transaction_id
LEFT JOIN users
  ON users.user_id = alerts.user_id
LEFT JOIN sessions
  ON sessions.session_id = alerts.session_id
LEFT JOIN cases
  ON cases.alert_id = alerts.alert_id
ORDER BY alerts.generated_at, alerts.alert_id;
