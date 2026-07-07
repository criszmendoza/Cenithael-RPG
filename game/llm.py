import json
import os

from dotenv import load_dotenv
from together import Together

from game.config import MODEL

_client: Together | None = None


def get_client() -> Together:
    global _client
    if _client is None:
        load_dotenv()
        api_key = os.getenv("TOGETHER_API_KEY")
        if not api_key:
            raise ValueError("TOGETHER_API_KEY no está configurada. Copia .env.example a .env")
        _client = Together(api_key=api_key)
    return _client


def parse_json_response(text: str) -> dict:
    if not text:
        return {}
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            return json.loads(text[start : end + 1])
        raise


def ask_json(messages: list, temperature: float = 0.7) -> dict:
    output = get_client().chat.completions.create(
        model=MODEL,
        messages=messages,
        response_format={"type": "json_object"},
        temperature=temperature,
    )
    return parse_json_response(output.choices[0].message.content)
