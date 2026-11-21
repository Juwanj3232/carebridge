"""
Follow-up agent: keeps "after the visit" going once the patient has left the clinic.

  Day 0  When the doctor approves the summary, CareBridge texts the patient that it is ready and that
         it will check in about the visit in 3 days.
  Day 3  A check-in built from the patient's main symptom ("Is your ear feeling better?"),
         then "Do you need anything from us?".

Every reply goes through the same plain-code safety screen as check-in BEFORE anything else.
Red flags get emergency instructions right away. Anything worrying, unclear, or a request for help
lands in the staff inbox for a person to answer. The agent never gives new medical advice: the only
answers it sends come from the doctor-approved summary (qa.answer).

Demo: texts show inside the app instead of going out by SMS, and a demo button sends the day-3 text early.
"""

from __future__ import annotations

import re

from . import languages, qa, safety
from .safety import normalize

CHECKIN_DAYS = 3

# First matching symptom tag (in the order the patient mentioned them) -> day-3 question.
QUESTIONS = {
    "ear": ("Is your ear feeling better?", "¿Se siente mejor su oído?", "Votre oreille va-t-elle mieux ?"),
    "sinus": ("Is your congestion feeling better?", "¿Se siente mejor de la congestión?", "Votre congestion va-t-elle mieux ?"),
    "throat": ("Is your throat feeling better?", "¿Se siente mejor su garganta?", "Votre gorge va-t-elle mieux ?"),
    "cough": ("Is your cough getting better?", "¿Está mejorando su tos?", "Votre toux s'améliore-t-elle ?"),
    "headache": ("Are your headaches getting better?", "¿Están mejorando sus dolores de cabeza?", "Vos maux de tête s'améliorent-ils ?"),
    "dizzy": ("Is the dizziness getting better?", "¿Está mejorando el mareo?", "Les étourdissements s'améliorent-ils ?"),
    "bp": ("How are you doing with your blood pressure medicine?", "¿Cómo le va con su medicina para la presión?", "Comment ça se passe avec votre médicament pour la tension ?"),
    "fever": ("Is your fever gone?", "¿Ya se le quitó la fiebre?", "Votre fièvre est-elle partie ?"),
    "back": ("Is your back feeling better?", "¿Se siente mejor de la espalda?", "Votre dos va-t-il mieux ?"),
    "rash": ("Is your rash getting better?", "¿Está mejorando el sarpullido?", "Votre éruption s'améliore-t-elle ?"),
    "urinary": ("Are your urinary symptoms better?", "¿Están mejor sus síntomas al orinar?", "Vos symptômes urinaires vont-ils mieux ?"),
    "stomach": ("Is your stomach feeling better?", "¿Se siente mejor del estómago?", "Votre estomac va-t-il mieux ?"),
    "swelling": ("Is the swelling going down?", "¿Está bajando la hinchazón?", "L'enflure diminue-t-elle ?"),
}
JOINTS = {"ankle": ("tobillo", "cheville", "elle"), "knee": ("rodilla", "genou", "il"), "wrist": ("muñeca", "poignet", "il")}
GENERIC = ("Are you feeling better since your visit?", "¿Se siente mejor desde su visita?", "Vous sentez-vous mieux depuis votre visite ?")
_INDEX = {"en": 0, "es": 1, "fr": 2}

