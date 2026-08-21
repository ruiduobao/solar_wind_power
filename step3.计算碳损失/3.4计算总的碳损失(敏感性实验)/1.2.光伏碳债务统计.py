"""
Statistical analysis of solar carbon debt (2017 and later)
Author: 锐多宝 (Trae AI)
Date: 2026-01-27

Functions:
1. Read the merged solar total carbon debt results table.
2. Filter solar sites built in 2017 and later.
3. Compute totals, country rankings, annual trends, component contributions and distribution characteristics.
4. Output charts and corresponding data tables.
5. Map distribution, latitude-band analysis and resource mismatch chart (combined with power potential and grid factors).
"""

import os  # File path operations
import pandas as pd  # Tabular data processing
import numpy as np  # Numerical computation
import matplotlib.pyplot as plt  # Plotting
import seaborn as sns  # Statistical plotting
from datetime import datetime  # Timestamp
import geopandas as gpd  # Map plotting
from matplotlib.colors import LogNorm  # Log color scale

# ================= Configuration =================

# Base path
BASE_INPUT_DIR = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\4.4.1光伏碳债务合并损失"
POWER_CSV = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\3.发电潜力计算\Solar_Power_Potential.csv"  # Location and potential data

try:
    WORLD_SHP = gpd.datasets.get_path('naturalearth_lowres')  # World vector
except Exception:
    WORLD_SHP = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\3.发电潜力计算\ne_110m_admin_0_countries\ne_110m_admin_0_countries.shp"  # Fallback

START_YEAR = 2017  # Statistics start year
END_YEAR = 2024  # Statistics end year

# Plot style settings
sns.set_theme(style="ticks", font="Arial", context="paper")  # Set seaborn style
plt.rcParams["figure.dpi"] = 300  # Figure resolution
plt.rcParams["savefig.dpi"] = 300  # Save resolution
plt.rcParams["axes.grid"] = True  # Show grid
plt.rcParams["grid.alpha"] = 0.3  # Grid transparency
plt.rcParams["font.sans-serif"] = ["Arial", "SimHei"]  # Font settings
plt.rcParams["axes.unicode_minus"] = False  # Minus sign display

# ================= Utility functions =================

def ensure_dir(path):  # Create directory
    if not os.path.exists(path):  # Check if directory exists
        os.makedirs(path)  # Create directory

def log_message(message, log_path=None):  # Write log
    time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Current time
    full_message = f"[{time_str}] {message}"  # Compose log message
    print(full_message)  # Print to terminal
    if log_path:
        with open(log_path, "a", encoding="utf-8") as f:  # Open log file
            f.write(full_message + "\n")  # Write log message

def export_plot_data(df, filename, output_dir, log_path=None):  # Export chart data
    csv_path = os.path.join(output_dir, filename.replace(".png", ".csv"))  # Output path
    df.to_csv(csv_path, index=True, encoding="utf-8-sig")  # Save CSV
    log_message(f"Chart data exported: {csv_path}", log_path)  # Log export info

def check_required_columns(df, cols, table_name, log_path=None):  # Check required columns
    missing = [c for c in cols if c not in df.columns]  # List of missing columns
    if missing:  # If any are missing
        log_message(f"{table_name} missing columns: {missing}", log_path)  # Output log
        return False  # Return failure
    return True  # Return success

# ================= Data loading =================

def load_data(input_csv, log_path=None):  # Load data
    if not os.path.exists(input_csv):  # Check if input file exists
        log_message(f"Error: input file not found {input_csv}", log_path)  # Output error
        return None  # Return empty
    df = pd.read_csv(input_csv)  # Read input table
    log_message(f"Number of records read: {len(df)}", log_path)  # Output record count
    required_ok = check_required_columns(df, ["fid", "Total_Debt_tCO2"], "Total carbon debt table", log_path)  # Check required columns
    if not required_ok:  # If required columns are missing
        return None  # Return empty
    if "installation_year" not in df.columns and "year" in df.columns:  # If installation_year is missing
        df["installation_year"] = df["year"]  # Use year as substitute
    if "installation_year" not in df.columns:  # If the year column still does not exist
        log_message("Error: missing installation_year/year field, cannot filter by year", log_path)  # Output error
        return None  # Return empty
    df["installation_year"] = pd.to_numeric(df["installation_year"], errors="coerce")  # Convert to numeric
    df = df[df["installation_year"].notna()].copy()  # Drop records without year
    df["installation_year"] = df["installation_year"].astype(int)  # Convert to integer
    return df  # Return data

