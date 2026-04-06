#!/usr/bin/env python3
"""
Ingere arquivos em data/ (*.txt, *.pdf) no índice FAISS.

Uso (na raiz do projeto):
  python -m scripts.ingest_rag

Variáveis opcionais:
  RAG_MODEL — modelo sentence-transformers (padrão: multilingual MiniLM).
"""

from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.shared.rag.faiss_store import (  # noqa: E402
    build_index_from_chunks,
    chunk_text,
    data_dir,
    extract_pdf_text,
    model_name,
)


def collect_chunks() -> list[dict[str, str]]:
    ddir = data_dir()
    if not ddir.is_dir():
        raise SystemExit(f"Diretório não encontrado: {ddir}")

    all_chunks: list[dict[str, str]] = []

    for path in sorted(ddir.glob("*.txt")):
        text = path.read_text(encoding="utf-8", errors="replace")
        all_chunks.extend(chunk_text(text, source=str(path.name)))

    for path in sorted(ddir.glob("*.pdf")):
        text = extract_pdf_text(path)
        all_chunks.extend(chunk_text(text, source=str(path.name)))

    return all_chunks


def main() -> None:
    print(f"Modelo: {model_name()}")
    chunks = collect_chunks()
    print(f"Chunks gerados: {len(chunks)}")
    if not chunks:
        raise SystemExit("Nenhum texto extraído de data/*.txt ou data/*.pdf.")

    build_index_from_chunks(chunks)
    print(f"Índice gravado em {data_dir()}/ (rag_faiss.index, rag_chunks.json, rag_manifest.json)")


if __name__ == "__main__":
    main()
