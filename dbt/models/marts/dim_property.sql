select
    property_id,
    property_code,
    property_name,
    location,
    total_rooms,
    property_type,
    opening_date
from {{ ref('properties') }}
