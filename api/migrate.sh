#!/bin/bash

# Database Migration Script for SAFE-BMAD System
# This script handles database migrations using Alembic

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
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

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if .env file exists
if [ ! -f "../.env" ]; then
    print_error ".env file not found. Please create it from .env.example"
    exit 1
fi

# Load environment variables
if [ -f "../.env" ]; then
    export $(cat ../.env | grep -v '^#' | xargs)
fi

# Check database connection
check_database_connection() {
    print_status "Checking database connection..."

    # Extract connection details from DATABASE_URL
    if [[ $DATABASE_URL =~ postgresql://([^:]+):([^@]+)@([^:]+):([0-9]+)/(.+) ]]; then
        DB_USER="${BASH_REMATCH[1]}"
        DB_PASS="${BASH_REMATCH[2]}"
        DB_HOST="${BASH_REMATCH[3]}"
        DB_PORT="${BASH_REMATCH[4]}"
        DB_NAME="${BASH_REMATCH[5]}"

        # Test connection using psql if available
        if command -v psql &> /dev/null; then
            if PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" &> /dev/null; then
                print_success "Database connection successful"
                return 0
            else
                print_error "Cannot connect to database"
                return 1
            fi
        else
            print_warning "psql not available, skipping connection test"
            return 0
        fi
    else
        print_warning "Could not parse DATABASE_URL, skipping connection test"
        return 0
    fi
}

# Initialize Alembic if not already initialized
initialize_alembic() {
    if [ ! -d "alembic" ]; then
        print_status "Initializing Alembic..."
        alembic init alembic
        print_success "Alembic initialized"
    else
        print_status "Alembic already initialized"
    fi
}

# Create new migration
create_migration() {
    local message="$1"
    if [ -z "$message" ]; then
        print_error "Migration message is required"
        echo "Usage: $0 create \"migration message\""
        exit 1
    fi

    print_status "Creating new migration: $message"
    alembic revision --autogenerate -m "$message"
    print_success "Migration created successfully"
}

# Upgrade database
upgrade_database() {
    local revision="$1"

    print_status "Upgrading database..."

    if [ -z "$revision" ]; then
        alembic upgrade head
    else
        alembic upgrade "$revision"
    fi

    print_success "Database upgraded successfully"
}

# Downgrade database
downgrade_database() {
    local revision="$1"

    if [ -z "$revision" ]; then
        print_error "Target revision is required for downgrade"
        echo "Usage: $0 downgrade <revision>"
        exit 1
    fi

    print_status "Downgrading database to revision: $revision"
    alembic downgrade "$revision"
    print_success "Database downgraded successfully"
}

# Show current revision
show_current_revision() {
    print_status "Current database revision:"
    alembic current
}

# Show migration history
show_history() {
    print_status "Migration history:"
    alembic history
}

# Show pending migrations
show_pending() {
    print_status "Pending migrations:"
    alembic heads
}

# Reset database (drop and recreate)
reset_database() {
    print_warning "This will reset the entire database. All data will be lost!"
    read -p "Are you sure you want to continue? (yes/no): " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        print_status "Resetting database..."

        # Drop all tables
        alembic downgrade base

        # Recreate tables
        alembic upgrade head

        print_success "Database reset successfully"
    else
        print_status "Database reset cancelled"
    fi
}

# Show help
show_help() {
    echo "SAFE-BMAD Database Migration Script"
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  check                    Check database connection"
    echo "  init                     Initialize Alembic"
    echo "  create \"message\"        Create new migration"
    echo "  upgrade [revision]       Upgrade database (to head or specific revision)"
    echo "  downgrade <revision>     Downgrade database to specific revision"
    echo "  current                  Show current revision"
    echo "  history                  Show migration history"
    echo "  pending                  Show pending migrations"
    echo "  reset                    Reset database (WARNING: deletes all data)"
    echo "  help                     Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 check"
    echo "  $0 create \"Add user preferences field\""
    echo "  $0 upgrade"
    echo "  $0 upgrade 0002"
    echo "  $0 downgrade 0001"
    echo "  $0 current"
}

# Main script logic
case "${1:-help}" in
    check)
        check_database_connection
        ;;
    init)
        initialize_alembic
        ;;
    create)
        create_migration "$2"
        ;;
    upgrade)
        check_database_connection
        upgrade_database "$2"
        ;;
    downgrade)
        check_database_connection
        downgrade_database "$2"
        ;;
    current)
        show_current_revision
        ;;
    history)
        show_history
        ;;
    pending)
        show_pending
        ;;
    reset)
        check_database_connection
        reset_database
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac