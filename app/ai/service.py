import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

def generate_ai_response(conversation: str) -> str:

    response = client.responses.create(
        model="gpt-6-luna",
        instructions=(
            "You are an AI customer support assistant. "
            "Be helpful, concise, and professional. "
            "If you do not have enough information to confidently "
            "solve the customer's problem, say that you need human support."
        ),
        input=conversation
    )

    return response.output_text