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

# ✅ Load CRM Data
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
crm_path = os.path.join(base_dir, "app", "data", "synthetic_crm_modified.csv")

# ✅ Fetch clients whose status is 'DRAFT_FOR_BROKER'


# ✅ Create Broker Review Email Prompt
def create_broker_review_prompt(client_info, client_email_body):
    expiry_date = pd.to_datetime(client_info["Expiry_Date"], dayfirst=True).strftime('%d %B %Y')

    prompt = f"""
        Act as a professional mortgage assistant.

        Generate a broker review email for the client's fixed-rate review.

        ✅ Structure:
        Heading: Fixed Rate Review – {client_info['Customer']} – 90 days out

        Title: {client_info['Customer']}'s fixed rate review is coming up in 90 days, here’s some info:

        Client Overview:
        - Settled: {expiry_date}
        - Next Fixed Expiry: {expiry_date}
        - Settlement amount: ${client_info['Loan_Amount']:,}
        - Terms: {client_info['Rate_Type']} rate with {client_info['Lender']}

        Below is an email draft to the client. Would you like to send it?

        <Send to Client>    <Edit>

        --- Client Email Draft Starts ---

        {client_email_body}

        --- Client Email Draft Ends ---

        """
    return prompt


# ✅ Generate Email Body using OpenAI
def generate_email_body(prompt):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    return response.choices[0].message.content.strip()


# 🚀 Main Email Draft + Approval Flow
def main(client_info):
    client_prompt = create_email_prompt(client_info)
    client_email_body = generate_client_email(client_prompt)

    broker_prompt = create_broker_review_prompt(client_info, client_email_body)
    broker_email_body = generate_email_body(broker_prompt)
    return broker_email_body


if __name__ == "__main__":
    main()
