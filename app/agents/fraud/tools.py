from __future__ import annotations
from typing import Any
from app.agents.fraud.patterns import PatternMatch, detect_patterns, matches_to_legacy_flags
from app.agents.fraud.scoring import heuristic_risk


def pattern_checker(text: str) -> list[dict[str, str]]:
    """Alias do checklist: retorna lista {pattern, matched}."""
    return matches_to_legacy_flags(detect_patterns(text))


def risk_scorer(flags: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Aceita o formato legado (só `pattern`) ou matches completos com `severity`.
    """
    if not flags:
        return heuristic_risk([])
    if "severity" in flags[0]:
        return heuristic_risk(flags)  # type: ignore[arg-type]
    matches: list[PatternMatch] = [
        PatternMatch(
            pattern_id=str(f.get("pattern", "unknown")),
            category="legacy",
            severity=2,
        )
        for f in flags
    ]
    return heuristic_risk(matches)
