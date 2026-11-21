# Judge Prep

For the team presenting CareBridge. What judges are likely to press on, the short answer to give, where to show it in
the app, and the honest limit behind each answer. Checked against the code on Nov 21, 2026.

Live site: https://carebridge-ypuw.onrender.com/ · Staff sign-in: `dr.demo` / `carebridge-demo`

## Fix or rehearse before presenting

1. **Judges will type their own emergency.** On 25 new emergency phrasings written for this prep (none tuned
   against), 15 reached the 911 screen, 2 got a nurse check, and **8 got no flag**:
   "I feel like I'm dying, help", "I took too many pills", "the baby is blue", "my baby has a fever of 105",
   "my child swallowed bleach", "my stomach pain is 10 out of 10" (typed, not on the slider), "I can't feel my legs",
   "I was in a car accident". Either add rules for these before judging, or know the answer in "Safety" below cold.
2. **The For Clinics page says "every emergency caught".** That is true of the 272-phrasing test set, not of every
   possible message. Say "every emergency in our test set", never "we catch every emergency".
3. **Open the live link 5 minutes early.** The free plan sleeps after 15 idle minutes and takes about a minute to wake.
   Waking or redeploying resets the demo to its five test patients.
4. **Claude is on in the live site.** Q&A answers and summaries come from Claude there, not the rules. Rehearse the
   demo questions on the live site, not only on a laptop.
5. **Decide pricing.** It is hidden from the app, but "how do you make money?" is nearly certain. See "Business".

## Numbers to know

| Number | What it means |
|---|---|
| 272 | Safety test phrasings, in English, Spanish and French |
| 177 of 177 | Emergencies in the test set sent to the 911 screen, with 0 false alarms on 55 routine messages |
| 27 of 31 | Emergencies caught on wording never tuned against (the honest number). The original screen caught 12 of 31 |
| 0.1 ms | Time the safety screen takes per message |
| 43 | Automated backend tests |
| 3 | Patient languages: English, Spanish, French. Any other language books an interpreter |
| 300 | Daily cap on Claude calls (about 75 full visits); past it the app uses rules |
| 5 to 15 cents | Estimated Claude cost per complete visit |

## The demo (about 3 minutes)

1. **Check-In.** Load "Sinus & Ear Pain", press Check in. Point at the plain-language visit prep.
2. Load "Red flag: chest pain", press Check in. Point at "Tell the front desk right away / call 911".
   Optional: type "chest pian" to show the misspelling caught.
3. **Clinic Dashboard.** Sign in as `dr.demo`. The red flag sits at the top of the queue. Open a patient's 30-second
   brief: every agenda item quotes the patient.
4. Press **Export to EHR**, flip to the FHIR tab, close.
5. Type short visit notes, press **Draft patient summary**, show a line next to the note text it came from, press
   **Approve and send**.
6. **After-Visit.** Next steps at home first, the cost breakdown with brand vs. generic, then ask one question the
   summary answers and one it doesn't (it goes to the care team).
7. Press **Send the day-3 check-in now**, reply "still hurts", and show it land in the staff inbox.
8. **For Clinics.** Comparison table, "How the AI stays safe", and the privacy and EHR strip.

## Safety

**"What if your rules miss an emergency?"**
Say: "They can, and we measured how often. On wording we'd never seen, the rules caught 27 of 31. So the rules are
never the only check: anything vague or high-discomfort goes to a nurse, staff always see the patient's own words,
and every miss we find becomes a test and a rule." Then show `docs/SAFETY_BENCHMARK.md` if asked for method.
Limit: the 8 misses listed above. If a judge finds one live, thank them, say it becomes test phrasing #273, and point
to the nurse-check backstop.

**"Why not let the AI decide what's urgent?"**
Say: "An emergency check has to give the same answer every time, run in a fraction of a millisecond, and keep working
if the AI is down. Plain rules do that. The AI never sees a message the rules flag as an emergency."

**"How do you catch misspellings without AI?"**
Say: "Fuzzy matching. 'pian' is one letter away from 'pain', so the rules read it as 'chest pain', and staff see both
what was typed and how it was read. Real words like 'cooking' are never 'corrected' to 'choking'."

**"What about 'no chest pain'?"**
Say: "A denied red flag still gets a nurse check. We never silently ignore one."

## AI accuracy

**"What if the AI explains something wrong?"**
Say: "Three locks. The summary comes only from the doctor's own notes, and any line Claude can't quote back from those
notes is removed. The doctor reviews every line and presses Approve and send; the patient sees nothing before that.
And patient questions are answered only from the approved summary; anything else goes to the care team."

