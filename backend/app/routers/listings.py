from __future__ import annotations
from fastapi import APIRouter, HTTPException, Query
from uuid import uuid4, UUID
from typing import Optional, List
import json

# POOL NOTE: adapt this import to your pool helper
# e.g., from app.database import pool  OR  from app.database import get_pool
from app.database import pool  # adjust if named differently

from app.schemas_marketplace import ListingCreate, ListingUpdate, ListingOut, RecheckRequest
from app.services.queue import enqueue_recheck

router = APIRouter(prefix="/products", tags=["products"])

async def _row_to_listing(row) -> ListingOut:
    return ListingOut(
        id=row["id"], seller_id=row["seller_id"], title=row["title"], description=row["description"],
        category=row["category"], price=row["price"], inventory=row["inventory"],
        image_url=row["image_url"], status=row["status"],
        last_checked_at=row["last_checked_at"].isoformat() if row["last_checked_at"] else None,
        created_at=row["created_at"].isoformat(), updated_at=row["updated_at"].isoformat()
    )

@router.post("", response_model=ListingOut)
async def create_listing(body: ListingCreate):
    new_id = uuid4()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO listings(id, seller_id, title, description, category, price, inventory, image_url,
                                 status, last_checked_at, created_at, updated_at)
            VALUES($1,$2,$3,$4,$5,$6,$7,$8,'Active', NULL, NOW(), NOW())
            """,
            new_id, body.seller_id, body.title, body.description, body.category, body.price,
            body.inventory, body.image_url
        )
    # fire-and-forget first scan
    await enqueue_recheck(new_id)
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM listings WHERE id=$1", new_id)
    return await _row_to_listing(row)

@router.get("", response_model=List[ListingOut])
async def list_listings(
    status: Optional[str] = Query(None),
    seller_id: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    limit: int = 50,
    offset: int = 0
):
    where = []
    params = []
    if status:
        where.append("status = $" + str(len(params)+1)); params.append(status)
    if seller_id:
        where.append("seller_id = $" + str(len(params)+1)); params.append(seller_id)
    if q:
        where.append("(title ILIKE $" + str(len(params)+1) + " OR description ILIKE $" + str(len(params)+1) + ")")
        params.append(f"%{q}%")
    sql = "SELECT * FROM listings"
    if where: sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY updated_at DESC LIMIT $" + str(len(params)+1) + " OFFSET $" + str(len(params)+2)
    params.extend([limit, offset])
    async with pool.acquire() as conn:
        rows = await conn.fetch(sql, *params)
    return [await _row_to_listing(r) for r in rows]

@router.get("/{listing_id}", response_model=ListingOut)
async def get_listing(listing_id: UUID):
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM listings WHERE id=$1", listing_id)
    if not row: raise HTTPException(404, "Listing not found")
    return await _row_to_listing(row)

@router.patch("/{listing_id}", response_model=ListingOut)
async def update_listing(listing_id: UUID, body: ListingUpdate):
    fields = []
    params = []
    for k, v in body.model_dump(exclude_unset=True).items():
        fields.append(f"{k} = $" + str(len(params)+1))
        params.append(v)
    if not fields:
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM listings WHERE id=$1", listing_id)
        if not row: raise HTTPException(404, "Listing not found")
        return await _row_to_listing(row)
    params.extend([listing_id])
    async with pool.acquire() as conn:
        await conn.execute(
            f"UPDATE listings SET {', '.join(fields)}, updated_at=NOW() WHERE id=$" + str(len(params))
            , *params
        )
        row = await conn.fetchrow("SELECT * FROM listings WHERE id=$1", listing_id)
    if not row: raise HTTPException(404, "Listing not found")
    # enqueue recheck on edits
    await enqueue_recheck(listing_id)
    return await _row_to_listing(row)

@router.post("/{listing_id}/recheck")
async def recheck_listing(listing_id: UUID):
    await enqueue_recheck(listing_id)
    return {"ok": True}
