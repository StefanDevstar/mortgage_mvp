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


# ✅ Load CRM Data
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
crm_path = os.path.join(base_dir, "app", "data", "synthetic_crm_modified.csv")

# ✅ Fetch clients whose status is 'DRAFT_SECOND_FOR_BROKER'


# ✅ Create Email Prompt for 30-Day Follow-up
def create_email_prompt(client_info):
    expiry_date = pd.to_datetime(client_info["Expiry_Date"], dayfirst=True).strftime('%d %B %Y')

    prompt = f"""
        You are a professional mortgage advisor.

        Generate a simple 30-day follow-up email to the client because their fixed-rate expiry is approaching. Keep it very short and simple as per this format:

        Subject: Reminder: Your Fixed Rate Expiry is Approaching

        Hi {client_info['Customer']},

        I have emailed you a couple of times letting you know that your fixed rate expiry is coming up, and there’s only 30 days left (expiry date: {expiry_date}).

        Have a look at the email I sent you and let me know if you would like a run down of the situation to explore your options.

        Let me know if you would like to explore your options.

        Kind regards,  
        Advisor
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
    prompt = create_email_prompt(client_info)
    email_body = generate_email_body(prompt)
    return email_body

if __name__ == "__main__":
    main()
