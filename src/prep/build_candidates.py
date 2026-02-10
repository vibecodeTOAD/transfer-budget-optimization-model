from __future__ import annotations

import re
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"

FINANCE_XLSX = PROCESSED / "finance_master.xlsx"
SHORTLIST_XLSX = PROCESSED / "Midfielders_data_shortlist.xlsx"
OUT_XLSX = PROCESSED / "candidates_midfield.xlsx"


# ---------- helpers ----------
def norm_name(x: str) -> str:
    if pd.isna(x):
        return ""
    x = str(x).strip().lower()
    x = re.sub(r"\s+", " ", x)
    # remove common punctuation that causes mismatches
    x = x.replace("’", "'").replace("`", "'")
    x = re.sub(r"[^\w\s'\-]", "", x)
    return x


def find_col(df: pd.DataFrame, patterns: list[str], required: bool = True) -> str | None:
    cols = list(df.columns)
    low = {c.lower(): c for c in cols}

    # exact / contains match
    for p in patterns:
        p = p.lower()
        for lc, orig in low.items():
            if p == lc or p in lc:
                return orig

    # regex match
    for p in patterns:
        rx = re.compile(p, re.IGNORECASE)
        for c in cols:
            if rx.search(str(c)):
                return c

    if required:
        raise ValueError(
            f"Could not find column matching {patterns}. Available columns: {cols}"
        )
    return None


def to_number_eur(s: pd.Series) -> pd.Series:
    """Coerce mixed currency strings/numbers to float. Leaves NaN if not parseable."""
    if pd.api.types.is_numeric_dtype(s):
        return s.astype(float)

    x = s.astype(str).str.replace(",", "", regex=False).str.strip()

    # remove currency symbols and text
    x = x.str.replace("€", "", regex=False)
    x = x.str.replace("EUR", "", regex=False).str.replace("eur", "", regex=False)

    # common placeholders
    x = x.replace({"": None, "nan": None, "None": None, "-": None})

    # extract first number
    x = x.str.extract(r"([-+]?\d*\.?\d+)")[0]
    return pd.to_numeric(x, errors="coerce")


# ---------- main ----------
def main():
    if not FINANCE_XLSX.exists():
        raise FileNotFoundError(f"Missing: {FINANCE_XLSX}")
    if not SHORTLIST_XLSX.exists():
        raise FileNotFoundError(f"Missing: {SHORTLIST_XLSX}")

    # load files
    finance = pd.read_excel(FINANCE_XLSX)
    shortlist = pd.read_excel(SHORTLIST_XLSX)

    # detect key columns
    sl_player = find_col(shortlist, ["player name", "player_name", r"^player$"])
    sl_role = find_col(shortlist, ["midfield playstyle final", "role", "role_tag"], required=False)
    sl_pos = find_col(shortlist, ["position", "pos"], required=False)

    fin_player = find_col(finance, ["player", "player name", "player_name", "name"])

    # finance: value + wage + contract (best-effort)
    fin_value = "market value EUR"
    fin_wage = "Total Gross P/Y (Eur)"
    fin_contract = find_col(
        finance,
        ["contract", "expiration", "expiry", "end", "until"],
        required=False,
    )

    # normalize names for joining
    shortlist = shortlist.copy()
    finance = finance.copy()

    shortlist["player_name"] = shortlist[sl_player].map(norm_name)
    finance["player_name"] = finance[fin_player].map(norm_name)

    # dedupe finance by player_name (keep the row with max wage/value if duplicates exist)
    if fin_wage:
        finance["_wage_num"] = to_number_eur(finance[fin_wage])
    else:
        finance["_wage_num"] = pd.Series([pd.NA] * len(finance))

    if fin_value:
        finance["_value_num"] = to_number_eur(finance[fin_value])
    else:
        finance["_value_num"] = pd.Series([pd.NA] * len(finance))

    finance = (
        finance.sort_values(by=["player_name", "_wage_num", "_value_num"], ascending=[True, False, False])
        .drop_duplicates(subset=["player_name"], keep="first")
    )

    # inner join: shortlist ∩ finance (optimizer needs complete finance)
    merged = shortlist.merge(
        finance,
        on="player_name",
        how="inner",
        suffixes=("_sl", "_fin")
    )

    # pick important output columns (keep your extra shortlist columns too)
    out = pd.DataFrame()
    out["player_name"] = merged["player_name"]

    if sl_pos:
        out["position"] = merged[sl_pos]
    if sl_role:
        out["role_tag"] = merged[sl_role]

    # keep shortlist numeric features if present
    for c in ["Creativity Index", "Verticality Score", "Ball Progression", "Ball Security Index", "X G", "Pca X", "Pca Y"]:
        if c in merged.columns:
            out[c.lower().replace(" ", "_")] = pd.to_numeric(merged[c], errors="coerce")

    # finance fields (best-effort)
    if fin_value:
        out["market_value_eur"] = merged["_value_num"]
    else:
        out["market_value_eur"] = pd.NA

    if fin_wage:
        out["wage_eur_year"] = merged["_wage_num"]
    else:
        out["wage_eur_year"] = pd.NA

    if fin_contract:
        out["contract_raw"] = merged[fin_contract]

    # Eligibility flags (VERY IMPORTANT)
    out["has_value"] = out["market_value_eur"].notna()
    out["has_wage"] = out["wage_eur_year"].notna()
    out["optimizer_eligible"] = out["has_value"] & out["has_wage"]

    # quick audit prints
    print("Shortlist rows:", len(shortlist))
    print("Finance rows (deduped):", len(finance))
    print("Candidates rows (inner-joined):", len(out))

    # save
    OUT_XLSX.parent.mkdir(parents=True, exist_ok=True)
    out.to_excel(OUT_XLSX, index=False)
    print("✅ Wrote:", OUT_XLSX)


if __name__ == "__main__":
    main()