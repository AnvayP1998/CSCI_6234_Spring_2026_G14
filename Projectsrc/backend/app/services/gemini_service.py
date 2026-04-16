import anthropic
from typing import AsyncIterator

from app.core.config import settings

_client: anthropic.Anthropic | None = None
_async_client: anthropic.AsyncAnthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        if not settings.ANTHROPIC_API_KEY:
            raise RuntimeError("ANTHROPIC_API_KEY is not set in .env")
        _client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    return _client


def _get_async_client() -> anthropic.AsyncAnthropic:
    global _async_client
    if _async_client is None:
        if not settings.ANTHROPIC_API_KEY:
            raise RuntimeError("ANTHROPIC_API_KEY is not set in .env")
        _async_client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    return _async_client


def call_gemini(prompt: str) -> str:
    """Call Claude (Anthropic) for AI analysis. Function name kept for compatibility."""
    client = _get_client()
    message = client.messages.create(
        model=settings.ANTHROPIC_MODEL,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text.strip()


async def stream_gemini(prompt: str) -> AsyncIterator[str]:
    """Async-stream Claude tokens, yielding each text delta."""
    client = _get_async_client()
    async with client.messages.stream(
        model=settings.ANTHROPIC_MODEL,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        async for text in stream.text_stream:
            yield text
