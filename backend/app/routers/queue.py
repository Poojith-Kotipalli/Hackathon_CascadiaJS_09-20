import asyncio
from uuid import UUID
from typing import Optional
from app.database import pool  # POOL NOTE
from app.services.agents.listings_agent import scan_one

_queue: asyncio.Queue[UUID] = asyncio.Queue()
_worker_started = False

async def enqueue_recheck(listing_id: UUID) -> None:
    await _queue.put(listing_id)

async def _queue_worker():
    while True:
        listing_id = await _queue.get()
        try:
            await scan_one(listing_id)
        except Exception as e:
            # log & continue
            print(f"[queue] error scanning {listing_id}: {e}")
        finally:
            _queue.task_done()

async def _periodic_scan(interval_seconds: int = 3600):
    while True:
        try:
            async with pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT id FROM listings
                    WHERE last_checked_at IS NULL
                       OR last_checked_at < NOW() - INTERVAL '24 hours'
                    ORDER BY last_checked_at NULLS FIRST
                    LIMIT 100
                """)
            for r in rows:
                await enqueue_recheck(r["id"])
        except Exception as e:
            print(f"[scanner] error scheduling scans: {e}")
        await asyncio.sleep(interval_seconds)

async def start_background_workers():
    global _worker_started
    if _worker_started: return
    _worker_started = True
    asyncio.create_task(_queue_worker())
    asyncio.create_task(_periodic_scan())
