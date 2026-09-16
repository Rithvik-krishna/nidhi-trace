"""
NIDHI TRACE Server with Integrated NIDHI Assistant Endpoint and Remote Backend Proxy
Serves:
1. Static HTML/JS/CSS assets for NIDHI TRACE on port 3000
2. Proxy for REST API routes (/api/works, /api/anomalies, /health) to remote Render backend:
   https://nidhitrace-api.onrender.com
3. POST /api/assistant/chat -> NIDHI Assistant AI Audit Copilot
4. GET /api/assistant/status -> Operational status & mode
"""

import sys
import os
import json
import urllib.request
import urllib.error
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Remote FastAPI backend URL (hosted on Render)
BACKEND_URL = os.environ.get('BACKEND_URL', 'https://nidhitrace-api.onrender.com').rstrip('/')

try:
    from assistant_service import handle_chat_request, get_assistant_status
except Exception as e:
    print(f"[NIDHI Server] Assistant service import notice: {e}")
    def handle_chat_request(body, client_ip="127.0.0.1"):
        return {"status": "success", "message": "NIDHI Assistant is running in fallback mode.", "mode": "demo"}
    def get_assistant_status():
        return {"name": "NIDHI Assistant", "status": "online", "mode": "demo", "model": "Local Fallback"}

class NidhiTraceRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE_DIR, **kwargs)

    def _set_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()

    def _serve_local_json(self, relative_path: str):
        full_path = os.path.join(BASE_DIR, relative_path.replace('/', os.sep))
        if os.path.exists(full_path):
            with open(full_path, 'rb') as f:
                data = f.read()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self._set_cors_headers()
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return True
        return False

    def do_GET(self):
        url_path = self.path.split('?')[0]

        if url_path == '/api/assistant/status':
            status = get_assistant_status()
            resp_bytes = json.dumps(status).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self._set_cors_headers()
            self.send_header('Content-Length', str(len(resp_bytes)))
            self.end_headers()
            self.wfile.write(resp_bytes)
            return

        # Remote Render Backend Proxy Routes (/health, /api/works, /api/anomalies)
        if url_path == '/health' or url_path.startswith('/api/works') or url_path.startswith('/api/anomalies'):
            target_url = f"{BACKEND_URL}{self.path}"
            try:
                req = urllib.request.Request(
                    target_url,
                    headers={'User-Agent': 'NidhiTrace-Frontend-Proxy/1.0'}
                )
                with urllib.request.urlopen(req, timeout=12) as resp:
                    resp_data = resp.read()
                    self.send_response(resp.status)
                    content_type = resp.headers.get('Content-Type', 'application/json')
                    self.send_header('Content-Type', content_type)
                    self._set_cors_headers()
                    self.send_header('Content-Length', str(len(resp_data)))
                    self.end_headers()
                    self.wfile.write(resp_data)
                    return
            except urllib.error.HTTPError as e:
                # If /api/anomalies/overview is missing on remote backend, fall back to assets/data/overview_kpis.json
                if url_path == '/api/anomalies/overview':
                    if self._serve_local_json('assets/data/overview_kpis.json'):
                        return
                err_data = e.read()
                self.send_response(e.code)
                self.send_header('Content-Type', 'application/json')
                self._set_cors_headers()
                self.send_header('Content-Length', str(len(err_data)))
                self.end_headers()
                self.wfile.write(err_data)
                return
            except Exception as e:
                print(f"[NIDHI Server] Proxy error connecting to {target_url}: {e}")
                # Fallbacks for key endpoints
                if url_path == '/api/anomalies/overview':
                    if self._serve_local_json('assets/data/overview_kpis.json'):
                        return
                elif url_path.startswith('/api/anomalies/summary/breakdown'):
                    if self._serve_local_json('assets/data/analytics_data.json'):
                        return
                elif url_path.startswith('/api/works'):
                    if self._serve_local_json('assets/data/ledger_works.json'):
                        return
                elif url_path.startswith('/api/anomalies'):
                    if self._serve_local_json('assets/data/flagged_cases.json'):
                        return

                self._send_json({"error": f"Failed to connect to backend: {e}", "backend_url": BACKEND_URL}, status_code=502)
                return

        # Default static file handling
        return super().do_GET()

    def do_POST(self):
        url_path = self.path.split('?')[0]

        if url_path == '/api/assistant/chat':
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                if content_length <= 0:
                    self._send_json({"status": "bad_request", "message": "Empty body"}, status_code=400)
                    return

                raw_body = self.rfile.read(content_length).decode('utf-8')
                try:
                    body = json.loads(raw_body)
                except json.JSONDecodeError:
                    self._send_json({"status": "bad_request", "message": "Invalid JSON format"}, status_code=400)
                    return

                client_ip = self.client_address[0] if self.client_address else "127.0.0.1"
                result = handle_chat_request(body, client_ip=client_ip)

                status_code = 200
                if result.get("status") == "rate_limited":
                    status_code = 429
                elif result.get("status") == "bad_request":
                    status_code = 400

                self._send_json(result, status_code=status_code)

            except Exception as e:
                print(f"[NIDHI Server] Error processing chat request: {e}")
                self._send_json({
                    "status": "error",
                    "message": "NIDHI Assistant couldn't complete that request. Please try again.",
                    "mode": "error"
                }, status_code=500)
            return

        self.send_error(404, "Endpoint not found")

    def _send_json(self, data: dict, status_code: int = 200):
        resp_bytes = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self._set_cors_headers()
        self.send_header('Content-Length', str(len(resp_bytes)))
        self.end_headers()
        self.wfile.write(resp_bytes)

    def log_message(self, format, *args):
        first_arg = args[0] if args else ""
        if "/api/" in str(first_arg):
            sys.stderr.write(f"[{self.log_date_time_string()}] API: {format % args}\n")
        else:
            pass

def run_server(port=3000):
    server_address = ('', port)
    httpd = ThreadingHTTPServer(server_address, NidhiTraceRequestHandler)
    print(f"==================================================")
    print(f"  NIDHI TRACE Institutional Platform & Assistant  ")
    print(f"==================================================")
    print(f"  Local URL:   http://localhost:{port}/")
    print(f"  Backend:     {BACKEND_URL}")
    print(f"  API Proxy:   http://localhost:{port}/api/works/")
    print(f"               http://localhost:{port}/api/anomalies/")
    print(f"  Assistant:   http://localhost:{port}/api/assistant/chat")
    print(f"==================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        httpd.server_close()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', '3000'))
    run_server(port)
