from pathlib import Path
import pandas as pd
from itertools import combinations

# ----------------------------
# Scenario Parameters (EDIT)
# ----------------------------
TRANSFER_BUDGET_EUR = 60000000
WAGE_CAP_EUR_YEAR = 12000000
K = 3  # number of midfielders to select

# ----------------------------
# Paths
# ----------------------------
ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"

INPUT_XLSX = PROCESSED / "candidates_midfield_v2_imputed.xlsx"
OUTPUT_XLSX = PROCESSED / "optimized_midfield_v1.xlsx"

# Objective column in your dataset
SCORE_COL = "ball_security_index"

def main():
    df = pd.read_excel(INPUT_XLSX)

    # Ensure numeric
    df["market_value_eur"] = pd.to_numeric(df["market_value_eur"], errors="coerce")
    df["wage_eur_year"] = pd.to_numeric(df["wage_eur_year"], errors="coerce")
    df[SCORE_COL] = pd.to_numeric(df[SCORE_COL], errors="coerce")

    # Keep only eligible rows
    df = df[df["optimizer_eligible"] == True].copy()

    # Drop rows missing required numbers
    df = df.dropna(subset=["market_value_eur", "wage_eur_year", SCORE_COL])

    n = len(df)
    print("Eligible candidates:", n)

    if n < K:
        raise ValueError(f"Not enough eligible candidates to select K={K}. Only {n} available.")

    # Brute-force search over all combinations of size K
    best_combo = None
    best_score = float("-inf")
    best_value = None
    best_wage = None

    rows = df.to_dict(orient="records")

    for combo in combinations(rows, K):
        total_value = sum(r["market_value_eur"] for r in combo)
        total_wage = sum(r["wage_eur_year"] for r in combo)

        if total_value <= TRANSFER_BUDGET_EUR and total_wage <= WAGE_CAP_EUR_YEAR:
            total_score = sum(r[SCORE_COL] for r in combo)

            if total_score > best_score:
                best_score = total_score
                best_combo = combo
                best_value = total_value
                best_wage = total_wage

    if best_combo is None:
        print("No feasible solution under given constraints.")
        print(f"Budget={TRANSFER_BUDGET_EUR:,} | Wage cap={WAGE_CAP_EUR_YEAR:,} | K={K}")
        return

    result = pd.DataFrame(list(best_combo))
    result["total_transfer_spend"] = best_value
    result["total_annual_wage"] = best_wage
    result["remaining_budget"] = TRANSFER_BUDGET_EUR - best_value
    result["remaining_wage_capacity"] = WAGE_CAP_EUR_YEAR - best_wage
    result["objective_total_score"] = best_score

    OUTPUT_XLSX.parent.mkdir(parents=True, exist_ok=True)
    result.to_excel(OUTPUT_XLSX, index=False)

    print("\nSelected Player(s):")
    print(result[["player_name", SCORE_COL, "market_value_eur", "wage_eur_year", "wage_imputed"]])
    print("\nObjective total score:", best_score)
    print("Total Transfer Spend:", best_value)
    print("Total Annual Wage:", best_wage)
    print("Remaining Budget:", TRANSFER_BUDGET_EUR - best_value)
    print("Remaining Wage Cap:", WAGE_CAP_EUR_YEAR - best_wage)
    print("\n✅ Wrote:", OUTPUT_XLSX)

if __name__ == "__main__":
    main()