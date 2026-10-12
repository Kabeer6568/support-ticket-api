import logging
import os
import time

import httpx
from dotenv import load_dotenv
from google import genai
from google.genai import errors

load_dotenv()
logger = logging.getLogger(__name__)


class AIServiceError(RuntimeError):
    """Raised when the AI provider cannot complete a request."""


def get_ai_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is missing")

    return genai.Client(api_key=api_key)


def generate_ai_response(prompt: str) -> str:
    if not prompt or not prompt.strip():
        raise ValueError("Prompt cannot be empty")

    client = get_ai_client()
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    max_retries = 3

    for attempt in range(1, max_retries + 1):
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt
            )

            text = getattr(response, "text", None)
            if text:
                return text

            raise ValueError("AI returned an empty response")

        except (
            errors.ServerError,
            errors.ClientError,
            errors.APIError,
            httpx.TransportError,
        ) as e:
            logger.warning("AI request failed (attempt %s/%s): %s", attempt, max_retries, e)

            if attempt == max_retries:
                raise AIServiceError("AI request failed after retries") from e

            wait_time = 2 ** (attempt - 1)
            time.sleep(wait_time)

    raise AIServiceError("AI request failed after retries")