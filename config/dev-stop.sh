#!/bin/bash

# Development Environment Stop Script for SAFE-BMAD
# Gracefully stops all services and performs cleanup

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

# Function to stop services
stop_services() {
    print_status "Stopping SAFE-BMAD development environment..."

    if docker-compose -f $COMPOSE_FILE ps -q | grep -q .; then
        print_status "Stopping Docker services..."
        docker-compose -f $COMPOSE_FILE down
        print_success "All services stopped"
    else
        print_warning "No services are currently running"
    fi
}

# Function to clean up (optional)
cleanup_resources() {
    if [ "$1" = "--cleanup" ]; then
        print_status "Cleaning up Docker resources..."

        # Remove stopped containers
        docker container prune -f > /dev/null 2>&1

        # Remove unused images (only those created by this project)
        docker image prune -f > /dev/null 2>&1

        print_success "Cleanup completed"
    fi
}

# Function to show final status
show_status() {
    echo ""
    print_status "Final Status:"
    echo "============="

    # Check if any containers are still running
    running_containers=$(docker ps --filter "name=safe-bmad" --format "table {{.Names}}\t{{.Status}}" | grep -v NAMES || true)

    if [ -n "$running_containers" ]; then
        echo "🟡 Still running containers:"
        echo "$running_containers"
        echo ""
        print_warning "Some containers may still be running"
    else
        print_success "All SAFE-BMAD containers are stopped"
    fi

    # Show Docker stats
    echo ""
    print_status "Docker Resource Usage:"
    docker system df --format "table {{.Type}}\t{{.TotalCount}}\t{{.Size}}" | head -4
}

# Function to show restart options
show_restart_options() {
    echo ""
    print_status "Restart Options:"
    echo "=================="
    echo "🚀 Start services:   ./config/dev-start.sh"
    echo "🔄 Restart services: ./config/dev-restart.sh"
    echo "🗄️  Access database:  docker-compose -f $COMPOSE_FILE exec postgres psql -U safe_user -d safe_dev"
    echo "🗄️  Access Redis:     ./config/cache-cli.sh connect"
}

# Main execution
main() {
    echo ""
    echo "🛑 SAFE-BMAD Development Environment Stopper"
    echo "=========================================="
    echo ""

    stop_services
    cleanup_resources "$1"
    show_status
    show_restart_options

    echo ""
    print_success "Development environment stopped successfully! 👋"
    echo ""
}

# Handle script arguments
case "${1:-}" in
    --cleanup)
        main --cleanup
        ;;
    --force)
        print_status "Force stopping all services..."
        docker-compose -f $COMPOSE_FILE kill
        docker-compose -f $COMPOSE_FILE down --remove-orphans
        print_success "Force stop completed"
        ;;
    --help|help|-h)
        echo "SAFE-BMAD Development Environment Stopper"
        echo ""
        echo "Usage: $0 [options]"
        echo ""
        echo "Options:"
        echo "  --cleanup    Remove unused Docker resources after stopping"
        echo "  --force      Force stop all services immediately"
        echo "  --help       Show this help message"
        echo ""
        echo "Examples:"
        echo "  $0                Stop all services"
        echo "  $0 --cleanup      Stop services and clean up resources"
        echo "  $0 --force        Force stop all services"
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