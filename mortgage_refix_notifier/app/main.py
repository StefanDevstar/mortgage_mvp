# app/main.py

import pandas as pd
#from orchestrator import run_orchestration
from app.orchestrator import run_orchestration

import os

def load_synthetic_crm_data():
    data_path = os.path.join(os.path.dirname(__file__), "data", "synthetic_crm.csv")
    return pd.read_csv(data_path).to_dict(orient="records")

if __name__ == "__main__":
    print("🚀 Starting Mortgage Refix Notification System...\n")
    client_data = load_synthetic_crm_data()
    run_orchestration(client_data)
