from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"

FINANCE_XLSX = PROCESSED / "finance_master.xlsx"
CANDIDATES_XLSX = PROCESSED / "candidates_midfield.xlsx"
OUT_XLSX = PROCESSED / "candidates_midfield_v2_imputed.xlsx"

VALUE_COL = "market value EUR"          # in finance_master
WAGE_COL  = "Total Gross P/Y (Eur)"     # in finance_master

def main():
    finance = pd.read_excel(FINANCE_XLSX)
    cand = pd.read_excel(CANDIDATES_XLSX)

    # numeric coercion
    finance[VALUE_COL] = pd.to_numeric(finance[VALUE_COL], errors="coerce")
    finance[WAGE_COL]  = pd.to_numeric(finance[WAGE_COL], errors="coerce")
    cand["market_value_eur"] = pd.to_numeric(cand["market_value_eur"], errors="coerce")
    cand["wage_eur_year"] = pd.to_numeric(cand["wage_eur_year"], errors="coerce")

    # Build a simple wage-to-value ratio from finance_master (only where both exist)
    ratio = (finance[WAGE_COL] / finance[VALUE_COL]).replace([np.inf, -np.inf], np.nan)
    ratio = ratio.dropna()

    if ratio.empty:
        raise ValueError("No valid wage/value ratio found in finance_master. Cannot impute wages.")

    # Robust central value (median)
    median_ratio = ratio.median()

    # Impute missing wages in candidates: wage = market_value * median_ratio
    cand["wage_imputed"] = False
    missing = cand["wage_eur_year"].isna() & cand["market_value_eur"].notna()
    cand.loc[missing, "wage_eur_year"] = cand.loc[missing, "market_value_eur"] * median_ratio
    cand.loc[missing, "wage_imputed"] = True

    # Refresh flags
    cand["has_value"] = cand["market_value_eur"].notna()
    cand["has_wage"] = cand["wage_eur_year"].notna()
    cand["optimizer_eligible"] = cand["has_value"] & cand["has_wage"]

    OUT_XLSX.parent.mkdir(parents=True, exist_ok=True)
    cand.to_excel(OUT_XLSX, index=False)

    print("Median wage/value ratio used:", float(median_ratio))
    print("Candidates total:", len(cand))
    print("Eligible after imputation:", int(cand["optimizer_eligible"].sum()))
    print("✅ Wrote:", OUT_XLSX)

if __name__ == "__main__":
    main()