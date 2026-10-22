-- One row per review. Grain: review_id.
-- Reviews are tied to a reservation when the platform allows it:
--   Post-stay Survey -> PMS number directly; Booking.com -> OTA reference -> PMS number.
-- Google Reviews and TripAdvisor carry no booking reference.

with reviews as (

    select * from {{ ref('stg_reviews') }}

),

ota as (

    select ota_ref, res_no from {{ ref('int_ota__bookings_matched') }}

),

resolved as (

    select
        r.*,
        case
            when r.platform = 'Post-stay Survey' then r.booking_reference
            when r.platform = 'Booking.com' then ota.res_no
        end                                               as res_no
    from reviews as r
    left join ota
        on r.platform = 'Booking.com'
        and ota.ota_ref = r.booking_reference

)

select
    r.review_id,
    r.property_id,
    r.review_date,
    r.submitted_at,
    r.platform,
    b.res_no,
    b.channel_id,
    coalesce(r.reviewer_country_code, b.guest_country_code)
                                                          as reviewer_country_code,
    r.overall_rating,
    r.cleanliness_rating,
    r.service_rating,
    r.location_rating,
    r.value_rating,
    r.overall_rating < {{ var('low_rating_threshold') }}  as is_low_rating,
    r.review_text
from resolved as r
left join {{ ref('int_pms__reservations') }} as b on b.res_no = r.res_no

