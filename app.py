import os
from flask import Flask, request, session, redirect, url_for, render_template, jsonify
from flask_mail import Mail, Message
from dotenv import load_dotenv
import openai
import stripe

# Load environment variables
load_dotenv()

# Flask setup
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")

# OpenAI setup
openai.api_key = os.getenv("OPENAI_API_KEY")

# Stripe setup
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# Flask-Mail setup
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')

mail = Mail(app)

# Home page
@app.route("/")
def index():
    return render_template("index.html")

# Handle idea generation and redirect to checkout
@app.route("/checkout", methods=["POST"])
def checkout():
    data = request.get_json()
    niche = data.get("niche")
    platform = data.get("platform")
    email = data.get("email")

    if not all([niche, platform, email]):
        return jsonify({"error": "Missing data"}), 400

    # Generate AI ideas
    try:
        prompt = f"Generate 5 creative content ideas for {niche} on {platform}."
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        ideas_text = response.choices[0].message.content.strip().split("\n")
        ideas = [idea.strip("- ").strip() for idea in ideas_text if idea.strip()]
        session["ideas"] = ideas
        session["email"] = email
    except Exception as e:
        print("OpenAI error:", e)
        return jsonify({"error": "Failed to generate ideas"}), 500

    # Create Stripe checkout session
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {"name": "AI Content Ideas"},
                    "unit_amount": 500, # $5.00
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=url_for("success", _external=True),
            cancel_url=url_for("index", _external=True),
        )
        return jsonify({"checkout_url": checkout_session.url})
    except Exception as e:
        print("Stripe error:", e)
        return jsonify({"error": "Payment setup failed"}), 500

# Success route - send email
@app.route("/success")
def success():
    ideas = session.get("ideas")
    email = session.get("email")

    if not ideas:
        return redirect(url_for("index"))

    # Send email
    if email:
        try:
            msg = Message("Your AI Content Ideas", recipients=[email])
            msg.body = "\n\n".join(ideas)
            mail.send(msg)
        except Exception as e:
            print("Email sending failed:", e)

    # Clear session
    session.pop("ideas", None)
    session.pop("email", None)

    return render_template("success.html", ideas=ideas)

# Run app locally
if __name__ == "__main__":
    app.run(debug=True)
