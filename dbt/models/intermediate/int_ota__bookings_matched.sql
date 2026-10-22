-- Links each OTA booking to its PMS reservation.
-- Normally the channel manager sends the PMS number (hotel_reservation_no). When it is missing
-- (about 2% of records), the booking is matched on property, channel, stay dates and amount,
-- but only when exactly one unclaimed PMS reservation fits.

with ota as (

    select * from {{ ref('stg_ota__bookings') }}

),

pms as (

    select * from {{ ref('int_pms__reservations') }}

),

linked as (

    select ota.ota_ref, pms.res_no, 'reservation_no' as match_method
    from ota
    inner join pms on pms.res_no = ota.res_no

),

candidates as (

    select
        ota.ota_ref,
        pms.res_no,
        count(*) over (partition by ota.ota_ref) as candidates_for_ota,
        count(*) over (partition by pms.res_no)  as candidates_for_pms
    from ota
    inner join pms
        on pms.property_id = ota.property_id
        and pms.channel_id = ota.channel_id
        and pms.check_in_date = ota.check_in_date
        and pms.check_out_date = ota.check_out_date
        and pms.total_amount = ota.total_amount
    where ota.res_no is null
      and pms.res_no not in (select res_no from linked)

),

fallback as (

    select ota_ref, res_no, 'stay_attributes' as match_method
    from candidates
    where candidates_for_ota = 1 and candidates_for_pms = 1

),

matches as (

    select * from linked
    union all
    select * from fallback

)

select
    ota.ota_ref,
    matches.res_no,
    coalesce(matches.match_method, 'unmatched')           as match_method,
    ota.channel_id,
    ota.property_id,
    ota.commission_amount,
    ota.is_cancelled,
    ota.booked_at
from ota
left join matches on matches.ota_ref = ota.ota_ref
