# Environment Variables Configuration Guide

This document explains the environment variables used by the SAFE-BMAD system and how to configure them for different environments.

## Overview

SAFE-BMAD uses environment variables to configure various aspects of the system including database connections, API settings, AI model configuration, and more. The system supports multiple environments (development, testing, staging, production) with different configurations for each.

## Getting Started

### 1. Create Environment File

Copy the template to create your environment file:

```bash
cp .env.template .env
```

### 2. Edit Environment File

Edit the `.env` file with your specific configuration values.

### 3. Validate Configuration

Run the validation script to ensure your configuration is correct:

```bash
./config/validate-env.sh
```

## Environment Variables

### Database Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | - | PostgreSQL connection URL in format `postgresql://user:password@host:port/database` |
| `DB_HOST` | No | localhost | Database server hostname |
| `DB_PORT` | No | 5432 | Database server port |
| `DB_NAME` | No | safe_dev | Database name |
| `DB_USER` | No | safe_user | Database username |
| `DB_PASSWORD` | No | safe_password | Database password |
| `DB_POOL_SIZE` | No | 10 | Database connection pool size |
| `DB_MAX_OVERFLOW` | No | 20 | Maximum overflow connections |
| `DB_POOL_TIMEOUT` | No | 30 | Connection pool timeout in seconds |
| `DB_POOL_RECYCLE` | No | 3600 | Connection recycle time in seconds |

### Redis Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `REDIS_URL` | Yes | - | Redis connection URL in format `redis://host:port/db` |
| `REDIS_HOST` | No | localhost | Redis server hostname |
| `REDIS_PORT` | No | 6379 | Redis server port |
| `REDIS_DB` | No | 0 | Redis database number |
| `REDIS_PASSWORD` | No | - | Redis password (optional) |
| `REDIS_POOL_SIZE` | No | 10 | Redis connection pool size |
| `REDIS_MAX_CONNECTIONS` | No | 50 | Maximum Redis connections |

### API Service Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `API_HOST` | Yes | 0.0.0.0 | API server bind address |
| `API_PORT` | Yes | 8000 | API server port |
| `API_WORKERS` | No | 1 | Number of worker processes |
| `DEBUG` | No | true | Enable debug mode |
| `RELOAD` | No | true | Enable auto-reload in development |
| `LOG_LEVEL` | No | DEBUG | Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `LOG_FORMAT` | No | json | Log format (json, text) |
| `LOG_FILE` | No | logs/app.log | Log file path |

### Security Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECRET_KEY` | Yes | - | JWT secret key (must be at least 32 characters) |
| `ALGORITHM` | No | HS256 | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | 30 | Access token expiration time in minutes |
| `REFRESH_TOKEN_EXPIRE_DAYS` | No | 7 | Refresh token expiration time in days |
| `ENCRYPTION_KEY` | No | - | Data encryption key |
| `HASH_ROUNDS` | No | 10 | Password hash rounds |
| `SESSION_TIMEOUT` | No | 3600 | Session timeout in seconds |

### CORS Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `CORS_ORIGINS` | No | ["http://localhost:3000"] | Allowed CORS origins |
| `CORS_ALLOW_CREDENTIALS` | No | true | Allow credentials in CORS |
| `CORS_ALLOW_METHODS` | No | ["GET", "POST", "PUT", "DELETE"] | Allowed HTTP methods |
| `CORS_ALLOW_HEADERS` | No | ["*"] | Allowed HTTP headers |

### AI/ML Model Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AI_MODEL_NAME` | No | deepseek-chat | AI model name |
| `AI_MODEL_BASE_URL` | No | http://localhost:8000/v1 | AI model API base URL |
| `AI_API_KEY` | No | - | AI model API key |
| `AI_MODEL_TEMPERATURE` | No | 0.7 | AI model temperature (0.0-1.0) |
| `AI_MODEL_MAX_TOKENS` | No | 2000 | Maximum tokens for AI responses |
| `AI_MODEL_TIMEOUT` | No | 30 | AI model timeout in seconds |

### AutoGen Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AUTOGEN_MAX_WORKER_AGENTS` | No | 5 | Maximum number of worker agents |
| `AUTOGEN_MAX_ROUND_TRIPS` | No | 10 | Maximum conversation rounds |
| `AUTOGEN_ENABLE_CODE_EXECUTION` | No | true | Enable code execution in agents |
| `AUTOGEN_ENABLE_DOCKER` | No | false | Enable Docker for code execution |

