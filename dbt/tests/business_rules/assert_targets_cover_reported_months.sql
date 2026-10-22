-- Every property must have a Finance target for every month that has actual data.
-- Without it the revenue-vs-target dashboard would silently show gaps.

with months as (

    select distinct date_trunc('month', date_day)::date as month_start, property_id
    from {{ ref('fact_daily_revenue') }}

)

select m.month_start, m.property_id
from months as m
left join {{ ref('fact_monthly_target') }} as t
    on t.month_start = m.month_start
    and t.property_id = m.property_id
where t.month_start is null
