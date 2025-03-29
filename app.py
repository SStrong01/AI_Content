from flask import Flask, render_template, request, jsonify, session, redirect, url_for import os from openai import OpenAI import stripe import smtplib from email.mime.text import MIMEText from email.mime.multipart import MIMEMultipart from dotenv import load_dotenv

Load environment variables

load_dotenv()

app = Flask(name) app.secret_key = os.getenv("SECRET_KEY")

OpenAI and Stripe configuration

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

@app.route("/") def index(): return render_template("index.html")

@app.route("/generate", methods=["POST"]) def generate_ideas(): data = request.get_json() niche = data.get("niche") platform = data.get("platform")

if not niche or not platform:
    return jsonify({"error": "Missing required fields"}), 400

try:
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that generates viral content ideas."},
            {"role": "user", "content": f"Generate viral content ideas for {platform} in the {niche} niche."}
        ],
        max_tokens=200,
    )

    ideas = response.choices[0].message.content.strip().split("\n")
    session["generated_ideas"] = ideas
    session.modified = True

    return jsonify({"ideas": ideas})

except Exception as e:
    return jsonify({"error": str(e)}), 500

@app.route("/checkout", methods=["POST"]) def checkout(): try: session_data = stripe.checkout.Session.create( payment_method_types=["card"], line_items=[ { "price_data": { "currency": "usd", "product_data": {"name": "AI-Generated Content Ideas"}, "unit_amount": 1000, }, "quantity": 1, } ], mode="payment", success_url=url_for("success", _external=True), cancel_url=url_for("index", _external=True), )

return jsonify({"checkout_url": session_data.url})

except Exception as e:
    return jsonify({"error": str(e)}), 500

@app.route("/success") def success(): ideas = session.get("generated_ideas", []) return render_template("success.html", ideas=ideas)

if name == "main": app.run(debug=True)
