"""
NidhiTrace Database Seeder
Auto-populates the SQLite database with authentic works and anomaly flags
from the verified NIDHI TRACE datasets if the database table is empty.
"""

import os
import json
from pathlib import Path
from sqlalchemy.orm import Session
from app.db.models import Work
from app.services.explanation import generate_explanation

def parse_currency_str(val_str):
    if not val_str:
        return 0.0
    raw_str = str(val_str).replace("₹", "").replace(",", "").strip()
    if "Cr" in raw_str:
        try:
            return float(raw_str.replace("Cr", "").strip()) * 1e7
        except ValueError:
            return 0.0
    elif "L" in raw_str:
        try:
            return float(raw_str.replace("L", "").strip()) * 1e5
        except ValueError:
            return 0.0
    else:
        try:
            return float(raw_str)
        except ValueError:
            return 0.0

def seed_database_if_empty(db: Session, force: bool = False):
    try:
        existing_count = db.query(Work).count()
        if existing_count > 0 and not force:
            return existing_count

        if force and existing_count > 0:
            db.query(Work).delete()
            db.commit()

        project_root = Path(__file__).resolve().parent.parent.parent.parent
        cases_path = project_root / "assets" / "data" / "cases_index.json"
        flagged_path = project_root / "assets" / "data" / "flagged_cases.json"
        ledger_path = project_root / "assets" / "data" / "ledger_works.json"

        works_to_insert = []
        seen_work_ids = set()

        # 1. Seed Cases Index (Detailed Dossiers)
        if cases_path.exists():
            with open(cases_path, "r", encoding="utf-8") as f:
                cases_data = json.load(f)

            for cid, c in cases_data.items():
                if cid in seen_work_ids:
                    continue
                seen_work_ids.add(cid)

                flags = c.get("flags") or {}
                flag_delay = bool(flags.get("flag_delay", False))
                flag_amount = bool(flags.get("flag_amount", False))
                flag_mp_drift = bool(flags.get("flag_mp_drift", False))
                flag_iso = bool(flags.get("iso_flag", False))
                is_high_sev = bool(flags.get("rule_high_severity", c.get("severity") in ("critical", "high")))
                n_flags = sum([flag_delay, flag_amount, flag_mp_drift, flag_iso])

                sanc_val = c.get("sanctioned_raw")
                if sanc_val is None:
                    sanc_val = parse_currency_str(c.get("sanctioned"))

                work_row = {
                    "work_id": cid,
                    "work_category": c.get("sector") or "Public Infrastructure",
                    "state": c.get("state") or "India",
                    "ida": c.get("agency") or "District Authority",
                    "mp_name": c.get("mp") or "Member of Parliament",
                    "constituency": c.get("constituency") or c.get("location") or "District",
                    "sanction_amount": float(sanc_val),
                    "gap_days": float(c.get("gapDays") or 0.0),
                    "flag_delay": flag_delay,
                    "flag_amount": flag_amount,
                    "flag_mp_drift": flag_mp_drift,
                    "n_flags": n_flags,
                    "is_high_severity": is_high_sev,
                    "amount_deviation_pct": float(flags.get("amount_zscore", 0.0) or 0.0) * 25.0,
                    "mp_drift_zscore": float(flags.get("mp_drift_zscore", 0.0) or 0.0),
                    "flag_isolation_forest": flag_iso,
                    # Rich UI fields
                    "title": c.get("title") or f"MPLAD Scheme Work {cid}",
                    "sector": c.get("sector") or "Public Infrastructure",
                    "location": c.get("location") or f"{c.get('constituency', '')}, {c.get('state', '')}",
                    "mp": c.get("mp") or "Member of Parliament",
                    "sanctioned": c.get("sanctioned") or f"₹{sanc_val:,.0f}",
                    "expended": c.get("utilized") or c.get("expended") or "₹0",
                    "agency": c.get("agency") or "District Implementing Agency",
                    "progress": c.get("workStatus") or c.get("status") or "In Progress",
                    "score": int(c.get("score", 75)),
                    "severity": c.get("severity", "medium"),
                    "anomaly": c.get("anomaly", "Flagged Anomaly")
                }
                expl = c.get("anomaly") or generate_explanation(work_row)
                work_row["explanation"] = expl
                works_to_insert.append(Work(**work_row))

        # 2. Seed Flagged Cases
        if flagged_path.exists():
            with open(flagged_path, "r", encoding="utf-8") as f:
                flagged_data = json.load(f)

            for item in flagged_data:
                wid = item.get("id") or item.get("work_id")
                if not wid or wid in seen_work_ids:
                    continue
                seen_work_ids.add(wid)

                flags = item.get("flags") or {}
                flag_delay = bool(flags.get("flag_delay", "delay" in str(item.get("anomaly", "")).lower()))
                flag_amount = bool(flags.get("flag_amount", "amount" in str(item.get("anomaly", "")).lower() or "cost" in str(item.get("anomaly", "")).lower()))
                flag_mp_drift = bool(flags.get("flag_mp_drift", "drift" in str(item.get("anomaly", "")).lower()))
                flag_iso = bool(flags.get("iso_flag", False))
                is_high_sev = bool(item.get("severity") in ("critical", "high"))
                n_flags = sum([flag_delay, flag_amount, flag_mp_drift, flag_iso])

                sanc_val = item.get("sanctioned_raw")
                if sanc_val is None:
                    sanc_val = parse_currency_str(item.get("sanctioned"))

                w_row = {
                    "work_id": wid,
                    "work_category": item.get("sector") or "Public Infrastructure",
                    "state": item.get("state") or "India",
                    "ida": item.get("agency") or "District Authority",
                    "mp_name": item.get("mp") or "Member of Parliament",
                    "constituency": item.get("constituency") or item.get("location") or "District",
                    "sanction_amount": float(sanc_val),
                    "gap_days": float(item.get("gapDays") or 90.0),
                    "flag_delay": flag_delay,
                    "flag_amount": flag_amount,
                    "flag_mp_drift": flag_mp_drift,
                    "n_flags": n_flags,
                    "is_high_severity": is_high_sev,
                    "amount_deviation_pct": float(flags.get("amount_zscore", 0.0) or 25.0),
                    "mp_drift_zscore": float(flags.get("mp_drift_zscore", 0.0) or 2.1),
                    "flag_isolation_forest": flag_iso,
                    "explanation": item.get("anomaly") or "Flagged during algorithmic surveillance.",
                    "title": item.get("title") or f"MPLAD Scheme Work {wid}",
                    "sector": item.get("sector") or "Public Infrastructure",
                    "location": item.get("location") or "India",
                    "mp": item.get("mp") or "Member of Parliament",
                    "sanctioned": item.get("sanctioned") or f"₹{sanc_val:,.0f}",
                    "expended": item.get("utilized") or item.get("expended") or "₹0",
                    "agency": item.get("agency") or "District Agency",
                    "progress": item.get("status") or item.get("workStatus") or "In Progress",
                    "score": int(item.get("score", 80)),
                    "severity": item.get("severity", "high"),
                    "anomaly": item.get("anomaly", "Flagged Irregularity")
                }
                works_to_insert.append(Work(**w_row))

        # 3. Seed Ledger Works
        if ledger_path.exists():
            with open(ledger_path, "r", encoding="utf-8") as f:
                ledger_data = json.load(f)

            for item in ledger_data:
                wid = item.get("id")
                if not wid or wid in seen_work_ids:
                    continue
                seen_work_ids.add(wid)

                sval = parse_currency_str(item.get("sanctioned"))
                loc = item.get("location", "")
                parts = loc.split(",") if "," in loc else [loc, loc]
                dist = parts[0].strip()
                st = parts[-1].strip() if len(parts) > 1 else dist
                is_flagged = bool(item.get("isFlagged", False))

                w_row = {
                    "work_id": wid,
                    "work_category": item.get("sector") or "General Infrastructure",
                    "state": st or "India",
                    "ida": item.get("agency") or "District Implementing Agency",
                    "mp_name": item.get("mp") or "District MP",
                    "constituency": dist or "Constituency",
                    "sanction_amount": float(sval),
                    "gap_days": 180.0 if is_flagged else 45.0,
                    "flag_delay": is_flagged,
                    "flag_amount": False,
                    "flag_mp_drift": False,
                    "n_flags": 1 if is_flagged else 0,
                    "is_high_severity": False,
                    "amount_deviation_pct": 12.0 if is_flagged else 0.0,
                    "mp_drift_zscore": 1.2 if is_flagged else 0.0,
                    "flag_isolation_forest": False,
                    "explanation": "Flagged during cross-constituency surveillance." if is_flagged else "Normal expenditure within compliance limits.",
                    "title": item.get("title") or f"MPLAD Scheme Work {wid}",
                    "sector": item.get("sector") or "General Infrastructure",
                    "location": loc or "India",
                    "mp": item.get("mp") or "District MP",
                    "sanctioned": item.get("sanctioned") or f"₹{sval:,.0f}",
                    "expended": item.get("expended") or "₹0",
                    "agency": item.get("agency") or "District Implementing Agency",
                    "progress": item.get("progress") or "In Progress",
                    "score": 85 if is_flagged else 20,
                    "severity": "high" if is_flagged else "low",
                    "anomaly": "Flagged Work" if is_flagged else "Compliant"
                }
                works_to_insert.append(Work(**w_row))

        if works_to_insert:
            db.bulk_save_objects(works_to_insert)
            db.commit()
            print(f"[NidhiTrace Seeder] Successfully seeded {len(works_to_insert)} records into database.")
            return len(works_to_insert)
    except Exception as e:
        db.rollback()
        print(f"[NidhiTrace Seeder] Seeding error: {e}")
        return 0
