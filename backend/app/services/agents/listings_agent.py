from __future__ import annotations
from uuid import UUID, uuid4
import json
from typing import Optional, List

from app.database import pool  # POOL NOTE
from app.services.agents.dispatcher import route_targets_for_listing, run_coordinator_restricted
from app.services.alerts.twilio_alerts import send_alerts_if_needed  # already in your repo

async def scan_one(listing_id: UUID) -> dict:
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM listings WHERE id=$1", listing_id)
    if not row:
        return {"error": "not_found", "listing_id": str(listing_id)}

    text = f"{row['title']}\n{row['description']}".strip()
    image_url = row["image_url"]
    targets = await route_targets_for_listing(text=text, image_url=image_url, category=row["category"])
    # call coordinator constrained to those agents
    result = await run_coordinator_restricted(text=text, allowed_agents=targets)

    # persist compliance result
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO compliance_results(
                id, listing_id, route, compliant, severity, confidence, uses_context, score,
                violations, suggestions, top_rules, agent_summaries, created_at
            ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9::jsonb,$10::jsonb,$11::jsonb,$12::jsonb,NOW())
        """,
        uuid4(), listing_id, "listings_agent",
        result.get("compliant"), result.get("severity"), result.get("confidence"),
        result.get("uses_context"), max([a.get("score",0) for a in result.get("agent_summaries",[])] + [0]),
        json.dumps(result.get("violations",[])),
        json.dumps(result.get("suggestions",[])),
        json.dumps(result.get("top_rules",[])),
        json.dumps(result.get("agent_summaries",[])),
        )

        await conn.execute("UPDATE listings SET last_checked_at=NOW() WHERE id=$1", listing_id)

    sev = (result.get("severity") or "low").lower()
    if sev in ("high","critical"):
        reason = (result.get("violations") or ["Policy violation"])[0]
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO flags(id, listing_id, severity, reason, created_at)
                VALUES($1,$2,$3,$4,NOW())
            """, uuid4(), listing_id, sev, reason)
            await conn.execute("UPDATE listings SET status='Flagged', updated_at=NOW() WHERE id=$1", listing_id)
        await send_alerts_if_needed(sev, listing_id=str(listing_id), summary=reason)

    return result
