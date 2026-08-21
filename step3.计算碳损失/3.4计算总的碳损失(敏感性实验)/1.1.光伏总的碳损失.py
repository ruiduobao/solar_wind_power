"""
Solar total carbon debt aggregation and computation (Solar Total Carbon Debt Aggregation)
Author: 锐多宝 (Trae AI)
Date: 2026-01-27

Function:
1. Read the solar soil carbon loss result (Solar_Soil_Loss_Result.csv).
2. Read the solar aboveground biomass carbon loss result (Solar_Biomass_Loss_Result.csv).
3. Read the solar manufacturing carbon loss result (Solar_Manufacturing_Carbon_Result.csv).
4. Merge the three carbon loss tables using fid as the key.
5. Compute the total carbon debt (tCO2e) with the formula Total_Debt = (E_Bio + E_Soil) * 3.67 + E_Mfg.
6. Output the merged result table and a field description file.
"""

import os  # Handle file paths
import pandas as pd  # Tabular processing
import numpy as np  # Numerical computation
from datetime import datetime  # Timestamps

# ================= Configuration =================

# Base paths
BASE_SOIL_DIR = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\4.1.1光伏土壤碳损失"
BASE_BIO_DIR = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\4.2.1光伏生物碳损失"
BASE_MFG_DIR = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\4.3.1光伏制造碳损失"

# Output base directory
BASE_OUTPUT_DIR = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\4.4.1光伏碳债务合并损失"

CO2_CONVERSION = 3.67  # C -> CO2 conversion factor

# ================= Utility functions =================

def ensure_dir(path):  # Create the output directory
    if not os.path.exists(path):  # Check whether the directory exists
        os.makedirs(path)  # Create the directory

def log_message(message, log_path):  # Output to both the terminal and the log file
    time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Current time
    full_message = f"[{time_str}] {message}"  # Compose the log content
    print(full_message)  # Terminal output
    with open(log_path, "a", encoding="utf-8") as f:  # Open the log file
        f.write(full_message + "\n")  # Write the log

def check_required_columns(df, required_cols, log_path, table_name):  # Check required columns
    missing = [c for c in required_cols if c not in df.columns]  # List of missing columns
    if missing:  # If there are missing columns
        log_message(f"{table_name} missing columns: {missing}", log_path)  # Output the error message
        return False  # Return failure
    return True  # Return success

# ================= Main flow =================

