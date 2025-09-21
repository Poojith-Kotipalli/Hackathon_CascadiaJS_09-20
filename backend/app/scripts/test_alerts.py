import asyncio
import sys
from pathlib import Path

# Make 'app' importable when running this file directly
BACKEND_DIR = Path(__file__).resolve().parents[2]  # .../backend
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.config import settings
from app.services.alerts.twilio_alerts import send_alerts_if_needed

EXAMPLE_TEXT = "Smoke test from ComplianceMonster"

EXAMPLES = [
    {"severity": "low", "compliant": True,  "violations": [], "confidence": 0.9},                       # no alert
    {"severity": "high", "compliant": False, "violations": ["High severity test"], "confidence": 0.8},   # SMS
    {"severity": "critical", "compliant": False, "violations": ["Critical severity test"], "confidence": 0.7},  # Voice+SMS
]

async def main():
    print("ENABLE_ALERTS:", settings.ENABLE_ALERTS)
    print("FROM SMS:", settings.TWILIO_FROM_SMS, "TARGET SMS:", settings.ALERT_TARGET_SMS)
    print("TARGET VOICE:", settings.ALERT_TARGET_VOICE)
    print()

    for payload in EXAMPLES:
        print(f"--> Sending severity={payload['severity']} …")
        await send_alerts_if_needed(EXAMPLE_TEXT, payload)
        print("   queued (check Twilio Console logs).")

if __name__ == "__main__":
    asyncio.run(main())
