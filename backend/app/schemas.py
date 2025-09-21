from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from enum import Enum

# Enums for standardized values
class ComplianceStatus(str, Enum):
    APPROVED = "APPROVED"
    DENIED = "DENIED"
    REVIEW = "REVIEW"
    PENDING = "PENDING"
    APPEALED = "APPEALED"

class RiskLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class AgentType(str, Enum):
    CLASSIFIER = "ProductClassifier"
    CPSC = "CPSC_Safety_Expert"
    FDA_FOOD = "FDA_Food_Inspector"
    FDA_DRUG = "FDA_Drug_Analyst"
    FTC = "FTC_Marketing_Auditor"
    ELECTRONICS = "Electronics_Safety_Expert"
    MEDICAL = "Medical_Device_Specialist"
    SYNTHESIZER = "ComplianceSynthesizer"

# Product Schemas
class ProductBase(BaseModel):
    title: str
    description: Optional[str] = None
    price: Optional[float] = None
    category: Optional[str] = None
    seller_id: Optional[str] = None
    image_url: Optional[str] = None
    ingredients: Optional[str] = None  # Added for FDA checks
    claims: Optional[List[str]] = []   # Added for marketing claims
    certifications: Optional[List[str]] = []  # Added for electronics/safety

class ProductCreate(ProductBase):
    pass

class Product(ProductBase):
    id: int
    compliance_score: float
    compliance_status: ComplianceStatus
    risk_level: RiskLevel
    violations: List[Dict[str, Any]]
    last_checked: datetime
    created_at: datetime
    flagged_reason: Optional[str] = None  # AI-generated explanation
    agents_consulted: List[str] = []  # Which agents reviewed this
    
    class Config:
        from_attributes = True

# Agent-specific response schemas
class AgentFinding(BaseModel):
    agent_name: AgentType
    timestamp: datetime
    violations_found: List[str] = []
    severity: RiskLevel
    compliance_score: float = Field(ge=0, le=100)
    specific_concerns: Dict[str, Any] = {}
    recommendations: List[str] = []
    confidence: float = Field(ge=0, le=1.0)

class ClassifierResult(BaseModel):
    category: str
    risk_level: RiskLevel
    recommended_agents: List[AgentType]
    confidence: float

class CPSCResult(BaseModel):
    lead_content_ppm: Optional[float] = None
    choking_hazard: bool = False
    battery_safety: bool = True
    flammability_compliant: bool = True
    recall_matches: List[str] = []
    age_appropriate: Optional[str] = None
    violations: List[str] = []
    severity: RiskLevel
    compliance_score: float

class FDAFoodResult(BaseModel):
    undeclared_allergens: List[str] = []
    labeling_issues: List[str] = []
    false_claims: List[str] = []
    banned_ingredients: List[str] = []
    organic_verified: Optional[bool] = None
    violations: List[str] = []
    severity: RiskLevel
    compliance_score: float

class FDADrugResult(BaseModel):
    violations_found: List[str] = []
    banned_ingredients: List[str] = []
    false_claims: List[str] = []
    hidden_drugs: List[str] = []
    severity: RiskLevel
    compliance_score: float
    requires_prescription: bool = False

# Compliance Check Schemas
class ComplianceCheckRequest(BaseModel):
    text: Optional[str] = None  # For text-based checks
    product_id: Optional[int] = None  # For product-based checks
    check_type: Literal["realtime", "full", "batch", "image"] = "full"
    agents_to_use: Optional[List[AgentType]] = None  # Specify agents
    confidence_threshold: float = 0.8  # For human-in-loop trigger

