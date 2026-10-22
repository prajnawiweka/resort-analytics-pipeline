-- One row per review, on a common 1-5 scale, with company property ids and local time.
-- Booking.com publishes 1-10; Google Reviews and TripAdvisor publish only an overall score.

with source as (

    select
        record,
        _source_file,
        row_number() over (
            partition by record ->> 'review_id'
            order by _source_file desc, _row_number desc
        ) as version_rank
    from {{ source('raw', 'reviews') }}

),

parsed as (

    select
        record ->> 'review_id'                                        as review_id,
        record ->> 'platform'                                         as platform,
        record ->> 'property'                                         as property_name_raw,
        nullif(record ->> 'booking_reference', '')                    as booking_reference,
        nullif(record ->> 'reviewer_country', '')                     as reviewer_country_name,
        (record -> 'rating' ->> 'scale')::numeric                     as rating_scale,
        (record -> 'rating' ->> 'overall')::numeric                   as overall_raw,
        (record -> 'rating' ->> 'cleanliness')::numeric               as cleanliness_raw,
        (record -> 'rating' ->> 'service')::numeric                   as service_raw,
        (record -> 'rating' ->> 'location')::numeric                  as location_raw,
        (record -> 'rating' ->> 'value')::numeric                     as value_raw,
        record ->> 'text'                                             as review_text,
        ((record ->> 'submitted_at')::timestamptz
            at time zone '{{ var("local_timezone") }}')               as submitted_at,
        _source_file                                                  as source_file
    from source
    where version_rank = 1

)

select
    parsed.review_id,
    parsed.platform,
    property_map.property_id,
    parsed.booking_reference,
    countries.country_code                                            as reviewer_country_code,
    parsed.rating_scale,
    round(parsed.overall_raw * 5 / parsed.rating_scale, 2)            as overall_rating,
    round(parsed.cleanliness_raw * 5 / parsed.rating_scale, 2)        as cleanliness_rating,
    round(parsed.service_raw * 5 / parsed.rating_scale, 2)            as service_rating,
    round(parsed.location_raw * 5 / parsed.rating_scale, 2)           as location_rating,
    round(parsed.value_raw * 5 / parsed.rating_scale, 2)              as value_rating,
    parsed.review_text,
    parsed.submitted_at,
    parsed.submitted_at::date                                         as review_date,
    parsed.property_name_raw,
    parsed.source_file
from parsed
left join {{ ref('property_name_map') }} as property_map
    on property_map.source_system = 'review'
    and property_map.source_name = parsed.property_name_raw
left join {{ ref('countries') }} as countries
    on countries.country_name = parsed.reviewer_country_name
