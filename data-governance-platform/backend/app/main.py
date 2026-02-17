"""
Data Governance Platform API application.

This is the main FastAPI application module that initializes the
Data Governance Platform API, configures CORS middleware, registers
API routers, and provides health check endpoints.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import init_db
from app.api import datasets, git, subscriptions, semantic, orchestration

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Policy-as-Code Data Governance Platform with Federated Governance",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    """
    Initialize database on startup.

    Creates all database tables if they don't exist and performs
    any necessary initialization for the application.
    """
    print("Initializing database...")
    init_db()
    print("Database initialized successfully!")


# Include routers
app.include_router(datasets.router, prefix=settings.API_V1_PREFIX)
app.include_router(git.router, prefix=settings.API_V1_PREFIX)
app.include_router(subscriptions.router)
app.include_router(semantic.router, prefix=settings.API_V1_PREFIX)
app.include_router(orchestration.router, prefix=settings.API_V1_PREFIX)


@app.get("/")
def root():
    """
    Root endpoint.

    Returns:
        dict: API information including name, version, and docs URL.
    """
    return {
        "message": "Data Governance Platform API",
        "version": settings.APP_VERSION,
        "docs": "/api/docs"
    }


@app.get("/health")
def health_check():
    """
    Health check endpoint.

    Returns:
        dict: Health status, service name, and version information.
    """
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