def load_power_df(log_path=None):  # Load power potential and location data
    if not os.path.exists(POWER_CSV):  # Check if file exists
        log_message(f"Warning: potential file not found {POWER_CSV}, map and mismatch analysis will be skipped.", log_path)  # Output warning
        return None  # Return empty
    cols = ["fid", "lon", "lat", "country", "pvout_daily_kwh_kwp", "grid_ef", "capacity_mw_est", "avoided_co2_ton", "annual_gen_mwh"]  # Selected columns
    df = pd.read_csv(POWER_CSV)  # Read
    for c in cols:  # Check columns
        if c not in df.columns:  # If missing
            log_message(f"Warning: potential table missing column {c}, subsequent analysis may be limited.", log_path)  # Notify
    return df[ [c for c in cols if c in df.columns] ]  # Return trimmed columns

# ================= Plotting functions =================

def plot_country_ranking(df, output_dir, log_path=None):  # Country ranking
    log_message("Plotting 1. Country carbon debt ranking...", log_path)  # Log progress
    if "country_final" not in df.columns:  # Check country field
        df["country_final"] = "Unknown"  # Fill with Unknown if missing
    cnt_stats = df.groupby("country_final")["Total_Debt_tCO2"].sum().sort_values(ascending=False).head(20)  # Compute ranking
    cnt_stats_mt = cnt_stats / 1e6  # Convert to MtCO2e
    plt.figure(figsize=(12, 7))  # Canvas size
    sns.barplot(x=cnt_stats_mt.values, y=cnt_stats_mt.index, palette="Oranges_r")  # Draw bar plot
    plt.title("Top 20 Countries by Solar Carbon Debt (2017+)", fontsize=16, fontweight="bold")  # Title
    plt.xlabel("Total Carbon Debt (MtCO2e)", fontsize=12)  # X axis
    plt.ylabel("")  # Y axis
    for i, v in enumerate(cnt_stats_mt.values):  # Add labels
        plt.text(v + v * 0.01, i, f"{v:.2f}", va="center", fontsize=10)  # Value annotation
    filename = "1_Bar_Country_TotalDebt_2017plus.png"  # Output figure name
    plt.savefig(os.path.join(output_dir, filename))  # Save figure
    plt.close()  # Close figure
    export_plot_data(cnt_stats_mt, filename, output_dir, log_path)  # Export chart data

def plot_annual_trend(df, output_dir, log_path=None):  # Annual trend
    log_message("Plotting 2. Annual carbon debt trend...", log_path)  # Log progress
    trend_df = df[(df["installation_year"] >= START_YEAR) & (df["installation_year"] <= END_YEAR)]  # Filter by year
    yr_stats = trend_df.groupby("installation_year")["Total_Debt_tCO2"].sum() / 1e6  # Aggregate by year
    plt.figure(figsize=(12, 6))  # Canvas size
    plt.bar(yr_stats.index, yr_stats.values, color="#ff7f0e", alpha=0.7)  # Bar plot
    plt.title("Annual Solar Carbon Debt (2017-2024)", fontsize=16, fontweight="bold")  # Title
    plt.xlabel("Year", fontsize=12)  # X axis
    plt.ylabel("Annual Carbon Debt (MtCO2e)", fontsize=12)  # Y axis
    plt.grid(axis="y", alpha=0.3)  # Grid
    filename = "2_Bar_Annual_TotalDebt_2017_2024.png"  # Output figure name
    plt.savefig(os.path.join(output_dir, filename))  # Save figure
    plt.close()  # Close figure
    export_plot_data(yr_stats, filename, output_dir, log_path)  # Export chart data

