-- One row per reservation. Grain: res_no.
-- Revenue and room nights count only reservations that were not cancelled.
-- Commission: actual amount from the OTA report when matched; contract rate otherwise.

with reservations as (

    select * from {{ ref('int_pms__reservations') }}

),

ota as (

    select res_no, ota_ref, commission_amount, match_method
    from {{ ref('int_ota__bookings_matched') }}
    where res_no is not null

),

as_of as (

    select data_as_of from {{ ref('data_freshness') }}

),

sequenced as (

    select
        r.*,
        count(*) filter (where not r.is_cancelled) over (
            partition by r.guest_key
            order by r.booked_at, r.res_no
            rows between unbounded preceding and 1 preceding
        )                                                 as prior_stays
    from reservations as r

)

select
    s.res_no,
    s.property_id,
    s.room_type_id,
    s.channel_id,
    s.guest_key,
    s.booked_at,
    s.booked_at::date                                     as booking_date,
    s.check_in_date,
    s.check_out_date,
    s.cancelled_at,
    s.cancelled_at::date                                  as cancellation_date,
    s.nights,
    s.adults,
    s.children,
    s.room_rate,
    s.total_amount,
    s.is_cancelled,
    case
        when s.is_cancelled then 'Cancelled'
        when s.check_out_date <= as_of.data_as_of then 'Completed'
        when s.check_in_date <= as_of.data_as_of then 'In-house'
        else 'Upcoming'
    end                                                   as booking_status,
    s.check_in_date - s.booked_at::date                   as lead_time_days,
    case when s.is_cancelled then 0 else s.nights end     as room_nights,
    case when s.is_cancelled then 0 else s.total_amount end
                                                          as booking_revenue,
    case
        when s.is_cancelled then 0
        when ota.commission_amount is not null then ota.commission_amount
        else round(s.total_amount * s.commission_rate, 2)
    end                                                   as commission_amount,
    case
        when s.channel_type = 'Direct' then 'none'
        when ota.commission_amount is not null then 'ota_report'
        else 'contract_rate'
    end                                                   as commission_source,
    case when s.is_cancelled then 0 else s.total_amount end
      - case
            when s.is_cancelled then 0
            when ota.commission_amount is not null then ota.commission_amount
            else round(s.total_amount * s.commission_rate, 2)
        end                                               as net_revenue,
    ota.ota_ref,
    ota.match_method                                      as ota_match_method,
    s.prior_stays > 0                                     as is_repeat_guest
from sequenced as s
cross join as_of
left join ota on ota.res_no = s.res_no
