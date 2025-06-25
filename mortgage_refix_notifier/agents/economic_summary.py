import requests
from bs4 import BeautifulSoup
import datetime
import json

INSIGHTS_FILE = "latest_insights.json"
ECON_URLS = [
    "https://www.tonyalexander.nz/latest-tonys-view/"
]

def fetch_insights():
    insights = []
    for url in ECON_URLS:
        resp = requests.get(url)
        soup = BeautifulSoup(resp.text, "html.parser")
        print(soup.get_text())
        # This selector will depend on the actual site structure
        headlines = soup.select("h2, h3, li, div, span")
        for headline in headlines:
            text = headline.get_text(strip=True)
            if any(word in text.lower() for word in ["mortgage", "rate", "inflation", "rbnz", "interest"]):
                insights.append(text)
            if len(insights) >= 3:
                break
        if len(insights) >= 2:
            break

    return insights

def get_latest_insights():
    try:
        with open(INSIGHTS_FILE, "r") as f:
            data = json.load(f)
            if data["date"] == datetime.date.today().isoformat():
                return data["insights"]
    except Exception:
        pass
    return fetch_insights()

# Usage:
if __name__ == "__main__":
    insights = get_latest_insights()
    print("Today's economic insights:", insights)
