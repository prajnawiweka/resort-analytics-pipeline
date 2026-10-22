-- One-time setup on Neon. Run in the Neon SQL Editor, database "resort", as the project owner
-- (neondb_owner, the editor's default).
--
-- Roles are created HERE with SQL, not in the Console's Roles page: Neon gives every role made
-- in the Console membership of neon_superuser, which would let the BI reader see everything.
--
-- Before running: replace the two passwords below in the editor (at least 12 characters,
-- mixing upper/lower case, digits and symbols). Do not save the real passwords in this file.
--
--   pipeline_rw : used by GitHub Actions; owns and rebuilds every schema
--   looker_ro   : used by Looker Studio / Power BI; may only read the marts schema

create role pipeline_rw login password 'REPLACE-pipeline-password';
create role looker_ro   login password 'REPLACE-looker-password';

-- Let the owner act for pipeline_rw, needed to hand it the schemas below
grant pipeline_rw to current_user;

grant connect on database resort to pipeline_rw, looker_ro;
-- Python and dbt run "create schema if not exists", which checks this privilege even when
-- the schema already exists
grant create on database resort to pipeline_rw;

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

-- Check: expect pipeline_rw and looker_ro, both with is_neon_superuser = false
select r.rolname,
       pg_has_role(r.rolname, 'neon_superuser', 'member') as is_neon_superuser
from pg_roles r
where r.rolname in ('pipeline_rw', 'looker_ro');
