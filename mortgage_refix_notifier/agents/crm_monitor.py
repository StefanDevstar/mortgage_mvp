import os
import pandas as pd
from datetime import datetime, timedelta

def check_mortgage_expiry(state: dict) -> dict:
    """
    Reads CRM data and finds clients whose mortgage end date is within the next 60 days.
    Returns a filtered list of clients to pass to the next agent.
    """

    # ✅ Fix: Point to app/data/synthetic_crm.csv
    base_dir = os.path.dirname(os.path.dirname(__file__))  # Go from agents/ to root
    file_path = os.path.join(base_dir, "app", "data", "synthetic_crm.csv")

    df = pd.read_csv(file_path, parse_dates=["mortgage_end"])

    today = datetime.today()
    upcoming = today + timedelta(days=60)

    expiring_soon = df[df["mortgage_end"].between(today, upcoming)]
    client_data = expiring_soon.to_dict(orient="records")

    print(f"Found {len(client_data)} clients with expiring mortgages in the next 60 days.")
    return client_data
