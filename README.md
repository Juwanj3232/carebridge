# CareBridge: Family Medicine Pre-Visit Check-In

A rebuild of the CareBridge prototype (`carebridge_small_clinic_pharmacy_ai_assistant.html`) as a real app:
a Python API that makes every decision, and a React frontend with the prototype's look.
It is a standalone project, separate from the DSU hackathon drought repository.

**One sentence:** Most tools stop at check-in. CareBridge helps before, during, and after the visit.

## Run it

```bash
# from this folder, Python 3.11+ and Node 18+
cd frontend && npm install && npm run build && cd ..
python3 server.py            # open http://localhost:8100
```

* Staff sign-in for the Clinic Dashboard: `dr.demo` (can approve summaries), `nurse.demo`, `frontdesk.demo`.
  Password `carebridge-demo` (printed when the server starts).
* **Optional Claude:** `pip install -r requirements.txt`, then put `ANTHROPIC_API_KEY=...` in `.env` in this folder.
  Without a key the app runs in rules mode and every feature still works. The red-flag safety screen never uses AI.
* Frontend dev with hot reload: `cd frontend && npm run dev` (port 5174, proxies `/api` to 8100).
* Tests: `python3 -m unittest discover -s tests -v` (43 tests, no network, no key).
* Safety screen benchmark: `python3 scripts/safety_benchmark.py --misses` (272 test phrasings, see `docs/SAFETY_BENCHMARK.md`).

## Deploy (Render) and the live demo link

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/Juwanj3232/carebridge)

1. Click the button, or in the Render dashboard choose **New > Blueprint** and pick this repo. `render.yaml` builds the
   `Dockerfile`: one web service serves the API and the React UI.
2. When Render asks for `ANTHROPIC_API_KEY`, paste the key. Leave it empty for rules-only mode. The demo link is public,
   so limit what it can spend, in two layers:
   * **In the app:** `CAREBRIDGE_AI_DAILY_LIMIT` (default 300 in `render.yaml`) caps Claude calls per UTC day. Past the cap
     the app switches to rules mode until midnight UTC; the demo bar shows it.
   * **In the Claude Console:** limits apply per workspace or organization, not per key. Create a workspace just for
     this demo, set its monthly spend limit at platform.claude.com/settings/spend-limits and its requests-per-minute
     limit at platform.claude.com/usage/limits, then create the key inside that workspace.
3. Wait for the deploy, then copy the service URL (for example `https://carebridge.onrender.com`).
4. Prove Claude runs live there: `python3 scripts/claude_live_check.py --url <service URL>`. Every row should say `CLAUDE`.
5. Make the slide QR code: `.venv/bin/pip install segno==1.6.1`, then `.venv/bin/python scripts/make_qr.py <service URL>`.
   It writes `docs/qr-live-demo.png` and `.svg`. Scan it with a phone before presenting.

The free plan sleeps after 15 idle minutes and the first visit then takes about a minute. Open the link a few minutes
before judging. Waking up, or any restart, resets the demo to its five test patients.
To test the container locally: `docker build -t carebridge . && docker run --rm -p 8100:8100 carebridge`.

## The demo, in order

1. **Pre-Visit Check-In (patient).** Load a scenario or type symptoms. Plain-code safety rules run first.
   **Preferred language** on the form switches the whole app to English, Spanish or French. "Another language" records
   it (for example Vietnamese or ASL), keeps the app in a language it can safety-screen, and puts "Book a Vietnamese
   interpreter" near the top of the staff agenda, in the queue and in the EHR export.
   Red flags show "Tell the front desk right away / call 911" and are marked RED FLAG for staff. Vague worries ("my heart feels weird") get a nurse check.
2. **Clinic Dashboard (staff, sign-in required).** Queue sorted by urgency with RED FLAG and Nurse check badges, 30-second brief with an AI priority agenda
   (every item quotes the patient), **Export to EHR** (clean note + FHIR R4 bundle). The clinician types visit notes, presses
   **Draft patient summary**, reviews each line next to the note text it came from, and presses **Approve and send**.
   Flagged follow-up texts and escalated patient questions show at the top with a reply box.
3. **After-Visit & Costs (patient).** Approved summary only, with the next steps at home first and "Questions? Contact your clinic." at the end.
   Cost table with generic/brand toggle and the estimated out-of-pocket total, and **Ask about your visit**: answers only from the approved summary.
   Until the patient's own summary is approved, the page shows the seeded sample (Test Patient Maya).
   **Follow-up texts:** on approval the follow-up agent texts that the summary is ready and that it will check in about the visit in 3 days.
   On day 3 it asks about the main symptom ("Is your ear feeling better?") and whether the patient needs anything. Every reply goes through
   the same safety screen as check-in. Red flags get 911 instructions; "not better", requests and unclear replies land in the staff inbox.
   The demo button **Send the day-3 check-in now** skips the wait.
4. **For Clinics.** Comparison table and **How the AI stays safe** across the full width. A strip on the bottom border lists the
   privacy (HIPAA) and records (EHR) plans: each item has a plain-English promise, the precise version for compliance and IT
   staff, and a dot showing whether it is live in the demo or planned for launch. (Savings calculator and pricing are hidden for now; the logic stays in `backend/savings.py`.)

