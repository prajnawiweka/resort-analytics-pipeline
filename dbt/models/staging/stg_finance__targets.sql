-- One row per property per month with revenue and occupancy targets.
-- The finance workbook is wide (one column per month, e.g. "Jan-26") and ends with a TOTAL
-- row; this model unpivots the months and drops the total.

with rows as (

    select
        sheet_name,
        record,
        _source_file,
        substring(_source_file from 'finance_targets_(\d{4})')::int   as target_year
    from {{ source('raw', 'finance_targets') }}

),

-- if Finance re-issues a year's workbook, only the newest file counts
latest_file as (

    select target_year, max(_source_file) as source_file
    from rows
    group by target_year

),

cells as (

    select
        rows.sheet_name,
        rows.record ->> 'Property'                                    as property_name_raw,
        to_date(month_cell.key, 'Mon-YY')                             as target_month,
        month_cell.value #>> '{}'                                     as cell_value,
        rows._source_file
    from rows
    inner join latest_file
        on latest_file.source_file = rows._source_file
    cross join lateral jsonb_each(rows.record) as month_cell
    where month_cell.key ~ '^[A-Z][a-z]{2}-\d{2}$'
      and upper(trim(rows.record ->> 'Property')) <> 'TOTAL'

)

select
    property_map.property_id,
    cells.target_month,
    max(case when cells.sheet_name = 'Revenue Target'
             then cells.cell_value::numeric end)::numeric(14, 2)      as revenue_target,
    max(case when cells.sheet_name = 'Occupancy Target'
             then cells.cell_value::numeric end)::numeric(6, 4)       as occupancy_target,
    max(cells.property_name_raw)                                      as property_name_raw,
    max(cells._source_file)                                           as source_file
from cells
left join {{ ref('property_name_map') }} as property_map
    on property_map.source_system = 'finance'
    and property_map.source_name = cells.property_name_raw
group by property_map.property_id, cells.target_month
