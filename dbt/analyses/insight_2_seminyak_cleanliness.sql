-- Insight 2: Seminyak cleanliness and low-rating share, Jun-Sep vs Jan-May, 2025 vs 2026
select
    p.location,
    extract(year from m.month_start)::int                         as year,
    round(avg(m.avg_cleanliness) filter (where extract(month from m.month_start) between 1 and 5), 2)
                                                                  as cleanliness_jan_may,
    round(avg(m.avg_cleanliness) filter (where extract(month from m.month_start) between 6 and 9), 2)
                                                                  as cleanliness_jun_sep,
    round(sum(m.reviews * m.low_rating_share) filter (where extract(month from m.month_start) between 6 and 9)
        / nullif(sum(m.reviews) filter (where extract(month from m.month_start) between 6 and 9), 0), 4)
                                                                  as low_rating_share_jun_sep
from {{ ref('mart_property_monthly') }} as m
inner join {{ ref('dim_property') }} as p using (property_id)
group by 1, 2
order by 1, 2
