# app/config.py
import os
from dotenv import load_dotenv
from typing import TypedDict, Optional, List

class CustomState(TypedDict, total=False):
    client_name: str
    client_email: str
    mortgage_details: dict
    property_valuation: dict
    economic_summary: dict
    repayment_options: List[dict]
    email_content: str
    follow_up_reminder: Optional[str]



load_dotenv()

class Config:
    MONGO_URI = os.getenv('MONGO_URI')
    CORELOGIC_API_KEY = os.getenv('CORELOGIC_API_KEY')
    CORELOGIC_BASE_URL = os.getenv('CORELOGIC_BASE_URL', 'https://api.corelogic.co.nz')
    GMAIL_CLIENT_ID = os.getenv('GMAIL_CLIENT_ID')
    GMAIL_CLIENT_SECRET = os.getenv('GMAIL_CLIENT_SECRET')