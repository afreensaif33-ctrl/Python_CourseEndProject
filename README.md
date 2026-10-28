# Rural Essential-Service Accessibility Analyzer

A Python + Streamlit project for the **Social Welfare** case study. It analyzes rural access to healthcare, banking, transport, education, and other essential services.

## Features
- Upload and validate a CSV file.
- Clean missing, malformed, and inconsistent values using pandas.
- Calculate availability and accessibility percentages.
- Compare service categories, districts, and reporting periods.
- Flag underserved villages using configurable distance and travel-time thresholds.
- Generate practical recommendations.
- Export cleaned data, service summaries, and village-priority tables.
- Interactive charts with Plotly.

> **Important:** The included dataset is illustrative sample data for testing the application. It is not official or verified rural-service data. Replace it with collected/approved records before presenting real-world conclusions.

## Run locally
Python 3.10+ recommended.

```bash
python -m venv .venv
```

Windows:
```bash
.venv\Scripts\activate
```

macOS/Linux:
```bash
source .venv/bin/activate
```

Install dependencies and start:
```bash
pip install -r requirements.txt
streamlit run app.py
```

Streamlit will print a local URL (usually `http://localhost:8501`) to open in your browser.

## Deploy / upload to GitHub
1. Create a GitHub repository.
2. Upload `app.py`, `requirements.txt`, `README.md`, `.gitignore`, and the `data/` folder.
3. To deploy free, open [Streamlit Community Cloud](https://share.streamlit.io/), connect your GitHub account, choose the repository and branch, and set the main file to `app.py`.

## CSV data dictionary
The uploaded CSV must include these columns (column names are case-insensitive; spaces are converted to underscores):

| Column | Meaning | Example |
|---|---|---|
| `district` | District or administrative area | Nandipur |
| `village` | Village name | Lakshmipur |
| `service_type` | Healthcare, Banking, Transport, Education, Other | Healthcare |
| `facility_name` | Name/type of facility | Primary Health Centre |
| `distance_km` | Distance from village reference point to service, in km | 4.2 |
| `travel_time_min` | Approximate one-way travel time, in minutes | 25 |
| `available` | Whether the service is currently available: Yes/No | Yes |
| `population` | Approximate village population | 2400 |
| `period` | Month, year, or survey period | 2026-Q1 |

A row represents one village-service observation. If a village has multiple service types, create one row per service type. Use consistent units and a consistent definition of distance/travel time.

## How accessibility is classified
A record is considered accessible when all three conditions are true:
1. `available` is Yes.
2. `distance_km` is at or below the selected maximum distance.
3. `travel_time_min` is at or below the selected maximum travel time.

The app defaults to 5 km and 30 minutes, but these are **analysis settings**, not official standards. Adjust them to match your instructor's instructions or local policy.

Village priority is based on the share of service records classified as accessible:
- **High:** below 40%
- **Medium:** 40% to below 70%
- **Low:** 70% or higher

These thresholds are simple project heuristics, not official government categories.

## Suggested project workflow
1. Define the study area and objective.
2. Collect/obtain village-level records from a reliable source or a clearly documented survey.
3. Validate and clean the data.
4. Compare access by service, village, district, and period.
5. Interpret gaps and prioritize field verification.
6. Recommend practical interventions such as mobile clinics, banking correspondents, better transport routes, or scheduled outreach.
7. State data limitations in the final report.

## Limitations
- Distance and travel time are treated as supplied measurements; this project does not calculate road-network routes or predict demand.
- The current prototype does not use GIS maps or machine learning.
- A high accessibility percentage does not guarantee affordability, quality, capacity, safe access, or availability at all hours.
- Recommendations should be validated with residents and local officials.
