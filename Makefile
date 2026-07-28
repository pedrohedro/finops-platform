PYTHON ?= python3
PNPM ?= corepack pnpm

.PHONY: up down build logs clean setup test test-smoke smoke

up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f

clean:
	docker compose down -v
	rm -rf dashboard/.next dashboard/node_modules
	find . -type d -name "__pycache__" -exec rm -rf {} +

setup:
	cp .env.example .env || true
	$(PNPM) --dir dashboard install --frozen-lockfile

test:
	$(PYTHON) -m pytest api collector normalizer forecast -q
	$(PNPM) --dir dashboard install --frozen-lockfile
	$(PNPM) --dir dashboard build
	./scripts/test_smoke.sh

test-smoke:
	./scripts/test_smoke.sh

smoke:
	./scripts/smoke.sh
