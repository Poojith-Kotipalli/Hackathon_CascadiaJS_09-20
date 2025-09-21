from __future__ import annotations
from fastapi import APIRouter
from uuid import uuid4, UUID
import json

from app.database import pool  # POOL NOTE
from app.schemas_marketplace import BanRequest, ReinstateRequest

router = APIRouter(tags=["moderation"])

@router.get("/flags")
async def get_flags():
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT f.id, f.listing_id, f.severity, f.reason, f.created_at,
                   l.title, l.seller_id, l.status
            FROM flags f
            JOIN listings l ON l.id=f.listing_id
            WHERE f.resolved_at IS NULL
            ORDER BY f.created_at DESC
        """)
    return [dict(r) for r in rows]

@router.post("/moderation/ban")
async def ban_listing(req: BanRequest):
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO bans(id, listing_id, reason, evidence_top_rules, created_at)
            VALUES($1,$2,$3,$4::jsonb,NOW())
        """, uuid4(), req.listing_id, req.reason, json.dumps(req.evidence_top_rules))
        await conn.execute("UPDATE listings SET status='Banned', updated_at=NOW() WHERE id=$1", req.listing_id)
        await conn.execute("UPDATE flags SET resolved_at=NOW() WHERE listing_id=$1 AND resolved_at IS NULL", req.listing_id)
    return {"ok": True}

@router.post("/moderation/reinstate")
async def reinstate_listing(req: ReinstateRequest):
    async with pool.acquire() as conn:
        await conn.execute("UPDATE listings SET status='Active', updated_at=NOW() WHERE id=$1", req.listing_id)
        await conn.execute("""
            UPDATE bans SET lifted_at=NOW()
            WHERE listing_id=$1 AND lifted_at IS NULL
        """, req.listing_id)
    return {"ok": True}
