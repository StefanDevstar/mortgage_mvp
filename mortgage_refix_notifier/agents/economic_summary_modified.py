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
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()

            soup = BeautifulSoup(resp.text, "html.parser")

            headlines = soup.find_all(["h2", "h3", "li", "p"])

            for tag in headlines:
                text = tag.get_text(strip=True)
                if any(word in text.lower() for word in ["mortgage", "rate", "inflation", "rbnz", "interest", "economy", "growth"]):
                    if len(text) > 30:
                        insights.append(text)
                if len(insights) >= 3:
                    break

            if len(insights) >= 3:
                break

        except Exception as e:
            print(f"❌ Error fetching {url}: {e}")
            return ["Failed to fetch economic summary."]

    # ✅ Save to cache
    with open(INSIGHTS_FILE, "w") as f:
        json.dump({"date": datetime.date.today().isoformat(), "insights": insights}, f)

    return insights


def get_latest_insights():
    try:
        with open(INSIGHTS_FILE, "r") as f:
            data = json.load(f)
            if data.get("date") == datetime.date.today().isoformat():
                return data.get("insights", [])
    except Exception:
        pass

    return fetch_insights()


# ✅ Run example
if __name__ == "__main__":
    insights = get_latest_insights()
    print("Today's economic insights:", insights)
