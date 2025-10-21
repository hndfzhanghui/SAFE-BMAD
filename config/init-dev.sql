-- Development Database Initialization Script
-- This script is executed when the PostgreSQL container starts for the first time

-- Create additional databases if needed
-- CREATE DATABASE safe_test;
-- CREATE DATABASE safe_staging;

-- Create additional users with specific permissions
-- CREATE USER safe_test_user WITH PASSWORD 'test_password';
-- CREATE USER safe_readonly_user WITH PASSWORD 'readonly_password';

-- Grant permissions
-- GRANT ALL PRIVILEGES ON DATABASE safe_test TO safe_test_user;
-- GRANT CONNECT ON DATABASE safe_dev TO safe_readonly_user;
-- GRANT USAGE ON SCHEMA public TO safe_readonly_user;
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO safe_readonly_user;

-- Install useful extensions for development
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create schemas for better organization
CREATE SCHEMA IF NOT EXISTS agents;
CREATE SCHEMA IF NOT EXISTS workflows;
CREATE SCHEMA IF NOT EXISTS audit;

-- Set up logging
ALTER SYSTEM SET log_statement = 'mod';
ALTER SYSTEM SET log_min_duration_statement = 1000; -- Log queries taking more than 1 second
SELECT pg_reload_conf();

-- Grant schema permissions
GRANT ALL ON SCHEMA agents TO safe_user;
GRANT ALL ON SCHEMA workflows TO safe_user;
GRANT ALL ON SCHEMA audit TO safe_user;

COMMIT;