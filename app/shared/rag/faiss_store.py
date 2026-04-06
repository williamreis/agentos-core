from __future__ import annotations
import json
import os
import re
from functools import lru_cache
from pathlib import Path
import numpy as np

INDEX_NAME = "rag_faiss.index"
CHUNKS_NAME = "rag_chunks.json"
MANIFEST_NAME = "rag_manifest.json"

DEFAULT_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def _project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def data_dir() -> Path:
    return _project_root() / "data"


def model_name() -> str:
    return os.environ.get("RAG_MODEL", DEFAULT_MODEL)


@lru_cache(maxsize=1)
def get_encoder():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(model_name())


def faiss_index_path() -> Path:
    return data_dir() / INDEX_NAME


def chunks_path() -> Path:
    return data_dir() / CHUNKS_NAME


def manifest_path() -> Path:
    return data_dir() / MANIFEST_NAME


def faiss_available() -> bool:
    return faiss_index_path().exists() and chunks_path().exists()


def load_manifest() -> dict | None:
    p = manifest_path()
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def load_chunks() -> list[dict]:
    raw = json.loads(chunks_path().read_text(encoding="utf-8"))
    return raw if isinstance(raw, list) else []


def load_faiss_index():
    import faiss

    return faiss.read_index(str(faiss_index_path()))


def encode_normalize(texts: list[str]) -> np.ndarray:
    import faiss

    model = get_encoder()
    emb = model.encode(
        texts,
        convert_to_numpy=True,
        show_progress_bar=len(texts) > 16,
    )
    emb = np.asarray(emb, dtype=np.float32)
    faiss.normalize_L2(emb)
    return emb


def chunk_text(text: str, source: str, *, max_len: int = 900, overlap: int = 120) -> list[dict[str, str]]:
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if not paragraphs:
        paragraphs = [text]
    chunks: list[dict[str, str]] = []
    for para in paragraphs:
        if len(para) <= max_len:
            chunks.append({"text": para, "source": source})
            continue
        start = 0
        while start < len(para):
            piece = para[start: start + max_len]
            chunks.append({"text": piece, "source": source})
            start += max_len - overlap
    return chunks


def extract_pdf_text(path: Path) -> str:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    parts: list[str] = []
    for page in reader.pages:
        t = page.extract_text()
        if t:
            parts.append(t)
    return "\n\n".join(parts)


def search_faiss(
        query: str,
        top_k: int,
        *,
        min_similarity: float,
) -> list[dict[str, str]]:
    """Inner product sobre vetores L2-normalizados ≈ similaridade de cosseno."""
    import faiss

    if not faiss_available():
        return []

    chunks = load_chunks()
    if not chunks:
        return []

    manifest = load_manifest()
    if manifest and manifest.get("model_name") != model_name():
        pass

    index = load_faiss_index()
    n = index.ntotal
    if n == 0:
        return []

    k = min(max(top_k * 4, top_k), n)
    q = encode_normalize([query])
    scores, ids = index.search(q, k)

    out: list[dict[str, str]] = []
    for sim, idx in zip(scores[0], ids[0]):
        if idx < 0 or idx >= len(chunks):
            continue
        if float(sim) < min_similarity:
            continue
        ch = chunks[idx]
        out.append(
            {
                "score": f"{float(sim):.4f}",
                "text": ch["text"],
                "source": ch.get("source", ""),
            }
        )
        if len(out) >= top_k:
            break
    return out


def build_index_from_chunks(chunks: list[dict[str, str]]) -> None:
    import faiss

    if not chunks:
        raise ValueError("Nenhum chunk para indexar.")

    texts = [c["text"] for c in chunks]
    emb = encode_normalize(texts)
    dim = emb.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(emb)

    ddir = data_dir()
    ddir.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(faiss_index_path()))
    chunks_path().write_text(json.dumps(chunks, ensure_ascii=False, indent=0), encoding="utf-8")
    manifest_path().write_text(
        json.dumps(
            {
                "model_name": model_name(),
                "dim": dim,
                "n_chunks": len(chunks),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
