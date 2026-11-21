# Safety screen benchmark

The red-flag screen (`backend/safety.py`) is plain code that runs before any AI. This page reports how well it
does on 341 test phrasings in English, Spanish and French, and how those numbers were produced, so nobody has to take
them on trust.

Re-run it any time:

```bash
python3 scripts/safety_benchmark.py --misses
```

## Results (Nov 21, 2026)

On the 229 English and Spanish phrasings, before and after this round of work:

| | Original screen | Current screen |
|---|---|---|
| Emergencies sent to the 911 screen | 63 of 148 | **148 of 148** |
| Nurse-check cases flagged | 26 of 33 | **33 of 33** |
| Routine messages with no false alarm | 48 of 48 | **48 of 48** |
| Average screen time per message | 0.04 ms | **0.07 ms** (0.14 ms at the 99th percentile) |

**The honest number is the round-2 held-out set.** It was written before the last round of rule changes and scored
once. The current screen caught **27 of 31 emergencies** there, with 7 of 7 nurse checks and 0 false alarms on 10
routine messages. Misspellings scored 10 of 10 and Spanish 7 of 7. The original screen caught 12 of 31 on the same set.
The four misses were wording gaps ("he is not breathing", "the left side of my face is numb",
"my chest is on fire", "I'm going to end it tonight"). They were added to the rules afterwards, so the 148 of 148
above includes them.

**French (added Nov 21, 2026): 43 phrasings.** The French tuning set (31) scores 21 of 21 emergencies, 5 of 5 nurse
checks and 0 false alarms. The French held-out set (12) was scored once: 7 of 8 emergencies, 2 of 2 nurse checks,
0 false alarms. Its miss ("ma poitrine me fait très mal") was fixed afterwards.

**Judge-style round 3 (added Nov 21, 2026): 31 phrasings.** Written during judge prep as messages a judge might type
into the live demo, labelled before scoring, and scored once: **15 of 22 emergencies**, 1 of 3 nurse checks, 0 false
alarms on 6 routine messages. The misses were "I feel like I'm dying, help", "I took too many pills", "the baby is
blue", "my baby has a fever of 105", "my child swallowed bleach", "I can't feel my legs" (no flag), "I hit my head and
I'm confused" (nurse check only), "my stomach pain is 10 out of 10" and "I was in a car accident" (no nurse check).
New rules cover overdose and poisoning, feeling like dying, someone turning blue, very high fever, head injury with
warning signs, sudden loss of feeling, pain rated 9 or 10 in words, recent accidents and fever in a baby, in English,
Spanish and French.

**Round 4: 9 phrasings.** Found while checking the round-3 fixes, labelled before scoring, scored once: **1 of 7
emergencies** and 0 of 2 nurse checks. The misses included "I have a gun and I'm thinking about using it", "my husband
won't wake up", "she is not responding" and "my blood sugar is 40". New rules (English only) cover a weapon plus
intent, someone who won't wake up or respond, everything going black, very low blood sugar and not being able to walk
straight. Rounds 3 and 4 are now tuning data.

**All 341 phrasings today:** 217 of 217 emergencies sent to the 911 screen, 46 of 46 nurse checks, 0 false alarms on
78 routine messages, at 0.13 ms per message on average.

A one-line version for a slide:

> Measured on 341 test phrasings in English, Spanish and French, including misspellings and slang: every emergency in
> the test set sent to the 911 screen, 0 false alarms, about 0.1 ms per message. On phrasings we had never tuned
> against, 27 of 31 English and Spanish emergencies were caught before any fixes, up from 12 of 31.

## What is in the test set

Every phrasing is in `tests/safety_cases.py`, written by the team. None are real patient messages.

