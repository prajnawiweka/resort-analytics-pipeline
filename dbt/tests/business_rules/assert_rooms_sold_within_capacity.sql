-- A hotel cannot sell more rooms than it has available, nor have more available than it owns.

select f.date_day, f.property_id, f.rooms_sold, f.rooms_available, p.total_rooms
from {{ ref('fact_daily_revenue') }} as f
inner join {{ ref('dim_property') }} as p on p.property_id = f.property_id
where f.rooms_sold > f.rooms_available
   or f.rooms_available > p.total_rooms
   or f.rooms_sold < 0
