#!/bin/bash

# Database Backup Script for SAFE-BMAD Development Environment
# Usage: ./backup.sh [database_name] [backup_file]

set -e

# Default values
DB_NAME=${1:-"safe_dev"}
DB_USER="safe_user"
DB_PASSWORD="safe_password"
DB_HOST="localhost"
DB_PORT="5432"
BACKUP_DIR="backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE=${2:-"${DB_NAME}_backup_${TIMESTAMP}.sql"}

# Create backup directory if it doesn't exist
mkdir -p $BACKUP_DIR

echo "🔄 Starting database backup..."
echo "Database: $DB_NAME"
echo "Backup file: $BACKUP_DIR/$BACKUP_FILE"

# Check if database is accessible
if ! PGPASSWORD=$DB_PASSWORD pg_isready -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME; then
    echo "❌ Database is not accessible. Please check your Docker containers."
    exit 1
fi

# Perform backup
echo "📦 Creating backup..."
PGPASSWORD=$DB_PASSWORD pg_dump \
    -h $DB_HOST \
    -p $DB_PORT \
    -U $DB_USER \
    -d $DB_NAME \
    --verbose \
    --clean \
    --no-owner \
    --no-privileges \
    --format=custom \
    --file="$BACKUP_DIR/$BACKUP_FILE"

# Compress the backup file
echo "🗜️  Compressing backup..."
gzip "$BACKUP_DIR/$BACKUP_FILE"

echo "✅ Backup completed successfully!"
echo "📁 Backup file: $BACKUP_DIR/${BACKUP_FILE}.gz"
echo "💾 Size: $(du -h $BACKUP_DIR/${BACKUP_FILE}.gz | cut -f1)"

# List recent backups
echo ""
echo "📋 Recent backups:"
ls -lh $BACKUP_DIR/*.gz | tail -5