TEXT = {
    "intro": {
        "en": "Hi {name}, this is CareBridge from your clinic. Your visit summary is ready to review. "
              "I'll check in with you in {days} days to see how you're feeling after your visit. Reply here anytime if you need anything.",
        "es": "Hola {name}, le escribe CareBridge de su clínica. Su resumen de la visita está listo. "
              "Le escribiré en {days} días para saber cómo se siente después de su visita. Responda aquí si necesita algo.",
        "fr": "Bonjour {name}, ici CareBridge de votre clinique. Le résumé de votre visite est prêt. Je reprendrai de vos nouvelles dans {days} jours pour savoir comment vous vous sentez après votre visite. Répondez ici si vous avez besoin de quoi que ce soit.",
    },
    "checkin": {
        "en": "Hi {name}, it's CareBridge checking in about your visit {days} days ago. {question} "
              "Reply here, and let me know if you need anything.",
        "es": "Hola {name}, le escribe CareBridge para saber cómo sigue después de su visita de hace {days} días. {question} "
              "Responda aquí y avíseme si necesita algo.",
        "fr": "Bonjour {name}, ici CareBridge, je prends de vos nouvelles après votre visite d'il y a {days} jours. {question} Répondez ici et dites-moi si vous avez besoin de quelque chose.",
    },
    "ask_needs": {
        "en": "Glad to hear you're feeling better. Do you need anything from us, like a refill, a work or school note, "
              "or a question for your care team?",
        "es": "Qué bueno que se siente mejor. ¿Necesita algo de nosotros, como resurtir una receta, una nota para el trabajo "
              "o la escuela, o hacerle una pregunta a su equipo médico?",
        "fr": "Ravi d'apprendre que vous allez mieux. Avez-vous besoin de quelque chose, comme un renouvellement d'ordonnance, un certificat pour le travail ou l'école, ou une question pour votre équipe soignante ?",
    },
    "all_set": {
        "en": "You're all set. Take care, and reply here anytime if you need anything.",
        "es": "Listo. Cuídese, y responda aquí cuando necesite algo.",
        "fr": "C'est noté. Prenez soin de vous, et répondez ici si vous avez besoin de quoi que ce soit.",
    },
    "not_better": {
        "en": "Thank you for telling me. I've sent this to your care team, and someone will contact you. "
              "If you feel much worse, call the clinic. In an emergency, call 911.",
        "es": "Gracias por avisarme. Envié esto a su equipo médico y alguien se comunicará con usted. "
              "Si se siente mucho peor, llame a la clínica. En una emergencia, llame al 911.",
        "fr": "Merci de me l'avoir dit. J'ai transmis cela à votre équipe soignante, et quelqu'un va vous contacter. Si vous vous sentez beaucoup plus mal, appelez la clinique. En cas d'urgence, appelez le 911.",
    },
    "request": {
        "en": "Got it. I've passed this to your care team. They'll reply here or call you.",
        "es": "Entendido. Le pasé esto a su equipo médico. Le responderán aquí o le llamarán.",
        "fr": "C'est noté. J'ai transmis votre demande à votre équipe soignante. Elle vous répondra ici ou vous appellera.",
    },
    "unclear": {
        "en": "Thanks for your message. I've passed it to your care team so a person can follow up with you.",
        "es": "Gracias por su mensaje. Se lo pasé a su equipo médico para que una persona le dé seguimiento.",
        "fr": "Merci pour votre message. Je l'ai transmis à votre équipe soignante pour qu'une personne fasse le suivi avec vous.",
    },
    "emergency": {
        "en": "What you wrote can be a sign of an emergency. Call 911 now or go to the nearest emergency room. "
              "I've also alerted your care team.",
        "es": "Lo que escribió puede ser señal de una emergencia. Llame al 911 ahora o vaya a la sala de emergencias más cercana. "
              "También avisé a su equipo médico.",
        "fr": "Ce que vous avez écrit peut être le signe d'une urgence. Appelez le 911 maintenant ou rendez-vous aux urgences les plus proches. J'ai aussi prévenu votre équipe soignante.",
    },
    "urgent": {
        "en": "Thank you for telling me. I've sent this to your care team, and a nurse will call you today. "
              "If you feel worse, call the clinic. In an emergency, call 911.",
        "es": "Gracias por avisarme. Envié esto a su equipo médico y una enfermera le llamará hoy. "
              "Si se siente peor, llame a la clínica. En una emergencia, llame al 911.",
        "fr": "Merci de me l'avoir dit. J'ai transmis cela à votre équipe soignante, et une infirmière vous appellera aujourd'hui. Si vous vous sentez plus mal, appelez la clinique. En cas d'urgence, appelez le 911.",
    },
}

# Patterns run on safety.normalize() text (lowercase, no accents or apostrophes). Deliberately over-inclusive:
# when in doubt, a person on the care team reads it.
WORSE = re.compile(r"\b(worse|not (any |much )?better|no better|not (really|improving|good|great|well)|hasnt (gotten |got )?better|"
                   r"still (hurts?|have|has|sick|in pain|bad)|hurts? more|more pain|cant|cannot|throwing up|"
                   r"peor|no (estoy |me siento )?mejor|todavia|sigue|pire|pas mieux|toujours (mal|malade)|empire|saggrave)\b")
# Symptoms only count when not negated ("much better, no fever" is fine).
SYMPTOMS = re.compile(r"\b(fever|pus|bleed\w*|swell\w*|swollen|vomit\w*|fiebre|hinchad\w*|fievre|saign\w*|enfle\w*|gonfle\w*|vomi\w*)\b")
LEADING_NO = re.compile(r"^(no|nope|nah|not really|not yet|non|pas vraiment|pas encore)\b")
BETTER = re.compile(r"\b(better|good|great|fine|well|improv\w*|yes|yeah|yep|yup|ok|okay|mejor|bien|si|mieux|oui|ca va)\b")
NOTHING = re.compile(r"^(no|nope|nah|nothing|im good|all good|im fine|im ok|im okay|no thanks?|no thank you|thats all|"
                     r"nada|no gracias|estoy bien|non merci|rien|ca va|tout va bien)\b")
