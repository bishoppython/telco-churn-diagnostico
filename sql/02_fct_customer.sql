-- Fato no grão de cliente, com atributos derivados usados na análise e no modelo.
create or replace table fct_customer as
select
    *,
    case
        when tenure_months <= 6  then '0-6 meses'
        when tenure_months <= 12 then '7-12 meses'
        when tenure_months <= 24 then '13-24 meses'
        when tenure_months <= 48 then '25-48 meses'
        else '49+ meses' end                                   as tenure_band,
    (online_security = 'Yes')::int + (online_backup = 'Yes')::int + (device_protection = 'Yes')::int
      + (tech_support = 'Yes')::int                            as protection_addons,
    (streaming_tv = 'Yes')::int + (streaming_movies = 'Yes')::int as streaming_addons
from stg_customers;
