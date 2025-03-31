from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_mail import Mail, Message
import openai
import os
import stripe
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "default_secret_key")

# Configure OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# Configure Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# Configure Flask-Mail
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
def generate():
    data = request.get_json()
    niche = data.get("niche")
    platform = data.get("platform")
    email = data.get("email")

    if not niche or not platform or not email:
        return jsonify({"error": "Missing fields"}), 400

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{
                "role": "user",
                "content": f"Generate 2 viral content ideas for {platform} in the {niche} niche."
            }]
        )
        ideas = response.choices[0].message["content"].strip().split("\n")
        session["generated_ideas"] = ideas

        # Send email
        msg = Message("Your Free AI-Generated Ideas", sender=app.config["MAIL_USERNAME"], recipients=[email])
        msg.body = "\n".join(ideas)
        mail.send(msg)

        return jsonify({"message": "Email sent!", "ideas": ideas})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "unit_amount": 1500,
                    "product_data": {
                        "name": "Premium AI-Generated Ideas",
                    },
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=url_for("success", _external=True),
            cancel_url=url_for("index", _external=True),
        )
        return jsonify({"checkout_url": checkout_session.url})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/success")
def success():
    # Fetch new ideas for premium user
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{
                "role": "user",
                "content": f"Generate 6 viral premium content ideas for a customer."
            }]
        )
        ideas = response.choices[0].message["content"].strip().split("\n")
        session["generated_ideas"] = ideas
        return render_template("success.html", ideas=ideas)
    except Exception as e:
        return render_template("success.html", ideas=["Failed to load ideas: " + str(e)])

if __name__ == "__main__":
    app.run(debug=True)
