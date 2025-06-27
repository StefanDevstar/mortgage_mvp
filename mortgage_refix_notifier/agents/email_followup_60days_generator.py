import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI

from crm_monitor_status import scrape_crm_by_status
from app.gmail_client import send_email


# ✅ Load environment variables
load_dotenv()

# ✅ OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ✅ Load CRM Data
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
crm_path = os.path.join(base_dir, "app", "data", "synthetic_crm_modified.csv")

# ✅ Fetch clients whose status is 'AWAITING_CLIENT_RESPONSE'
crm_data = scrape_crm_by_status(file_path=crm_path, status="AWAITING_CLIENT_RESPONSE")


# ✅ Create 60-Day Follow-Up Email Prompt
def create_followup_prompt(client_info):
    expiry_date = pd.to_datetime(client_info["Expiry_Date"], dayfirst=True).strftime('%d %B %Y')
    
    prompt = f"""
You are a professional mortgage advisor.

Generate a simple and direct follow-up email to the client, because it's been 30 days since the first email. The tone should be clear, polite, and informative — not pushy.

✅ Format:

Hi {client_info['Customer']},

I emailed you about a month ago letting you know that your fixed rate expiry is coming up.

Have a look at the email I sent you and let me know if you would like a run down of the situation to explore your options.

You have about 60 days before your fixed rate expires (on {expiry_date}).

Just reply to this email if you'd like to discuss further.

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


# 🚀 Main
def main():
    for client_info in crm_data:
        prompt = create_followup_prompt(client_info)
        email_body = generate_email_body(prompt)

        print("\n================ 60-DAY FOLLOW-UP EMAIL =================\n")
        print(email_body)
        print("\n==========================================================")

        approve = input("✅ Do you want to send this follow-up email? (yes/no): ").strip().lower()

        if approve == "yes":
            to_address = "indumathydevanathasamy@gmail.com"
            subject = "Reminder: Your Fixed Rate Expiry is Coming Up"
            send_email(to_address, subject, email_body)
            print(f"✅ Follow-up email sent to {to_address}")
        else:
            print("❌ Email NOT sent.")


if __name__ == "__main__":
    main()
