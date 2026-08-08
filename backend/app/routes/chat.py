from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import os
import base64
import time
import requests as http_requests
from app.schemas import ChatMessageSchema
from app.utils.validation import validate_request

chat_bp = Blueprint('chat', __name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

SYSTEM_PROMPT = """You are a helpful career assistant for a smart internship platform.
You help students find internships, improve their profiles, and prepare for applications.
You help employers write better job descriptions and find suitable candidates.

Formatting Guidelines:
- Use clear Markdown formatting for readability.
- Use bold text for key concepts or emphasis.
- Use bullet points or numbered lists when giving multi-step advice.
- Use headers (## or ###) to organize response sections for longer answers.
- Keep responses concise, friendly, and professional.

If a file or image is shared, analyze it thoroughly and provide relevant career advice.
If asked about specific internships or matches, encourage the student to check their
recommendations on the platform."""

ALLOWED_EXTENSIONS = {
    'pdf': 'application/pdf',
    'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'doc': 'application/msword',
    'png': 'image/png',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'webp': 'image/webp',
    'gif': 'image/gif'
}

MODELS_TO_TRY = [
    "gemini-3.1-flash-lite",
    "gemini-3.5-flash",
    "gemini-3.1-flash-lite-preview"
]


def get_mime_type(filename: str) -> str:
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    return ALLOWED_EXTENSIONS.get(ext, 'application/octet-stream')


def call_gemini(parts: list) -> dict:
    """
    Calls Gemini API with retry logic across multiple models.
    parts: list of content parts (text and/or inline_data)
    Returns the response dict or raises an exception.
    """
    payload = {
        "contents": [{"parts": parts}],
        "generationConfig": {
            "maxOutputTokens": 800,
            "temperature": 0.7
        }
    }

    last_error = None
    for model in MODELS_TO_TRY:
        for attempt in range(2):
            response = http_requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}",
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=30
            )
            if response.status_code == 200:
                return response.json()
            if response.status_code == 503:
                print(f"Model {model} overloaded attempt {attempt + 1}, retrying...")
                time.sleep(2)
                last_error = response.text
            else:
                print(f"Model {model} error {response.status_code}: {response.text[:150]}")
                last_error = response.text
                break

    raise Exception(f"All models failed. Last error: {last_error}")


