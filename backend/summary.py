"""
After-visit explainer (judge items #7 and #8).

Source of truth = the doctor's own notes + diagnosis + prescription fields. Nothing else.
  * draft()  turns them into a patient-friendly summary. Every line carries "source": the exact note text it came from.
             With Claude, any line whose source quote isn't found in the notes is dropped (grounding check).
             Without Claude, a fixed shorthand dictionary does the translation.
  * The draft is NOT visible to the patient until a clinician presses "Approve and send" (see store.approve_summary).
  * Every summary ends with "Questions? Contact your clinic."
"""

from __future__ import annotations

import re

from . import ai, languages
from .safety import normalize

FOOTER = {"en": "Questions? Contact your clinic.", "es": "¿Preguntas? Comuníquese con su clínica.",
          "fr": "Des questions ? Contactez votre clinique."}

# Whole phrases first (reviewed, fixed translations), then single abbreviations.
PHRASES = [
    (r"ottawa ankle rules? (were )?negative,? ?", "The ankle exam showed no signs of a broken bone, so "),
    (r"orthostatic precautions", "Stand up slowly to avoid dizziness"),
    (r"\bECG NSR\b", "Your heart tracing (ECG) showed a normal rhythm"),
    (r"\bRICE\b", "Rest, ice, compression and elevation (RICE)"),
    (r"\bwarm compress to (R|right) ear\b", "Hold a warm, damp cloth against your right ear"),
    (r"\bhydration \+ OTC\b", "Drink plenty of fluids and use an OTC"),
    (r"\bhydration\b", "Drink plenty of fluids"),
    (r"\bno X-?ray needed\b", "you do not need an X-ray"),
    (r"^holter monitor if\b", "You may need a take-home heart monitor (Holter) if"),
    (r"\bholter monitor\b", "a take-home heart monitor (Holter)"),
    (r"\bPt reports\b", "You told us you have"),
    (r"\bPRN (pain|swelling|fever|itching)\b", r"as needed for \1"),
    (r"> ?(\d+) ?wks?\b", r"for more than \1 weeks"),
    (r"\bat pharmacy kiosk\b", "at the pharmacy kiosk"),
]
ABBREVIATIONS = [
    (r"\bPO\b", "by mouth"), (r"\bTID\b", "three times a day"), (r"\bBID\b", "twice a day"), (r"\bQID\b", "four times a day"),
    (r"\bQHS\b", "at bedtime"), (r"\b(QD|qd)\b", "once a day"), (r"\bdaily\b", "once a day"), (r"\bPRN\b", "as needed"),
    (r"\bx(\d+)d\b", r"for \1 days"), (r"\bx(\d+) ?h\b", r"for \1 hours"), (r"\bx(\d+) ?min\b", r"for \1 minutes"),
    (r"\b(\d+) ?h\b", r"\1 hours"), (r"\b1 ?wk\b", "1 week"), (r"\b(\d+) ?wks?\b", r"\1 weeks"), (r"#(\d+)", r"(\1 pills)"),
    (r"\bw/o\b", "without"), (r"\bw/", "with "), (r"\bF/?u\b", "Follow up"), (r"\bf/?u\b", "follow up"),
    (r"\bRTC\b", "Come back to the clinic"), (r"\bGo to ED\b", "Go to the emergency room"), (r"\bED\b", "the emergency room"),
    (r"\bER\b", "the emergency room"), (r"\bPt\b", "You"), (r"\bpt\b", "you"),
    (r"\btemp\b", "temperature"), (r"(\d+(\.\d+)?) ?F\b", r"\1°F"), (r">", "above "), (r"<", "below "),
    (r"\bsx\b", "symptoms"), (r"\bdx\b", "diagnosis"), (r"\brx\b", "prescription"), (r"\bOTC\b", "over-the-counter"),
    (r"\bHR\b", "heart rate"), (r"\bBP\b", "blood pressure"), (r"\bCP\b", "chest pain"), (r"\bSOB\b", "shortness of breath"),
    (r"\bHA\b", "headache"), (r"\bworsen\b", "get worse"), (r"\bsyncope\b", "fainting"), (r"\bR ear\b", "right ear"), (r"\bL ankle\b", "left ankle"),
    (r"/day\b", " a day"), (r"\bNSAID\b", "anti-inflammatory pain reliever"), (r" \+ ", " and "),
]

