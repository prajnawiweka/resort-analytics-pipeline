-- One-time setup on Neon (or any hosted Postgres). Run in the Neon SQL Editor as the project
-- owner (neondb_owner), AFTER creating the roles pipeline_rw and looker_ro in the Neon console.
-- Not part of `make db-init`: the pipeline role must not be able to create or change roles.
--
--   pipeline_rw : used by GitHub Actions; owns and rebuilds every schema
--   looker_ro   : used by Looker Studio / Power BI; may only read the marts schema

-- The pipeline owns the data layers so it can create and replace tables
create schema if not exists raw       authorization pipeline_rw;
create schema if not exists staging   authorization pipeline_rw;
create schema if not exists marts     authorization pipeline_rw;
create schema if not exists reference authorization pipeline_rw;

-- The BI reader sees only the marts, including tables dbt recreates on every run
grant usage on schema marts to looker_ro;
grant select on all tables in schema marts to looker_ro;
alter default privileges for role pipeline_rw in schema marts grant select on tables to looker_ro;

-- Nothing else is visible to the BI reader
revoke all on schema raw, staging, reference from looker_ro;
revoke create on schema public from looker_ro;
