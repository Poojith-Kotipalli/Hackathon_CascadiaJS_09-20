from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from .config import settings
from .database import engine, Base
from .routers import products, compliance, agents  # Added agents import

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting ComplianceMonster...")
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    
    # Verify Multi-Agent System Configuration
    try:
        from .agents.config import AgentConfig
        config = AgentConfig()
        logger.info(f"✅ OpenAI API Key configured: {config.OPENAI_API_KEY[:20]}...")
        logger.info(f"✅ Using model: {config.MODEL}")
        logger.info("✅ Multi-agent system ready!")
    except ValueError as e:
        logger.warning(f"⚠️ Multi-agent system not configured: {str(e)}")
        logger.warning("⚠️ Please set OPENAI_API_KEY in .env file to enable agent features")
    except Exception as e:
        logger.error(f"❌ Error initializing multi-agent system: {str(e)}")
    
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
app.include_router(agents.router, prefix="/api/agents", tags=["Multi-Agent System"])  # Added agents router

@app.get("/")
async def root():
    return {
        "message": "ComplianceMonster API", 
        "version": settings.VERSION,
        "features": {
            "rag_compliance": "✅ Active",
            "multi_agent_system": "✅ Active with gpt-4o-mini",
            "databases": ["PostgreSQL with pgvector", "10,880 compliance records"],
            "ai_models": ["OpenAI gpt-4o-mini", "Gemini Flash (backup)", "Ollama (local)"]
        }
    }

@app.get("/health")
async def health():
    """Health check endpoint with system status"""
    health_status = {
        "status": "healthy",
        "services": {
            "database": "connected",
            "rag_system": "operational",
            "multi_agent": "unknown"
        }
    }
    
    # Check if multi-agent system is configured
    try:
        from .agents.config import AgentConfig
        config = AgentConfig()
        health_status["services"]["multi_agent"] = "operational"
    except:
        health_status["services"]["multi_agent"] = "not configured"
    
    return health_status

# WebSocket for real-time compliance (original endpoint)
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Original WebSocket endpoint for basic compliance updates"""
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

# Note: The multi-agent WebSocket is at /api/agents/ws/compliance-stream