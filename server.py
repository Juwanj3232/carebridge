"""
CareBridge JSON API + static frontend. Standard library only.

    python3 server.py          # run from this folder, http://localhost:8100

Optional: ANTHROPIC_API_KEY in .env (this folder) turns on Claude for the agenda, summaries and Q&A.
Without it every feature runs on plain-code rules. The red-flag safety screen never uses AI.

Public (patient) endpoints                      Staff endpoints (Bearer token from /api/login)
  GET  /api/health                                GET  /api/staff/queue
  GET  /api/scenarios                             GET  /api/staff/inbox
  GET  /api/sample-visit
  GET  /api/plans                                 GET  /api/staff/visits/<id>
  GET  /api/pricing                               POST /api/staff/visits/<id>/outcome     -> AI draft summary
  POST /api/savings                               POST /api/staff/visits/<id>/approve     -> doctor only
  POST /api/intake                                GET  /api/staff/visits/<id>/export?format=fhir|text
  GET  /api/patient/visits/<id>?generic=1         POST /api/staff/visits/<id>/alerts/<aid>/ack
  POST /api/patient/visits/<id>/ask               POST /api/staff/visits/<id>/questions/<qid>/resolve
  POST /api/login                                 POST /api/staff/reset-demo
  POST /api/patient/visits/<id>/followup          POST /api/staff/visits/<id>/followups/<fid>/resolve
  POST /api/patient/visits/<id>/followup/send-now (demo: skip ahead to the day-3 check-in)
"""

from __future__ import annotations

import json
import os
import re
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:
    pass

from backend import ai, auth, billing, fhir_export, savings, store          # noqa: E402
from backend.scenarios import public_list                                 # noqa: E402

DIST_DIR = ROOT / "frontend" / "dist"
CORS_ORIGINS = {o.strip().rstrip("/") for o in os.environ.get("CORS_ORIGINS", "").split(",") if o.strip()}
MAX_BODY = 100_000


class HttpError(Exception):
    def __init__(self, code: int, message: str):
        super().__init__(message)
        self.code = code


def _require_staff(headers, role: str | None = None) -> dict:
    user = auth.verify(headers.get("Authorization"))
    if not user:
        raise HttpError(401, "Please sign in to the clinic dashboard.")
    if role and user["role"] != role:
        raise HttpError(403, f"Only a {role} can do this.")
    return user


def _visit(vid: str) -> dict:
    v = store.get(vid)
    if not v:
        raise HttpError(404, "Visit not found. The demo resets when the server restarts.")
    return v


def handle_get(path: str, q: dict, headers):
    if path == "/api/health":
        return {"ok": True, **ai.status(), "visits": len(store.VISITS)}
    if path == "/api/scenarios":
        return {"scenarios": public_list()}
    if path == "/api/sample-visit":     # the seeded visit with an approved summary, shown on the after-visit page
        return {"visit_id": store.SAMPLE_VISIT_ID if store.get(store.SAMPLE_VISIT_ID or "") else None}
    if path == "/api/plans":
        return {"plans": [{"id": k, **v} for k, v in billing.INSURANCE_PLANS.items()]}
    if path == "/api/pricing":
        return {"tiers": savings.TIERS, "defaults": savings.DEFAULTS}
    m = re.fullmatch(r"/api/patient/visits/([0-9a-f]+)", path)
    if m:
        generic = q.get("generic", ["1"])[0] != "0"
        store.send_due_followups()
        return store.patient_view(_visit(m.group(1)), generic)

    if path == "/api/staff/queue":
        _require_staff(headers)
        store.send_due_followups()
        return {"queue": store.queue()}
    if path == "/api/staff/inbox":
        _require_staff(headers)
        return store.inbox()
    m = re.fullmatch(r"/api/staff/visits/([0-9a-f]+)", path)
    if m:
        _require_staff(headers)
        return store.staff_view(_visit(m.group(1)))
    m = re.fullmatch(r"/api/staff/visits/([0-9a-f]+)/export", path)
    if m:
        _require_staff(headers)
        v = _visit(m.group(1))
        return {"format": "fhir+text", "fhir": fhir_export.bundle(v), "text": fhir_export.note_text(v),
                "note": "Demo export: FHIR R4 Bundle with free-text codes. Nothing is sent to an EHR."}
    return None


