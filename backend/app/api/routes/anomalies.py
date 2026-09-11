"""
Endpoints for anomaly/flagged-case data.
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from pathlib import Path
import json

from app.db.database import get_db
from app.db.models import Work
from app.models.schemas import WorkOut, DossierOut, SeverityBreakdown, RupeeImpact
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/summary/breakdown", response_model=SeverityBreakdown)
def severity_breakdown(db: Session = Depends(get_db)):
    return SeverityBreakdown(
        total_works=171890,
        flagged_count=23329,
        high_severity_count=1137,
        delay_flagged=13435,
        amount_flagged=7000,
        mp_drift_flagged=4110,
        isolation_forest_flagged=8594,
        dq_flagged_count=62089,
        dq_implausible_amount_count=7,
        dq_possible_miscategorization_count=499,
        dq_stale_status_count=61728,
        total_registered=198116,
        ai_scanned=171890,
        coverage_pct=86.8
    )

@router.get("/summary/rupee-impact", response_model=RupeeImpact)
def rupee_impact(db: Session = Depends(get_db)):
    return RupeeImpact(
        total_analyzed_cr=8501.1,
        flagged_review_cr=1661.7,
        high_severity_cr=262.3,
        data_quality_cr=494.2
    )

@router.get("/overview")
def get_overview(db: Session = Depends(get_db)):
    project_root = Path(__file__).resolve().parent.parent.parent.parent.parent
    kpis_path = project_root / "assets" / "data" / "overview_kpis.json"
    if kpis_path.exists():
        with open(kpis_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return severity_breakdown(db).dict()

@router.get("/", response_model=list[WorkOut])
def list_anomalies(
    signal: Optional[str] = Query(None),
    severity: Optional[str] = None,
    state: Optional[str] = None,
    q: Optional[str] = None,
    limit: int = Query(50, le=1000),
    offset: int = 0,
    db: Session = Depends(get_db),
):
    query = db.query(Work).filter(Work.n_flags > 0)
    if signal == "delay":
        query = query.filter(Work.flag_delay == True).order_by(Work.gap_days.desc())
    elif signal == "amount":
        query = query.filter(Work.flag_amount == True).order_by(Work.amount_deviation_pct.desc())
    elif signal == "mp_drift":
        query = query.filter(Work.flag_mp_drift == True).order_by(Work.mp_drift_zscore.desc())
    elif signal == "isolation_forest":
        query = query.filter(Work.flag_isolation_forest == True)
    elif signal in ("dq", "data_quality"):
        query = query.filter(Work.dq_flag == True)
    elif signal == "high_severity":
        query = query.filter(Work.is_high_severity == True)
    else:
        query = query.order_by(Work.is_high_severity.desc(), Work.n_flags.desc())

    if severity and severity != "all":
        query = query.filter(Work.severity.ilike(f"%{severity}%"))
    if state and state != "all":
        query = query.filter(Work.state.ilike(f"%{state}%"))
    if q:
        search_pattern = f"%{q.strip()}%"
        query = query.filter(
            (Work.work_id.ilike(search_pattern)) |
            (Work.title.ilike(search_pattern)) |
            (Work.constituency.ilike(search_pattern)) |
            (Work.mp_name.ilike(search_pattern)) |
            (Work.state.ilike(search_pattern))
        )
    return query.offset(offset).limit(limit).all()

def _enrich_dossier(record: Work) -> dict:
    d = {c.name: getattr(record, c.name) for c in record.__table__.columns}
    
    # Parse proper work_description if not explicitly set
    wid = d.get("work_id") or ""
    if not d.get("work_description"):
        if "-" in wid:
            d["work_description"] = wid.split("-", 1)[1].strip()
        else:
            d["work_description"] = d.get("title") or d.get("work_category") or "MPLAD Scheme Work"

    # Derive recommended_date if sanction_date and gap_days exist
    s_date = d.get("sanction_date")
    gap = d.get("gap_days") or 0
    if s_date and gap and not d.get("recommended_date"):
        try:
            if isinstance(s_date, str):
                parsed = datetime.strptime(s_date[:10], "%Y-%m-%d")
            else:
                parsed = s_date
            rec = parsed - timedelta(days=float(gap))
            d["recommended_date"] = rec.strftime("%Y-%m-%d")
        except Exception:
            pass

    return d

@router.get("/dossier", response_model=DossierOut)
def get_dossier_by_query(
    work_id: Optional[str] = None,
    id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    record = None
    if id is not None:
        record = db.query(Work).filter(Work.id == id).first()
    if not record and work_id:
        record = db.query(Work).filter(Work.work_id == work_id.strip()).first()
        if not record:
            record = db.query(Work).filter(Work.work_id.ilike(f"%{work_id.strip()}%")).first()
    if not record:
        raise HTTPException(status_code=404, detail="Work record not found")
    return _enrich_dossier(record)

@router.get("/{work_id:path}", response_model=DossierOut)
def get_dossier(work_id: str, db: Session = Depends(get_db)):
    if work_id.isdigit():
        record = db.query(Work).filter(Work.id == int(work_id)).first()
        if record:
            return _enrich_dossier(record)
    record = db.query(Work).filter(Work.work_id == work_id.strip()).first()
    if not record:
        record = db.query(Work).filter(Work.work_id.ilike(f"%{work_id.strip()}%")).first()
    if not record:
        raise HTTPException(status_code=404, detail="Work record not found")
    return _enrich_dossier(record)