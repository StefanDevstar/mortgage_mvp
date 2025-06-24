# agents/client_email_generator.py

def generate_email(client, valuation, rate_data, economic_summary, repayment_options):
    """
    Generates a personalized email message for the client about mortgage refix updates.

    Args:
        client (dict): Dictionary with client information.
        valuation (float): The estimated property valuation.
        rate_data (dict): Dictionary of parsed mortgage rate data.
        economic_summary (dict): Regional economic summary.
        repayment_options (list): List of repayment scenario strings.

    Returns:
        str: A personalized email message.
    """

    name = client.get("name", "Valued Client")
    current_rate = client.get("current_rate", 6.85)
    new_rate = rate_data.get("1-year Fixed Rate", 6.45)

    summary_insights = f"""
    - Unemployment Rate: {economic_summary.get("UnemploymentRate", "N/A")}%
    - Median Income: ${economic_summary.get("MedianIncome", "N/A")}
    - Inflation Rate: {economic_summary.get("InflationRate", "N/A")}%
    - Growth Rate: {economic_summary.get("GrowthRate", "N/A")}%
    """

    
    repayment_text = "\n".join(
    [f"- {opt['term']}: ${opt['monthly_repayment']:,.2f}/month" for opt in repayment_options]
    )


    email_message = f"""
    Hi {name},

    I hope you're doing well.

    We wanted to let you know that your current mortgage rate of {current_rate:.2f}% is due for a refix.
    Based on recent economic updates and property trends, we suggest a new fixed rate of {new_rate:.2f}% for your consideration.

    
    Your property has an estimated value of ${valuation['estimated_value']:,.2f}


    Here’s a quick snapshot of the economic factors influencing our recommendations:
    {summary_insights}

    Based on your profile, here are a few repayment options we’ve calculated:
    {repayment_text}

    Please feel free to reach out if you’d like to explore other rate options or have any questions.
    We’re here to help you make the best financial decision.

    Warm regards,
    Your Mortgage Advisory Team
    """

    return email_message.strip()
