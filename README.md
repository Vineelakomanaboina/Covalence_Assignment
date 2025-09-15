# 🔌 Smart Grid Power Consumption Analyzer  

This repository contains my implementation of a **Power Consumption Analyzer System** as part of my assignment.  
The project simulates a real-world **smart grid monitoring pipeline**, where hourly power consumption is recorded at household level, merged with city-level metadata, and analyzed to generate risk insights and visualizations.  

---

## 📌 Problem Statement  

Responsible for monitoring power consumption across multiple cities to optimize energy distribution and prevent blackouts.  

Each city has multiple districts, and each district has hundreds of households.  
Smart meters in each household record hourly consumption data, stored as:  

- **CSV files** → per district, with hourly household-level consumption.  
- **JSON files** → per city per day, with district metadata (thresholds, critical hours).  

Our system must:  

- **Read & Merge Hybrid Data** (CSV + JSON).  
- **Perform Multi-Level Aggregations** (household, district, city).  
- **Generate Risk Insights** (detect threshold violations & critical-hour peaks).  
- **Handle Missing & Corrupted Data** gracefully.  
- **Generate Output Reports** (CSV + JSON).  
- **Produce Visualizations** for trends and risk distribution.  

---

## Requiremts Setup

pip install -r requirements.txt

---

## Run The project

python main.py

This will:

Generate CSV + JSON data in data/.

Process and merge data.

Compute district/city level statistics.

Save outputs in output/summary_csv/ and output/reports_json/.

---

## Visualize Results

python covalence_assignment_visualization.py

This will:
Display visualizations (bar charts, line plots, pie charts, heatmaps).
Save all plots in output/plots/.

---


## 🏗️ Project Structure  

.
├── main.py # Main program - generates data, processes metrics, saves outputs
├── covalence_assignment_visualization.ipynb # Visualization script (bar charts, pie charts, heatmaps, etc.)
├── data/
│ ├── csv/ # District-level hourly consumption CSV files
│ └── json/ # City-level metadata JSON files (thresholds, critical hours)
├── output/
│ ├── summary_csv/ # Per-city daily summary CSVs
│ └── reports_json/ # JSON reports with risk alerts
└── README.md # Project documentation (this file)

---


