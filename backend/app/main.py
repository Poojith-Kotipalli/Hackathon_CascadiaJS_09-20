from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from .config import settings
from .database import engine, Base
from .routers import products, compliance

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting ComplianceMonster...")
    Base.metadata.create_all(bind=engine)
    yield
    logger.info("👋 Shutting down...")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(products.router, prefix="/api/products", tags=["products"])
app.include_router(compliance.router, prefix="/api/compliance", tags=["compliance"])

@app.get("/")
async def root():
    return {"message": "ComplianceMonster API", "version": settings.VERSION}

@app.get("/health")
async def health():
    return {"status": "healthy"}

# WebSocket for real-time compliance
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            # Process and send back compliance results
            await websocket.send_json({
                "type": "compliance_update",
                "score": 85.5,
                "status": "checking"
            })
    except WebSocketDisconnect:
        logger.info("Client disconnected")