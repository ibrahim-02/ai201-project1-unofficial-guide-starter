"""
Embedding and vector store pipeline.

Loads chunks from ingest.py, embeds them with all-MiniLM-L6-v2,
and upserts them into a persistent ChromaDB collection.

Run once (or re-run to rebuild the index from scratch):
    python embed.py
"""

import os
import chromadb
from sentence_transformers import SentenceTransformer
from ingest import chunk_documents, load_documents

CHROMA_DIR = os.path.join(os.path.dirname(__file__), "chroma_db")
COLLECTION_NAME = "student_guides"
MODEL_NAME = "all-MiniLM-L6-v2"


def build_vector_store() -> chromadb.Collection:
    print("Loading documents and chunking...")
    docs = load_documents()
    chunks = chunk_documents(docs)
    print(f"  {len(docs)} documents -> {len(chunks)} chunks")

    print(f"Loading embedding model '{MODEL_NAME}'...")
    model = SentenceTransformer(MODEL_NAME)

    print("Embedding chunks...")
    texts = [c["text"] for c in chunks]
    embeddings = model.encode(texts, show_progress_bar=True, batch_size=32)

    print(f"Upserting into ChromaDB at '{CHROMA_DIR}'...")
    client = chromadb.PersistentClient(path=CHROMA_DIR)

    # Drop and recreate so re-runs are idempotent
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    collection.upsert(
        ids=[f"{c['source']}__chunk{c['chunk_index']}" for c in chunks],
        embeddings=[e.tolist() for e in embeddings],
        documents=texts,
        metadatas=[{"source": c["source"], "chunk_index": c["chunk_index"]} for c in chunks],
    )

    print(f"Done. {collection.count()} vectors stored.")
    return collection


def get_collection() -> chromadb.Collection:
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    return client.get_collection(COLLECTION_NAME)


if __name__ == "__main__":
    collection = build_vector_store()

    # Quick smoke test
    model = SentenceTransformer(MODEL_NAME)
    test_query = "What is the best dining hall at BU?"
    query_embedding = model.encode([test_query])[0].tolist()
    results = collection.query(query_embeddings=[query_embedding], n_results=3)
    print(f"\nTest query: '{test_query}'")
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        print(f"  [{meta['source']}] {doc[:120]}...")
