"""
In-memory visit store for the demo (resets on restart; no real patient data is ever stored).
A real product would use HIPAA-eligible hosting with encryption at rest and an audit log (docs/JUDGE_PREP.md).
"""

from __future__ import annotations

import copy
import threading
import uuid
from datetime import datetime, timedelta, timezone

from . import billing, intake, qa, safety, summary
from .scenarios import SCENARIOS

_LOCK = threading.RLock()
VISITS: dict[str, dict] = {}
LEVEL_ORDER = {"emergency": 0, "urgent_review": 1, "routine": 2}


def _now(offset_min: int = 0) -> str:
    return (datetime.now(timezone.utc) - timedelta(minutes=offset_min)).isoformat(timespec="seconds")


def create_visit(body: dict, scenario: str | None = None, minutes_ago: int = 0) -> dict:
    p = intake.clean_intake(body)
    screen = safety.screen(p["symptoms"], p["severity"], p["language"]).to_dict()     # 1. safety first, plain code
    tags = intake.detect_tags(p["symptoms"])
    v = {
        "id": uuid.uuid4().hex[:12],
        "created_at": _now(minutes_ago),
        "scenario": scenario if scenario in SCENARIOS else None,
        "intake": p,
        "tags": tags,
        "safety": screen,
        "patient_prep": None if screen["level"] == "emergency" else intake.patient_prep(p, tags, p["language"]),
        "brief": intake.provider_brief(p, tags, screen),                              # AI only if screen allowed it
        "status": "sent_to_emergency" if screen["level"] == "emergency" else "checked_in",
        "outcome": None, "summary_draft": None, "summary_approved": None, "approved_by": None, "approved_at": None,
        "questions": [],
        "alerts": [],
    }
    if screen["level"] != "routine":
        v["alerts"].append({"id": uuid.uuid4().hex[:8], "level": "red" if screen["level"] == "emergency" else "amber",
                            "message": screen["staff_message"], "created_at": v["created_at"], "acknowledged": False})
    with _LOCK:
        VISITS[v["id"]] = v
    return v


def get(visit_id: str) -> dict | None:
    with _LOCK:
        return VISITS.get(visit_id)


def queue() -> list[dict]:
    with _LOCK:
        visits = list(VISITS.values())
    def key(v):
        open_alert = any(not a["acknowledged"] for a in v["alerts"])
        return (0 if open_alert else 1, LEVEL_ORDER[v["safety"]["level"]], v["created_at"])
    return [{
        "id": v["id"], "name": v["intake"]["name"], "created_at": v["created_at"], "status": v["status"],
        "level": v["safety"]["level"], "chief_complaint": v["brief"]["chief_complaint"], "severity": v["intake"]["severity"],
        "open_alerts": sum(not a["acknowledged"] for a in v["alerts"]),
        "open_questions": sum(q["escalated"] and q["status"] == "open" for q in v["questions"]),
        "language": v["intake"]["language"], "channel": v["intake"]["channel"],
    } for v in sorted(visits, key=key)]


def inbox() -> dict:
    """Everything staff must act on: unacknowledged alerts and escalated patient questions."""
    with _LOCK:
        visits = list(VISITS.values())
    alerts = [{**a, "visit_id": v["id"], "name": v["intake"]["name"]} for v in visits for a in v["alerts"] if not a["acknowledged"]]
    alerts.sort(key=lambda a: (a["level"] != "red", a["created_at"]))
    questions = [{**q, "visit_id": v["id"], "name": v["intake"]["name"]} for v in visits for q in v["questions"]
                 if q["escalated"] and q["status"] == "open"]
    return {"alerts": alerts, "questions": questions}


def set_outcome(visit_id: str, body: dict) -> dict | None:
    v = get(visit_id)
    if not v:
        return None
    o = {
        "diagnosis": str(body.get("diagnosis") or "").strip()[:200],
        "rx_generic": str(body.get("rx_generic") or "").strip()[:200],
        "rx_brand": str(body.get("rx_brand") or "").strip()[:200],
        "notes": str(body.get("notes") or "").strip()[:3000],
        "test_name": str(body.get("test_name") or "").strip()[:120],
    }
    for k in ("visit_fee", "test_fee", "rx_generic_price", "rx_brand_price"):
        try:
            o[k] = max(0.0, min(100000.0, float(body.get(k) or 0)))
        except (TypeError, ValueError):
            o[k] = 0.0
    if not o["notes"] or not o["diagnosis"]:
        raise ValueError("Enter a diagnosis and the visit notes first.")
    draft = summary.draft(o, v["intake"]["language"])          # may call Claude: do it outside the lock
    with _LOCK:
        v["outcome"] = o
        v["summary_draft"] = draft
        v["summary_approved"] = None
        v["approved_by"] = v["approved_at"] = None
        v["status"] = "summary_draft"
    return v


