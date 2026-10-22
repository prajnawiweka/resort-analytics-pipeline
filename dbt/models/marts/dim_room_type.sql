select
    rt.room_type_id,
    rt.property_id,
    rt.room_type_code,
    rt.room_category,
    rt.base_rate,
    rt.max_occupancy,
    rt.room_count
from {{ ref('room_types') }} as rt
