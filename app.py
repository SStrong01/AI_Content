from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import openai
import os
from dotenv import load_dotenv
import stripe
from flask_mail import Mail, Message

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "default_key")

# OpenAI (v1.x compatible)
openai.api_key = os.getenv("OPENAI_API_KEY")

# Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# Flask-Mail
app.config.update(
    MAIL_SERVER="smtp.gmail.com",
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME=os.getenv("EMAIL_USER"),
    MAIL_PASSWORD=os.getenv("EMAIL_PASS"),
)
mail = Mail(app)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json()
    niche = data.get("niche")
    platform = data.get("platform")
    email = data.get("email")

    if not niche or not platform or not email:
        return jsonify({"error": "Missing fields"}), 400

    try:
        chat_response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": f"Generate 6 viral content ideas for {platform} in the {niche} niche."}
            ]
        )
        ideas_raw = chat_response.choices[0].message.content
        ideas = [line.strip() for line in ideas_raw.split("\n") if line.strip()]
        session["ideas"] = ideas

        # Email the ideas
        msg = Message("Your Premium AI Content Ideas", sender=app.config["MAIL_USERNAME"], recipients=[email])
        msg.body = "\n".join(ideas)
        mail.send(msg)

        return jsonify({"success": True, "ideas": ideas})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/create-checkout-session", methods=["POST"])
def create_checkout():
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "unit_amount": 1500,
                    "product_data": {"name": "Premium AI Content Ideas"},
                },
                "quantity": 1
            }],
            mode="payment",
            success_url=url_for("success", _external=True),
            cancel_url=url_for("index", _external=True),
        )
        return jsonify({"checkout_url": checkout_session.url})
    except Exception as e:
        return jsonify({"error": str(e)}), 403

@app.route("/success")
def success():
    ideas = session.get("ideas", [])
    return render_template("success.html", ideas=ideas)

if __name__ == "__main__":
    app.run(debug=True)
