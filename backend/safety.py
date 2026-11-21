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
They cover English, Spanish and French because the check-in form offers all three (backend/languages.py).

Spelling tolerance ("chest pian", "cant breth", "siezure"): before giving up, the screen corrects words that are one
or two typos away from a red-flag word (rapidfuzz optimal-string-alignment distance, swaps count as one typo; same first letter; a correction only counts if
it completes a red-flag phrase) and runs the same rules again. Still plain code: no AI is involved at any step.
Measured on 181 test phrasings: python3 scripts/safety_benchmark.py
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

try:   # fast C implementation; the pure-Python fallback below gives the same answers, only slower
    from rapidfuzz.distance import OSA as _DL       # optimal string alignment: edits plus adjacent swaps
except ImportError:   # pragma: no cover - depends on the environment
    _DL = None

# (category, staff label, regex patterns). Patterns run on normalized text: lowercase, no accents,
# apostrophes removed, single spaces.
RED_FLAGS: list[tuple[str, str, list[str]]] = [
    ("cardiac", "Chest pain / pressure", [
        r"chest (is |feels |has been )?(really |very |so )?(pain|pressure|tightness|tight|hurts?|hurting|squeez\w*|crushing|heaviness|heavy)",
        r"(squeez\w*|crushing|pressing on) (my )?chest", r"chest (is |feels )?(like (its |it is )?)?on fire",
        r"(pain|pressure|tightness|squeezing|heaviness) (in|on) (my )?chest",
        r"heart attack",
        r"pain (going|spreading|moving|radiating) (down|to|into) (my )?(left )?(arm|jaw)",
        r"chest (is )?killing me", r"(elephant|something heavy|a weight) (sitting |is sitting )?on (my )?chest",
        r"dolor (de|en el) pecho", r"presion en el pecho", r"ataque al corazon", r"me duele (mucho )?el pecho",
        r"douleur (thoracique|a la poitrine|dans la poitrine|au thorax)", r"(jai )?mal (a la|dans la) poitrine",
        r"(oppression|pression|serrement|poids) (a la|dans la|sur la) poitrine", r"poitrine (me fait (tres |vraiment |si )?mal|serree|qui serre)",
        r"crise cardiaque", r"infarctus",
    ]),
    ("breathing", "Trouble breathing", [
        r"(trouble|difficulty|hard|struggling|cant|cannot|can not|unable to) (to )?(breathe|breathing|breath)",
        r"short(ness)? of breath", r"cant catch my breath", r"(barely|hardly) (breathe|breathing|breath)", r"(isnt|is not|not|stopped) breathing",
        r"(breathing|breathe) is (really |very |so )?(hard|difficult)", r"gasping", r"choking",
        r"lips (are |is )?(turning |going )?(blue|purple|gray|grey)",
        r"(baby|infant|newborn|child|kid|toddler|son|daughter|he|she|face|skin) (is |looks |went |turned |is turning |is going |turning )(blue|purple|gray|grey)",
        r"(cant|cannot|can not) (get|take) (any |enough )?(air|a breath)",
        r"no puedo respirar", r"dificultad para respirar", r"falta de aire", r"me falta el aire", r"me ahogo",
        r"(peux|peut|arrive|narrive|parviens) (pas|plus) a respirer", r"(peux|peut) (pas|plus) respirer",
        r"(difficulte|difficultes|du mal) a respirer", r"manque dair", r"metouffe", r"levres (bleues|violettes)",
        r"(bebe|nino|nina|hijo|hija) (esta |se puso |se esta poniendo )?(morad[oa]|azul)",
        r"(bebe|enfant|fils|fille) (est |devient )(tout )?(bleu|violet)\w*",
    ]),
    ("self_harm", "Suicidal thoughts / self-harm", [
        r"suicid\w*", r"kill?(ing)? my ?self", r"end(ing)? my life", r"want(ing)? to die", r"better off dead",
        r"hurt(ing)? my ?self", r"self harm", r"overdos\w*", r"kms", r"unalive\w*", r"end(ing)? it (all|tonight|today|now)", r"going to end it",
        r"(dont|do not) want to (be alive|live|be here)", r"pills to (end it|die|end my life)",
        r"(gun|pistol|rifle|weapon|knife|rope) .{0,40}(use it|using it|end it|on myself|kill|hurt)",
        r"(thinking about|planning to|going to|want to) (shoot|hang|stab) my ?self",
        r"quiero morir", r"matarme", r"me quiero matar", r"quitarme la vida", r"hacerme dano",
        r"me (tuer|suicider)", r"(envie de|veux) mourir", r"d?en finir", r"mettre fin a (mes jours|ma vie)", r"me faire du mal",
        r"surdose",
    ]),
    ("bleeding", "Severe bleeding", [
        r"(severe|heavy|lots of|a lot of|uncontrolled|wont stop|will not stop|non stop) bleeding",
        r"bleeding (that )?(wont|will not|doesnt|does not) stop",
        r"bleeding .{0,30}(wont|will not|doesnt|does not|cant) stop",
        r"(coughing|vomiting|throwing|spitting) (up )?blood", r"blood in (my )?vomit",
        r"sangrado (fuerte|abundante|que no para)", r"sangr\w* .{0,25}no (para|se detiene)", r"vomitando sangre",
        r"saign\w* (beaucoup|abondamment|sans arret)", r"saignement (abondant|important|qui ne sarrete pas)",
        r"sarrete pas de saigner", r"(crache|vomis|vomit) du sang",
    ]),
    ("stroke", "Possible stroke signs", [
        r"face (is |went |looks |feels )?(drooping|droop\w*)", r"slur\w* speech", r"(having|is having|had) a stroke", r"(cant|cannot) (speak|talk|move my)",
        r"(sudden )?(numb|weak)(ness)? on one side",
        r"(cant|cannot|can not) feel (my |his |her )?(legs?|arms?|face|feet|foot|side)",
        r"(cant|cannot|can not) walk (straight|properly|right|in a straight line)",
        r"no (siento|puedo sentir) (las |mis |el |la |los )?(piernas?|brazos?|cara|pies?)",
        r"(sens|sent) (plus|pas) (mes |ses |la |le )?(jambes?|bras|visage|pieds?)",
        r"(one|left|right) side of (my |his |her )?(body|face) (is |went |feels )?(numb|weak|droop\w*)",
        r"worst headache", r"thunderclap headache",
        r"cara caida", r"no puedo hablar",
        r"visage (est )?(affaisse|tombant|paralyse)\w*", r"(peux|arrive|narrive) (pas|plus) (a )?parler", r"parole (pateuse|confuse)",
        r"(engourdi\w*|faiblesse|paralys\w*) (dun|du) (seul )?cote", r"\bavc\b",
    ]),
    ("collapse", "Fainting / seizure / unresponsive", [
        r"passed out", r"pass(ed|ing)? out", r"faint(ed|ing)", r"black(ed|ing) out", r"seizures?", r"convulsions?",
        r"unconscious", r"unresponsive", r"collapsed", r"(not|isnt|wont|wasnt) waking up",
        r"(wont|will not|doesnt|isnt|is not) wake up(?! (for|in time|early|on time|in the morning))",
        r"(cant|cannot|can not|couldnt) wake (him|her|them|my \w+|the baby|the \w+) up",
        r"(he|she|they|baby|husband|wife|mom|dad|mother|father|son|daughter|child|kid|partner|grandma|grandpa) (is not|isnt|wont|will not|stopped|is) (responding|responsive)(?! to\b)",
        r"(everything|it all|my vision) (went|goes|is going|turned|started going) (black|dark)",
        r"me desmaye", r"desmayo", r"convulsion(es)?",
        r"evanoui\w*", r"perdu connaissance", r"crise (depilepsie|convulsive)", r"inconscient\w*", r"(se )?reveille pas",
    ]),
    ("allergic", "Severe allergic reaction", [
        r"throat (is )?(closing|swelling|swollen|tight)", r"throat (feels )?like (its|it is) (closing|swelling)", r"tongue (is )?(swelling|swollen)", r"anaphyla\w*",
        r"(face|lips) (are |is )?(swelling|swollen)",
        r"garganta (cerrada|hinchada)",
        r"gorge (qui se ferme|se ferme|serree|gonflee|enflee)", r"(langue|levres|visage) (a )?(gonfle|enfle)\w*", r"choc anaphylactique",
    ]),
    ("poisoning", "Overdose / poisoning", [
        r"(took|taken|take|swallowed|ate|had) (way )?too many (of (my|his|her|the) )?(\w+ )?(pills|tablets|meds|medicines?|medications?|capsules)",
        r"(swallowed|drank|ate|ingested|drinking|eating) (some |a lot of |the |a )?(bleach|poison\w*|cleaner|detergent|antifreeze|drain cleaner|batter(y|ies)|laundry pods?|rat poison|pesticide|lighter fluid)",
        r"(tome|tomo|se tomo|trago|me trague) (demasiadas|muchas) (pastillas|pildoras|medicinas)",
        r"(trago|tomo|bebio|se tomo|comio) (cloro|lejia|veneno|detergente)",
        r"(pris|avale) trop de (comprimes|medicaments|pilules|cachets)",
        r"(avale|bu|mange) (de la |du |un |une )?(javel|poison|detergent|pile)",
    ]),
    ("dying", "Patient says they feel like they are dying", [
        r"(feel|feels|feeling) like (im|i am|i was|i might be) dying",
        r"(think|afraid|scared|worried|sure) (that )?(im|i am|i might be) dying",
        r"(im|i am) dying(?! to\b)", r"(im|i am) (going to|gonna|about to) die",
        r"me estoy muriendo", r"(siento que|creo que) me (muero|voy a morir)", r"me voy a morir",
        r"je (suis en train de )?meurs(?! de (faim|soif|chaud|froid|rire|envie|fatigue))", r"(je vais|jai limpression de|jai peur de) mourir",
    ]),
    ("fever", "Very high fever (105 F / 40.5 C or more)", [
        r"(fever|temperature|temp) (of |is |was |at |is at |hit |reached |reading )?(about |around |over )?(10[5-9]|4[1-3]|40 5)\b",
        r"(10[5-9]|4[1-3]) (degree |degrees )?(f |c )?fever",
        r"(fiebre|temperatura) (de |a )?(10[5-9]|4[1-3])\b",
        r"(fievre|temperature) (de |a )?(10[5-9]|4[1-3])\b",
    ]),
    ("low_sugar", "Very low blood sugar", [
        r"(blood sugar|sugar|glucose|bg) (level )?(is |was |at |of |reading |dropped to |down to |went down to )?(about |around |under |below |only )?([1-5]\d)\b",
        r"(azucar|glucosa) (esta |en |de )?([1-5]\d)\b", r"(glycemie|sucre) (est |a |de )?([1-5]\d)\b",
    ]),
    ("head_injury", "Head injury with warning signs", [
        r"(hit|hurt|bumped|banged|injured|smacked) (my |his |her |their )?head .{0,40}(confus\w*|passed out|vomit\w*|throwing up|cant remember|knocked out|drowsy)",
        r"(confus\w*|vomit\w*|throwing up) .{0,30}(hit|hurt|bumped|banged) (my |his |her |their )?head",
        r"knocked (out|unconscious)",
        r"(golpe|me golpee|se golpeo) (en )?la cabeza .{0,40}(confundid\w*|vomit\w*|desmay\w*)",
        r"(cogne|frappe) la tete .{0,40}(confus\w*|vomi\w*|evanoui\w*)",
    ]),
]

