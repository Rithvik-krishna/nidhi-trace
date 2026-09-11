"""
Vercel Serverless Function: /api/anomalies
Handles GET /api/anomalies, /api/anomalies/overview, /api/anomalies/summary/breakdown, and dossiers on Vercel
"""

import os
import sys
import json
from http.server import BaseHTTPRequestHandler

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if os.path.join(PROJECT_ROOT, "backend") not in sys.path:
    sys.path.insert(0, os.path.join(PROJECT_ROOT, "backend"))

try:
    from backend.app.main import app as fastapi_app
    from fastapi.testclient import TestClient
    client = TestClient(fastapi_app)
except Exception as e:
    client = None

class handler(BaseHTTPRequestHandler):
    def _set_cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')

    def do_OPTIONS(self):
        self.send_response(200)
        self._set_cors()
        self.end_headers()

    def do_GET(self):
        if client:
            resp = client.get(self.path)
            self.send_response(resp.status_code)
            for k, v in resp.headers.items():
                if k.lower() not in ('content-length', 'server', 'date'):
                    self.send_header(k, v)
            self._set_cors()
            self.send_header('Content-Length', str(len(resp.content)))
            self.end_headers()
            self.wfile.write(resp.content)
            return

        try:
            url_path = self.path.split('?')[0]
            if url_path.endswith('/summary/breakdown'):
                payload = {
                    "total_works": 171890,
                    "flagged_count": 23329,
                    "high_severity_count": 1137,
                    "delay_flagged": 13435,
                    "amount_flagged": 7000,
                    "mp_drift_flagged": 4110,
                    "isolation_forest_flagged": 8594,
                    "dq_flagged_count": 62089,
                    "dq_implausible_amount_count": 7,
                    "dq_possible_miscategorization_count": 499,
                    "dq_stale_status_count": 61728,
                    "total_registered": 198116,
                    "ai_scanned": 171890,
                    "coverage_pct": 86.8
                }
                data = json.dumps(payload).encode('utf-8')
            elif url_path.endswith('/summary/rupee-impact'):
                payload = {
                    "total_analyzed_cr": 8501.1,
                    "flagged_review_cr": 1661.7,
                    "high_severity_cr": 262.3,
                    "data_quality_cr": 494.2
                }
                data = json.dumps(payload).encode('utf-8')
            else:
                with open(os.path.join(PROJECT_ROOT, 'assets', 'data', 'flagged_cases.json'), 'rb') as f:
                    data = f.read()

            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self._set_cors()
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        except Exception as e:
            self.send_response(500)
            self.end_headers()
