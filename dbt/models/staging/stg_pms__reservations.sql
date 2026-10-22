-- One row per PMS reservation, latest version.
-- The PMS re-sends a reservation when it is cancelled, and sometimes repeats a line;
-- the newest business date (then the last row in that file) wins.

with source as (

    select
        *,
        left(_source_file, 10)::date as business_date
    from {{ source('raw', 'pms_reservations') }}

),

latest as (

    select
        *,
        row_number() over (
            partition by trim(res_no)
            order by business_date desc, _row_number desc
        ) as version_rank
    from source

)

select
    trim(res_no)                                          as res_no,
    upper(trim(hotel_code))                               as property_code,
    upper(trim(room_type))                                as room_type_code,
    upper(trim(source))                                   as channel_code,
    to_date(arrival, 'DD/MM/YYYY')                        as check_in_date,
    to_date(departure, 'DD/MM/YYYY')                      as check_out_date,
    nights::int                                           as nights,
    adults::int                                           as adults,
    children::int                                         as children,
    rate::numeric(12, 2)                                  as room_rate,
    total::numeric(12, 2)                                 as total_amount,
    upper(trim(status))                                   as pms_status,
    upper(trim(status)) = 'CANCELLED'                     as is_cancelled,
    trim(split_part(guest_name, ',', 2))                  as guest_first_name,
    initcap(trim(split_part(guest_name, ',', 1)))         as guest_last_name,
    lower(trim(guest_email))                              as guest_email,
    upper(trim(guest_country))                            as guest_country_code,
    to_timestamp(created_at, 'DD/MM/YYYY HH24:MI')::timestamp           as booked_at,
    to_timestamp(nullif(trim(cancelled_at), ''), 'DD/MM/YYYY HH24:MI')::timestamp
                                                          as cancelled_at,
    business_date                                         as last_seen_business_date,
    _source_file                                          as source_file
from latest
where version_rank = 1
