from __future__ import annotations
import json
import time
from typing import Any
from app.core.registry import get_client
from app.shared.logging.logger import log_execution

MAX_STEPS = 8


def run_agent(agent_name: str, user_input: str, app_id: str | None = None) -> dict[str, Any]:
    started = time.perf_counter()
    steps = 0
    try:
        client = get_client(agent_name)
        output: str | None = None
        while steps < MAX_STEPS:
            steps += 1
            output = client.run(user_input)
            break

        elapsed_ms = (time.perf_counter() - started) * 1000
        log_execution(
            agent=agent_name,
            elapsed_ms=elapsed_ms,
            status="ok",
            steps=steps,
            app_id=app_id,
        )

        parsed: Any = output
        if isinstance(output, str):
            try:
                parsed = json.loads(output)
            except json.JSONDecodeError:
                parsed = output

        return {
            "status": "ok",
            "agent": agent_name,
            "output": parsed,
            "elapsed_ms": round(elapsed_ms, 2),
            "steps": steps,
        }
    except Exception as exc:
        elapsed_ms = (time.perf_counter() - started) * 1000
        log_execution(
            agent=agent_name,
            elapsed_ms=elapsed_ms,
            status="error",
            steps=steps,
            app_id=app_id,
            error=str(exc),
        )
        return {
            "status": "error",
            "agent": agent_name,
            "message": str(exc),
            "elapsed_ms": round(elapsed_ms, 2),
            "steps": steps,
        }
