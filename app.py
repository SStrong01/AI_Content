from flask import Flask, render_template, request, redirect, session, url_for, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import sqlite3
import stripe
import openai
import os

# Load environment variables from .env
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")

# Stripe API Keys
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PUBLIC_KEY = os.getenv("STRIPE_PUBLIC_KEY")
stripe.api_key = STRIPE_SECRET_KEY

# OpenAI (v1.0+)
from openai import OpenAI
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Optional DB init
def init_db():
    with sqlite3.connect('database.db') as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            email TEXT UNIQUE,
            username TEXT,
            password TEXT,
            plan TEXT DEFAULT 'free')''')
        conn.execute('''CREATE TABLE IF NOT EXISTS ads (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            title TEXT,
            description TEXT,
            platform TEXT)''')

init_db()

# Homepage
@app.route('/')
def index():
    return render_template('index.html', stripe_public_key=STRIPE_PUBLIC_KEY)

# Create Stripe Checkout Session
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
        return jsonify(error="Stripe session creation failed."), 400

# AI-Powered Success Page
@app.route('/success')
def success():
    niche = session.get("niche", "content")
    platform = session.get("platform", "social media")

    prompt = (
        f"Give me 4 unique, creative content ideas for promoting a {niche} brand on {platform}. "
        "Make each idea short, catchy, and effective."
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
        print("OpenAI error:", e)
        return render_template("success.html", ideas=[
            "Error generating ideas. Please try again.",
            str(e)
        ])

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