def approve_summary(visit_id: str, edited: dict | None, user: dict) -> dict | None:
    v = get(visit_id)
    if not v or not v["summary_draft"]:
        return None
    final = copy.deepcopy(v["summary_draft"])
    if edited:   # the clinician may edit any line before sending
        for key in ("what_we_found", "next_steps", "warning_signs"):
            if isinstance(edited.get(key), list):
                final[key] = [{"text": str(i.get("text", ""))[:500], "source": str(i.get("source", "Edited by clinician"))[:500]}
                              for i in edited[key] if str(i.get("text", "")).strip()]
        if isinstance(edited.get("what_you_have"), dict) and edited["what_you_have"].get("text"):
            final["what_you_have"] = {"text": str(edited["what_you_have"]["text"])[:800],
                                      "source": edited["what_you_have"].get("source", final["what_you_have"]["source"])}
        if edited.get("diagnosis_title"):
            final["diagnosis_title"] = str(edited["diagnosis_title"])[:200]
    final["footer"] = summary.FOOTER.get(final.get("language", "en"), summary.FOOTER["en"])   # always present
    with _LOCK:
        v["summary_approved"] = final
        v["approved_by"] = user.get("name", user.get("username"))
        v["approved_at"] = _now()
        v["status"] = "summary_sent"
    return v


def ask(visit_id: str, question: str) -> dict | None:
    v = get(visit_id)
    if not v:
        return None
    if not v["summary_approved"]:
        raise ValueError("Your visit summary isn't approved yet. You can ask questions once your clinician sends it.")
    result = qa.answer(question, v["summary_approved"], v["intake"]["language"])
    entry = {"id": uuid.uuid4().hex[:8], "question": question, "answer": result["answer"], "kind": result["kind"],
             "escalated": result["escalated"], "status": "open" if result["escalated"] else "answered",
             "created_at": _now(), "reply": None}
    with _LOCK:
        v["questions"].append(entry)
        if result["kind"] == "emergency":
            v["alerts"].append({"id": uuid.uuid4().hex[:8], "level": "red", "created_at": entry["created_at"], "acknowledged": False,
                                "message": "RED FLAG in after-visit question: \"" + question[:200] + "\". Call the patient now."})
    return entry


def resolve_question(visit_id: str, qid: str, reply: str, user: dict) -> dict | None:
    v = get(visit_id)
    if not v:
        return None
    with _LOCK:
        for q in v["questions"]:
            if q["id"] == qid:
                q["status"] = "resolved"
                q["reply"] = {"text": str(reply or "").strip()[:1000], "by": user.get("name"), "at": _now()}
                return q
    return None


def ack_alert(visit_id: str, alert_id: str, user: dict) -> dict | None:
    v = get(visit_id)
    if not v:
        return None
    with _LOCK:
        for a in v["alerts"]:
            if a["id"] == alert_id:
                a["acknowledged"] = True
                a["acknowledged_by"] = user.get("name")
                a["acknowledged_at"] = _now()
                return a
    return None


def staff_view(v: dict) -> dict:
    return {**v, "billing": billing.breakdown(v["intake"]["insurance"], v["outcome"]) if v["outcome"] else None}


def patient_view(v: dict, use_generic: bool = True) -> dict:
    """What the patient may see. Never includes the unapproved draft or staff-only notes."""
    approved = v["summary_approved"]
    return {
        "id": v["id"], "name": v["intake"]["name"], "language": v["intake"]["language"], "status": v["status"],
        "safety": {"level": v["safety"]["level"], "patient_message": v["safety"]["patient_message"]},
        "patient_prep": v["patient_prep"],
        "summary": approved,
        "summary_status": "approved" if approved else ("awaiting_approval" if v["summary_draft"] else "not_started"),
        "approved_by": v["approved_by"], "approved_at": v["approved_at"],
        "billing": billing.breakdown(v["intake"]["insurance"], v["outcome"], use_generic) if approved and v["outcome"] else None,
        "questions": [{k: q[k] for k in ("id", "question", "answer", "kind", "escalated", "status", "reply", "created_at")}
                      for q in v["questions"]],
    }


def seed_demo() -> None:
    """Fill the dashboard queue with the synthetic scenarios so the demo never starts empty."""
    for i, (key, s) in enumerate(reversed(list(SCENARIOS.items()))):
        create_visit({**s["intake"], "channel": "kiosk" if key == "bp" else "phone"}, scenario=key, minutes_ago=5 + i * 7)
