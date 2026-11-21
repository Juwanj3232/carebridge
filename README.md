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
* Tests: `python3 -m unittest discover -s tests -v` (24 tests, no network, no key).

## The demo, in order

1. **Pre-Visit Check-In (patient).** Load a scenario or type symptoms. Plain-code safety rules run first.
   Red flags show "Tell the front desk right away / call 911" and alert staff in red. Vague worries ("my heart feels weird") get a nurse check.
2. **Clinic Dashboard (staff, sign-in required).** Queue sorted by urgency, red and amber alerts, 30-second brief with an AI priority agenda
   (every item quotes the patient), **Export to EHR** (clean note + FHIR R4 bundle). The clinician types visit notes, presses
   **Draft patient summary**, reviews each line next to the note text it came from, and presses **Approve and send**.
3. **After-Visit & Costs (patient).** Approved summary only, ending with "Questions? Contact your clinic.", cost table with generic/brand toggle,
   insurance chart, and **Ask about your visit**: answers only from the approved summary, everything else goes to the care team's inbox.
4. **For Clinics.** Savings calculator (labeled estimates), per-provider pricing tiers, comparison table, privacy and EHR plans.

Header toggles: **Español**, **Large text**, **Kiosk** (clinic tablet: patient screens only, large text, "start over" button).

## Files

| Path | What it does |
|---|---|
| `server.py` | Standard-library HTTP server. Serves the API and the built frontend. |
| `backend/safety.py` | Red-flag and vague-symptom rules, English + Spanish. Runs before any AI and can block it. |
| `backend/intake.py` | Turns patient words into the patient prep sheet and the provider brief / priority agenda. |
| `backend/summary.py` | Doctor notes to patient summary. Shorthand dictionary in rules mode; Claude mode drops any line not quoted from the notes. |
| `backend/qa.py` | Patient questions: safety screen, then answer from the approved summary or escalate. |
| `backend/store.py` | In-memory visits, alerts, approval gate, escalated questions. Seeds five synthetic patients. |
| `backend/billing.py` | Visit + test + prescription costs per plan (prototype math). |
| `backend/fhir_export.py` | FHIR R4 Bundle and plain-text note for "Export to EHR". |
| `backend/auth.py` | Demo staff login: PBKDF2 passwords, signed 8-hour tokens, doctor-only approval. |
| `backend/savings.py` | Savings calculator and pricing tiers. |
| `backend/ai.py` | Optional Claude call (`claude-opus-5-5`, structured JSON output, server-side refusal fallback). Returns None on any failure so rules take over. |
| `backend/scenarios.py` | Synthetic "Test Patient" cases. |
| `frontend/` | React + Vite + Tailwind UI. |
| `docs/JUDGE_PREP.md` | Each judge question, what we built, where to show it, and what to say. |
| `STATUS_REPORT.md` | Where the project stands. |

## API

Patient: `GET /api/health`, `/api/scenarios`, `/api/plans`, `/api/pricing`, `/api/patient/visits/<id>?generic=1`;
`POST /api/intake`, `/api/patient/visits/<id>/ask`, `/api/savings`, `/api/login`.

Staff (Bearer token): `GET /api/staff/queue`, `/api/staff/inbox`, `/api/staff/visits/<id>`, `/api/staff/visits/<id>/export`;
`POST /api/staff/visits/<id>/outcome`, `/approve` (doctor only), `/alerts/<aid>/ack`, `/questions/<qid>/resolve`, `/api/staff/reset-demo`.

## Limits (say these before a judge finds them)

* Demo only: synthetic data, in-memory store that resets on restart, demo-grade login. Not for real patient information.
* Safety rules are keyword lists. They catch many phrasings in English and Spanish but can miss misspellings ("chest pian") and unusual wording.
  That is why vague wording and high discomfort go to a nurse, and why staff always see the raw patient text.
* Rules-mode Q&A is cautious: it escalates when unsure (for example "How long do I take it?"), which is the safe failure.
* Spanish after-visit summaries need Claude; in rules mode the draft is English and the clinician is told so.
* The FHIR export uses free text, not SNOMED/ICD/RxNorm codes, and is not sent anywhere.
