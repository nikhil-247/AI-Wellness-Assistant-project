import os
from typing import Any

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS

load_dotenv()

app = Flask(__name__)
CORS(app, origins=os.getenv("FRONTEND_ORIGIN", "http://localhost:5173"))

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL")
MAX_MESSAGE_CHARS = 4_000
MAX_HISTORY_ITEMS = 10


class LLMConfigurationError(RuntimeError):
    """Raised when required provider configuration is missing."""


def call_llm(messages: list[dict[str, str]], temperature: float = 0.7) -> str:
    if not OPENROUTER_API_KEY or not OPENROUTER_MODEL:
        raise LLMConfigurationError(
            "Set OPENROUTER_API_KEY and OPENROUTER_MODEL in the backend environment."
        )

    response = requests.post(
        OPENROUTER_URL,
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": OPENROUTER_MODEL,
            "messages": messages,
            "temperature": temperature,
        },
        timeout=30,
    )
    response.raise_for_status()

    data: Any = response.json()
    choices = data.get("choices") if isinstance(data, dict) else None
    if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
        raise ValueError("LLM provider returned an unexpected response.")
    message = choices[0].get("message")
    content = message.get("content") if isinstance(message, dict) else None
    if not isinstance(content, str) or not content.strip():
        raise ValueError("LLM provider returned an empty response.")
    return content.strip()


def wellness_system_prompt() -> str:
    return (
        "You are Self Love, a calm and supportive AI wellness companion. "
        "Provide empathetic, practical, non-clinical responses. "
        "Do not diagnose conditions, prescribe medication, or present yourself as a therapist. "
        "For emergencies or immediate danger, encourage the user to contact local emergency "
        "services or a qualified professional. Keep responses concise and conversational."
    )


def provider_error(exc: Exception):
    app.logger.warning("AI provider request failed: %s", type(exc).__name__)
    return jsonify({"error": "The AI service could not complete the request. Please try again."}), 502


@app.get("/api/health")
def health():
    configured = bool(OPENROUTER_API_KEY and OPENROUTER_MODEL)
    return jsonify(
        {
            "status": "ok",
            "service": "self-love-backend",
            "ai_configured": configured,
        }
    )


@app.post("/api/chat")
def chat():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "A JSON object is required."}), 400

    message = payload.get("message")
    if not isinstance(message, str) or not message.strip():
        return jsonify({"error": "message must be a non-empty string."}), 400
    message = message.strip()
    if len(message) > MAX_MESSAGE_CHARS:
        return jsonify({"error": f"message must be at most {MAX_MESSAGE_CHARS} characters."}), 413

    mood_value = payload.get("mood", "neutral")
    mood = mood_value.strip() if isinstance(mood_value, str) else "neutral"
    mood = (mood or "neutral")[:80]

    history_value = payload.get("history", [])
    history = history_value if isinstance(history_value, list) else []
    safe_history = [
        {"role": item["role"], "content": item["content"][:MAX_MESSAGE_CHARS]}
        for item in history
        if isinstance(item, dict)
        and item.get("role") in {"user", "assistant"}
        and isinstance(item.get("content"), str)
        and item["content"].strip()
    ][-MAX_HISTORY_ITEMS:]

    messages = [
        {"role": "system", "content": wellness_system_prompt()},
        {
            "role": "system",
            "content": f"The user's current mood is: {mood}. Adapt your tone accordingly.",
        },
        *safe_history,
        {"role": "user", "content": message},
    ]

    try:
        return jsonify({"reply": call_llm(messages)})
    except LLMConfigurationError:
        return jsonify(
            {"error": "The AI service is not configured. Set the required backend environment variables."}
        ), 503
    except requests.RequestException as exc:
        return provider_error(exc)
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        return provider_error(exc)


@app.post("/api/story")
def story():
    payload = request.get_json(silent=True)
    if payload is None:
        payload = {}
    if not isinstance(payload, dict):
        return jsonify({"error": "A JSON object is required."}), 400

    theme_value = payload.get("theme", "a peaceful night")
    mood_value = payload.get("mood", "calm")
    if not isinstance(theme_value, str) or not isinstance(mood_value, str):
        return jsonify({"error": "theme and mood must be strings."}), 400

    theme = theme_value.strip() or "a peaceful night"
    mood = mood_value.strip() or "calm"
    if len(theme) > 200 or len(mood) > 80:
        return jsonify({"error": "theme must be at most 200 characters and mood at most 80."}), 400

    messages = [
        {"role": "system", "content": wellness_system_prompt()},
        {
            "role": "user",
            "content": (
                "Write a gentle bedtime story in 250 words or less. "
                f"Theme: {theme}. Desired mood: {mood}. "
                "Keep it comforting, simple, and suitable for winding down."
            ),
        },
    ]

    try:
        return jsonify({"story": call_llm(messages, temperature=0.8)})
    except LLMConfigurationError:
        return jsonify(
            {"error": "The AI service is not configured. Set the required backend environment variables."}
        ), 503
    except requests.RequestException as exc:
        return provider_error(exc)
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        return provider_error(exc)


if __name__ == "__main__":
    app.run(
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "5000")),
        debug=os.getenv("FLASK_DEBUG", "false").lower() == "true",
    )
