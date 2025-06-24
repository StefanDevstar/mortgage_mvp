import os
import re
import fitz  # from PyMuPDF

def extract_rates_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()

    # Extract rate lines like "1 year 6.45%" using regex
    pattern = r"(\d+\s+year).*?(\d+\.\d+)%"
    matches = re.findall(pattern, text, re.IGNORECASE)

    rates = {}
    for term, rate in matches:
        rates[term.strip()] = float(rate)

    return rates

def parse_latest_rate_card(folder_path="app/data/rate_cards"):
    pdf_files = [f for f in os.listdir(folder_path) if f.endswith(".pdf")]
    if not pdf_files:
        print("❌ No PDF files found in rate card folder.")
        return {}

    latest_pdf = max(
        [os.path.join(folder_path, f) for f in pdf_files],
        key=os.path.getctime
    )
    rates = extract_rates_from_pdf(latest_pdf)
    print(f"Extracted rates from {latest_pdf}: {rates}")
    return rates