class ComplianceCheckResponse(BaseModel):
    # Overall results
    compliant: bool
    status: ComplianceStatus
    overall_score: float = Field(ge=0, le=100)
    risk_level: RiskLevel
    
    # Agent-specific results
    classifier_result: Optional[ClassifierResult] = None
    agent_findings: List[AgentFinding] = []
    
    # Violations and recommendations
    violations: List[Dict[str, Any]]
    critical_violations: List[str] = []  # Most severe issues
    suggestions: List[str]
    required_actions: List[str] = []  # Mandatory fixes
    
    # Reasoning and confidence
    ai_reasoning: str  # Detailed explanation
    confidence_score: float = Field(ge=0, le=1.0)
    requires_human_review: bool = False
    
    # Metadata
    agents_consulted: List[AgentType]
    conversation_turns: int = 0
    model_used: str = "gpt-4o-mini"
    processing_time_ms: float
    tokens_used: Optional[int] = None
    estimated_cost: Optional[float] = None
    
    # Audit trail
    conversation_id: Optional[str] = None  # For retrieving full chat
    timestamp: datetime = Field(default_factory=datetime.now)

# Batch Processing Schemas
class BatchComplianceRequest(BaseModel):
    product_ids: List[int]
    priority: Literal["high", "normal", "low"] = "normal"
    parallel_processing: bool = True
    max_concurrent: int = Field(default=10, le=20)

class BatchComplianceResponse(BaseModel):
    batch_id: str
    total_products: int
    processed: int
    approved: int
    denied: int
    review_needed: int
    results: List[ComplianceCheckResponse]
    processing_time_seconds: float
    total_cost: float

# Appeals Schemas
class AppealCreate(BaseModel):
    product_id: int
    seller_id: str
    reason: str
    supporting_documents: Optional[List[str]] = []
    proposed_changes: Optional[Dict[str, Any]] = {}

class Appeal(AppealCreate):
    id: int
    status: Literal["pending", "reviewing", "approved", "rejected"] = "pending"
    submitted_at: datetime
    reviewed_at: Optional[datetime] = None
    reviewer_notes: Optional[str] = None
    original_violations: List[Dict[str, Any]]
    re_evaluation_result: Optional[ComplianceCheckResponse] = None
    
    class Config:
        from_attributes = True

class AppealResponse(BaseModel):
    appeal_id: int
    status: str
    message: str
    next_steps: Optional[List[str]] = None

# Seller Dashboard Schemas
class SellerComplianceStats(BaseModel):
    seller_id: str
    total_products: int
    compliant_products: int
    flagged_products: int
    pending_appeals: int
    compliance_rate: float
    common_violations: List[Dict[str, int]]  # violation_type: count
    risk_distribution: Dict[RiskLevel, int]
    last_updated: datetime

# Agent Conversation Schema (for debugging/audit)
class AgentConversation(BaseModel):
    conversation_id: str
    product_id: int
    messages: List[Dict[str, Any]]  # Full AG2 conversation
    agents_involved: List[AgentType]
    total_turns: int
    final_verdict: ComplianceStatus
    timestamp: datetime
    
    class Config:
        from_attributes = True

# Real-time monitoring schemas
class ComplianceAlert(BaseModel):
    alert_id: str
    severity: RiskLevel
    product_id: int
    seller_id: str
    violation_type: str
    message: str
    recommended_action: str
    created_at: datetime

# Webhook schemas for external integrations
class ComplianceWebhookPayload(BaseModel):
    event_type: Literal["product_flagged", "appeal_submitted", "compliance_updated"]
    product_id: int
    seller_id: str
    compliance_status: ComplianceStatus
    details: Dict[str, Any]
    timestamp: datetime

# Search and Filter schemas
class ComplianceSearchRequest(BaseModel):
    query: Optional[str] = None
    status: Optional[ComplianceStatus] = None
    risk_level: Optional[RiskLevel] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    seller_id: Optional[str] = None
    page: int = 1
    limit: int = Field(default=20, le=100)

class ComplianceSearchResponse(BaseModel):
    results: List[Product]
    total: int
    page: int
    pages: int
    facets: Dict[str, Dict[str, int]]  # For filters

# Cost tracking schema
class UsageReport(BaseModel):
    period_start: datetime
    period_end: datetime
    total_checks: int
    total_tokens: int
    total_cost: float
    cost_by_agent: Dict[AgentType, float]
    average_tokens_per_check: float
    high_risk_products_found: int