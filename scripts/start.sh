#!/bin/bash

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Helper functions
print_status() {
    echo -e "${BLUE}→${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}!${NC} $1"
}

# Check if ollama is installed
check_ollama() {
    if ! command -v ollama &> /dev/null; then
        print_error "Ollama not installed. Install from: https://ollama.ai"
        exit 1
    fi
    print_success "Ollama is installed"
}

# Start ollama on specified port
start_ollama_instance() {
    local port=$1
    local log_file="/tmp/ollama-${port}.log"
    
    # Check if already running
    if curl -s http://localhost:${port}/api/tags > /dev/null 2>&1; then
        print_success "Ollama on port ${port} is already running"
        return 0
    fi
    
    print_status "Starting Ollama on port ${port}..."
    OLLAMA_HOST=0.0.0.0:${port} OLLAMA_ORIGINS="*" nohup ollama serve > "${log_file}" 2>&1 &
    local ollama_pid=$!
    
    # Wait for ollama to be ready
    local max_attempts=30
    local attempt=0
    while [ $attempt -lt $max_attempts ]; do
        if curl -s http://localhost:${port}/api/tags > /dev/null 2>&1; then
            print_success "Ollama on port ${port} is ready (PID: ${ollama_pid})"
            return 0
        fi
        sleep 1
        attempt=$((attempt + 1))
    done
    
    print_error "Ollama on port ${port} failed to start"
    print_warning "Check logs at: ${log_file}"
    exit 1
}

# Pull models if needed
pull_models() {
    print_status "Checking for qwen3.6 model..."
    if ! ollama list 2>/dev/null | grep -q "qwen3.6"; then
        print_status "Pulling qwen3.6..."
        ollama pull qwen3.6
    else
        print_success "qwen3.6 already available"
    fi
    
    print_status "Checking for gemma4 model..."
    if ! ollama list 2>/dev/null | grep -q "gemma4"; then
        print_status "Pulling gemma4..."
        ollama pull gemma4
    else
        print_success "gemma4 already available"
    fi
}

# Stop all ollama instances
stop_ollama() {
    print_status "Stopping Ollama instances..."
    pkill -f "ollama serve" 2>/dev/null || true
    sleep 2
    print_success "Ollama instances stopped"
}

# Main script
main() {
    case "${1:-help}" in
        start)
            print_status "Starting Job Search application..."
            echo ""
            
            check_ollama
            pull_models
            echo ""
            
            start_ollama_instance 11434
            start_ollama_instance 11435
            echo ""
            
            print_status "Starting Docker Compose..."
            docker compose up --build -d
            sleep 5
            
            echo ""
            print_success "Application started!"
            echo ""
            echo "URLs:"
            echo "  Frontend:  http://localhost:3000"
            echo "  Backend:   http://localhost:8000"
            echo ""
            echo "Ollama instances:"
            echo "  qwen3.6 (port 11434):  http://localhost:11434"
            echo "  gemma4 (port 11435):   http://localhost:11435"
            echo ""
            echo "Check logs: make logs"
            echo "Check health: make health"
            ;;
        
        stop)
            print_status "Stopping application..."
            docker compose down
            stop_ollama
            print_success "Application stopped"
            ;;
        
        restart)
            $0 stop
            sleep 2
            $0 start
            ;;
        
        ollama-start)
            check_ollama
            start_ollama_instance 11434
            start_ollama_instance 11435
            ;;
        
        ollama-stop)
            stop_ollama
            ;;
        
        ollama-pull)
            check_ollama
            pull_models
            ;;
        
        *)
            echo "Usage: $0 {start|stop|restart|ollama-start|ollama-stop|ollama-pull}"
            exit 1
            ;;
    esac
}

main "$@"
