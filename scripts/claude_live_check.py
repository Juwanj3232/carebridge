"""
Run every Claude-powered step once, for real, and report whether Claude (not the rules fallback) answered.

  Local (uses ANTHROPIC_API_KEY from the environment or .env in the repo root):
      .venv/bin/python scripts/claude_live_check.py

  Deployed site (the key lives in Render's environment, never on this machine):
      python3 scripts/claude_live_check.py --url https://carebridge.onrender.com

Each run makes about three small Claude calls (agenda, summary draft, and one patient question in local mode).
Exit code 0 only when every step was answered by Claude.
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def local() -> list[tuple[str, bool, str, float]]:
    try:
        from dotenv import load_dotenv
        load_dotenv(ROOT / ".env")
    except ImportError:
        pass
    from backend import ai, intake, qa, safety, summary
    from backend.scenarios import SCENARIOS

    if not ai.enabled():
        sys.exit("Claude is off: install the packages (pip install -r requirements.txt) and set ANTHROPIC_API_KEY in .env.")
    print(f"Model: {ai.MODEL}")
    s = SCENARIOS["ear"]
    p = intake.clean_intake(s["intake"])
    rows = []

    t = time.perf_counter()
    brief = intake.provider_brief(p, intake.detect_tags(p["symptoms"]), safety.screen(p["symptoms"]).to_dict())
    rows.append(("Priority agenda (check-in)", brief.get("agenda_source") == "claude",
                 f"{len(brief.get('agenda', []))} agenda items", time.perf_counter() - t))

    t = time.perf_counter()
    draft = summary.draft(s["outcome"], "en")
    rows.append(("After-visit summary draft", draft.get("generated_by") == "claude",
                 draft.get("diagnosis_title", ""), time.perf_counter() - t))

    t = time.perf_counter()
    answer = qa.answer("How often should I use the warm compress?", draft, "en")
    rows.append(("Patient question answer", answer.get("answered_by") == "claude",
                 answer.get("answer", "")[:90], time.perf_counter() - t))
    return rows


def call(base: str, method: str, path: str, body=None, token=None):
    req = urllib.request.Request(base + path, method=method,
                                 data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Content-Type": "application/json",
                                          **({"Authorization": "Bearer " + token} if token else {})})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())


def remote(base: str) -> list[tuple[str, bool, str, float]]:
    base = base.rstrip("/")
    t = time.perf_counter()
    health = call(base, "GET", "/api/health")     # first request may take a minute while a free instance wakes up
    print(f"Site is up ({time.perf_counter() - t:.1f}s). AI mode: {health.get('mode')}, model: {health.get('model')}")
    from backend.scenarios import SCENARIOS
    s = SCENARIOS["ear"]
    rows = []

    t = time.perf_counter()
    visit = call(base, "POST", "/api/intake", s["intake"])
    password = os.environ.get("CAREBRIDGE_DEMO_PASSWORD", "carebridge-demo")
    token = call(base, "POST", "/api/login", {"username": "dr.demo", "password": password})["token"]
    staff = call(base, "GET", f"/api/staff/visits/{visit['visit_id']}", token=token)
    rows.append(("Priority agenda (check-in)", staff["brief"].get("agenda_source") == "claude",
                 f"{len(staff['brief'].get('agenda', []))} agenda items", time.perf_counter() - t))

    t = time.perf_counter()
    v = call(base, "POST", f"/api/staff/visits/{visit['visit_id']}/outcome", s["outcome"], token)
    rows.append(("After-visit summary draft", v["summary_draft"].get("generated_by") == "claude",
                 v["summary_draft"].get("diagnosis_title", ""), time.perf_counter() - t))
    return rows


def main() -> None:
    url = sys.argv[sys.argv.index("--url") + 1] if "--url" in sys.argv else None
    try:
        rows = remote(url) if url else local()
    except urllib.error.URLError as e:
        sys.exit(f"Could not reach {url}: {e}")
    print()
    for name, by_claude, detail, secs in rows:
        print(f"  {'CLAUDE' if by_claude else 'RULES '}  {name:28} {secs:5.1f}s  {detail}")
    ok = all(r[1] for r in rows)
    print("\nEvery step was answered by Claude." if ok else
          "\nSome steps fell back to the rules. Check the server log for '[ai]' lines (key, network, or refusal).")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
