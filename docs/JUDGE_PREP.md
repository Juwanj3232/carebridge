# Judge & Clinic Prep: What We Built for Each Question

For the team. Each of the 12 items from the prep list, with what exists in the app, where to show it, and what to say.
Status key: **Built** (in the app and tested) · **In app, team to confirm** (built with placeholder choices) · **Team task** (needs people, not code).

## 1. Audience is too broad: Built
- The check-in form, symptom tags, diagnosis glossary and demo patients are all **family medicine**.
- The For Clinics page opens with: "We start with independent family medicine clinics, then expand to other specialties."
- **Say:** "We start with family medicine clinics, then expand to other specialties."

## 2. Competitors already exist: In app, team to confirm
- For Clinics has a comparison table: CareBridge vs. a typical check-in tool, with rows for the AI priority agenda, the after-visit explainer, and small-clinic pricing.
- The "typical tool" column is our general read of the category. **Before quoting Phreesia or anyone by name, check their current features.**
- **Say:** "Most tools stop at check-in. We help before, during, and after the visit."
- Team task: put the same table on a slide.

## 3. No proof it saves money: In app, team to confirm
- For Clinics has a live savings calculator with exactly three metrics: staff minutes saved per check-in, no-shows recovered, after-visit calls avoided.
- A clinic enters patients per day, providers and days; it shows monthly savings vs. the subscription and a return multiple. Every assumption is editable.
- It is labeled "Example estimates" twice. The default numbers are placeholders, not research. Replace them with a real clinic's numbers if you get any.

## 4. Doesn't connect to clinic records (EHR): Built (mock)
- Clinic Dashboard: **Export to EHR** opens a clean clinical note to paste into any EHR, plus a **FHIR R4 Bundle** (Patient, Encounter, QuestionnaireResponse, Flag, AllergyIntolerance, MedicationStatement, Condition, MedicationRequest, DocumentReference). Copy or download.
- **Know this:** FHIR (Fast Healthcare Interoperability Resources) is the HL7 standard format many EHRs use to share data. Real hookups use the EHR's FHIR API with SMART on FHIR sign-in.
- **Say:** "We'd integrate with the 1–2 EHRs most common among small clinics first."

## 5. Patient privacy (HIPAA): Built for the demo; plan memorized for the product
- Every demo patient is named "Test Patient …". The banner, footer and export all say synthetic data.
- The Clinic Dashboard needs a staff sign-in. Only the doctor account can approve summaries. Nothing is written to disk.
- **Real-product plan (memorize):** HIPAA-compliant hosting, encrypted data in transit and at rest, staff access controls with audit logs, and a signed business associate agreement (BAA) with each clinic.

## 6. Urgent symptoms on the check-in form: Built
- `backend/safety.py` is plain code that runs **before** any AI. Red-flag list covers chest pain, trouble breathing, suicidal thoughts, severe bleeding, stroke signs, fainting/seizure, severe allergic reaction, in English and Spanish.
- On a hit, the patient sees **"Tell the front desk right away / call 911"** (plus 988 for self-harm), staff get a **red** alert at the top of the dashboard, and the AI is never called.
- **Demo it:** load "Red flag: chest pain", press Check in, then open the Clinic Dashboard.
- **Open question (vague wording like "my heart feels weird"):** we built a proposed answer for the team to accept or change. Vague but worrying phrases, a red flag the patient denies ("no chest pain"), or discomfort 9–10/10 all trigger an **amber nurse check**: the patient is asked to tell the front desk, and a nurse is asked to check within 10 minutes. Demo with the "heart feels weird" scenario.

## 7. Where does the after-visit summary come from? Built
- The clinician types brief visit notes (shorthand is fine) and presses **Draft patient summary**. Each line of the draft shows the note text it came from.
- The patient sees nothing until a doctor presses **Approve and send**. The doctor can edit any line first.
- **Say:** "Later we can connect to AI scribe tools clinics already use."

## 8. AI could explain something wrong: Built
- With Claude on, any summary line whose quote is not found in the doctor's notes is removed automatically, and the doctor sees what was removed.
- Patient Q&A answers only from the approved summary. If the answer isn't there: "I'll send this to your care team", and the question appears in the staff inbox for a reply.
- New emergencies typed as questions ("I have chest pain now") get the 911 message and a red staff alert.
- Every summary ends with "Questions? Contact your clinic."
- **Demo it:** ask "How many times a day do I take the antibiotic?" (answered) then "Can I drink alcohol with this?" (sent to the care team).

## 9. Not every patient uses smartphones: Built
- **Kiosk** toggle: clinic-tablet mode with patient screens only, large text and a "Start over for the next patient" button.
- **Large text** toggle and an **Español** toggle on every patient screen. Safety messages and the check-in prep work in Spanish without AI.
- **Say:** "Front desk staff can always fill it out with the patient." (The form says this too.)

## 10. How will you find clinics? Team task
- The plan line is on the For Clinics page: free 30-day pilot for 2–3 local independent clinics, then paid.
- Still to do: talk to one receptionist or office manager before the hackathon and get a real quote.

## 11. Pricing is vague: In app, team to confirm
- Tiers per provider per month on For Clinics and in the calculator: **Basic $99**, **Plus $199**, **Complete $299** (placeholders).
- Basic = check-in, forms, scheduling, reminders. Plus = adds the AI priority agenda. Complete = adds after-visit explainers and patient Q&A.
- Team task: pick the real prices, then re-check the calculator still shows the app paying for itself.

## 12. Wording: Done in the app; slides are a team task
- The app says "pre-visit check-in" and "routine questions" everywhere. "Simulator" and "unimportant" appear nowhere.
- The project's slides are not in this repository, so spelling fixes on slides ("patients," "lose," "incorporation," "clinics") are still to do.

## Three-minute demo script
1. Check-In: load "Sinus & Ear Pain", press Check in. Point at the plain-language prep.
2. Load "Red flag: chest pain", press Check in. Point at "Tell the front desk / call 911".
3. Clinic Dashboard: sign in as `dr.demo`. Show the red and amber alerts at the top, then Test Patient Maya's brief and priority agenda.
4. Press Export to EHR, flip to the FHIR tab, close.
5. Press Draft patient summary. Show a line and the note text under it. Press Approve and send.
6. After-Visit: show the summary, toggle brand vs. generic, ask one answerable and one unanswerable question.
7. For Clinics: change patients per day; show the return multiple and the comparison table.
