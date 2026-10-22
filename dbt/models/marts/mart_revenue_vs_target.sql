-- Actual vs target per property per month, up to the month of the latest data.
-- For the running month the target is pro-rated by elapsed days so achievement is comparable.

with as_of as (

    select data_as_of from {{ ref('data_freshness') }}

),

actual as (

    select
        date_trunc('month', date_day)::date               as month_start,
        property_id,
        count(*)                                          as days_reported,
        sum(total_revenue)                                as actual_revenue,
        sum(rooms_sold)                                   as rooms_sold,
        sum(rooms_available)                              as rooms_available
    from {{ ref('fact_daily_revenue') }}
    group by 1, 2

)

select
    t.month_start,
    t.property_id,
    extract(day from (t.month_start + interval '1 month - 1 day'))::int
                                                          as days_in_month,
    coalesce(a.days_reported, 0)                          as days_reported,
    coalesce(a.days_reported, 0)
        = extract(day from (t.month_start + interval '1 month - 1 day'))::int
                                                          as is_month_complete,
    coalesce(a.actual_revenue, 0)                         as actual_revenue,
    t.revenue_target,
    round(t.revenue_target * coalesce(a.days_reported, 0)
        / extract(day from (t.month_start + interval '1 month - 1 day')), 2)
                                                          as revenue_target_to_date,
    round(coalesce(a.actual_revenue, 0)
        / nullif(t.revenue_target * coalesce(a.days_reported, 0)
            / extract(day from (t.month_start + interval '1 month - 1 day')), 0), 4)
                                                          as revenue_achievement,
    round(a.rooms_sold::numeric / nullif(a.rooms_available, 0), 4)
                                                          as occupancy_actual,
    t.occupancy_target,
    round(a.rooms_sold::numeric / nullif(a.rooms_available, 0), 4) - t.occupancy_target
                                                          as occupancy_gap
from {{ ref('fact_monthly_target') }} as t
cross join as_of
left join actual as a
    on a.month_start = t.month_start
    and a.property_id = t.property_id
where t.month_start <= as_of.data_as_of
