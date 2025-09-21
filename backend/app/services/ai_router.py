import time
import logging
import json
import re
from typing import Dict, Any, Optional, List

from openai import AsyncOpenAI
from ..config import settings

logger = logging.getLogger(__name__)
JSON_PATTERN = re.compile(r"\{.*\}", re.S)

class AIRouter:
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        # Lazy; do not raise here
        self.api_key = (api_key or settings.OPENAI_API_KEY or "").strip()
        self.model   = (model or settings.OPENAI_MODEL or "gpt-4o-mini").strip()
        self._client: Optional[AsyncOpenAI] = None

    def _ensure_client(self):
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY missing. Put it in .env or env var.")
        if self._client is None:
            self._client = AsyncOpenAI(api_key=self.api_key)

    async def _chat(self, messages: List[Dict[str, str]], *, json_mode: bool = False) -> str:
        self._ensure_client()
        kwargs = {"model": self.model, "messages": messages, "temperature": 0.2}
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        resp = await self._client.chat.completions.create(**kwargs)
        return (resp.choices[0].message.content or "").strip()

    # ---------- NEW API ----------
    async def get_text(
        self, *, system: str, user: str, model: Optional[str] = None, extras: Optional[dict] = None
    ) -> str:
        if model:
            self.model = model
        msgs = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        return await self._chat(msgs, json_mode=False)

    async def get_structured_response(
        self, *, system: str, user: str, json_schema: dict, model: Optional[str] = None, extras: Optional[dict] = None
    ) -> Dict[str, Any]:
        if model:
            self.model = model
        schema_hint = json.dumps(
            {"type": "object", "properties": json_schema.get("properties", {}), "required": json_schema.get("required", [])},
            indent=0,
        )
        sys_msg = (
            f"{system}\n"
            "You must answer ONLY with valid JSON that conforms to this schema (no extra keys, no text outside JSON):\n"
            f"{schema_hint}"
        )
        msgs = [{"role": "system", "content": sys_msg}, {"role": "user", "content": user}]
        raw = await self._chat(msgs, json_mode=True)
        try:
            return json.loads(raw)
        except Exception:
            m = JSON_PATTERN.search(raw or "")
            return json.loads(m.group(0)) if m else {}

    # ---------- LEGACY API (compat) ----------
    async def legacy_get_text(self, prompt: str) -> str:
        msgs = [{"role": "user", "content": prompt}]
        return await self._chat(msgs, json_mode=False)

    async def legacy_get_structured_response(self, prompt: str, model_type: Optional[str] = None) -> Dict[str, Any]:
        # You can map model_type to a different model if needed; otherwise ignore.
        schema_req = (
            "Respond ONLY with valid JSON using exactly these keys: "
            '{"compliant": <boolean>, "violations": <array of strings>, '
            '"severity": "high|medium|low|critical", "suggestions": <array of strings>, '
            '"confidence": <number 0..1> }'
        )
        msgs = [{"role": "system", "content": schema_req}, {"role": "user", "content": prompt}]
        raw = await self._chat(msgs, json_mode=True)
        try:
            return json.loads(raw)
        except Exception:
            m = JSON_PATTERN.search(raw or "")
            return json.loads(m.group(0)) if m else {}

# Lazy singleton (optional shims for old imports)
_router_singleton: Optional[AIRouter] = None
def _get_router() -> AIRouter:
    global _router_singleton
    if _router_singleton is None:
        _router_singleton = AIRouter()
    return _router_singleton

async def get_structured_response(*, system: str, user: str, json_schema: dict, model: str, extras: dict | None = None):
    return await _get_router().get_structured_response(system=system, user=user, json_schema=json_schema, model=model, extras=extras)

async def get_text(*, system: str, user: str, model: str, extras: dict | None = None):
    return await _get_router().get_text(system=system, user=user, model=model, extras=extras)
