import pandas as pd
import re
from pathlib import Path

FILES = [
    "Bundesliga_Players.xlsx",
    "Ligue1_Players.xlsx",
    "SerieA_Players.xlsx",
    "Premier_League_Players.xlsx",
    "LaLiga_Players.xlsx"
]

POSITIONS = [
    "Goalkeeper",
    "Centre-Back", "Left-Back", "Right-Back", "Full-Back",
    "Defensive Midfield", "Central Midfield", "Attacking Midfield",
    "Left Midfield", "Right Midfield",
    "Left Winger", "Right Winger", "Winger",
    "Second Striker", "Centre-Forward"
]

position_pattern = r"^(.*)\s+(" + "|".join(map(re.escape, POSITIONS)) + r")$"

all_dfs = []

for file_path in FILES:
    df = pd.read_excel(file_path)

    # --- split player into name + position ---
    extracted = df["player"].astype(str).str.extract(position_pattern)
    df["player_name"] = extracted[0]
    df["position"] = extracted[1]

    # --- drop source_url if present ---
    if "source_url" in df.columns:
        df = df.drop(columns=["source_url"])

    # --- add league name from filename ---
    league = Path(file_path).stem.replace("_Players", "")
    df["league"] = league

    all_dfs.append(df)

# --- merge all into one dataframe ---
final = pd.concat(all_dfs, ignore_index=True)

# (optional) move columns to front
front_cols = ["league", "player_name", "position"]
other_cols = [c for c in final.columns if c not in front_cols]
final = final[front_cols + other_cols]

final.to_excel("All_Leagues_Merged_Cleaned.xlsx", index=False)
print("Saved: All_Leagues_Merged_Cleaned.xlsx")
print("Total rows:", len(final))