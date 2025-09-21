from typing import Any, Dict, List, Optional, Tuple
from .base_agent import AgentResult
from .cpsc_agent import CPSC_Safety_Agent
from .fda_drug_agent import FDA_Drug_Agent
from .fda_food_agent import FDA_Food_Agent
from .fda_device_agent import FDA_Device_Agent
from ..ai_router import AIRouter
from ...config import settings

SYSTEM_COORD = (
    "You are the Coordinator_Agent. You receive findings from domain agents.\n"
    "Combine them into a single JSON with fields: compliant, violations, severity, "
    "suggestions, confidence, uses_context, top_rules.\n"
    "Ground EVERY claim in at least one agent rule provided below. If agents disagree, "
    "explain briefly and lower confidence in your own reasoning (not requested in JSON). "
    "IMPORTANT: Do NOT invent or rephrase rules — use ONLY the provided agent rules."
)

# Optional: only propagate rules from agents if their engine similarity >= this threshold
RULE_SIM_THRESHOLD = 0.25

class CoordinatorAgent:
    def __init__(self):
        self.domain_agents = [
            CPSC_Safety_Agent(),
            FDA_Drug_Agent(),
            FDA_Food_Agent(),
            FDA_Device_Agent(),
        ]
        self.ai = AIRouter()

    async def run(self, text: str, check_type: str | None = None) -> Dict[str, Any]:
        # 1) Run agents
        results: List[AgentResult] = await self._gather(text, check_type)

        # 2) Build a compact, factual summary for the LLM (no free-form “rules” generation)
        agent_payload, merged_rules = self._prepare_payload(results)

        # 3) Ask LLM for the unified verdict ONLY
        synth = await self.ai.get_structured_response(
            system=SYSTEM_COORD,
            user=(
                "User text:\n"
                f"{text}\n\n"
                "Agent findings (JSON):\n"
                f"{agent_payload}\n\n"
                "Unify into ONE decision. Return ONLY JSON per schema."
            ),
            json_schema={
                "type": "object",
                "properties": {
                    "compliant": {"type": "boolean"},
                    "violations": {"type": "array", "items": {"type": "string"}},
                    "severity": {"type": "string"},
                    "suggestions": {"type": "array", "items": {"type": "string"}},
                    "confidence": {"type": "number"},
                    "uses_context": {"type": "boolean"},
                    "top_rules": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["compliant","violations","severity","suggestions","confidence","uses_context","top_rules"],
            },
            model=settings.OPENAI_MODEL,
            extras=None,
        )

        # 4) FORCE grounding: replace LLM-provided top_rules with the merged agent rules
        synth["top_rules"] = merged_rules

        # 5) Attach provenance for UI/debug
        synth["agent_summaries"] = [
            {
                "name": r.name,
                "table": r.table,
                "score": r.report.get("score"),
                "top_rules": r.report.get("top_rules", []),
                "uses_context": r.report.get("uses_context", None),
                "severity": r.report.get("severity", None),
                "compliant": r.report.get("compliant", None),
            }
            for r in results
        ]
        return synth

    async def _gather(self, text: str, check_type: str | None) -> List[AgentResult]:
        out: List[AgentResult] = []
        for agent in self.domain_agents:
            out.append(await agent.run(text, check_type))
        return out

    def _prepare_payload(self, results: List[AgentResult]) -> Tuple[str, List[str]]:
        """
        Build a minimal JSON-ish string for the LLM and merge real rules from agents.
        We only include agent rules that passed vector similarity threshold via their engine.
        If an engine didn't expose per-rule similarity, we accept its top_rules as-is.
        """
        import json as _json

        # Build a compact agent view
        compact = []
        merged_rules: List[str] = []
        seen = set()

        for r in results:
            rep = r.report or {}
            top_rules = rep.get("top_rules", []) or []
            score = rep.get("score", 0.0)
            uses_ctx = rep.get("uses_context", None)

            # Take top_rules if the agent actually used context or similarity score is decent
            if (uses_ctx is True) or (isinstance(score, (int, float)) and score >= RULE_SIM_THRESHOLD):
                for rule in top_rules:
                    if not rule:
                        continue
                    key = rule.strip()
                    if key not in seen:
                        seen.add(key)
                        merged_rules.append(key)

            compact.append(
                {
                    "name": r.name,
                    "table": r.table,
                    "compliant": rep.get("compliant", None),
                    "severity": rep.get("severity", None),
                    "confidence": rep.get("confidence", None),
                    "score": score,
                    "uses_context": uses_ctx,
                    "violations": rep.get("violations", []),
                    "top_rules": top_rules,
                }
            )

        # Fallback if nothing passed threshold: still surface first few agent rules to avoid empty list
        if not merged_rules:
            for r in results:
                for rule in (r.report or {}).get("top_rules", [])[:2]:
                    k = (rule or "").strip()
                    if k and k not in seen:
                        seen.add(k)
                        merged_rules.append(k)
                        if len(merged_rules) >= 4:
                            break
                if len(merged_rules) >= 4:
                    break

        return _json.dumps(compact, ensure_ascii=False), merged_rules
