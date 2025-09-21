from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import logging

from .config import settings
from .database import engine, Base
from .routers import products, compliance  # required

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting ComplianceMonster...")
    # Create tables on boot (OK for dev; switch to migrations for prod)
    Base.metadata.create_all(bind=engine)
    yield
    logger.info("👋 Shutting down...")

app = FastAPI(
    title=getattr(settings, "APP_NAME", "ComplianceMonster API"),
    version=getattr(settings, "VERSION", "0.1.0"),
    lifespan=lifespan,
)

# ---- Middlewares
# CORS: explicit locals + wildcard v0.dev previews
app.add_middleware(
    CORSMiddleware,
    allow_origins=getattr(settings, "CORS_ORIGINS", ["http://localhost:3000", "http://127.0.0.1:3000"]),
    allow_origin_regex=r"https://.*\.v0\.dev$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Response compression
app.add_middleware(GZipMiddleware, minimum_size=1024)
# Lock down hosts if provided; default permissive for dev
app.add_middleware(TrustedHostMiddleware, allowed_hosts=getattr(settings, "TRUSTED_HOSTS", ["*"]))

# ---- Routers (required)
app.include_router(products.router, prefix="/api/products", tags=["products"])
app.include_router(compliance.router, prefix="/api/compliance", tags=["compliance"])

# Optional routers: register if they exist
try:
    from .routers import moderation as _moderation
    app.include_router(_moderation.router, prefix="/api/moderation", tags=["moderation"])
except Exception as e:
    logger.info("Moderation router not enabled: %s", e)

try:
    from .routers import appeals as _appeals
    app.include_router(_appeals.router, prefix="/api/appeals", tags=["appeals"])
except Exception as e:
    logger.info("Appeals router not enabled: %s", e)

# ---- Health & meta
@app.get("/")
async def root():
    return {"message": "ComplianceMonster API", "version": getattr(settings, "VERSION", "0.1.0")}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/ready")
async def ready():
    return {"ok": True}

# ---- WebSocket (basic echo/progress stub)
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            _ = await websocket.receive_text()
            await websocket.send_json({"type": "compliance_update", "score": 85.5, "status": "checking"})
    except WebSocketDisconnect:
        logger.info("Client disconnected")
import os
ENABLE_MOD = os.getenv("ENABLE_MOD_ROUTERS", "false").lower() == "true"

if ENABLE_MOD:
    try:
        from .routers import moderation as _moderation
        app.include_router(_moderation.router, prefix="/api/moderation", tags=["moderation"])
    except Exception as e:
        logger.info("Moderation router not enabled: %s", e)

    try:
        from .routers import appeals as _appeals
        app.include_router(_appeals.router, prefix="/api/appeals", tags=["appeals"])
    except Exception as e:
        logger.info("Appeals router not enabled: %s", e)
