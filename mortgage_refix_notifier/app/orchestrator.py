# app/orchestrator.py

from agents.property_valuation import get_property_valuation
from agents.repayment_scenarios import generate_repayment_options
from agents.client_email_generator import generate_email
from agents.follow_up import schedule_follow_up
from agents.crm_monitor import check_mortgage_expiry
from agents.rate_card_parser import parse_latest_rate_card
from agents.economic_summary import EconomicSummaryAgent  # updated import

def run_orchestration(client_data):
    print("\n🔄 Starting Orchestration...\n")

    # Step 1: CRM Monitoring
    eligible_clients = check_mortgage_expiry(client_data)

    # Initialize Economic Summary Agent once
    econ_agent = EconomicSummaryAgent()

    for client in eligible_clients:
        print(f"\n➡️ Processing Client: {client['name']}")

        # Step 2: Rate Card Parsing
        rates = parse_latest_rate_card()

        # Step 3: Property Valuation
        valuation = get_property_valuation(client)

        # Step 4: Economic Summary using client's region or default to 'Dunedin'
        region = client.get("region", "Dunedin")
        summary = econ_agent.get_summary_for_region(region)

        # Step 5: Repayment Scenarios
        repayment_options = generate_repayment_options(client, rates)

        # Step 6: Generate Email
        email = generate_email(client, valuation, rates, summary, repayment_options)

        # Step 7: Follow-up
        schedule_follow_up(client)

        print(f"\n✅ Email Ready for {client['name']}:\n{email}")

    print("\n🎉 Orchestration Complete!")
