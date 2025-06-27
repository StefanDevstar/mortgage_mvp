import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI

from crm_monitor_status import scrape_crm_by_status
from app.gmail_client import send_email
from rate_card_parser import parse_latest_rate_card
from economic_summary_modified import get_latest_insights


# ✅ Load environment variables
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ✅ Load CRM Data
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
crm_path = os.path.join(base_dir, "app", "data", "synthetic_crm_modified.csv")

# ✅ Fetch clients with 'CLIENT_RESPONDED' status
crm_data = scrape_crm_by_status(file_path=crm_path, status="CLIENT_RESPONDED")

# ✅ Fetch rate card
rate_data = parse_latest_rate_card()

# ✅ Fetch economic insights
economic_summary = get_latest_insights()


# ✅ Create the email body
def create_email_body(client_info, rates, insights):
    expiry_date = pd.to_datetime(client_info["Expiry_Date"], dayfirst=True).strftime('%d %B %Y')

    # Format rate card section
    rates_text = "\n".join(
        [f"- {term}: {details.get('Advertised', 'N/A')}% p.a."
         for term, details in rates.items()]
    )

    # Format economic summary section
    insights_clean = [line.strip() for line in insights if line.strip()]
    top_insights = insights_clean[:3] if insights_clean else ["No recent insights available."]
    insights_text = "\n".join([f"- {point}" for point in top_insights])

    email_body = f"""
Hi {client_info['Customer']},

Thank you for your response. As your fixed rate expiry is approaching on {expiry_date}, I wanted to share the latest rate options and provide you with a quick economic update to assist with your decision.

📌 Current Rate Options with {client_info['Lender']}:
{rates_text}

📊 Economic Update Highlights:
{insights_text}

Next Steps:
- Review these rate options.
- Let me know if you’d like to discuss any of these options in detail.
- I’m happy to assist with the refixing process or answer any questions.

Please reply if you’d like to proceed or explore your options further.

Kind regards,  
Advisor
"""
    return email_body.strip()


# 🚀 Main Function
def main():
    if not crm_data:
        print("❌ No clients found with status 'CLIENT_RESPONDED'.")
        return

    for client_info in crm_data:
        email_body = create_email_body(client_info, rate_data, economic_summary)

        print("\n================ EMAIL DRAFT =================\n")
        print(email_body)
        print("\n==============================================")

        approve = input("✅ Do you want to send this email? (yes/no): ").strip().lower()

        if approve == "yes":
            to_address = "indumathydevanathasamy@gmail.com"
            subject = f"Fixed Rate Options – {client_info['Customer']} – {client_info['Lender']}"
            send_email(to_address, subject, email_body)
            print(f"✅ Email sent to {to_address}")
        else:
            print("❌ Email NOT sent.")


if __name__ == "__main__":
    main()
