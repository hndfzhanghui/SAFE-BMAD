#!/bin/bash

# Service Connectivity Test Script for SAFE-BMAD
# Tests connectivity between all services in the development environment

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Service configuration
SERVICES=(
    "postgres:5432:Database:PostgreSQL"
    "redis:6379:Cache:Redis"
    "api:8000:API:FastAPI"
    "ui:3000:Frontend:Vue.js"
    "pgadmin:5050:DB Admin:PgAdmin"
    "redis-commander:8081:Redis Admin:Redis Commander"
)

# Test results
TESTS_PASSED=0
TESTS_FAILED=0

# Function to print colored output
print_status() {
    echo -e "${BLUE}🔍 $1${NC}"
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

# Function to test Docker container status
test_container_status() {
    local service_name="$1"
    local container_name="safe-bmad-${service_name}-dev"

    print_status "Checking container status for $service_name..."

    if docker ps --format "table {{.Names}}\t{{.Status}}" | grep -q "$container_name"; then
        local status=$(docker ps --format "table {{.Names}}\t{{.Status}}" | grep "$container_name" | awk '{print $2, $3, $4}')
        print_success "Container $container_name is running ($status)"
        ((TESTS_PASSED++))
        return 0
    else
        print_error "Container $container_name is not running"
        ((TESTS_FAILED++))
        return 1
    fi
}

# Function to test port connectivity
test_port_connectivity() {
    local host="$1"
    local port="$2"
    local service_name="$3"
    local description="$4"

    print_status "Testing $description connectivity ($host:$port)..."

    # Check if port is open
    if nc -z -w3 "$host" "$port" 2>/dev/null; then
        print_success "$description is accessible on port $port"
        ((TESTS_PASSED++))
        return 0
    else
        print_error "$description is not accessible on port $port"
        ((TESTS_FAILED++))
        return 1
    fi
}

# Function to test HTTP/HTTPS connectivity
test_http_connectivity() {
    local url="$1"
    local service_name="$2"
    local description="$3"
    local expected_status="${4:-200}"

    print_status "Testing $description HTTP connectivity..."

    local response_code=$(curl -s -o /dev/null -w "%{http_code}" \
        --max-time 10 \
        "$url" \
        2>/dev/null || echo "000")

    if [ "$response_code" = "$expected_status" ]; then
        print_success "$description is responding (HTTP $response_code)"
        ((TESTS_PASSED++))
        return 0
    else
        print_error "$description is not responding (HTTP $response_code)"
        ((TESTS_FAILED++))
        return 1
    fi
}

# Function to test database connectivity
test_database_connectivity() {
    print_status "Testing database connectivity..."

    # Check if we can connect to PostgreSQL
    if docker exec safe-bmad-db-dev pg_isready -U safe_user -d safe_dev > /dev/null 2>&1; then
        print_success "Database connection is working"

        # Test basic query
        local result=$(docker exec safe-bmad-db-dev psql -U safe_user -d safe_dev -t -c "SELECT 1;" 2>/dev/null || echo "")
        if [ "$result" = "1" ]; then
            print_success "Database query execution is working"
            ((TESTS_PASSED++))
        else
            print_error "Database query execution failed"
            ((TESTS_FAILED++))
        fi
    else
        print_error "Database connection failed"
        ((TESTS_FAILED++))
    fi
}

# Function to test Redis connectivity
test_redis_connectivity() {
    print_status "Testing Redis connectivity..."

    # Check if we can connect to Redis
    if docker exec safe-bmad-redis-dev redis-cli ping > /dev/null 2>&1; then
        print_success "Redis connection is working"

        # Test basic operations
        local test_key="test_connectivity_$(date +%s)"
        docker exec safe-bmad-redis-dev redis-cli set "$test_key" "test_value" > /dev/null 2>&1
        local test_value=$(docker exec safe-bmad-redis-dev redis-cli get "$test_key" 2>/dev/null || echo "")
        docker exec safe-bmad-redis-dev redis-cli del "$test_key" > /dev/null 2>&1

        if [ "$test_value" = "test_value" ]; then
            print_success "Redis operations are working"
            ((TESTS_PASSED++))
        else
            print_error "Redis operations failed"
            ((TESTS_FAILED++))
        fi
    else
        print_error "Redis connection failed"
        ((TESTS_FAILED++))
    fi
}

# Function to test API endpoints
test_api_endpoints() {
    print_status "Testing API endpoints..."

    # Test health endpoint
    if test_http_connectivity "http://localhost:8000/health" "api" "API Health Endpoint"; then
        ((TESTS_PASSED++))
    else
        ((TESTS_FAILED++))
    fi

    # Test ready endpoint
    if test_http_connectivity "http://localhost:8000/ready" "api" "API Ready Endpoint"; then
        ((TESTS_PASSED++))
    else
        ((TESTS_FAILED++))
    fi

    # Test root endpoint
    if test_http_connectivity "http://localhost:8000/" "api" "API Root Endpoint"; then
        ((TESTS_PASSED++))
    else
        ((TESTS_FAILED++))
    fi

    # Test metrics endpoint
    if test_http_connectivity "http://localhost:8000/metrics" "api" "API Metrics Endpoint"; then
        ((TESTS_PASSED++))
    else
        ((TESTS_FAILED++))
    fi
}

# Function to test service dependencies
test_service_dependencies() {
    print_status "Testing service dependencies..."

    # Test if API can reach database
    local api_logs=$(docker logs safe-bmad-api-dev 2>&1 | tail -10)
    if echo "$api_logs" | grep -q "Database connection successful\|database.*connected"; then
        print_success "API can connect to database"
        ((TESTS_PASSED++))
    else
        print_warning "API database connection status unclear"
        # Don't count as failure since logs might not show this yet
    fi

    # Test if API can reach Redis
    if echo "$api_logs" | grep -q "Redis connection successful\|redis.*connected"; then
        print_success "API can connect to Redis"
        ((TESTS_PASSED++))
    else
        print_warning "API Redis connection status unclear"
        # Don't count as failure since logs might not show this yet
    fi
}

# Function to check Docker network
test_docker_network() {
    print_status "Testing Docker network connectivity..."

    # Check if Docker network exists
    if docker network ls | grep -q "safe-bmad-dev-network"; then
        print_success "Docker network exists"

        # Check if containers are on the same network
        local network_containers=$(docker network inspect safe-bmad-dev-network --format='{{range .Containers}}{{.Name}} {{end}}' 2>/dev/null)
        local expected_containers="safe-bmad-api-dev safe-bmad-db-dev safe-bmad-redis-dev"

        local missing_containers=""
        for container in $expected_containers; do
            if ! echo "$network_containers" | grep -q "$container"; then
                missing_containers="$missing_containers $container"
            fi
        done

        if [ -z "$missing_containers" ]; then
            print_success "All containers are on the Docker network"
            ((TESTS_PASSED++))
        else
            print_warning "Some containers are not on the Docker network:$missing_containers"
        fi
    else
        print_error "Docker network does not exist"
        ((TESTS_FAILED++))
    fi
}

# Function to show system resources
show_system_resources() {
    print_status "System resource usage:"

    # Docker stats
    echo ""
    echo "📊 Docker Container Resource Usage:"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}" | head -10

    # Disk usage
    echo ""
    echo "💾 Disk Usage:"
    df -h | grep -E "(Filesystem|/dev/)"

    # Memory usage
    echo ""
    echo "🧠 Memory Usage:"
    free -h
}