Header controls: a **light / dark theme** button (red on white, red on black; it starts from the device setting and is remembered
on that device); a **language menu** (English, Español, Français) for every patient screen, check-in prep, answers and follow-up texts;
**Large text**; **Kiosk** (clinic tablet: patient screens only, large text, "start over" button).
A language is only offered once the safety screen can read it: adding one means its text in `backend/languages.py` and the modules that use it,
its red-flag rules in `backend/safety.py`, and test phrasings in `tests/safety_cases.py`.

## Files

| Path | What it does |
|---|---|
| `server.py` | Standard-library HTTP server. Serves the API and the built frontend. |
| `backend/languages.py` | The patient languages (English, Spanish, French) and helpers. |
| `backend/safety.py` | Red-flag and vague-symptom rules in English, Spanish and French, with spelling tolerance (rapidfuzz, no AI). Runs before any AI and can block it. |
| `backend/fuzzy_guard.txt` | Real words never "corrected" into a one-word red flag ("cooking" vs "choking"). Built by `scripts/build_fuzzy_guard.py`. |
| `backend/intake.py` | Turns patient words into the patient prep sheet and the provider brief / priority agenda. |
| `backend/summary.py` | Doctor notes to patient summary. Shorthand dictionary in rules mode; Claude mode drops any line not quoted from the notes. |
| `backend/qa.py` | Patient questions: safety screen, then answer from the approved summary or escalate. |
| `backend/followup.py` | Follow-up agent: day-0 and day-3 texts, safety-screened replies, and what goes to the staff inbox. Plain rules, no AI decisions. |
| `backend/store.py` | In-memory visits, alerts, approval gate, escalated questions, follow-up threads. Seeds five synthetic patients, one with an approved summary. |
| `backend/billing.py` | Visit + test + prescription costs per plan (prototype math). |
| `backend/fhir_export.py` | FHIR R4 Bundle and plain-text note for "Export to EHR". |
| `backend/auth.py` | Demo staff login: PBKDF2 passwords, signed 8-hour tokens, doctor-only approval. |
| `backend/savings.py` | Savings calculator and pricing tiers (not shown in the UI for now). |
| `backend/ai.py` | Optional Claude call (`claude-opus-5-5`, structured JSON output, server-side refusal fallback). Returns None on any failure so rules take over. |
| `backend/scenarios.py` | Synthetic "Test Patient" cases. |
| `frontend/` | React + Vite + Tailwind UI. |
| `tests/safety_cases.py` | The 272 safety test phrasings: misspellings, slang, Spanish, French, negations, routine messages, spelling traps. |
| `scripts/safety_benchmark.py` | Scores the safety screen on those phrasings and times it. |
| `scripts/claude_live_check.py` | Runs each Claude step once, locally or against the deployed site, and shows whether Claude answered. |
| `scripts/make_qr.py` | QR code for the live demo link, for the slides. |
| `Dockerfile`, `render.yaml` | One-container deploy: builds the UI, then runs `server.py`. Render blueprint. |
| `docs/SAFETY_BENCHMARK.md` | Safety screen results and exactly how they were measured. |
| `docs/JUDGE_PREP.md` | Each judge question, what we built, where to show it, and what to say. |
| `STATUS_REPORT.md` | Where the project stands. |

## API

Patient: `GET /api/health`, `/api/scenarios`, `/api/plans`, `/api/pricing`, `/api/sample-visit`, `/api/patient/visits/<id>?generic=1`;
`POST /api/intake`, `/api/patient/visits/<id>/ask`, `/api/patient/visits/<id>/followup`, `/api/patient/visits/<id>/followup/send-now` (demo), `/api/savings`, `/api/login`.

Staff (Bearer token): `GET /api/staff/queue`, `/api/staff/inbox`, `/api/staff/visits/<id>`, `/api/staff/visits/<id>/export`;
`POST /api/staff/visits/<id>/outcome`, `/approve` (doctor only), `/alerts/<aid>/ack`, `/questions/<qid>/resolve`, `/followups/<fid>/resolve`, `/api/staff/reset-demo`.

## Limits (say these before a judge finds them)

* Demo only: synthetic data, in-memory store that resets on restart, demo-grade login. Not for real patient information.
* Safety rules are keyword lists with spelling tolerance. On 272 test phrasings every emergency reached the 911 screen with
  0 false alarms, but on wording we had not tuned against, 27 of 31 were caught (`docs/SAFETY_BENCHMARK.md`). Unusual wording
  can still be missed, which is why vague wording and high discomfort go to a nurse and staff always see the raw patient text.
* Rules-mode Q&A is cautious: it escalates when unsure (for example "How long do I take it?"), which is the safe failure.
* Spanish and French after-visit summaries need Claude; in rules mode the draft is English and the clinician is told so.
  The clinic dashboard (staff) stays in English; every other screen, including For Clinics, follows the language menu.
* Follow-up texts appear in the app only. Real SMS needs a texting provider and patient consent to receive texts.
  The day-3 check-in is sent when the server next handles a request after it comes due, not by a background scheduler.
* The FHIR export uses free text, not SNOMED/ICD/RxNorm codes, and is not sent anywhere.
