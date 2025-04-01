from flask import Flask, render_template, request, jsonify, session
from dotenv import load_dotenv
import os
from openai import OpenAI

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "your_secret_key")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json()
    niche = data.get("niche")
    platform = data.get("platform")

    if not niche or not platform:
        return jsonify({"error": "Missing input"}), 400

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "user",
                    "content": f"Generate 2 viral content ideas for {platform} in the {niche} niche."
                }
            ]
        )

        ideas = response.choices[0].message.content.strip().split("\n")
        session["ideas"] = ideas
        return jsonify({"ideas": ideas})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/success")
def success():
    ideas = session.get("ideas", [])
    return render_template("success.html", ideas=ideas)

if __name__ == "__main__":
    app.run(debug=True)
