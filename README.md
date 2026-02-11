📊 Transfer Budget Optimization Model

A data-driven decision framework to identify the optimal combination of football player signings under financial constraints.
This project integrates scouting intelligence with financial modeling to simulate real-world transfer strategy under budget and wage constraints.

🎯 Project Objective

Select K = 3 midfielders that:
	•	Maximize on-field performance metric (Ball Security Index)
	•	Stay within a defined transfer budget
	•	Stay within a defined annual wage cap

This simulates realistic squad planning constraints used by professional football clubs.

💰 Financial Constraints (Version 1)
	•	Transfer Budget: €60M
	•	Annual Wage Cap: €12M
	•	Selection Size: 3 Players

🧠 Methodology

1️⃣ Player Shortlisting
	•	Shortlist generated from a separate Player Replacement Model
	•	Based on role clustering and performance feature engineering
	•	PCA used for dimensionality reduction
	•	Players tagged by tactical profile (e.g., Creative Midfielder)

2️⃣ Financial Data Integration
	•	Scraped market values and wage data
	•	Created a consolidated finance master dataset
	•	Matched shortlisted players with financial information

3️⃣ Wage Imputation

Since salary data coverage was incomplete:
	•	Computed wage-to-market-value ratios from observed finance data
	•	Used median ratio to estimate missing wages
	•	Flagged imputed values transparently

Formula:

Estimated Wage = Market Value × Median(Wage / Market Value)
This preserved decision realism while maintaining analytical integrity.

4️⃣ Optimization Model

Performed exhaustive combinatorial optimization (brute-force search):

For K = 3,
All possible combinations were evaluated:

Constraints:

Σ Market Value ≤ Transfer Budget
Σ Annual Wage ≤ Wage Cap

Objective:

Maximize Σ Ball Security Index

This guarantees a globally optimal solution for the given candidate set.

📈 Output

The model produces:
	•	Selected player combination
	•	Total transfer spend
	•	Total annual wage
	•	Remaining budget capacity
	•	Total objective score

Results are visualized via Tableau.

📊 Interactive Dashboard

👉 View Live Dashboard Here: https://public.tableau.com/views/TransferBudgetOptimization/TransferBudgetOptimization?:language=en-GB&:sid=&:redirect=auth&:display_count=n&:origin=viz_share_link

Dashboard includes:
	•	Candidate financial tradeoff scatter plot
	•	Selected vs non-selected visualization
	•	Budget utilization KPIs
	•	Selected player summary table

🛠 Tech Stack
	•	Python (pandas, itertools)
	•	Web scraping (Transfermarkt / salary sources)
	•	Feature engineering & clustering (PCA, KMeans)
	•	Tableau Public
	•	Git version control
    
🚀 Key Takeaways
	•	Demonstrates integration of scouting analytics and financial constraints
	•	Applies optimization under real-world cost limitations
	•	Implements transparent wage imputation methodology
	•	Provides interactive visualization for strategic decision explanation

📌 Future Improvements
	•	Extend optimization across multiple positions
	•	Implement Integer Linear Programming (PuLP)
	•	Add dynamic budget parameter control
	•	Incorporate multi-metric weighted objective function

👤 Author

Sahil (MBA – Business Analytics)
Senior Technical Associate | Sports Analytics Enthusiast
