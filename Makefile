.PHONY: help start stop restart logs ollama-pull ollama-start ollama-stop health docker-start docker-stop

help:
	@echo "Job Search App - Available Commands:"
	@echo ""
	@echo "  make start          - Start the full application (ollama + docker compose)"
	@echo "  make stop           - Stop all services"
	@echo "  make restart        - Restart all services"
	@echo "  make logs           - View docker compose logs"
	@echo "  make ollama-pull    - Pull qwen3.6 and gemma4 models"
	@echo "  make ollama-start   - Start ollama instances on ports 11434 & 11435"
	@echo "  make ollama-stop    - Stop ollama instances"
	@echo "  make docker-start   - Start docker compose services only"
	@echo "  make docker-stop    - Stop docker compose services only"
	@echo "  make health         - Check health of all services"

# Main startup - delegated to script
start:
	@./scripts/start.sh start

# Stop all services
stop:
	@./scripts/start.sh stop

# Restart all services
restart:
	@./scripts/start.sh restart

# Ollama commands
ollama-pull:
	@./scripts/start.sh ollama-pull

ollama-start:
	@./scripts/start.sh ollama-start

ollama-stop:
	@./scripts/start.sh ollama-stop

# Docker compose commands
docker-start:
	@echo "Starting docker compose..."
	docker compose up --build -d
	@echo "Waiting for services to be healthy..."
	@sleep 5

docker-stop:
	@echo "Stopping docker compose..."
	docker compose down

# Logs
logs:
	docker compose logs -f

# Health check
health:
	@echo "Checking service health..."
	@echo ""
	@echo "Backend health:"
	@curl -s http://localhost:8000/health | python3 -m json.tool || echo "❌ Backend unreachable"
	@echo ""
	@echo "Ollama (qwen:11434):"
	@curl -s http://localhost:11434/api/tags | python3 -m json.tool | head -20 || echo "❌ Ollama 11434 unreachable"
	@echo ""
	@echo "Ollama (gemma:11435):"
	@curl -s http://localhost:11435/api/tags | python3 -m json.tool | head -20 || echo "❌ Ollama 11435 unreachable"
	@echo ""
	@echo "Frontend: http://localhost:3000"
	@echo "Backend:  http://localhost:8000"
