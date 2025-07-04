import os
import pandas as pd
import camelot
from dotenv import load_dotenv
from app.services.dashboard import saveLog

load_dotenv()


def extract_rate_table(pdf_path):
    """
    Extracts the largest table from the PDF using Camelot.
    """
    try:
        tables = camelot.read_pdf(pdf_path, pages='1-end', flavor='stream')
    except Exception as e:
        print(f"❌ Error reading PDF: {e}")
        saveLog("extract_rate_table", f"❌ Error reading PDF: {e}")

        return None

    if tables.n == 0:
        print("❌ No tables found in the PDF.")
        saveLog("extract_rate_table", f"In Rate Card, No tables found in the PDF.")

        return None

    table = max(tables, key=lambda t: t.df.shape[0] * t.df.shape[1])

    df = table.df

    print("📄 Extracted Raw Table:\n", df)

    # ✅ Dynamically set column names based on the number of columns
    df.columns = [f'col_{i}' for i in range(df.shape[1])]
    df = df.reset_index(drop=True)

    print("📄 Processed Table:\n", df)

    return df


def _to_float(val):
    try:
        return float(
            str(val)
            .replace("%", "")
            .replace("p.a.", "")
            .replace("p.a", "")
            .replace(",", "")
            .strip()
        )
    except Exception:
        return None


def rate_table_to_dict(df):
    rates = {}

    invalid_terms = ["Product", "ASB Home", "Loan", "Term", "", "Rate", "Housing Variable", "Orbit Variable"]

    for idx, row in df.iterrows():
        row = row.fillna("")

        term = str(row.get('col_1', '')).strip()

        if (
            term in invalid_terms
            or "variable" in term.lower()
            or not any(char.isdigit() for char in term)
        ):
            continue

        advertised = (
            _to_float(row.get('col_2'))
            or _to_float(row.get('col_1'))
            or _to_float(row.get('col_3'))
        )
        lvr_80 = (
            _to_float(row.get('col_3'))
            or _to_float(row.get('col_4'))
            or _to_float(row.get('col_2'))
        )
        lvr_gt_80 = (
            _to_float(row.get('col_4'))
            or _to_float(row.get('col_3'))
            or _to_float(row.get('col_2'))
        )

        rates[term] = {
            "Advertised": advertised,
            "LVR <= 80%": lvr_80,
            "LVR > 80%": lvr_gt_80,
        }

        print(f"✅ Parsed Row {idx}: {term} → {rates[term]}")

    print("📊 Cleaned Parsed Rates Dictionary:\n", rates)
    return rates


def parse_latest_rate_card(folder_path="app/data/rate_cards"):
    pdf_files = [f for f in os.listdir(folder_path) if f.endswith(".pdf")]
    if not pdf_files:
        print("❌ No PDF files found in rate card folder.")
        return {}

    latest_pdf = max(
        [os.path.join(folder_path, f) for f in pdf_files],
        key=os.path.getctime,
    )
    # print(f"🗂️ Parsing rate card from: {latest_pdf}")

    df = extract_rate_table(latest_pdf)

    if df is not None:
        rates = rate_table_to_dict(df)
    else:
        rates = {}

    print(f"✅ Final Rates: {rates}")
    return rates


# if __name__ == "__main__":
#     rates = parse_latest_rate_card()
#     print("🎯 Extracted Mortgage Rates:", rates)