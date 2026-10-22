-- Every reservation number that ever arrived from the PMS must reach fact_bookings exactly once.
-- Catches rows dropped by a failed code mapping (unknown hotel, room type or channel code).

with raw_reservations as (

    select distinct trim(res_no) as res_no
    from {{ source('raw', 'pms_reservations') }}

)

select r.res_no
from raw_reservations as r
left join {{ ref('fact_bookings') }} as f on f.res_no = r.res_no
where f.res_no is null
