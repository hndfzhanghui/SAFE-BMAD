#!/bin/bash

# Database Restore Script for SAFE-BMAD Development Environment
# Usage: ./restore.sh [backup_file] [database_name]

set -e

# Default values
BACKUP_FILE=${1:-""}
DB_NAME=${2:-"safe_dev"}
DB_USER="safe_user"
DB_PASSWORD="safe_password"
DB_HOST="localhost"
DB_PORT="5432"
BACKUP_DIR="backups"

# Function to show usage
show_usage() {
    echo "Usage: $0 [backup_file] [database_name]"
    echo ""
    echo "Examples:"
    echo "  $0 safe_dev_backup_20231021_143022.sql.gz safe_dev"
    echo "  $0 backups/safe_dev_backup_20231021_143022.sql.gz"
    echo "  $0  # Lists available backups"
}

# Function to list available backups
list_backups() {
    echo "📋 Available backups:"
    if [ -d "$BACKUP_DIR" ] && [ "$(ls -A $BACKUP_DIR/*.gz 2>/dev/null)" ]; then
        ls -lh $BACKUP_DIR/*.gz | nl
    else
        echo "No backup files found in $BACKUP_DIR/"
    fi
}

# Check if backup file is provided
if [ -z "$BACKUP_FILE" ]; then
    list_backups
    echo ""
    show_usage
    exit 1
fi

# If backup file doesn't exist in current directory, try backup directory
if [ ! -f "$BACKUP_FILE" ]; then
    if [ -f "$BACKUP_DIR/$BACKUP_FILE" ]; then
        BACKUP_FILE="$BACKUP_DIR/$BACKUP_FILE"
    else
        echo "❌ Backup file not found: $BACKUP_FILE"
        list_backups
        exit 1
    fi
fi

echo "🔄 Starting database restore..."
echo "Backup file: $BACKUP_FILE"
echo "Target database: $DB_NAME"

# Check if Docker containers are running
if ! docker ps | grep -q safe-bmad-db; then
    echo "❌ Database container is not running. Please start Docker services first."
    exit 1
fi

# Check if database is accessible
if ! PGPASSWORD=$DB_PASSWORD pg_isready -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME; then
    echo "❌ Database is not accessible. Please check your Docker containers."
    exit 1
fi

# Confirm restore operation
echo ""
echo "⚠️  This will completely replace the current database '$DB_NAME' with the backup."
read -p "Are you sure you want to continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "❌ Restore operation cancelled."
    exit 1
fi

# Extract backup if compressed
TEMP_BACKUP=""
if [[ $BACKUP_FILE == *.gz ]]; then
    TEMP_BACKUP="${BACKUP_FILE%.gz}"
    echo "📦 Extracting backup file..."
    gunzip -c "$BACKUP_FILE" > "$TEMP_BACKUP"
    BACKUP_FILE="$TEMP_BACKUP"
fi

# Drop and recreate database
echo "🗑️  Dropping existing database..."
PGPASSWORD=$DB_PASSWORD dropdb -h $DB_HOST -p $DB_PORT -U $DB_USER -f $DB_NAME --if-exists

echo "🆕 Creating new database..."
PGPASSWORD=$DB_PASSWORD createdb -h $DB_HOST -p $DB_PORT -U $DB_USER $DB_NAME

# Restore backup
echo "📥 Restoring database..."
PGPASSWORD=$DB_PASSWORD pg_restore \
    -h $DB_HOST \
    -p $DB_PORT \
    -U $DB_USER \
    -d $DB_NAME \
    --verbose \
    --clean \
    --no-owner \
    --no-privileges \
    "$BACKUP_FILE"

# Clean up temporary file
if [ ! -z "$TEMP_BACKUP" ]; then
    rm -f "$TEMP_BACKUP"
fi

echo "✅ Database restore completed successfully!"
echo ""
echo "🔍 Verifying restored data..."
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "
SELECT
    (SELECT COUNT(*) FROM agents) as agents_count,
    (SELECT COUNT(*) FROM plan_instances) as plans_count,
    (SELECT COUNT(*) FROM tasks) as tasks_count;
"

echo "🎉 Restore completed! Database '$DB_NAME' is ready for use."