# HabitLoop Retention Analysis

Competitive voice-of-customer retention benchmark for consumer subscription and habit-driven apps.

This project analyzes 3,992 real public App Store reviews across competing apps, classifies customer feedback into retention risk themes, and converts insights into lifecycle marketing recommendations such as onboarding, engagement, save, and win-back strategies.

## Why This Project Exists

Public reviews often reveal churn drivers that product analytics alone may miss, such as pricing friction, broken streaks, motivation loss, onboarding confusion, and support pain points. This project uses customer language to uncover those signals and benchmark competing apps.

## Data Source

Collected from Apple public App Store review feeds. No synthetic data used.

### Competitive App Categories
- Language learning: Duolingo vs Babbel  
- Meditation and sleep: Headspace vs Calm  
- Self-care journaling: Finch vs Daylio  
- Routine and habit building: Fabulous vs Habitica  

## Project Outputs

- `dashboard.html` – Interactive dashboard  
- `summary.json` – Aggregated metrics  
- `retention_review_log_compact.xlsx` – Supporting dataset  
- Python scripts for data collection and analysis  

## Dashboard Features

- KPI overview  
- Retention Signal Map  
- Cross-App Benchmarking  
- Lifecycle Campaign Briefs  
- Review Explorer  
- Campaign Decision Lab  

## How to Run

```bash
python -m pip install -r requirements.txt
python 1_collect_reviews.py
python 2_analyze_reviews.py