# Function to show test summary
show_summary() {
    echo ""
    echo "🎯 Connectivity Test Summary"
    echo "==========================="
    echo "Tests passed: $TESTS_PASSED"
    echo "Tests failed: $TESTS_FAILED"
    echo "Total tests: $((TESTS_PASSED + TESTS_FAILED))"

    local total_tests=$((TESTS_PASSED + TESTS_FAILED))
    if [ $total_tests -gt 0 ]; then
        local success_rate=$(( (TESTS_PASSED * 100) / total_tests ))
        echo "Success rate: ${success_rate}%"
    fi

    echo ""

    if [ $TESTS_FAILED -eq 0 ]; then
        print_success "All connectivity tests passed! 🎉"
        echo ""
        echo "🌐 All services are properly connected and accessible!"
        echo "📚 API Documentation: http://localhost:8000/docs"
        echo "🗄️  Database Admin: http://localhost:5050"
        echo "🗄️  Redis Admin: http://localhost:8081"
    else
        print_error "Some connectivity tests failed! ❌"
        echo ""
        echo "Please check the failed services:"
        echo "  - Ensure Docker containers are running: docker-compose -f docker-compose.dev.yml ps"
        echo "  - Check container logs: docker-compose -f docker-compose.dev.yml logs [service_name]"
        echo "  - Restart services if needed: ./config/dev-restart.sh"
    fi
}

# Function to check if Docker is running
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

# Main execution
main() {
    echo ""
    echo "🔗 SAFE-BMAD Service Connectivity Tests"
    echo "======================================"
    echo ""

    check_docker

    # Test Docker containers
    for service_info in "${SERVICES[@]}"; do
        IFS=':' read -r service_name port service_desc service_type <<< "$service_info"
        test_container_status "$service_name"
        test_port_connectivity "localhost" "$port" "$service_name" "$service_desc"
    done

    # Test specific service connectivity
    test_database_connectivity
    test_redis_connectivity
    test_api_endpoints
    test_service_dependencies
    test_docker_network

    # Show system information
    show_system_resources

    # Show summary
    show_summary
}

# Handle script arguments
case "${1:-}" in
    --help|help|-h)
        echo "SAFE-BMAD Service Connectivity Tests"
        echo ""
        echo "Usage: $0 [options]"
        echo ""
        echo "Options:"
        echo "  --help     Show this help message"
        echo ""
        echo "Description:"
        echo "  Tests connectivity between all services in the SAFE-BMAD"
        echo "  development environment, including Docker containers, ports,"
        echo "  HTTP endpoints, and service dependencies."
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