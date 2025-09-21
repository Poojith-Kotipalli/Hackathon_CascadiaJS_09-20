# backend/app/config.py
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None

def _load_dotenv_explicit():
    if not load_dotenv:
        return
    here = Path(__file__).resolve()
    candidates = [
        here.parents[1] / ".env",  # backend/.env
        here.parent / ".env",      # backend/app/.env
        here.parents[2] / ".env",  # repo-root/.env
    ]
    for p in candidates:
        try:
            if p.exists():
                load_dotenv(p, override=False)
                break
        except Exception:
            pass

_load_dotenv_explicit()

def _get_env(key: str, default=None):
    v = os.getenv(key)
    return v if v is not None else default

class Settings:
    # Database
    DATABASE_URL = _get_env("DATABASE_URL", "sqlite:///./test.db")

    # Models / Keys
    OPENAI_API_KEY = _get_env("OPENAI_API_KEY", "")
    OPENAI_MODEL   = _get_env("OPENAI_MODEL", "gpt-4o-mini")
    AG2_MAX_TURNS  = int(_get_env("AG2_MAX_TURNS", "4"))
    HUGGINGFACE_TOKEN = _get_env("HUGGINGFACE_TOKEN", "")

    # App
    APP_NAME = "ComplianceMonster"
    VERSION  = "0.1.0"
    DEBUG    = True

    # CORS
    CORS_ORIGINS = ["http://localhost:3000", "http://localhost:3001"]

    # --- Twilio / Alerts ---
    ENABLE_ALERTS = (_get_env("ENABLE_ALERTS", "false") or "").lower() in ("1","true","yes","y")
    TWILIO_ACCOUNT_SID = _get_env("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN  = _get_env("TWILIO_AUTH_TOKEN", "")
    TWILIO_FROM_SMS = _get_env("TWILIO_FROM_SMS", "")                 # +1XXXXXXXXXX
    TWILIO_FROM_WHATSAPP = _get_env("TWILIO_FROM_WHATSAPP", "")       # whatsapp:+1XXXXXXXXXX
    ALERT_TARGET_SMS = _get_env("ALERT_TARGET_SMS", "")               # +1YYYYYYYYYY
    ALERT_TARGET_VOICE = _get_env("ALERT_TARGET_VOICE", "")           # +1YYYYYYYYYY
    ALERT_TARGET_WHATSAPP = _get_env("ALERT_TARGET_WHATSAPP", "")     # whatsapp:+1YYYYYYYYYY

settings = Settings()