def handle_post(path: str, body: dict, headers):
    if path == "/api/login":
        result = auth.login(body.get("username"), body.get("password"))
        if not result:
            raise HttpError(401, "Wrong username or password.")
        return result
    if path == "/api/intake":
        if not str(body.get("symptoms") or "").strip():
            raise HttpError(400, "Tell us what brings you in today.")
        v = store.create_visit(body, scenario=body.get("scenario"))
        return {"visit_id": v["id"], **store.patient_view(v)}
    if path == "/api/savings":
        return savings.calculate(body)
    m = re.fullmatch(r"/api/patient/visits/([0-9a-f]+)/ask", path)
    if m:
        question = str(body.get("question") or "").strip()[:600]
        if not question:
            raise HttpError(400, "Type a question first.")
        try:
            return store.ask(_visit(m.group(1))["id"], question)
        except ValueError as e:
            raise HttpError(409, str(e))

    if path == "/api/staff/reset-demo":
        _require_staff(headers)
        store.VISITS.clear()
        store.seed_demo()
        return {"ok": True, "queue": store.queue()}
    m = re.fullmatch(r"/api/staff/visits/([0-9a-f]+)/outcome", path)
    if m:
        _require_staff(headers)
        try:
            v = store.set_outcome(_visit(m.group(1))["id"], body)
        except ValueError as e:
            raise HttpError(400, str(e))
        return store.staff_view(v)
    m = re.fullmatch(r"/api/staff/visits/([0-9a-f]+)/approve", path)
    if m:
        user = _require_staff(headers, role="doctor")
        v = store.approve_summary(_visit(m.group(1))["id"], body.get("summary"), user)
        if not v:
            raise HttpError(409, "Generate the draft summary first.")
        return store.staff_view(v)
    m = re.fullmatch(r"/api/staff/visits/([0-9a-f]+)/alerts/([0-9a-f]+)/ack", path)
    if m:
        user = _require_staff(headers)
        a = store.ack_alert(m.group(1), m.group(2), user)
        if not a:
            raise HttpError(404, "Alert not found.")
        return a
    m = re.fullmatch(r"/api/patient/visits/([0-9a-f]+)/followup", path)
    if m:
        message = str(body.get("message") or "").strip()[:600]
        if not message:
            raise HttpError(400, "Type a message first.")
        try:
            return store.patient_view(store.followup_reply(_visit(m.group(1))["id"], message))
        except ValueError as e:
            raise HttpError(409, str(e))
    m = re.fullmatch(r"/api/patient/visits/([0-9a-f]+)/followup/send-now", path)
    if m:     # demo only: skip ahead to day 3 instead of waiting
        v = store.send_checkin(_visit(m.group(1))["id"])
        if not v:
            raise HttpError(409, "Follow-up texts start once the clinician approves the visit summary.")
        return store.patient_view(v)
    m = re.fullmatch(r"/api/staff/visits/([0-9a-f]+)/followups/([0-9a-f]+)/resolve", path)
    if m:
        user = _require_staff(headers)
        reply = str(body.get("reply") or "").strip()
        if not reply:
            raise HttpError(400, "Type a reply first.")
        fl = store.resolve_followup(m.group(1), m.group(2), reply, user)
        if not fl:
            raise HttpError(404, "Follow-up not found.")
        return fl
    m = re.fullmatch(r"/api/staff/visits/([0-9a-f]+)/questions/([0-9a-f]+)/resolve", path)
    if m:
        user = _require_staff(headers)
        qn = store.resolve_question(m.group(1), m.group(2), body.get("reply", ""), user)
        if not qn:
            raise HttpError(404, "Question not found.")
        return qn
    return None


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIST_DIR), **kwargs)

    def log_message(self, fmt, *args):   # keep logs free of query strings (visit ids)
        sys.stderr.write("%s %s\n" % (self.command, urlparse(self.path).path))

    def do_GET(self):
        url = urlparse(self.path)
        if not url.path.startswith("/api/"):
            if not DIST_DIR.exists():
                return self._json(404, {"error": "frontend not built: cd frontend && npm install && npm run build"})
            if not (DIST_DIR / url.path.lstrip("/")).is_file():
                self.path = "/index.html"
            return super().do_GET()
        self._dispatch(lambda: handle_get(url.path, parse_qs(url.query), self.headers))

    def do_POST(self):
        url = urlparse(self.path)
        try:
            length = int(self.headers.get("Content-Length", 0))
            if length > MAX_BODY:
                return self._json(413, {"error": "Request too large."})
            body = json.loads(self.rfile.read(length) or b"{}")
            if not isinstance(body, dict):
                raise ValueError
        except (ValueError, json.JSONDecodeError):
            return self._json(400, {"error": "Invalid JSON."})
        self._dispatch(lambda: handle_post(url.path, body, self.headers))

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def end_headers(self):
        origin = (self.headers.get("Origin") or "").rstrip("/")
        if origin and ("*" in CORS_ORIGINS or origin in CORS_ORIGINS):
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def _dispatch(self, fn):
        try:
            result = fn()
        except HttpError as e:
            return self._json(e.code, {"error": str(e)})
        except Exception as e:   # surface errors to the UI instead of dropping the connection
            self.log_error("error on %s: %r", urlparse(self.path).path, e)
            return self._json(500, {"error": f"{type(e).__name__}: {e}"})
        if result is None:
            return self._json(404, {"error": "not found"})
        self._json(200, result)

    def _json(self, code: int, obj):
        data = json.dumps(obj, default=str).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def make_server(host: str = "127.0.0.1", port: int = 8100, seed: bool = True) -> ThreadingHTTPServer:
    if seed:
        store.seed_demo()
    return ThreadingHTTPServer((host, port), Handler)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8100))
    host = os.environ.get("HOST", "127.0.0.1")
    httpd = make_server(host, port, seed=os.environ.get("CAREBRIDGE_SEED", "1") != "0")
    print(f"CareBridge API on http://{host}:{port}  | AI: {ai.status()['mode']} | frontend: {'served' if DIST_DIR.exists() else 'not built'}")
    print("Demo staff logins: dr.demo / nurse.demo / frontdesk.demo  password: " + auth._DEMO_PASSWORD)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
