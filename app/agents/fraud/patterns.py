"""Detecção de padrões (regex / regras) — primeira etapa do pipeline de fraude."""

from __future__ import annotations

import re
from typing import Any, TypedDict


class PatternMatch(TypedDict, total=False):
    pattern_id: str
    category: str
    severity: int
    matched_span_preview: str


# (regex, pattern_id, category, severity 1–3)
_RULES: list[tuple[str, str, str, int]] = [
    (
        r"(?i)\b(urgente|imediato|agora\s+mesmo|última\s+chance|prazo\s+expira)\b",
        "urgency_language",
        "urgency",
        2,
    ),
    (
        r"(?i)\b(bitcoin|cripto|criptomoeda|usdt|pix\s+para\s+liberar|gift\s*card)\b",
        "financial_scam_keywords",
        "financial_fraud",
        3,
    ),
    # Golpes comuns no BR: PIX + prêmio/sorteio/ganhar (mensagem curta ou longa).
    (
        r"(?i)\b(realizar|fazer|enviar|mandar|transferir)\s+pix\b.{0,140}\b(pr[eê]mio|ganhar|sorteio|resgatar|liberar)\b",
        "pix_prize_bait_verb",
        "financial_fraud",
        3,
    ),
    (
        r"(?i)\bpix\b.{0,120}\b(pr[eê]mio|sorteio|ganhar|resgatar|voc[eê]\s+foi\s+sorteado)\b",
        "pix_near_prize_language",
        "financial_fraud",
        3,
    ),
    (
        r"(?i)\b(ganhar|resgatar)\b.{0,80}\b(pr[eê]mio|pix)\b",
        "prize_or_pix_bait",
        "financial_fraud",
        2,
    ),
    (
        r"(?i)\b(golpe\s+do\s+pix|pix\s+falso|falso\s+pix|chave\s+pix\s+falsa)\b",
        "pix_scam_labels",
        "financial_fraud",
        3,
    ),
    # Gancho de sorteio/prêmio sem mencionar PIX na mesma frase (mensagens curtas).
    (
        r"(?i)\b(voc[eê]\s+foi\s+sortead[oa]|voc[eê]\s+[eé]\s+o\s+ganhador|voc[eê]\s+ganhou\s+o\s+sorteio)\b",
        "lottery_winner_hook",
        "financial_fraud",
        3,
    ),
    (
        r"(?i)\bparab[eé]ns\b.{0,60}\b(sorteado|ganhou|pr[eê]mio|vale[-\s]?bradesco|rod[aá]\s+da\s+sorte)\b",
        "congrats_prize_hook",
        "financial_fraud",
        2,
    ),
    (
        r"(?i)\b(bilhete\s+premiado|número\s+da\s+sorte|consulte\s+seu\s+pr[eê]mio)\b",
        "lottery_ticket_language",
        "financial_fraud",
        2,
    ),
    (
        r"(?i)\b(clique\s+aqui|clique\s+no\s+link|verificar\s+(sua\s+)?conta|atualizar\s+dados)\b",
        "phishing_style",
        "phishing",
        3,
    ),
    (
        r"(?i)\b(envie\s+(sua|o)\s*(senha|cpf)|mande\s+(o\s+)?pix|transferência\s+urgente)\b",
        "credential_or_transfer_request",
        "credential_theft",
        3,
    ),
    (
        r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b",
        "card_like_sequence",
        "pii_financial",
        2,
    ),
    (
        r"(?i)(bit\.ly|tinyurl|goo\.gl|short\.link|encurtador)",
        "url_shortener",
        "phishing",
        2,
    ),
    (
        r"(?i)\b(você\s+foi\s+(hackeado|bloqueado)|conta\s+suspensa|irregularidade\s+detectada)\b",
        "account_scare",
        "phishing",
        2,
    ),
    (
        r"(?:[A-ZÁÀÂÃÉÊÍÓÔÕÚÇ]{3,}\s*){4,}[A-ZÁÀÂÃÉÊÍÓÔÕÚÇ]{2,}",
        "excessive_uppercase",
        "urgency",
        1,
    ),
]


def detect_patterns(text: str) -> list[PatternMatch]:
    """Varre regras e devolve matches estruturados (sem duplicar o mesmo pattern_id)."""
    seen: set[str] = set()
    out: list[PatternMatch] = []
    # Evita regex pesadas em textos enormes
    scan = text[:12000]
    for rx, pid, category, severity in _RULES:
        if pid in seen:
            continue
        m = re.search(rx, scan)
        if not m:
            continue
        seen.add(pid)
        snippet = m.group(0).strip()
        if len(snippet) > 100:
            snippet = snippet[:97] + "..."
        out.append(
            PatternMatch(
                pattern_id=pid,
                category=category,
                severity=severity,
                matched_span_preview=snippet,
            )
        )
    return out


def matches_to_legacy_flags(matches: list[PatternMatch]) -> list[dict[str, str]]:
    """Formato compacto compatível com o checklist / ferramentas antigas."""
    return [{"pattern": m["pattern_id"], "matched": "true"} for m in matches]
