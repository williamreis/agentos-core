from __future__ import annotations
import os
import re
from pathlib import Path
from app.shared.rag import faiss_store

"""RAG: FAISS + embeddings quando o índice existe; senão busca por palavras-chave."""

_CORPUS: list[str] = []
_KEYWORD_LOADED = False
_STOPWORDS = frozenset(
    """
    o a os as um uma uns umas de do da dos das em no na nos nas por com sem para
    que qual quais como quando onde pra ao à aos às pelo pela pelos pelas este essa
    isso isto aquilo ele ela eles elas eu tu você vocês nós se seu sua seus suas meu
    minha teu tua há foi ser era são é foi foram sendo ter tem tinha terão ao aos
    mais menos muito pouco já não sim ou então mas também só até sobre entre
    """.split()
)


def _default_min_similarity() -> float:
    raw = os.environ.get("RAG_MIN_SIMILARITY", "0.28")
    try:
        return float(raw)
    except ValueError:
        return 0.28


def _data_dir() -> Path:
    return Path(__file__).resolve().parents[3] / "data"


def _load_keyword_corpus() -> None:
    global _CORPUS, _KEYWORD_LOADED
    if _KEYWORD_LOADED:
        return
    path = _data_dir() / "faq_corpus.txt"
    if path.exists():
        text = path.read_text(encoding="utf-8")
        _CORPUS = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not _CORPUS:
        _CORPUS = [
            "Documentação em construção. Nenhum arquivo de corpus encontrado.",
        ]
    _KEYWORD_LOADED = True


def _meaningful_tokens(query: str) -> list[str]:
    raw = re.findall(r"[a-zA-Z0-9áàâãéêíóôõúçÁÀÂÃÉÊÍÓÔÕÚÇ]+", query.lower())
    out: list[str] = []
    for w in raw:
        if len(w) <= 2:
            continue
        if w in _STOPWORDS:
            continue
        out.append(w)
    return out


def _whole_word_hits(token: str, paragraph_lower: str) -> int:
    try:
        rx = re.compile(rf"\b{re.escape(token)}\b", re.IGNORECASE)
    except re.error:
        return 0
    return len(rx.findall(paragraph_lower))


def _retrieve_keyword(
        query: str,
        top_k: int,
        *,
        min_hits: int,
) -> list[dict[str, str]]:
    _load_keyword_corpus()
    tokens = _meaningful_tokens(query)
    if not tokens:
        return []

    scored: list[tuple[int, str]] = []
    for para in _CORPUS:
        low = para.lower()
        score = sum(_whole_word_hits(t, low) for t in tokens)
        scored.append((score, para))
    scored.sort(key=lambda x: x[0], reverse=True)

    best = scored[0][0] if scored else 0
    if best < min_hits:
        return []

    out: list[dict[str, str]] = []
    for score, text in scored[:top_k]:
        if score < min_hits:
            break
        out.append({"score": str(score), "text": text, "source": "keyword"})
    return out


def _use_faiss() -> bool:
    if os.environ.get("RAG_FORCE_KEYWORD", "").lower() in ("1", "true", "yes"):
        return False
    return faiss_store.faiss_available()


def retrieve_docs(
        query: str,
        top_k: int = 3,
        *,
        min_hits: int = 1,
        min_similarity: float | None = None,
) -> list[dict[str, str]]:
    """
    Com índice FAISS em data/: busca vetorial (cosseno via produto interno normalizado).
    Sem índice: fallback por palavras-chave (faq_corpus.txt).
    """
    if _use_faiss():
        ms = min_similarity if min_similarity is not None else _default_min_similarity()
        vec = faiss_store.search_faiss(query, top_k, min_similarity=ms)
        if vec:
            return vec
    return _retrieve_keyword(query, top_k, min_hits=min_hits)
