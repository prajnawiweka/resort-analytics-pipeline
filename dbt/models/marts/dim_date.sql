-- Calendar from the first simulated stay to the end of the forecast horizon.
-- Bali seasons: high = Jul-Aug and 20 Dec-5 Jan; low = Feb, Mar, Nov; shoulder otherwise.

select
    d::date                                               as date_day,
    extract(year from d)::int                             as year,
    extract(quarter from d)::int                          as quarter,
    extract(month from d)::int                            as month,
    to_char(d, 'Mon')                                     as month_name,
    date_trunc('month', d)::date                          as month_start,
    extract(isodow from d)::int                           as day_of_week,
    to_char(d, 'Dy')                                      as day_name,
    extract(isodow from d) in (5, 6)                      as is_weekend_night,
    case
        when extract(month from d) in (7, 8)
          or (extract(month from d) = 12 and extract(day from d) >= 20)
          or (extract(month from d) = 1 and extract(day from d) <= 5) then 'High'
        when extract(month from d) in (2, 3, 11) then 'Low'
        else 'Shoulder'
    end                                                   as season
from generate_series('2024-12-01'::date, '2027-12-31'::date, interval '1 day') as d
