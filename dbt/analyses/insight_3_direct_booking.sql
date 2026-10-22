-- Insight 3: direct booking share and commission cost, stays Jan-Sep 2025 vs 2026
select
    extract(year from b.check_in_date)::int                       as year,
    round(count(*) filter (where not b.is_cancelled and c.is_direct)::numeric
        / count(*) filter (where not b.is_cancelled), 4)          as direct_share,
    sum(b.booking_revenue)                                        as booking_revenue,
    sum(b.commission_amount)                                      as commission_cost,
    round(sum(b.commission_amount) / sum(b.booking_revenue), 4)   as commission_pct_of_revenue
from {{ ref('fact_bookings') }} as b
inner join {{ ref('dim_channel') }} as c using (channel_id)
where extract(month from b.check_in_date) between 1 and 9
  and extract(year from b.check_in_date) in (2025, 2026)
group by 1
order by 1
