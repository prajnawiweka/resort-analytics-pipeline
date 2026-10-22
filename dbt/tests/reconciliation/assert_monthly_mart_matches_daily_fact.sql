-- The KPI mart must add up to the daily fact it is built from, per property.

with mart as (

    select property_id, sum(total_revenue) as revenue, sum(rooms_sold) as rooms_sold
    from {{ ref('mart_property_monthly') }}
    group by 1

),

fact as (

    select property_id, sum(total_revenue) as revenue, sum(rooms_sold) as rooms_sold
    from {{ ref('fact_daily_revenue') }}
    group by 1

)

select fact.property_id, fact.revenue, mart.revenue as mart_revenue,
       fact.rooms_sold, mart.rooms_sold as mart_rooms_sold
from fact
full outer join mart on mart.property_id = fact.property_id
where mart.revenue is distinct from fact.revenue
   or mart.rooms_sold is distinct from fact.rooms_sold
