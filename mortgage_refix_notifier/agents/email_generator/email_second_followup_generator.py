import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI


# ✅ Load environment variables
load_dotenv()

# ✅ OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
# ✅ Load CRM Data with status 'AWAITING_BROKER_REVIEW'
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
crm_path = os.path.join(base_dir, "app", "data", "synthetic_crm_modified.csv")


# ✅ Create Email Prompt
def create_email_prompt(client_info):
    expiry_date = pd.to_datetime(client_info["Expiry_Date"], dayfirst=True).strftime('%d %B %Y')
    today = pd.Timestamp(datetime.today())
    expiry = pd.to_datetime(client_info["Expiry_Date"], dayfirst=True)
    weeks_to_expiry = max(((expiry - today).days) // 7, 0)

    prompt = f"""
                Act as a professional mortgage advisor.

                Generate a follow-up email reminder to the customer because the first draft email was already sent but there has been no response yet.

                The tone should be professional, clear, and simple — exactly like this format:

                ---

                Subject: Follow-Up: Fixed-Rate Home Loan Expiry - Action Needed

                Hi {client_info['Customer']},

                Hope you are doing well.

                This is a gentle reminder regarding your lending with {client_info['Lender']}, as you have a facility coming up for refix in the next {weeks_to_expiry} weeks (on {expiry_date}).

                Your {client_info['Lender']} loan details:
                Facility 1: ${client_info['Loan_Amount']:,} — action required.

                We can request rates from {client_info['Lender']} to ensure that you are getting the best deal possible and help you through the refix process.

                Please let us know how you would like to proceed.

                Kind regards,  
                Advisor
                """
    return prompt


# ✅ Generate Email Body
def generate_email_body(prompt):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    return response.choices[0].message.content.strip()


# 🚀 Main Email Draft + Approval Flow
def main(client_info):

    prompt = create_email_prompt(client_info)
    email_body = generate_email_body(prompt)
    return email_body

if __name__ == "__main__":
    main()
