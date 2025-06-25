import random
from agents.corelogic.valuation_agent import fetch_valuation

def get_property_valuation(address: str) -> dict:
    """
    Placeholder function for CoreLogic property valuation API.
    Currently returns a synthetic valuation between 90% and 110% of a random base value.
    """

    # Simulate API output with random valuation logic
    valuation = fetch_valuation(address)

    print(f"Estimated valuation for {address}: ${valuation}")
    return {
        "address": address,
        "estimated_value": valuation,
        "confidence": "high"  # Placeholder confidence level
    }

def enrich_clients_with_valuation(state: dict) -> dict:
    """
    Adds estimated property valuation to each client record.
    """
    clients = state.get("clients", [])
    enriched = []

    for client in clients:
        address = client.get("address", "")
        valuation_data = get_property_valuation(address)
        client.update(valuation_data)
        enriched.append(client)

    print(f"Valuations added for {len(enriched)} clients.")
    return {"clients": enriched}
