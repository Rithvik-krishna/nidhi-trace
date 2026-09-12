from pydantic import BaseModel
from typing import Optional
from datetime import date

class WorkOut(BaseModel):
    id: int
    work_id: str
    work_category: str
    state: str
    ida: str
    mp_name: str
    constituency: str
    sanction_amount: float
    gap_days: float
    flag_delay: bool
    flag_amount: bool
    flag_mp_drift: bool
    flag_isolation_forest: bool = False
    n_flags: int = 0
    is_high_severity: bool = False
    dq_flag: bool = False
    
    # Human-readable & derived fields
    work_description: Optional[str] = None
    title: Optional[str] = None
    sector: Optional[str] = None
    location: Optional[str] = None
    mp: Optional[str] = None
    sanctioned: Optional[str] = None
    expended: Optional[str] = None
    agency: Optional[str] = None
    progress: Optional[str] = None
    severity: Optional[str] = None
    anomaly: Optional[str] = None
    anomalyType: Optional[str] = None
    flag_agency: Optional[bool] = False

    class Config:
        from_attributes = True

class DossierOut(WorkOut):
    work_status: Optional[str] = None
    sanction_date: Optional[str] = None
    recommended_date: Optional[str] = None
    lok_sabha_term: Optional[str] = None
    gap_robust_z: Optional[float] = None
    amount_robust_z: Optional[float] = None
    mp_drift_robust_z: Optional[float] = None
    mp_baseline_eligible: Optional[bool] = None
    dq_implausible_amount: bool = False
    dq_possible_miscategorization: bool = False
    dq_stale_status: bool = False
    dq_reason: Optional[str] = None
    explanation: Optional[str] = None
    amount_deviation_pct: Optional[float] = None
    mp_drift_zscore: Optional[float] = None

class SeverityBreakdown(BaseModel):
    critical_count: int
    high_count: int
    med_count: int
    low_count: int
    rule_flagged_count: int
    total_works: int
    flagged_count: int
    high_severity_count: int
    delay_flagged: int
    amount_flagged: int
    mp_drift_flagged: int
    isolation_forest_flagged: int
    dq_flagged_count: int
    dq_implausible_amount_count: int
    dq_possible_miscategorization_count: int
    dq_stale_status_count: int
    total_registered: int
    ai_scanned: int
    coverage_pct: float

class RupeeImpact(BaseModel):
    total_analyzed_cr: float
    flagged_review_cr: float
    high_severity_cr: float
    data_quality_cr: float