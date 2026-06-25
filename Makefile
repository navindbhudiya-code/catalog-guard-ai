.DEFAULT_GOAL := help
PY := .venv/bin/python
PIP := .venv/bin/pip

.PHONY: help install verify lint type compile imports test audit trace up down clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
	  awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

install: ## Create venv deps (dev + core)
	$(PY) -m pip install -q --upgrade pip
	$(PIP) install -q -e ".[dev]"

lint: ## ruff lint + format check
	$(PY) -m ruff check src tests evals
	$(PY) -m ruff format --check src tests evals

type: ## mypy --strict on core
	$(PY) -m mypy

compile: ## byte-compile sanity (the "compilated" gate)
	$(PY) -m compileall -q src evals

imports: ## import-layering contract
	.venv/bin/lint-imports

test: ## run tests with 100% core coverage gate
	$(PY) -m pytest --cov --cov-report=term-missing

trace: ## assert every requirement in TRACEABILITY.md has a test
	$(PY) -m catalogguard.tools.trace_check

verify: lint type compile imports test trace ## full build gate (run before every commit)
	@echo "✅ verify passed — build is green, traceable, and 100% core-covered."

audit: ## run a catalog audit (see CLAUDE.md for flags)
	$(PY) -m catalogguard audit $(ARGS)

up: ## start docker stack (python svc + chromadb)
	docker compose -f docker/docker-compose.yml up -d

down: ## stop docker stack
	docker compose -f docker/docker-compose.yml down

clean: ## remove caches and runtime artifacts
	rm -rf .mypy_cache .ruff_cache .pytest_cache htmlcov .coverage
	find . -path ./.venv -prune -o -name __pycache__ -exec rm -rf {} +
