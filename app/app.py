import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from flask import Flask, render_template, request
from predict import score_message

app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    message_text = ""
    if request.method == "POST":
        message_text = request.form.get("message", "")
        if message_text.strip():
            result = score_message(message_text)
    return render_template("index.html", result=result, message_text=message_text)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
