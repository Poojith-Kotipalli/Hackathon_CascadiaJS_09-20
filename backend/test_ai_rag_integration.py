# backend/test_ai_rag_integration.py
import asyncio
import time
from dotenv import load_dotenv
load_dotenv()

from app.services.compliance_engine import ComplianceEngine

TESTS = [
    ("cpsc_recalls", "Magnetic building blocks for toddlers ages 2-4"),
    ("cpsc_recalls", "Battery-powered toy with small removable battery compartment"),
    ("fda_drug_enforcement", "FDA approved dietary supplement that cures diabetes"),
    ("fda_drug_enforcement", "Natural herbal remedy that prevents cancer"),
    ("fda_food_enforcement", "Chocolate bars made in facility that processes peanuts"),
    ("fda_food_enforcement", "All natural energy drink with artificial flavors"),
    ("fda_device_data", "Bluetooth heart rate monitor for medical diagnosis"),
    ("fda_device_data", "Software app that detects skin cancer from photos"),
    ("fda_drug_labels", "Pain relief medication safe for pregnant women"),
    ("electronics_compliance", "USB charger with exposed wiring sold online"),
    ("electronics_compliance", "Lithium battery pack without safety certification"),
]

async def main():
    engine = ComplianceEngine()
    detected = 0
    total = 0

    for table, text in TESTS:
        print("\n" + "="*80)
        print(f"TABLE: {table}\nQUERY: {text}")
        start = time.time()
        result = await engine.analyze(text, check_type="realtime", table=table)
        dur = (time.time() - start) * 1000
        print(f"Model: {result['model_used']}  Latency: {dur:.1f} ms  UsesContext: {result['uses_context']}")
        if result.get("top_rules"):
            for i, r in enumerate(result["top_rules"], 1):
                print(f"  Rule {i}: {r['domain']} sim={r['similarity']:.2f} sev={r['severity']} | {r['rule_text'][:90]}...")
        print("Compliant:", result["compliant"], "Score:", f"{result['score']:.1f}")
        print("Violations:", result["violations"])
        total += 1
        if not result["compliant"]:
            detected += 1

    print("\nSUMMARY:", f"{detected}/{total} violations detected")

if __name__ == "__main__":
    asyncio.run(main())
