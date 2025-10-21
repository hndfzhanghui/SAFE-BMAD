#!/bin/bash

# Environment Variables Validation Script for SAFE-BMAD
# Validates that all required environment variables are set and properly formatted

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ENV_FILE=".env"
REQUIRED_VARS=(
    "DATABASE_URL"
    "REDIS_URL"
    "API_HOST"
    "API_PORT"
    "SECRET_KEY"
    "ENVIRONMENT"
)

OPTIONAL_VARS=(
    "AI_API_KEY"
    "LOG_LEVEL"
    "DEBUG"
    "VITE_API_BASE_URL"
)

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

# Function to validate environment file exists
check_env_file() {
    if [ ! -f "$ENV_FILE" ]; then
        print_error "Environment file '$ENV_FILE' not found!"
        echo ""
        echo "Please create an environment file:"
        echo "1. Copy the template: cp .env.template .env"
        echo "2. Edit the .env file with your settings"
        echo "3. Run this validation script again"
        exit 1
    fi

    print_success "Environment file found: $ENV_FILE"
}

# Function to load environment variables
load_env_vars() {
    print_status "Loading environment variables from $ENV_FILE..."

    # Source the environment file
    set -a
    source "$ENV_FILE"
    set +a

    print_success "Environment variables loaded"
}

