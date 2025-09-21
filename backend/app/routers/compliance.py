from fastapi import APIRouter, HTTPException
import hashlib

from ..schemas import ComplianceCheckRequest, ComplianceCheckResponse
from ..services.compliance_engine import ComplianceEngine
from ..utils.cache import compliance_cache

# Multi-agent coordinator + alerts
from ..services.agents.coordinator import CoordinatorAgent
from ..services.alerts.twilio_alerts import send_alerts_if_needed

router = APIRouter()

# Single-engine for /check
compliance_engine = ComplianceEngine()
# Coordinator for /check/agents
coordinator = CoordinatorAgent()

@router.post("/check", response_model=ComplianceCheckResponse)
async def check_compliance(request: ComplianceCheckRequest):
    """
    Single-engine compliance path (legacy) — keeps existing behavior.
    """
    cache_key = hashlib.md5(f"{request.text}:{request.check_type}".encode()).hexdigest()

    cached = compliance_cache.get(cache_key)
    if cached:
        return cached

    try:
        result = await compliance_engine.check_compliance(request.text, request.check_type)
        response = ComplianceCheckResponse(
            compliant=result["compliant"],
            score=result.get("score"),
            violations=result["violations"],
            suggestions=result.get("suggestions", []),
            model_used=request.check_type,
            latency_ms=result.get("latency_ms", 0),
        )
        compliance_cache.set(cache_key, response)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/check/agents", response_model=ComplianceCheckResponse)
async def check_compliance_agents(request: ComplianceCheckRequest):
    """
    Multi-agent path: Coordinator runs domain agents and unifies output.
    Also triggers Twilio alerts based on severity (gated by ENABLE_ALERTS).
    """
    cache_key = hashlib.md5(f"agents:{request.text}:{request.check_type}".encode()).hexdigest()

    cached = compliance_cache.get(cache_key)
    if cached:
        return cached

    try:
        synth = await coordinator.run(text=request.text, check_type=request.check_type)
        response = ComplianceCheckResponse(
            compliant=synth.get("compliant", False),
            score=None,  # avoid conflicting with single-engine scoring
            violations=synth.get("violations", []),
            suggestions=synth.get("suggestions", []),
            model_used="coordinator:" + (request.check_type or ""),
            latency_ms=0,
        )

        # Fire alerts based on severity (critical/high/etc.)
        await send_alerts_if_needed(original_text=request.text, unified_result=synth)

        compliance_cache.set(cache_key, response)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/regulations")
async def get_regulations():
    return {
        "regulations": [
            {
                "name": "FDA",
                "description": "Food and Drug Administration",
                "categories": ["Health Claims", "Dietary Supplements", "Cosmetics", "Medical Devices"],
            },
            {
                "name": "FTC",
                "description": "Federal Trade Commission",
                "categories": ["Truth in Advertising", "Endorsements", "Warranties"],
            },
            {
                "name": "CPSC",
                "description": "Consumer Product Safety Commission",
                "categories": ["Children's Products", "Hazardous Substances", "Flammability"],
            },
        ]
    }

@router.get("/test")
async def test_compliance():
    """Quick test endpoint"""
    test_cases = [
        "This toy is perfect for children",
        "This supplement cures diabetes and is FDA approved",
        "100% guaranteed to work or your money back",
    ]
    results = []
    for text in test_cases:
        result = await compliance_engine.check_compliance(text, "realtime")
        results.append({
            "text": text[:50] + "...",
            "score": result.get("score"),
            "violations": len(result.get("violations", [])),
        })
    return {"test_results": results}
