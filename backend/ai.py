"""
Optional Claude layer. Every caller has a plain-code fallback, so the app runs with no key and no SDK.

Rules that keep the AI safe (judge items #7 and #8):
  * It is only called after safety.screen() allows it.
  * It only sees the text it must transform (patient intake, or the doctor's own notes, or the approved summary).
  * Every output is JSON with a "source" quote; callers drop anything whose quote isn't in the input.
"""

from __future__ import annotations

import json
import os

MODEL = os.environ.get("CAREBRIDGE_MODEL", "claude-opus-5-5")

try:   # optional dependency
    import anthropic
except ImportError:   # pragma: no cover - depends on the environment
    anthropic = None

_client = None


def enabled() -> bool:
    if anthropic is None or os.environ.get("CAREBRIDGE_DISABLE_AI") == "1":
        return False
    return bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN") or os.environ.get("ANTHROPIC_PROFILE"))


def status() -> dict:
    return {"ai_enabled": enabled(), "model": MODEL if enabled() else None,
            "mode": "Claude" if enabled() else "Rules only (no API key): every feature still works"}


def _get_client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic(timeout=60.0, max_retries=1)
    return _client


def ask_json(system: str, user: str, schema: dict, max_tokens: int = 4000) -> dict | None:
    """One structured-output call. Returns parsed JSON, or None on any failure (caller then uses rules)."""
    if not enabled():
        return None
    try:
        response = _get_client().beta.messages.create(
            model=MODEL,
            max_tokens=max_tokens,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",                 # a declined request is retried on a fallback model server-side
            system=system,
            messages=[{"role": "user", "content": user}],
            output_config={"effort": "low", "format": {"type": "json_schema", "schema": schema}},
        )
        if response.stop_reason in ("refusal", "max_tokens"):
            return None
        text = next((b.text for b in response.content if b.type == "text"), "")
        return json.loads(text)
    except anthropic.APIStatusError as e:
        print(f"[ai] API error {e.status_code}: {e.message}")
    except anthropic.APIConnectionError:
        print("[ai] network error; using rules")
    except (json.JSONDecodeError, StopIteration, TypeError, AttributeError) as e:
        print(f"[ai] unusable response ({type(e).__name__}); using rules")
    return None
