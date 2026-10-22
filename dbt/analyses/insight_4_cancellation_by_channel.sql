-- Insight 4: cancellation rate and lead time by channel type, check-ins Jan-Sep 2026
select
    c.channel_type,
    count(*)                                                      as bookings,
    round(avg(b.is_cancelled::int), 4)                            as cancellation_rate,
    round(avg(b.lead_time_days), 1)                               as avg_lead_time_days
from {{ ref('fact_bookings') }} as b
inner join {{ ref('dim_channel') }} as c using (channel_id)
where b.check_in_date between '2026-01-01' and '2026-09-30'
group by 1
order by cancellation_rate desc
