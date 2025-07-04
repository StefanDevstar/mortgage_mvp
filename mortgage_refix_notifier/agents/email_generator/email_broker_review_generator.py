import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI

from agents.email_generator.email_first_draft_generator import create_email_prompt, generate_email_body as generate_client_email
from app.gmail_client import send_email

# ✅ Load environment variables
load_dotenv()

# ✅ OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ✅ Create Broker Review Email Prompt (HTML formatted)
def create_broker_review_prompt(client_info, client_email_body):
    expiry_date = pd.to_datetime(client_info["Expiry_Date"], dayfirst=True).strftime('%d %B %Y')

    broker_email = f"""
    <h2>Fixed Rate Review – {client_info['Customer']} – 90 days out</h2>
    <p><strong>Title:</strong> {client_info['Customer']}'s fixed rate review is coming up in 90 days. Here’s some info:</p>
    <p><strong>Client Overview:</strong></p>
    <ul>
        <li>Settled: {expiry_date}</li>
        <li>Next Fixed Expiry: {expiry_date}</li>
        <li>Settlement amount: ${client_info['Loan_Amount']:,}</li>
        <li>Terms: {client_info['Rate_Type']} rate with {client_info['Lender']}</li>
    </ul>
    <p>Below is an email draft to the client. Would you like to send it?</p>

    <hr>
    <h3>📩 Client Email Draft</h3>
    <div style="padding:10px;background-color:#f9f9f9;border-left:4px solid #007bff;margin-bottom:10px;">
        {client_email_body.replace('\n', '<br>')}
    </div>
    <hr>
    """
    return broker_email

# 🚀 Main Email Draft + Approval Flow
def main(client_info):
    # Generate client email content (plain text)
    client_prompt = create_email_prompt(client_info)
    client_email_body = generate_client_email(client_prompt)
    client_subject = "Upcoming Fixed-Rate Home Loan Expiry - Action Required"

    # Generate broker-facing email (HTML)
    broker_email_body = create_broker_review_prompt(client_info, client_email_body)
    broker_subject = f"Refix Review - {client_info['Customer']}"

    return {
        "broker_subject": broker_subject,
        "broker_body": broker_email_body,
        "client_subject": client_subject,
        "client_body": client_email_body
    }

if __name__ == "__main__":
    print("⚠️ Run this only via tasks.py for full flow.")
