from typing import Dict, Any, Optional
import logging
from twilio.rest import Client
from ...config import settings

log = logging.getLogger(__name__)
_client: Optional[Client] = None

def _client_ok() -> bool:
    return bool(settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN)

def _get_client() -> Optional[Client]:
    global _client
    if not settings.ENABLE_ALERTS or not _client_ok():
        log.debug("Alerts disabled or Twilio creds missing; skipping client init.")
        return None
    if _client is None:
        _client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    return _client

async def send_sms(body: str) -> None:
    cli = _get_client()
    if not cli or not settings.ALERT_TARGET_SMS or not settings.TWILIO_FROM_SMS:
        log.debug("SMS not configured; skipping. from=%s to=%s", settings.TWILIO_FROM_SMS, settings.ALERT_TARGET_SMS)
        return
    try:
        cli.messages.create(body=body, from_=settings.TWILIO_FROM_SMS, to=settings.ALERT_TARGET_SMS)
        log.info("SMS queued to %s", settings.ALERT_TARGET_SMS)
    except Exception as e:
        log.warning("SMS send failed: %s", e)

async def send_voice(twiml: str) -> None:
    cli = _get_client()
    if not cli or not settings.ALERT_TARGET_VOICE or not settings.TWILIO_FROM_SMS:
        log.debug("Voice not configured; skipping. from=%s to=%s", settings.TWILIO_FROM_SMS, settings.ALERT_TARGET_VOICE)
        return
    try:
        cli.calls.create(twiml=twiml, to=settings.ALERT_TARGET_VOICE, from_=settings.TWILIO_FROM_SMS)
        log.info("Voice call queued to %s", settings.ALERT_TARGET_VOICE)
    except Exception as e:
        log.warning("Voice call failed: %s", e)

def _format_summary(unified_result: Dict[str, Any]) -> str:
    sev = (unified_result.get("severity") or "unknown").upper()
    comp = "COMPLIANT" if unified_result.get("compliant", False) else "NON-COMPLIANT"
    vios = unified_result.get("violations", []) or []
    head = vios[0] if vios else "No explicit violations listed"
    conf = unified_result.get("confidence", None)
    conf_txt = f" (confidence {conf:.2f})" if isinstance(conf, (float, int)) else ""
    return f"[ComplianceMonster] Severity: {sev} — {comp}{conf_txt}. Top: {head}"

def _voice_twiml(unified_result: Dict[str, Any]) -> str:
    sev = unified_result.get("severity", "unknown")
    comp = "compliant" if unified_result.get("compliant", False) else "non-compliant"
    vios = unified_result.get("violations", []) or []
    brief = vios[0] if vios else "no violations listed"
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say voice="Polly.Joanna">Compliance Alert. Severity {sev}. Determined {comp}. Key issue: {brief}.</Say>
</Response>"""

async def send_alerts_if_needed(original_text: str, unified_result: Dict[str, Any]) -> None:
    """
    Escalation policy (WhatsApp removed):
      - CRITICAL: Voice + SMS
      - HIGH: SMS
      - MEDIUM/LOW/UNKNOWN: No alert
    Failures are logged, not raised.
    """
    if not settings.ENABLE_ALERTS:
        log.debug("ENABLE_ALERTS=false; skipping.")
        return

    severity = (unified_result.get("severity") or "").lower()
    summary = _format_summary(unified_result)
    voice_xml = _voice_twiml(unified_result)

    try:
        if severity == "critical":
            await send_voice(voice_xml)
            await send_sms(summary)
        elif severity == "high":
            await send_sms(summary)
        else:
            log.debug("Severity %s -> no alert sent", severity)
    except Exception as e:
        log.warning("Alert dispatch encountered an error: %s", e)
