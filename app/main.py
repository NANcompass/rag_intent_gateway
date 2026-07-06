"""
RAG Intent Gateway - Main FastAPI Application.

This is the entry point for the RAG intent processing pipeline.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.core.config import settings
from app.api import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    print(f"\n🚀 {settings.app_name} v{settings.app_version} is starting...")
    print(f"📡 API prefix: {settings.api_prefix}")
    print(f"🤖 Using model: {settings.openai_model}")
    yield
    # Shutdown
    print(f"\n👋 {settings.app_name} is shutting down...")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
## RAG Intent Gateway

A sophisticated RAG (Retrieval Augmented Generation) pre-processing pipeline that:

- **Intent Classification**: Determines if a query needs knowledge base retrieval (RAG) or is casual conversation (CHITCHAT)
- **Context Resolution**: Resolves ambiguous references using conversation history
- **Query Rewriting**: Splits complex queries into sub-queries
- **Query Expansion**: Generates synonym variants for better retrieval

### Key Features

1. Single LLM call for efficient processing
2. Structured JSON output with Pydantic validation
3. Multi-path retrieval query generation
4. Support for multi-turn conversation context
    """,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(api_router, prefix=settings.api_prefix)


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint - API information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "redoc": "/redoc",
        "api_prefix": settings.api_prefix
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.app_version
    }


def main():
    """Run the application with uvicorn."""
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )


if __name__ == "__main__":
    main()
