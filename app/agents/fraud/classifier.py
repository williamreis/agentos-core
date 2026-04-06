from __future__ import annotations
import os
from functools import lru_cache
from typing import Any
import numpy as np
from app.config import get_settings

# Frases âncora por rótulo (PT/EN) — comparação por cosseno via embeddings normalizados.
_LABEL_PROTOTYPES: dict[str, list[str]] = {
    "phishing_like": [
        "Clique aqui para confirmar seus dados bancários com urgência.",
        "Click here to verify your account before it is suspended.",
    ],
    "credential_harvesting": [
        "Me envie sua senha e o código SMS para liberar o acesso.",
        "Send your password and OTP to unlock your profile.",
    ],
    "scam_urgency": [
        "Pague agora via PIX ou seu CPF será bloqueado hoje.",
        "Transfer Bitcoin immediately or lose your funds forever.",
    ],
    "legitimate_business": [
        "Segue o relatório semanal em anexo para sua revisão quando possível.",
        "Could you approve the budget proposal by next Friday?",
    ],
}


def _semantic_enabled() -> bool:
    raw = os.environ.get("FRAUD_SEMANTIC")
    if raw is not None and str(raw).strip() != "":
        v = str(raw).strip().lower()
        if v in ("1", "true", "yes", "on"):
            return True
        if v in ("0", "false", "no", "off"):
            return False
    return get_settings().fraud_semantic_enabled


@lru_cache(maxsize=1)
def _label_embedding_matrix() -> tuple[list[str], np.ndarray]:
    """Uma média L2-normalizada de protótipos por rótulo."""
    import faiss

    from app.shared.rag.faiss_store import encode_normalize

    labels = list(_LABEL_PROTOTYPES.keys())
    vectors: list[np.ndarray] = []
    for label in labels:
        texts = _LABEL_PROTOTYPES[label]
        emb = encode_normalize(texts)
        centroid = emb.mean(axis=0, keepdims=True)
        faiss.normalize_L2(centroid)
        vectors.append(centroid[0])
    mat = np.stack(vectors, axis=0).astype(np.float32)
    return labels, mat


def optional_semantic_classify(text: str) -> dict[str, Any] | None:
    """
    Retorna o rótulo de maior similaridade e confiança aproximada.
    Desligado por padrão (config / env); falha silenciosa se o encoder não carregar.
    """
    if not _semantic_enabled():
        return None
    if not text or not text.strip():
        return None
    try:
        from app.shared.rag.faiss_store import encode_normalize
    except Exception:
        return None

    try:
        labels, mat = _label_embedding_matrix()
        q = encode_normalize([text[:2000]])
        sims = (q @ mat.T)[0]
        order = np.argsort(-sims)
        top_i = int(order[0])
        second_i = int(order[1]) if len(order) > 1 else top_i
        top_sim = float(sims[top_i])
        second_sim = float(sims[second_i])
        margin = max(0.0, top_sim - second_sim)
        confidence = float(max(0.0, min(1.0, (top_sim - 0.25) * 1.15 + margin * 0.5)))

        by_label = {labels[j]: round(float(sims[j]), 4) for j in range(len(labels))}
        return {
            "label": labels[top_i],
            "confidence": round(confidence, 4),
            "similarity_top": round(top_sim, 4),
            "scores_by_label": by_label,
            "method": "embedding_cosine_prototypes",
        }
    except Exception:
        return None


def merge_scores(heuristic: dict[str, Any], semantic: dict[str, Any] | None) -> dict[str, Any]:
    """Combina heurística com ajuste opcional do classificador semântico."""
    base = int(heuristic.get("score", 10))
    level = str(heuristic.get("risk_level", "low"))

    if not semantic:
        return {
            "final_score": base,
            "risk_level": level,
            "adjustment": 0,
            "rationale": "Somente heurística de padrões (classificador semântico desligado ou indisponível).",
        }

    label = semantic.get("label", "")
    conf = float(semantic.get("confidence", 0.0))
    adjustment = 0
    rationale_parts: list[str] = []

    if label in ("phishing_like", "credential_harvesting", "scam_urgency"):
        adjustment = int(round(conf * 22))
        rationale_parts.append(
            f"Modelo semântico sugere '{label}' (conf.≈{conf:.2f}); score reforçado."
        )
    elif label == "legitimate_business":
        adjustment = -int(round(conf * 15))
        rationale_parts.append(
            f"Modelo semântico sugere contexto legítimo (conf.≈{conf:.2f}); score atenuado."
        )
    else:
        rationale_parts.append("Classificação semântica sem ajuste direto para este rótulo.")

    final = int(max(5, min(100, base + adjustment)))

    if final >= 75:
        new_level = "high"
    elif final >= 45:
        new_level = "medium"
    else:
        new_level = "low"

    rationale = " ".join(rationale_parts) + f" Heurística: {base} → final: {final}."

    return {
        "final_score": final,
        "risk_level": new_level,
        "adjustment": adjustment,
        "rationale": rationale,
    }
