# agents/follow_up.py

def schedule_follow_up(client: dict) -> None:
    """
    Mock function to simulate scheduling a follow-up with the client.
    
    Args:
        client (dict): Dictionary containing client information.
    """
    name = client.get("name", "Unknown")
    email = client.get("email", "no-email@example.com")
    print(f"📅 Follow-up scheduled with {name} ({email}) in 3 days.")
