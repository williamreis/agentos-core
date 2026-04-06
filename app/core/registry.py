from __future__ import annotations
from typing import Any
from app.core.clients import FAQClient, FraudClient

_clients: dict[str, Any] = {}


def _ensure_loaded() -> None:
    if not _clients:
        _clients["fraud"] = FraudClient()
        _clients["faq"] = FAQClient()


def get_client(name: str):
    """Retorna o cliente responsável pela execução do agente (não chamar agente direto no executor)."""
    _ensure_loaded()
    if name not in _clients:
        raise KeyError(f"agente desconhecido: {name}")
    return _clients[name]


def get_agent(name: str):
    """Alias do checklist: mesmo que get_client (execução via camada de cliente)."""
    return get_client(name)


# Metadados somente leitura (dashboard)
AGENT_MANIFEST: list[dict[str, Any]] = [
    {
        "name": "fraud",
        "description": "Classificação de risco com regras, heurística e classificador semântico opcional (sem RAG de FAQ).",
        "tools": [
            "pattern_checker",
            "risk_scorer",
            "semantic_classifier (opcional)",
        ],
    },
    {
        "name": "faq",
        "description": "Respostas a partir de documentos indexados (RAG).",
        "tools": ["retrieve_docs", "summarizer"],
    },
]
