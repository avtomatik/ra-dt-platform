.PHONY: build up down logs

build:
	docker build -f docker/Dockerfile -t ra-ds-explorer:latest .

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f
