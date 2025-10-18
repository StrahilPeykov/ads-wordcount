.PHONY: help build up down logs clean test test-lb ps stats

help:
	@echo "Word Count Service - Available Commands"
	@echo "========================================"
	@echo "make build       - Build Docker image"
	@echo "make up          - Start all services"
	@echo "make down        - Stop all services"
	@echo "make logs        - View logs (all services)"
	@echo "make logs-server - View server logs"
	@echo "make logs-client - View client logs"
	@echo "make logs-lb     - View load balancer logs"
	@echo "make clean       - Clean up Docker resources"
	@echo "make test        - Run standard client test"
	@echo "make test-lb     - Run load balancer algorithm test"
	@echo "make ps          - Show running containers"
	@echo "make stats       - Show container stats"
	@echo ""
	@echo "Phase 3 - Testing Different Algorithms:"
	@echo "make test-round-robin      - Test with Round Robin"
	@echo "make test-least-conn       - Test with Least Connections"
	@echo ""
	@echo "Cache Management:"
	@echo "make clear-cache           - Clear Redis cache"
	@echo "make test-with-clear       - Clear cache and run test"
	@echo "make compare-cache         - Compare performance with/without cache"

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
	docker-compose logs -f server1 server2 server3

logs-client:
	docker-compose logs -f client

logs-redis:
	docker-compose logs -f redis

logs-lb:
	docker-compose logs -f load_balancer

clean:
	docker-compose down -v
	docker image prune -f
	docker network prune -f

ps:
	docker ps -a

stats:
	docker stats --no-stream

rebuild:
	docker-compose down
	docker-compose build --no-cache
	docker-compose up

test:
	docker-compose run --rm client python /app/client/client.py

test-lb:
	docker-compose run --rm client python /app/client/test_load_balancer.py

test-round-robin:
	@echo "Testing Round Robin Algorithm..."
	@docker-compose down
	@LB_ALGORITHM=round_robin docker-compose up -d
	@sleep 5
	@docker-compose run --rm client python /app/client/test_load_balancer.py

test-least-conn:
	@echo "Testing Least Connections Algorithm..."
	@docker-compose down
	@LB_ALGORITHM=least_connections docker-compose up -d
	@sleep 5
	@docker-compose run --rm client python /app/client/test_load_balancer.py

clear-cache:
	@echo "Clearing Redis cache..."
	@docker-compose exec -T redis redis-cli FLUSHALL
	@echo "✓ Cache cleared!"

test-with-clear:
	@echo "Clearing cache and running test..."
	@docker-compose exec -T redis redis-cli FLUSHALL
	@echo "✓ Cache cleared, running test..."
	@sleep 1
	@docker-compose run --rm client python /app/client/test_load_balancer.py
