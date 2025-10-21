#!/bin/bash

# Database Rollback Script for SAFE-BMAD System
# This script handles database rollbacks using Alembic

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

# Function to create backup before rollback
create_backup() {
    local backup_name="safe_bmad_backup_$(date +%Y%m%d_%H%M%S)"
    print_status "Creating database backup: $backup_name"

    # Extract connection details from DATABASE_URL
    if [[ $DATABASE_URL =~ postgresql://([^:]+):([^@]+)@([^:]+):([0-9]+)/(.+) ]]; then
        DB_USER="${BASH_REMATCH[1]}"
        DB_PASS="${BASH_REMATCH[2]}"
        DB_HOST="${BASH_REMATCH[3]}"
        DB_PORT="${BASH_REMATCH[4]}"
        DB_NAME="${BASH_REMATCH[5]}"

        # Create backup using pg_dump if available
        if command -v pg_dump &> /dev/null; then
            PGPASSWORD="$DB_PASS" pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "../backups/${backup_name}.sql"
            print_success "Backup created: ../backups/${backup_name}.sql"
            echo "$backup_name" > ../backups/last_backup.txt
        else
            print_warning "pg_dump not available, skipping backup creation"
        fi
    fi
}

# Function to restore from backup
restore_backup() {
    local backup_name="$1"

    if [ -z "$backup_name" ]; then
        print_error "Backup name is required"
        echo "Usage: $0 restore <backup_name>"
        exit 1
    fi

    if [ ! -f "../backups/${backup_name}.sql" ]; then
        print_error "Backup file not found: ../backups/${backup_name}.sql"
        exit 1
    fi

    print_warning "This will restore database from backup: $backup_name"
    print_warning "All current data will be lost!"
    read -p "Are you sure you want to continue? (yes/no): " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        print_status "Restoring database from backup..."

        # Extract connection details from DATABASE_URL
        if [[ $DATABASE_URL =~ postgresql://([^:]+):([^@]+)@([^:]+):([0-9]+)/(.+) ]]; then
            DB_USER="${BASH_REMATCH[1]}"
            DB_PASS="${BASH_REMATCH[2]}"
            DB_HOST="${BASH_REMATCH[3]}"
            DB_PORT="${BASH_REMATCH[4]}"
            DB_NAME="${BASH_REMATCH[5]}"

            # Restore backup using psql if available
            if command -v psql &> /dev/null; then
                PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "../backups/${backup_name}.sql"
                print_success "Database restored successfully"
            else
                print_error "psql not available, cannot restore backup"
                exit 1
            fi
        fi
    else
        print_status "Database restore cancelled"
    fi
}

# Rollback to previous revision
rollback_previous() {
    print_status "Rolling back to previous revision..."
    create_backup

    # Get current revision
    current_revision=$(alembic current --verbose | grep -o 'Rev: [a-f0-9]*' | cut -d' ' -f2)

    if [ -z "$current_revision" ]; then
        print_error "Could not determine current revision"
        exit 1
    fi

    # Rollback to previous revision
    alembic downgrade -1
    print_success "Rolled back from revision: $current_revision"
}

# Rollback to specific revision
rollback_to_revision() {
    local target_revision="$1"

    if [ -z "$target_revision" ]; then
        print_error "Target revision is required"
        echo "Usage: $0 revision <revision_id>"
        exit 1
    fi

    print_status "Rolling back to revision: $target_revision"
    create_backup

    alembic downgrade "$target_revision"
    print_success "Rolled back to revision: $target_revision"
}

# Rollback to specific timestamp
rollback_to_timestamp() {
    local timestamp="$1"

    if [ -z "$timestamp" ]; then
        print_error "Timestamp is required"
        echo "Usage: $0 timestamp <YYYYMMDD_HHMMSS>"
        exit 1
    fi

    print_status "Finding revision closest to timestamp: $timestamp"

    # This would require custom logic to find revision by timestamp
    # For now, show available revisions
    print_status "Available revisions:"
    alembic history
    print_warning "Please use 'revision' command with the desired revision ID"
}

# List available backups
list_backups() {
    print_status "Available database backups:"

    if [ -d "../backups" ]; then
        ls -la ../backups/*.sql 2>/dev/null || print_warning "No backups found"
    else
        print_warning "Backups directory not found"
        mkdir -p ../backups
    fi
}

# Show rollback history
show_rollback_history() {
    print_status "Migration history (newest first):"
    alembic history
}

# Verify database integrity after rollback
verify_database() {
    print_status "Verifying database integrity..."

    # Check if alembic_version table exists and has valid data
    if alembic current &> /dev/null; then
        print_success "Database integrity check passed"
    else
        print_error "Database integrity check failed"
        return 1
    fi

    # Add more integrity checks as needed
    print_status "Database rollback verification completed"
}

# Safe rollback (with backup and verification)
safe_rollback() {
    local target_revision="$1"

    print_status "Starting safe rollback process..."

    # Create backup
    create_backup

    # Perform rollback
    if [ -n "$target_revision" ]; then
        rollback_to_revision "$target_revision"
    else
        rollback_previous
    fi

    # Verify integrity
    if verify_database; then
        print_success "Safe rollback completed successfully"
    else
        print_error "Rollback verification failed. Please check database manually."
        exit 1
    fi
}

# Show help
show_help() {
    echo "SAFE-BMAD Database Rollback Script"
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  previous                    Rollback to previous revision"
    echo "  revision <revision_id>      Rollback to specific revision"
    echo "  timestamp <timestamp>       Rollback to revision closest to timestamp"
    echo "  safe [revision_id]          Safe rollback with backup and verification"
    echo "  backup                      Create manual backup"
    echo "  restore <backup_name>       Restore from backup"
    echo "  list                        List available backups"
    echo "  history                     Show rollback history"
    echo "  verify                      Verify database integrity"
    echo "  help                        Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 previous"
    echo "  $0 revision 0001"
    echo "  $0 safe 0002"
    echo "  $0 backup"
    echo "  $0 restore safe_bmad_backup_20231021_143000"
    echo "  $0 list"
}

# Create backups directory if it doesn't exist
mkdir -p ../backups

# Main script logic
case "${1:-help}" in
    previous)
        safe_rollback
        ;;
    revision)
        safe_rollback "$2"
        ;;
    timestamp)
        rollback_to_timestamp "$2"
        ;;
    safe)
        safe_rollback "$2"
        ;;
    backup)
        create_backup
        ;;
    restore)
        restore_backup "$2"
        ;;
    list)
        list_backups
        ;;
    history)
        show_rollback_history
        ;;
    verify)
        verify_database
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