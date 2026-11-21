# CareBridge: Family Medicine Pre-Visit Check-In | Team Name: GAP - Guiding appointments post & pre

A pre-visit check-in app for family medicine clinics. A Python API makes every decision, and a React frontend shows it
to patients and staff.

**One sentence:** Most tools stop at check-in. CareBridge helps before, during, and after the visit.

## Try it

**Live site: [carebridge-ypuw.onrender.com](https://carebridge-ypuw.onrender.com/)**

* Everything in the demo uses made-up test patients, so you can click anything.
* Staff sign-in for the Clinic Dashboard: `dr.demo` (can approve summaries), `nurse.demo` or `frontdesk.demo`,
  password `carebridge-demo`.
* The site sleeps when nobody has used it for a while, so the first visit can take about a minute to load.

## The demo, in order

The bar at the top of every page loads a test patient with one click.

1. **Check-In (the patient, before the visit).**
   * The patient picks a test patient or types how they feel in their own words.
   * They choose their preferred language: English, Spanish or French. If they pick another language, such as
     Vietnamese, the clinic is told to book an interpreter.
   * Before anything else, a safety check looks for emergency words like "chest pain". If it finds one, the patient
     is told to tell the front desk right away or call 911.
   * Typos still count: "chest pian" is read as "chest pain". Unclear worries, like "my heart feels weird", are sent
     to a nurse to check.
2. **Clinic Dashboard (the staff, during the visit).** Staff sign in first.
   * The list of patients puts the most urgent at the top, marked RED FLAG or Nurse check.
   * Each patient has a 30-second brief for the doctor, built from the patient's own words.
   * **Export to EHR** turns the visit into a note the clinic's records system could take in.
   * The doctor types visit notes and presses **Draft patient summary**. They check each line against their notes,
     then press **Approve and send**. Nothing reaches the patient before a doctor approves it.
   * The inbox at the top shows patient texts and questions that need a person to answer.
3. **After-Visit & Costs (the patient, after the visit).**
   * The patient reads the summary their doctor approved. What to do at home comes first.
   * A cost breakdown shows what the visit and medicines may cost, and how much a generic medicine saves.
   * **Ask about your visit** answers questions using only what the doctor approved. Anything else goes to the clinic.
   * Before a patient's own summary is approved, the page shows a sample (Test Patient Maya).
   * **Follow-up texts:** 3 days later, the app texts "Is your ear feeling better?" and asks if they need anything.
     Every reply gets the same safety check. Emergencies get 911 instructions, and replies like "not better" go to
     the staff inbox. To skip the wait, press **Send the day-3 check-in now**.
4. **For Clinics (clinic owners).**
   * A table compares CareBridge with other check-in tools.
   * **How the AI stays safe** explains the safety rules in plain words.
   * The bottom of the page lists the privacy (HIPAA) and records system (EHR) plans. Each one has a short promise,
     then the exact details. A dot shows whether it works in the demo today or is planned for launch.

Buttons in the top bar:
* **Light / dark mode:** red on white, or red on black. It starts from the device's setting and remembers your choice.
* **Language menu:** English, Español or Français, for every patient screen and the For Clinics page.
* **Large text.**
* **Kiosk:** for a clinic tablet. Patient screens only, large text, and a "start over" button.

A language is only offered once the safety screen can read it. Adding one means its text in `backend/languages.py`
and the modules that use it, its red-flag rules in `backend/safety.py`, and test phrasings in `tests/safety_cases.py`.

## Files

| Path | What it does |
|---|---|
| `server.py` | Standard-library HTTP server. Serves the API and the built frontend. |
| `backend/languages.py` | The patient languages (English, Spanish, French) and helpers. |
| `backend/safety.py` | Red-flag and vague-symptom rules in English, Spanish and French, with spelling tolerance (rapidfuzz, no AI). Runs before any AI and can block it. |
| `backend/fuzzy_guard.txt` | Real words never "corrected" into a one-word red flag ("cooking" vs "choking"). Built by `scripts/build_fuzzy_guard.py`. |
| `backend/intake.py` | Turns patient words into the patient prep sheet and the provider brief / priority agenda, including interpreter requests. |
| `backend/summary.py` | Doctor notes to patient summary. Shorthand dictionary in rules mode; Claude mode drops any line not quoted from the notes. |
| `backend/qa.py` | Patient questions: safety screen, then answer from the approved summary or escalate. |
| `backend/followup.py` | Follow-up agent: day-0 and day-3 texts, safety-screened replies, and what goes to the staff inbox. Plain rules, no AI decisions. |
| `backend/store.py` | In-memory visits, alerts, approval gate, escalated questions, follow-up threads. Seeds five synthetic patients, one with an approved summary. |
| `backend/billing.py` | Visit, test and prescription costs per plan (prototype math). |
| `backend/fhir_export.py` | FHIR R4 Bundle and plain-text note for "Export to EHR". |
| `backend/auth.py` | Demo staff login: PBKDF2 passwords, signed 8-hour tokens, doctor-only approval. |
| `backend/savings.py` | Savings calculator and pricing tiers (not shown in the UI for now). |
| `backend/ai.py` | Optional Claude call (`claude-opus-5-5`, structured JSON output, server-side refusal fallback, daily call cap). Returns None on any failure so rules take over. |
| `backend/scenarios.py` | Synthetic "Test Patient" cases. |
| `frontend/` | React, Vite and Tailwind UI. `src/lib/i18n.js` and `src/lib/clinics-i18n.js` hold the English, Spanish and French text. |
| `tests/test_backend.py` | Backend tests: safety, intake, summaries, Q&A, follow-up agent, languages, interpreter requests, AI cap. |
| `tests/safety_cases.py` | The 341 safety test phrasings: misspellings, slang, Spanish, French, negations, judge-style messages, routine messages, spelling traps. |
| `scripts/safety_benchmark.py` | Scores the safety screen on those phrasings and times it. |
| `scripts/claude_live_check.py` | Runs each Claude step once and shows whether Claude answered. |
| `docs/SAFETY_BENCHMARK.md` | Safety screen results and exactly how they were measured. |
| `docs/JUDGE_PREP.md` | Each judge question, what we built, where to show it, and what to say. |
| `STATUS_REPORT.md` | Where the project stands. |

## API

Patient: `GET /api/health`, `/api/scenarios`, `/api/plans`, `/api/pricing`, `/api/sample-visit`,
`/api/patient/visits/<id>?generic=1`;
`POST /api/intake`, `/api/patient/visits/<id>/ask`, `/api/patient/visits/<id>/followup`,
`/api/patient/visits/<id>/followup/send-now` (demo), `/api/savings`, `/api/login`.

Staff (Bearer token): `GET /api/staff/queue`, `/api/staff/inbox`, `/api/staff/visits/<id>`,
`/api/staff/visits/<id>/export`;
`POST /api/staff/visits/<id>/outcome`, `/approve` (doctor only), `/alerts/<aid>/ack`, `/questions/<qid>/resolve`,
`/followups/<fid>/resolve`, `/api/staff/reset-demo`.

## Limits (say these before a judge finds them)

* Demo only: synthetic data, an in-memory store that resets on restart, and demo-grade login. Not for real patient information.
* Safety rules are keyword lists with spelling tolerance. On 341 test phrasings every emergency reached the 911 screen
  with 0 false alarms, but on wording we had not tuned against, 27 of 31 were caught, and 15 of 22 on judge-style messages written later
  (`docs/SAFETY_BENCHMARK.md`).
  Unusual wording can still be missed: "I got bit by a snake" gets no flag today. That is why vague wording and
  high discomfort go to a nurse, and staff always see the raw patient text.
* Rules-mode Q&A is cautious: it escalates when unsure (for example "How long do I take it?"), which is the safe failure.
* Spanish and French after-visit summaries need Claude; in rules mode the draft is English and the clinician is told so.
  The clinic dashboard (staff) stays in English; every other screen follows the language menu.
* Follow-up texts appear in the app only. Real SMS needs a texting provider and patient consent to receive texts.
  The day-3 check-in is sent when the server next handles a request after it comes due, not by a background scheduler.
* The FHIR export uses free text, not SNOMED/ICD/RxNorm codes, and is not sent anywhere.

## Future feature: AI second opinion

Keyword rules can't know every way to describe an emergency. "I got bit by a snake" has no emergency word, so the
safety check misses it today. The planned fix is an AI second opinion. It is switched off for the website because it
would add a Claude call for every routine message on a public demo link. It fits a standalone app, where each clinic
runs it with its own key and limits.

How it would work:
* **Only when the rules find nothing.** A small, fast model (Claude Haiku 5.5) reads the message at check-in, on
  after-visit questions and on follow-up text replies, and answers one question: could this need care sooner than
  the visit?
* **It can only raise the alarm, never lower it.** The keyword rules still run first, with no AI. If the AI is off,
  slower than 4 seconds or past the daily limit, the patient gets exactly what they get today.
* **The patient is sent to a person, based on where they are:**

  | Who flagged it | At the clinic (kiosk) | At home (phone) |
  |---|---|---|
  | AI only, possible emergency | Tell the front desk right away | Call 911 or go to the nearest ER now |
  | AI only, needs a nurse today | Tell the front desk now | Call the clinic now, urgent care if closed, 911 if worse |

* **Staff check every flag.** An AI FLAG badge marks it in the queue, with the patient's own words the AI was worried
  about. Patients at home can leave an optional call-back number.
* **The rules keep learning.** Every AI flag goes to a "Possible missed rules" list. Staff mark each one Real miss or
  False alarm, and real misses become new safety tests and rules, so the next patient is caught without the AI.
* **Measured before launch.** Score keyword rules alone against rules plus the AI on wording the rules were never
  tuned on, including the AI's false alarms on routine messages.

A full version was built and tested (11 tests, checked in Chrome) in commit `1f23a3b`, then taken out in the commit
after it. Reverting that removal brings it back.
