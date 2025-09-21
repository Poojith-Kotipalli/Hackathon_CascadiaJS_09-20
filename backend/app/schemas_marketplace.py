from __future__ import annotations
from typing import Literal, List, Optional
from uuid import UUID
from decimal import Decimal
from pydantic import BaseModel, Field

Severity = Literal["critical","high","medium","low"]
ListingStatus = Literal["Active","Flagged","Banned"]

class ListingCreate(BaseModel):
    seller_id: str
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=10_000)
    category: Optional[str] = None
    price: Optional[Decimal] = None
    inventory: Optional[int] = 0
    image_url: Optional[str] = None

class ListingUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    price: Optional[Decimal] = None
    inventory: Optional[int] = None
    image_url: Optional[str] = None

class ListingOut(BaseModel):
    id: UUID
    seller_id: str
    title: str
    description: str
    category: Optional[str]
    price: Optional[Decimal]
    inventory: Optional[int]
    image_url: Optional[str]
    status: ListingStatus
    last_checked_at: Optional[str]
    created_at: str
    updated_at: str

class BanRequest(BaseModel):
    listing_id: UUID
    reason: str
    evidence_top_rules: List[str] = []

class ReinstateRequest(BaseModel):
    listing_id: UUID

class AppealCreate(BaseModel):
    listing_id: UUID
    seller_id: str
    message: str

class AppealResolve(BaseModel):
    resolution_note: Optional[str] = None
    approve: bool = False  # if True -> reinstate listing

# Lightweight type for queue recheck
class RecheckRequest(BaseModel):
    listing_id: UUID
