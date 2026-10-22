# Load .env when present so Python and dbt see the same settings
ifneq (,$(wildcard .env))
include .env
export
endif

DBT = cd dbt && dbt

.PHONY: install up down db-init lint test dbt-debug ci

install:            ## Install Python and dbt dependencies
	pip install -r requirements.txt

up:                 ## Start local Postgres and wait until healthy
	docker compose up -d --wait

down:               ## Stop local Postgres (data volume is kept)
	docker compose down

db-init:            ## Create schemas raw, staging, marts
	python -m ingestion.init_db

lint:               ## Check Python style
	ruff check .
	ruff format --check .

test:               ## Run Python tests (needs a running database)
	python -m pytest -q

dbt-debug:          ## Check dbt can reach the database
	$(DBT) debug --profiles-dir .

ci: db-init lint test dbt-debug   ## Everything CI runs
