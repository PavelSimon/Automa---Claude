#!/bin/bash

# run.sh - Spustenie Automa backendu a frontendu s LAN prístupom
# Usage: ./run.sh [backend|frontend|both]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKEND_HOST="0.0.0.0"  # Listen on all interfaces for LAN access
BACKEND_PORT="8001"
FRONTEND_HOST="0.0.0.0"  # Listen on all interfaces for LAN access
FRONTEND_PORT="8002"

# Get local IP address for display
LOCAL_IP=$(hostname -I | awk '{print $1}')

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_banner() {
    echo -e "${GREEN}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                        AUTOMA LAUNCHER                      ║"
    echo "║              Python Agent Management Platform               ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

check_requirements() {
    print_info "Checking requirements..."

    # Check if uv is installed
    if ! command -v uv &> /dev/null; then
        print_error "uv is not installed. Please install uv first:"
        echo "curl -LsSf https://astral.sh/uv/install.sh | sh"
        exit 1
    fi

    # Check if node is installed (for frontend)
    if [[ "$1" == "frontend" || "$1" == "both" ]]; then
        if ! command -v node &> /dev/null; then
            print_error "Node.js is not installed. Please install Node.js first."
            exit 1
        fi

        if ! command -v npm &> /dev/null; then
            print_error "npm is not installed. Please install npm first."
            exit 1
        fi
    fi

    print_success "Requirements check passed"
}

setup_backend() {
    print_info "Setting up backend..."

    # Create required directories
    mkdir -p data scripts

    # Install dependencies if needed
    if [ ! -d ".venv" ]; then
        print_info "Creating virtual environment..."
        uv venv
    fi

    print_info "Installing/updating dependencies..."
    uv sync

    print_success "Backend setup completed"
}

setup_frontend() {
    print_info "Setting up frontend..."

    cd frontend

    # Install dependencies if node_modules doesn't exist
    if [ ! -d "node_modules" ]; then
        print_info "Installing frontend dependencies..."
        npm install
    fi

    cd ..

    print_success "Frontend setup completed"
}

start_backend() {
    print_info "Starting backend server..."
    print_info "Backend will be accessible at:"
    echo -e "  ${GREEN}Local:${NC}   http://localhost:${BACKEND_PORT}"
    echo -e "  ${GREEN}Network:${NC} http://${LOCAL_IP}:${BACKEND_PORT}"
    echo -e "  ${GREEN}API:${NC}     http://${LOCAL_IP}:${BACKEND_PORT}/docs"
    echo ""

    # Start backend with LAN access
    uv run uvicorn backend.app.main:app --reload --host ${BACKEND_HOST} --port ${BACKEND_PORT}
}

start_frontend() {
    print_info "Starting frontend server..."
    print_info "Frontend will be accessible at:"
    echo -e "  ${GREEN}Local:${NC}   http://localhost:${FRONTEND_PORT}"
    echo -e "  ${GREEN}Network:${NC} http://${LOCAL_IP}:${FRONTEND_PORT}"
    echo ""

    cd frontend

    # Start frontend with LAN access
    npm run dev -- --host ${FRONTEND_HOST} --port ${FRONTEND_PORT}
}

start_both() {
    print_info "Starting both backend and frontend..."
    print_info "Services will be accessible at:"
    echo -e "  ${GREEN}Frontend:${NC} http://${LOCAL_IP}:${FRONTEND_PORT}"
    echo -e "  ${GREEN}Backend:${NC}  http://${LOCAL_IP}:${BACKEND_PORT}"
    echo -e "  ${GREEN}API Docs:${NC} http://${LOCAL_IP}:${BACKEND_PORT}/docs"
    echo ""

    # Start backend in background
    print_info "Starting backend in background..."
    uv run uvicorn backend.app.main:app --reload --host ${BACKEND_HOST} --port ${BACKEND_PORT} &
    BACKEND_PID=$!

    # Wait a moment for backend to start
    sleep 3

    # Start frontend in foreground
    print_info "Starting frontend..."
    cd frontend
    npm run dev -- --host ${FRONTEND_HOST} --port ${FRONTEND_PORT} &
    FRONTEND_PID=$!

    # Setup trap to kill both processes on exit
    trap "print_info 'Stopping services...' && kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT

    print_success "Both services started successfully!"
    print_info "Press Ctrl+C to stop both services"

    # Wait for frontend process
    wait $FRONTEND_PID
}

show_usage() {
    echo "Usage: $0 [backend|frontend|both]"
    echo ""
    echo "Commands:"
    echo "  backend   - Start only the backend server (FastAPI)"
    echo "  frontend  - Start only the frontend server (Vue.js)"
    echo "  both      - Start both backend and frontend servers"
    echo ""
    echo "If no command is specified, 'both' is used as default."
    echo ""
    echo "Network Access:"
    echo "  Backend:  http://${LOCAL_IP}:${BACKEND_PORT}"
    echo "  Frontend: http://${LOCAL_IP}:${FRONTEND_PORT}"
    echo "  API Docs: http://${LOCAL_IP}:${BACKEND_PORT}/docs"
}

# Main script logic
MODE=${1:-both}

case $MODE in
    "backend")
        print_banner
        check_requirements "backend"
        setup_backend
        start_backend
        ;;
    "frontend")
        print_banner
        check_requirements "frontend"
        setup_frontend
        start_frontend
        ;;
    "both")
        print_banner
        check_requirements "both"
        setup_backend
        setup_frontend
        start_both
        ;;
    "help"|"-h"|"--help")
        print_banner
        show_usage
        ;;
    *)
        print_error "Invalid command: $MODE"
        echo ""
        show_usage
        exit 1
        ;;
esac