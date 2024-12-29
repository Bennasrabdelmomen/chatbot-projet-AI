import requests
import json
from threading import Event
from app.utils import enforce_html_structure

stop_event = Event()

# Instruction for the bot to use the CV content
INSTRUCTION = """
You are an AI assistant specializing in analyzing and answering questions based on CVs.
Your role is to provide detailed, accurate, and concise answers based on the provided CV.
If the question is unclear or the answer is not found in the CV, ask for clarification or explain that the information is unavailable.
Always ensure your tone is professional and helpful.
"""


def prepare_cv_context(cv_text):
    """
    Prepare the CV content as context for the assistant.
    """
    return {"role": "system", "content": f"The following is the CV content: {cv_text}"}


def qwen_generator_stream(history, model_name, server, cv_text=None):
    if not history or not isinstance(history, list):
        yield f"data: <div style='color:red;'>Invalid conversation history.</div>\n\n"
        return

    if not model_name or not server:
        yield f"data: <div style='color:red;'>Configuration error: Missing model name or server.</div>\n\n"
        return

    try:
        payload = {"model": model_name, "messages": history}
        response = requests.post(f"{server}/api/chat", json=payload, stream=True)
        response.raise_for_status()

        buffer = ""
        for line in response.iter_lines():
            if stop_event.is_set():
                break

            if line:
                try:
                    data = json.loads(line.decode("utf-8"))
                    if "message" in data and "content" in data["message"]:
                        content = data["message"]["content"]
                        buffer += content
                        if content.endswith("\n") or len(buffer.strip()) > 100:
                            yield f"data: {enforce_html_structure(buffer.strip())}\n\n"
                            buffer = ""
                except json.JSONDecodeError:
                    yield f"data: <div style='color:red;'>Error decoding response.</div>\n\n"
    except requests.exceptions.RequestException as e:
        yield f"data: <div style='color:red;'>Error communicating with server: {e}</div>\n\n"
