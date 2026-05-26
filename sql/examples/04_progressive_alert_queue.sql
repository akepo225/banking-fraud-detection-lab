-- Alert queue inspection using the foundation Alert lifecycle Progressive data view.
WITH alert_queue AS (
  SELECT
    alert_id,
    institution_name,
    banking_relationship_id,
    account_id,
    transaction_id,
    activity_type,
    alert_status,
    severity,
    generated_at,
    status_updated_at,
    COALESCE(case_status, 'not_opened') AS case_status,
    COALESCE(outcome_type, 'not_decided') AS outcome_type,
    ROUND(
      (JULIANDAY(status_updated_at) - JULIANDAY(generated_at)) * 24,
      2
    ) AS alert_age_hours_to_status_update,
    ROW_NUMBER() OVER (
      PARTITION BY institution_name
      ORDER BY
        CASE severity
          WHEN 'high' THEN 1
          WHEN 'medium' THEN 2
          ELSE 3
        END,
        generated_at,
        alert_id
    ) AS alert_queue_rank
  FROM foundation_alert_lifecycle
  WHERE alert_id IS NOT NULL
)
SELECT
  alert_id,
  institution_name,
  banking_relationship_id,
  account_id,
  transaction_id,
  activity_type,
  severity,
  alert_status,
  case_status,
  outcome_type,
  alert_age_hours_to_status_update,
  alert_queue_rank
FROM alert_queue
ORDER BY institution_name, alert_queue_rank, alert_id;
