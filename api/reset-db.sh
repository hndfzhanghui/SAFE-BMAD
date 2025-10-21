#!/bin/bash

# Database Reset Script for SAFE-BMAD System
# This script completely resets the database to initial state

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

# Function to create backup before reset
create_final_backup() {
    local backup_name="safe_bmad_before_reset_$(date +%Y%m%d_%H%M%S)"
    print_status "Creating final backup before reset: $backup_name"

    # Extract connection details from DATABASE_URL
    if [[ $DATABASE_URL =~ postgresql://([^:]+):([^@]+)@([^:]+):([0-9]+)/(.+) ]]; then
        DB_USER="${BASH_REMATCH[1]}"
        DB_PASS="${BASH_REMATCH[2]}"
        DB_HOST="${BASH_REMATCH[3]}"
        DB_PORT="${BASH_REMATCH[4]}"
        DB_NAME="${BASH_REMATCH[5]}"

        # Create backup using pg_dump if available
        if command -v pg_dump &> /dev/null; then
            mkdir -p ../backups
            PGPASSWORD="$DB_PASS" pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "../backups/${backup_name}.sql"
            print_success "Final backup created: ../backups/${backup_name}.sql"
        else
            print_warning "pg_dump not available, skipping backup creation"
        fi
    fi
}

# Function to drop and recreate database
reset_complete_database() {
    print_status "Completely resetting database..."

    # Extract connection details from DATABASE_URL
    if [[ $DATABASE_URL =~ postgresql://([^:]+):([^@]+)@([^:]+):([0-9]+)/(.+) ]]; then
        DB_USER="${BASH_REMATCH[1]}"
        DB_PASS="${BASH_REMATCH[2]}"
        DB_HOST="${BASH_REMATCH[3]}"
        DB_PORT="${BASH_REMATCH[4]}"
        DB_NAME="${BASH_REMATCH[5]}"
        DB_ADMIN="${DB_USER}"  # Assuming user has admin privileges

        print_warning "Dropping all tables in database: $DB_NAME"

        # Drop all public schema objects
        if command -v psql &> /dev/null; then
            PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_ADMIN" -d "$DB_NAME" << EOF
-- Drop all tables in the public schema
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;

-- Grant permissions
GRANT ALL ON SCHEMA public TO $DB_USER;
GRANT ALL ON SCHEMA public TO PUBLIC;

-- Set default permissions
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO $DB_USER;
EOF

            if [ $? -eq 0 ]; then
                print_success "Database schema reset successfully"
            else
                print_error "Failed to reset database schema"
                exit 1
            fi
        else
            print_error "psql not available, cannot reset database"
            exit 1
        fi
    else
        print_error "Could not parse DATABASE_URL"
        exit 1
    fi
}

# Function to run initial migrations
run_initial_migrations() {
    print_status "Running initial database migrations..."

    # Stamp database with base revision
    alembic stamp base

    # Run all migrations
    alembic upgrade head

    print_success "Initial migrations completed"
}

# Function to insert seed data
insert_seed_data() {
    print_status "Inserting seed data..."

    # Extract connection details from DATABASE_URL
    if [[ $DATABASE_URL =~ postgresql://([^:]+):([^@]+)@([^:]+):([0-9]+)/(.+) ]]; then
        DB_USER="${BASH_REMATCH[1]}"
        DB_PASS="${BASH_REMATCH[2]}"
        DB_HOST="${BASH_REMATCH[3]}"
        DB_PORT="${BASH_REMATCH[4]}"
        DB_NAME="${BASH_REMATCH[5]}"

        if command -v psql &> /dev/null; then
            PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" << 'EOF'
-- Insert default admin user (password: admin123)
INSERT INTO users (username, email, password_hash, full_name, role, is_active)
VALUES (
    'admin',
    'admin@safe-bmad.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj6QJw/2Ej7W',
    'System Administrator',
    'admin',
    true
) ON CONFLICT (username) DO NOTHING;

-- Insert default agent types configuration data
INSERT INTO scenarios (title, description, status, priority, created_by_id, emergency_type)
VALUES (
    'System Initialization',
    'Default scenario for system initialization',
    'active',
    'medium',
    1,
    '{"type": "system", "category": "initialization"}'
) ON CONFLICT DO NOTHING;

-- Update sequence values
SELECT setval('users_id_seq', (SELECT COALESCE(MAX(id), 1) FROM users));
SELECT setval('scenarios_id_seq', (SELECT COALESCE(MAX(id), 1) FROM scenarios));
EOF

            if [ $? -eq 0 ]; then
                print_success "Seed data inserted successfully"
            else
                print_warning "Failed to insert seed data (this is not critical)"
            fi
        fi
    fi
}

# Function to verify database reset
verify_database_reset() {
    print_status "Verifying database reset..."

    # Check if tables exist
    tables=("users" "scenarios" "agents" "analysis" "decisions" "resources" "messages" "user_scenarios")

    for table in "${tables[@]}"; do
        if ! alembic current &> /dev/null; then
            print_error "Database reset verification failed"
            return 1
        fi
    done

    # Check if seed data exists
    if command -v psql &> /dev/null; then
        if [[ $DATABASE_URL =~ postgresql://([^:]+):([^@]+)@([^:]+):([0-9]+)/(.+) ]]; then
            DB_USER="${BASH_REMATCH[1]}"
            DB_PASS="${BASH_REMATCH[2]}"
            DB_HOST="${BASH_REMATCH[3]}"
            DB_PORT="${BASH_REMATCH[4]}"
            DB_NAME="${BASH_REMATCH[5]}"

            admin_count=$(PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM users WHERE role='admin';" | tr -d ' ')

            if [ "$admin_count" -gt 0 ]; then
                print_success "Admin user found in database"
            else
                print_warning "No admin user found in database"
            fi
        fi
    fi

    print_success "Database reset verification completed"
}

# Function to show reset warning
show_reset_warning() {
    echo ""
    print_warning "╔════════════════════════════════════════════════════════════════╗"
    print_warning "║                      WARNING: DATABASE RESET                   ║"
    print_warning "╠════════════════════════════════════════════════════════════════╣"
    print_warning "║ This operation will completely ERASE all data in the database! ║"
    print_warning "║ All user data, scenarios, agents, and analysis will be lost.   ║"
    print_warning "║ A backup will be created before the reset.                    ║"
    print_warning "╚════════════════════════════════════════════════════════════════╝"
    echo ""
}

# Main reset function
reset_database() {
    show_reset_warning

    read -p "Are you absolutely sure you want to reset the database? (type 'RESET' to confirm): " -r
    echo

    if [[ $REPLY == "RESET" ]]; then
        print_status "Starting database reset process..."

        # Step 1: Create final backup
        create_final_backup

        # Step 2: Drop and recreate database
        reset_complete_database

        # Step 3: Run initial migrations
        run_initial_migrations

        # Step 4: Insert seed data
        insert_seed_data

        # Step 5: Verify reset
        verify_database_reset

        print_success "Database reset completed successfully!"
        print_status "Default admin credentials:"
        print_status "  Username: admin"
        print_status "  Password: admin123"
        print_warning "Please change the default password after first login!"
    else
        print_status "Database reset cancelled"
    fi
}

# Function to quick reset (without confirmation - for development only)
quick_reset() {
    print_warning "Quick reset mode - no confirmation required"
    print_status "Starting quick database reset..."

    create_final_backup
    reset_complete_database
    run_initial_migrations
    insert_seed_data
    verify_database_reset

    print_success "Quick database reset completed!"
}

# Function to show help
show_help() {
    echo "SAFE-BMAD Database Reset Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  reset       Full database reset with confirmation and backup"
    echo "  quick       Quick reset (development only, no confirmation)"
    echo "  help        Show this help message"
    echo ""
    echo "WARNING: This script will completely erase all database data!"
    echo "Always create backups before performing resets in production."
    echo ""
    echo "Examples:"
    echo "  $0 reset     # Full reset with confirmation"
    echo "  $0 quick     # Quick reset for development"
}

# Create backups directory if it doesn't exist
mkdir -p ../backups

# Main script logic
case "${1:-help}" in
    reset)
        reset_database
        ;;
    quick)
        quick_reset
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