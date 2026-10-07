import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import errors

load_dotenv()


def generate_ai_response(prompt: str):

    client = genai.Client(
        api_key=os.getenv("GEMINI_API_KEY")
    )

    max_retries = 3

    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt
            )

            return response.text

        except errors.ServerError as e:

            if attempt == max_retries - 1:
                raise e

            wait_time = 2 ** attempt
            time.sleep(wait_time)