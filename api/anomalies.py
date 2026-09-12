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

from backend.app.services import dashboard_summary

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
                payload = dashboard_summary.breakdown()
                data = json.dumps(payload).encode('utf-8')
            elif url_path.endswith('/summary/rupee-impact'):
                payload = dashboard_summary.rupee_impact()
                data = json.dumps(payload).encode('utf-8')
            elif url_path.endswith('/overview'):
                data = json.dumps(dashboard_summary.overview()).encode('utf-8')
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
