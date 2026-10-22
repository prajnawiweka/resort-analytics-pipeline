-- One row per property per audit date. Amounts arrive as text such as "12,345.00".

with source as (

    select
        *,
        row_number() over (
            partition by audit_date, hotel_code
            order by _source_file desc, _row_number desc
        ) as version_rank
    from {{ source('raw', 'pms_night_audit') }}

)

select
    to_date(audit_date, 'DD/MM/YYYY')                     as audit_date,
    upper(trim(hotel_code))                               as property_code,
    rooms_available::int                                  as rooms_available,
    rooms_sold::int                                       as rooms_sold,
    replace(room_rev, ',', '')::numeric(14, 2)            as room_revenue,
    replace(fb_rev, ',', '')::numeric(14, 2)              as fnb_revenue,
    replace(spa_rev, ',', '')::numeric(14, 2)             as spa_revenue,
    replace(other_rev, ',', '')::numeric(14, 2)           as other_revenue,
    _source_file                                          as source_file
from source
where version_rank = 1