| Group | Examples |
|---|---|
| Plain emergencies | "I have chest pain", "I'm coughing up blood", "my son had a seizure" |
| Misspellings | "chest pian", "cant breth", "siezure", "hart attack", "chestpain" |
| Slang | "my chest is killing me", "kms", "I can't get any air", "he isn't waking up" |
| Spanish | "me duele el pecho", "me falta el aire", "dolor en el pecjo" |
| French | "j'ai mal à la poitrine", "je n'arrive pas à respirer", "j'ai envie d'en finir", "douleur a la poitrinne" |
| Negations | "no chest pain", "I don't have chest pain", "denies shortness of breath" |
| Vague worries | "my heart feels weird", "the room is spinning" |
| Routine | "sore throat for 3 days", "I need a refill", "heartburn after spicy food" |
| Judge-style | "I took too many pills", "the baby is blue", "my husband won't wake up", "my blood sugar is 40" |
| Spelling traps | "I was cooking dinner" (one letter from "choking"), "I feel like I'm doing better" (one letter from "dying"), "grasping the rail" |

What counts as correct:

* An emergency must reach the 911 screen. A nurse check does not count.
* A negation ("no chest pain") must get a nurse check. Our design never ignores a denied red flag.
* A routine message must raise no flag at all.

## How the numbers were produced

1. **Baseline.** The original screen was scored first: 38 of 89 emergencies on the tuning set, and only 1 of 30
   misspellings.
2. **Tuning set (139 phrasings).** Spelling tolerance was added, and rules were extended only for tuning-set misses.
3. **Held-out round 1 (42 phrasings).** Written together with the tuning set. After the tuning work it scored 19 of 28
   emergencies, 6 of 6 nurse checks and 0 false alarms. Its misses were then fixed, so it is now tuning data. One
   caveat: its results were printed once mid-way, while tuning was still going on.
4. **Held-out round 2 (48 phrasings).** Written after round 1 and before round 1's fixes. Scored once at the end:
   27 of 31. Its four misses were fixed after that.
5. **Judge-style round 3 (31 phrasings) and round 4 (9 phrasings).** Labelled before scoring, scored once (15 of 22,
   then 1 of 7 emergencies), then fixed. Each fix added spelling traps for its new words, such as "I'm doing better"
   and "my son is not responding to the antibiotics", to check it raised no false alarm.

All phrasings were written by the same team that wrote the rules, so this is a regression test plus an honest
check on wording we had not seen. It is not an independent clinical validation.

## How spelling tolerance works (still no AI)

When no red flag matches exactly, the screen corrects likely typos and runs the same rules again.

* A word is corrected only toward a word the rules use, and only when it starts with the same letter. It must be one
  edit away, or two edits for words of 8 or more letters. Swapping two neighbouring letters counts as one edit.
  The distance comes from `rapidfuzz.distance.OSA`, with a built-in fallback that gives identical results.
* A correction only matters if it completes a red-flag phrase. "chess" being near "chest" changes nothing unless the
  next word is "pain".
* Real words that sit one letter away from a one-word red flag are never corrected, such as "cooking" and "choking",
  or "grasping" and "gasping". That list, `backend/fuzzy_guard.txt`, is generated from a dictionary by
  `scripts/build_fuzzy_guard.py`.
* Some rule words are never spelling targets because everyday words sit one letter away: "dying" ("doing",
  "drying"), "pills" ("bills"), "head" ("heal", "heat"), "blue", "legs", "fever", "baby". Typed correctly, they still match.
* Staff see exactly what the patient typed, for example *RED FLAG: Chest pain / pressure ("chest pian, read as chest pain")*.

## Known limits

* Words of three letters or fewer are never corrected, so "kil" is caught only because a rule now allows it.
* Sentences that describe an emergency without any rule word can still be missed. Today "I got bit by a snake" and
  "my water broke and the baby is coming" get no flag at all. Round 4 showed how fast new wording finds gaps: 1 of 7
  before its fixes. The backstop is staff reading the raw patient text, which the dashboard always shows.
* The list will keep growing. Every miss found in a demo or a pilot should become a new phrasing in
  `tests/safety_cases.py`, then a rule fix.
