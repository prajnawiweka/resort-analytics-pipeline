-- Commission reported by the channel manager should equal the contracted rate for that OTA.
-- A difference above 1 USD means either the contract table (seed) or the OTA invoice is wrong.

select
    b.res_no,
    c.channel_name,
    b.total_amount,
    b.commission_amount,
    round(b.total_amount * c.commission_rate, 2)          as contract_commission
from {{ ref('fact_bookings') }} as b
inner join {{ ref('dim_channel') }} as c on c.channel_id = b.channel_id
where b.commission_source = 'ota_report'
  and not b.is_cancelled  -- cancelled reservations carry no commission
  and abs(b.commission_amount - b.total_amount * c.commission_rate) > 1
