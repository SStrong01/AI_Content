import os
from flask import Flask, render_template, request, redirect, url_for, jsonify
from dotenv import load_dotenv
from openai import OpenAI
import stripe
import smtplib
from email.mime.text import MIMEText

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")

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
    topic = data.get("topic")
    platform = data.get("platform")
    customer_email = data.get("email")

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that generates social media content ideas."},
                {"role": "user", "content": f"Generate 5 content ideas about {topic} for {platform}."}
            ]
        )

        ideas = response.choices[0].message.content

        # Email the ideas
        send_email(customer_email, ideas)

        return jsonify({"ideas": ideas})

    except Exception as e:
        print("OpenAI error:", e)
        return jsonify({"error": str(e)}), 500

@app.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'unit_amount': 500,
                    'product_data': {
                        'name': 'AI-Generated Content Ideas'
                    },
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=url_for('success', _external=True),
            cancel_url=url_for('index', _external=True),
        )
        return redirect(checkout_session.url, code=303)

    except Exception as e:
        return jsonify(error=str(e)), 403

@app.route("/success")
def success():
    return render_template("success.html")

def send_email(to_email, ideas):
    try:
        from_email = os.getenv("EMAIL")
        password = os.getenv("EMAIL_PASSWORD")

        msg = MIMEText(ideas)
        msg['Subject'] = 'Your AI-Generated Content Ideas'
        msg['From'] = from_email
        msg['To'] = to_email

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(from_email, password)
            server.send_message(msg)

        print("Email sent to", to_email)
    except Exception as e:
        print("Error sending email:", e)

if __name__ == "__main__":
    app.run(debug=True)
