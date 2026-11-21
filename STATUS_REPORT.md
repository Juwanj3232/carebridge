# CareBridge Status Report (Nov 21, 2026)

## Where we are
CareBridge is a working app on GitHub at https://github.com/Juwanj3232/carebridge, live at
https://carebridge-ypuw.onrender.com/ with Claude turned on. The safety screen has a measured result.

## Verified
- 54 backend tests pass, with rapidfuzz installed and with the built-in fallback.
- **AI second opinion** (`backend/second_opinion.py`): when the keyword rules find nothing, Claude Haiku 5.5 reads
  the message and can only escalate. Tested with a stand-in for the AI (11 tests, and the screens checked in Chrome);
  not yet run with real Claude. On 30 new phrasings the rules alone catch 0 of 12 emergencies; run
  `python3 scripts/second_opinion_benchmark.py --ai` for the combined number.
- Check-in asks for a **preferred language**. Choosing another language (for example Vietnamese) books an interpreter:
  it shows in the staff queue, near the top of the agenda and in the EHR export.
- The app caps Claude calls per day (`CAREBRIDGE_AI_DAILY_LIMIT`, default 300) and falls back to rules mode past it.
- **Safety screen, measured on 341 test phrasings** in English, Spanish and French (misspellings, slang, negations,
  judge-style messages, routine messages): every one of 217 emergencies reached the 911 screen, all 46 nurse-check
  cases were flagged, and 0 of 78 routine messages raised a false alarm. Average screen time is 0.13 ms per message.
  On wording never tuned against: 27 of 31 emergencies (round 2, up from 12 of 31 for the original screen), 15 of 22
  (judge-style round 3) and 1 of 7 (round 4). Those misses are now fixed. Method and caveats are in
  `docs/SAFETY_BENCHMARK.md`.
- Misspellings are caught without AI: "chest pian" is read as "chest pain" and shown to staff that way.
- **French** is a full patient language: screens, check-in prep, safety rules and messages, answers and follow-up texts.
  The French held-out set scored 7 of 8 emergencies before its one miss was fixed. A headless-Chrome run confirmed
  the language menu, the French screens and the For Clinics page at desktop and phone width, with no console errors.
- The deploy image builds and runs locally exactly as Render will run it. It serves the UI and the API on Render's
  port, runs as a non-root user, and screens a misspelled red flag correctly.
- The live-check script runs end to end against that container. With no key it correctly reports rules mode.

- **Deployed on Render** at https://carebridge-ypuw.onrender.com/. Its health check reports Claude mode, with Claude
  calls counted against the daily cap. Every push to main redeploys it.

## Not done yet
- **Slide QR code.** `.venv/bin/python scripts/make_qr.py https://carebridge-ypuw.onrender.com/`, then put
  `docs/qr-live-demo.png` on the slide and scan it with a phone to check.

## Judge items
| # | Item | Status |
|---|---|---|
| 1 | Focus on one specialty | Built: family medicine only |
| 2 | Competitors | Comparison table in app; slide and competitor check still to do |
| 3 | Savings proof | Calculator hidden from the UI; logic kept for later |
| 4 | EHR connection | Export to EHR built: clinical note and FHIR R4 bundle (mock) |
| 5 | Privacy | Built for demo: test patients, staff login, doctor-only approval |
| 6 | Urgent symptoms | Built and measured: plain-code red flags with spelling tolerance before any AI, 341-phrasing benchmark |
| 7 | Summary source | Built: from doctor's notes, Approve and send |
| 8 | Wrong explanations | Built: grounding check, Q&A escalation, required footer |
| 9 | Non-smartphone users | Built: kiosk mode, large text, Spanish and French |
| 10 | First customers | Plan in the judge prep (free 30-day pilot with 2 or 3 local clinics); no clinic staff interviewed yet |
| 11 | Pricing | Hidden from the UI until the team settles it |
| 12 | Wording | Fixed in app; slides not in repo |

Also built since the last report: the follow-up agent (day-0 and day-3 texts, safety-screened replies, staff inbox),
and a simpler dashboard, after-visit page and For Clinics page.

## Decisions the team needs to make
1. **Vague symptoms (open question in #6).** We built a proposal: vague worrying words, a denied red flag, or
   discomfort 9–10 send a nurse check within 10 minutes. Accept it or change it.
2. **Render plan.** The free plan sleeps after 15 idle minutes, and the first visit then takes about a minute. The
   paid starter plan stays awake. Either way, open the link a few minutes before judging.
3. **API key spend limit.** The demo link is public, so anyone with it can trigger Claude calls. Set a monthly limit
   on the key before pasting it into Render. Estimated cost: about 5 to 15 cents per complete visit on Claude Opus 5.5,
   so a $10 to $20 limit covers a judging day. Claude Pro does not include API usage; API credits are billed separately.

## Known limits
- The safety rules catch every phrasing in the test set, but new wording can still be missed. For example,
  "I got bit by a snake" gets no flag from the rules. The AI second opinion (when Claude is on), the nurse-check
  tier and the raw patient text on the dashboard are the backstop. Every miss found in a demo should become a new test phrasing and then a rule.
- Spanish and French after-visit summaries need Claude. Without it, the draft is English and the clinician sees a note saying so.
- Visits live in memory and reset when the server restarts or a free instance wakes up. Login is demo-grade, and the
  demo password is public in the README.
- Follow-up texts appear in the app only; nothing is sent by SMS.

## How to run
```bash
cd /Users/jayflm/dev/carebridge
cd frontend && npm install && npm run build && cd ..
python3 server.py                           # http://localhost:8100   staff: dr.demo / carebridge-demo
python3 -m unittest discover -s tests       # 54 tests
python3 scripts/safety_benchmark.py         # safety numbers
```
