.PHONY: up down build logs clean setup

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
	npm install --prefix dashboard --legacy-peer-deps
