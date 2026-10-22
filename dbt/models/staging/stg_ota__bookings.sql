-- One row per OTA booking (latest version per ota_ref), translated into company keys:
-- the channel manager's own property names and channel spellings are mapped to ids,
-- and its UTC timestamps are converted to Bali local time.

with source as (

    select
        record,
        _source_file,
        row_number() over (
            partition by record ->> 'ota_ref'
            order by _source_file desc, _row_number desc
        ) as version_rank
    from {{ source('raw', 'ota_bookings') }}

),

parsed as (

    select
        record ->> 'ota_ref'                                          as ota_ref,
        lower(trim(record ->> 'channel'))                             as channel_name_normalized,
        record ->> 'channel'                                          as channel_name_raw,
        record ->> 'property'                                         as property_name_raw,
        nullif(trim(record ->> 'hotel_reservation_no'), '')           as res_no,
        (record -> 'stay' ->> 'check_in')::date                       as check_in_date,
        (record -> 'stay' ->> 'check_out')::date                      as check_out_date,
        (record ->> 'total_amount')::numeric(12, 2)                   as total_amount,
        (record -> 'commission' ->> 'amount')::numeric(12, 2)         as commission_amount,
        record -> 'commission' ->> 'currency'                         as commission_currency,
        record ->> 'status'                                           as ota_status,
        ((record ->> 'booked_at')::timestamptz
            at time zone '{{ var("local_timezone") }}')               as booked_at,
        ((record ->> 'cancelled_at')::timestamptz
            at time zone '{{ var("local_timezone") }}')               as cancelled_at,
        _source_file                                                  as source_file
    from source
    where version_rank = 1

)

select
    parsed.ota_ref,
    channel_map.channel_id,
    property_map.property_id,
    parsed.res_no,
    parsed.check_in_date,
    parsed.check_out_date,
    parsed.total_amount,
    parsed.commission_amount,
    parsed.commission_currency,
    parsed.ota_status,
    parsed.ota_status = 'cancelled'                                   as is_cancelled,
    parsed.booked_at,
    parsed.cancelled_at,
    parsed.channel_name_raw,
    parsed.property_name_raw,
    parsed.source_file
from parsed
left join {{ ref('channel_name_map') }} as channel_map
    on channel_map.source_system = 'ota'
    and channel_map.source_name_normalized = parsed.channel_name_normalized
left join {{ ref('property_name_map') }} as property_map
    on property_map.source_system = 'ota'
    and property_map.source_name = parsed.property_name_raw
