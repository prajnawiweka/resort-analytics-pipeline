-- Database layers. Safe to run more than once.
--   raw      : data exactly as received from each source, never edited
--   staging  : cleaned and conformed (built by dbt)
--   marts    : star schema and KPIs read by the dashboards (built by dbt)

create schema if not exists raw;
create schema if not exists staging;
create schema if not exists marts;

comment on schema raw is 'Source data as received. Loaded by ingestion/load.py. Never transformed in place.';
comment on schema staging is 'Cleaned, typed and key-mapped source data. Built by dbt.';
comment on schema marts is 'Fact and dimension tables for BI. Built by dbt. The only schema dashboards may read.';
