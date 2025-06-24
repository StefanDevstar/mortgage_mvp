import pandas as pd
from typing import Dict

class EconomicSummaryAgent:
    def __init__(self, csv_path: str = "app/data/economic_summary.csv"):
        self.data = pd.read_csv(csv_path)

    def get_summary_for_region(self, region: str) -> Dict[str, float]:
        row = self.data[self.data["Region"].str.lower() == region.lower()]
        if row.empty:
            return {
                "UnemploymentRate": None,
                "MedianIncome": None,
                "InflationRate": None,
                "GrowthRate": None
            }
        row = row.iloc[0]
        return {
            "UnemploymentRate": row["UnemploymentRate"],
            "MedianIncome": row["MedianIncome"],
            "InflationRate": row["InflationRate"],
            "GrowthRate": row["GrowthRate"]
        }

# Example usage:
if __name__ == "__main__":
    agent = EconomicSummaryAgent()
    summary = agent.get_summary_for_region("Dunedin")
    print(summary)
