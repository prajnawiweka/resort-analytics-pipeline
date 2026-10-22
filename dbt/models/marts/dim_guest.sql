-- One row per guest, identified by e-mail address.
-- Segment: VIP = 3+ stays or USD 6,000+ spent; Returning = 2 stays; New = otherwise.

with reservations as (

    select * from {{ ref('int_pms__reservations') }}

),

latest_profile as (

    select distinct on (guest_key)
        guest_key, guest_first_name, guest_last_name, guest_country_code
    from reservations
    order by guest_key, booked_at desc

),

history as (

    select
        guest_key,
        min(booked_at)::date                                          as first_booking_date,
        count(*) filter (where not is_cancelled)                      as stays,
        coalesce(sum(total_amount) filter (where not is_cancelled), 0) as lifetime_spend
    from reservations
    group by guest_key

)

select
    p.guest_key,
    p.guest_first_name                                    as first_name,
    p.guest_last_name                                     as last_name,
    p.guest_country_code                                  as country_code,
    c.country_name,
    h.first_booking_date,
    h.stays,
    h.lifetime_spend,
    case
        when h.stays >= 3 or h.lifetime_spend >= 6000 then 'VIP'
        when h.stays = 2 then 'Returning'
        else 'New'
    end                                                   as guest_segment
from latest_profile as p
inner join history as h on h.guest_key = p.guest_key
left join {{ ref('countries') }} as c on c.country_code = p.guest_country_code