# Vague-but-worrying phrases: not on the red-flag list, but a human should check soon.
REVIEW_FLAGS: list[tuple[str, str, list[str]]] = [
    ("heart_vague", "Vague heart symptom", [
        r"heart (feels|is|has been|keeps)? ?(weird|funny|strange|off|wrong|racing|pounding|fluttering|skipping|jumping)",
        r"(racing|pounding|fluttering|skipping) heart", r"palpitations?",
        r"heart (is )?(beating|pounding|racing) (out of my chest|so fast|really fast|very fast)", r"heart (beat|beating) (fast|weird|funny|irregular)",
        r"corazon (esta )?(raro|acelerado|late rapido)", r"palpitaciones",
        r"coeur (qui )?(bat (vite|fort|bizarrement)|semballe|bizarre)",
    ]),
    ("breathing_vague", "Vague breathing symptom", [
        r"(hard|harder) to breathe", r"winded", r"out of breath", r"wheez\w*", r"essouffl\w*",
    ]),
    ("neuro_vague", "Dizziness / confusion", [
        r"(very|really|super|extremely) dizzy", r"room (is )?spinning", r"seeing double", r"double vision",
        r"(cant stop|cannot stop|uncontrollabl\w*) (shaking|trembling)", r"(shaking|trembling|shaky) and (sweating|sweaty|clammy)",
        r"(blood sugar|glucose) (is |was |at |of |reading )?(over |above )?([4-9]\d\d)\b", r"confus\w*", r"vision (is )?(blurry|blurred|changes?|went)",
        r"mareado", r"confundido", r"(tres|vraiment) etourdi\w*", r"la tete (me )?tourne", r"vision (floue|trouble)",
    ]),
    ("general_vague", "Patient says something feels very wrong", [
        r"something (is |feels )?(really |very )?wrong", r"(feel|feels|feeling) (really )?(off|terrible|awful)",
        r"(scared|afraid|worried) (that )?(i|its|it is) (am )?(dying|serious|bad)",
        r"algo (anda|esta) mal", r"quelque chose (ne va pas|va mal)", r"je me sens (tres |vraiment )?mal",
    ]),
    ("mental_health", "Mental health concern", [
        r"(hopeless|cant go on|no reason to live|depressed|panic attack)",
        r"sin esperanza", r"deprimid\w*", r"desespere\w*", r"deprime\w*",
    ]),
    ("severity_text", "Patient rates pain 9 or 10 out of 10", [
        r"(9|10|nine|ten) (out of|outta|on a scale of) (10|ten)", r"(pain|dolor|douleur) (is |es |est )?(a |un )?(9|10) 10",
        r"(9|10) (de|sobre) 10", r"(9|10) sur 10",
    ]),
    ("injury", "Recent accident or injury", [
        r"(was|been|got|were|just had) (in )?(a |an )?(car |auto |motorcycle |bike |traffic )?(accident|crash|wreck|collision)",
        r"hit by a (car|truck|bus|bike)", r"(tuve|tuvimos) un (accidente|choque)", r"(eu|fait) un accident",
    ]),
    ("infant_fever", "Fever in a baby", [
        r"(baby|infant|newborn) .{0,25}(fever|temperature)", r"(bebe) .{0,25}(fiebre|fievre)",
    ]),
    ("pregnancy", "Pregnancy symptom", [
        r"pregnan\w* .*(bleeding|cramp|pain)", r"(bleeding|cramp\w*|pain) .*pregnan\w*", r"embarazada", r"enceinte",
    ]),
]

