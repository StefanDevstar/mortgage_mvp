def generate_repayment_options(client, rate_data):
    """
    Generates hypothetical repayment scenarios based on the current rate card.
    """
    scenarios = []
    principal = client.get("mortgage_amount", 500000)
    term_years = client.get("term_years", 25)

    for label, rate in rate_data.items():
        monthly_rate = rate / 100 / 12
        months = term_years * 12
        monthly_payment = (principal * monthly_rate) / (1 - (1 + monthly_rate) ** -months)

        scenarios.append({
            "term": label,  # 👈 changed from 'plan' to 'term'
            "rate": rate,
            "monthly_repayment": round(monthly_payment, 2)  # 👈 renamed key
        })

    print(f"Generated {len(scenarios)} repayment scenarios for {client['name']}")
    return scenarios
