import json
import re
import time
import urllib.request
import urllib.error

from app.core.config import settings

_MAX_RETRIES = 3


def call_gemini(prompt: str) -> str:
    """Send a prompt to Gemini and return the text response.
    Automatically retries on 429 rate-limit errors using the retry delay
    reported by the API.
    """
    if not settings.GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not set in .env")

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{settings.GEMINI_MODEL}:generateContent?key={settings.GEMINI_API_KEY}"
    )
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": 4096},
    }).encode()

    for attempt in range(_MAX_RETRIES):
        req = urllib.request.Request(
            url, data=body, headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read())
                return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except urllib.error.HTTPError as e:
            err = json.loads(e.read())
            msg = err.get("error", {}).get("message", str(e))

            if e.code == 429 and attempt < _MAX_RETRIES - 1:
                # Parse "Please retry in Xs" from the error message
                match = re.search(r"retry in ([\d.]+)s", msg)
                wait = float(match.group(1)) if match else 35.0
                time.sleep(wait + 1)  # +1s buffer
                continue

            raise RuntimeError(f"Gemini API error: {msg}")

    raise RuntimeError("Gemini API: max retries exceeded")
