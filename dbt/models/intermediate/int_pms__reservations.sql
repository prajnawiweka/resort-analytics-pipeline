-- PMS reservations with company ids instead of PMS codes.

select
    r.res_no,
    p.property_id,
    rt.room_type_id,
    c.channel_id,
    c.channel_type,
    c.commission_rate,
    md5(r.guest_email)                                    as guest_key,
    r.guest_email,
    r.guest_first_name,
    r.guest_last_name,
    r.guest_country_code,
    r.check_in_date,
    r.check_out_date,
    r.nights,
    r.adults,
    r.children,
    r.room_rate,
    r.total_amount,
    r.is_cancelled,
    r.booked_at,
    r.cancelled_at
from {{ ref('stg_pms__reservations') }} as r
inner join {{ ref('properties') }} as p on p.property_code = r.property_code
inner join {{ ref('room_types') }} as rt on rt.room_type_code = r.room_type_code
inner join {{ ref('channels') }} as c on c.channel_code = r.channel_code
