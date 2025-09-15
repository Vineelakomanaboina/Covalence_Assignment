"""
Smart Grid Power Consumption Analyzer
-----------------------------------
Generates synthetic power consumption data, merges CSV + JSON files,
computes multi-level statistics, calculates district risk scores,
and produces both CSV/JSON reports and visualizations.

Features:
- Modular, reusable structure
- Docstrings for every function
- Detailed inline comments explaining loops, logic, and formulas
- Graceful exception handling for missing/corrupted data
- No external APIs or LLMs used — only open-source packages
"""

import os
import pandas as pd
import json
import numpy as np
import random
from datetime import datetime, timedelta
import matplotlib.pyplot as plt

# =========================
# 1. DATA GENERATION
# =========================
def generate_sample_data(data_dir="data", num_cities=2, num_districts=3, num_households=10, num_days=2):
    """
    Generate synthetic CSV (district-level) and JSON (city-level) data for Smart Grid analysis.

    Parameters:
        data_dir (str): Directory to store generated CSVs and JSONs.
        num_cities (int): Number of cities to generate.
        num_districts (int): Number of districts per city.
        num_households (int): Number of households per district.
        num_days (int): Number of days with hourly readings.

    Returns:
        None
    """
    # Ensure folders exist for CSV and JSON files
    os.makedirs(f"{data_dir}/csv", exist_ok=True)
    os.makedirs(f"{data_dir}/json", exist_ok=True)

    cities = [f"City{i+1}" for i in range(num_cities)]  # City1, City2, etc.
    start_date = datetime(2025, 9, 10)  # Base date for data generation

    # Loop through each city
    for city in cities:
        # Loop through each day to generate daily data
        for d in range(num_days):
            date = (start_date + timedelta(days=d)).strftime("%Y-%m-%d")
            district_metadata = []

            # Loop through districts of the city
            for district in range(1, num_districts + 1):
                district_id = f"{100 + district}"
                # Assign random threshold between 1.0 - 2.0 kWh for district
                threshold = round(random.uniform(1.0, 2.0), 2)
                district_metadata.append({"district_id": district_id, "threshold": threshold})

                rows = []
                # Generate household-level hourly consumption
                for h in range(1, num_households + 1):
                    household_id = f"H{h:03d}"
                    for hour in range(24):
                        ts = f"{date} {hour:02d}:00"
                        # 5% chance of missing consumption to simulate real-world incomplete data
                        consumption = round(random.uniform(0.5, 2.5), 2) if random.random() > 0.05 else np.nan
                        rows.append([household_id, ts, consumption])

                # Convert rows into DataFrame and save to CSV
                df = pd.DataFrame(rows, columns=["household_id", "timestamp", "consumption_kwh"])
                csv_filename = f"{data_dir}/csv/district_{city}_{district_id}_{date}.csv"
                df.to_csv(csv_filename, index=False)

            # Save JSON metadata for the city for the day
            json_filename = f"{data_dir}/json/city_{city}_{date}.json"
            city_data = {
                "city": city,
                "date": date,
                "districts": district_metadata,
                "critical_hours": ["18:00", "19:00", "20:00", "21:00"]  # Peak demand hours
            }
            with open(json_filename, "w") as f:
                json.dump(city_data, f, indent=4)


# =========================
# 2. DATA LOADING
# =========================
def load_and_merge_data(data_dir="data"):
    """
    Load CSVs + JSONs, merge into one big DataFrame with thresholds and metadata.

    Returns:
        pandas.DataFrame: Unified dataset with household-level readings + district thresholds.
    """
    csv_dir = f"{data_dir}/csv"
    json_dir = f"{data_dir}/json"
    all_data = []

    # Loop through each JSON file (one per city per day)
    for json_file in os.listdir(json_dir):
        try:
            with open(f"{json_dir}/{json_file}", "r") as f:
                city_meta = json.load(f)
        except json.JSONDecodeError:
            print(f"⚠️ Skipping corrupted JSON: {json_file}")
            continue

        city = city_meta.get("city", "UnknownCity")
        date = city_meta.get("date", "UnknownDate")
        critical_hours = city_meta.get("critical_hours", [])

        # Loop through each district mentioned in JSON metadata
        for district in city_meta.get("districts", []):
            district_id = district.get("district_id", "Unknown")
            threshold = district.get("threshold", 1.5)

            csv_filename = f"{csv_dir}/district_{city}_{district_id}_{date}.csv"
            if not os.path.exists(csv_filename):
                print(f"⚠️ Missing CSV: {csv_filename}")
                continue

            try:
                df = pd.read_csv(csv_filename)
            except pd.errors.EmptyDataError:
                print(f"⚠️ Empty CSV skipped: {csv_filename}")
                continue

            # Impute missing consumption with district mean to handle missing data gracefully
            if df["consumption_kwh"].isna().sum() > 0:
                mean_value = df["consumption_kwh"].mean()
                df["consumption_kwh"].fillna(mean_value, inplace=True)

            # Add metadata columns for city, district, and threshold
            df["city"] = city
            df["district_id"] = district_id
            df["threshold"] = threshold
            df["critical_hours"] = [critical_hours] * len(df)
            all_data.append(df)

    if not all_data:
        raise ValueError("No data found. Please run data generation first.")
    return pd.concat(all_data, ignore_index=True)


