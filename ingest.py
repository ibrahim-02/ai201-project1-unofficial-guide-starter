"""
Document ingestion and chunking pipeline.

load_documents() — reads all .txt files from documents/ and returns a list of
    {"text": str, "source": str} dicts where source is the filename.

chunk_text() — splits a single text string into overlapping character-level chunks.
    chunk_size=500, overlap=100 (see planning.md for rationale).

chunk_documents() — applies chunk_text to every loaded document and attaches
    source metadata to each chunk for later citation in responses.
"""

import os
from typing import TypedDict

DOCS_DIR = os.path.join(os.path.dirname(__file__), "documents")
CHUNK_SIZE = 500
OVERLAP = 100


class Document(TypedDict):
    text: str
    source: str


class Chunk(TypedDict):
    text: str
    source: str
    chunk_index: int


def load_documents(docs_dir: str = DOCS_DIR) -> list[Document]:
    docs: list[Document] = []
    for filename in sorted(os.listdir(docs_dir)):
        if not filename.endswith(".txt"):
            continue
        filepath = os.path.join(docs_dir, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read().strip()
        if text:
            docs.append({"text": text, "source": filename})
    return docs


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = OVERLAP) -> list[str]:
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        if end >= len(text):
            break
        start += chunk_size - overlap
    return chunks


def chunk_documents(docs: list[Document]) -> list[Chunk]:
    chunks: list[Chunk] = []
    for doc in docs:
        for i, chunk_text_str in enumerate(chunk_text(doc["text"])):
            chunks.append({
                "text": chunk_text_str,
                "source": doc["source"],
                "chunk_index": i,
            })
    return chunks


if __name__ == "__main__":
    docs = load_documents()
    print(f"Loaded {len(docs)} documents")

    chunks = chunk_documents(docs)
    print(f"Produced {len(chunks)} chunks")

    # Sanity checks
    oversized = [c for c in chunks if len(c["text"]) > CHUNK_SIZE]
    print(f"Oversized chunks (should be 0): {len(oversized)}")

    # Show a sample chunk
    if chunks:
        sample = chunks[5]
        print(f"\nSample chunk #{sample['chunk_index']} from '{sample['source']}':")
        print("-" * 60)
        print(sample["text"])
        print("-" * 60)
