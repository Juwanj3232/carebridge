"""
Red-flag safety screen (judge item #6). Plain code, runs BEFORE any AI call.

Three outcomes:
  emergency      A red-flag phrase was found (chest pain, trouble breathing, suicidal thoughts, ...).
                 The patient is told "Tell the front desk right away / call 911", staff get a red alert,
                 and the AI is never called for that check-in.
  urgent_review  Worrying but vague wording ("my heart feels weird"), a negated red flag
                 ("no chest pain" is still worth a human look), or discomfort 9-10/10.
                 The patient is asked to tell the front desk, and a nurse gets an amber alert.
                 This is our proposed answer to the team's open question on vague symptoms.
  routine        Nothing matched. Normal check-in.

The lists are deliberately over-inclusive: a false alarm costs a nurse one minute, a miss can cost a life.
They cover English and Spanish because the check-in form offers both.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

# (category, staff label, regex patterns). Patterns run on normalized text: lowercase, no accents,
# apostrophes removed, single spaces.
RED_FLAGS: list[tuple[str, str, list[str]]] = [
    ("cardiac", "Chest pain / pressure", [
        r"chest (pain|pressure|tightness|tight|hurts?|is hurting|squeez\w*|crushing|heaviness|heavy)",
        r"(pain|pressure|tightness|squeezing|heaviness) (in|on) (my )?chest",
        r"heart attack",
        r"pain (going|spreading|moving|radiating) (down|to|into) (my )?(left )?(arm|jaw)",
        r"dolor (de|en el) pecho", r"presion en el pecho", r"ataque al corazon",
    ]),
    ("breathing", "Trouble breathing", [
        r"(trouble|difficulty|hard|struggling|cant|cannot|can not|unable to) (to )?(breathe|breathing|breath)",
        r"short(ness)? of breath", r"cant catch my breath", r"gasping", r"choking",
        r"lips (are |turning )?(blue|purple)",
        r"no puedo respirar", r"dificultad para respirar", r"falta de aire", r"me ahogo",
    ]),
    ("self_harm", "Suicidal thoughts / self-harm", [
        r"suicid\w*", r"kill(ing)? myself", r"end(ing)? my life", r"want(ing)? to die", r"better off dead",
        r"hurt(ing)? myself", r"self harm", r"overdos\w*",
        r"quiero morir", r"matarme", r"quitarme la vida", r"hacerme dano",
    ]),
    ("bleeding", "Severe bleeding", [
        r"(severe|heavy|lots of|a lot of|uncontrolled|wont stop|will not stop|non stop) bleeding",
        r"bleeding (that )?(wont|will not|doesnt|does not) stop",
        r"(coughing|vomiting|throwing) up blood", r"blood in (my )?vomit",
        r"sangrado (fuerte|abundante|que no para)", r"vomitando sangre",
    ]),
    ("stroke", "Possible stroke signs", [
        r"face (is )?(drooping|droop)", r"slurred speech", r"(cant|cannot) (speak|talk|move my)",
        r"(sudden )?(numb|weak)(ness)? on one side", r"one side of (my )?(body|face) (is )?(numb|weak)",
        r"worst headache", r"thunderclap headache",
        r"cara caida", r"no puedo hablar",
    ]),
    ("collapse", "Fainting / seizure / unresponsive", [
        r"passed out", r"pass(ed|ing)? out", r"faint(ed|ing)", r"blacked out", r"seizure", r"convulsion",
        r"unconscious", r"unresponsive",
        r"me desmaye", r"desmayo", r"convulsion",
    ]),
    ("allergic", "Severe allergic reaction", [
        r"throat (is )?(closing|swelling|swollen|tight)", r"tongue (is )?(swelling|swollen)", r"anaphyla\w*",
        r"(face|lips) (are |is )?(swelling|swollen)",
        r"garganta (cerrada|hinchada)",
    ]),
]

# Vague-but-worrying phrases: not on the red-flag list, but a human should check soon.
REVIEW_FLAGS: list[tuple[str, str, list[str]]] = [
    ("heart_vague", "Vague heart symptom", [
        r"heart (feels|is|has been|keeps)? ?(weird|funny|strange|off|wrong|racing|pounding|fluttering|skipping|jumping)",
        r"(racing|pounding|fluttering|skipping) heart", r"palpitations?", r"heart (beat|beating) (fast|weird|funny|irregular)",
        r"corazon (raro|acelerado|late rapido)", r"palpitaciones",
    ]),
    ("breathing_vague", "Vague breathing symptom", [
        r"(hard|harder) to breathe", r"winded", r"out of breath", r"wheez\w*",
    ]),
    ("neuro_vague", "Dizziness / confusion", [
        r"(very|really|super|extremely) dizzy", r"room (is )?spinning", r"confus\w*", r"vision (is )?(blurry|blurred|changes?|went)",
        r"mareado", r"confundido",
    ]),
    ("general_vague", "Patient says something feels very wrong", [
        r"something (is |feels )?(really |very )?wrong", r"(feel|feels|feeling) (really )?(off|terrible|awful)",
        r"(scared|afraid|worried) (that )?(i|its|it is) (am )?(dying|serious|bad)",
        r"algo (anda|esta) mal",
    ]),
    ("mental_health", "Mental health concern", [
        r"(hopeless|cant go on|no reason to live|depressed|panic attack)",
        r"sin esperanza", r"deprimid\w*",
    ]),
    ("pregnancy", "Pregnancy symptom", [
        r"pregnan\w* .*(bleeding|cramp|pain)", r"(bleeding|cramp\w*|pain) .*pregnan\w*", r"embarazada",
    ]),
]

NEGATIONS = r"(no|not|denies|deny|without|never|sin|niega)"

PATIENT_MESSAGES = {
    "emergency": {
        "en": {
            "title": "Tell the front desk right away",
            "body": "Something you wrote can be a sign of an emergency. Please tell the front desk now. "
                    "If you are not at the clinic, or symptoms are severe, call 911.",
            "crisis": "If you are thinking about hurting yourself, call or text 988 (Suicide & Crisis Lifeline) or call 911.",
        },
        "es": {
            "title": "Avise a la recepción de inmediato",
            "body": "Algo que escribió puede ser señal de una emergencia. Avise a la recepción ahora. "
                    "Si no está en la clínica, o los síntomas son graves, llame al 911.",
            "crisis": "Si está pensando en hacerse daño, llame o envíe un mensaje al 988 o llame al 911.",
        },
    },
    "urgent_review": {
        "en": {
            "title": "A nurse will check with you shortly",
            "body": "Thanks for telling us. Please let the front desk know you're here so a nurse can talk with you soon. "
                    "If you feel worse while waiting, tell staff right away or call 911.",
        },
        "es": {
            "title": "Una enfermera hablará con usted pronto",
            "body": "Gracias por avisarnos. Informe a la recepción que ya llegó para que una enfermera hable con usted pronto. "
                    "Si se siente peor mientras espera, avise al personal de inmediato o llame al 911.",
        },
    },
}


@dataclass
class SafetyResult:
    level: str = "routine"                       # emergency | urgent_review | routine
    matches: list[dict] = field(default_factory=list)
    ai_allowed: bool = True
    patient_message: dict | None = None
    staff_message: str = ""

    def to_dict(self) -> dict:
        return {
            "level": self.level,
            "matches": self.matches,
            "ai_allowed": self.ai_allowed,
            "patient_message": self.patient_message,
            "staff_message": self.staff_message,
        }


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(c for c in text if not unicodedata.combining(c)).lower()
    text = text.replace("'", "").replace("’", "")
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _is_negated(norm: str, start: int) -> bool:
    """True when a negation word appears in the 3 words before the match ("no chest pain", "denies chest pain")."""
    before = norm[:start].split()[-3:]
    return any(re.fullmatch(NEGATIONS, w) for w in before)


def _scan(norm: str, table) -> list[dict]:
    found = []
    for category, label, patterns in table:
        hits = []
        for pat in patterns:
            for m in re.finditer(rf"\b(?:{pat})\b", norm):
                hits.append({"category": category, "label": label, "phrase": m.group(0),
                             "negated": _is_negated(norm, m.start())})
        if hits:
            # One hit per category; a live (non-negated) mention always wins over "no chest pain".
            found.append(next((h for h in hits if not h["negated"]), hits[0]))
    return found


def screen(text: str, severity: int | None = None, language: str = "en") -> SafetyResult:
    """Screen free text from a patient. Never calls the AI; always returns a decision."""
    lang = language if language in ("en", "es") else "en"
    norm = normalize(text)
    red = _scan(norm, RED_FLAGS)
    review = _scan(norm, REVIEW_FLAGS)

    live_red = [m for m in red if not m["negated"]]
    negated_red = [m for m in red if m["negated"]]
    live_review = [m for m in review if not m["negated"]]

    if live_red:
        msg = dict(PATIENT_MESSAGES["emergency"][lang])
        if not any(m["category"] == "self_harm" for m in live_red):
            msg.pop("crisis", None)
        return SafetyResult(
            level="emergency",
            matches=[{**m, "tier": "red"} for m in live_red] + [{**m, "tier": "amber"} for m in live_review],
            ai_allowed=False,
            patient_message=msg,
            staff_message="RED FLAG: " + "; ".join(f"{m['label']} (\"{m['phrase']}\")" for m in live_red)
                          + ". See patient now; follow clinic emergency protocol.",
        )

    reasons = [{**m, "tier": "amber"} for m in live_review]
    reasons += [{**m, "tier": "amber", "label": m["label"] + " (patient said no, confirm)"} for m in negated_red]
    if severity is not None and severity >= 9:
        reasons.append({"category": "severity", "label": f"Discomfort rated {severity}/10", "phrase": f"{severity}/10",
                        "negated": False, "tier": "amber"})
    if reasons:
        return SafetyResult(
            level="urgent_review",
            matches=reasons,
            ai_allowed=True,
            patient_message=PATIENT_MESSAGES["urgent_review"][lang],
            staff_message="NURSE CHECK: " + "; ".join(f"{m['label']} (\"{m['phrase']}\")" for m in reasons)
                          + ". Check on patient within 10 minutes.",
        )
    return SafetyResult()
