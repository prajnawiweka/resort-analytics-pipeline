-- The PMS night audit must agree with the reservations staying each night:
-- rooms sold = number of non-cancelled reservations in house, room revenue = sum of their rates.
-- A mismatch means reservations were lost, duplicated or mis-dated somewhere in the pipeline.

with nights as (

    select
        b.property_id,
        (b.check_in_date + n)::date                       as date_day,
        b.room_rate
    from {{ ref('fact_bookings') }} as b
    cross join lateral generate_series(0, b.nights - 1) as n
    where not b.is_cancelled

),

expected as (

    select property_id, date_day, count(*) as rooms_sold, sum(room_rate) as room_revenue
    from nights
    group by 1, 2

)

select
    a.date_day,
    a.property_id,
    a.rooms_sold                                          as audit_rooms_sold,
    coalesce(e.rooms_sold, 0)                             as reservation_rooms_sold,
    a.room_revenue                                        as audit_room_revenue,
    coalesce(e.room_revenue, 0)                           as reservation_room_revenue
from {{ ref('fact_daily_revenue') }} as a
left join expected as e
    on e.property_id = a.property_id
    and e.date_day = a.date_day
where a.rooms_sold <> coalesce(e.rooms_sold, 0)
   or a.room_revenue <> coalesce(e.room_revenue, 0)
