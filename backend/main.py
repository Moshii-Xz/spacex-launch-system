import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers import health, launches, sync

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title       = "SpaceX Launch Tracker API",
    description = (
        "API REST para consultar y sincronizar datos de lanzamientos espaciales de SpaceX. "
        "Los datos son almacenados en Amazon DynamoDB y actualizados automáticamente cada 6 horas "
        "mediante una función AWS Lambda. También es posible forzar la sincronización manualmente."
    ),
    version     = "1.0.0",
    contact     = {
        "name": "SpaceX Launch System",
        "url":  "https://github.com/Moshii-Xz/spacex-launch-system",
    },
    license_info = {
        "name": "MIT",
    },
    docs_url    = "/docs",    # Swagger UI
    redoc_url   = "/redoc",   # ReDoc
    openapi_url = "/openapi.json",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
origins = os.environ.get("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins     = origins,
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(health.router)
app.include_router(launches.router, prefix="/api/v1")
app.include_router(sync.router,     prefix="/api/v1")


# ── Root ──────────────────────────────────────────────────────────────────────
@app.get("/", include_in_schema=False)
def root():
    return {
        "service": "SpaceX Launch Tracker API",
        "version": "1.0.0",
        "docs":    "/docs",
        "redoc":   "/redoc",
    }
