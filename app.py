from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_mail import Mail, Message
from openai import OpenAI
import stripe
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "default_secret_key")

# OpenAI setup (v1)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Stripe setup
stripe.api_key = os.getenv("STRIPE_API_KEY")

# Flask-Mail setup
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = os.getenv("EMAIL_USER")
app.config["MAIL_PASSWORD"] = os.getenv("EMAIL_PASS")
mail = Mail(app)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate_free_ideas():
    data = request.get_json()
    niche = data.get("niche")
    platform = data.get("platform")

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "user",
                    "content": f"Generate 2 content ideas for {platform} in the {niche} niche."
                }
            ]
        )
        ideas = response.choices[0].message.content.strip().split("\n")
        return jsonify({"ideas": ideas})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/create-checkout-session", methods=["POST"])
def create_checkout():
    data = request.get_json()
    session["niche"] = data.get("niche")
    session["platform"] = data.get("platform")
    session["email"] = data.get("email")

    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "unit_amount": 1500,
                        "product_data": {
                            "name": "Premium AI Content Ideas"
                        },
                    },
                    "quantity": 1,
                }
            ],
            mode="payment",
            success_url=url_for("success", _external=True),
            cancel_url=url_for("index", _external=True),
        )
        return jsonify({"checkout_url": checkout_session.url})
    except Exception as e:
        return jsonify({"error": str(e)}), 403

@app.route("/success")
def success():
    niche = session.get("niche")
    platform = session.get("platform")
    email = session.get("email")

    ideas = []
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "user",
                    "content": f"Generate 6 content ideas for {platform} in the {niche} niche."
                }
            ]
        )
        ideas = response.choices[0].message.content.strip().split("\n")
        
        # Send email
        msg = Message("Your Premium AI-Generated Content Ideas",
                      sender=app.config['MAIL_USERNAME'],
                      recipients=[email])
        msg.body = "\n".join(ideas)
        mail.send(msg)

    except Exception as e:
        ideas = [f"Failed to load ideas: {e}"]

    return render_template("success.html", ideas=ideas)

if __name__ == "__main__":
    app.run(debug=True)
