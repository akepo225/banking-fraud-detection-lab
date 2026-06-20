-- Digital-banking session and channel features for session_payment_velocity and
-- new_beneficiary_payment.
-- Demonstrates session risk telemetry, risky channel, and beneficiary-country
-- risk signals for NovaBank Digital transactions.
WITH digital_transactions AS (
  SELECT
    t.transaction_id,
    t.account_id,
    t.booked_at,
    t.channel,
    t.direction,
    CAST(t.amount_chf AS REAL) AS amount_chf,
    t.payment_beneficiary_id,
    sa.session_id
  FROM transactions AS t
  JOIN accounts AS a
    ON a.account_id = t.account_id
  LEFT JOIN suspicious_activities AS sa
    ON sa.transaction_id = t.transaction_id
  WHERE a.institution_name = 'NovaBank Digital'
),
session_context AS (
  SELECT
    dt.transaction_id,
    dt.account_id,
    dt.booked_at,
    dt.channel,
    dt.direction,
    dt.amount_chf,
    dt.payment_beneficiary_id,
    dt.session_id,
    s.is_vpn_or_proxy,
    s.asn_risk_score,
    s.auth_method,
    pb.beneficiary_account_country
  FROM digital_transactions AS dt
  LEFT JOIN sessions AS s
    ON s.session_id = dt.session_id
  LEFT JOIN payment_beneficiaries AS pb
    ON pb.payment_beneficiary_id = dt.payment_beneficiary_id
)
SELECT
  transaction_id,
  account_id,
  booked_at,
  channel,
  direction,
  ROUND(amount_chf, 2) AS amount_chf,
  CASE WHEN is_vpn_or_proxy = 1 THEN 1 ELSE 0 END AS db_is_vpn_or_proxy,
  COALESCE(asn_risk_score, 0) AS db_asn_risk_score,
  CASE WHEN COALESCE(asn_risk_score, 0) >= 70 THEN 1 ELSE 0 END AS db_is_high_risk_network,
  CASE WHEN auth_method = 'password_sms' THEN 1 ELSE 0 END AS db_is_password_sms_auth,
  CASE WHEN channel = 'mobile_app' THEN 1 ELSE 0 END AS db_is_mobile_app_channel,
  CASE
    WHEN beneficiary_account_country IN ('LT', 'BG', 'RU') THEN 1
    ELSE 0
  END AS db_is_beneficiary_country_risky
FROM session_context
ORDER BY booked_at, transaction_id;