# Function to validate database URL
validate_database_url() {
    print_status "Validating DATABASE_URL..."

    if [ -z "$DATABASE_URL" ]; then
        print_error "DATABASE_URL is not set"
        return 1
    fi

    # Check if URL has correct format
    if [[ ! "$DATABASE_URL" =~ ^postgresql:// ]]; then
        print_error "DATABASE_URL must start with 'postgresql://'"
        return 1
    fi

    # Extract components
    if [[ "$DATABASE_URL" =~ ^postgresql://([^:]+):([^@]+)@([^:]+):([0-9]+)/([^/]+)$ ]]; then
        local user="${BASH_REMATCH[1]}"
        local password="${BASH_REMATCH[2]}"
        local host="${BASH_REMATCH[3]}"
        local port="${BASH_REMATCH[4]}"
        local database="${BASH_REMATCH[5]}"

        print_success "Database URL components:"
        echo "  Host: $host"
        echo "  Port: $port"
        echo "  Database: $database"
        echo "  User: $user"

        return 0
    else
        print_error "DATABASE_URL format is invalid"
        echo "Expected format: postgresql://user:password@host:port/database"
        return 1
    fi
}

# Function to validate Redis URL
validate_redis_url() {
    print_status "Validating REDIS_URL..."

    if [ -z "$REDIS_URL" ]; then
        print_error "REDIS_URL is not set"
        return 1
    fi

    # Check if URL has correct format
    if [[ ! "$REDIS_URL" =~ ^redis:// ]]; then
        print_error "REDIS_URL must start with 'redis://'"
        return 1
    fi

    # Extract components
    if [[ "$REDIS_URL" =~ ^redis://([^:/]+)(:([0-9]+))?(/([0-9]+))?$ ]]; then
        local host="${BASH_REMATCH[1]}"
        local port="${BASH_REMATCH[3]:-6379}"
        local db="${BASH_REMATCH[5]:-0}"

        print_success "Redis URL components:"
        echo "  Host: $host"
        echo "  Port: $port"
        echo "  Database: $db"

        return 0
    else
        print_error "REDIS_URL format is invalid"
        echo "Expected format: redis://host[:port][/db]"
        return 1
    fi
}

# Function to validate API configuration
validate_api_config() {
    print_status "Validating API configuration..."

    local errors=0

    # Check API_HOST
    if [ -z "$API_HOST" ]; then
        print_error "API_HOST is not set"
        ((errors++))
    else
        print_success "API_HOST: $API_HOST"
    fi

    # Check API_PORT
    if [ -z "$API_PORT" ]; then
        print_error "API_PORT is not set"
        ((errors++))
    elif [[ ! "$API_PORT" =~ ^[0-9]+$ ]]; then
        print_error "API_PORT must be a number"
        ((errors++))
    else
        print_success "API_PORT: $API_PORT"
    fi

    # Check SECRET_KEY
    if [ -z "$SECRET_KEY" ]; then
        print_error "SECRET_KEY is not set"
        ((errors++))
    elif [ "$SECRET_KEY" = "your-secret-key-change-in-production" ]; then
        print_warning "SECRET_KEY is using default value - change for production!"
        ((errors++))
    elif [ ${#SECRET_KEY} -lt 32 ]; then
        print_warning "SECRET_KEY should be at least 32 characters long"
        ((errors++))
    else
        print_success "SECRET_KEY is set (length: ${#SECRET_KEY})"
    fi

    # Check ENVIRONMENT
    if [ -z "$ENVIRONMENT" ]; then
        print_error "ENVIRONMENT is not set"
        ((errors++))
    elif [[ ! "$ENVIRONMENT" =~ ^(development|testing|staging|production)$ ]]; then
        print_warning "ENVIRONMENT should be one of: development, testing, staging, production"
        ((errors++))
    else
        print_success "ENVIRONMENT: $ENVIRONMENT"
    fi

    return $errors
}

# Function to validate optional variables
validate_optional_vars() {
    print_status "Validating optional variables..."

    # Check AI_API_KEY
    if [ -n "$AI_API_KEY" ]; then
        if [ "$AI_API_KEY" = "your-deepseek-api-key-here" ]; then
            print_warning "AI_API_KEY is using placeholder value"
        else
            print_success "AI_API_KEY is configured"
        fi
    else
        print_warning "AI_API_KEY is not set - AI features may not work"
    fi

    # Check LOG_LEVEL
    if [ -n "$LOG_LEVEL" ]; then
        if [[ ! "$LOG_LEVEL" =~ ^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$ ]]; then
            print_warning "LOG_LEVEL should be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL"
        else
            print_success "LOG_LEVEL: $LOG_LEVEL"
        fi
    else
        print_warning "LOG_LEVEL is not set, using default"
    fi

    # Check DEBUG
    if [ -n "$DEBUG" ]; then
        if [[ ! "$DEBUG" =~ ^(true|false)$ ]]; then
            print_warning "DEBUG should be either 'true' or 'false'"
        else
            print_success "DEBUG: $DEBUG"
        fi
    fi
}

# Function to test database connectivity
test_database_connectivity() {
    print_status "Testing database connectivity..."

    # Extract database connection info from DATABASE_URL
    if [[ "$DATABASE_URL" =~ ^postgresql://([^:]+):([^@]+)@([^:]+):([0-9]+)/([^/]+)$ ]]; then
        local user="${BASH_REMATCH[1]}"
        local host="${BASH_REMATCH[3]}"
        local port="${BASH_REMATCH[4]}"
        local database="${BASH_REMATCH[5]}"

        # Test connection using docker if available
        if command -v docker > /dev/null && docker ps | grep -q safe-bmad-db; then
            if docker exec safe-bmad-db pg_isready -U "$user" -d "$database" > /dev/null 2>&1; then
                print_success "Database is accessible"
            else
                print_error "Database is not accessible - check if container is running"
                return 1
            fi
        else
            print_warning "Cannot test database connectivity - Docker not available or container not running"
        fi
    fi
}

# Function to test Redis connectivity
test_redis_connectivity() {
    print_status "Testing Redis connectivity..."

    # Extract Redis connection info from REDIS_URL
    if [[ "$REDIS_URL" =~ ^redis://([^:/]+)(:([0-9]+))?(/([0-9]+))?$ ]]; then
        local host="${BASH_REMATCH[1]}"
        local port="${BASH_REMATCH[3]:-6379}"

        # Test connection using docker if available
        if command -v docker > /dev/null && docker ps | grep -q safe-bmad-redis; then
            if docker exec safe-bmad-redis redis-cli ping > /dev/null 2>&1; then
                print_success "Redis is accessible"
            else
                print_error "Redis is not accessible - check if container is running"
                return 1
            fi
        else
            print_warning "Cannot test Redis connectivity - Docker not available or container not running"
        fi
    fi
}

# Function to show summary
show_summary() {
    local validation_status="$1"

    echo ""
    echo "🎯 Environment Validation Summary"
    echo "==============================="

    if [ "$validation_status" = "success" ]; then
        print_success "All validations passed! ✨"
        echo ""
        echo "Your environment is ready for development."
        echo "You can start the services with: ./config/dev-start.sh"
    else
        print_error "Validation failed! ❌"
        echo ""
        echo "Please fix the issues above before starting the services."
        echo "Refer to the documentation for more information."
    fi
}

# Main validation function
main() {
    local validation_errors=0

    echo ""
    echo "🔧 SAFE-BMAD Environment Variables Validator"
    echo "=========================================="
    echo ""

    check_env_file
    load_env_vars

    # Validate required variables
    validate_database_url || ((validation_errors++))
    validate_redis_url || ((validation_errors++))
    validate_api_config || ((validation_errors++))

    # Validate optional variables
    validate_optional_vars

    # Test connectivity (optional, may fail if services not running)
    echo ""
    print_status "Testing service connectivity (optional)..."
    test_database_connectivity || true
    test_redis_connectivity || true

    # Show summary
    if [ $validation_errors -eq 0 ]; then
        show_summary "success"
        exit 0
    else
        show_summary "failed"
        exit 1
    fi
}

# Handle script arguments
case "${1:-}" in
    --help|help|-h)
        echo "SAFE-BMAD Environment Variables Validator"
        echo ""
        echo "Usage: $0 [options]"
        echo ""
        echo "Options:"
        echo "  --help    Show this help message"
        echo ""
        echo "Description:"
        echo "  Validates that all required environment variables are set"
        echo "  and properly formatted for SAFE-BMAD development environment."
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