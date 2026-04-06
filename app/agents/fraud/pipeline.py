from __future__ import annotations
from typing import Any
from app.agents.fraud.classifier import merge_scores, optional_semantic_classify
from app.agents.fraud.patterns import detect_patterns, matches_to_legacy_flags
from app.agents.fraud.scoring import heuristic_risk


def run_fraud_pipeline(user_input: str) -> dict[str, Any]:
    text = (user_input or "").strip()
    matches = detect_patterns(text)
    heur = heuristic_risk(matches)
    semantic = optional_semantic_classify(text) if text else None
    summary = merge_scores(heur, semantic)

    return {
        "pattern_detection": {
            "matches": matches,
            "count": len(matches),
        },
        "heuristic": heur,
        "classification": semantic,
        "context_rag": [],
        "summary": summary,
        "flags_legacy": matches_to_legacy_flags(matches),
    }
