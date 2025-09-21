from fastapi import APIRouter, Depends, HTTPException
from typing import List
import hashlib
from ..schemas import ComplianceCheckRequest, ComplianceCheckResponse
from ..services.compliance_engine import ComplianceEngine
from ..utils.cache import compliance_cache

router = APIRouter()
compliance_engine = ComplianceEngine()

@router.post("/check", response_model=ComplianceCheckResponse)
async def check_compliance(request: ComplianceCheckRequest):
    # Create cache key
    cache_key = hashlib.md5(f"{request.text}:{request.check_type}".encode()).hexdigest()
    
    # Check cache first
    cached_result = compliance_cache.get(cache_key)
    if cached_result:
        return cached_result
    
    try:
        # Run compliance check
        result = await compliance_engine.check_compliance(
            request.text,
            request.check_type
        )
        
        response = ComplianceCheckResponse(
            compliant=result["compliant"],
            score=result["score"],
            violations=result["violations"],
            suggestions=result.get("suggestions", []),
            model_used=request.check_type,
            latency_ms=result.get("latency_ms", 0)
        )
        
        # Cache the result
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
                "categories": ["Health Claims", "Dietary Supplements", "Cosmetics", "Medical Devices"]
            },
            {
                "name": "FTC", 
                "description": "Federal Trade Commission",
                "categories": ["Truth in Advertising", "Endorsements", "Warranties"]
            },
            {
                "name": "CPSC",
                "description": "Consumer Product Safety Commission", 
                "categories": ["Children's Products", "Hazardous Substances", "Flammability"]
            }
        ]
    }

@router.get("/test")
async def test_compliance():
    """Quick test endpoint"""
    test_cases = [
        "This toy is perfect for children",
        "This supplement cures diabetes and is FDA approved",
        "100% guaranteed to work or your money back"
    ]
    
    results = []
    for text in test_cases:
        result = await compliance_engine.check_compliance(text, "realtime")
        results.append({
            "text": text[:50] + "...",
            "score": result["score"],
            "violations": len(result["violations"])
        })
    
    return {"test_results": results}