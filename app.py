from flask import Flask, render_template, request, redirect, session, url_for, jsonify
from dotenv import load_dotenv
from openai import OpenAI
import stripe
import openai
import os

load_dotenv()

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = os.getenv("FLASK_SECRET_KEY")

# Stripe setup
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PUBLIC_KEY = os.getenv("STRIPE_PUBLIC_KEY")
stripe.api_key = STRIPE_SECRET_KEY

# OpenAI setup
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route('/')
def index():
    return render_template('index.html', stripe_public_key=STRIPE_PUBLIC_KEY)

@app.route('/buy', methods=['POST'])
def buy():
    data = request.get_json()
    niche = data.get("niche", "")
    platform = data.get("platform", "")
    session["niche"] = niche
    session["platform"] = platform

    try:
        session_data = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {'name': 'Premium Ad Access'},
                    'unit_amount': 1500,
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=url_for('success', _external=True),
            cancel_url=url_for('index', _external=True),
        )
        return jsonify(id=session_data.id)
    except Exception as e:
        print("Stripe error:", e)
        return jsonify(error=str(e)), 400

@app.route('/success')
def success():
    niche = session.get("niche", "content")
    platform = session.get("platform", "social media")

    prompt = (
        f"Give me 4 unique, creative content ideas for promoting a {niche} brand on {platform}. "
        "Make them short, catchy, and effective."
    )

    try:
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a creative content strategist."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.9,
            max_tokens=300,
        )
        output = response.choices[0].message.content
        ideas = [line.strip("- ").strip() for line in output.split("\n") if line.strip()]
        return render_template("success.html", ideas=ideas)
    except Exception as e:
        return render_template("success.html", ideas=[
            "Error generating ideas. Please try again.",
            str(e)
        ])

if __name__ == '__main__':
    app.run(debug=True)