def plot_component_pie(df, output_dir, log_path=None):  # Component contribution pie chart
    log_message("Plotting 3. Carbon debt component contributions...", log_path)  # Log progress
    if "Loss_Bio_tCO2" not in df.columns:  # Check biomass CO2 field
        df["Loss_Bio_tCO2"] = 0  # Set to 0 if missing
    if "Loss_Soil_tCO2" not in df.columns:  # Check soil CO2 field
        df["Loss_Soil_tCO2"] = 0  # Set to 0 if missing
    if "Loss_Mfg_tCO2" not in df.columns:  # Check manufacturing carbon field
        df["Loss_Mfg_tCO2"] = 0  # Set to 0 if missing
    sums = [df["Loss_Bio_tCO2"].sum(), df["Loss_Soil_tCO2"].sum(), df["Loss_Mfg_tCO2"].sum()]  # Compute sums
    labels = ["Biomass CO2e", "Soil CO2e", "Manufacturing CO2e"]  # Labels
    plt.figure(figsize=(8, 8))  # Canvas size
    plt.pie(sums, labels=labels, autopct="%1.1f%%", startangle=90, colors=["#d62728", "#8c564b", "#1f77b4"])  # Pie chart
    plt.title("Composition of Solar Carbon Debt (2017+)", fontsize=16, fontweight="bold")  # Title
    filename = "3_Pie_Component_Contribution_2017plus.png"  # Output figure name
    plt.savefig(os.path.join(output_dir, filename))  # Save figure
    plt.close()  # Close figure
    export_plot_data(pd.Series(sums, index=labels), filename, output_dir, log_path)  # Export chart data

def plot_component_trend(df, output_dir, log_path=None):  # Component annual trend
    log_message("Plotting 4. Component annual trend...", log_path)  # Log progress
    trend_df = df[(df["installation_year"] >= START_YEAR) & (df["installation_year"] <= END_YEAR)]  # Filter by year
    comp_df = trend_df.groupby("installation_year")[["Loss_Bio_tCO2", "Loss_Soil_tCO2", "Loss_Mfg_tCO2"]].sum() / 1e6  # Aggregate
    comp_df = comp_df.fillna(0)  # Fill missing with 0
    comp_df.plot(kind="bar", stacked=True, figsize=(12, 6), color=["#d62728", "#8c564b", "#1f77b4"])  # Stacked bar plot
    plt.title("Annual Component Breakdown of Solar Carbon Debt (2017-2024)", fontsize=16, fontweight="bold")  # Title
    plt.xlabel("Year", fontsize=12)  # X axis
    plt.ylabel("Annual Carbon Debt (MtCO2e)", fontsize=12)  # Y axis
    plt.legend(["Biomass CO2e", "Soil CO2e", "Manufacturing CO2e"])  # Legend
    plt.grid(axis="y", alpha=0.3)  # Grid
    filename = "4_Stacked_Annual_Component_2017_2024.png"  # Output figure name
    plt.savefig(os.path.join(output_dir, filename))  # Save figure
    plt.close()  # Close figure
    export_plot_data(comp_df, filename, output_dir, log_path)  # Export chart data

def plot_debt_distribution(df, output_dir, log_path=None):  # Carbon debt distribution
    log_message("Plotting 5. Per-site carbon debt distribution...", log_path)  # Log progress
    plot_df = df[df["Total_Debt_tCO2"] > 0].copy()  # Filter out invalid data
    plot_df["Log_Total_Debt"] = np.log10(plot_df["Total_Debt_tCO2"])  # Take logarithm
    plt.figure(figsize=(10, 6))  # Canvas size
    sns.histplot(plot_df["Log_Total_Debt"], bins=50, kde=True, color="#ff7f0e")  # Distribution plot
    plt.title("Distribution of Solar Carbon Debt per Site (Log10)", fontsize=16, fontweight="bold")  # Title
    plt.xlabel("Log10(Total Debt tCO2e)", fontsize=12)  # X axis
    plt.ylabel("Count of Solar Sites", fontsize=12)  # Y axis
    filename = "5_Hist_Debt_Distribution_Log10.png"  # Output figure name
    plt.savefig(os.path.join(output_dir, filename))  # Save figure
    plt.close()  # Close figure
    export_plot_data(plot_df["Log_Total_Debt"].describe(), filename, output_dir, log_path)  # Export chart data

