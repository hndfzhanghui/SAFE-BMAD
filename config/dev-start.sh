#!/bin/bash

# Development Environment Startup Script for SAFE-BMAD
# Starts all services in the correct order with health checks

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.dev.yml"
PROJECT_NAME="safe-bmad"
LOG_LEVEL="info"

# Function to print colored output
print_status() {
    echo -e "${BLUE}🔄 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to check Docker
check_docker() {
    if ! docker --version > /dev/null 2>&1; then
        print_error "Docker is not installed or not running"
        exit 1
    fi

    if ! docker-compose --version > /dev/null 2>&1; then
        print_error "Docker Compose is not installed"
        exit 1
    fi

    print_success "Docker and Docker Compose are available"
}

# Function to create environment file if it doesn't exist
create_env_file() {
    if [ ! -f ".env" ]; then
        print_warning ".env file not found, creating from template..."
        if [ -f ".env.example" ]; then
            cp .env.example .env
            print_success "Created .env from .env.example"
            print_warning "Please review and update .env file with your settings"
        else
            print_error ".env.example file not found"
            exit 1
        fi
    fi
}

# Function to start services
start_services() {
    print_status "Starting SAFE-BMAD development environment..."

    # Create logs directory
    mkdir -p logs

    # Start services
    print_status "Starting Docker services..."
    docker-compose -f $COMPOSE_FILE up -d

    print_success "All services started"
}

# Function to wait for services to be healthy
wait_for_services() {
    print_status "Waiting for services to be healthy..."

    # Wait for PostgreSQL
    print_status "Waiting for PostgreSQL..."
    timeout 60 bash -c 'until docker-compose -f docker-compose.dev.yml exec -T postgres pg_isready -U safe_user -d safe_dev; do sleep 2; done'

    # Wait for Redis
    print_status "Waiting for Redis..."
    timeout 30 bash -c 'until docker-compose -f docker-compose.dev.yml exec -T redis redis-cli ping; do sleep 1; done'

    # Wait for API
    print_status "Waiting for API service..."
    timeout 60 bash -c 'until curl -f http://localhost:8000/health > /dev/null 2>&1; do sleep 3; done'

    print_success "All services are healthy and ready"
}

# Function to show service status
show_status() {
    echo ""
    print_status "Service Status:"
    echo "=================="
    docker-compose -f $COMPOSE_FILE ps

    echo ""
    print_status "Service URLs:"
    echo "==============="
    echo "🌐 API Service:      http://localhost:8000"
    echo "🌐 Frontend:         http://localhost:3000"
    echo "🗄️  Database Admin:   http://localhost:5050 (PgAdmin)"
    echo "🗄️  Redis Admin:      http://localhost:8081 (Redis Commander)"
    echo ""
    print_status "API Documentation:"
    echo "==================="
    echo "📚 Swagger UI:       http://localhost:8000/docs"
    echo "📚 ReDoc:            http://localhost:8000/redoc"
}

# Function to run database migrations
run_migrations() {
    print_status "Running database migrations..."

    # Check if there are migration files to run
    if [ -d "config/migrations" ] && [ "$(ls -A config/migrations/*.sql 2>/dev/null)" ]; then
        # Apply migrations
        for migration in config/migrations/*.sql; do
            if [ -f "$migration" ]; then
                print_status "Applying migration: $(basename $migration)"
                docker-compose -f $COMPOSE_FILE exec -T postgres psql -U safe_user -d safe_dev -f "/docker-entrypoint-initdb.d/$(basename $migration)"
            fi
        done
        print_success "Database migrations completed"
    else
        print_warning "No migration files found"
    fi
}

# Function to show helpful commands
show_help() {
    echo ""
    print_status "Useful Commands:"
    echo "=================="
    echo "📊 View logs:        docker-compose -f $COMPOSE_FILE logs -f [service_name]"
    echo "🛑 Stop services:    ./config/dev-stop.sh"
    echo "🔄 Restart services: ./config/dev-restart.sh"
    echo "🗄️  Database shell:  docker-compose -f $COMPOSE_FILE exec postgres psql -U safe_user -d safe_dev"
    echo "🗄️  Redis shell:     ./config/cache-cli.sh connect"
    echo "🧹 Clear cache:      ./config/flush-cache.sh"
    echo "💾 Backup database:  ./config/backup.sh"
    echo "📥 Restore database: ./config/restore.sh"
}

# Main execution
main() {
    echo ""
    echo "🚀 SAFE-BMAD Development Environment Starter"
    echo "=========================================="
    echo ""

    check_docker
    create_env_file
    start_services
    wait_for_services
    run_migrations
    show_status
    show_help

    echo ""
    print_success "Development environment is ready! 🎉"
    echo ""
}

# Handle script arguments
case "${1:-}" in
    --no-migrations)
        print_warning "Skipping database migrations"
        check_docker
        create_env_file
        start_services
        wait_for_services
        show_status
        show_help
        ;;
    --logs-only)
        print_status "Showing logs only..."
        docker-compose -f $COMPOSE_FILE logs -f
        ;;
    --help|help|-h)
        echo "SAFE-BMAD Development Environment Starter"
        echo ""
        echo "Usage: $0 [options]"
        echo ""
        echo "Options:"
        echo "  --no-migrations    Skip database migrations"
        echo "  --logs-only        Show logs only (don't start services)"
        echo "  --help             Show this help message"
        echo ""
        echo "Examples:"
        echo "  $0                 Start all services"
        echo "  $0 --no-migrations Start services without running migrations"
        echo "  $0 --logs-only     Show live logs"
        ;;
    "")
        main
        ;;
    *)
        print_error "Unknown option: $1"
        echo "Use --help for available options"
        exit 1
        ;;
esac