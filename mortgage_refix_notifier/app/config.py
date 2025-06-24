# app/config.py

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
