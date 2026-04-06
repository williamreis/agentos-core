from __future__ import annotations
import json
from app.agents.fraud.pipeline import run_fraud_pipeline
from app.core.base_agent import BaseAgent


class FraudAgent(BaseAgent):
    name = "fraud"

    def run(self, user_input: str) -> str:
        pipe = run_fraud_pipeline(user_input)
        summary = pipe["summary"]
        matches = pipe["pattern_detection"]["matches"]

        payload: dict = {
            "agent": self.name,
            "input_preview": (user_input or "")[:200],
            # Caminho explícito do pipeline (auditoria / UI)
            "pipeline": {
                "pattern_detection": pipe["pattern_detection"],
                "heuristic": pipe["heuristic"],
                "classification": pipe["classification"],
                "context_rag": pipe["context_rag"],  # sempre vazio: fraud não usa índice FAQ/PDF
                "summary": {
                    **summary,
                    "recommended_action": _recommended_action(summary["risk_level"]),
                },
            },
            # Compatível com clientes que só leem flags + risk
            "flags": pipe["flags_legacy"],
            "risk": {
                "score": summary["final_score"],
                "risk_level": summary["risk_level"],
                "flag_count": len(matches),
            },
        }
        return json.dumps(payload, ensure_ascii=False)


def _recommended_action(risk_level: str) -> str:
    return {
        "high": "block_or_escalate",
        "medium": "manual_review",
        "low": "log_monitor",
    }.get(risk_level, "log_monitor")
