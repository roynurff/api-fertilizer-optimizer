"""
Fertilizer Distribution Route Optimizer — FastAPI Service
CVRPTW + ALNS (Adaptive Large Neighborhood Search)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import optimize
from app.core.config import settings

app = FastAPI(
    title="Fertilizer Route Optimizer API",
    description="CVRPTW + ALNS optimization service for fertilizer distribution routing",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ─── CORS — allow Laravel to call this service ────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ──────────────────────────────────────────────────────────────────
app.include_router(optimize.router, prefix="/api/v1", tags=["Optimization"])


@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "service": "Fertilizer Route Optimizer", "version": "1.0.0"}


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy"}