NEGATIONS = r"(no|not|denies|deny|without|never|dont|doesnt|didnt|havent|hasnt|isnt|arent|wasnt|sin|niega|nunca|pas|sans|aucun|aucune|jamais)"

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
        "fr": {
            "title": "Prévenez l'accueil immédiatement",
            "body": "Ce que vous avez écrit peut être le signe d'une urgence. Prévenez l'accueil maintenant. "
                    "Si vous n'êtes pas à la clinique, ou si les symptômes sont graves, appelez le 911.",
            "crisis": "Si vous pensez à vous faire du mal, appelez ou envoyez un texto au 988, ou appelez le 911.",
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
        "fr": {
            "title": "Une infirmière va vous voir rapidement",
            "body": "Merci de nous l'avoir dit. Signalez votre arrivée à l'accueil pour qu'une infirmière puisse vous parler bientôt. "
                    "Si vous vous sentez plus mal en attendant, prévenez le personnel immédiatement ou appelez le 911.",
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
                hits.append({"category": category, "label": label, "phrase": m.group(0), "span": m.span(),
                             "negated": _is_negated(norm, m.start())})
        if hits:
            # One hit per category; a live (non-negated) mention always wins over "no chest pain".
            found.append(next((h for h in hits if not h["negated"]), hits[0]))
    return found


# ---- Spelling tolerance (plain code, no AI) ----

# Words worth correcting toward: every literal word in the rules, plus full forms of stems the rules match
# with a suffix pattern (suicid\w*, faint(ed|ing), ...) so a typo of the whole word still lands on it.
_EXTRA_WORDS = """shortness seizure suicide suicidal fainted fainting overdose overdosed anaphylaxis anaphylactic squeezing wheezing
    confused confusion pregnant pregnancy seizures convulsions convulsiones drooping breathing breathe breath
    poitrine thoracique respirer evanoui evanouie inconscient inconsciente suicider saigne saignement
    unconscious unresponsive bleeding hurting myself chest pecho respirar""".split()
_VOCAB = frozenset(w for _, _, pats in RED_FLAGS + REVIEW_FLAGS for p in pats for w in re.findall(r"[a-z]{3,}", p)) \
    | frozenset(_EXTRA_WORDS)
# Rule words never used as spelling targets: short or common words whose real-word neighbours are everyday speech
# ("doing", "drying" -> dying; "bills" -> pills; "heal", "heat" -> head). Typed correctly, they still match.
_NOT_TARGETS = frozenset("dying blue head legs pills fever baby meds died".split())
_TARGETS: dict[str, tuple[str, ...]] = {}
for _w in sorted(w for w in _VOCAB if len(w) >= 4 and w not in _NOT_TARGETS):
    _TARGETS.setdefault(_w[0], tuple())
    _TARGETS[_w[0]] += (_w,)


# Real words that sit one typo away from a ONE-word red flag ("cooking" vs "choking", "grasping" vs "gasping").
# They are never corrected. Generated from a dictionary by scripts/build_fuzzy_guard.py, plus a few by hand.
_GUARD_FILE = Path(__file__).with_name("fuzzy_guard.txt")
_GUARD = frozenset(_GUARD_FILE.read_text().split()) if _GUARD_FILE.exists() else frozenset()


def _osa_distance(a: str, b: str) -> int:
    """Optimal-string-alignment distance (edits + adjacent swaps): the same measure as rapidfuzz.distance.OSA."""
    prev2, prev = None, list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i] + [0] * len(b)
        for j, cb in enumerate(b, 1):
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb))
            if prev2 is not None and i > 1 and j > 1 and ca == b[j - 2] and a[i - 2] == cb:
                cur[j] = min(cur[j], prev2[j - 2] + 1)
        prev2, prev = prev, cur
    return prev[-1]


