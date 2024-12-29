from flask import Flask, render_template, jsonify, Response, request, stream_with_context
import fitz
from app.stream import qwen_generator_stream, stop_event
from app.utils import enforce_html_structure
import logging

# Flask app initialization
app = Flask(__name__)

# Configuration
OLLAMA_SERVER = "http://localhost:11434"
MODEL_NAME = "qwen2.5:7b-instruct"

# Global CV content (consider using session or database for production)
cv_text = ""

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Instruction for the bot
INSTRUCTION = """
You are an AI assistant specializing in analyzing and answering questions based on CVs.
Your role is to provide detailed, accurate, and concise answers based on the provided CV.
If the question is unclear or the answer is not found in the CV, ask for clarification or explain that the information is unavailable.
Always ensure your tone is professional and helpful.
"""



def extract_text_from_pdf(file):
    """
    Extract text from an uploaded PDF file using PyMuPDF.
    :param file: A file-like object (e.g., from Flask's request.files).
    :return: Extracted text as a string.
    """
    try:
        pdf_document = fitz.open(stream=file.read(), filetype="pdf")
        text = ""
        for page in pdf_document:
            text += page.get_text()
        return text.strip()
    except Exception as e:
        logging.error(f"Error extracting text from PDF: {e}")
        return None


from flask import session

# Ensure secret key is set for session handling
app.secret_key = "your_secret_key"

@app.route("/upload_cv", methods=["POST"])
def upload_cv():
    if "file" not in request.files:
        return jsonify({"success": False, "message": "No file provided."}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"success": False, "message": "No file selected."}), 400

    if file and file.filename.endswith(".pdf"):
        cv_text = extract_text_from_pdf(file)
        if cv_text:
            logging.info(f"Extracted CV Text: {cv_text[:500]}...")  # Log first 500 characters
            session["cv_text"] = cv_text  # Store in session
            return jsonify({"success": True, "message": "CV uploaded successfully."}), 200
        else:
            logging.error("Failed to extract text from the CV.")
            return jsonify({"success": False, "message": "Failed to extract text from the CV."}), 500

    return jsonify({"success": False, "message": "Invalid file type. Only PDF files are supported."}), 400


@app.route("/conversation", methods=["POST"])
def conversation():
    """
    Handle user queries based on conversation history and CV content.
    """
    global cv_text
    stop_event.clear()
    data = request.get_json()
    history = data.get("history", [])

    if not history:
        return jsonify({"success": False, "message": "History cannot be empty."}), 400

    try:
        return Response(
            stream_with_context(qwen_generator_stream(history, MODEL_NAME, OLLAMA_SERVER, cv_text=cv_text)),
            content_type="text/event-stream"
        )
    except Exception as e:
        logging.error(f"Error in conversation: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/stop", methods=["POST"])
def stop():
    """
    Stop the streaming of responses.
    """
    stop_event.set()
    return jsonify({"success": True, "message": "Streaming stopped."})


@app.route("/download", methods=["POST"])
def download():
    """
    Allow downloading the conversation log.
    """
    data = request.get_json()
    conversation = data.get("conversation", "")

    if not conversation:
        return jsonify({"success": False, "message": "No conversation to download."}), 400

    return Response(
        conversation,
        mimetype="text/plain",
        headers={"Content-Disposition": "attachment;filename=conversation.txt"}
    )


@app.route("/", methods=["GET"])
def index():
    """
    Render the main chatbot interface.
    """
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
