from __future__ import annotations
import json
import re

from app.core.base_agent import BaseAgent
from app.shared.rag.rag_tool import retrieve_docs

_CREDENTIAL_RX = re.compile(
    r"(?i)\b("
    r"senha|password|passwd|credencial|credentials|"
    r"pin\b|cvv|cvc|token\s*de\s*acesso|2fa|c[oó]digo\s*de\s*verifica"
    r")\b"
)


def _is_credential_solicitation(text: str) -> bool:
    if _CREDENTIAL_RX.search(text):
        return True
    # Frases comuns de engenharia social (curtas)
    if re.search(
            r"(?i)(me\s+(envie|mande|passe)|informe\s+sua|digite\s+sua).{0,40}(senha|credencial)",
            text,
    ):
        return True
    return False


def summarizer(chunks: list[dict[str, str]]) -> str:
    if not chunks:
        return (
            "Não encontrei no FAQ conteúdo relacionado à sua pergunta."
        )
    parts = [c["text"] for c in chunks[:2]]
    joined = " ".join(parts)
    if len(joined) > 400:
        joined = joined[:397] + "..."
    return f"Com base na documentação: {joined}"


class FAQAgent(BaseAgent):
    name = "faq"

    def run(self, user_input: str) -> str:
        if _is_credential_solicitation(user_input):
            payload = {
                "agent": self.name,
                "answer": (
                    "Não posso ajudar com pedidos de senha, credenciais ou dados sensíveis. "
                    "Use canais oficiais da sua organização ou redefinição de senha no sistema apropriado."
                ),
                "sources": [],
                "intent": "refused_credential_request",
            }
            return json.dumps(payload, ensure_ascii=False)

        docs = retrieve_docs(user_input, top_k=3, min_hits=1)
        answer = summarizer(docs)
        payload = {
            "agent": self.name,
            "answer": answer,
            "sources": docs,
            "intent": "faq_rag",
        }
        return json.dumps(payload, ensure_ascii=False)
