"""
=============================================================
BiscuitAI Chatbot — Knowledge Base Builder
=============================================================
Reads all .txt files from knowledge/ folder,
chunks them, embeds them, and stores in ChromaDB.

Run once to build the vector store:
    python backend/chatbot/knowledge_base.py

Re-run any time knowledge files are updated.
=============================================================
"""

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import chromadb
from chromadb.utils import embedding_functions

KNOWLEDGE_DIR  = os.path.join(os.path.dirname(__file__), "knowledge")
CHROMA_DB_PATH = os.path.join(os.path.dirname(__file__), "chroma_db")
COLLECTION_NAME = "biscuitai_knowledge"

# ── Chunk text into overlapping segments ──────────────────
def chunk_text(text: str, chunk_size: int = 600, overlap: int = 100) -> list[str]:
    """Split text into chunks with overlap so context isn't lost at boundaries."""
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk_words = words[i: i + chunk_size]
        chunks.append(" ".join(chunk_words))
        i += chunk_size - overlap
    return [c.strip() for c in chunks if len(c.strip()) > 50]


# ── Load all knowledge files ───────────────────────────────
def load_knowledge_files() -> list[dict]:
    """Load all .txt files from knowledge/ directory."""
    documents = []
    if not os.path.exists(KNOWLEDGE_DIR):
        print(f"[ERROR] Knowledge directory not found: {KNOWLEDGE_DIR}")
        return documents

    for filename in os.listdir(KNOWLEDGE_DIR):
        if not filename.endswith(".txt"):
            continue
        filepath = os.path.join(KNOWLEDGE_DIR, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read().strip()

        source = filename.replace(".txt", "")
        chunks = chunk_text(content)

        for i, chunk in enumerate(chunks):
            documents.append({
                "id":       f"{source}_{i}",
                "text":     chunk,
                "metadata": {"source": source, "chunk_index": i}
            })

        print(f"  [OK] {filename} → {len(chunks)} chunks")

    return documents


# ── Build / rebuild ChromaDB collection ───────────────────
def build_knowledge_base(force_rebuild: bool = False) -> chromadb.Collection:
    """Create or load ChromaDB collection with all knowledge chunks."""

    os.makedirs(CHROMA_DB_PATH, exist_ok=True)

    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)

    # Use default sentence-transformers embedding (all-MiniLM-L6-v2, runs locally)
    embed_fn = embedding_functions.DefaultEmbeddingFunction()

    # Delete and rebuild if forced
    if force_rebuild:
        try:
            client.delete_collection(COLLECTION_NAME)
            print(f"[INFO] Existing collection deleted — rebuilding...")
        except Exception:
            pass

    # Check if collection already exists with data
    try:
        collection = client.get_collection(
            name=COLLECTION_NAME,
            embedding_function=embed_fn
        )
        count = collection.count()
        if count > 0 and not force_rebuild:
            print(f"[INFO] Knowledge base already exists ({count} chunks). Skipping rebuild.")
            print("[INFO] Pass force_rebuild=True to rebuild.")
            return collection
    except Exception:
        pass

    # Create fresh collection
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embed_fn,
        metadata={"hnsw:space": "cosine"}
    )

    # Load and index documents
    print("\n[INFO] Loading knowledge files...")
    documents = load_knowledge_files()

    if not documents:
        print("[ERROR] No knowledge files found. Check knowledge/ directory.")
        return collection

    # Add in batches of 50
    batch_size = 50
    for i in range(0, len(documents), batch_size):
        batch = documents[i: i + batch_size]
        collection.add(
            ids       = [d["id"]       for d in batch],
            documents = [d["text"]     for d in batch],
            metadatas = [d["metadata"] for d in batch],
        )

    print(f"\n[OK] Knowledge base built: {collection.count()} total chunks indexed")
    print(f"[OK] Stored at: {CHROMA_DB_PATH}")
    return collection


# ── Retrieval function ─────────────────────────────────────
def get_collection() -> chromadb.Collection:
    """Get the existing ChromaDB collection (builds if not exists)."""
    os.makedirs(CHROMA_DB_PATH, exist_ok=True)
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    embed_fn = embedding_functions.DefaultEmbeddingFunction()

    try:
        collection = client.get_collection(
            name=COLLECTION_NAME,
            embedding_function=embed_fn
        )
        if collection.count() == 0:
            return build_knowledge_base(force_rebuild=True)
        return collection
    except Exception:
        return build_knowledge_base(force_rebuild=True)


def retrieve_context(query: str, n_results: int = 4) -> list[str]:
    """Retrieve the most relevant knowledge chunks for a query."""
    collection = get_collection()
    results = collection.query(
        query_texts=[query],
        n_results=min(n_results, collection.count())
    )
    return results["documents"][0] if results["documents"] else []


# ── Entry point ────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 56)
    print("  BiscuitAI — Knowledge Base Builder")
    print("=" * 56)
    build_knowledge_base(force_rebuild=True)
    print("\n[TEST] Running sample query...")
    chunks = retrieve_context("What tech stack does BiscuitAI use?")
    print(f"  Retrieved {len(chunks)} chunks")
    for i, chunk in enumerate(chunks):
        print(f"\n  Chunk {i+1}: {chunk[:120]}...")
    print("\nDone.")
