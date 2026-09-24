"""
JSON API for the AI-Generated Phishing Detector.
This is what the Flutter mobile app will call over the internet.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from flask import Flask, request, jsonify
from flask_cors import CORS
from predict import score_message

app = Flask(__name__)
CORS(app)  # allows the mobile app to call this from anywhere


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/api/analyze", methods=["POST"])
def analyze():
    data = request.get_json(silent=True) or {}
    message = data.get("message", "").strip()

    if not message:
        return jsonify({"error": "No message provided"}), 400

    result = score_message(message)
    return jsonify(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
