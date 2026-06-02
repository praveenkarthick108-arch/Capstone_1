"""
Ingestion pipeline: embed incidents and store in ChromaDB + BM25 index.
"""
import os
import sys
import pickle
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx
from config import settings
from data.preprocessor import load_and_clean, prepare_documents, get_bm25_corpus
from rank_bm25 import BM25Okapi
import chromadb
from openai import OpenAI


def get_openai_client() -> OpenAI:
    return OpenAI(
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.OPENAI_BASE_URL,
        http_client=httpx.Client(verify=False),
    )


def get_chroma_collection(reset: bool = False):
    client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
    if reset:
        try:
            client.delete_collection(settings.CHROMA_COLLECTION)
        except Exception:
            pass
    collection = client.get_or_create_collection(
        name=settings.CHROMA_COLLECTION,
        metadata={"hnsw:space": "cosine"},
    )
    return collection


def embed_texts_batch(client: OpenAI, texts: list[str], batch_size: int = 50) -> list[list[float]]:
    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i: i + batch_size]
        response = client.embeddings.create(model=settings.EMBEDDING_MODEL, input=batch)
        batch_embeddings = [item.embedding for item in response.data]
        all_embeddings.extend(batch_embeddings)
        print(f"  Embedded {min(i + batch_size, len(texts))}/{len(texts)} texts...")
        time.sleep(0.2)
    return all_embeddings


def build_bm25_index(corpus: list[list[str]]) -> BM25Okapi:
    return BM25Okapi(corpus)


def save_bm25_index(bm25: BM25Okapi, corpus: list[list[str]], alarm_ids: list[str]):
    data = {"bm25": bm25, "corpus": corpus, "alarm_ids": alarm_ids}
    with open(settings.BM25_INDEX_PATH, "wb") as f:
        pickle.dump(data, f)
    print(f"BM25 index saved to {settings.BM25_INDEX_PATH}")


def load_bm25_index() -> tuple:
    with open(settings.BM25_INDEX_PATH, "rb") as f:
        data = pickle.load(f)
    return data["bm25"], data["corpus"], data["alarm_ids"]


def run_ingestion(csv_path: str = None, force_reingest: bool = False):
    csv_path = csv_path or settings.DATA_CSV_PATH
    print(f"Loading dataset from {csv_path}...")
    df = load_and_clean(csv_path)
    print(f"Loaded {len(df)} records after cleaning.")

    ids, texts, metadatas = prepare_documents(df)
    corpus = get_bm25_corpus(df)

    collection = get_chroma_collection(reset=force_reingest)
    existing = collection.count()

    if existing > 0 and not force_reingest:
        print(f"ChromaDB already has {existing} records. Skipping vector ingestion.")
    else:
        print("Embedding documents...")
        oai_client = get_openai_client()
        embeddings = embed_texts_batch(oai_client, texts)

        print("Inserting into ChromaDB...")
        batch_size = 100
        for i in range(0, len(ids), batch_size):
            collection.upsert(
                ids=ids[i: i + batch_size],
                embeddings=embeddings[i: i + batch_size],
                documents=texts[i: i + batch_size],
                metadatas=metadatas[i: i + batch_size],
            )
        print(f"ChromaDB ingestion complete. Total records: {collection.count()}")

    if not os.path.exists(settings.BM25_INDEX_PATH) or force_reingest:
        print("Building BM25 index...")
        bm25 = build_bm25_index(corpus)
        save_bm25_index(bm25, corpus, ids)
    else:
        print(f"BM25 index already exists at {settings.BM25_INDEX_PATH}")

    print("Ingestion pipeline complete.")
    return len(df)


if __name__ == "__main__":
    run_ingestion(force_reingest="--force" in sys.argv)
