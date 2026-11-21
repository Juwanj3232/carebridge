"""
Patient questions after the visit (judge item #8).

  1. safety.screen() on the question first: "I'm having chest pain now" gets the 911 message, never an AI answer.
  2. Answer ONLY from the clinician-approved summary.
  3. If the answer isn't in it: "I'll send this to your care team", and the question goes on the staff dashboard.

Rules mode: keyword overlap between the question and each approved summary line.
Claude mode: Claude must return a quote; the quote must be found in the approved summary or we escalate.
"""

from __future__ import annotations

import re

from . import ai, safety
from .safety import normalize

STOP = set("""a an the i im me my mine you your yours is are was were be been am do does did can could should would will
to of in on at for with and or if it its this that these those what when where why how which who whom much many
much any some there here have has had get got take taking please doctor clinic okay ok so just still also about
el la los las de del y o que en un una mi me por para con es puedo debo cuando como""".split())

SYNONYMS = {
    "medicine": {"medicine", "medication", "meds", "pill", "pills", "antibiotic", "antibiotics", "dose", "prescription",
                 "amoxicillin", "lisinopril", "naproxen", "tablet", "medicina", "pastilla", "receta"},
    "warning": {"call", "worse", "worried", "emergency", "return", "come", "back", "er", "911", "fever", "temperature",
                "llamar", "peor", "emergencia"},
    "times": {"times", "often", "frequency", "day", "daily", "twice", "three", "veces", "dia"},
    "ice": {"ice", "cold", "swelling", "elevate", "elevation", "rest", "hielo"},
    "heart": {"heart", "ecg", "rhythm", "caffeine", "monitor", "holter", "corazon"},
    "pressure": {"pressure", "bp", "dizzy", "dizziness", "stand", "presion", "mareo"},
    "duration": {"long", "days", "weeks", "until", "finish", "stop", "dias", "semanas"},
}

ANSWER_PREFIX = {"en": "From your approved visit summary: ", "es": "Según el resumen aprobado de su visita: "}
ESCALATE = {
    "en": "I can only answer from your approved visit summary, and it doesn't cover that. I'll send this to your care team. "
          "They'll get back to you. If it's urgent, call the clinic.",
    "es": "Solo puedo responder con el resumen aprobado de su visita, y no incluye eso. Enviaré su pregunta a su equipo de atención. "
          "Le responderán pronto. Si es urgente, llame a la clínica.",
}
FOOTER = {"en": "Questions? Contact your clinic.", "es": "¿Preguntas? Comuníquese con su clínica."}

# Questions that always need a clinician, even if a summary line shares words with them.
ALWAYS_ESCALATE = re.compile(r"\b(alcohol|drink(ing)? (beer|wine)|pregnan|breast ?feed|interact|together with|mix|"
                             r"double (the )?dose|stop taking|skip|another (medicine|drug)|other (medicine|drug)|refund|bill)\b")


def _words(text: str) -> set[str]:
    return {w for w in normalize(text).split() if w not in STOP and len(w) > 1}


def _groups(words: set[str]) -> set[str]:
    return {g for g, members in SYNONYMS.items() if words & members}


def summary_lines(summary: dict) -> list[str]:
    lines = [summary["what_you_have"]["text"]]
    for key in ("what_we_found", "next_steps"):
        lines += [i["text"] for i in summary.get(key, [])]
    lines += ["Call the clinic or get care if: " + i["text"] for i in summary.get("warning_signs", [])]
    return lines


def _rules_answer(question: str, summary: dict) -> str | None:
    q = _words(question)
    if not q or ALWAYS_ESCALATE.search(normalize(question)):
        return None
    qg = _groups(q)
    scored = []
    for line in summary_lines(summary):
        lw = _words(line)
        score = len(q & lw) + 1.5 * len(qg & _groups(lw))
        scored.append((score, line))
    scored.sort(key=lambda x: -x[0])
    if not scored or scored[0][0] < 2:
        return None
    best = [line for s, line in scored if s >= max(2, scored[0][0] - 0.5)][:2]
    return " ".join(best)


QA_SCHEMA = {
    "type": "object",
    "properties": {"answerable": {"type": "boolean"}, "answer": {"type": "string"}, "quote": {"type": "string"}},
    "required": ["answerable", "answer", "quote"], "additionalProperties": False,
}
QA_SYSTEM = """You answer a patient's question about their own clinic visit using ONLY the approved visit summary below.
If the summary clearly answers it, set answerable=true, answer in 1-3 short plain sentences in {language}, and set
"quote" to the exact sentence from the summary you relied on (copied word for word).
If the summary does not clearly answer it (new symptoms, other drugs, alcohol, dose changes, anything not written there),
set answerable=false and leave answer and quote empty. Never give medical advice beyond the summary.

APPROVED SUMMARY:
{summary}"""


def answer(question: str, summary: dict, language: str = "en") -> dict:
    lang = "es" if language == "es" else "en"
    screen = safety.screen(question, language=lang)
    if screen.level == "emergency":
        msg = screen.patient_message
        return {"kind": "emergency", "answer": f"{msg['title']}. {msg['body']}" + (f" {msg['crisis']}" if msg.get("crisis") else ""),
                "escalated": True, "safety": screen.to_dict()}

    text = summary_text_for_ai(summary)
    result = None
    if screen.level == "routine" and not ALWAYS_ESCALATE.search(normalize(question)):
        result = ai.ask_json(QA_SYSTEM.format(language="Spanish" if lang == "es" else "English", summary=text),
                             question, QA_SCHEMA, max_tokens=1500)
    if result is not None:
        grounded = result["answerable"] and normalize(result["quote"]) and normalize(result["quote"]) in normalize(text)
        if grounded:
            return {"kind": "answer", "answer": f"{result['answer']} {FOOTER[lang]}", "quote": result["quote"],
                    "escalated": False, "answered_by": "claude"}
        return {"kind": "escalated", "answer": ESCALATE[lang], "escalated": True, "answered_by": "claude"}

    if screen.level == "urgent_review":
        return {"kind": "escalated", "answer": ESCALATE[lang], "escalated": True, "safety": screen.to_dict(), "answered_by": "rules"}
    found = _rules_answer(question, summary)
    if found:
        return {"kind": "answer", "answer": f"{ANSWER_PREFIX[lang]}{found} {FOOTER[lang]}", "quote": found,
                "escalated": False, "answered_by": "rules"}
    return {"kind": "escalated", "answer": ESCALATE[lang], "escalated": True, "answered_by": "rules"}


def summary_text_for_ai(summary: dict) -> str:
    return "\n".join(summary_lines(summary))
