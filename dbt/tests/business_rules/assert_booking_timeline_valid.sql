-- A reservation is booked on or before arrival, stays at least one night, and is cancelled
-- after it was booked and no later than the arrival day.

select res_no, booked_at, check_in_date, check_out_date, cancelled_at
from {{ ref('fact_bookings') }}
where booking_date > check_in_date
   or check_out_date <= check_in_date
   or check_out_date - check_in_date <> nights
   or (cancelled_at is not null and cancelled_at < booked_at)
   or (cancelled_at is not null and cancellation_date > check_in_date)
   or (is_cancelled and cancelled_at is null)
