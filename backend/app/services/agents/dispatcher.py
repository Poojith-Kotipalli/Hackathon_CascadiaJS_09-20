from __future__ import annotations
from typing import List, Optional
import re

from app.services.image_classifier import extract_tags
# Your coordinator module should expose a function you can call directly.
# If not, create a thin wrapper around the same code your /compliance/check/agents route uses.
from app.services.agents.coordinator import run_coordinator  # adjust name if different

# Map keywords/tags -> agents
ROUTE_RULES = [
    # FDA drug (cosmetics, OTC, supplements)
    (["sunscreen","spf","serum","cosmetic","cream","ointment","supplement","vitamin","otc","medicine","drug"], ["FDA_Drug_Agent"]),
    # FDA food
    (["snack","beverage","drink","juice","bar","granola","allergen","peanut","gluten"], ["FDA_Food_Agent"]),
    # FDA device
    (["thermometer","glucose","bp monitor","cpap","pulse oximeter","device"], ["FDA_Device_Agent"]),
    # CPSC toys/children/magnets
    (["toy","toddler","children","magnet","choking","ride-on","stroller","crib"], ["CPSC_Safety_Agent"]),
    # Electronics safety
    (["charger","battery","lithium","adapter","power bank","e-bike","e scooter","usb-c"], ["Electronics_Agent"]),
]

def _normalize(s: str) -> str:
    return (s or "").lower()

async def route_targets_for_listing(text: str, image_url: Optional[str], category: Optional[str]) -> List[str]:
    hay = " ".join([_normalize(text), _normalize(category or "")])
    tags = await extract_tags(image_url) if image_url else []
    hay += " " + " ".join(tags)

    hits: List[str] = []
    for needles, agents in ROUTE_RULES:
        if any(k in hay for k in needles):
            for a in agents:
                if a not in hits:
                    hits.append(a)
    # Fallback: if nothing matched, run the general set (all)
    return hits or ["CPSC_Safety_Agent","FDA_Drug_Agent","FDA_Food_Agent","FDA_Device_Agent"]

async def run_coordinator_restricted(text: str, allowed_agents: List[str]) -> dict:
    # The coordinator should accept a list of agent names/tables to run.
    # If your current coordinator lacks this param, add it (small diff) or filter after.
    return await run_coordinator(text=text, allowed_agents=allowed_agents)
