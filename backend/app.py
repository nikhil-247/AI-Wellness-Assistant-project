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


def call_llm(messages: list[dict[str, str]], temperature: float = 0.7) -> str:
    if not OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is not configured")

    if not OPENROUTER_MODEL:
        raise RuntimeError("OPENROUTER_MODEL is not configured")

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
        timeout=60,
    )
    response.raise_for_status()

    data: dict[str, Any] = response.json()
    return data["choices"][0]["message"]["content"].strip()


def wellness_system_prompt() -> str:
    return (
        "You are Self Love, a calm and supportive AI wellness companion. "
        "Provide empathetic, practical, non-clinical responses. "
        "Do not diagnose conditions, prescribe medication, or present yourself as a therapist. "
        "For emergencies or immediate danger, encourage the user to contact local emergency "
        "services or a qualified professional. Keep responses concise and conversational."
    )


@app.get("/api/health")
def health():
    return jsonify({"status": "ok", "service": "self-love-backend"})


@app.post("/api/chat")
def chat():
    payload = request.get_json(silent=True) or {}
    message = str(payload.get("message", "")).strip()
    mood = str(payload.get("mood", "neutral")).strip()
    history = payload.get("history", [])

    if not message:
        return jsonify({"error": "message is required"}), 400

    safe_history = [
        item
        for item in history
        if isinstance(item, dict)
        and item.get("role") in {"user", "assistant"}
        and isinstance(item.get("content"), str)
    ][-10:]

    messages = [
        {"role": "system", "content": wellness_system_prompt()},
        {
            "role": "system",
            "content": f"The user's current mood is: {mood}. Adapt your tone accordingly.",
        },
        *[
            {"role": item["role"], "content": item["content"]}
            for item in safe_history
        ],
        {"role": "user", "content": message},
    ]

    try:
        reply = call_llm(messages)
        return jsonify({"reply": reply})
    except requests.HTTPError as exc:
        return jsonify({"error": f"LLM provider error: {exc}"}), 502
    except (RuntimeError, KeyError, IndexError, TypeError, ValueError) as exc:
        return jsonify({"error": str(exc)}), 500


@app.post("/api/story")
def story():
    payload = request.get_json(silent=True) or {}
    theme = str(payload.get("theme", "a peaceful night")).strip()
    mood = str(payload.get("mood", "calm")).strip()

    messages = [
        {"role": "system", "content": wellness_system_prompt()},
        {
            "role": "user",
            "content": (
                f"Write a gentle bedtime story in 250 words or less. "
                f"Theme: {theme}. Desired mood: {mood}. "
                "Keep it comforting, simple, and suitable for winding down."
            ),
        },
    ]

    try:
        reply = call_llm(messages, temperature=0.8)
        return jsonify({"story": reply})
    except requests.HTTPError as exc:
        return jsonify({"error": f"LLM provider error: {exc}"}), 502
    except (RuntimeError, KeyError, IndexError, TypeError, ValueError) as exc:
        return jsonify({"error": str(exc)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
