-- Raw landing tables. Data is stored exactly as received:
--   * CSV feeds: one text column per source column (no casting, so a bad value never blocks a load)
--   * JSON / Excel feeds: one jsonb record per item or row
-- Every row keeps where it came from (_source_file, _row_number) and which load wrote it.
-- Cleaning, typing and key mapping happen later in dbt staging.

create table if not exists raw.load_log (
    load_id        bigint generated always as identity primary key,
    business_date  date        not null,
    source         text        not null,
    source_file    text        not null,
    file_sha256    text        not null,
    rows_loaded    integer,
    status         text        not null check (status in ('success', 'failed')),
    error          text,
    started_at     timestamptz not null,
    finished_at    timestamptz not null default now()
);
create index if not exists load_log_file_idx on raw.load_log (source_file, status);
comment on table raw.load_log is 'One row per file load attempt. A file is skipped when the same content (sha256) already loaded successfully.';

create table if not exists raw.pms_reservations (
    res_no        text,
    hotel_code    text,
    room_type     text,
    arrival       text,
    departure     text,
    nights        text,
    adults        text,
    children      text,
    rate          text,
    total         text,
    status        text,
    source        text,
    guest_name    text,
    guest_email   text,
    guest_country text,
    created_at    text,
    cancelled_at  text,
    _load_id      bigint      not null references raw.load_log (load_id),
    _source_file  text        not null,
    _row_number   integer     not null,
    _loaded_at    timestamptz not null default now(),
    primary key (_source_file, _row_number)
);
comment on table raw.pms_reservations is 'PMS reservation export: one file per business date with reservations created or cancelled that day. Dates dd/mm/yyyy, times WITA.';

create table if not exists raw.pms_night_audit (
    audit_date      text,
    hotel_code      text,
    rooms_available text,
    rooms_sold      text,
    room_rev        text,
    fb_rev          text,
    spa_rev         text,
    other_rev       text,
    _load_id        bigint      not null references raw.load_log (load_id),
    _source_file    text        not null,
    _row_number     integer     not null,
    _loaded_at      timestamptz not null default now(),
    primary key (_source_file, _row_number)
);
comment on table raw.pms_night_audit is 'PMS night audit: rooms and revenue per hotel per day. Amounts are text with thousand separators.';

create table if not exists raw.ota_bookings (
    record        jsonb       not null,
    _load_id      bigint      not null references raw.load_log (load_id),
    _source_file  text        not null,
    _row_number   integer     not null,
    _loaded_at    timestamptz not null default now(),
    primary key (_source_file, _row_number)
);
comment on table raw.ota_bookings is 'Channel manager report: one record per OTA booking event. Timestamps UTC.';

create table if not exists raw.reviews (
    record        jsonb       not null,
    _load_id      bigint      not null references raw.load_log (load_id),
    _source_file  text        not null,
    _row_number   integer     not null,
    _loaded_at    timestamptz not null default now(),
    primary key (_source_file, _row_number)
);
comment on table raw.reviews is 'Review aggregator feed: one record per review. Rating scale differs per platform. Timestamps UTC.';

create table if not exists raw.finance_targets (
    sheet_name    text        not null,
    record        jsonb       not null,
    _load_id      bigint      not null references raw.load_log (load_id),
    _source_file  text        not null,
    _row_number   integer     not null,
    _loaded_at    timestamptz not null default now(),
    primary key (_source_file, sheet_name, _row_number)
);
comment on table raw.finance_targets is 'Finance target workbook: one record per spreadsheet row below the header, keyed by column header. Includes the TOTAL row as received.';
