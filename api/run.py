"""
Development Server Startup Script

This script starts the SAFE-BMAD API development server with proper configuration.
"""

import os
import sys
import logging
import asyncio
from pathlib import Path

# Add app directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(current_dir.parent / "shared"))

import uvicorn
from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse

# Import application
from app.api.v1.api import api_router
from app.core.config import get_settings
from shared.utils.logger import setup_logging
from app.db.database import create_database_engines, close_database_connections

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()


def create_app() -> FastAPI:
    """Create FastAPI application"""
    app = FastAPI(
        title="S3DA2 - SAFE BMAD System API",
        description="S3DA2 SAFE BMAD System with S-A-F-E-R Agent Framework - Multi-Agent Emergency Response System",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        contact={
            "name": "SAFE-BMAD Team",
            "email": "team@safe-bmad.com",
        },
        license_info={
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT",
        }
    )

    # Include API routes
    app.include_router(api_router, prefix=settings.api_prefix)

    # Add health check endpoints
    @app.get("/", tags=["Root"])
    async def root():
        """Root endpoint with basic information"""
        return {
            "message": "Welcome to S3DA2 - SAFE BMAD System API",
            "version": "1.0.0",
            "description": "Multi-Agent Emergency Response System with S-A-F-E-R Framework",
            "api_version": "v1",
            "api_prefix": settings.api_prefix,
            "documentation": {
                "swagger": f"{settings.api_prefix}/docs",
                "redoc": f"{settings.api_prefix}/redoc",
                "openapi": f"{settings.api_prefix}/openapi.json"
            },
            "health_checks": {
                "health": f"{settings.api_prefix}/health/health",
                "ready": f"{settings.api_prefix}/health/ready",
                "version": f"{settings.api_prefix}/health/version"
            },
            "endpoints": {
                "users": f"{settings.api_prefix}/users",
                "scenarios": f"{settings.api_prefix}/scenarios",
                "agents": f"{settings.api_prefix}/agents"
            }
        }

    # Custom docs endpoint with additional information
    @app.get("/docs-enhanced", include_in_schema=False)
    async def custom_swagger_ui_html():
        """Enhanced Swagger UI with additional documentation"""
        html_content = get_swagger_ui_html(
            openapi_url=f"{settings.api_prefix}/openapi.json",
            title=f"{settings.app_title} - Swagger UI",
            oauth2_redirect_url="/docs/oauth2-redirect",
            swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
            swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
        )

        # Add custom content
        custom_content = """
        <div class="swagger-ui">
            <div class="information-container" style="margin-top: 20px; padding: 20px; background-color: #f8f9fa; border-radius: 5px;">
                <h3>🚀 S3DA2 - SAFE BMAD System API Documentation</h3>
                <p><strong>Multi-Agent Emergency Response System with S-A-F-E-R Framework</strong></p>

                <h4>📖 Getting Started</h4>
                <ol>
                    <li>Use the <a href="#/health/health_health">Health Check</a> endpoints to verify API status</li>
                    <li>Create a user account using the <a href="#/users/users_post">POST /users</a> endpoint</li>
                    <li>Create emergency scenarios using the <a href="#/scenarios/scenarios_post">POST /scenarios</a> endpoint</li>
                    <li>Deploy S-A-F-E-R agents using the <a href="#/agents/agents_post">POST /agents</a> endpoint</li>
                </ol>

                <h4>🤖 S-A-F-E-R Agent Framework</h4>
                <ul>
                    <li><strong>S</strong> - Searcher: Information gathering and reconnaissance</li>
                    <li><strong>A</strong> - Analyst: Data analysis and situation assessment</li>
                    <li><strong>F</strong> - Frontline: Tactical response and field operations</li>
                    <li><strong>E</strong> - Executive: Strategic decision making and coordination</li>
                    <li><strong>E</strong> - Evaluator: Performance assessment and learning</li>
                </ul>

                <h4>🔧 API Features</h4>
                <ul>
                    <li>RESTful API design with proper HTTP status codes</li>
                    <li>Comprehensive request/response schemas with validation</li>
                    <li>Pagination support for list endpoints</li>
                    <li>Advanced filtering and search capabilities</li>
                    <li>JWT-based authentication and authorization</li>
                    <li>Real-time health monitoring and metrics</li>
                </ul>

                <h4>📊 Monitoring & Health</h4>
                <ul>
                    <li><code>GET {api_prefix}/health/health</code> - Basic health check</li>
                    <li><code>GET {api_prefix}/health/ready</code> - Readiness check with dependencies</li>
                    <li><code>GET {api_prefix}/health/metrics</code> - System and application metrics</li>
                    <li><code>GET {api_prefix}/health/version</code> - Version information</li>
                </ul>

                <p><em>For detailed API documentation, see the endpoints below.</em></p>
            </div>
        </div>
        """.format(api_prefix=settings.api_prefix)

        # Insert custom content into HTML
        html_content = html_content.replace(
            '<div id="swagger-ui">',
            custom_content + '<div id="swagger-ui">'
        )

        return HTMLResponse(content=html_content)

    return app


async def main():
    """Main function to start the application"""
    logger.info("Starting S3DA2 - SAFE BMAD API Development Server")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"API host: {settings.api_host}")
    logger.info(f"API port: {settings.api_port}")
    logger.info(f"API prefix: {settings.api_prefix}")

    try:
        # Initialize database connections
        logger.info("Initializing database connections...")
        create_database_engines()

        # Create application
        app = create_app()

        # Start server
        config = uvicorn.Config(
            app,
            host=settings.api_host,
            port=settings.api_port,
            reload=settings.reload,
            log_level=settings.log_level.lower(),
            access_log=True,
            use_colors=True
        )

        server = uvicorn.Server(config)
        logger.info(f"Server starting on http://{settings.api_host}:{settings.api_port}")
        logger.info(f"Swagger UI available at: http://{settings.api_host}:{settings.api_port}{settings.api_prefix}/docs")
        logger.info(f"Enhanced docs available at: http://{settings.api_host}:{settings.api_port}/docs-enhanced")
        logger.info(f"ReDoc available at: http://{settings.api_host}:{settings.api_port}{settings.api_prefix}/redoc")

        await server.serve()

    except KeyboardInterrupt:
        logger.info("Shutting down server...")
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}")
        raise
    finally:
        # Cleanup
        logger.info("Closing database connections...")
        await close_database_connections()
        logger.info("Server shutdown complete")


if __name__ == "__main__":
    # Set event loop policy for macOS
    if sys.platform == "darwin":
        import platform
        if platform.release() >= "22.0":  # macOS 12.0+
            asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())

    # Run the application
    asyncio.run(main())