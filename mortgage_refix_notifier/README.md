# 🏠 Mortgage Refix Notification System

An AI-powered modular system to notify clients of upcoming mortgage refixes using mock data. Built using Python, this project parses CRM details, rate card data (from PDF), and economic summaries to generate personalized email suggestions.

---

## 🚀 Features

- Detects clients whose mortgages are expiring in the next 90 days
- Parses current interest rates from PDF rate card
- Simulates property valuation
- Incorporates mock economic indicators
- Generates a personalized refix email per client
- Modular structure – easily extendable to use real APIs or scraped data

---

### Setup

cd mortgage_refix_notifier
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
python -m app.main
