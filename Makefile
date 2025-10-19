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
	@echo ""
	@echo "Phase 3 - Testing Different Algorithms:"
	@echo "make test-round-robin      - Test with Round Robin (5 clients)"
	@echo "make test-least-conn       - Test with Least Connections (5 clients)"
	@echo ""
	@echo "Phase 4 - Fault Tolerance Testing:"
	@echo "make test-fault-tolerance  - Interactive fault tolerance test"
	@echo "make stop-server SERVER=1  - Stop a specific server (1, 2, or 3)"
	@echo "make start-server SERVER=1 - Start a specific server (1, 2, or 3)"
	@echo "make server-status         - Show status of all servers"
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
	docker-compose logs -f client1 client2 client3 client4 client5

logs-client1:
	docker-compose logs -f client1

logs-client2:
	docker-compose logs -f client2

logs-client3:
	docker-compose logs -f client3

logs-client4:
	docker-compose logs -f client4

logs-client5:
	docker-compose logs -f client5

logs-redis:
	docker-compose logs -f redis

logs-lb:
	docker-compose logs -f load_balancer

clean:
	docker-compose down -v
	docker image prune -f
	docker network prune -f

rebuild:
	docker-compose down
	docker-compose build --no-cache
	docker-compose up

test:
	docker-compose exec client1 python /app/client/client.py

test-lb:
	@echo "Running test with 5 concurrent clients..."
	@docker-compose exec -T client1 python /app/client/test_load_balancer.py & \
	docker-compose exec -T client2 python /app/client/test_load_balancer.py & \
	docker-compose exec -T client3 python /app/client/test_load_balancer.py & \
	docker-compose exec -T client4 python /app/client/test_load_balancer.py & \
	docker-compose exec -T client5 python /app/client/test_load_balancer.py & \
	wait

test-round-robin:
	@docker-compose down
	@LB_ALGORITHM=round_robin docker-compose up -d
	@sleep 5
	@make test-lb

test-least-conn:
	@docker-compose down
	@LB_ALGORITHM=least_connections docker-compose up -d
	@sleep 5
	@make test-lb

clear-cache:
	@docker-compose exec -T redis redis-cli FLUSHALL

test-with-clear:
	@echo "Ensuring services are running..."
	@docker-compose up -d
	@sleep 2
	@echo "Clearing cache..."
	@docker-compose exec -T redis redis-cli FLUSHALL

clear-cache-only:
	@echo "Clearing cache without restarting containers..."
	@docker-compose exec -T redis redis-cli FLUSHALL
	@sleep 1
	@make test-lb

# Phase 4: Fault Tolerance Testing
test-fault-tolerance:
	@echo "Starting fault tolerance test..."
	@docker-compose up -d
	@sleep 3
	@sleep 2
	@echo "Clearing cache..."
	@docker-compose exec -T redis redis-cli FLUSHALL
	@sleep 1
	@docker-compose exec -T client1 python /app/client/test_fault_tolerance.py

stop-server:
	@if [ -z "$(SERVER)" ]; then \
		echo "Error: Please specify SERVER number (1, 2, or 3)"; \
		echo "Usage: make stop-server SERVER=2"; \
		exit 1; \
	fi
	@echo "Stopping server$(SERVER)..."
	@docker stop word_count_server$(SERVER)
	@echo "Server$(SERVER) stopped. Wait 5 seconds for load balancer to detect..."

start-server:
	@if [ -z "$(SERVER)" ]; then \
		echo "Error: Please specify SERVER number (1, 2, or 3)"; \
		echo "Usage: make start-server SERVER=2"; \
		exit 1; \
	fi
	@echo "Starting server$(SERVER)..."
	@docker start word_count_server$(SERVER)
	@echo "Server$(SERVER) started. Wait 5 seconds for load balancer to detect..."

server-status:
	@echo "Server Status:"
	@echo "=============="
	@docker ps --filter "name=word_count_server" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

ps:
	docker ps -a

stats:
	docker stats --no-stream

