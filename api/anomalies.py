"""
Vercel Serverless Function: /api/anomalies
Handles GET /api/anomalies, /api/anomalies/overview, /api/anomalies/summary/breakdown, and dossiers on Vercel
Proxies to remote Render backend: https://nidhitrace-api.onrender.com
"""

import os
import sys
import json
import urllib.request
import urllib.error
from http.server import BaseHTTPRequestHandler

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

BACKEND_URL = os.environ.get('BACKEND_URL', 'https://nidhitrace-api.onrender.com').rstrip('/')

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
        url_path = self.path.split('?')[0]

        # Try remote Render backend first
        target_url = f"{BACKEND_URL}{self.path}"
        try:
            req = urllib.request.Request(target_url, headers={'User-Agent': 'NidhiTrace-Vercel-Proxy/1.0'})
            with urllib.request.urlopen(req, timeout=10) as resp:
                resp_data = resp.read()
                self.send_response(resp.status)
                self.send_header('Content-Type', resp.headers.get('Content-Type', 'application/json'))
                self._set_cors()
                self.send_header('Content-Length', str(len(resp_data)))
                self.end_headers()
                self.wfile.write(resp_data)
                return
        except Exception:
            pass

        # Fallback to local snapshot data
        try:
            if url_path.endswith('/overview'):
                fallback_file = os.path.join(PROJECT_ROOT, 'assets', 'data', 'overview_kpis.json')
            elif url_path.endswith('/summary/breakdown'):
                fallback_file = os.path.join(PROJECT_ROOT, 'assets', 'data', 'analytics_data.json')
            else:
                fallback_file = os.path.join(PROJECT_ROOT, 'assets', 'data', 'flagged_cases.json')

            if os.path.exists(fallback_file):
                with open(fallback_file, 'rb') as f:
                    data = f.read()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self._set_cors()
                self.send_header('Content-Length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return

            self.send_response(404)
            self.end_headers()
        except Exception as e:
            self.send_response(500)
            self.end_headers()