# =========================
# 3. DATA ANALYSIS
# =========================
def analyze_data(df, output_dir="output"):
    """
    Perform district-level aggregations, compute violation ratio, risk scores,
    and generate CSV + JSON reports.

    Returns:
        pandas.DataFrame: Aggregated district-level results.
    """
    os.makedirs(f"{output_dir}/summary_csv", exist_ok=True)
    os.makedirs(f"{output_dir}/reports_json", exist_ok=True)

    results = []
    city_reports = {}

    # Extract hour from timestamp and check threshold violations
    df["hour"] = pd.to_datetime(df["timestamp"]).dt.hour
    df["violation"] = df["consumption_kwh"] > df["threshold"]

    # Loop through each (city, district, date) group to compute stats
    for (city, district_id, date), group in df.groupby(["city", "district_id", df["timestamp"].str[:10]]):
        # Calculate consumption stats
        avg_cons = group["consumption_kwh"].mean()
        min_cons = group["consumption_kwh"].min()
        max_cons = group["consumption_kwh"].max()

        # Determine peak hour (hour with highest total consumption)
        peak_hour = group.groupby("hour")["consumption_kwh"].sum().idxmax()
        peak_hour_str = f"{peak_hour:02d}:00"
        critical_hours = group["critical_hours"].iloc[0]
        peak_hour_risk = 1 if peak_hour_str in critical_hours else 0

        # Count violations and calculate violation ratio
        violations = group["violation"].sum()
        total = len(group)
        violation_ratio = violations / total

        # Risk score calculation (only if district is at risk)
        if violation_ratio >= 0.25 or peak_hour_risk == 1:
            risk_score = round((0.6 * violation_ratio) + (0.4 * peak_hour_risk), 2)
        else:
            risk_score = 0

        # Assign risk level based on score
        if risk_score == 0:
            risk_level = "NO RISK"
        elif risk_score <= 0.30:
            risk_level = "LOW"
        elif risk_score <= 0.60:
            risk_level = "MEDIUM"
        else:
            risk_level = "HIGH"

        # Append result for summary CSV
        results.append([city, district_id, date, avg_cons, min_cons, max_cons, peak_hour_str,
                        violations, violation_ratio, risk_score, risk_level])

        # Prepare data for JSON alerts
        city_reports.setdefault((city, date), []).append({
            "district_id": district_id,
            "Avg % of violations per day": f"{violation_ratio * 100:.1f}%",
            "risk_score": risk_score,
            "risk_level": risk_level
        })

    results_df = pd.DataFrame(results, columns=[
        "city", "district_id", "date", "avg_consumption", "min_consumption", "max_consumption",
        "peak_hour", "violations", "violation_ratio", "risk_score", "risk_level"
    ])

    # Save per-city summary CSVs
    for city, city_group in results_df.groupby("city"):
        city_group.to_csv(f"{output_dir}/summary_csv/{city}_summary.csv", index=False)

    # Save per-city JSON reports
    for (city, date), districts in city_reports.items():
        high = sum(1 for d in districts if d["risk_level"] == "HIGH")
        med = sum(1 for d in districts if d["risk_level"] == "MEDIUM")
        low = sum(1 for d in districts if d["risk_level"] == "LOW")

        report = {
            "city": city,
            "date": date,
            "summary": {
                "total_districts": len(districts),
                "high_risk_districts": high,
                "medium_risk_districts": med,
                "low_risk_districts": low
            },
            "critical_alerts": [d for d in districts if d["risk_score"] > 0]
        }

        with open(f"{output_dir}/reports_json/{city}_{date}_report.json", "w") as f:
            json.dump(report, f, indent=4)

    return results_df


# =========================
# 4. VISUALIZATION
# =========================
def visualize_results(results_df, df, output_dir="output/plots"):
    """
    Generate:
    1. Bar chart of risk level distribution per city.
    2. Line chart of hourly consumption per district with peak hour highlighted.
    """
    os.makedirs(output_dir, exist_ok=True)

    # Risk Level Distribution per city
    for city, group in results_df.groupby("city"):
        plt.figure(figsize=(6, 4))
        group["risk_level"].value_counts().reindex(["NO RISK", "LOW", "MEDIUM", "HIGH"], fill_value=0).plot(
            kind="bar", color=["gray", "yellowgreen", "orange", "red"], edgecolor="black"
        )
        plt.title(f"Risk Level Distribution - {city}")
        plt.ylabel("Number of Districts")
        plt.xticks(rotation=30)
        plt.tight_layout()
        plt.savefig(f"{output_dir}/{city}_risk_levels.png")
        plt.close()

    # Hourly consumption trend for each district
    for (city, district_id, date), group in df.groupby(["city", "district_id", df["timestamp"].str[:10]]):
        plt.figure(figsize=(8, 4))
        hourly_sum = group.groupby("hour")["consumption_kwh"].sum()
        peak_hour = hourly_sum.idxmax()

        plt.plot(hourly_sum.index, hourly_sum.values, marker="o", label="Total Consumption")
        plt.axvline(peak_hour, color="red", linestyle="--", label=f"Peak Hour {peak_hour}:00")
        plt.title(f"Hourly Consumption Trend - {city} District {district_id} ({date})")
        plt.xlabel("Hour of Day")
        plt.ylabel("Total Consumption (kWh)")
        plt.legend()
        plt.grid(alpha=0.3)
        plt.tight_layout()
        plt.savefig(f"{output_dir}/{city}_{district_id}_{date}_trend.png")
        plt.close()


# =========================
# MAIN DRIVER
# =========================
if __name__ == "__main__":
    try:
        print("🔄 Step 1: Generating synthetic data...")
        generate_sample_data()

        print("📥 Step 2: Loading and merging data...")
        data = load_and_merge_data()
        print(f"✅ Loaded {len(data)} rows of consumption data.")

        print("📊 Step 3: Running analysis...")
        summary = analyze_data(data)

        print("📈 Step 4: Generating visualizations...")
        visualize_results(summary, data)

        print("✅ All done! Check the 'output/' folder for CSV, JSON, and plots.")
        print(summary.head())

    except Exception as e:
        print(f"❌ ERROR: {e}")




