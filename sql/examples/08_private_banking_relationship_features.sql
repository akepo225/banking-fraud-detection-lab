-- Private-banking relationship features for pb_transaction_fraud.
-- Demonstrates new-counterparty detection and relationship-manager
-- concentration for Alpine Crest Private Bank transactions.
WITH transaction_counterparties AS (
  SELECT
    t.transaction_id,
    t.account_id,
    a.banking_relationship_id,
    br.relationship_manager_code,
    t.payment_beneficiary_id,
    t.booked_at,
    pb.created_at AS counterparty_created_at,
    pb.beneficiary_change_event,
    ROW_NUMBER() OVER (
      PARTITION BY t.payment_beneficiary_id
      ORDER BY t.booked_at, t.transaction_id
    ) AS counterparty_use_rank
  FROM transactions AS t
  JOIN accounts AS a
    ON a.account_id = t.account_id
  JOIN banking_relationships AS br
    ON br.banking_relationship_id = a.banking_relationship_id
  LEFT JOIN payment_beneficiaries AS pb
    ON pb.payment_beneficiary_id = t.payment_beneficiary_id
  WHERE br.institution_name = 'Alpine Crest Private Bank'
),
rm_alert_counts AS (
  SELECT
    br.relationship_manager_code,
    COUNT(DISTINCT al.alert_id) AS rm_alert_count
  FROM banking_relationships AS br
  LEFT JOIN alerts AS al
    ON al.banking_relationship_id = br.banking_relationship_id
  WHERE br.institution_name = 'Alpine Crest Private Bank'
  GROUP BY br.relationship_manager_code
),
rm_case_counts AS (
  SELECT
    br.relationship_manager_code,
    COUNT(DISTINCT ca.case_id) AS rm_case_count
  FROM banking_relationships AS br
  LEFT JOIN cases AS ca
    ON ca.banking_relationship_id = br.banking_relationship_id
  WHERE br.institution_name = 'Alpine Crest Private Bank'
  GROUP BY br.relationship_manager_code
),
rm_concentration AS (
  SELECT
    rm_alert_counts.relationship_manager_code,
    rm_alert_counts.rm_alert_count,
    rm_case_counts.rm_case_count,
    CASE
      WHEN SUM(rm_alert_counts.rm_alert_count) OVER () > 0
        THEN CAST(rm_alert_counts.rm_alert_count AS REAL)
          / SUM(rm_alert_counts.rm_alert_count) OVER ()
      ELSE 0
    END AS rm_alert_share
  FROM rm_alert_counts
  JOIN rm_case_counts
    ON rm_case_counts.relationship_manager_code =
      rm_alert_counts.relationship_manager_code
)
SELECT
  transaction_counterparties.transaction_id,
  transaction_counterparties.banking_relationship_id,
  transaction_counterparties.relationship_manager_code,
  transaction_counterparties.payment_beneficiary_id,
  transaction_counterparties.booked_at,
  CASE
    WHEN transaction_counterparties.payment_beneficiary_id IS NOT NULL
      AND (
        transaction_counterparties.counterparty_use_rank = 1
        OR transaction_counterparties.beneficiary_change_event =
          'new_beneficiary_added'
        OR (
          julianday(transaction_counterparties.booked_at)
            - julianday(transaction_counterparties.counterparty_created_at)
        ) BETWEEN 0 AND 30
      ) THEN 1
    ELSE 0
  END AS is_new_counterparty,
  ROUND(
    CASE
      WHEN transaction_counterparties.counterparty_created_at IS NOT NULL
        THEN julianday(transaction_counterparties.booked_at)
          - julianday(transaction_counterparties.counterparty_created_at)
      ELSE -1
    END,
    2
  ) AS counterparty_age_days,
  rm_concentration.rm_alert_count,
  rm_concentration.rm_case_count,
  ROUND(rm_concentration.rm_alert_share, 4) AS rm_alert_share
FROM transaction_counterparties
JOIN rm_concentration
  ON rm_concentration.relationship_manager_code =
    transaction_counterparties.relationship_manager_code
ORDER BY transaction_counterparties.booked_at, transaction_counterparties.transaction_id;
