-- One row per property per month. Grain: (month_start, property_id).

select
    target_month                                          as month_start,
    property_id,
    revenue_target,
    occupancy_target
from {{ ref('stg_finance__targets') }}
