"""OpenAI-compatible embeddings client via keygateway."""
import sys
import os
import ssl
import httpx
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openai import OpenAI
from config import settings

_client: OpenAI = None


def _make_http_client():
    """Create httpx client with SSL verification disabled for corporate/educational gateways."""
    return httpx.Client(verify=False)


def get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL,
            http_client=_make_http_client(),
        )
    return _client


def embed_query(text: str) -> list[float]:
    client = get_client()
    response = client.embeddings.create(model=settings.EMBEDDING_MODEL, input=[text])
    return response.data[0].embedding


def embed_texts(texts: list[str]) -> list[list[float]]:
    client = get_client()
    response = client.embeddings.create(model=settings.EMBEDDING_MODEL, input=texts)
    return [item.embedding for item in response.data]
