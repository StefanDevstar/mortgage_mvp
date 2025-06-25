import time
import os
import requests
import base64
from dotenv import load_dotenv

load_dotenv()

# Config (put these in your .env for real code)
CLIENT_ID = os.getenv("CORELOGIC_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("CORELOGIC_CLIENT_SECRET", "")
CORELOGIC_BASE_URL = os.getenv("CORELOGIC_BASE_URL", "")
OAUTH_URL = "https://api.corelogic.asia/access/as/token.oauth2?grant_type=client_credentials"
MATCH_URL = f"{CORELOGIC_BASE_URL}/search/nz/matcher/address"

# Token cache (in-memory for demo)
token_data = {
    "access_token": None,
    "expires_at": 0
}

def get_access_token():
    """Fetch or refresh OAuth2 access token."""
    now = int(time.time())
    # If we have a token and it's still valid, use it
    if token_data["access_token"] and token_data["expires_at"] > now + 60:
        return token_data["access_token"]
    
    auth_header = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()

    headers = {
        'Content-Length': '0',
        'Authorization': f'Basic {auth_header}'
    }
    print("auth_header", CLIENT_SECRET)

    # Otherwise, fetch a new token
    resp = requests.post(
        OAUTH_URL,
        headers=headers
    )
    resp.raise_for_status()
    d = resp.json()
    token_data["access_token"] = d["access_token"]
    print("Acess Token:", d["access_token"])
    token_data["expires_at"] = now + int(d["expires_in"])
    return token_data["access_token"]

def corelogic_search(address):
    # Get address from query string
    if not address:
        return {"error": "No address specified"}

    # Get token, refresh if needed
    token = get_access_token()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    params = {
        "q": address,
        "matchProfileId": 1
    }
    url = MATCH_URL
    resp = requests.get(url, headers=headers, params=params)
    try:
        matches = resp.json().get("matches", [])
        print("matches:", matches)
        if not matches:
            print("No matches found.")
            property_id = None
        else:
            property_list = matches[0].get("references").get("propertyIdList")
            
            if not property_list:
                print("No property IDs found in the list.")
                property_id = None
            else:
                property_id = property_list[0]
                if property_id is None:
                    print("Property ID is None.")
                else:
                    print(f"Found Property ID: {property_id}")

                    avm_url = f"{CORELOGIC_BASE_URL}/avm/nz/properties/{property_id}/avm/intellival/origination/current"
                    params = {
                        "countryCode ": "nz",
                        "propertyId ": property_id
                    }
                                    
                    res = requests.get(avm_url, headers=headers, params=params)
                    print("Valuation Data:", res.json())
                    return res.json()

    except (IndexError, KeyError) as e:
        print(f"An error occurred accessing the data: {e}")
        property_id = None

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        property_id = None

    

def fetch_valuation(address):
    address = "41 Orchard Road"
    valuation = corelogic_search(address)
    print("valuation:", valuation)
    return valuation