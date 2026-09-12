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
from app.services import dashboard_summary

router = APIRouter()

@router.get("/summary/breakdown", response_model=SeverityBreakdown)
def severity_breakdown(db: Session = Depends(get_db)):
    return SeverityBreakdown(**dashboard_summary.breakdown())

@router.get("/summary/rupee-impact", response_model=RupeeImpact)
def rupee_impact(db: Session = Depends(get_db)):
    return RupeeImpact(**dashboard_summary.rupee_impact())

@router.get("/overview")
def get_overview(db: Session = Depends(get_db)):
    return dashboard_summary.overview()

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
        query = query.filter((Work.dq_flag == True) | (Work.anomalyType == "Data Quality"))
    elif signal == "agency":
        query = query.filter((Work.anomalyType == "Agency") | (Work.flag_agency == True) | (Work.anomaly.ilike("%agency%")))
    elif signal == "spatial":
        query = query.filter((Work.anomalyType == "Spatial") | (Work.flag_isolation_forest == True))
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
