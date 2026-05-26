-- Cohort-style analysis using the foundation Client relationship Progressive data view.
WITH relationship_context AS (
  SELECT
    fcr.client_id,
    fcr.client_segment,
    fcr.risk_rating,
    fcr.institution_name,
    fcr.banking_relationship_id,
    accounts.account_id
  FROM foundation_client_relationships AS fcr
  LEFT JOIN accounts
    ON accounts.banking_relationship_id = fcr.banking_relationship_id
),
cohort_rollup AS (
  SELECT
    client_segment,
    risk_rating,
    COUNT(DISTINCT client_id) AS cohort_client_count,
    COUNT(DISTINCT relationship_context.banking_relationship_id)
      AS cohort_relationship_count,
    COUNT(DISTINCT relationship_context.account_id) AS cohort_account_count,
    COUNT(DISTINCT transactions.transaction_id) AS cohort_transaction_count,
    COUNT(DISTINCT foundation_alert_lifecycle.alert_id) AS cohort_alert_count
  FROM relationship_context
  LEFT JOIN transactions
    ON transactions.account_id = relationship_context.account_id
  LEFT JOIN foundation_alert_lifecycle
    ON foundation_alert_lifecycle.banking_relationship_id =
       relationship_context.banking_relationship_id
  GROUP BY client_segment, risk_rating
)
SELECT
  client_segment,
  risk_rating,
  cohort_client_count,
  cohort_relationship_count,
  cohort_account_count,
  cohort_transaction_count,
  cohort_alert_count
FROM cohort_rollup
ORDER BY client_segment, risk_rating;
