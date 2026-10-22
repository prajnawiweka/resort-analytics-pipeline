-- One row: the last business date with complete data. Dashboards show it as "data as of".

select
    max(audit_date)                                       as data_as_of,
    (select max(finished_at) from {{ source('raw', 'load_log') }}
     where status = 'success')                            as last_loaded_at
from {{ ref('stg_pms__night_audit') }}