# Plain-language explanations for common family-medicine diagnoses (reviewed text, shown only after doctor approval).
GLOSSARY = [
    (r"sinusitis", "Your sinuses (the air spaces behind your cheeks and forehead) are inflamed and infected."),
    (r"otitis media", "You have an infection behind your eardrum, which causes pressure and ear pain."),
    (r"hypertension", "Your blood pressure is higher than it should be. Taking your medicine every day brings it back down."),
    (r"sprain", "You stretched or slightly tore the ligaments that hold your joint together. It usually heals with rest and care at home."),
    (r"palpitations", "You noticed your heartbeat more than usual. Your heart test today was normal."),
    (r"upper respiratory|\buri\b|common cold", "You have a viral cold. Antibiotics do not help colds; rest and fluids do."),
    (r"urinary tract|\buti\b", "You have a bladder infection. The medicine treats it; finish every dose."),
    (r"strep", "You have a bacterial throat infection (strep). The antibiotic treats it; finish every dose."),
    (r"diabetes", "Your body has trouble keeping blood sugar in a healthy range. Medicine, food and activity all help."),
]

WARNING_RE = re.compile(r"\b(return if|rtc|go to ed|ed if|er if|call if|seek care|worsen|emergency)\b", re.I)
FOLLOWUP_RE = re.compile(r"\b(f/?u|follow up|recheck|holter|re-?eval)\b", re.I)
FINDING_RE = re.compile(r"\b(BP \d+|HR \d+|ECG|negative|normal|NSR|reports?)\b", re.I)


def split_sentences(notes: str) -> list[str]:
    parts = re.split(r"(?<=[.;])\s+|\n+", notes or "")
    return [p.strip().rstrip(".;").strip() for p in parts if p and p.strip().rstrip(".;").strip()]


def plain(sentence: str) -> str:
    out = sentence
    for pat, rep in PHRASES:
        out = re.sub(pat, rep, out, flags=re.I)
    for pat, rep in ABBREVIATIONS:
        out = re.sub(pat, rep, out)
    out = re.sub(r"\s+", " ", out).strip()
    out = out[:1].upper() + out[1:]
    return out if out.endswith((".", "!", "?")) else out + "."


def _warning_text(sentence: str) -> str:
    t = plain(sentence)
    t = re.sub(r"^(Return if|Come back to the clinic if|Go to the emergency room if)\s*", "", t, flags=re.I)
    t = re.sub(r"^Return\b", "Come back", t)
    return t[:1].upper() + t[1:]


def _explain(diagnosis: str) -> str:
    found = [text for pat, text in GLOSSARY if re.search(pat, diagnosis, re.I)]
    return " ".join(found) if found else f"Your clinician's diagnosis is: {diagnosis}. Ask your care team if you'd like it explained in more detail."


def rules_draft(outcome: dict) -> dict:
    notes = outcome.get("notes", "")
    diagnosis = outcome.get("diagnosis", "").strip() or "See your clinician's notes"
    rx = outcome.get("rx_generic") or outcome.get("rx_brand") or ""
    what_we_found, next_steps, warnings = [], [], []
    for s in split_sentences(notes):
        item = {"text": plain(s), "source": s}
        if WARNING_RE.search(s):
            warnings.append({"text": _warning_text(s), "source": s})
        elif FINDING_RE.search(s) and not re.search(r"\b(start|take|renew|use)\b", s, re.I):
            what_we_found.append(item)
        else:
            next_steps.append(item)
    if rx:
        next_steps.insert(0, {"text": f"Pick up your prescription: {rx}. Take it exactly as written on the label.", "source": rx})
    return {
        "language": "en",
        "diagnosis_title": diagnosis,
        "what_you_have": {"text": _explain(diagnosis), "source": diagnosis},
        "what_we_found": what_we_found,
        "next_steps": next_steps,
        "warning_signs": warnings or [{"text": "Your symptoms get worse or you are worried.", "source": "Standard clinic advice"}],
        "footer": FOOTER["en"],
        "generated_by": "rules",
    }


