.PHONY: help build up down logs clean test

help:
	@echo "Word Count Service - Available Commands"
	@echo "========================================"
	@echo "make build      - Build Docker image"
	@echo "make up         - Start all services"
	@echo "make down       - Stop all services"
	@echo "make logs       - View logs (all services)"
	@echo "make logs-server - View server logs"
	@echo "make logs-client - View client logs"
	@echo "make clean      - Clean up Docker resources"
	@echo "make test       - Run test client"
	@echo "make ps         - Show running containers"

build:
	docker build --pull -t ads:lab .

up:
	docker-compose up

up-detached:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

logs-server:
	docker-compose logs -f server

logs-client:
	docker-compose logs -f client

logs-redis:
	docker-compose logs -f redis

clean:
	docker-compose down -v
	docker image prune -f
	docker network prune -f

ps:
	docker ps -a

rebuild:
	docker-compose down
	docker-compose build --no-cache
	docker-compose up

test:
	docker-compose run --rm client python /app/client/client.py