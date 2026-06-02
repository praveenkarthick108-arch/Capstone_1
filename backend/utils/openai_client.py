"""Shared OpenAI client factory with SSL bypass for educational gateway."""
import httpx
from openai import OpenAI

_client: OpenAI = None


def get_openai_client(api_key: str, base_url: str) -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            http_client=httpx.Client(verify=False),
        )
    return _client
