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


def cli_executor(operation: str, payload: dict[str, Any], timeout: float = 60.0) -> dict[str, Any]:
    """Run one `qloo exec <operation>` call and return its JSON result."""
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
    return parse_result(operation, proc.stdout)


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
