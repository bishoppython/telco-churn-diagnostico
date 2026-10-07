-- Taxa de churn e receita mensal perdida por segmento, em formato longo (dimensão, segmento).
create or replace table mart_churn_segments as
with base as (
    select 'Contrato' dim, contract seg, * from fct_customer
    union all select 'Tempo de casa', tenure_band, * from fct_customer
    union all select 'Internet', internet_service, * from fct_customer
    union all select 'Pagamento', payment_method, * from fct_customer
    union all select 'Serviços de proteção (com internet)', cast(protection_addons as varchar), * from fct_customer where internet_service <> 'No'
    union all select 'Fatura digital', case when paperless_billing then 'Sim' else 'Não' end, * from fct_customer
    union all select 'Idoso', case when is_senior then 'Sim' else 'Não' end, * from fct_customer
)
select
    dim, seg,
    count(*)                                            as customers,
    sum(churned::int)                                   as churners,
    round(100.0 * avg(churned::int), 1)                 as churn_rate_pct,
    round(sum(case when churned then monthly_charges else 0 end), 2) as lost_mrr
from base
group by dim, seg;
