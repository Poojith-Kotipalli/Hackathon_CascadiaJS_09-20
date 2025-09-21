# backend/test_ag2_all_agents.py
import asyncio
import time
from typing import List, Tuple

from app.services.agents.cpsc_agent import CPSC_Safety_Agent
from app.services.agents.fda_drug_agent import FDA_Drug_Agent
from app.services.agents.fda_food_agent import FDA_Food_Agent
from app.services.agents.fda_device_agent import FDA_Device_Agent
from app.services.agents.coordinator import CoordinatorAgent

BAR = "=" * 70

def _fmt_rules(rules: List[str], n: int = 3) -> List[str]:
    out = []
    for i, r in enumerate(rules[:n], 1):
        r = (r or "").replace("\n", " ")
        if len(r) > 180:
            r = r[:177] + "..."
        out.append(f"{i}. {r}")
    return out

async def run_agent(agent_name: str, agent_obj, q: str, check_type: str | None) -> Tuple[str, dict, int]:
    t0 = time.time()
    res = await agent_obj.run(q, check_type)
    dt = int((time.time() - t0) * 1000)
    report = res.report or {}
    print(f"\n[{agent_name}] table={res.table}  time={dt}ms")
    print(f"  compliant={report.get('compliant')}  severity={report.get('severity')}  conf={report.get('confidence')}")
    print(f"  uses_context={report.get('uses_context')}  score={report.get('score')}")
    rules = _fmt_rules(report.get('top_rules', []))
    if rules:
        print("  top_rules:")
        for line in rules:
            print("   -", line)
    else:
        print("  top_rules: []")
    return agent_name, report, dt

async def run_coordinator(q: str, check_type: str | None):
    coord = CoordinatorAgent()
    t0 = time.time()
    out = await coord.run(text=q, check_type=check_type)
    dt = int((time.time() - t0) * 1000)
    print(f"\n{BAR}\n[Coordinator] time={dt}ms")
    print(f"  compliant={out.get('compliant')}  severity={out.get('severity')}  conf={out.get('confidence')}")
    print(f"  uses_context={out.get('uses_context')}")
    rules = _fmt_rules(out.get('top_rules', []), n=5)
    if rules:
        print("  merged_top_rules:")
        for line in rules:
            print("   -", line)
    ag = out.get("agent_summaries", [])
    if ag:
        print("  agent_summaries:")
        for a in ag:
            print(f"   - {a.get('name')} ({a.get('table')}): score={a.get('score')}, compliant={a.get('compliant')}, severity={a.get('severity')}")
    print(BAR)

async def main():
    # === Test inputs per domain ===
    tests = [
        # CPSC / toys (hazards, magnets, etc.)
        ("Magnetic building blocks for toddlers ages 2-4", "safety"),
        # FDA Drug (supplements/claims)
        ("Herbal supplement claims to cure diabetes and is FDA approved", "drug"),
        # FDA Food (allergens/contamination)
        ("Chocolate bar contains peanuts but label omits allergen warning", "food"),
        # FDA Device (device class, recall reasoning)
        ("Unlabeled Class II pulse oximeter with inaccurate readings", "device"),
        # Cross-domain sanity (coordinator roll-up)
        ("Toddler toy set includes small high-powered magnets and loose batteries", None),
    ]

    cpsc = CPSC_Safety_Agent()
    drug = FDA_Drug_Agent()
    food = FDA_Food_Agent()
    dev  = FDA_Device_Agent()
    agents = [
        ("CPSC_Safety_Agent", cpsc),
        ("FDA_Drug_Agent", drug),
        ("FDA_Food_Agent", food),
        ("FDA_Device_Agent", dev),
    ]

    for q, check_type in tests:
        print(f"\n\n🚀 TEST: {q}\n{BAR}")
        # Run all domain agents
        for name, obj in agents:
            try:
                await run_agent(name, obj, q, check_type)
            except Exception as e:
                print(f"[{name}] ERROR: {e}")

        # Run coordinator (always)
        try:
            await run_coordinator(q, check_type)
        except Exception as e:
            print(f"[Coordinator] ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(main())
