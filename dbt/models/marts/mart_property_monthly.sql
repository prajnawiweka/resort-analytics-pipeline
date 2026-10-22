-- Monthly KPI table per property: one place where every dashboard KPI is defined.
-- Stay KPIs use the night audit; booking KPIs use check-in month; review KPIs use review month.
-- Ratios are computed from monthly totals, never by averaging daily ratios.

with stays as (

    select
        date_trunc('month', date_day)::date               as month_start,
        property_id,
        sum(rooms_available)                              as rooms_available,
        sum(rooms_sold)                                   as rooms_sold,
        sum(room_revenue)                                 as room_revenue,
        sum(ancillary_revenue)                            as ancillary_revenue,
        sum(total_revenue)                                as total_revenue
    from {{ ref('fact_daily_revenue') }}
    group by 1, 2

),

bookings as (

    select
        date_trunc('month', b.check_in_date)::date        as month_start,
        b.property_id,
        count(*)                                          as bookings,
        count(*) filter (where b.is_cancelled)            as cancellations,
        count(*) filter (where not b.is_cancelled and c.is_direct)
                                                          as direct_bookings,
        count(*) filter (where not b.is_cancelled)        as confirmed_bookings,
        avg(b.lead_time_days)                             as avg_lead_time_days,
        sum(b.commission_amount)                          as commission_cost
    from {{ ref('fact_bookings') }} as b
    inner join {{ ref('dim_channel') }} as c on c.channel_id = b.channel_id
    group by 1, 2

),

reviews as (

    select
        date_trunc('month', review_date)::date            as month_start,
        property_id,
        count(*)                                          as reviews,
        avg(overall_rating)                               as avg_rating,
        avg(cleanliness_rating)                           as avg_cleanliness,
        avg(service_rating)                               as avg_service,
        count(*) filter (where is_low_rating)             as low_ratings
    from {{ ref('fact_reviews') }}
    group by 1, 2

),

monthly as (

    select
        s.month_start,
        s.property_id,
        s.rooms_available,
        s.rooms_sold,
        s.room_revenue,
        s.ancillary_revenue,
        s.total_revenue,
        round(s.rooms_sold::numeric / nullif(s.rooms_available, 0), 4)   as occupancy_rate,
        round(s.room_revenue / nullif(s.rooms_sold, 0), 2)               as adr,
        round(s.room_revenue / nullif(s.rooms_available, 0), 2)          as revpar,
        coalesce(b.bookings, 0)                                          as bookings,
        coalesce(b.cancellations, 0)                                     as cancellations,
        round(b.cancellations::numeric / nullif(b.bookings, 0), 4)       as cancellation_rate,
        round(b.direct_bookings::numeric / nullif(b.confirmed_bookings, 0), 4)
                                                                         as direct_booking_share,
        round(b.avg_lead_time_days, 1)                                   as avg_lead_time_days,
        coalesce(b.commission_cost, 0)                                   as commission_cost,
        coalesce(r.reviews, 0)                                           as reviews,
        round(r.avg_rating, 2)                                           as avg_rating,
        round(r.avg_cleanliness, 2)                                      as avg_cleanliness,
        round(r.avg_service, 2)                                          as avg_service,
        round(r.low_ratings::numeric / nullif(r.reviews, 0), 4)          as low_rating_share
    from stays as s
    left join bookings as b
        on b.month_start = s.month_start and b.property_id = s.property_id
    left join reviews as r
        on r.month_start = s.month_start and r.property_id = s.property_id

)

select
    m.*,
    ly.total_revenue                                                     as total_revenue_last_year,
    round(m.total_revenue / nullif(ly.total_revenue, 0) - 1, 4)          as total_revenue_yoy,
    ly.occupancy_rate                                                    as occupancy_rate_last_year
from monthly as m
left join monthly as ly
    on ly.property_id = m.property_id
    and ly.month_start = (m.month_start - interval '1 year')::date
