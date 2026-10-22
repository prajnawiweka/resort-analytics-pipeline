-- Insight 5: F&B revenue per occupied room night, Jun-Sep 2025 vs 2026 (Ubud rooftop opened Jun 2026)
select
    p.location,
    extract(year from f.date_day)::int                            as year,
    round(sum(f.fnb_revenue) / sum(f.rooms_sold), 2)              as fnb_per_room_night
from {{ ref('fact_daily_revenue') }} as f
inner join {{ ref('dim_property') }} as p using (property_id)
where extract(month from f.date_day) between 6 and 9
group by 1, 2
order by 1, 2
