# CareBridge Status Report (Nov 21, 2026)

## Where we are
CareBridge is a working app on GitHub at https://github.com/Juwanj3232/carebridge.
It is ready to deploy to Render with one click, and the safety screen now has a measured result.
Two steps still need the team's own accounts: the Render deploy itself, and the first live Claude call.

## Verified
- 38 backend tests pass, with rapidfuzz installed and with the built-in fallback.
- **Safety screen, measured on 229 test phrasings** (misspellings, slang, Spanish, negations, routine messages):
  every one of 148 emergencies reached the 911 screen, all 33 nurse-check cases were flagged, and 0 of 48 routine
  messages raised a false alarm. Average screen time is 0.07 ms per message. On a held-out set written before the last
  fixes, it caught 27 of 31 emergencies, up from 12 of 31 for the original screen. Method and caveats are in
  `docs/SAFETY_BENCHMARK.md`.
- Misspellings are caught without AI: "chest pian" is read as "chest pain" and shown to staff that way.
- The deploy image builds and runs locally exactly as Render will run it. It serves the UI and the API on Render's
  port, runs as a non-root user, and screens a misspelled red flag correctly.
- The live-check script runs end to end against that container. With no key it correctly reports rules mode.

## Not verified yet (needs the team's accounts)
- **Not deployed.** Nobody on the build side has Render access. Steps: click **Deploy to Render** in the README, or
  choose New > Blueprint and pick the repo. Paste `ANTHROPIC_API_KEY` when asked and wait for the deploy.
- **Claude has never been called with a real key.** After the deploy, run
  `python3 scripts/claude_live_check.py --url <the Render URL>`. Every row should say `CLAUDE`. Or run it locally
  with the key in `.env`.
- **Slide QR code.** After the deploy: `.venv/bin/python scripts/make_qr.py <the Render URL>`, then put
  `docs/qr-live-demo.png` on the slide and scan it with a phone to check.

## Judge items
| # | Item | Status |
|---|---|---|
| 1 | Focus on one specialty | Built: family medicine only |
| 2 | Competitors | Comparison table in app; slide and competitor check still to do |
| 3 | Savings proof | Calculator hidden from the UI; logic kept for later |
| 4 | EHR connection | Export to EHR built: clinical note and FHIR R4 bundle (mock) |
| 5 | Privacy | Built for demo: test patients, staff login, doctor-only approval |
| 6 | Urgent symptoms | Built and measured: plain-code red flags with spelling tolerance before any AI, 229-phrasing benchmark |
| 7 | Summary source | Built: from doctor's notes, Approve and send |
| 8 | Wrong explanations | Built: grounding check, Q&A escalation, required footer |
| 9 | Non-smartphone users | Built: kiosk mode, large text, Spanish |
| 10 | First customers | Plan line in app; receptionist interview still to do |
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
   on the key before pasting it into Render.

## Known limits
- The safety rules catch every phrasing in the test set, but new wording can still be missed. For example,
  "I feel like I'm dying, help" gets no flag today. The nurse-check tier and the raw patient text on the dashboard are
  the backstop. Every miss found in a demo should become a new test phrasing and then a rule.
- Spanish after-visit summaries need Claude. Without it, the draft is English and the clinician sees a note saying so.
- Visits live in memory and reset when the server restarts or a free instance wakes up. Login is demo-grade, and the
  demo password is public in the README.
- Follow-up texts appear in the app only; nothing is sent by SMS.

## How to run
```bash
cd /Users/jayflm/dev/carebridge
cd frontend && npm install && npm run build && cd ..
python3 server.py                           # http://localhost:8100   staff: dr.demo / carebridge-demo
python3 -m unittest discover -s tests       # 38 tests
python3 scripts/safety_benchmark.py         # safety numbers
```
