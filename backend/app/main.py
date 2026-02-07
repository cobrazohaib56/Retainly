import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1 import router as api_router
from app.lifespan import lifespan

# Configure logging

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Retainly API",
    description="API for processing invoice/receipt images and extracting InvoiceTotal, TotalDiscount using Azure Prebuilt Invoice model",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"📥 {request.method} {request.url.path} - Origin: {request.headers.get('origin', 'N/A')}")
    response = await call_next(request)
    logger.info(f"📤 {request.method} {request.url.path} - Status: {response.status_code}")
    return response

# OPTIONS handler for CORS preflight
@app.options("/{full_path:path}")
async def options_handler(request: Request):
    return {"message": "OK"}

# Include API routers
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Retainly API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
