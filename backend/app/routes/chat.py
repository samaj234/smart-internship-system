from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import os
import requests as http_requests
from app.schemas import ChatMessageSchema
from app.utils.validation import validate_request

chat_bp = Blueprint('chat', __name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

SYSTEM_PROMPT = """You are a helpful career assistant for a smart internship platform.
You help students find internships, improve their profiles, and prepare for applications.
You help employers write better job descriptions and find suitable candidates.
Keep responses concise, friendly and professional.
If asked about specific internships or matches, encourage the student to check their
recommendations on the platform."""


@chat_bp.post('/message')
@jwt_required()
def chat():
    user_id = int(get_jwt_identity())

    data, error = validate_request(ChatMessageSchema(), request.get_json() or {})
    if error:
        return jsonify(error), 400

    conversation_history = data.get('history', [])

    conversation_context = ""
    for msg in conversation_history:
        role = "User" if msg["role"] == "user" else "Assistant"
        conversation_context += f"{role}: {msg['content']}\n"

    full_prompt = SYSTEM_PROMPT
    if conversation_context:
        full_prompt += f"\n\nConversation so far:\n{conversation_context}"
    full_prompt += f"\n\nUser: {data['message']}\nAssistant:"

    response = http_requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}",
        headers={"Content-Type": "application/json"},
        json={
            "contents": [
                {
                    "parts": [{"text": full_prompt}]
                }
            ],
            "generationConfig": {
                "maxOutputTokens": 500,
                "temperature": 0.7
            }
        }
    )

    if response.status_code != 200:
        print("Gemini error:", response.text)
        return jsonify({"error": "Chatbot service unavailable"}), 503

    reply = response.json()["candidates"][0]["content"]["parts"][0]["text"]

    updated_history = conversation_history + [
        {"role": "user", "content": data['message']},
        {"role": "assistant", "content": reply}
    ]

    return jsonify({
        "reply": reply,
        "history": updated_history
    }), 200