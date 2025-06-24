from agents.rate_card_parser import parse_rate_card_pdf

def test_parse_rate_card():
    pdf_path = "data/rate_cards/sample_rate_card.pdf"
    rates = parse_rate_card_pdf(pdf_path)
    print(rates)
    assert isinstance(rates, dict)
