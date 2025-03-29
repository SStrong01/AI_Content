from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
import openai
import stripe
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# OpenAI and Stripe config
openai.api_key = os.getenv("OPENAI_API_KEY")
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# Email config
EMAIL_ADDRESS = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASS")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate_idea():
    data = request.get_json()
    niche = data.get("niche")
    platform = data.get("platform")

    if not niche or not platform:
        return jsonify({"error": "Missing required fields"}), 400

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"Generate viral content ideas for {platform} in the {niche} niche."}
            ],
            max_tokens=300
        )

        ideas = response.choices[0].message.content.strip().split("\n")
        session["generated_ideas"] = ideas
        session.modified = True
        return jsonify({"ideas": ideas})
    except Exception as e:
        print("OpenAI error:", e)
        return jsonify({"error": str(e)}), 500

@app.route("/checkout", methods=["POST"])
def checkout():
    try:
        session_data = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": "AI-Generated Content Ideas"
                    },
                    "unit_amount": 1000,
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=url_for("success", _external=True),
            cancel_url=url_for("index", _external=True),
        )
        return jsonify({"checkout_url": session_data.url})
    except Exception as e:
        print("Stripe error:", e)
        return jsonify({"error": str(e)}), 500

@app.route("/success")
def success():
    ideas = session.get("generated_ideas", [])
    if EMAIL_ADDRESS and EMAIL_PASSWORD:
        try:
            msg = MIMEMultipart()
            msg["From"] = EMAIL_ADDRESS
            msg["To"] = EMAIL_ADDRESS
            msg["Subject"] = "Your AI Content Ideas"
            msg.attach(MIMEText("\n".join(ideas), "plain"))

            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
            server.quit()
        except Exception as e:
            print("Email sending error:", e)

    return render_template("success.html", ideas=ideas)

if __name__ == "__main__":
    app.run(debug=True)
