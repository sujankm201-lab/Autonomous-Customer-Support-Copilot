import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .db import connect_db, close_db
from .routers import auth, users, tickets, chat, admin, rag, intent
from .middleware import log_requests_middleware
from .exceptions import setup_exception_handlers
from .logging_config import setup_logging
from .config import settings

# Initialize logging
setup_logging()
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="Autonomous Customer Support Copilot - Backend",
    description="Backend API for Customer Support Copilot",
    version="0.1.0",
)

# Setup exception handlers
setup_exception_handlers(app)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request logging middleware
app.middleware("http")(log_requests_middleware)

# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(tickets.router)
app.include_router(chat.router)
app.include_router(admin.router)
app.include_router(rag.router)
app.include_router(intent.router)


@app.on_event("startup")
async def startup():
    logger.info("Starting up application...")
    await connect_db()
    logger.info("Database connected successfully")


@app.on_event("shutdown")
async def shutdown():
    logger.info("Shutting down application...")
    await close_db()
    logger.info("Database connection closed")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Autonomous Customer Support Copilot - Backend API",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}