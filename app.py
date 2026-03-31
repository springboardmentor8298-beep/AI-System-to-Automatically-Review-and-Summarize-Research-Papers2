from flask import Flask, render_template, request, jsonify
from milestone1 import fetch_papers
from milestone2 import process_paper
import os

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")


# FETCH PAPERS
@app.route("/fetch", methods=["POST"])
def fetch():
    topic = request.json["topic"]
    max_papers = int(request.json["max_papers"])

    papers = fetch_papers(topic, max_papers)
    return jsonify(papers)


# ANALYZE PAPER
@app.route("/process", methods=["POST"])
def process():
    pdf = request.json["pdf"]

    pdf_path = os.path.join("papers", pdf)

    if not os.path.exists(pdf_path):
        return jsonify({"error": f"PDF not found: {pdf_path}"})

    result = process_paper(pdf_path)
    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True)