**"What happens if the AI is down or too expensive?"**
Say: "Every feature has a rules fallback. Without Claude, or past the daily cap, the app keeps working." Limit: in rules
mode, Spanish and French summaries stay in English, and the clinician is told so.

**"Claude helped write your code. How do you know it's right?"**
Say: "We didn't take the code on trust. We checked it the way you'd check any new hire's work: by testing what it
does, not by reading how confident it sounds." Then name the checks:
* **43 automated tests**, run with no internet and no AI, cover safety, summaries, Q&A, the
  follow-up texts, languages and the daily AI cap.
* **The safety screen is measured, not assumed.** 272 test phrasings, including a held-out set written before the
  last fixes and scored once (27 of 31). The misses were real, and we published them.
* **Checks in a real browser.** Every page was opened in Chrome in light and dark mode, plus the French screens at
  phone width, and screenshots were checked for errors.
* **The deploy was rehearsed.** The container was built and run locally exactly as the host runs it before going live.
* **The riskiest parts have the simplest code.** The emergency check is plain rules anyone can read, not AI, and the
  AI's output is never shown to a patient before a doctor approves it.

Have one concrete example ready of testing catching an AI-written mistake:
* The first spelling tolerance read "I was cooking dinner" as "choking". We added a list of real words that are never
  corrected.
* The French symptom rules had a typo that meant they never matched anything. Testing French check-ins caught it.

Then add, in your own words, what the team itself reviewed: which files you read line by line, what you changed,
and what you'd want an outside security and clinical review to look at before real patients. Only claim review you
actually did.

## Privacy and records

**"Is this HIPAA compliant?"**
Say: "The demo uses only made-up test patients and stores nothing on disk, so there's no patient data to protect yet.
Before real data we'd have HIPAA-eligible hosting, encryption in transit and at rest, audit logs, and signed Business
Associate Agreements with each clinic and with our hosting and AI vendors." The For Clinics strip marks what's live
in the demo and what's planned. Don't say "we are HIPAA compliant".

**"Does it connect to our EHR?"**
Say: "Today it exports a clinical note and a FHIR R4 bundle, the standard format certified EHRs must support. Next is a
SMART on FHIR app that opens inside the EHR, starting with the one or two EHRs most common in small practices."
Limit: the export uses free text, not SNOMED or ICD codes, and isn't sent anywhere.

## Patients and access

**"What about patients without smartphones?"** Kiosk mode for a clinic tablet, large text, and "front desk staff can
always fill it out with the patient."

**"What about other languages?"** English, Spanish and French are full patient languages, including the safety rules.
Any other language is recorded and books an interpreter, shown at the top of the staff brief. "We only add a
language once the safety screen can read it."

**"Do the follow-up texts really send?"** Not yet: they appear in the app. Real SMS needs a texting provider and the
patient's consent to receive texts.

## Business

**"How do you make money?"** Team decision needed. The hidden placeholder was per provider per month: Basic $99
(check-in), Plus $199 (adds the AI agenda), Complete $299 (adds after-visit summaries and Q&A), in
`backend/savings.py`. Pick real numbers and be able to justify them.

**"Who are your competitors?"** Judges may name check-in and patient-messaging tools such as Phreesia or Luma Health.
Say: "Most tools stop at check-in. We help before, during, and after the visit." Check each competitor's current
features before naming them; the table says "typical tool" on purpose.

**"How will you get your first clinics?"** Free 30-day pilot with 2 or 3 local independent family medicine clinics,
then paid. Strongest if you can quote one real receptionist or office manager.

**"Does it save money?"** The calculator is hidden because its numbers were placeholders. Answer with the three
savings you'd measure in a pilot: staff minutes per check-in, no-shows recovered, after-visit calls avoided.

## Hard questions

**"Is this a medical device? What about the FDA?"**
Say: "CareBridge doesn't diagnose or recommend treatment. It routes patients to people and drafts text a clinician
approves. Before launch we'd get regulatory review of the safety screen." Don't claim an FDA status.

**"Who's liable if it misses something?"**
Say: "The clinic's staff stay in charge. The screen only adds alerts, it never removes a patient from the queue, and
staff always see the patient's own words."

**"Will this scale?"** The demo is one small server with data in memory, chosen so no patient data is ever stored.
A real product moves to a database and HIPAA-eligible hosting; the safety screen itself takes 0.1 ms per message.

**"How did you build it?"** Answer honestly, including any AI coding tools the team used, and focus on the decisions
the team made: rules before AI, doctor approval, measuring the safety screen, and the held-out test.