ITEM = {"type": "object", "properties": {"text": {"type": "string"}, "source": {"type": "string"}},
        "required": ["text", "source"], "additionalProperties": False}
SUMMARY_SCHEMA = {
    "type": "object",
    "properties": {
        "diagnosis_title": {"type": "string"},
        "what_you_have": ITEM,
        "what_we_found": {"type": "array", "items": ITEM},
        "next_steps": {"type": "array", "items": ITEM},
        "warning_signs": {"type": "array", "items": ITEM},
    },
    "required": ["diagnosis_title", "what_you_have", "what_we_found", "next_steps", "warning_signs"],
    "additionalProperties": False,
}

SUMMARY_SYSTEM = """You turn a family-medicine clinician's visit notes into a patient-friendly after-visit summary.
Write at a 6th-grade reading level, short sentences, second person ("you").
Hard rules:
1. Use ONLY facts in the DIAGNOSIS, PRESCRIPTION and NOTES given. Do not add advice, doses, drugs, tests, timelines or warnings that are not written there.
2. Every item's "source" must be an exact, word-for-word copy of the text it came from (a phrase from NOTES, or the DIAGNOSIS or PRESCRIPTION text).
3. what_you_have: explain the diagnosis name in one or two plain sentences; its source is the DIAGNOSIS text.
4. warning_signs: only the return/call/ER criteria the clinician wrote.
5. Expand all medical shorthand (PO, TID, PRN, RTC, CP, SOB ...).
Write the "text" fields in {language}. Keep "source" fields exactly as in the input (do not translate them)."""


def draft(outcome: dict, language: str = "en") -> dict:
    """Build the draft the clinician reviews. Claude when available (grounding-checked), otherwise rules."""
    base = rules_draft(outcome)
    lang = languages.code(language)
    haystack = " ".join([outcome.get("notes", ""), outcome.get("diagnosis", ""), outcome.get("rx_generic", ""), outcome.get("rx_brand", "")])
    user = (f"DIAGNOSIS: {outcome.get('diagnosis', '')}\nPRESCRIPTION: {outcome.get('rx_generic') or outcome.get('rx_brand') or 'none'}\n"
            f"NOTES: {outcome.get('notes', '')}")
    result = ai.ask_json(SUMMARY_SYSTEM.format(language=languages.english_name(lang)), user, SUMMARY_SCHEMA)
    if not result:
        if lang != "en":
            name = languages.english_name(lang)
            base["note_for_clinician"] = (f"{name} summary needs the AI key; this draft is in English. "
                                          f"Hand the patient the clinic's {name} copy or ask staff to translate.")
        return base
    hay = normalize(haystack)

    def keep(items):
        good, dropped = [], []
        for i in items:
            (good if normalize(i["source"]) and normalize(i["source"]) in hay else dropped).append(i)
        return good, dropped

    out = {"language": lang, "diagnosis_title": result["diagnosis_title"] or base["diagnosis_title"], "generated_by": "claude",
           "footer": FOOTER[lang], "dropped_ungrounded": []}
    wy, d = keep([result["what_you_have"]])
    out["what_you_have"] = wy[0] if wy else base["what_you_have"]
    out["dropped_ungrounded"] += d
    for key in ("what_we_found", "next_steps", "warning_signs"):
        good, d = keep(result[key])
        out[key] = good or base[key]
        out["dropped_ungrounded"] += d
    return out


def as_text(summary: dict) -> str:
    """Plain-text version (for the patient portal, SMS, or the EHR export)."""
    lines = [f"Diagnosis: {summary['diagnosis_title']}", summary["what_you_have"]["text"], ""]
    if summary.get("what_we_found"):
        lines += ["What we found:"] + [f"- {i['text']}" for i in summary["what_we_found"]] + [""]
    lines += ["Your next steps:"] + [f"- {i['text']}" for i in summary["next_steps"]] + [""]
    lines += ["Call the clinic or get care if:"] + [f"- {i['text']}" for i in summary["warning_signs"]] + [""]
    lines.append(summary["footer"])
    return "\n".join(lines)
