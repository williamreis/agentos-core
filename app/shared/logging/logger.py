from __future__ import annotations
import json
import sys
from datetime import UTC, datetime
from typing import Any


def log_execution(
        *,
        agent: str,
        elapsed_ms: float,
        status: str,
        steps: int,
        app_id: str | None = None,
        error: str | None = None,
) -> None:
    payload: dict[str, Any] = {
        "ts": datetime.now(UTC).isoformat(),
        "agent": agent,
        "elapsed_ms": elapsed_ms,
        "status": status,
        "steps": steps,
        "app_id": app_id,
    }
    if error:
        payload["error"] = error
    print(json.dumps(payload, ensure_ascii=False), file=sys.stderr)