def process_scenario(scenario_name):
    """
    Process the carbon loss computation for a single scenario
    """
    print(f"\n>>> Processing scenario: {scenario_name}")
    
    # Build the input paths
    soil_csv = os.path.join(BASE_SOIL_DIR, scenario_name, "Solar_Soil_Loss_Result.csv")
    bio_csv = os.path.join(BASE_BIO_DIR, scenario_name, "Solar_Biomass_Loss_Result.csv")
    mfg_csv = os.path.join(BASE_MFG_DIR, scenario_name, "Solar_Manufacturing_Carbon_Result.csv")
    
    # Build the output paths
    output_dir = os.path.join(BASE_OUTPUT_DIR, scenario_name)
    ensure_dir(output_dir)
    
    output_csv = os.path.join(output_dir, "Solar_Total_Carbon_Debt_Result.csv")
    output_desc = os.path.join(output_dir, "Solar_Total_Carbon_Debt_Field_Description.csv")
    output_log = os.path.join(output_dir, "Solar_Total_Carbon_Debt_Run_Log.txt")
    
    if os.path.exists(output_log):
        os.remove(output_log)
    
    log_message(f"Scenario: {scenario_name}", output_log)

    # 1. Read the soil carbon loss
    if not os.path.exists(soil_csv):
        log_message(f"Error: soil carbon loss file not found: {soil_csv}", output_log)
        return
    soil_df = pd.read_csv(soil_csv)
    log_message(f"Soil carbon loss records: {len(soil_df)}", output_log)

    # 2. Read the biomass carbon loss
    if not os.path.exists(bio_csv):
        log_message(f"Error: biomass carbon loss file not found: {bio_csv}", output_log)
        return
    bio_df = pd.read_csv(bio_csv)
    log_message(f"Biomass carbon loss records: {len(bio_df)}", output_log)

    # 3. Read the manufacturing carbon loss
    if not os.path.exists(mfg_csv):
        log_message(f"Error: manufacturing carbon loss file not found: {mfg_csv}", output_log)
        return
    mfg_df = pd.read_csv(mfg_csv)
    log_message(f"Manufacturing carbon loss records: {len(mfg_df)}", output_log)

    # 4. Validate the required fields
    soil_ok = check_required_columns(soil_df, ["fid", "Loss_Soil_tC"], output_log, "soil carbon loss table")
    bio_ok = check_required_columns(bio_df, ["fid", "Loss_Bio_tC"], output_log, "biomass carbon loss table")
    mfg_ok = check_required_columns(mfg_df, ["fid", "Loss_Mfg_tCO2"], output_log, "manufacturing carbon loss table")
    if not (soil_ok and bio_ok and mfg_ok):
        log_message("Field validation failed; the program is terminated.", output_log)
        return

    # 5. Unify the fid types
    soil_df["fid"] = soil_df["fid"].astype(int)
    bio_df["fid"] = bio_df["fid"].astype(int)
    mfg_df["fid"] = mfg_df["fid"].astype(int)

    # 6. Select the output fields and rename
    soil_keep = ["fid", "Loss_Soil_tC"]
    if "installation_year" in soil_df.columns:
        soil_keep.append("installation_year")
    if "country_iso_a3" in soil_df.columns:
        soil_keep.append("country_iso_a3")
    soil_df = soil_df[soil_keep]

    bio_keep = ["fid", "Loss_Bio_tC"]
    if "installation_year" in bio_df.columns:
        bio_keep.append("installation_year")
    if "country" in bio_df.columns:
        bio_keep.append("country")
    bio_df = bio_df[bio_keep]

    mfg_keep = ["fid", "Loss_Mfg_tCO2"]
    if "year" in mfg_df.columns:
        mfg_keep.append("year")
    if "country" in mfg_df.columns:
        mfg_keep.append("country")
    if "Rated_Power_MW" in mfg_df.columns:
        mfg_keep.append("Rated_Power_MW")
    mfg_df = mfg_df[mfg_keep]

    # 7. Merge the data
    log_message("Starting to merge the three carbon loss tables ...", output_log)
    merged_df = pd.merge(soil_df, bio_df, on="fid", how="outer", suffixes=("_soil", "_bio"))
    merged_df = pd.merge(merged_df, mfg_df, on="fid", how="outer")
    log_message(f"Records after merge: {len(merged_df)}", output_log)

    # 8. Unify the year and country fields
    if "installation_year_soil" in merged_df.columns and "installation_year_bio" in merged_df.columns:
        merged_df["installation_year"] = merged_df["installation_year_bio"].fillna(merged_df["installation_year_soil"])
    elif "installation_year_bio" in merged_df.columns:
        merged_df["installation_year"] = merged_df["installation_year_bio"]
    elif "installation_year_soil" in merged_df.columns:
        merged_df["installation_year"] = merged_df["installation_year_soil"]
    elif "year" in merged_df.columns:
        merged_df["installation_year"] = merged_df["year"]

    if "country" in merged_df.columns and "country_iso_a3" in merged_df.columns:
        merged_df["country_final"] = merged_df["country"].fillna(merged_df["country_iso_a3"])
    elif "country" in merged_df.columns:
        merged_df["country_final"] = merged_df["country"]
    elif "country_iso_a3" in merged_df.columns:
        merged_df["country_final"] = merged_df["country_iso_a3"]

    # 9. Handle missing values
    merged_df["Loss_Bio_tC"] = merged_df["Loss_Bio_tC"].fillna(0)
    merged_df["Loss_Soil_tC"] = merged_df["Loss_Soil_tC"].fillna(0)
    merged_df["Loss_Mfg_tCO2"] = merged_df["Loss_Mfg_tCO2"].fillna(0)

    # 10. Compute CO2e
    merged_df["Loss_Bio_tCO2"] = merged_df["Loss_Bio_tC"] * CO2_CONVERSION
    merged_df["Loss_Soil_tCO2"] = merged_df["Loss_Soil_tC"] * CO2_CONVERSION
    merged_df["Total_Debt_tCO2"] = merged_df["Loss_Bio_tCO2"] + merged_df["Loss_Soil_tCO2"] + merged_df["Loss_Mfg_tCO2"]

    # 11. Output the results
    output_cols = [
        "fid",
        "country_final",
        "installation_year",
        "Loss_Bio_tC",
        "Loss_Soil_tC",
        "Loss_Mfg_tCO2",
        "Loss_Bio_tCO2",
        "Loss_Soil_tCO2",
        "Total_Debt_tCO2"
    ]
    output_cols = [c for c in output_cols if c in merged_df.columns]
    merged_df[output_cols].to_csv(output_csv, index=False, encoding="utf-8-sig")
    log_message(f"Results exported: {output_csv}", output_log)

    # 12. Output the field description file
    desc_rows = [
        {"Field": "fid", "Description": "Unique ID of the solar farm site", "Unit": ""},
        {"Field": "country_final", "Description": "Country name or country code (country preferred)", "Unit": ""},
        {"Field": "installation_year", "Description": "Construction year (merged from soil/biomass/manufacturing)", "Unit": "year"},
        {"Field": "Loss_Bio_tC", "Description": "Biomass carbon loss", "Unit": "tC"},
        {"Field": "Loss_Soil_tC", "Description": "Soil organic carbon loss", "Unit": "tC"},
        {"Field": "Loss_Mfg_tCO2", "Description": "Manufacturing carbon emissions", "Unit": "tCO2e"},
        {"Field": "Loss_Bio_tCO2", "Description": "Biomass carbon converted to CO2 equivalent (tC * 3.67)", "Unit": "tCO2e"},
        {"Field": "Loss_Soil_tCO2", "Description": "Soil carbon converted to CO2 equivalent (tC * 3.67)", "Unit": "tCO2e"},
        {"Field": "Total_Debt_tCO2", "Description": "Total carbon debt = biomass CO2e + soil CO2e + manufacturing carbon", "Unit": "tCO2e"}
    ]
    desc_df = pd.DataFrame(desc_rows)
    desc_df.to_csv(output_desc, index=False, encoding="utf-8-sig")
    log_message(f"Field description exported: {output_desc}", output_log)

    # 13. Output the global statistics
    total_debt_mt = merged_df["Total_Debt_tCO2"].sum() / 1e6
    log_message(f"{scenario_name} - Global solar total carbon debt: {total_debt_mt:.4f} MtCO2e", output_log)

def main():
    scenarios = ["乐观场景", "标准场景", "悲观场景"]
    for scenario in scenarios:
        process_scenario(scenario)

if __name__ == "__main__":
    main()
