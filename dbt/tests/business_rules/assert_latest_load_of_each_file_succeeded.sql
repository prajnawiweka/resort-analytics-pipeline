-- Warn when the most recent attempt to load a file failed (e.g. the source changed its format).
{{ config(severity='warn') }}

with ranked as (

    select
        source_file,
        status,
        error,
        row_number() over (partition by source_file order by load_id desc) as attempt_rank
    from {{ source('raw', 'load_log') }}

)

select source_file, error
from ranked
where attempt_rank = 1 and status = 'failed'
