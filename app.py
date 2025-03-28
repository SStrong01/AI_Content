import os
import uuid
from flask import Flask, request, session, redirect, url_for, render_template, jsonify
from dotenv import load_dotenv
import openai
import stripe

# Load .env secrets
load_dotenv()

# API Keys
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# Flask app setup
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/checkout", methods=["POST"])
def checkout():
    data = request.get_json()
    niche = data.get("niche")
    platform = data.get("platform")

    # Generate AI content ideas
    try:
        prompt = f"Give me 5 creative content ideas for {platform} in the {niche} niche."
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        ideas = response.choices[0].message.content.strip().split("\n")

        # Save ideas to temp file
        session_id = str(uuid.uuid4())
        session["session_id"] = session_id

        with open(f"temp_{session_id}.txt", "w", encoding="utf-8") as f:
            for idea in ideas:
                f.write(idea + "\n")

        # Create Stripe Checkout
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": { "name": "AI Content Ideas" },
                    "unit_amount": 500 # $5.00
                },
                "quantity": 1
            }],
            mode="payment",
            success_url=url_for("success", _external=True),
            cancel_url=url_for("index", _external=True)
        )

        return jsonify({ "checkout_url": checkout_session.url })

    except Exception as e:
        print("Checkout Error:", e)
        return jsonify({ "error": str(e) }), 500

@app.route("/success")
def success():
    session_id = session.get("session_id")
    ideas = []

    if session_id:
        try:
            with open(f"temp_{session_id}.txt", "r", encoding="utf-8") as f:
                ideas = f.read().splitlines()
        except Exception as e:
            print("File Read Error:", e)

    return render_template("success.html", ideas=ideas)

if __name__ == "__main__":
    app.run(debug=True)
