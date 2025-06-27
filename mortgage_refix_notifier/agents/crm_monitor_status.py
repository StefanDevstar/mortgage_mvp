import os
import pandas as pd
import logging
from typing import List, Dict

# ✅ Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('crm_monitor_status')

def scrape_crm_by_status(
    file_path: str,
    status: str,
    **csv_kwargs
) -> List[Dict]:
    """
    Scrapes CRM data from CSV and filters records 
    based on the 'Status' column (e.g., DRAFT_FOR_BROKER, AWAITING_BROKER_REVIEW).
    """
    try:
        required_columns = ["Customer", "Lender", "Rate_Type", "Expiry_Date", "Loan_Amount", "Address", "Status"]

        logger.info(f"Reading CRM data from: {file_path}")

        df = pd.read_csv(
            file_path,
            parse_dates=["Expiry_Date"],
            dayfirst=True,
            usecols=lambda col: col in required_columns,
            **csv_kwargs
        )

        # ✅ Filter data by 'Status'
        filtered_df = df[df['Status'].str.strip().str.upper() == status.strip().upper()].copy()

        client_data = filtered_df.to_dict(orient="records")

        logger.info(f"Found {len(client_data)} clients with status '{status}'")
        return client_data

    except Exception as e:
        logger.error(f"Error processing CRM data: {str(e)}", exc_info=True)
        raise


def main():
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        crm_path = os.path.join(base_dir, "app", "data", "synthetic_crm_modified.csv")

        # ✅ Example: Filter clients where status is 'AWAITING_BROKER_REVIEW'
        clients = scrape_crm_by_status(
            file_path=crm_path,
            status="AWAITING_BROKER_REVIEW",
            delimiter=","
        )

        if clients:
            logger.info("Clients summary with selected status:")
            for loan in clients:
                logger.info(
                    f"Customer: {loan['Customer']}, "
                    f"Lender: {loan['Lender']}, "
                    f"Rate: {loan['Rate_Type']}, "
                    f"Expires: {loan['Expiry_Date'].strftime('%Y-%m-%d')}, "
                    f"Amount: ${loan['Loan_Amount']:,}, "
                    f"Status: {loan['Status']}"
                )
        else:
            logger.info("No clients found with the specified status")

    except Exception as e:
        logger.error(f"Monitoring failed: {e}")
        return 1
    return 0


if __name__ == "__main__":
    exit(main())
