-- Every property has a night audit for every day from the first audit to data_as_of.
-- A gap means a daily file was not delivered or not loaded.

with as_of as (

    select data_as_of from {{ ref('data_freshness') }}

),

expected as (

    select d.date_day, p.property_id
    from {{ ref('dim_date') }} as d
    cross join {{ ref('dim_property') }} as p
    cross join as_of
    where d.date_day between (select min(date_day) from {{ ref('fact_daily_revenue') }})
                         and as_of.data_as_of

)

select e.date_day, e.property_id
from expected as e
left join {{ ref('fact_daily_revenue') }} as f
    on f.date_day = e.date_day
    and f.property_id = e.property_id
where f.date_day is null
