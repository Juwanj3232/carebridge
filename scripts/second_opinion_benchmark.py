"""
Measure the AI second opinion: keyword rules alone vs. rules plus the AI second opinion, on NEW_WORDING
(tests/safety_cases.py), a held-out set the keyword rules were never tuned on.

  python3 scripts/second_opinion_benchmark.py          rules alone (free, no key, no network)
  python3 scripts/second_opinion_benchmark.py --ai     also rules + AI: real Claude calls (about one short Claude
                                                       Haiku 5.5 call per message the rules call routine, roughly
                                                       25 calls), using ANTHROPIC_API_KEY from the environment or .env

An emergency counts as caught only if it reaches the emergency level. A nurse-check case counts if it gets any flag.
A routine message counts as correct only if it raises no flag (an AI flag on a routine message is a false alarm).
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from safety_cases import NEW_WORDING  # noqa: E402

from backend import ai, safety, second_opinion  # noqa: E402

CORRECT = {
    "emergency": lambda level: level == "emergency",
    "review": lambda level: level in ("emergency", "urgent_review"),
    "routine": lambda level: level == "routine",
}


def score(results: list[tuple[str, str, str]]) -> dict:
    out = {}
    for kind in ("emergency", "review", "routine"):
        rows = [(text, level) for expected, text, level in results if expected == kind]
        out[kind] = (sum(CORRECT[kind](level) for _, level in rows), len(rows))
    return out


def main() -> None:
    use_ai = "--ai" in sys.argv
    if use_ai:
        try:
            from dotenv import load_dotenv
            load_dotenv(ROOT / ".env")
        except ImportError:
            pass
        if not ai.enabled():
            sys.exit("--ai needs ANTHROPIC_API_KEY (environment or .env) and the anthropic package.")

    rules = [(e, t, safety.screen(t).level) for e, _, t in NEW_WORDING]
    both, seconds = [], []
    if use_ai:
        for e, _, t in NEW_WORDING:
            start = time.perf_counter()
            r = second_opinion.check(t, at_clinic=True, source="benchmark")
            seconds.append(time.perf_counter() - start)
            both.append((e, t, r.level))

    print(f"Second-opinion benchmark: {len(NEW_WORDING)} new phrasings, never used to tune the rules\n")
    a = score(rules)
    b = score(both) if use_ai else None
    names = {"emergency": "Emergencies reaching the emergency level", "review": "Nurse-check cases flagged",
             "routine": "Routine messages with no false alarm"}
    print(f"{'':44} {'Rules alone':>12} {'Rules + AI':>12}")
    for kind, name in names.items():
        right = f"{b[kind][0]} of {b[kind][1]}" if b else "run --ai"
        print(f"{name:44} {f'{a[kind][0]} of {a[kind][1]}':>12} {right:>12}")
    if use_ai:
        print(f"\nTime per message with the AI step: {sum(seconds) / len(seconds):.2f} s average, {max(seconds):.2f} s max "
              f"(time limit {second_opinion.TIME_LIMIT:.0f} s)")
        print(f"Claude calls used today: {ai.usage()['calls_today']}")
    print("\nPer message (expected -> rules" + (" -> rules + AI" if use_ai else "") + "):")
    for i, (e, t, lvl) in enumerate(rules):
        extra = f" -> {both[i][2]}" if use_ai else ""
        print(f"  {e:9} -> {lvl:13}{extra:16}  {t}")


if __name__ == "__main__":
    main()