THANKS = re.compile(r"^(thanks?|thank you|ty|ok|okay|great|cool|gracias|vale|merci|daccord|parfait)\b")
REQUEST = re.compile(r"\b(refills?|appointment|note|need|needs|help|call me|prescriptions?|pharmacy|letter|reschedule|"
                     r"cita|receta|necesito|ayuda|llamen?me|ordonnance|renouvel\w*|rendez vous|certificat|besoin|aide|appelez moi|rappeler)\b")
QUESTION_START = re.compile(r"^(how|what|when|can|could|should|is|are|do|does|will|why|where|como|cuando|que|puedo|debo|es|"
                            r"est ce|comment|quand|combien|puis je|dois je|pourquoi)\b")


def _lang(language: str) -> str:
    return languages.code(language)


def checkin_question(tags: list[dict], symptoms: str, language: str) -> str:
    i = _INDEX[_lang(language)]
    for t in tags:
        if t["id"] == "injury":
            joint = next((j for j in JOINTS if re.search(rf"\b({j}|{JOINTS[j][0]}|{JOINTS[j][1]})", normalize(symptoms))), None)
            if joint:
                return (f"Is your {joint} feeling better?", f"¿Se siente mejor su {JOINTS[joint][0]}?",
                        f"Votre {JOINTS[joint][1]} va-t-{JOINTS[joint][2]} mieux ?")[i]
            return ("Is your injury feeling better?", "¿Se siente mejor de la lesión?", "Votre blessure va-t-elle mieux ?")[i]
        if t["id"] in QUESTIONS:
            return QUESTIONS[t["id"]][i]
    return GENERIC[i]


def text(key: str, language: str, **kw) -> str:
    return languages.pick(TEXT[key], language).format(days=CHECKIN_DAYS, **kw)


def _flag(level: str, reason: str) -> dict:
    return {"level": level, "reason": reason}


def handle_reply(message: str, stage: str, summary: dict | None, language: str) -> dict:
    """Decide what the agent says back and whether a person must see it.

    Returns {"replies": [str], "flag": None | {"level": red|amber|request, "reason": str}, "stage": str}.
    Stages: scheduled (day 0 sent) -> awaiting_checkin (day 3 sent) -> awaiting_needs -> done.
    """
    lang = _lang(language)
    norm = normalize(message)

    # 1. Safety first, exactly like check-in. Plain code, no AI.
    screen = safety.screen(message, None, lang)
    if screen.level == "emergency":
        reply = text("emergency", lang)
        crisis = (screen.patient_message or {}).get("crisis")
        return {"replies": [reply + (f" {crisis}" if crisis else "")], "stage": stage,
                "flag": _flag("red", screen.staff_message.replace("See patient now", "Call the patient now"))}
    if screen.level == "urgent_review":
        return {"replies": [text("urgent", lang)], "stage": stage,
                "flag": _flag("amber", screen.staff_message.replace("Check on patient within 10 minutes", "Call the patient today"))}

    # 2. Not getting better: always a person.
    live_symptom = any(not safety._is_negated(norm, m.start()) for m in SYMPTOMS.finditer(norm))
    if WORSE.search(norm) or live_symptom or (stage == "awaiting_checkin" and LEADING_NO.match(norm)):
        return {"replies": [text("not_better", lang)], "stage": "with_care_team",
                "flag": _flag("amber", "Follow-up: patient says they are not getting better. Call the patient today.")}

    # 3. Asking for something (refill, note, appointment, a call): a person handles it.
    if REQUEST.search(norm):
        return {"replies": [text("request", lang)], "stage": "with_care_team",
                "flag": _flag("request", "Follow-up: patient is asking for something. Reply or call the patient.")}

    # 4. A question: answer only from the approved summary, otherwise a person answers.
    if summary and ("?" in message or QUESTION_START.match(norm)):
        result = qa.answer(message, summary, lang)
        if not result.get("escalated"):
            return {"replies": [result["answer"]], "stage": stage, "flag": None}
        return {"replies": [result["answer"]], "stage": "with_care_team",
                "flag": _flag("request", "Follow-up: question not covered by the approved summary. Reply to the patient.")}

    # 5. The day-3 check-in answered with "better".
    if stage == "awaiting_checkin" and BETTER.search(norm):
        return {"replies": [text("ask_needs", lang)], "stage": "awaiting_needs", "flag": None}

    # 6. "No, I'm good" / "thanks" once there is nothing left to ask.
    if stage != "awaiting_checkin" and (NOTHING.match(norm) or (THANKS.match(norm) and len(norm.split()) <= 4)):
        return {"replies": [text("all_set", lang)], "stage": "done", "flag": None}

    # 7. Anything else: don't guess, hand it to a person.
    return {"replies": [text("unclear", lang)], "stage": "with_care_team",
            "flag": _flag("amber", "Follow-up: reply the agent couldn't sort. Please read it and follow up.")}
