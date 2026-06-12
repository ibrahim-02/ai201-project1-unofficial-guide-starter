"""
Document ingestion and chunking pipeline.

load_documents() — reads all .txt files from documents/, strips the Reddit
    post header block (Title/Subreddit/URL/Score lines), and returns a list of
    {"text": str, "source": str} dicts where source is the filename.

chunk_text() — paragraph-aware chunking: splits on blank lines first so every
    chunk starts and ends at a clean paragraph boundary. Paragraphs are merged
    greedily up to chunk_size (500 chars). Overlap is achieved by carrying the
    last paragraph of the previous chunk into the next one.

chunk_documents() — applies chunk_text to every loaded document and attaches
    source metadata to each chunk for later citation in responses.
"""

import os
import re
from typing import TypedDict

DOCS_DIR = os.path.join(os.path.dirname(__file__), "documents")
CHUNK_SIZE = 500
OVERLAP = 100
MIN_CHUNK_SIZE = 150  # paragraphs shorter than this get merged with the next one

# Matches the 4-line Reddit-style header block at the top of each document
_HEADER_RE = re.compile(
    r"^Title:.*\nSubreddit:.*\nURL:.*\nScore:.*\n",
    re.MULTILINE,
)


class Document(TypedDict):
    text: str
    source: str


class Chunk(TypedDict):
    text: str
    source: str
    chunk_index: int


def _clean(text: str) -> str:
    # Remove Reddit header boilerplate
    text = _HEADER_RE.sub("", text)
    # Collapse 3+ blank lines to 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def load_documents(docs_dir: str = DOCS_DIR) -> list[Document]:
    docs: list[Document] = []
    for filename in sorted(os.listdir(docs_dir)):
        if not filename.endswith(".txt"):
            continue
        filepath = os.path.join(docs_dir, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            raw = f.read()
        text = _clean(raw)
        if text:
            docs.append({"text": text, "source": filename})
    return docs


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = OVERLAP,
               min_chunk_size: int = MIN_CHUNK_SIZE) -> list[str]:
    # Split into paragraphs on blank lines
    paragraphs = [p.strip() for p in re.split(r"\n\n+", text) if p.strip()]

    chunks: list[str] = []
    current_parts: list[str] = []
    current_len = 0

    for para in paragraphs:
        para_len = len(para)

        # If adding this paragraph exceeds chunk_size, save current chunk and start new one
        if current_len + para_len > chunk_size and current_parts:
            chunk_str = "\n\n".join(current_parts)
            # Only save if the chunk meets the minimum size threshold
            if len(chunk_str) >= min_chunk_size:
                chunks.append(chunk_str)
                # Overlap: carry the last paragraph into the next chunk
                overlap_part = current_parts[-1]
                if len(overlap_part) <= overlap:
                    current_parts = [overlap_part]
                    current_len = len(overlap_part)
                else:
                    current_parts = []
                    current_len = 0
            # If too short, keep accumulating (don't reset)

        # If a single paragraph exceeds chunk_size, save it as its own chunk
        if para_len > chunk_size and not current_parts:
            chunks.append(para)
            continue

        current_parts.append(para)
        current_len += para_len

    # Flush remaining paragraphs
    if current_parts:
        chunks.append("\n\n".join(current_parts))

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

    oversized = [c for c in chunks if len(c["text"]) > CHUNK_SIZE * 2]
    print(f"Very large chunks (>1000 chars): {len(oversized)}")
    print(f"Empty chunks: {sum(1 for c in chunks if not c['text'].strip())}")

    print("\n--- 5 sample chunks ---")
    import random
    random.seed(42)
    for c in random.sample(chunks, min(5, len(chunks))):
        print(f"\n[{c['source']} | idx {c['chunk_index']} | {len(c['text'])} chars]")
        print(c["text"])
        print("-" * 60)
