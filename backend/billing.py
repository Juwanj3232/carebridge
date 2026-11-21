"""Visit + pharmacy cost breakdown (prototype step 3), computed server-side so the numbers can be tested."""

INSURANCE_PLANS = {
    "ppo": {"label": "BlueCross Silver PPO (demo)", "short": "$30 copay, 80% Rx", "visit_copay": 30, "test_coverage": 0.80, "rx_coverage": 0.80},
    "hmo": {"label": "Aetna Bronze HMO (demo)", "short": "$50 copay, 65% Rx", "visit_copay": 50, "test_coverage": 0.65, "rx_coverage": 0.65},
    "self": {"label": "Uninsured / Self-Pay (30% clinic discount)", "short": "Sliding scale", "visit_copay": None, "test_coverage": 0.30, "rx_coverage": 0.0},
}

SELF_PAY_DISCOUNT = 0.30
DEFAULT_OUTCOME_FEES = {"visit_fee": 130, "test_name": "", "test_fee": 0, "rx_generic_price": 0, "rx_brand_price": 0}


def _money(x: float) -> float:
    return round(float(x) + 1e-9, 2)


def breakdown(plan_key: str, outcome: dict, use_generic: bool = True) -> dict:
    plan = INSURANCE_PLANS.get(plan_key, INSURANCE_PLANS["self"])
    o = {**DEFAULT_OUTCOME_FEES, **(outcome or {})}
    items = []

    visit_billed = float(o["visit_fee"] or 0)
    if plan["visit_copay"] is None:
        visit_patient = _money(visit_billed * (1 - SELF_PAY_DISCOUNT))
    else:
        visit_patient = min(float(plan["visit_copay"]), visit_billed)
    items.append({"kind": "visit", "label": "Family Medicine Office Visit", "billed": visit_billed,
                  "covered": _money(visit_billed - visit_patient), "patient": _money(visit_patient)})

    if o.get("test_name") and float(o.get("test_fee") or 0) > 0:
        billed = float(o["test_fee"])
        covered = _money(billed * plan["test_coverage"])
        items.append({"kind": "test", "label": o["test_name"], "billed": billed, "covered": covered,
                      "patient": _money(billed - covered)})

    has_brand = bool(o.get("rx_brand")) and float(o.get("rx_brand_price") or 0) > 0
    generic_selected = use_generic or not has_brand
    rx_label = o.get("rx_generic") if generic_selected else o.get("rx_brand")
    rx_price = float((o.get("rx_generic_price") if generic_selected else o.get("rx_brand_price")) or 0)
    if rx_label and rx_price > 0:
        covered = _money(rx_price * plan["rx_coverage"])
        items.append({"kind": "rx", "label": rx_label, "billed": rx_price, "covered": covered,
                      "patient": _money(rx_price - covered)})

    total_billed = _money(sum(i["billed"] for i in items))
    total_covered = _money(sum(i["covered"] for i in items))
    total_patient = _money(sum(i["patient"] for i in items))

    out_of_pocket = 1 - plan["rx_coverage"]
    savings = 0.0
    if has_brand and float(o.get("rx_generic_price") or 0) > 0:
        savings = _money((float(o["rx_brand_price"]) - float(o["rx_generic_price"])) * out_of_pocket)

    if savings > 0 and generic_selected:
        tip = f"Choosing the generic saves you ${savings:.2f} out of pocket compared with the brand-name prescription."
    elif savings > 0:
        tip = f"You could save ${savings:.2f} by switching to the FDA-approved generic. Ask the pharmacist."
    else:
        tip = "No prescription cost today. Ask the front desk about payment plans if the visit cost is a burden."

    return {
        "plan_key": plan_key, "plan": plan["label"], "use_generic": generic_selected, "has_brand_option": has_brand,
        "items": items, "total_billed": total_billed, "total_covered": total_covered, "total_patient": total_patient,
        "generic_savings": savings, "tip": tip,
        "disclaimer": "Estimate using demo plan rules. Your final bill depends on your insurer's processing.",
    }
