from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from typing import Dict, List, Optional
import json
from ..agents.orchestrator import ComplianceOrchestrator
from ..schemas import ProductCreate
from pydantic import BaseModel

router = APIRouter(prefix="/agents", tags=["Multi-Agent Compliance"])

# Initialize orchestrator (singleton)
orchestrator = ComplianceOrchestrator()

class ProductComplianceRequest(BaseModel):
    name: str
    description: str
    category: str = "general"
    price: float = 0.0
    ingredients: Optional[str] = None
    materials: Optional[str] = None
    warnings: Optional[str] = None
    age_range: Optional[str] = None
    certifications: Optional[str] = None

@router.post("/check-compliance")
async def check_compliance_with_agents(product: ProductComplianceRequest):
    """
    Run multi-agent compliance check on a product
    
    Returns detailed compliance analysis with agent reasoning chain
    """
    try:
        # Convert Pydantic model to dict
        product_dict = product.dict()
        
        # Run compliance check
        results = orchestrator.check_product_compliance(product_dict)
        
        return {
            "status": "success",
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.websocket("/ws/compliance-stream")
async def websocket_compliance_check(websocket: WebSocket):
    """
    WebSocket endpoint for streaming agent conversation in real-time
    """
    await websocket.accept()
    try:
        while True:
            # Receive product data
            data = await websocket.receive_text()
            product = json.loads(data)
            
            # Send initial acknowledgment
            await websocket.send_json({
                "type": "check_started",
                "message": "Initiating multi-agent compliance check...",
                "timestamp": datetime.now().isoformat()
            })
            
            # Run compliance check (for now, not real-time streaming)
            results = orchestrator.check_product_compliance(product)
            
            # Send agent messages one by one for animation effect
            for agent_msg in results.get("agent_reasoning_chain", []):
                await websocket.send_json({
                    "type": "agent_message",
                    "data": agent_msg
                })
                await asyncio.sleep(0.5)  # Slight delay for effect
            
            # Send final results
            await websocket.send_json({
                "type": "compliance_complete",
                "data": results
            })
            
    except WebSocketDisconnect:
        print("Client disconnected from WebSocket")
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })

@router.get("/test-agents")
async def test_agents():
    """
    Test endpoint to verify agents are working
    """
    test_product = {
        "name": "Test Children's Magnetic Building Toy",
        "description": "Colorful magnetic tiles with small powerful magnets for creative play",
        "category": "toys",
        "age_range": "3+",
        "warnings": "Contains small magnets",
        "price": 34.99
    }
    
    try:
        results = orchestrator.check_product_compliance(test_product)
        return {
            "status": "success",
            "message": "Multi-agent system is operational",
            "test_results": results
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Agent system error: {str(e)}",
            "troubleshooting": [
                "Check OPENAI_API_KEY in .env file",
                "Verify gpt-4o-mini model access",
                "Check internet connectivity",
                "Verify pyautogen installation"
            ]
        }

@router.get("/token-usage")
async def get_token_usage():
    """
    Get current token usage and cost estimate
    """
    usage = orchestrator.get_token_usage()
    return {
        "total_tokens_used": usage["total_tokens"],
        "total_compliance_checks": usage["total_checks"],
        "estimated_cost_usd": usage["estimated_cost"],
        "remaining_budget": 100.0 - usage["estimated_cost"],  # Assuming $100 budget
        "checks_remaining": int((100.0 - usage["estimated_cost"]) / 0.002)  # ~$0.002 per check
    }