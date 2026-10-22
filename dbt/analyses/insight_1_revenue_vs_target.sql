-- Insight 1: which properties drive the gap to the 2026 revenue target (Jan-Sep, complete months)
select
    p.location,
    sum(r.actual_revenue)                                         as actual_revenue,
    sum(r.revenue_target)                                         as revenue_target,
    sum(r.actual_revenue) - sum(r.revenue_target)                 as gap,
    round(sum(r.actual_revenue) / sum(r.revenue_target), 4)       as achievement
from {{ ref('mart_revenue_vs_target') }} as r
inner join {{ ref('dim_property') }} as p using (property_id)
where r.month_start between '2026-01-01' and '2026-09-01'
group by p.location
order by achievement
