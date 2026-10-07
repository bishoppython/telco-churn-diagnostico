-- Staging: tipagem e padronização. TotalCharges vem em branco para clientes com 0 meses de casa
-- (ainda não faturados); nesses casos o valor correto é 0, não nulo.
create or replace table stg_customers as
select
    customerID                                              as customer_id,
    gender,
    SeniorCitizen = '1'                                     as is_senior,
    Partner = 'Yes'                                         as has_partner,
    Dependents = 'Yes'                                      as has_dependents,
    cast(tenure as integer)                                 as tenure_months,
    PhoneService = 'Yes'                                    as has_phone,
    MultipleLines                                           as multiple_lines,
    InternetService                                         as internet_service,
    OnlineSecurity                                          as online_security,
    OnlineBackup                                            as online_backup,
    DeviceProtection                                        as device_protection,
    TechSupport                                             as tech_support,
    StreamingTV                                             as streaming_tv,
    StreamingMovies                                         as streaming_movies,
    Contract                                                as contract,
    PaperlessBilling = 'Yes'                                as paperless_billing,
    PaymentMethod                                           as payment_method,
    cast(MonthlyCharges as double)                          as monthly_charges,
    coalesce(try_cast(nullif(trim(TotalCharges), '') as double), 0) as total_charges,
    Churn = 'Yes'                                           as churned
from raw_telco;
