import os
import pandas as pd
from datetime import datetime
import logging
from typing import List, Dict

# ✅ Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('crm_monitor')

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
crm_path = os.path.join(base_dir, "app", "data", "synthetic_crm_modified.csv")

def scrape_crm_data(
    file_path: str = crm_path,
    expiry_column: str = "Expiry_Date",
    filter_days: int = 90,
    amount_column: str = "Loan_Amount",
    **csv_kwargs
) -> List[Dict]:
    """
    Scrapes CRM data from CSV and filters records 
    where the expiry date is exactly 'filter_days' days from today.
    """
    try:
        required_columns = ["Customer", "Lender", "Rate_Type", expiry_column, amount_column, "Address"]

        logger.info(f"Reading CRM data from: {file_path}")

        df = pd.read_csv(
            file_path,
            parse_dates=[expiry_column],
            dayfirst=True,
            usecols=lambda col: col in required_columns,
            **csv_kwargs
        )

        # ✅ Filter for expiry exactly 'filter_days' days from today
        today = pd.Timestamp(datetime.today()).normalize()
        target_date = today + pd.Timedelta(days=filter_days)

        filtered_df = df[
            (df[expiry_column].dt.normalize() < target_date)
        ].copy()

        client_data = filtered_df.to_dict(orient="records")

        logger.info(f"Found {len(client_data)} loans expiring exactly in {filter_days} days")
        return client_data

    except Exception as e:
        logger.error(f"Error processing CRM data: {str(e)}", exc_info=True)
        raise


def main():
    try:
        

        clients = scrape_crm_data(
            file_path=crm_path,
            expiry_column="Expiry_Date",
            filter_days=90,
            delimiter=","
        )

        if clients:
            logger.info("Expiring loans summary:")
            for loan in clients:
                logger.info(
                    f"Customer: {loan['Customer']}, "
                    f"Lender: {loan['Lender']}, "
                    f"Rate: {loan['Rate_Type']}, "
                    f"Expires: {loan['Expiry_Date'].strftime('%Y-%m-%d')}, "
                    f"Amount: ${loan['Loan_Amount']:,}"
                )
        else:
            logger.info("No expiring loans found")

    except Exception as e:
        logger.error(f"Monitoring failed: {e}")
        return 1
    return 0


if __name__ == "__main__":
    exit(main())