def _distance(a: str, b: str, cutoff: int) -> int:
    if _DL is not None:
        return _DL.distance(a, b, score_cutoff=cutoff)
    d = _osa_distance(a, b)
    return d if d <= cutoff else cutoff + 1


def fuzzy_status() -> str:
    return "rapidfuzz" if _DL is not None else "built-in fallback"


@lru_cache(maxsize=4096)
def _closest(token: str) -> tuple[str, ...]:
    """Rule words a typo most likely meant: same first letter, 1 edit (2 for words of 8+ letters).
    Returns every word at the smallest distance ("hart" -> hard, heart), so each one gets tried."""
    limit = 1 if len(token) < 8 else 2
    found: dict[int, list[str]] = {}
    for w in _TARGETS.get(token[0], ()):
        if abs(len(w) - len(token)) > limit:
            continue
        d = _distance(token, w, limit)
        if d <= limit:
            found.setdefault(d, []).append(w)
    return tuple(found[min(found)][:3]) if found else ()


def _split(token: str) -> list[str] | None:
    """Two rule words typed without a space: "chestpain", "cantbreathe"."""
    for k in range(3, len(token) - 2):
        if token[:k] in _VOCAB and token[k:] in _VOCAB:
            return [token[:k], token[k:]]
    return None


def _corrected(norm: str) -> list[tuple[str, list[int], list[str]]]:
    """Spelling-corrected versions of the text (one per candidate when a typo is ambiguous), each with the
    original-token index of every new token and the original tokens. Empty when nothing needed correcting."""
    tokens = norm.split()
    options: list[list[list[str]]] = []
    changed = False
    for t in tokens:
        choice = None
        if len(t) >= 4 and t not in _VOCAB and t not in _GUARD and not t.isdigit():
            near = _closest(t)
            if near:
                choice = [[w] for w in near]
            elif len(t) >= 7 and (parts := _split(t)):
                choice = [parts]
        if choice:
            changed = True
        options.append(choice or [[t]])
    if not changed:
        return []
    variants = []
    for k in range(max(len(o) for o in options)):
        out, origin = [], []
        for i, o in enumerate(options):
            parts = o[min(k, len(o) - 1)]
            out += parts
            origin += [i] * len(parts)
        variants.append((" ".join(out), origin, tokens))
    return variants


