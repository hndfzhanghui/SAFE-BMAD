#!/bin/bash

# API Health Check Test Script for SAFE-BMAD
# Tests all health endpoints and provides detailed status

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
API_BASE_URL="http://localhost:8000"
TIMEOUT=30
RETRY_COUNT=3
RETRY_DELAY=2

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

# Function to make HTTP request with retries
make_request() {
    local endpoint="$1"
    local method="${2:-GET}"
    local expected_status="${3:-200}"
    local retry_count=0
    local response=""

    while [ $retry_count -lt $RETRY_COUNT ]; do
        response=$(curl -s -w "\n%{http_code}" \
            -X "$method" \
            --max-time $TIMEOUT \
            "$API_BASE_URL$endpoint" \
            2>/dev/null || true)

        local status_code=$(echo "$response" | tail -n1)
        local body=$(echo "$response" | sed '$d')

        if [ "$status_code" -eq "$expected_status" ]; then
            echo "$body"
            return 0
        fi

        ((retry_count++))
        if [ $retry_count -lt $RETRY_COUNT ]; then
            sleep $RETRY_DELAY
        fi
    done

    echo "HTTP $status_code: $body"
    return 1
}

# Function to test health endpoint
test_health_endpoint() {
    print_status "Testing /health endpoint..."

    local response
    if response=$(make_request "/health"); then
        print_success "Health endpoint is responding"

        # Parse JSON response (basic parsing)
        local status=$(echo "$response" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
        local timestamp=$(echo "$response" | grep -o '"timestamp":"[^"]*"' | cut -d'"' -f4)
        local service=$(echo "$response" | grep -o '"service":"[^"]*"' | cut -d'"' -f4)
        local version=$(echo "$response" | grep -o '"version":"[^"]*"' | cut -d'"' -f4)

        echo "  Status: $status"
        echo "  Service: $service"
        echo "  Version: $version"
        echo "  Timestamp: $timestamp"

        if [ "$status" = "healthy" ]; then
            ((TESTS_PASSED++))
            return 0
        else
            print_error "Health endpoint reports unhealthy status"
            ((TESTS_FAILED++))
            return 1
        fi
    else
        print_error "Health endpoint is not responding"
        ((TESTS_FAILED++))
        return 1
    fi
}

# Function to test readiness endpoint
test_readiness_endpoint() {
    print_status "Testing /ready endpoint..."

    local response
    if response=$(make_request "/ready"); then
        print_success "Readiness endpoint is responding"

        # Parse JSON response
        local status=$(echo "$response" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
        local timestamp=$(echo "$response" | grep -o '"timestamp":"[^"]*"' | cut -d'"' -f4)

        echo "  Status: $status"
        echo "  Timestamp: $timestamp"

        # Check individual component status
        local db_status=$(echo "$response" | grep -o '"database":{"status":"[^"]*"' | cut -d'"' -f4)
        local redis_status=$(echo "$response" | grep -o '"redis":{"status":"[^"]*"' | cut -d'"' -f4)

        echo "  Database: $db_status"
        echo "  Redis: $redis_status"

        if [ "$status" = "ready" ]; then
            ((TESTS_PASSED++))
            return 0
        else
            print_warning "Readiness endpoint reports not ready"
            ((TESTS_FAILED++))
            return 1
        fi
    else
        print_error "Readiness endpoint is not responding"
        ((TESTS_FAILED++))
        return 1
    fi
}

# Function to test metrics endpoint
test_metrics_endpoint() {
    print_status "Testing /metrics endpoint..."

    local response
    if response=$(make_request "/metrics"); then
        print_success "Metrics endpoint is responding"

        # Parse JSON response
        local timestamp=$(echo "$response" | grep -o '"timestamp":"[^"]*"' | cut -d'"' -f4)
        local version=$(echo "$response" | grep -o '"version":"[^"]*"' | cut -d'"' -f4)
        local environment=$(echo "$response" | grep -o '"environment":"[^"]*"' | cut -d'"' -f4)

        echo "  Version: $version"
        echo "  Environment: $environment"
        echo "  Timestamp: $timestamp"

        ((TESTS_PASSED++))
        return 0
    else
        print_error "Metrics endpoint is not responding"
        ((TESTS_FAILED++))
        return 1
    fi
}

# Function to test root endpoint
test_root_endpoint() {
    print_status "Testing root endpoint..."

    local response
    if response=$(make_request "/"); then
        print_success "Root endpoint is responding"

        # Parse JSON response
        local message=$(echo "$response" | grep -o '"message":"[^"]*"' | cut -d'"' -f4)
        local version=$(echo "$response" | grep -o '"version":"[^"]*"' | cut -d'"' -f4)

        echo "  Message: $message"
        echo "  Version: $version"

        ((TESTS_PASSED++))
        return 0
    else
        print_error "Root endpoint is not responding"
        ((TESTS_FAILED++))
        return 1
    fi
}

# Function to test API documentation endpoints
test_docs_endpoints() {
    print_status "Testing API documentation endpoints..."

    # Test Swagger UI
    if make_request "/docs" > /dev/null; then
        print_success "Swagger UI is accessible"
        ((TESTS_PASSED++))
    else
        print_error "Swagger UI is not accessible"
        ((TESTS_FAILED++))
    fi

    # Test ReDoc
    if make_request "/redoc" > /dev/null; then
        print_success "ReDoc is accessible"
        ((TESTS_PASSED++))
    else
        print_error "ReDoc is not accessible"
        ((TESTS_FAILED++))
    fi

    # Test OpenAPI JSON
    if make_request "/openapi.json" > /dev/null; then
        print_success "OpenAPI JSON is accessible"
        ((TESTS_PASSED++))
    else
        print_error "OpenAPI JSON is not accessible"
        ((TESTS_FAILED++))
    fi
}

# Function to test CORS headers
test_cors_headers() {
    print_status "Testing CORS headers..."

    local response_headers
    response_headers=$(curl -s -I \
        -H "Origin: http://localhost:3000" \
        -H "Access-Control-Request-Method: POST" \
        -H "Access-Control-Request-Headers: X-Requested-With" \
        -X OPTIONS \
        "$API_BASE_URL/test-cors" \
        2>/dev/null || true)

    if echo "$response_headers" | grep -q "Access-Control-Allow-Origin"; then
        print_success "CORS headers are properly configured"
        ((TESTS_PASSED++))
    else
        print_warning "CORS headers test inconclusive (endpoint may not exist)"
        # Don't count as failure since this is optional
    fi
}

# Function to check API response time
test_response_time() {
    print_status "Testing API response times..."

    local start_time=$(date +%s%N)
    make_request "/health" > /dev/null
    local end_time=$(date +%s%N)

    local response_time=$(( (end_time - start_time) / 1000000 )) # Convert to milliseconds

    echo "  Health endpoint response time: ${response_time}ms"

    if [ $response_time -lt 1000 ]; then
        print_success "API response time is acceptable (< 1s)"
        ((TESTS_PASSED++))
    else
        print_warning "API response time is slow (> 1s)"
        ((TESTS_FAILED++))
    fi
}

# Function to show test summary
show_summary() {
    echo ""
    echo "🎯 Test Summary"
    echo "=============="
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
        print_success "All tests passed! 🎉"
        echo ""
        echo "🌐 API is healthy and ready for use!"
        echo "📚 API Documentation: $API_BASE_URL/docs"
        echo "📊 Metrics: $API_BASE_URL/metrics"
    else
        print_error "Some tests failed! ❌"
        echo ""
        echo "Please check the API service and try again."
        echo "You can view logs with: docker-compose -f docker-compose.dev.yml logs -f api"
    fi
}

# Function to check if API is running
check_api_running() {
    print_status "Checking if API service is running..."

    if ! curl -s --max-time 5 "$API_BASE_URL/health" > /dev/null 2>&1; then
        print_error "API service is not running at $API_BASE_URL"
        echo ""
        echo "Please start the API service first:"
        echo "  ./config/dev-start.sh"
        echo ""
        echo "Or start it manually:"
        echo "  cd api && python main.py"
        exit 1
    else
        print_success "API service is running"
    fi
}

# Main execution
main() {
    echo ""
    echo "🧪 SAFE-BMAD API Health Check Tests"
    echo "==================================="
    echo ""

    check_api_running

    # Run all tests
    test_health_endpoint
    test_readiness_endpoint
    test_metrics_endpoint
    test_root_endpoint
    test_docs_endpoints
    test_response_time
    test_cors_headers

    # Show summary
    show_summary
}

# Handle script arguments
case "${1:-}" in
    --help|help|-h)
        echo "SAFE-BMAD API Health Check Tests"
        echo ""
        echo "Usage: $0 [options]"
        echo ""
        echo "Options:"
        echo "  --help     Show this help message"
        echo ""
        echo "Description:"
        echo "  Runs comprehensive health checks on the SAFE-BMAD API service."
        echo "  Tests all health endpoints and provides detailed status reporting."
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