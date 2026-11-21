"""
Measure the safety screen on the test phrasings in tests/safety_cases.py.

  python3 scripts/safety_benchmark.py            # report for both sets
  python3 scripts/safety_benchmark.py --misses   # also list every case that did not get the expected result

"Caught" means the expected tier or a stricter one: an emergency must be "emergency"; a review case passes as
"urgent_review" (an emergency there is a stricter call, counted separately); a routine case must stay "routine".
"""

from __future__ import annotations

import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from backend import safety  # noqa: E402
from safety_cases import FRENCH, FRENCH_HELDOUT, HELDOUT_1, HELDOUT_2, TUNING  # noqa: E402

LEVEL = {"emergency": "emergency", "review": "urgent_review", "routine": "routine"}


def evaluate(cases: list[tuple[str, str, str]]) -> dict:
    out = {"emergency": [0, 0, 0], "review": [0, 0, 0], "routine": [0, 0], "misses": [], "by_group": {}}
    for expected, group, text in cases:
        got = safety.screen(text).level
        g = out["by_group"].setdefault(group, [0, 0])
        g[1] += 1
        if expected == "emergency":
            out["emergency"][1] += 1
            if got == "emergency":
                out["emergency"][0] += 1
                g[0] += 1
            elif got == "routine":
                out["emergency"][2] += 1          # missed entirely: no flag at all
                out["misses"].append((expected, group, text, got))
            else:
                out["misses"].append((expected, group, text, got))   # caught as a nurse check only
        elif expected == "review":
            out["review"][1] += 1
            if got == "urgent_review":
                out["review"][0] += 1
                g[0] += 1
            else:
                if got == "routine":
                    out["review"][2] += 1
                out["misses"].append((expected, group, text, got))
        else:
            out["routine"][1] += 1
            if got == "routine":
                g[0] += 1
            else:
                out["routine"][0] += 1             # false alarm
                out["misses"].append((expected, group, text, got))
    return out


def timing(cases, rounds: int = 200) -> tuple[float, float]:
    texts = [t for _, _, t in cases]
    samples = []
    for _ in range(rounds):
        for t in texts:
            start = time.perf_counter()
            safety.screen(t)
            samples.append((time.perf_counter() - start) * 1000)
    samples.sort()
    return statistics.mean(samples), samples[int(len(samples) * 0.99) - 1]


def report(name: str, cases) -> dict:
    r = evaluate(cases)
    e_hit, e_n, e_none = r["emergency"]
    v_hit, v_n, v_none = r["review"]
    fa, ok_n = r["routine"]
    nurse_only = e_n - e_hit - e_none
    print(f"\n{name}: {len(cases)} phrasings")
    print(f"  Emergencies sent to the 911 screen : {e_hit} of {e_n}"
          f"  ({nurse_only} caught as a nurse check only, {e_none} missed with no flag)")
    print(f"  Nurse-check cases flagged correctly : {v_hit} of {v_n}  ({v_none} missed with no flag)")
    print(f"  Routine cases with no false alarm   : {ok_n - fa} of {ok_n}  ({fa} false alarms)")
    print("  By group: " + ", ".join(f"{g} {a}/{n}" for g, (a, n) in r["by_group"].items()))
    return r


def main() -> None:
    show = "--misses" in sys.argv
    status = safety.fuzzy_status() if hasattr(safety, "fuzzy_status") else "not installed"
    print(f"Safety screen benchmark (spelling tolerance: {status})")
    sets = {"Tuning set": TUNING, "Held-out round 1 (now tuning data)": HELDOUT_1, "Held-out round 2": HELDOUT_2,
            "French (tuning)": FRENCH, "French held-out": FRENCH_HELDOUT}
    results = {name: report(name, cases) for name, cases in sets.items()}
    every = TUNING + HELDOUT_1 + HELDOUT_2 + FRENCH + FRENCH_HELDOUT
    mean_ms, p99_ms = timing(every)
    print(f"\nScreen time per message: {mean_ms:.3f} ms average, {p99_ms:.3f} ms at the 99th percentile "
          f"({len(every)} phrasings x 200 runs)")
    if show:
        for name, r in results.items():
            if r["misses"]:
                print(f"\n{name} misses:")
                for expected, group, text, got in r["misses"]:
                    print(f"  expected {expected:9} got {got:13} [{group}] {text}")


if __name__ == "__main__":
    main()
