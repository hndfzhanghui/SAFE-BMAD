#!/bin/bash

# Cache Flush Script for SAFE-BMAD Development Environment
# Provides safe cache clearing with confirmation

CONTAINER_NAME="safe-bmad-redis-dev"
REDIS_PASSWORD="dev_redis_password"

echo "🧹 SAFE-BMAD Cache Flush Utility"
echo "================================="

# Function to check if Redis container is running
check_redis_container() {
    if ! docker ps | grep -q $CONTAINER_NAME; then
        echo "❌ Redis container is not running."
        echo "Please start Docker services first: docker-compose -f docker-compose.dev.yml up -d"
        exit 1
    fi
}

# Function to get current cache info
show_cache_info() {
    echo "📊 Current Cache Information:"
    if [ -n "$REDIS_PASSWORD" ]; then
        docker exec $CONTAINER_NAME redis-cli -a $REDIS_PASSWORD info keyspace | head -5
    else
        docker exec $CONTAINER_NAME redis-cli info keyspace | head -5
    fi
    echo ""
}

# Function to show database sizes
show_database_sizes() {
    echo "💾 Database Sizes:"
    for db in {0..15}; do
        size=$(docker exec $CONTAINER_NAME redis-cli -n $db dbsize 2>/dev/null)
        if [ "$size" != "0" ]; then
            echo "  DB$db: $size keys"
        fi
    done
    echo ""
}

# Check container status
check_redis_container

# Show current cache information
show_cache_info
show_database_sizes

echo "🎯 Available flush options:"
echo "1) Flush current database only (DB0)"
echo "2) Flush specific database (0-15)"
echo "3) Flush ALL databases"
echo "4) Show cache statistics only"
echo "5) Exit"

read -p "Please select an option (1-5): " choice

case $choice in
    1)
        echo "⚠️  This will clear the current database (DB0)."
        read -p "Are you sure? (yes/no): " confirm
        if [ "$confirm" = "yes" ]; then
            echo "🧹 Flushing current database..."
            if [ -n "$REDIS_PASSWORD" ]; then
                docker exec $CONTAINER_NAME redis-cli -a $REDIS_PASSWORD flushdb
            else
                docker exec $CONTAINER_NAME redis-cli flushdb
            fi
            echo "✅ Current database flushed successfully"
        else
            echo "❌ Operation cancelled"
        fi
        ;;
    2)
        read -p "Enter database number (0-15): " db_num
        if [[ $db_num =~ ^[0-9]+$ ]] && [ $db_num -ge 0 ] && [ $db_num -le 15 ]; then
            echo "⚠️  This will clear database DB$db_num."
            read -p "Are you sure? (yes/no): " confirm
            if [ "$confirm" = "yes" ]; then
                echo "🧹 Flushing database DB$db_num..."
                if [ -n "$REDIS_PASSWORD" ]; then
                    docker exec $CONTAINER_NAME redis-cli -a $REDIS_PASSWORD -n $db_num flushdb
                else
                    docker exec $CONTAINER_NAME redis-cli -n $db_num flushdb
                fi
                echo "✅ Database DB$db_num flushed successfully"
            else
                echo "❌ Operation cancelled"
            fi
        else
            echo "❌ Invalid database number. Please enter 0-15."
        fi
        ;;
    3)
        echo "⚠️  This will clear ALL databases in Redis (DB0-DB15)."
        read -p "Are you absolutely sure? Type 'DELETE ALL' to confirm: " confirm
        if [ "$confirm" = "DELETE ALL" ]; then
            echo "🧹 Flushing all databases..."
            if [ -n "$REDIS_PASSWORD" ]; then
                docker exec $CONTAINER_NAME redis-cli -a $REDIS_PASSWORD flushall
            else
                docker exec $CONTAINER_NAME redis-cli flushall
            fi
            echo "✅ All databases flushed successfully"
        else
            echo "❌ Operation cancelled"
        fi
        ;;
    4)
        echo "📈 Detailed Cache Statistics:"
        if [ -n "$REDIS_PASSWORD" ]; then
            docker exec $CONTAINER_NAME redis-cli -a $REDIS_PASSWORD info memory
            echo ""
            docker exec $CONTAINER_NAME redis-cli -a $REDIS_PASSWORD info stats
        else
            docker exec $CONTAINER_NAME redis-cli info memory
            echo ""
            docker exec $CONTAINER_NAME redis-cli info stats
        fi
        ;;
    5)
        echo "👋 Exiting..."
        exit 0
        ;;
    *)
        echo "❌ Invalid option. Please select 1-5."
        exit 1
        ;;
esac

echo ""
echo "✅ Cache flush operation completed!"
echo ""
echo "📊 Updated cache information:"
show_cache_info
show_database_sizes