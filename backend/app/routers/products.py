from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import random

from ..database import SessionLocal
from .. import models

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def _mock_scan_and_update(product_id: int):
    # New session in background task
    db = SessionLocal()
    try:
        prod = db.get(models.Product, product_id)
        if not prod:
            return
        # 80% clear, 20% flagged (low/med/high)
        if random.random() < 0.2:
            sev = random.choice(["low", "medium", "high"])
            score = {"low": 85.0, "medium": 65.0, "high": 40.0}[sev]
            status = "flagged" if sev in ("medium", "high") else "warning"
            violations = [{"code": "PKG_WARN", "severity": sev, "msg": "Labeling inconsistency"}]
        else:
            score, status, violations = 99.0, "clear", []
        prod.compliance_score = float(score)
        prod.compliance_status = status
        prod.violations = violations          # JSON column/list
        prod.last_checked = datetime.now(timezone.utc)
        db.add(prod)
        db.commit()
    finally:
        db.close()

@router.post("/{product_id}/recheck", summary="Trigger compliance re-scan")
def recheck_product(
    product_id: int,
    bg: BackgroundTasks,
    db: Session = Depends(get_db),
):
    prod = db.get(models.Product, product_id)
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")
    # mark as checking immediately
    prod.compliance_status = "checking"
    prod.last_checked = datetime.now(timezone.utc)
    db.add(prod)
    db.commit()
    # run mock scan in background
    bg.add_task(_mock_scan_and_update, product_id=product_id)
    return {"ok": True, "message": "Scan queued"}