def plot_debt_map(df, power_df, output_dir, log_path=None):  # Carbon debt map distribution
    log_message("Plotting 6. Global carbon debt spatial distribution map...", log_path)  # Log progress
    if power_df is None:  # If no potential data
        log_message("Skipped: potential data missing, cannot plot map.", log_path)  # Notify
        return  # Return
    df_m = df.merge(power_df[["fid", "lon", "lat"]], on="fid", how="left")  # Merge lon/lat
    df_m = df_m[df_m["Total_Debt_tCO2"] > 0]  # Filter valid records
    df_m = df_m.dropna(subset=["lon", "lat"])  # Drop records without coordinates
    try:
        world = gpd.read_file(WORLD_SHP)  # Read world map
    except Exception:
        world = None  # No world map
    fig, ax = plt.subplots(figsize=(15, 8))  # Canvas
    if world is not None:  # Draw base map
        world.plot(ax=ax, color="#f0f0f0", edgecolor="white")  # World base map
    sc = ax.scatter(  # Scatter plot
        df_m["lon"], df_m["lat"],  # Coordinates
        c=df_m["Total_Debt_tCO2"],  # Color by carbon debt
        s=(df_m["Total_Debt_tCO2"] / df_m["Total_Debt_tCO2"].max()) * 50 + 2,  # Point size
        cmap="Reds",  # Color map
        norm=LogNorm(vmin=max(df_m["Total_Debt_tCO2"].quantile(0.05), 1e-6), vmax=df_m["Total_Debt_tCO2"].quantile(0.99)),  # Log color scale
        alpha=0.85,  # Transparency
        edgecolors="none"  # Edges
    )  # End of plotting
    plt.colorbar(sc, label="Total Carbon Debt (tCO2e)", fraction=0.02, pad=0.04)  # Color bar
    plt.title("Global Distribution of Solar Carbon Debt (2017+)", fontsize=16, fontweight="bold")  # Title
    plt.axis("off")  # Turn off axes
    filename = "6_Map_Solar_Carbon_Debt_2017plus.png"  # File name
    plt.savefig(os.path.join(output_dir, filename))  # Save figure
    plt.close()  # Close figure
    export_plot_data(df_m[["fid", "lon", "lat", "Total_Debt_tCO2"]], filename, output_dir, log_path)  # Export data

def plot_latitude_band(df, power_df, output_dir, log_path=None):  # Latitude band analysis
    log_message("Plotting 7. Latitude band carbon debt statistics...", log_path)  # Log progress
    if power_df is None:  # If no potential data
        log_message("Skipped: potential data missing, cannot compute latitude bands.", log_path)  # Notify
        return  # Return
    df_m = df.merge(power_df[["fid", "lat"]], on="fid", how="left")  # Merge latitude
    df_m = df_m.dropna(subset=["lat"])  # Drop records without latitude
    bins = list(range(-60, 95, 5))  # 5-degree bins
    df_m["lat_bin"] = pd.cut(df_m["lat"], bins=bins)  # Bin
    band_stats = df_m.groupby("lat_bin")["Total_Debt_tCO2"].sum() / 1e6  # MtCO2e
    band_stats = band_stats[band_stats > 0]  # Filter empty bins
    plt.figure(figsize=(12, 6))  # Canvas
    sns.barplot(x=band_stats.index.astype(str), y=band_stats.values, color="#ff7f0e")  # Bar plot
    plt.xticks(rotation=90)  # Rotate X ticks
    plt.title("Solar Carbon Debt by Latitude Band (2017+)", fontsize=16, fontweight="bold")  # Title
    plt.xlabel("Latitude Band (deg)")  # X axis
    plt.ylabel("Total Carbon Debt (MtCO2e)")  # Y axis
    filename = "7_Bar_Latitude_Band_TotalDebt_2017plus.png"  # Output name
    plt.tight_layout()  # Compact layout
    plt.savefig(os.path.join(output_dir, filename))  # Save figure
    plt.close()  # Close
    export_plot_data(band_stats, filename, output_dir, log_path)  # Export data

