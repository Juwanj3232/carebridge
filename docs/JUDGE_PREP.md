# Judge Prep

For the team presenting CareBridge. What judges are likely to press on, the short answer to give, where to show it in
the app, and the honest limit behind each answer. Checked against the code on Nov 21, 2026.

Live site: https://carebridge-ypuw.onrender.com/ · Staff sign-in: `dr.demo` / `carebridge-demo`

## Fix or rehearse before presenting

1. **Judges will type their own emergency. Fixed for the ones we found.** Messages a judge might type, written for
   this prep, first caught 15 of 22 emergencies. "I feel like I'm dying, help", "I took too many pills", "the baby is
   blue" and "my child swallowed bleach" got no flag. A second check found more, including "I have a gun and I'm
   thinking about using it" and "my husband won't wake up" (1 of 7). All of these now reach the 911 screen and are in
   the tests. New wording still slips past the keyword rules: "I got bit by a snake" has no rule word. The AI second
   opinion (below) is there for exactly that. Know the answer in "Safety" below cold.
2. **Say "every emergency in our test set", never "we catch every emergency".** The For Clinics page now says
   "every emergency in the test set caught".
3. **Open the live link 5 minutes early.** The free plan sleeps after 15 idle minutes and takes about a minute to wake.
   Waking or redeploying resets the demo to its five test patients.
4. **Claude is on in the live site.** Q&A answers and summaries come from Claude there, not the rules. Rehearse the
   demo questions on the live site, not only on a laptop.
5. **Try the AI second opinion on the live site before judging.** Type "I got bit by a snake" at check-in and confirm
   you see "This may be an emergency", then an AI FLAG on the dashboard. It was tested with a stand-in for the AI, so
   the live site is its first run with real Claude. Also run `python3 scripts/second_opinion_benchmark.py --ai` once
   (about 25 short Claude calls) to get the measured number for the table below.

## Numbers to know

| Number | What it means |
|---|---|
| 341 | Safety test phrasings, in English, Spanish and French |
| 217 of 217 | Emergencies in the test set sent to the 911 screen, with 0 false alarms on 78 routine messages |
| 27 of 31 | Emergencies caught on wording never tuned against (the honest number). The original screen caught 12 of 31 |
| 15 of 22 | Emergencies caught on judge-style messages before we fixed them. All 22 are caught now |
| 0 of 12 | Emergencies the keyword rules alone catch on 30 new, unusual phrasings ("I got bit by a snake"). This is what the AI second opinion is for; its combined number comes from the `--ai` benchmark run |
| 0.1 ms | About how long the safety screen takes per message |
| 54 | Automated backend tests |
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
9. Optional, if asked about missed wording: the AI second opinion demo in "AI second opinion" below.

## Safety

**"What if your rules miss an emergency?"**
Say: "They can, and we measured how often. On wording we'd never seen, the rules caught 27 of 31. When we wrote
messages a judge might type, they caught 15 of 22, so we fixed those and added them to the tests. That's why the rules
are never the only check: anything vague or high-discomfort goes to a nurse, staff always see the patient's own
words, and every miss we find becomes a test and a rule." Then show `docs/SAFETY_BENCHMARK.md` if asked for method.
Then: "And for wording no list can predict, an AI second opinion reads every message the rules call routine. It can
only raise the alarm, never lower it."
Limit: if the AI is off or past its daily limit, only the rules run, and new wording like "I got bit by a snake" gets
no flag. If a judge finds a miss live, thank them, say it becomes test phrasing #342, and point to the nurse-check
backstop.

## AI second opinion

**What it is.** When the keyword rules find nothing, a fast AI model (Claude Haiku 5.5) reads the patient's message
and answers one question: could this need care sooner than the visit? It runs at check-in, on after-visit questions
and on follow-up text replies. Code: `backend/second_opinion.py`.

**What the patient sees** depends on how sure the app is and where the patient is. Kiosk mode means they're at the clinic.

| Who flagged it | At the clinic (kiosk) | At home (phone) |
|---|---|---|
| Keyword rules (emergency) | Tell the front desk right away, or call 911 | Same message |
| AI only, possible emergency | Tell the front desk right away | Call 911 or go to the nearest ER now |
| AI only, needs a nurse today | Tell the front desk now | Call the clinic now, urgent care if closed, 911 if worse |

**What staff see.** An **AI FLAG** badge in the queue, the patient's own words the AI was worried about, its reason
in a few words, and the call-back number if the patient left one. Every AI flag also lands in **Possible missed
rules**, where staff mark it Real miss or False alarm. A real miss shows a line to paste into the safety tests.

**Demo it (30 seconds).** Check-In: type "I got bit by a snake" and press Check in. The patient is told to call 911
or go to the ER. Turn on Kiosk and do it again: now it says tell the front desk. Clinic Dashboard: point at the AI FLAG
badge, the brief that says the keyword rules found nothing, and the Possible missed rules list. Press Real miss.

