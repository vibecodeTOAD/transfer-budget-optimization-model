from pathlib import Path
import pandas as pd

# ----------------------------
# Scenario Parameters (EDIT)
# ----------------------------
TRANSFER_BUDGET_EUR = 60000000
WAGE_CAP_EUR_YEAR = 12000000
K = 1  # number of midfielders to select

# ----------------------------
# Paths
# ----------------------------
ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"

INPUT_XLSX = PROCESSED / "candidates_midfield_v2_imputed.xlsx"
OUTPUT_XLSX = PROCESSED / "optimized_midfield_v1.xlsx"

# ----------------------------
# Main
# ----------------------------
def main():
    df = pd.read_excel(INPUT_XLSX)
    print("Available columns:", list(df.columns))

    # Ensure numeric
    df["market_value_eur"] = pd.to_numeric(df["market_value_eur"], errors="coerce")
    df["wage_eur_year"] = pd.to_numeric(df["wage_eur_year"], errors="coerce")
    df["ball_security_index"] = pd.to_numeric(df["ball_security_index"], errors="coerce")

    # Filter eligible
    df = df[df["optimizer_eligible"] == True].copy()

    print("Eligible players:", len(df))

    # Sort by objective (maximize creativity)
    df = df.sort_values("ball_security_index", ascending=False)

    selected = []
    total_value = 0
    total_wage = 0

    # Simple greedy selection (since K is small)
    for _, row in df.iterrows():
        if len(selected) >= K:
            break

        new_total_value = total_value + row["market_value_eur"]
        new_total_wage = total_wage + row["wage_eur_year"]

        if new_total_value <= TRANSFER_BUDGET_EUR and new_total_wage <= WAGE_CAP_EUR_YEAR:
            selected.append(row)
            total_value = new_total_value
            total_wage = new_total_wage

    if not selected:
        print("No feasible solution under given constraints.")
        return

    result = pd.DataFrame(selected)

    result["remaining_budget"] = TRANSFER_BUDGET_EUR - total_value
    result["remaining_wage_capacity"] = WAGE_CAP_EUR_YEAR - total_wage

    OUTPUT_XLSX.parent.mkdir(parents=True, exist_ok=True)
    result.to_excel(OUTPUT_XLSX, index=False)

    print("\nSelected Player(s):")
    print(result[["player_name", "ball_security_index", "market_value_eur", "wage_eur_year"]])
    print("\nTotal Transfer Spend:", total_value)
    print("Total Annual Wage:", total_wage)
    print("Remaining Budget:", TRANSFER_BUDGET_EUR - total_value)
    print("Remaining Wage Cap:", WAGE_CAP_EUR_YEAR - total_wage)
    print("\n✅ Wrote:", OUTPUT_XLSX)

if __name__ == "__main__":
    main()