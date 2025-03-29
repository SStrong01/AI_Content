import os
from flask import Flask, render_template, request, redirect, url_for, jsonify
from dotenv import load_dotenv
import openai
import stripe
import smtplib
from email.message import EmailMessage

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")

# OpenAI setup
openai.api_key = os.getenv("OPENAI_API_KEY")

# Stripe setup
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
YOUR_DOMAIN = "https://ai-content-dqzc.onrender.com"

# Home page
@app.route('/')
def index():
    return render_template('index.html')

# Create Checkout Session
@app.route('/checkout', methods=['POST'])
def checkout():
    data = request.get_json()
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'usd',
                'unit_amount': 500,
                'product_data': {
                    'name': f"AI Content for {data['niche']} on {data['platform']}",
                },
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url=url_for('success', _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
        cancel_url=YOUR_DOMAIN,
    )
    return jsonify({'checkout_url': session.url})

# Success page
@app.route('/success')
def success():
    return render_template('success.html', ideas=[])

# Generate and Email AI content
@app.route('/generate', methods=['POST'])
def generate():
    niche = request.form['niche']
    platform = request.form['platform']
    email = request.form['email']

    prompt = f"Generate 5 unique {platform} content ideas for the {niche} niche."

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a creative assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8
        )
        ideas = response['choices'][0]['message']['content']

        # Send ideas via email
        send_email(email, ideas)

        return render_template("success.html", ideas=ideas.split("\n"))

    except Exception as e:
        print("ERROR CALLING OPENAI:", e)
        return "Error generating content, please try again."

# Email function
def send_email(to_email, content):
    msg = EmailMessage()
    msg['Subject'] = "Your AI-Generated Content Ideas"
    msg['From'] = os.getenv("EMAIL_USER")
    msg['To'] = to_email
    msg.set_content(f"Here are your AI-generated ideas:\n\n{content}")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(os.getenv("EMAIL_USER"), os.getenv("EMAIL_PASS"))
        smtp.send_message(msg)

if __name__ == '__main__':
    app.run(debug=True)