@chat_bp.post('/message')
@jwt_required()
def chat():
    user_id = int(get_jwt_identity())

    # Handle multipart form data (when file is attached)
    # or JSON (when no file is attached)
    if request.content_type and 'multipart/form-data' in request.content_type:
        message = request.form.get('message', '').strip()
        history_raw = request.form.get('history', '[]')
        try:
            import json
            conversation_history = json.loads(history_raw)
        except Exception:
            conversation_history = []
        uploaded_file = request.files.get('file')
    else:
        data, error = validate_request(ChatMessageSchema(), request.get_json() or {})
        if error:
            return jsonify(error), 400
        message = data.get('message', '')
        conversation_history = data.get('history', [])
        uploaded_file = None

    if not message and not uploaded_file:
        return jsonify({"error": "Message or file is required"}), 400

    # Build conversation context from history
    conversation_context = ""
    for msg in conversation_history:
        role = "User" if msg["role"] == "user" else "Assistant"
        conversation_context += f"{role}: {msg['content']}\n"

    # Build the full prompt text
    full_prompt = SYSTEM_PROMPT
    if conversation_context:
        full_prompt += f"\n\nConversation so far:\n{conversation_context}"
    if message:
        full_prompt += f"\n\nUser: {message}\nAssistant:"
    elif uploaded_file:
        full_prompt += f"\n\nUser has attached a file. Please analyze it and provide relevant career advice.\nAssistant:"

    # Build Gemini content parts
    parts = [{"text": full_prompt}]

    # Add file if present
    file_info = None
    if uploaded_file and uploaded_file.filename:
        filename = uploaded_file.filename
        mime_type = get_mime_type(filename)

        # Check file is allowed
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        if ext not in ALLOWED_EXTENSIONS:
            return jsonify({"error": f"File type .{ext} is not supported. Use PDF, DOCX, PNG, JPG, or WEBP."}), 400

        # Read and base64 encode the file
        file_bytes = uploaded_file.read()
        if len(file_bytes) > 10 * 1024 * 1024:  # 10MB limit
            return jsonify({"error": "File size must be under 10MB"}), 400

        file_b64 = base64.b64encode(file_bytes).decode('utf-8')

        # Add as inline_data part — Gemini's multimodal format
        parts.append({
            "inline_data": {
                "mime_type": mime_type,
                "data": file_b64
            }
        })

        file_info = {
            "name": filename,
            "type": mime_type,
            "size_kb": round(len(file_bytes) / 1024, 1)
        }

    # Call Gemini
    try:
        result = call_gemini(parts)
        reply = result["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        print(f"Gemini call failed: {e}")
        return jsonify({"error": "Career assistant is temporarily unavailable. Please try again."}), 503

    # Update conversation history
    user_message_content = message or f"[Attached file: {uploaded_file.filename if uploaded_file else 'unknown'}]"
    updated_history = conversation_history + [
        {"role": "user", "content": user_message_content},
        {"role": "assistant", "content": reply}
    ]

    return jsonify({
        "reply": reply,
        "history": updated_history,
        "file_processed": file_info
    }), 200

# import base64
# import os
# import time
# from flask import Blueprint, jsonify, request
# from flask_jwt_extended import get_jwt_identity, jwt_required
# import requests as http_requests

# from app.schemas import ChatMessageSchema
# from app.utils.validation import validate_request

# chat_bp = Blueprint("chat", __name__)

# GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# # Enhanced system prompt with explicit text formatting & structure guidelines
# SYSTEM_PROMPT = """You are a helpful career assistant for a smart internship platform.
# You help students find internships, improve their profiles, and prepare for applications.
# You help employers write better job descriptions and find suitable candidates.

# Formatting Guidelines:
# - Use clear Markdown formatting for readability.
# - Use bold text for key concepts or emphasis.
# - Use bullet points or numbered lists when giving multi-step advice.
# - Use headers (## or ###) to organize response sections for longer answers.
# - Keep responses concise, friendly, and professional.

# If a file or image is shared, analyze it thoroughly and provide relevant career advice.
# If asked about specific internships or matches, encourage the student to check their recommendations on the platform."""

# ALLOWED_EXTENSIONS = {
#     "pdf": "application/pdf",
#     "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
#     "doc": "application/msword",
#     "png": "image/png",
#     "jpg": "image/jpeg",
#     "jpeg": "image/jpeg",
#     "webp": "image/webp",
#     "gif": "image/gif",
# }

# MODELS_TO_TRY = [
#     "gemini-2.5-flash",
#     "gemini-2.5-flash-lite",
# ]


# def get_mime_type(filename: str) -> str:
#     ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
#     return ALLOWED_EXTENSIONS.get(ext, "application/octet-stream")


# def call_gemini(contents: list) -> dict:
#     """Calls Gemini API with system instructions and retry logic across multiple models."""
#     payload = {
#         # Native system instruction payload
#         "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
#         "contents": contents,
#         "generationConfig": {"maxOutputTokens": 800, "temperature": 0.7},
#     }

#     last_error = None
#     for model in MODELS_TO_TRY:
#         for attempt in range(2):
#             response = http_requests.post(
#                 f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}",
#                 headers={"Content-Type": "application/json"},
#                 json=payload,
#                 timeout=30,
#             )
#             if response.status_code == 200:
#                 return response.json()
#             if response.status_code == 503:
#                 print(
#                     f"Model {model} overloaded attempt {attempt + 1}, retrying..."
#                 )
#                 time.sleep(2)
#                 last_error = response.text
#             else:
#                 print(
#                     f"Model {model} error {response.status_code}: {response.text[:150]}"
#                 )
#                 last_error = response.text
#                 break

#     raise Exception(f"All models failed. Last error: {last_error}")


# @chat_bp.post("/message")
# @jwt_required()
# def chat():
#     user_id = int(get_jwt_identity())

#     if request.content_type and "multipart/form-data" in request.content_type:
#         message = request.form.get("message", "").strip()
#         history_raw = request.form.get("history", "[]")
#         try:
#             import json

#             conversation_history = json.loads(history_raw)
#         except Exception:
#             conversation_history = []
#         uploaded_file = request.files.get("file")
#     else:
#         data, error = validate_request(
#             ChatMessageSchema(), request.get_json() or {}
#         )
#         if error:
#             return jsonify(error), 400
#         message = data.get("message", "")
#         conversation_history = data.get("history", [])
#         uploaded_file = None

#     if not message and not uploaded_file:
#         return jsonify({"error": "Message or file is required"}), 400

#     # Build multi-turn payload using Gemini's standard roles ("user" / "model")
#     contents = []
#     for msg in conversation_history:
#         role = "model" if msg["role"] == "assistant" else "user"
#         contents.append({"role": role, "parts": [{"text": msg["content"]}]})

#     # Prepare latest turn user message parts
#     latest_user_parts = []
#     if message:
#         latest_user_parts.append({"text": message})

#     file_info = None
#     if uploaded_file and uploaded_file.filename:
#         filename = uploaded_file.filename
#         mime_type = get_mime_type(filename)

#         ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
#         if ext not in ALLOWED_EXTENSIONS:
#             return jsonify(
#                 {
#                     "error": f"File type .{ext} is not supported. Use PDF, DOCX, PNG, JPG, or WEBP."
#                 }
#             ), 400

#         file_bytes = uploaded_file.read()
#         if len(file_bytes) > 10 * 1024 * 1024:
#             return jsonify({"error": "File size must be under 10MB"}), 400

#         file_b64 = base64.b64encode(file_bytes).decode("utf-8")

#         latest_user_parts.append(
#             {"inline_data": {"mime_type": mime_type, "data": file_b64}}
#         )

#         file_info = {
#             "name": filename,
#             "type": mime_type,
#             "size_kb": round(len(file_bytes) / 1024, 1),
#         }

#     # Append latest user turn
#     contents.append({"role": "user", "parts": latest_user_parts})

#     try:
#         result = call_gemini(contents)
#         reply = result["candidates"][0]["content"]["parts"][0]["text"]
#     except Exception as e:
#         print(f"Gemini call failed: {e}")
#         return jsonify(
#             {
#                 "error": "Career assistant is temporarily unavailable. Please try again."
#             }
#         ), 503

#     user_message_content = (
#         message
#         or f"[Attached file: {uploaded_file.filename if uploaded_file else 'unknown'}]"
#     )
#     updated_history = conversation_history + [
#         {"role": "user", "content": user_message_content},
#         {"role": "assistant", "content": reply},
#     ]

#     return (
#         jsonify(
#             {
#                 "reply": reply,
#                 "history": updated_history,
#                 "file_processed": file_info,
#             }
#         ),
#         200,
#     )