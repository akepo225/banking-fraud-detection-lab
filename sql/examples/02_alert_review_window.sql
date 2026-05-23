-- Rank alerts within each Banking relationship for capacity-aware review queues.
WITH alert_queue AS (
  SELECT
    alerts.alert_id,
    alerts.generated_at,
    alerts.severity,
    br.banking_relationship_id,
    br.relationship_name,
    COALESCE(cases.case_status, 'not_opened') AS case_status,
    ROW_NUMBER() OVER (
      PARTITION BY br.banking_relationship_id
      ORDER BY alerts.generated_at, alerts.alert_id
    ) AS alert_sequence_for_relationship,
    COUNT(*) OVER (
      PARTITION BY br.banking_relationship_id
    ) AS relationship_alert_count,
    SUM(CASE WHEN cases.case_id IS NULL THEN 0 ELSE 1 END) OVER (
      PARTITION BY br.banking_relationship_id
    ) AS opened_case_count
  FROM alerts
  JOIN banking_relationships AS br
    ON br.banking_relationship_id = alerts.banking_relationship_id
  LEFT JOIN cases
    ON cases.alert_id = alerts.alert_id
)
SELECT
  alert_id,
  generated_at,
  severity,
  banking_relationship_id,
  relationship_name,
  case_status,
  alert_sequence_for_relationship,
  relationship_alert_count,
  opened_case_count
FROM alert_queue
ORDER BY generated_at, alert_id;
