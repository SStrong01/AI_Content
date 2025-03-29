# app.py
import os
from flask import Flask, render_template, request, redirect, url_for, jsonify
from dotenv import load_dotenv
from openai import OpenAI
import stripe
import smtplib
from email.mime.text import MIMEText

load_dotenv()

app = Flask(__name__)

# Stripe setup
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# OpenAI setup
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json()
    niche = data.get("niche")
    platform = data.get("platform")
    customer_email = data.get("email")

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that generates content ideas."},
                {"role": "user", "content": f"Generate 5 content ideas about {niche} for {platform}."}
            ]
        )
        ideas = response.choices[0].message.content.split("\n")
        send_email(customer_email, ideas)
        return jsonify({"ideas": ideas})
    except Exception as e:
        print("OpenAI error:", e)
        return jsonify({"error": str(e)}), 500

@app.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    try:
        data = request.get_json()
        niche = data.get("niche")
        platform = data.get("platform")
        email = data.get("email")

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "unit_amount": 1500,
                    "product_data": {
                        "name": "AI-Generated Content Ideas"
                    },
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=url_for("success", _external=True) + f"?niche={niche}&platform={platform}&email={email}",
            cancel_url=url_for("index", _external=True)
        )
        return jsonify({"checkout_url": session.url})
    except Exception as e:
        return jsonify({"error": str(e)}), 403

@app.route("/success")
def success():
    niche = request.args.get("niche")
    platform = request.args.get("platform")
    email = request.args.get("email")
    return render_template("success.html", niche=niche, platform=platform, email=email)

def send_email(to_email, ideas):
    from_email = os.getenv("EMAIL")
    password = os.getenv("EMAIL_PASSWORD")
    msg = MIMEText("\n".join(ideas))
    msg["Subject"] = "Your AI-Generated Content Ideas"
    msg["From"] = from_email
    msg["To"] = to_email

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(from_email, password)
            server.send_message(msg)
        print("Email sent successfully.")
    except Exception as e:
        print("Error sending email:", e)

if __name__ == "__main__":
    app.run(debug=True)
