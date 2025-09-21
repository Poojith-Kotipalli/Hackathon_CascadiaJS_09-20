from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean, JSON
from sqlalchemy.sql import func
from .database import Base

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    price = Column(Float)
    category = Column(String(100))
    seller_id = Column(String(100))
    image_url = Column(String(500))
    
    # Compliance fields
    compliance_score = Column(Float, default=100.0)
    compliance_status = Column(String(50), default="pending")  # pending, compliant, violation, under_review
    violations = Column(JSON, default=[])
    last_checked = Column(DateTime, server_default=func.now())
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

class ComplianceCheck(Base):
    __tablename__ = "compliance_checks"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer)
    check_type = Column(String(50))  # realtime, full, image
    result = Column(JSON)
    model_used = Column(String(50))
    latency_ms = Column(Float)
    created_at = Column(DateTime, server_default=func.now())