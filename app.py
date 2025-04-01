from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from dotenv import load_dotenv
from openai import OpenAI
import stripe
import os

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "default_secret_key")

# OpenAI Configuration
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Stripe Configuration
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PUBLIC_KEY = os.getenv("STRIPE_PUBLIC_KEY")
YOUR_DOMAIN = os.getenv("STRIPE_DOMAIN", "http://localhost:5000")


@app.route("/")
def index():
    return render_template("index.html", stripe_public_key=STRIPE_PUBLIC_KEY)


@app.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    try:
        data = request.get_json()
        niche = data.get("niche")
        platform = data.get("platform")

        if not niche or not platform:
            return jsonify({"error": "Missing niche or platform"}), 400

        session["niche"] = niche
        session["platform"] = platform

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "unit_amount": 1500,
                        "product_data": {
                            "name": "Premium Content Ideas"
                        }
                    },
                    "quantity": 1
                }
            ],
            mode="payment",
            success_url=YOUR_DOMAIN + "/success",
            cancel_url=YOUR_DOMAIN
        )

        return jsonify({"id": checkout_session.id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/success")
def success():
    niche = session.get("niche", "")
    platform = session.get("platform", "")

    if not niche or not platform:
        return render_template("success.html", ideas=["Something went wrong. Please try again."])

    try:
        prompt = f"Generate 7 viral content ideas for {platform} in the {niche} niche."

        chat_response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )

        content = chat_response.choices[0].message.content
        ideas = [line.strip() for line in content.split("\n") if line.strip()]

        return render_template("success.html", ideas=ideas)
    except Exception as e:
        return render_template("success.html", ideas=[f"Error: {str(e)}"])


if __name__ == "__main__":
    app.run(debug=True)
