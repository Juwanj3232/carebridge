# CareBridge Status Report (Nov 20, 2026)

## Where we are
The CareBridge prototype is rebuilt as a working app in its own folder, `/Users/jayflm/dev/carebridge`, separate from the DSU hackathon repository.
All nine build items from the judge prep list are in the app and tested. The pitch items are supported in the app, but slides and team decisions are still open.
The DSU hackathon repository is back on `main` with no changes. CareBridge is not under version control yet.

## Verified
- 24 backend tests pass, with and without the `anthropic` SDK installed.
- A headless-Chrome run of the full demo passed every check with no console errors: check-in, red flag, vague symptom, staff login, draft and approval, patient view, brand/generic costs, Q&A answer and escalation, EHR export, calculator, Spanish kiosk mode, and phone width.
- Costs match the prototype: the ear case on the PPO plan is $41.80 with the generic and $54.60 with the brand.

## Not verified
- **Claude was not called live.** No API key was available. The Claude path is tested with mocked responses, and the pinned SDK version accepts every parameter it sends. Turn it on with `ANTHROPIC_API_KEY` in `.env` in this folder and run the demo once before judging.

## Judge items
| # | Item | Status |
|---|---|---|
| 1 | Focus on one specialty | Built: family medicine only |
| 2 | Competitors | Comparison table in app; slide and competitor check still to do |
| 3 | Savings proof | Calculator built; numbers are placeholder estimates |
| 4 | EHR connection | Export to EHR built: clinical note and FHIR R4 bundle (mock) |
| 5 | Privacy | Built for demo: test patients, staff login, doctor-only approval |
| 6 | Urgent symptoms | Built: plain-code red flags before AI, 911 screen, red staff alert |
| 7 | Summary source | Built: from doctor's notes, Approve and send |
| 8 | Wrong explanations | Built: grounding check, Q&A escalation, required footer |
| 9 | Non-smartphone users | Built: kiosk mode, large text, Spanish |
| 10 | First customers | Plan line in app; receptionist interview still to do |
| 11 | Pricing | Tiers built at placeholder prices |
| 12 | Wording | Fixed in app; slides not in repo |

## Decisions the team needs to make
1. **Vague symptoms (open question in #6).** We built a proposal. Vague worrying words, a denied red flag, or discomfort 9–10 send a nurse check within 10 minutes. Accept it or change it.
2. **Prices.** Basic $99, Plus $199 and Complete $299 per provider per month are placeholders.
3. **Calculator defaults.** For example, 5 staff minutes saved per check-in and a 15% no-show rate. Replace them with a real clinic's numbers if possible.
4. **Repository.** CareBridge is a standalone folder. Decide where it should live on GitHub, then run `git init` and push.
5. **Hosting.** Nothing is deployed. The drought app's Render and GitHub Pages setup is a working template to copy.

## Known limits
- Keyword safety rules can miss misspellings and unusual wording. The nurse-check tier and raw patient text on the dashboard are the backstop.
- Spanish after-visit summaries need Claude. Without it, the draft is English and the clinician sees a note saying so.
- Visits live in memory and reset when the server restarts. Login is demo-grade.
- In rules mode, Q&A escalates when unsure, which is the safe failure.

## How to run
```bash
cd /Users/jayflm/dev/carebridge
cd frontend && npm install && npm run build && cd ..
python3 server.py        # http://localhost:8100   staff: dr.demo / carebridge-demo
python3 -m unittest discover -s tests
```
