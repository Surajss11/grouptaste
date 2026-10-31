"""Thin, bounded wrapper around the official `qloo exec` workflow CLI.

Every call goes through the public @qloo/qloo-harness package, so the API key
stays in the harness config or the QLOO_API_KEY environment variable and never
passes through this code.
"""

from __future__ import annotations

import json
import os
import shlex
import subprocess
from collections.abc import Callable
from typing import Any

Executor = Callable[[str, dict[str, Any]], dict[str, Any]]


class QlooError(RuntimeError):
    """Raised when a Qloo workflow fails or returns something unusable."""

    def __init__(self, operation: str, code: str, detail: str = "") -> None:
        self.operation = operation
        self.code = code
        super().__init__(f"qloo {operation} failed: {code}{' - ' + detail if detail else ''}")


def _command() -> list[str]:
    return shlex.split(os.environ.get("GROUPTASTE_QLOO_CMD", "qloo"))


def parse_result(operation: str, stdout: str) -> dict[str, Any]:
    """Parse the last JSON object `qloo exec` printed and surface its errors."""
    lines = [line for line in stdout.strip().splitlines() if line.strip()]
    if not lines:
        raise QlooError(operation, "EMPTY_OUTPUT")
    try:
        data = json.loads(lines[-1])
    except json.JSONDecodeError as exc:
        raise QlooError(operation, "BAD_JSON", lines[-1][:200]) from exc
    if not isinstance(data, dict):
        raise QlooError(operation, "BAD_JSON", "expected an object")
    if "error" in data:
        err = data["error"] if isinstance(data["error"], dict) else {}
        raise QlooError(operation, str(err.get("code", "UNKNOWN")), str(err.get("recovery", "")))
    return data


def _pick_candidate(issue: dict[str, Any], prefer_type: str | None) -> str | None:
    """Pick the highest-popularity candidate, preferring a matching entity type."""
    cands = [c for c in (issue.get("candidates") or []) if isinstance(c, dict) and c.get("id")]
    if not cands:
        return None
    if prefer_type:
        want = prefer_type if prefer_type.startswith("urn:") else f"urn:entity:{prefer_type}"
        typed = [c for c in cands if c.get("type") == want]
        if typed:
            cands = typed
    best = max(cands, key=lambda c: float(c.get("popularity") or 0.0))
    return str(best["id"])


def auto_resolve_payload(payload: dict[str, Any], data: dict[str, Any]) -> dict[str, Any] | None:
    """Replace ambiguous name signals with entity IDs from a needs_input response.

    Picks the most popular candidate per issue. For `signals`, prefers the
    payload's `target_type` when that type appears in the candidate list (so
    "Interstellar" resolves to the movie, not the album). Location filters keep
    the top candidate regardless of type.
    """
    issues = ((data.get("resolution") or {}).get("issues") or [])
    if not issues:
        return None
    prefer = payload.get("target_type") if isinstance(payload.get("target_type"), str) else None
    mapping: dict[str, str] = {}
    for issue in issues:
        if not isinstance(issue, dict) or not issue.get("input"):
            continue
        # Only prefer target_type for signal-entity ambiguity, not locations.
        field = issue.get("field")
        chosen = _pick_candidate(issue, prefer if field == "signals" else None)
        if chosen:
            mapping[str(issue["input"])] = chosen
    if not mapping:
        return None
    patched = dict(payload)
    signals = patched.get("signals")
    if isinstance(signals, list):
        patched["signals"] = [mapping.get(s, s) if isinstance(s, str) else s for s in signals]
    loc = patched.get("filter_location")
    if isinstance(loc, str) and loc in mapping:
        patched["filter_location"] = mapping[loc]
    return patched


def _exec_once(operation: str, payload: dict[str, Any], timeout: float) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            [*_command(), "exec", operation, "--input", json.dumps(payload)],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError as exc:
        raise QlooError(operation, "QLOO_CLI_MISSING", "install @qloo/qloo-harness") from exc
    except subprocess.TimeoutExpired as exc:
        raise QlooError(operation, "TIMEOUT", f"no answer in {timeout:.0f}s") from exc
    if proc.returncode not in (0, None) and not proc.stdout.strip():
        detail = (proc.stderr or "").strip()[:200] or f"exit {proc.returncode}"
        raise QlooError(operation, "CLI_FAILED", detail)
    return parse_result(operation, proc.stdout)


def cli_executor(operation: str, payload: dict[str, Any], timeout: float = 90.0) -> dict[str, Any]:
    """Run one `qloo exec <operation>` call and return its JSON result.

    When Qloo returns `needs_input` (ambiguous names), automatically pick the
    top candidate per issue and retry once with entity IDs. Offline fakes that
    return needs_input without candidates still surface as errors in build_plan.
    """
    data = _exec_once(operation, payload, timeout)
    if data.get("status") != "needs_input":
        return data
    patched = auto_resolve_payload(payload, data)
    if not patched or patched == payload:
        return data
    data2 = _exec_once(operation, patched, timeout)
    # Keep a breadcrumb of what we auto-resolved for the evidence section.
    data2.setdefault("notes", [])
    if isinstance(data2.get("notes"), list):
        data2["notes"].append("auto_resolved_ambiguous_signals")
    # Attach original resolution for debugging without failing the plan.
    data2.setdefault("auto_resolution", {"from": data.get("resolution"), "payload_signals": patched.get("signals")})
    return data2
