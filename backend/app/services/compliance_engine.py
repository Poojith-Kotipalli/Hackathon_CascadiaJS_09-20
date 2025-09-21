import asyncio
import time
from typing import Any, Dict, List, Optional, Tuple

import asyncpg

try:
    from sentence_transformers import SentenceTransformer
except Exception:
    SentenceTransformer = None  # type: ignore

from ..config import settings
from .ai_router import AIRouter

VECTOR_DIM = 384
DEFAULT_TOP_K = 5
SIM_THRESHOLD = 0.25
EMB_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

TABLES = [
    "cpsc_recalls",
    "fda_drug_enforcement",
    "fda_food_enforcement",
    "fda_device_data",
    "fda_drug_labels",
    "electronics_compliance",
]

SELECT_CLAUSE = """
SELECT rule_text, 1 - (embedding <=> $1::vector) AS similarity, severity
FROM {table}
ORDER BY embedding <=> $1::vector
LIMIT $2
"""

class ComplianceEngine:
    def __init__(self):
        self._pool: Optional[asyncpg.Pool] = None
        self._embedder = None
        self.ai_router = AIRouter()

    async def _get_pool(self) -> asyncpg.Pool:
        if self._pool is None:
            if not settings.DATABASE_URL:
                raise RuntimeError("DATABASE_URL is not set.")
            self._pool = await asyncpg.create_pool(dsn=settings.DATABASE_URL)
        return self._pool

    def _get_embedder(self):
        if self._embedder is None:
            if SentenceTransformer is None:
                raise RuntimeError("Install: pip install sentence-transformers")
            self._embedder = SentenceTransformer(EMB_MODEL)
        return self._embedder

    def _embed(self, text: str) -> List[float]:
        model = self._get_embedder()
        v = model.encode(text, normalize_embeddings=True)
        return [float(x) for x in v]

    @staticmethod
    def _vector_literal(vec: List[float]) -> str:
        return "[" + ",".join(f"{x:.6f}" for x in vec) + "]"

    async def _search_table(self, pool: asyncpg.Pool, table: str, emb: List[float], top_k: int) -> List[Dict[str, Any]]:
        vec = self._vector_literal(emb)
        sql = SELECT_CLAUSE.format(table=table)
        async with pool.acquire() as conn:
            rows = await conn.fetch(sql, vec, top_k)
        return [{"rule_text": r["rule_text"], "similarity": float(r["similarity"]), "severity": r["severity"]} for r in rows]

    async def _retrieve(self, text: str, table: Optional[str], top_k: int) -> Tuple[List[Dict[str, Any]], float]:
        pool = await self._get_pool()
        emb = self._embed(text)
        if table:
            rows = await self._search_table(pool, table, emb, top_k)
            return rows, max((r["similarity"] for r in rows), default=0.0)

        tasks = [self._search_table(pool, t, emb, top_k) for t in TABLES]
        blocks = await asyncio.gather(*tasks)
        merged: List[Dict[str, Any]] = []
        for b in blocks:
            merged.extend(b)
        merged.sort(key=lambda r: r["similarity"], reverse=True)
        merged = merged[:top_k]
        return merged, max((r["similarity"] for r in merged), default=0.0)

    @staticmethod
    def _rules_block(rows: List[Dict[str, Any]]) -> str:
        if not rows:
            return "RULES:\n- (no relevant rules found)\n"
        lines = [f"- {r['rule_text']} (sim={r['similarity']:.3f}, sev={r.get('severity')})" for r in rows]
        return "RULES:\n" + "\n".join(lines) + "\n"

    async def analyze(self, text: str, check_type: Optional[str] = None, table: Optional[str] = None, top_k: int = DEFAULT_TOP_K) -> Dict[str, Any]:
        t0 = time.time()
        rows, max_sim = await self._retrieve(text, table, top_k)
        rules = self._rules_block(rows)

        # LEGACY prompt path for compatibility with previous pipelines
        prompt = (
            f"{rules}\n"
            "TASK: Determine whether the USER content is compliant. If violations exist, list them succinctly.\n"
            f"USER CONTENT:\n{text}"
        )
        parsed = await self.ai_router.legacy_get_structured_response(prompt, model_type=check_type)

        compliant   = bool(parsed.get("compliant", False))
        violations  = parsed.get("violations", []) or []
        severity    = (parsed.get("severity") or "low").lower()
        suggestions = parsed.get("suggestions", []) or []
        confidence  = float(parsed.get("confidence", 0.0))

        uses_context = bool(max_sim >= SIM_THRESHOLD)
        top_rules = [r["rule_text"] for r in rows][:top_k]
        score = float(max_sim)
        latency_ms = (time.time() - t0) * 1000.0

        return {
            "compliant": compliant,
            "violations": violations,
            "severity": severity,
            "suggestions": suggestions,
            "confidence": confidence,
            "uses_context": uses_context,
            "top_rules": top_rules,
            "score": score,
            "latency_ms": latency_ms,
        }

    async def check_compliance(self, text: str, check_type: Optional[str] = None) -> Dict[str, Any]:
        table_map = {
            "safety": "cpsc_recalls",
            "drug": "fda_drug_enforcement",
            "food": "fda_food_enforcement",
            "device": "fda_device_data",
        }
        table = table_map.get((check_type or "").lower(), None)
        return await self.analyze(text=text, check_type=check_type, table=table, top_k=DEFAULT_TOP_K)
