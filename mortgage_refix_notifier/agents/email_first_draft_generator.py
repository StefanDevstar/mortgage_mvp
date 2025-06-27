import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI

# ✅ Import the new CRM monitor with status filtering
from crm_monitor_status import scrape_crm_by_status
from app.gmail_client import send_email


# ✅ Load environment variables
load_dotenv()

# ✅ OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# ✅ Load CRM Data based on status 'DRAFT_FOR_BROKER'
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
crm_path = os.path.join(base_dir, "app", "data", "synthetic_crm_modified.csv")
crm_data = scrape_crm_by_status(file_path=crm_path, status="DRAFT_FOR_BROKER")


# ✅ Create Email Prompt
def create_email_prompt(client_info):
    expiry_date = pd.to_datetime(client_info["Expiry_Date"], dayfirst=True).strftime('%d %B %Y')
    today = pd.Timestamp(datetime.today())
    expiry = pd.to_datetime(client_info["Expiry_Date"], dayfirst=True)
    weeks_to_expiry = max(((expiry - today).days) // 7, 0)

    prompt = f"""
You are a professional mortgage advisor.

Generate an email to the customer about their fixed-rate home loan expiry.

Use the following details:
- Customer Name: {client_info['Customer']}
- Lender: {client_info['Lender']}
- Loan Amount: ${client_info['Loan_Amount']:,}
- Expiry Date: {expiry_date} (in {weeks_to_expiry} weeks)

✅ Follow this structure exactly:

Subject: Upcoming Fixed-Rate Home Loan Expiry - Action Required

Hi {client_info['Customer']},

Hope you are doing well.

I am emailing regarding your lending with {client_info['Lender']}, as you have a facility that is coming up for refix in the next {weeks_to_expiry} weeks (on {expiry_date}).

Your {client_info['Lender']} loan details:
Facility 1: ${client_info['Loan_Amount']:,} — action required.

We can request rates from {client_info['Lender']} to ensure that you are getting the best deal possible, as well as help you through the process of refixing.

Please let us know how you would like to proceed.

Kind regards,  
Advisor
"""
    return prompt


# ✅ Generate Email Body
def generate_email_body(prompt):
    response = client.chat.completions.create(
        model="gpt-4o",  # ✅ Correct model
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    return response.choices[0].message.content.strip()


# 🚀 Main Email Draft + Approval Flow
def main():
    if not crm_data:
        print("❌ No clients found with status DRAFT_FOR_BROKER")
        return

    for client_info in crm_data:
        prompt = create_email_prompt(client_info)
        email_body = generate_email_body(prompt)

        print("\n================ EMAIL DRAFT =================\n")
        print(email_body)
        print("\n==============================================")

        approve = input("✅ Do you want to send this email? (yes/no): ").strip().lower()

        if approve == "yes":
            to_address = "indumathydevanathasamy@gmail.com"  # ✅ Your email for testing
            subject = "Upcoming Fixed-Rate Home Loan Expiry - Action Required"
            send_email(to_address, subject, email_body)
            print(f"✅ Email sent to {to_address}")
        else:
            print("❌ Email NOT sent.")


if __name__ == "__main__":
    main()
