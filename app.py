"""
Flask Web Server for the Skin Detection Agent
Provides REST API endpoints and serves the web UI.
"""

import os
import uuid
import threading
import requests
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
from detector import SkinDetectionAgent
from config import UPLOAD_FOLDER, MAX_CONTENT_LENGTH, ALLOWED_EXTENSIONS, EXTERNAL_WEBHOOK_URL

# Initialize Flask app
app = Flask(__name__, static_folder="static", static_url_path="")
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH
CORS(app)

# Create upload folder
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize the AI Agent
agent = SkinDetectionAgent()


def allowed_file(filename):
    """Check if the file extension is allowed."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def _fire_webhook(payload):
    """Background task to send webhook."""
    try:
        requests.post(EXTERNAL_WEBHOOK_URL, json=payload, timeout=5)
    except Exception as e:
        print(f"[Webhook Error] {e}")

def trigger_webhook(results):
    """Starts a thread to post results to the external webhook."""
    if EXTERNAL_WEBHOOK_URL and results and results.get("success"):
        thread = threading.Thread(target=_fire_webhook, args=(results,))
        thread.start()


@app.route("/")
def index():
    """Serve the main web UI."""
    return send_from_directory("static", "index.html")


@app.route("/api/detect", methods=["POST"])
def detect():
    """
    Run skin detection on an uploaded image.
    Accepts: multipart/form-data with 'image' file field
    Returns: JSON detection results
    """
    if "image" not in request.files:
        return jsonify({"error": "No image file provided", "success": False}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"error": "No file selected", "success": False}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Invalid file type. Use PNG, JPG, JPEG, or WEBP", "success": False}), 400

    # Save uploaded file
    filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    # Extract user profile if available
    age = request.form.get("age")
    skin_type = request.form.get("skin_type")

    try:
        # Run detection
        results = agent.detect_from_file(filepath, age=age, skin_type=skin_type)
        trigger_webhook(results)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e), "success": False}), 500
    finally:
        # Clean up uploaded file
        if os.path.exists(filepath):
            os.remove(filepath)


@app.route("/api/detect/base64", methods=["POST"])
def detect_base64():
    """
    Run skin detection on a base64 encoded image.
    Accepts: JSON with 'image' base64 string
    Returns: JSON detection results
    """
    data = request.get_json()
    if not data or "image" not in data:
        return jsonify({"error": "No image data provided", "success": False}), 400

    image_b64 = data["image"]
    # Strip data URL prefix if present
    if "," in image_b64:
        image_b64 = image_b64.split(",", 1)[1]

    try:
        age = data.get("age")
        skin_type = data.get("skin_type")
        results = agent.detect_from_base64(image_b64, age=age, skin_type=skin_type)
        trigger_webhook(results)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e), "success": False}), 500


@app.route("/api/detect/url", methods=["POST"])
def detect_url():
    """
    Run skin detection on an image URL.
    Accepts: JSON with 'url' string
    Returns: JSON detection results
    """
    data = request.get_json()
    if not data or "url" not in data:
        return jsonify({"error": "No URL provided", "success": False}), 400

    try:
        age = data.get("age")
        skin_type = data.get("skin_type")
        results = agent.detect_from_url(data["url"], age=age, skin_type=skin_type)
        trigger_webhook(results)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e), "success": False}), 500


@app.route("/api/history", methods=["GET"])
def history():
    """Return detection history."""
    return jsonify({"history": agent.get_history()})


@app.route("/api/conditions", methods=["GET"])
def conditions():
    """Return all detectable skin conditions."""
    from config import SKIN_CONDITIONS
    return jsonify({"conditions": SKIN_CONDITIONS})


if __name__ == "__main__":
    print("=" * 60)
    print("  🧬 Skin Problem Detection Agent")
    print("  Powered by Roboflow Multi-Class CV Model")
    print("=" * 60)
    print(f"  Open: http://localhost:8080")
    print("=" * 60)
    app.run(host="0.0.0.0", port=8080, debug=True)
