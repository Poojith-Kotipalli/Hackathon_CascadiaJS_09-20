from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class ProductBase(BaseModel):
    title: str
    description: Optional[str] = None
    price: Optional[float] = None
    category: Optional[str] = None
    seller_id: Optional[str] = None
    image_url: Optional[str] = None

class ProductCreate(ProductBase):
    pass

class Product(ProductBase):
    id: int
    compliance_score: float
    compliance_status: str
    violations: List[Dict[str, Any]]
    last_checked: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True

class ComplianceCheckRequest(BaseModel):
    text: str
    check_type: str = "realtime"  # realtime, full, image

class ComplianceCheckResponse(BaseModel):
    compliant: bool
    score: float
    violations: List[Dict[str, Any]]
    suggestions: List[str]
    model_used: str
    latency_ms: float