**"Doesn't safety depend on AI now?"**
Say: "No. The keyword rules still run first and work exactly as before, with no AI. The AI only runs when the rules
found nothing, and it can only add an alert. If it's down, slow or wrong, the patient gets exactly what they got
before."

**"What if the AI is wrong?"**
Say: "If it over-flags, a person checks: the front desk at the clinic, or the clinic's phone line at home. If it
misses, we're back to the rules and the nurse-check backstop, which is where we were without it. Staff mark every
flag Real miss or False alarm, so we can see how often each happens."

**"Why tell someone at home to call 911 on the AI's word?"**
Say: "Only when the AI thinks it may be an emergency. An unneeded ER trip is a bad day; staying home with a venomous
snake bite can kill. ER triage leans the same way. When the AI is less worried, we send them to the clinic's phone
line instead, so a nurse decides."

**"How do you know it works?"**
Say what's true on the day. Built and tested: 11 automated tests with a stand-in for the AI cover escalate-only,
timeouts, made-up quotes, each message by place and language, and the review list. Measured: on 30 new, unusual
phrasings, the keyword rules alone catch 0 of 12 emergencies. Run `python3 scripts/second_opinion_benchmark.py --ai`
before judging to get the combined number and the AI's false alarms on 12 routine messages.

**"Does the patient's message go to an AI company?"**
Say: "With Claude on, yes. The text the patient typed is sent, never the chart. Before real patients we'd sign a
Business Associate Agreement with the AI vendor, as with our hosting. That's already in the privacy plan on the
For Clinics page."

**"What does it cost, and is it fast?"**
Say: "One short call to a small, fast model per message the rules call routine, counted in the same daily limit as
everything else. It has a 4-second limit; past that the check-in carries on without it."

**How the rules keep learning.** AI flags marked Real miss are pasted into `tests/safety_cases.py` and get a rule, so
the next patient who says it is caught instantly, without the AI. The AI finds the gaps; the rules close them.

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
* **54 automated tests**, run with no internet and no AI, cover safety, summaries, Q&A, the
  follow-up texts, languages, the daily AI cap and the AI second opinion (with a stand-in for the AI).
* **The safety screen is measured, not assumed.** 341 test phrasings, including held-out sets labelled before
  scoring and scored once (27 of 31, then 15 of 22 on judge-style messages). The misses were real, and we published them.
* **Checks in a real browser.** Every page was opened in Chrome in light and dark mode, plus the French screens at
  phone width, and screenshots were checked for errors.
* **The deploy was rehearsed.** The container was built and run locally exactly as the host runs it before going live.
* **The riskiest parts have the simplest code.** The emergency check is plain rules anyone can read, not AI, and the
  AI's output is never shown to a patient before a doctor approves it.

Three mistakes in AI-written code that our testing caught and we fixed:
* **"Cooking" read as "choking".** The first version of spelling tolerance turned "I was cooking dinner" into a choking
  emergency, a false alarm. The test set includes spelling traps like this on purpose. The fix is a list of real
  dictionary words that are never "corrected" into an emergency word (`backend/fuzzy_guard.txt`).
* **"Hart attack" read as "hard attack".** "Hart" is one letter from both "heart" and "hard", and the code picked "hard",
  so a misspelled heart attack got no flag. The fix tries every equally close word, so "I think its a hart attack" now
  shows staff: RED FLAG, "hart attack, read as heart attack".
* **French symptom rules that never matched.** A typo in the French patterns meant no French symptom was ever
  recognized, even though nothing crashed. Testing French check-ins caught it.

If asked how closely the team read the code itself, say: "We looked over the code, but mostly we checked results.
After each change, we ran the app and looked at what it did. That's why the tests and the measured safety numbers
matter: they check the code more thoroughly than reading it would. Before real patients, we'd get an outside
security and clinical review."

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

**"Who are your competitors?"** Judges may name check-in and patient-messaging tools such as Phreesia or Luma Health.
Say: "Most tools stop at check-in. We help before, during, and after the visit." Check each competitor's current
features before naming them; the table says "typical tool" on purpose.

**"How will you get your first clinics?"** Free 30-day pilot with 2 or 3 local independent family medicine clinics,
then paid.

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
A real product moves to a database and HIPAA-eligible hosting; the safety screen itself takes about 0.1 ms per message.

**"How did you build it?"**
Say: "We built it with two AI coding assistants, Claude Code and Gemini, which generated most of the code from our
instructions. The whole team worked on the code together, and Carelle and Isaiah built the presentation. The
design decisions were Juwan's and Karim's: safety rules before any AI, a doctor approving every summary, and
measuring the safety screen on a test set we hadn't tuned against." Then point to "Claude helped write your code. How do you know it's right?"
above.
