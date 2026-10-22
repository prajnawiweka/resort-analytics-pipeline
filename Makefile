# Load .env when present so Python and dbt see the same settings
ifneq (,$(wildcard .env))
include .env
export
endif

DBT = cd dbt && dbt
# Last business date to generate: yesterday by default, override with `make generate END=2026-10-21`
END ?= $(shell python -c "import datetime as d; print(d.date.today() - d.timedelta(days=1))")

.PHONY: install up down db-init lint test dbt-debug dbt-build dbt-docs generate load pipeline ci

install:            ## Install Python and dbt dependencies
	pip install -r requirements.txt

up:                 ## Start local Postgres and wait until healthy
	docker compose up -d --wait

down:               ## Stop local Postgres (data volume is kept)
	docker compose down

db-init:            ## Create schemas and raw tables
	python -m ingestion.init_db

lint:               ## Check Python style
	ruff check .
	ruff format --check .

test:               ## Run Python tests (needs a running database)
	python -m pytest -q

dbt-debug:          ## Check dbt can reach the database
	$(DBT) debug --profiles-dir .

dbt-build:          ## Load seeds, build staging and marts, run every dbt test
	$(DBT) seed --profiles-dir .
	$(DBT) build --profiles-dir .

dbt-docs:           ## Generate and serve dbt documentation with lineage graph
	$(DBT) docs generate --profiles-dir .
	$(DBT) docs serve --profiles-dir .

generate:           ## Write source files for every business date up to END
	python -m ingestion.generate --end $(END)

load:               ## Load new or changed source files into raw
	python -m ingestion.load

pipeline: db-init generate load dbt-build   ## Full run: source files, raw load, dbt

# CI uses two months of data so every model and test runs in about a minute
CI_END = 2025-02-28
ci: db-init lint test   ## Everything CI runs
	$(MAKE) generate END=$(CI_END)
	$(MAKE) load
	$(MAKE) dbt-debug
	$(MAKE) dbt-build
