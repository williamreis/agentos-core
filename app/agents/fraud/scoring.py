from __future__ import annotations
from typing import Any
from app.agents.fraud.patterns import PatternMatch


def heuristic_risk(matches: list[PatternMatch]) -> dict[str, Any]:
    """
    Converte severidades e categorias em score 0–100 e nível discretizado.
    Sem flags → risco residual baixo (não é “zero” para não superestimar confiança).
    """
    if not matches:
        return {
            "score": 10,
            "risk_level": "low",
            "flag_count": 0,
            "factors": {
                "pattern_severity_sum": 0,
                "category_hits": {},
                "note": "nenhum padrão de regra disparado",
            },
        }

    sev_sum = sum(int(m.get("severity", 2)) for m in matches)
    cat_counts: dict[str, int] = {}
    for m in matches:
        c = m.get("category", "unknown")
        cat_counts[c] = cat_counts.get(c, 0) + 1

    # Base + contribuição por severidade (teto para não saturar antes do modelo opcional)
    raw = 15 + sev_sum * 12 + min(len(matches) * 5, 20)
    score = int(max(15, min(88, raw)))

    if score >= 70:
        level = "high"
    elif score >= 40:
        level = "medium"
    else:
        level = "low"

    return {
        "score": score,
        "risk_level": level,
        "flag_count": len(matches),
        "factors": {
            "pattern_severity_sum": sev_sum,
            "category_hits": cat_counts,
        },
    }
