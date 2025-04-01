from flask import Flask, render_template, request, session, jsonify
import os
from openai import OpenAI
import stripe
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "default_secret")

# OpenAI client setup (v1.x)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Stripe setup
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    data = request.get_json()
    niche = data.get("niche")
    platform = data.get("platform")
    email = data.get("email")

    try:
        # Generate 7 ideas with OpenAI
        prompt = f"Generate 7 viral content ideas for {platform} in the {niche} niche."
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{ "role": "user", "content": prompt }]
        )
        ideas = response.choices[0].message.content.strip().split("\n")
        session["premium_ideas"] = ideas

        # Create Stripe checkout session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "unit_amount": 1500, # $15
                    "product_data": {
                        "name": "Premium AI-Generated Ideas",
                    },
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=request.host_url + "success",
            cancel_url=request.host_url,
        )
        return jsonify({"checkout_url": checkout_session.url})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/success")
def success():
    ideas = session.get("premium_ideas", [])
    return render_template("success.html", ideas=ideas)

if __name__ == "__main__":
    app.run(debug=True)
