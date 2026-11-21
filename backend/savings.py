"""
Savings calculator + pricing tiers (judge items #3 and #11).

All inputs are EXAMPLE ESTIMATES that a clinic edits to match itself; the UI labels them that way.
Three metrics only: minutes saved per check-in, no-shows reduced, after-visit calls reduced.
"""

from __future__ import annotations

# Example per-provider monthly prices. Placeholders for the team to confirm (judge item #11).
TIERS = [
    {"id": "basic", "name": "Basic", "price_per_provider": 99,
     "includes": ["Digital pre-visit check-in (phone, tablet or kiosk)", "Family-medicine intake forms", "Scheduling & reminders",
                  "Red-flag safety screen"]},
    {"id": "plus", "name": "Plus", "price_per_provider": 199,
     "includes": ["Everything in Basic", "AI priority agenda for the nurse/doctor", "Export to EHR (FHIR format)"]},
    {"id": "complete", "name": "Complete", "price_per_provider": 299,
     "includes": ["Everything in Plus", "After-visit explainers with doctor approval", "Patient Q&A grounded in the approved summary",
                  "Cost & generic-savings breakdown"]},
]

DEFAULTS = {
    "patients_per_day": 30,
    "providers": 2,
    "clinic_days_per_month": 21,
    "tier": "complete",
    # 1) check-in time
    "minutes_saved_per_checkin": 5,
    "staff_cost_per_hour": 22,
    # 2) no-shows
    "no_show_rate_pct": 15,
    "no_show_reduction_pct": 20,     # relative reduction from reminders + easier check-in
    "revenue_per_visit": 110,
    # 3) after-visit calls
    "after_visit_calls_per_day": 8,
    "call_reduction_pct": 30,
    "minutes_per_call": 6,
}

LIMITS = {
    "patients_per_day": (1, 400), "providers": (1, 50), "clinic_days_per_month": (1, 31),
    "minutes_saved_per_checkin": (0, 30), "staff_cost_per_hour": (0, 200), "no_show_rate_pct": (0, 60),
    "no_show_reduction_pct": (0, 100), "revenue_per_visit": (0, 1000), "after_visit_calls_per_day": (0, 300),
    "call_reduction_pct": (0, 100), "minutes_per_call": (0, 60),
}


def calculate(raw: dict | None) -> dict:
    p = dict(DEFAULTS)
    for k, (lo, hi) in LIMITS.items():
        if raw and k in raw and raw[k] not in (None, ""):
            try:
                p[k] = max(lo, min(hi, float(raw[k])))
            except (TypeError, ValueError):
                pass
    if raw and raw.get("tier") in {t["id"] for t in TIERS}:
        p["tier"] = raw["tier"]
    tier = next(t for t in TIERS if t["id"] == p["tier"])
    days = p["clinic_days_per_month"]
    visits = p["patients_per_day"] * days

    checkin_hours = visits * p["minutes_saved_per_checkin"] / 60
    checkin_savings = checkin_hours * p["staff_cost_per_hour"]

    booked = visits / max(1e-9, 1 - p["no_show_rate_pct"] / 100)          # appointments booked to get `visits` seen
    no_shows = booked * p["no_show_rate_pct"] / 100
    recovered = no_shows * p["no_show_reduction_pct"] / 100
    no_show_savings = recovered * p["revenue_per_visit"]

    calls_avoided = p["after_visit_calls_per_day"] * days * p["call_reduction_pct"] / 100
    call_hours = calls_avoided * p["minutes_per_call"] / 60
    call_savings = call_hours * p["staff_cost_per_hour"]

    total = checkin_savings + no_show_savings + call_savings
    cost = tier["price_per_provider"] * p["providers"]
    r = lambda x: round(x, 2)
    return {
        "inputs": p, "tier": tier,
        "metrics": [
            {"id": "checkin", "label": "Staff minutes saved at check-in", "detail": f"{r(checkin_hours)} staff hours / month",
             "monthly_value": r(checkin_savings)},
            {"id": "no_shows", "label": "No-shows recovered", "detail": f"{r(recovered)} visits / month recovered",
             "monthly_value": r(no_show_savings)},
            {"id": "calls", "label": "After-visit phone calls avoided", "detail": f"{r(calls_avoided)} calls ({r(call_hours)} staff hours) / month",
             "monthly_value": r(call_savings)},
        ],
        "monthly_savings": r(total),
        "monthly_cost": r(cost),
        "net_monthly": r(total - cost),
        "roi_multiple": r(total / cost) if cost else None,
        "pays_for_itself": total >= cost,
        "disclaimer": "Example estimates only. Replace every input with your clinic's own numbers; results are not a guarantee.",
    }
