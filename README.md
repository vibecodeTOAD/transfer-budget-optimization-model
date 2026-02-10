# transfer-budget-optimization-model
## Current Pipeline Status

### Data Preparation
- Player shortlists are exported from the Player Replacement Model (Tableau)
- Financial data (market value, wages, contract) is collected separately
- A prep script joins shortlist and finance data to create optimizer-ready candidates

### Key Output (local, not committed)
- `data/processed/candidates_midfield.xlsx`
  - One row per shortlisted midfielder
  - Includes market value and available wage data
  - Contains explicit optimizer eligibility flags