-- One row per property per day from the night audit. Grain: (date_day, property_id).
-- Additive columns only; ratios (occupancy, ADR, RevPAR) are SUM(numerator) / SUM(denominator).

select
    a.audit_date                                          as date_day,
    p.property_id,
    a.rooms_available,
    a.rooms_sold,
    a.room_revenue,
    a.fnb_revenue,
    a.spa_revenue,
    a.other_revenue,
    a.fnb_revenue + a.spa_revenue + a.other_revenue       as ancillary_revenue,
    a.room_revenue + a.fnb_revenue + a.spa_revenue + a.other_revenue
                                                          as total_revenue
from {{ ref('stg_pms__night_audit') }} as a
inner join {{ ref('properties') }} as p on p.property_code = a.property_code
