"""Read full-corpus summaries from the same versioned export as the dashboard.

The SQLite database also holds sampled unflagged dossiers; it is not a full
corpus census. Never substitute its row count for the exported scanned count.
"""
import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[3] / 'assets' / 'data'


def overview():
    return json.loads((DATA_DIR / 'overview_kpis.json').read_text(encoding='utf-8'))


def breakdown():
    k = overview()
    signals = {c['type']: c['count'] for c in k['anomalyCategories']}
    return {
        'total_works': k['totalScannedWorks'],
        'flagged_count': k['flaggedCount'],
        'rule_flagged_count': k['ruleFlaggedCount'],
        'high_severity_count': k['criticalCount'],
        'critical_count': k['criticalCount'],
        'high_count': k['highCount'],
        'med_count': k['medCount'],
        'low_count': k['lowCount'],
        'delay_flagged': signals['Delay'],
        'amount_flagged': signals['Cost'],
        'mp_drift_flagged': signals['MP Drift'],
        'isolation_forest_flagged': signals['Spatial'],
        'dq_flagged_count': k['dataQualityCount'],
        **{name + '_count': count for name, count in k['dqCounts'].items()},
        'total_registered': k['totalRegisteredWorks'],
        'ai_scanned': k['totalScannedWorks'],
        'coverage_pct': k['coveragePct'],
    }


def rupee_impact():
    k = overview()
    return {
        'total_analyzed_cr': k['totalSanctionedCr'],
        'flagged_review_cr': k['scrutinyExposureCr'],
        'high_severity_cr': k['highSeverityExposureCr'],
        'data_quality_cr': k['dataQualityExposureCr'],
    }