def plot_resource_mismatch(df, power_df, output_dir, log_path=None):  # Resource mismatch chart
    log_message("Plotting 8. Resource-grid-carbon debt mismatch chart...", log_path)  # Log progress
    if power_df is None:  # If no potential data
        log_message("Skipped: potential data missing, cannot plot mismatch chart.", log_path)  # Notify
        return  # Return
    cols = ["fid", "pvout_daily_kwh_kwp", "grid_ef", "capacity_mw_est", "avoided_co2_ton"]  # Required columns
    df_p = power_df[[c for c in cols if c in power_df.columns]].copy()  # Trim
    df_m = df.merge(df_p, on="fid", how="left")  # Merge
    df_m["capacity_mw_est"] = pd.to_numeric(df_m["capacity_mw_est"], errors="coerce")  # Convert to numeric
    df_m["pvout_daily_kwh_kwp"] = pd.to_numeric(df_m["pvout_daily_kwh_kwp"], errors="coerce")  # Convert to numeric
    df_m["grid_ef"] = pd.to_numeric(df_m["grid_ef"], errors="coerce")  # Convert to numeric
    df_m = df_m.dropna(subset=["pvout_daily_kwh_kwp", "grid_ef", "capacity_mw_est"])  # Drop records with missing values
    df_m = df_m[df_m["capacity_mw_est"] > 0]  # Filter out zero capacity
    df_m["Debt_Intensity_tCO2_MW"] = df_m["Total_Debt_tCO2"] / df_m["capacity_mw_est"]  # Intensity
    df_m["BubbleSize"] = (df_m["capacity_mw_est"] / df_m["capacity_mw_est"].max()) * 300 + 10  # Bubble size
    plt.figure(figsize=(12, 8))  # Canvas
    sc = plt.scatter(  # Scatter
        df_m["grid_ef"], df_m["pvout_daily_kwh_kwp"],  # Axes
        c=df_m["Debt_Intensity_tCO2_MW"],  # Color by intensity
        s=df_m["BubbleSize"],  # Size by capacity
        cmap="viridis",  # Color map
        alpha=0.8,  # Transparency
        edgecolors="k", linewidths=0.2  # Edges
    )  # End of plotting
    plt.colorbar(sc, label="Carbon Debt Intensity (tCO2e/MW)")  # Color bar
    plt.title("Resource-Grid Mismatch vs Carbon Debt Intensity (2017+)", fontsize=16, fontweight="bold")  # Title
    plt.xlabel("Grid Emission Factor (tCO2/MWh)")  # X axis
    plt.ylabel("PVOUT (kWh/kWp/day)")  # Y axis
    filename = "8_Scatter_Resource_Mismatch_CarbonIntensity_2017plus.png"  # Output name
    plt.savefig(os.path.join(output_dir, filename))  # Save figure
    plt.close()  # Close
    export_plot_data(df_m[["fid", "grid_ef", "pvout_daily_kwh_kwp", "capacity_mw_est", "Debt_Intensity_tCO2_MW"]], filename, output_dir, log_path)  # Export data

# ================= Main program =================

def process_scenario(scenario_name):
    """
    Compute carbon debt statistics for a single scenario
    """
    print(f"\n>>> Start processing statistics for scenario: {scenario_name}")
    
    # Path settings
    input_csv = os.path.join(BASE_INPUT_DIR, scenario_name, "Solar_Total_Carbon_Debt_Result.csv")
    output_dir = os.path.join(BASE_INPUT_DIR, scenario_name)  # Output to the same directory
    ensure_dir(output_dir)
    log_path = os.path.join(output_dir, "Solar_Debt_Stats_2017plus_Log.txt")
    
    if os.path.exists(log_path):
        os.remove(log_path)
    
    log_message(f"Scenario: {scenario_name}", log_path)
    log_message(f"Input file: {input_csv}", log_path)

    # Load data
    df = load_data(input_csv, log_path)
    if df is None or df.empty:
        log_message("Data is empty, skipping this scenario.", log_path)
        return

    # Filter by year
    df = df[df["installation_year"] >= START_YEAR].copy()
    log_message(f"Records from 2017 and later: {len(df)}", log_path)
    
    # Data preprocessing
    df["Total_Debt_tCO2"] = df["Total_Debt_tCO2"].fillna(0)
    if "Loss_Bio_tCO2" not in df.columns and "Loss_Bio_tC" in df.columns:
        df["Loss_Bio_tCO2"] = df["Loss_Bio_tC"] * 3.67
    if "Loss_Soil_tCO2" not in df.columns and "Loss_Soil_tC" in df.columns:
        df["Loss_Soil_tCO2"] = df["Loss_Soil_tC"] * 3.67
        
    total_debt_mt = df["Total_Debt_tCO2"].sum() / 1e6
    log_message(f"Total solar carbon debt from 2017 and later: {total_debt_mt:.4f} MtCO2e", log_path)

    # Plotting
    plot_country_ranking(df, output_dir, log_path)
    plot_annual_trend(df, output_dir, log_path)
    plot_component_pie(df, output_dir, log_path)
    plot_component_trend(df, output_dir, log_path)
    plot_debt_distribution(df, output_dir, log_path)
    
    power_df = load_power_df(log_path)
    plot_debt_map(df, power_df, output_dir, log_path)
    plot_latitude_band(df, power_df, output_dir, log_path)
    plot_resource_mismatch(df, power_df, output_dir, log_path)
    
    log_message("All charts and data have been generated.", log_path)

def main():
    scenarios = ["乐观场景", "标准场景", "悲观场景"]
    for scenario in scenarios:
        process_scenario(scenario)

if __name__ == "__main__":
    main()
