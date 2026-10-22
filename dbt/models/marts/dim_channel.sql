select
    channel_id,
    channel_code,
    channel_name,
    channel_type,
    commission_rate,
    channel_type = 'Direct'                               as is_direct
from {{ ref('channels') }}
