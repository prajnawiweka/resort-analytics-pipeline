# Load .env when present so Python and dbt see the same settings
ifneq (,$(wildcard .env))
include .env
export
endif

DBT = cd dbt && dbt
# Last business date to generate: yesterday by default, override with `make generate END=2026-10-21`
END ?= $(shell python -c "import datetime as d; print(d.date.today() - d.timedelta(days=1))")

.PHONY: install up down db-init lint test dbt-debug generate load pipeline ci

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

generate:           ## Write source files for every business date up to END
	python -m ingestion.generate --end $(END)

load:               ## Load new or changed source files into raw
	python -m ingestion.load

pipeline: db-init generate load   ## Full run: schemas, source files, raw load

ci: db-init lint test dbt-debug   ## Everything CI runs
