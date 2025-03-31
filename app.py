from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_mail import Mail, Message
import openai
import os
from dotenv import load_dotenv
import stripe
from email.mime.text import MIMEText
load_dotenv() app = Flask(name)

Config

app.secret_key = os.getenv("FLASK_SECRET_KEY") stripe.api_key = os.getenv("STRIPE_SECRET_KEY") client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route("/") def index(): return render_template("index.html")

@app.route("/generate", methods=["POST"]) def generate(): try: data = request.get_json() niche = data.get("niche") platform = data.get("platform") customer_email = data.get("email")

response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that generates content ideas."},
            {"role": "user", "content": f"Generate 5 content ideas about {niche} for {platform}."}
        ]
    )

    ideas_raw = response.choices[0].message.content.strip()
    ideas = [line.strip("- ") for line in ideas_raw.split("\n") if line.strip()]

    send_email(customer_email, "\n".join(ideas))
    return jsonify({"ideas": ideas})

except Exception as e:
    print("Error:", e)
    return jsonify({"error": "Something went wrong. Please try again later."}), 500

@app.route("/checkout", methods=["POST"]) def create_checkout_session(): try: data = request.get_json() session = stripe.checkout.Session.create( payment_method_types=["card"], line_items=[ { "price_data": { "currency": "usd", "unit_amount": 1500, "product_data": { "name": "AI Generated Content Ideas" } }, "quantity": 1, } ], mode="payment", success_url=url_for("success", _external=True), cancel_url=url_for("index", _external=True) ) return jsonify({"checkout_url": session.url})

except Exception as e:
    return jsonify({"error": str(e)}), 403

@app.route("/success") def success(): ideas = request.args.get("ideas") ideas_list = [] if ideas: import json ideas_list = json.loads(ideas) return render_template("success.html", ideas=ideas_list)

def send_email(to_email, ideas): from_email = os.getenv("EMAIL") password = os.getenv("EMAIL_PASSWORD")

msg = MIMEText(ideas)
msg["Subject"] = "Your AI-Generated Content Ideas"
msg["From"] = from_email
msg["To"] = to_email

try:
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(from_email, password)
        server.sendmail(from_email, to_email, msg.as_string())
except Exception as e:
    print("Error sending email:", e)

if name == "main": app.run(debug=True)
