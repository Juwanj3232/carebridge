"""
"Export to EHR" (judge item #4): a FHIR R4 Bundle plus a clean plain-text note staff can paste.

FHIR is the standard many EHRs (Epic, athenahealth, eClinicalWorks, ...) use to exchange data. This export is a
demo: resources carry free text, not SNOMED/ICD/RxNorm codes, and nothing is sent anywhere. A real integration
would POST this bundle to the clinic EHR's FHIR API after SMART-on-FHIR authorization.
"""

from __future__ import annotations

import base64
import re
import uuid
from datetime import datetime, timezone

from . import summary as summary_mod, languages

SYNTHETIC_TAG = {"system": "http://terminology.hl7.org/CodeSystem/v3-ActReason", "code": "HTEST", "display": "test health data"}


def _ref(rid: str) -> str:
    return f"urn:uuid:{rid}"


def _entry(resource: dict) -> dict:
    rid = str(uuid.uuid5(uuid.NAMESPACE_URL, f"carebridge/{resource['resourceType']}/{resource.pop('_key')}"))
    resource["id"] = rid
    resource.setdefault("meta", {})["security"] = [SYNTHETIC_TAG]
    return {"fullUrl": _ref(rid), "resource": resource}


def bundle(visit: dict) -> dict:
    v = visit
    p = v["intake"]
    vid = v["id"]
    entries = []
    patient = _entry({"_key": vid, "resourceType": "Patient", "name": [{"text": p["name"]}],
                      "communication": [{"language": {"text": p.get("interpreter_language") or languages.english_name(p["language"])}, "preferred": True}]})
    pref = {"reference": patient["fullUrl"], "display": p["name"]}
    entries.append(patient)

    encounter = _entry({"_key": vid, "resourceType": "Encounter",
                        "status": "finished" if v.get("summary_approved") else "in-progress",
                        "class": {"system": "http://terminology.hl7.org/CodeSystem/v3-ActCode", "code": "AMB", "display": "ambulatory"},
                        "serviceType": {"text": "Family medicine"},
                        "subject": pref, "reasonCode": [{"text": v["brief"]["chief_complaint"]}],
                        "period": {"start": v["created_at"]}})
    eref = {"reference": encounter["fullUrl"]}
    entries.append(encounter)

    answers = [("symptoms", "What brings you in today?", p["symptoms"]), ("duration", "How long?", p["duration"]),
               ("severity", "Discomfort (1-10)", p["severity"]), ("meds", "Current medicines", p["meds"]),
               ("allergies", "Allergies", p["allergies"]), ("insurance", "Insurance plan", p["insurance"])]
    entries.append(_entry({
        "_key": vid, "resourceType": "QuestionnaireResponse", "status": "completed", "subject": pref, "encounter": eref,
        "authored": v["created_at"],
        "item": [{"linkId": k, "text": t, "answer": [{"valueInteger": a} if isinstance(a, int) else {"valueString": str(a or "")}]}
                 for k, t, a in answers],
    }))

    if v["safety"]["level"] != "routine":
        entries.append(_entry({"_key": vid, "resourceType": "Flag", "status": "active", "subject": pref, "encounter": eref,
                               "category": [{"text": "Safety screen"}],
                               "code": {"text": v["safety"]["staff_message"]}}))

    if p["allergies"] and not re.search(r"\bno\b|none|nkda", p["allergies"], re.I):
        for i, a in enumerate(x.strip() for x in p["allergies"].split(",") if x.strip()):
            entries.append(_entry({"_key": f"{vid}/{i}", "resourceType": "AllergyIntolerance", "patient": pref,
                                   "code": {"text": a}, "clinicalStatus": {"text": "active"}}))
    if p["meds"] and p["meds"].lower() not in ("none", "no", "n/a"):
        for i, m in enumerate(x.strip() for x in p["meds"].split(",") if x.strip()):
            entries.append(_entry({"_key": f"{vid}/{i}", "resourceType": "MedicationStatement", "status": "active",
                                   "subject": pref, "medicationCodeableConcept": {"text": m}, "informationSource": pref}))

    o = v.get("outcome")
    if o:
        entries.append(_entry({"_key": vid, "resourceType": "Condition", "subject": pref, "encounter": eref,
                               "code": {"text": o["diagnosis"]}, "clinicalStatus": {"text": "active"}}))
        rx = o.get("rx_generic") or o.get("rx_brand")
        if rx:
            entries.append(_entry({"_key": vid, "resourceType": "MedicationRequest", "status": "active", "intent": "order",
                                   "subject": pref, "encounter": eref, "medicationCodeableConcept": {"text": rx},
                                   "dosageInstruction": [{"text": o.get("notes", "")}]}))
    if v.get("summary_approved"):
        text = summary_mod.as_text(v["summary_approved"])
        entries.append(_entry({"_key": vid, "resourceType": "DocumentReference", "status": "current",
                               "type": {"text": "Patient after-visit summary (clinician approved)"}, "subject": pref,
                               "context": {"encounter": [eref]},
                               "content": [{"attachment": {"contentType": "text/plain",
                                                           "data": base64.b64encode(text.encode()).decode(),
                                                           "title": "After-visit summary"}}]}))
    return {"resourceType": "Bundle", "type": "collection",
            "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"), "entry": entries}


def note_text(visit: dict) -> str:
    """Clean pre-visit + visit note for copy/paste into any EHR."""
    v, p, b = visit, visit["intake"], visit["brief"]
    lines = [
        "CAREBRIDGE PRE-VISIT CHECK-IN (SYNTHETIC DEMO DATA)",
        f"Patient: {p['name']}    Check-in: {v['created_at']}    Channel: {p['channel']}",
        f"Safety screen: {v['safety']['level'].upper()}" + (f" - {v['safety']['staff_message']}" if v["safety"]["staff_message"] else ""),
        "",
        f"CC: {b['chief_complaint']}",
        f"Onset/severity: {b['onset']}",
        f"HPI: {b['hpi']}",
        f"Meds: {b['meds']}",
        f"Allergies: {b['allergies']}",
        "",
        "Priority agenda:",
    ] + [f"  {i + 1}. [{a['priority']}] {a['item']}" for i, a in enumerate(b["agenda"])]
    o = v.get("outcome")
    if o:
        lines += ["", f"Assessment: {o['diagnosis']}", f"Rx: {o.get('rx_generic') or o.get('rx_brand') or 'none'}", f"Plan: {o['notes']}"]
    if v.get("summary_approved"):
        lines += ["", f"After-visit summary approved by {v['approved_by']} at {v['approved_at']}:",
                  summary_mod.as_text(v["summary_approved"])]
    return "\n".join(lines)
