#!/bin/bash

# Development Environment Restart Script for SAFE-BMAD
# Restarts all services with options for selective restart

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

# Function to show service selection
show_service_menu() {
    echo "🔧 Select services to restart:"
    echo "============================="
    echo "1) All services"
    echo "2) Backend services (API, Database, Redis)"
    echo "3) Frontend only"
    echo "4) Database only"
    echo "5) Redis only"
    echo "6) API only"
    echo "7) Custom selection"
    echo ""
    read -p "Please select an option (1-7): " choice

    case $choice in
        1)
            SERVICES="postgres redis api ui pgadmin redis-commander"
            ;;
        2)
            SERVICES="postgres redis api"
            ;;
        3)
            SERVICES="ui"
            ;;
        4)
            SERVICES="postgres"
            ;;
        5)
            SERVICES="redis"
            ;;
        6)
            SERVICES="api"
            ;;
        7)
            echo "Available services: postgres redis api ui pgadmin redis-commander"
            read -p "Enter services to restart (space-separated): " SERVICES
            ;;
        *)
            print_error "Invalid selection. Restarting all services."
            SERVICES="postgres redis api ui pgadmin redis-commander"
            ;;
    esac

    echo "$SERVICES"
}

# Function to restart services
restart_services() {
    local services_to_restart="$1"
    local use_volumes="$2"

    if [ -z "$services_to_restart" ]; then
        services_to_restart="postgres redis api ui pgadmin redis-commander"
    fi

    print_status "Restarting services: $services_to_restart"

    if [ "$use_volumes" = "true" ]; then
        print_warning "This will also recreate volumes. Data may be lost!"
        read -p "Are you sure? (yes/no): " confirm
        if [ "$confirm" != "yes" ]; then
            print_error "Operation cancelled"
            exit 1
        fi
        docker-compose -f $COMPOSE_FILE down --volumes
        docker-compose -f $COMPOSE_FILE up -d $services_to_restart
    else
        # Restart specific services
        for service in $services_to_restart; do
            print_status "Restarting $service..."
            docker-compose -f $COMPOSE_FILE restart $service
        done
    fi

    print_success "Selected services restarted"
}

# Function to wait for critical services
wait_for_critical_services() {
    print_status "Waiting for critical services to be ready..."

    # Wait for PostgreSQL if it's being restarted
    if echo "$1" | grep -q "postgres"; then
        print_status "Waiting for PostgreSQL..."
        timeout 60 bash -c 'until docker-compose -f docker-compose.dev.yml exec -T postgres pg_isready -U safe_user -d safe_dev; do sleep 2; done'
    fi

    # Wait for Redis if it's being restarted
    if echo "$1" | grep -q "redis"; then
        print_status "Waiting for Redis..."
        timeout 30 bash -c 'until docker-compose -f docker-compose.dev.yml exec -T redis redis-cli ping; do sleep 1; done'
    fi

    # Wait for API if it's being restarted
    if echo "$1" | grep -q "api"; then
        print_status "Waiting for API service..."
        timeout 60 bash -c 'until curl -f http://localhost:8000/health > /dev/null 2>&1; do sleep 3; done'
    fi

    print_success "Critical services are ready"
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
}

# Function to run health checks
run_health_checks() {
    echo ""
    print_status "Running Health Checks:"
    echo "========================="

    # Check API health
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        print_success "API Health Check: ✅ OK"
    else
        print_warning "API Health Check: ⚠️ Not responding"
    fi

    # Check database connectivity
    if docker-compose -f $COMPOSE_FILE exec -T postgres pg_isready -U safe_user -d safe_dev > /dev/null 2>&1; then
        print_success "Database Health Check: ✅ OK"
    else
        print_warning "Database Health Check: ⚠️ Not ready"
    fi

    # Check Redis connectivity
    if docker-compose -f $COMPOSE_FILE exec -T redis redis-cli ping > /dev/null 2>&1; then
        print_success "Redis Health Check: ✅ OK"
    else
        print_warning "Redis Health Check: ⚠️ Not ready"
    fi
}

# Function to show restart options
show_options() {
    echo ""
    print_status "Additional Options:"
    echo "===================="
    echo "📊 View logs:        docker-compose -f $COMPOSE_FILE logs -f [service_name]"
    echo "🗄️  Database shell:  docker-compose -f $COMPOSE_FILE exec postgres psql -U safe_user -d safe_dev"
    echo "🗄️  Redis shell:     ./config/cache-cli.sh connect"
    echo "🧹 Clear cache:      ./config/flush-cache.sh"
    echo "🛑 Stop services:    ./config/dev-stop.sh"
}

# Main execution
main() {
    local restart_type="$1"
    local services=""

    echo ""
    echo "🔄 SAFE-BMAD Development Environment Restarter"
    echo "============================================"
    echo ""

    case $restart_type in
        --quick)
            print_status "Performing quick restart (no volume recreation)..."
            services="postgres redis api ui pgadmin redis-commander"
            restart_services "$services" "false"
            wait_for_critical_services "$services"
            ;;
        --hard)
            print_status "Performing hard restart (with volume recreation)..."
            services="postgres redis api ui pgadmin redis-commander"
            restart_services "$services" "true"
            wait_for_critical_services "$services"
            ;;
        --services)
            services=$(show_service_menu)
            restart_services "$services" "false"
            wait_for_critical_services "$services"
            ;;
        "")
            print_status "Performing full restart..."
            services="postgres redis api ui pgadmin redis-commander"
            restart_services "$services" "false"
            wait_for_critical_services "$services"
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use --help for available options"
            exit 1
            ;;
    esac

    show_status
    run_health_checks
    show_options

    echo ""
    print_success "Development environment restarted successfully! 🚀"
    echo ""
}

# Handle script arguments
case "${1:-}" in
    --quick)
        main --quick
        ;;
    --hard)
        main --hard
        ;;
    --services)
        main --services
        ;;
    --help|help|-h)
        echo "SAFE-BMAD Development Environment Restarter"
        echo ""
        echo "Usage: $0 [options]"
        echo ""
        echo "Options:"
        echo "  --quick         Restart all services quickly (preserve volumes)"
        echo "  --hard          Hard restart (recreate volumes - data loss possible)"
        echo "  --services      Interactive service selection"
        echo "  --help          Show this help message"
        echo ""
        echo "Examples:"
        echo "  $0              Restart all services"
        echo "  $0 --quick      Quick restart (preserve data)"
        echo "  $0 --hard       Hard restart (may lose data)"
        echo "  $0 --services   Select specific services to restart"
        ;;
    *)
        main
        ;;
esac