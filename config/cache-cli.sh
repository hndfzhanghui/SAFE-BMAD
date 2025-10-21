#!/bin/bash

# Redis CLI Wrapper for SAFE-BMAD Development Environment
# Provides easy access to Redis commands for cache management

REDIS_HOST="localhost"
REDIS_PORT="6379"
REDIS_PASSWORD="dev_redis_password"
CONTAINER_NAME="safe-bmad-redis-dev"

# Function to show usage
show_usage() {
    echo "SAFE-BMAD Redis CLI Tool"
    echo "Usage: $0 [command] [args...]"
    echo ""
    echo "Available commands:"
    echo "  connect              - Connect to Redis CLI"
    echo "  info                 - Show Redis server info"
    echo "  keys [pattern]       - List keys (default: *)"
    echo "  get <key>            - Get value for key"
    echo "  set <key> <value>    - Set value for key"
    echo "  del <key>            - Delete key"
    echo "  flushall             - Clear all databases"
    echo "  flushdb              - Clear current database"
    echo "  dbsize               - Show current database size"
    echo "  monitor              - Monitor Redis commands in real-time"
    echo "  scan                 - Scan keys with cursor"
    echo "  config               - Show configuration"
    echo "  stats                - Show performance statistics"
}

# Function to execute Redis command
execute_redis_cmd() {
    if [ -n "$REDIS_PASSWORD" ]; then
        docker exec -it $CONTAINER_NAME redis-cli -a $REDIS_PASSWORD "$@"
    else
        docker exec -it $CONTAINER_NAME redis-cli "$@"
    fi
}

# Function to check if Redis container is running
check_redis_container() {
    if ! docker ps | grep -q $CONTAINER_NAME; then
        echo "❌ Redis container is not running."
        echo "Please start Docker services first: docker-compose -f docker-compose.dev.yml up -d"
        exit 1
    fi
}

# Check container status
check_redis_container

# Process command
case "$1" in
    "connect")
        echo "🔗 Connecting to Redis CLI..."
        if [ -n "$REDIS_PASSWORD" ]; then
            docker exec -it $CONTAINER_NAME redis-cli -a $REDIS_PASSWORD
        else
            docker exec -it $CONTAINER_NAME redis-cli
        fi
        ;;
    "info")
        echo "📊 Redis Server Information:"
        execute_redis_cmd info
        ;;
    "keys")
        pattern=${2:-"*"}
        echo "🔑 Keys matching pattern '$pattern':"
        execute_redis_cmd keys "$pattern"
        ;;
    "get")
        if [ -z "$2" ]; then
            echo "❌ Please provide a key: $0 get <key>"
            exit 1
        fi
        echo "📖 Getting value for key '$2':"
        execute_redis_cmd get "$2"
        ;;
    "set")
        if [ -z "$2" ] || [ -z "$3" ]; then
            echo "❌ Please provide key and value: $0 set <key> <value>"
            exit 1
        fi
        echo "💾 Setting value for key '$2':"
        execute_redis_cmd set "$2" "$3"
        echo "✅ Value set successfully"
        ;;
    "del")
        if [ -z "$2" ]; then
            echo "❌ Please provide a key: $0 del <key>"
            exit 1
        fi
        echo "🗑️  Deleting key '$2':"
        execute_redis_cmd del "$2"
        ;;
    "flushall")
        echo "⚠️  This will clear ALL databases in Redis."
        read -p "Are you sure? (yes/no): " confirm
        if [ "$confirm" = "yes" ]; then
            execute_redis_cmd flushall
            echo "✅ All databases cleared"
        else
            echo "❌ Operation cancelled"
        fi
        ;;
    "flushdb")
        echo "⚠️  This will clear the current database."
        read -p "Are you sure? (yes/no): " confirm
        if [ "$confirm" = "yes" ]; then
            execute_redis_cmd flushdb
            echo "✅ Current database cleared"
        else
            echo "❌ Operation cancelled"
        fi
        ;;
    "dbsize")
        echo "📊 Current database size:"
        execute_redis_cmd dbsize
        ;;
    "monitor")
        echo "🔍 Monitoring Redis commands (Press Ctrl+C to stop):"
        execute_redis_cmd monitor
        ;;
    "scan")
        echo "🔍 Scanning keys with cursor:"
        execute_redis_cmd scan 0
        ;;
    "config")
        echo "⚙️  Redis Configuration:"
        execute_redis_cmd config get "*"
        ;;
    "stats")
        echo "📈 Performance Statistics:"
        execute_redis_cmd info stats
        echo ""
        echo "💾 Memory Usage:"
        execute_redis_cmd info memory
        echo ""
        echo "👥 Client Connections:"
        execute_redis_cmd info clients
        ;;
    "help"|"--help"|"-h"|"")
        show_usage
        ;;
    *)
        # Pass through any other Redis command
        echo "🚀 Executing Redis command: $@"
        execute_redis_cmd "$@"
        ;;
esac