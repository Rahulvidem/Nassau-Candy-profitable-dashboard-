# 🍬 Nassau Candy Distributor
## Product Line Profitability & Margin Performance Analysis

### Setup & Run

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Place the CSV data file as:
#    data.csv   (same folder as app.py)

# 3. Launch
streamlit run app.py
```

---

### Dashboard Tabs

| Tab | Description |
|-----|-------------|
| 📊 Product Profitability | Margin leaderboard, treemap, bubble chart, data table |
| 🏭 Division Performance  | Revenue vs profit, radar chart, margin distribution |
| 💰 Cost vs Margin        | Scatter diagnostics, quadrant analysis, risk flags |
| 📈 Pareto Analysis       | 80/20 profit & revenue, regional concentration |
| 🕐 Time Trends           | Monthly trends, product comparison, volatility |
| 🗺️ Factory Map           | Interactive map with bubble size = revenue |

### Sidebar Filters
- **Date Range** — filter by order date
- **Division** — Chocolate / Sugar / Other
- **Region** — Atlantic / Gulf / Interior / Pacific
- **Low-Margin Threshold** — products below this % are flagged at-risk
- **Product Search** — free-text filter

### KPIs Tracked
- Gross Margin (%)
- Profit per Unit
- Revenue & Profit Contribution %
- Cost Ratio (%)
- Margin Volatility (Std Dev over time)

---
*Nassau Candy Distributor — Internship ML Analytics Project*
