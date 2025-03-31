from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_mail import Mail, Message
from dotenv import load_dotenv
import os
import openai
import stripe

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")

# Email config
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv("EMAIL_USER")
app.config['MAIL_PASSWORD'] = os.getenv("EMAIL_PASS")
mail = Mail(app)

# Stripe config
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# OpenAI config (v1.x)
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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
        prompt = f"Generate 2 viral content ideas for {platform} in the {niche} niche."

        chat = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )

        ideas = chat.choices[0].message.content.strip().split("\n")
        session["ideas"] = ideas

        # Email the ideas
        msg = Message("Your Free AI-Generated Ideas", sender=app.config['MAIL_USERNAME'], recipients=[email])
        msg.body = "\n".join(ideas)
        mail.send(msg)

        return jsonify({"message": "Success", "ideas": ideas})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/buy", methods=["POST"])
def buy():
    data = request.get_json()
    niche = data.get("niche")
    platform = data.get("platform")
    email = data.get("email")

    try:
        session_data = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": "Premium AI Content Ideas",
                    },
                    "unit_amount": 1500,
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=url_for("success", _external=True) + "?email=" + email + "&niche=" + niche + "&platform=" + platform,
            cancel_url=url_for("index", _external=True),
        )
        return jsonify({"checkout_url": session_data.url})
    except Exception as e:
        return jsonify({"error": str(e)}), 403

@app.route("/success")
def success():
    email = request.args.get("email")
    niche = request.args.get("niche")
    platform = request.args.get("platform")

    try:
        prompt = f"Generate 6 premium viral content ideas for {platform} in the {niche} niche."

        chat = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )

        ideas = chat.choices[0].message.content.strip().split("\n")
        session["ideas"] = ideas

        # Email premium ideas
        msg = Message("Your Premium AI-Generated Ideas", sender=app.config['MAIL_USERNAME'], recipients=[email])
        msg.body = "\n".join(ideas)
        mail.send(msg)

        return render_template("success.html", ideas=ideas)
    except Exception as e:
        return render_template("success.html", ideas=[f"Failed to load ideas: {str(e)}"])

if __name__ == "__main__":
    app.run(debug=True)
