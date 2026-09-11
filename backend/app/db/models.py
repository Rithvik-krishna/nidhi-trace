from sqlalchemy import Column, Integer, String, Float, Boolean, Text
from app.db.database import Base

class Work(Base):
    __tablename__ = "works"

    id = Column(Integer, primary_key=True, index=True)
    work_id = Column(String, index=True)
    work_category = Column(String)
    state = Column(String, index=True)
    ida = Column(String)
    mp_name = Column(String, index=True)
    constituency = Column(String)
    sanction_amount = Column(Float)
    gap_days = Column(Float)

    flag_delay = Column(Boolean, default=False)
    flag_amount = Column(Boolean, default=False)
    flag_mp_drift = Column(Boolean, default=False)
    n_flags = Column(Integer, default=0)
    is_high_severity = Column(Boolean, default=False)

    amount_deviation_pct = Column(Float, nullable=True)
    mp_drift_zscore = Column(Float, nullable=True)

    explanation = Column(Text, nullable=True)
    flag_isolation_forest = Column(Boolean, default=False)
    dq_flag = Column(Boolean, default=False)
    dq_stale_status = Column(Boolean, default=False)
    dq_implausible_amount = Column(Boolean, default=False)
    dq_possible_miscategorization = Column(Boolean, default=False)
    dq_reason = Column(Text, nullable=True)

    # Rich metadata fields to support all frontend views
    title = Column(Text, nullable=True)
    sector = Column(String, nullable=True)
    location = Column(String, nullable=True)
    mp = Column(String, nullable=True)
    sanctioned = Column(String, nullable=True)
    expended = Column(String, nullable=True)
    agency = Column(String, nullable=True)
    progress = Column(String, nullable=True)
    score = Column(Integer, nullable=True)
    severity = Column(String, nullable=True)
    anomaly = Column(String, nullable=True)
    anomalyType = Column(String, nullable=True)
    flag_agency = Column(Boolean, default=False)