### Frontend Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `VITE_API_BASE_URL` | Yes | http://localhost:8000 | Frontend API base URL |
| `VITE_ENVIRONMENT` | No | development | Frontend environment |
| `VITE_RELOAD` | No | true | Enable hot reload |
| `VITE_APP_TITLE` | No | S3DA2 - SAFE BMAD System | Application title |
| `VITE_APP_VERSION` | No | 1.0.0 | Application version |

### Environment Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ENVIRONMENT` | Yes | development | Environment type (development, testing, staging, production) |
| `ENVIRONMENT_NAME` | No | Development Environment | Environment display name |

### Monitoring Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ENABLE_METRICS` | No | true | Enable metrics collection |
| `METRICS_PORT` | No | 9090 | Metrics server port |
| `HEALTH_CHECK_INTERVAL` | No | 30 | Health check interval in seconds |
| `PERFORMANCE_MONITORING` | No | true | Enable performance monitoring |

### Backup Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `BACKUP_ENABLED` | No | true | Enable automatic backups |
| `BACKUP_SCHEDULE` | No | 0 2 * * * | Backup schedule (cron format) |
| `BACKUP_RETENTION_DAYS` | No | 7 | Backup retention period in days |
| `BACKUP_COMPRESSION` | No | true | Enable backup compression |
| `BACKUP_STORAGE_PATH` | No | backups/ | Backup storage path |

### Email Configuration (Optional)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SMTP_HOST` | No | - | SMTP server hostname |
| `SMTP_PORT` | No | 587 | SMTP server port |
| `SMTP_USER` | No | - | SMTP username |
| `SMTP_PASSWORD` | No | - | SMTP password |
| `SMTP_USE_TLS` | No | true | Use TLS for SMTP |

## Environment-Specific Configurations

### Development Environment

```bash
ENVIRONMENT=development
DEBUG=true
RELOAD=true
LOG_LEVEL=DEBUG
DATABASE_URL=postgresql://safe_user:safe_password@localhost:5432/safe_dev
REDIS_URL=redis://localhost:6379/0
API_HOST=0.0.0.0
API_PORT=8000
```

### Testing Environment

```bash
ENVIRONMENT=testing
DEBUG=false
RELOAD=false
LOG_LEVEL=INFO
DATABASE_URL=postgresql://safe_user:safe_password@localhost:5432/safe_test
REDIS_URL=redis://localhost:6379/1
API_HOST=127.0.0.1
API_PORT=8001
```

### Production Environment

```bash
ENVIRONMENT=production
DEBUG=false
RELOAD=false
LOG_LEVEL=INFO
DATABASE_URL=postgresql://prod_user:secure_password@db.example.com:5432/safe_prod
REDIS_URL=redis://redis.example.com:6379/0
API_HOST=0.0.0.0
API_PORT=8000
SECRET_KEY=your-very-secure-secret-key-here
```

## Security Best Practices

1. **Never commit `.env` files to version control**
   - Add `.env` to `.gitignore`
   - Use `.env.example` or `.env.template` for reference

2. **Use strong secret keys**
   - Generate random keys with at least 32 characters
   - Use different keys for different environments

3. **Rotate secrets regularly**
   - Change API keys and passwords periodically
   - Update configuration files accordingly

4. **Limit access to production secrets**
   - Use secret management systems in production
   - Restrict access to environment files

## Troubleshooting

### Common Issues

1. **Database connection failed**
   - Check if DATABASE_URL format is correct
   - Verify database server is running
   - Ensure credentials are correct

2. **Redis connection failed**
   - Check if REDIS_URL format is correct
   - Verify Redis server is running
   - Check firewall settings

3. **API won't start**
   - Verify required variables are set
   - Check for syntax errors in `.env` file
   - Run validation script

4. **Frontend can't connect to API**
   - Check VITE_API_BASE_URL matches API configuration
   - Verify CORS settings are correct

### Validation Script

Use the validation script to check your configuration:

```bash
# Basic validation
./config/validate-env.sh

# Show help
./config/validate-env.sh --help
```

The script will:
- Check if `.env` file exists
- Validate variable formats
- Test database and Redis connectivity
- Provide detailed error messages

## Additional Resources

- [Docker Environment Variables](https://docs.docker.com/compose/environment-variables/)
- [FastAPI Environment Variables](https://fastapi.tiangolo.com/advanced/settings/)
- [Vite Environment Variables](https://vitejs.dev/guide/env-and-mode.html)
- [AutoGen Configuration](https://microsoft.github.io/autogen/docs/topics/groupchat)