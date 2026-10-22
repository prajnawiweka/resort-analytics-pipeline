-- Nothing in the marts may be dated after the last complete business date.

with as_of as (select data_as_of from {{ ref('data_freshness') }})

select 'booking' as record_type, res_no as record_id, booking_date as record_date
from {{ ref('fact_bookings') }}, as_of
where booking_date > as_of.data_as_of
union all
select 'review', review_id, review_date
from {{ ref('fact_reviews') }}, as_of
where review_date > as_of.data_as_of
union all
select 'audit', property_id::text, date_day
from {{ ref('fact_daily_revenue') }}, as_of
where date_day > as_of.data_as_of
