# app/langgraph_flow.py

from langgraph.graph import StateGraph, END
from agents.crm_monitor import crm_monitor_agent
from agents.property_valuation import property_valuation_agent
from agents.rate_card_parser import rate_card_parser_agent
from agents.economic_summary import economic_summary_agent
from agents.repayment_scenarios import repayment_scenarios_agent
from agents.client_email_generator import email_generator_agent
from agents.follow_up import follow_up_agent

from app.config import CustomState

def build_langgraph_flow():
    workflow = StateGraph(CustomState)

    # Add nodes (agents)
    workflow.add_node("CRM Monitor", crm_monitor_agent)
    workflow.add_node("Rate Card Parser", rate_card_parser_agent)
    workflow.add_node("Property Valuation", property_valuation_agent)
    workflow.add_node("Economic Summary", economic_summary_agent)
    workflow.add_node("Repayment Scenarios", repayment_scenarios_agent)
    workflow.add_node("Email Generator", email_generator_agent)
    workflow.add_node("Follow-Up", follow_up_agent)

    # Define flow
    workflow.set_entry_point("CRM Monitor")
    workflow.add_edge("CRM Monitor", "Rate Card Parser")
    workflow.add_edge("Rate Card Parser", "Property Valuation")
    workflow.add_edge("Property Valuation", "Economic Summary")
    workflow.add_edge("Economic Summary", "Repayment Scenarios")
    workflow.add_edge("Repayment Scenarios", "Email Generator")
    workflow.add_edge("Email Generator", "Follow-Up")
    workflow.add_edge("Follow-Up", END)

    # Compile the flow
    graph = workflow.compile()
    return graph
