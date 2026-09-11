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
    total_works: int = 171890
    flagged_count: int = 23329
    high_severity_count: int = 1137
    delay_flagged: int = 13435
    amount_flagged: int = 7000
    mp_drift_flagged: int = 4110
    isolation_forest_flagged: int = 8594
    dq_flagged_count: int = 62089
    dq_implausible_amount_count: int = 7
    dq_possible_miscategorization_count: int = 499
    dq_stale_status_count: int = 61728
    total_registered: int = 198116
    ai_scanned: int = 171890
    coverage_pct: float = 86.8

class RupeeImpact(BaseModel):
    total_analyzed_cr: float = 8501.1
    flagged_review_cr: float = 1661.7
    high_severity_cr: float = 262.3
    data_quality_cr: float = 494.2