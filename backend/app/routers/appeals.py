from __future__ import annotations
from fastapi import APIRouter, HTTPException
from uuid import uuid4, UUID

from app.database import pool  # POOL NOTE
from app.schemas_marketplace import AppealCreate, AppealResolve

router = APIRouter(prefix="/appeals", tags=["appeals"])

@router.post("")
async def create_appeal(a: AppealCreate):
    async with pool.acquire() as conn:
        # ensure listing exists
        row = await conn.fetchrow("SELECT id FROM listings WHERE id=$1", a.listing_id)
        if not row: raise HTTPException(404, "Listing not found")
        await conn.execute("""
            INSERT INTO appeals(id, listing_id, seller_id, message, status, created_at)
            VALUES($1,$2,$3,$4,'Open',NOW())
        """, uuid4(), a.listing_id, a.seller_id, a.message)
    return {"ok": True}

@router.get("")
async def list_appeals(status: str | None = None):
    sql = "SELECT * FROM appeals"
    params = []
    if status:
        sql += " WHERE status=$1"
        params.append(status)
    sql += " ORDER BY created_at DESC"
    async with pool.acquire() as conn:
        rows = await conn.fetch(sql, *params)
    return [dict(r) for r in rows]

@router.post("/{appeal_id}/resolve")
async def resolve_appeal(appeal_id: UUID, body: AppealResolve):
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE appeals SET status='Resolved', resolved_at=NOW(), resolution_note=$2
            WHERE id=$1
        """, appeal_id, body.resolution_note)
    # reinstate optional
    if body.approve:
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT listing_id FROM appeals WHERE id=$1", appeal_id)
            if row:
                await conn.execute("UPDATE listings SET status='Active', updated_at=NOW() WHERE id=$1", row["listing_id"])
    return {"ok": True}