def _with_typos(table, exact: list[dict], variants) -> list[dict]:
    """Add rule hits that only appear after spelling correction, quoting what the patient actually typed."""
    have = {m["category"] for m in exact}
    extra = []
    for text, origin, tokens in variants:
        for m in _scan(text, table):
            if m["category"] in have:
                continue
            start, end = m["span"]
            first, last = origin[text[:start].count(" ")], origin[text[:end].count(" ")]
            typed = " ".join(tokens[first:last + 1])
            if typed == m["phrase"]:
                continue
            have.add(m["category"])
            extra.append({**m, "phrase": f"{typed}, read as {m['phrase']}", "spelling_corrected": True})
    return exact + extra


def screen(text: str, severity: int | None = None, language: str = "en") -> SafetyResult:
    """Screen free text from a patient. Never calls the AI; always returns a decision."""
    lang = language if language in PATIENT_MESSAGES["emergency"] else "en"
    norm = normalize(text)
    red = _scan(norm, RED_FLAGS)
    review = _scan(norm, REVIEW_FLAGS)
    if not [m for m in red if not m["negated"]]:       # only spend time on spelling when no live red flag matched
        variants = _corrected(norm)
        red = _with_typos(RED_FLAGS, red, variants)
        review = _with_typos(REVIEW_FLAGS, review, variants)
    for m in red + review:
        m.pop("span", None)

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
