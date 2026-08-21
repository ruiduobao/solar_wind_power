# -*- coding: utf-8 -*-
"""
Carbon Loss Breakdown by Land Cover Type (Carbon Loss Breakdown by Land Cover Type)

Functions:
Group by the original land cover types occupied by wind/solar power (bareland, cropland, grassland, forest, shrub),
and compute soil carbon loss and biomass carbon loss separately.

Inputs:
- Solar/Wind soil carbon loss results (Solar/Wind_Soil_Loss_Result.csv)
- Solar/Wind biomass carbon loss results (Solar/Wind_Biomass_Loss_Result.csv)

Outputs:
- Carbon loss statistics tables grouped by land cover type (three scenarios)

Scenarios: 乐观场景、标准场景、悲观场景

Author: Claude
Date: 2026-05-12
"""

import os
import pandas as pd
import numpy as np

# ================= Configuration =================

# Base path
BASE_DIR = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图"

SOIL_PV_DIR = os.path.join(BASE_DIR, "4.1.1光伏土壤碳损失")
SOIL_WIND_DIR = os.path.join(BASE_DIR, "4.1.2风电土壤碳损失")
BIO_PV_DIR = os.path.join(BASE_DIR, "4.2.1光伏生物碳损失")
BIO_WIND_DIR = os.path.join(BASE_DIR, "4.2.2风电生物碳损失")

# Output path
OUTPUT_DIR = os.path.join(BASE_DIR, "5.碳损失按土地覆盖类型分解")
SCENARIOS = ["乐观场景", "标准场景", "悲观场景"]

# Land cover types (Chinese-English mapping)
LAND_TYPES = {
    'Trees': '森林',
    'Grass': '草地',
    'Shrub': '灌木',
    'Crops': '农田',
    'Bare': '裸地'
}

CO2_CONVERSION = 3.67  # C -> CO2e

# ================= Utility functions =================

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def load_csv_safe(base_dir, scenario, filename):
    """Safely load CSV, handling path issues"""
    path = os.path.join(base_dir, scenario, filename)
    if os.path.exists(path):
        return pd.read_csv(path)
    return None

# ================= Core statistics functions =================

def breakdown_carbon_by_land_type(solar_soil_df, solar_bio_df, wind_soil_df, wind_bio_df, scenario):
    """
    Break down carbon loss by land cover type

    Parameters:
        solar_soil_df: solar soil carbon loss data (contains Stock_Soil_* columns and K_Poly)
        solar_bio_df: solar biomass carbon loss data (contains Loss_Bio_*_tC columns)
        wind_soil_df: wind soil carbon loss data (contains Stock_Soil_* columns and K_Wind)
        wind_bio_df: wind biomass carbon loss data (contains Loss_Bio_*_tC columns)
        scenario: scenario name

    Outputs:
        Summary DataFrame containing:
        - Energy type (solar/wind)
        - Land cover type
        - Soil carbon loss (tC)
        - Biomass carbon loss (tC)
        - Total carbon loss (tC)
        - Soil carbon loss (tCO2e)
        - Biomass carbon loss (tCO2e)
        - Total carbon loss (tCO2e)
    """

    results = []

    # Land cover type list
    lc_types = ['Trees', 'Grass', 'Shrub', 'Crops', 'Bare']

    # ================= Solar =================
    if solar_soil_df is not None and 'K_Poly' in solar_soil_df.columns:
        k_pv = solar_soil_df['K_Poly'].mean()  # Take the mean disturbance coefficient
    else:
        k_pv = None

    if solar_bio_df is not None:
        # Biomass carbon loss already includes the K factor
        for lc_type in lc_types:
            col = f'Loss_Bio_{lc_type}_tC'
            if col in solar_bio_df.columns:
                loss_bio_tC = solar_bio_df[col].sum()
            else:
                loss_bio_tC = 0.0

            results.append({
                '能源类型': '光伏',
                '土地覆盖类型': lc_type,
                '生物碳损失_tC': loss_bio_tC
            })

    if solar_soil_df is not None:
        # Soil carbon loss = Stock * K_Poly
        if k_pv is None:
            # Compute the mean K from the data
            if 'K_Poly' in solar_soil_df.columns:
                k_pv = solar_soil_df['K_Poly'].replace(0, np.nan).mean()
                if pd.isna(k_pv):
                    k_pv = 0.1  # Default value
            else:
                k_pv = 0.1

        for lc_type in lc_types:
            col = f'Stock_Soil_{lc_type}'
            if col in solar_soil_df.columns:
                stock_soil = solar_soil_df[col].sum()
                loss_soil_tC = stock_soil * k_pv
            else:
                stock_soil = 0.0
                loss_soil_tC = 0.0

            # Find existing results and update the soil carbon loss
            for r in results:
                if r['能源类型'] == '光伏' and r['土地覆盖类型'] == lc_type:
                    r['土壤碳损失_tC'] = loss_soil_tC
                    r['K_PV'] = k_pv
                    break

    # ================= Wind =================
    if wind_soil_df is not None and 'K_Wind' in wind_soil_df.columns:
        k_wind = wind_soil_df['K_Wind'].iloc[0] if len(wind_soil_df) > 0 else 0.1
    else:
        k_wind = None

    if wind_bio_df is not None:
        for lc_type in lc_types:
            col = f'Loss_Bio_{lc_type}_tC'
            if col in wind_bio_df.columns:
                loss_bio_tC = wind_bio_df[col].sum()
            else:
                loss_bio_tC = 0.0

            results.append({
                '能源类型': '风电',
                '土地覆盖类型': lc_type,
                '生物碳损失_tC': loss_bio_tC
            })

    if wind_soil_df is not None:
        if k_wind is None:
            if 'K_Wind' in wind_soil_df.columns:
                k_wind = wind_soil_df['K_Wind'].replace(0, np.nan).mean()
                if pd.isna(k_wind):
                    k_wind = 0.1
            else:
                k_wind = 0.1

        for lc_type in lc_types:
            col = f'Stock_Soil_{lc_type}'
            if col in wind_soil_df.columns:
                stock_soil = wind_soil_df[col].sum()
                loss_soil_tC = stock_soil * k_wind
            else:
                stock_soil = 0.0
                loss_soil_tC = 0.0

            for r in results:
                if r['能源类型'] == '风电' and r['土地覆盖类型'] == lc_type:
                    r['土壤碳损失_tC'] = loss_soil_tC
                    r['K_Wind'] = k_wind
                    break

    # Convert to DataFrame
    df = pd.DataFrame(results)

    # Ensure the columns exist
    for col in ['土壤碳损失_tC', '生物碳损失_tC']:
        if col not in df.columns:
            df[col] = 0.0

    # Compute total carbon loss (tC)
    df['总碳损失_tC'] = df['土壤碳损失_tC'] + df['生物碳损失_tC']

    # Convert to CO2e
    df['土壤碳损失_tCO2e'] = df['土壤碳损失_tC'] * CO2_CONVERSION
    df['生物碳损失_tCO2e'] = df['生物碳损失_tC'] * CO2_CONVERSION
    df['总碳损失_tCO2e'] = df['总碳损失_tC'] * CO2_CONVERSION

    # Add scenario identifier
    df['场景'] = scenario

    return df


def main():
    print("=" * 60)
    print("Carbon loss breakdown by land cover type")
    print("=" * 60)

    all_results = []

    for scenario in SCENARIOS:
        print(f"\n>>> Processing scenario: {scenario}")

        # Read soil carbon loss data
        solar_soil = load_csv_safe(SOIL_PV_DIR, scenario, "Solar_Soil_Loss_Result.csv")
        wind_soil = load_csv_safe(SOIL_WIND_DIR, scenario, "Wind_Soil_Loss_Result.csv")

        # Read biomass carbon loss data
        solar_bio = load_csv_safe(BIO_PV_DIR, scenario, "Solar_Biomass_Loss_Result.csv")
        wind_bio = load_csv_safe(BIO_WIND_DIR, scenario, "Wind_Biomass_Loss_Result.csv")

        print(f"  Solar soil: {'Yes' if solar_soil is not None else 'No'} ({len(solar_soil) if solar_soil is not None else 0} records)")
        print(f"  Solar biomass: {'Yes' if solar_bio is not None else 'No'} ({len(solar_bio) if solar_bio is not None else 0} records)")
        print(f"  Wind soil: {'Yes' if wind_soil is not None else 'No'} ({len(wind_soil) if wind_soil is not None else 0} records)")
        print(f"  Wind biomass: {'Yes' if wind_bio is not None else 'No'} ({len(wind_bio) if wind_bio is not None else 0} records)")

        # Run the breakdown statistics
        df_result = breakdown_carbon_by_land_type(
            solar_soil, solar_bio, wind_soil, wind_bio, scenario
        )

        if df_result is not None and len(df_result) > 0:
            all_results.append(df_result)

            # Print the summary
            print(f"\n  {scenario} carbon loss summary (tCO2e):")
            pivot = df_result.pivot_table(
                index='土地覆盖类型',
                columns='能源类型',
                values='总碳损失_tCO2e',
                aggfunc='sum'
            ).fillna(0)
            print(pivot.to_string())

    # Merge all scenarios
    if all_results:
        df_all = pd.concat(all_results, ignore_index=True)

        # Output to CSV
        output_csv = os.path.join(OUTPUT_DIR, "碳损失按土地覆盖类型分解_三场景汇总.csv")
        df_all.to_csv(output_csv, index=False, encoding='utf-8-sig')
        print(f"\n>>> Summary result saved: {output_csv}")

        # Output pivot tables by scenario and energy type
        print("\n" + "=" * 60)
        print("Summary statistics for each scenario")
        print("=" * 60)

        for scenario in SCENARIOS:
            df_s = df_all[df_all['场景'] == scenario]
            if len(df_s) == 0:
                continue

            print(f"\n[{scenario}]")
            pivot = df_s.pivot_table(
                index='土地覆盖类型',
                columns='能源类型',
                values=['土壤碳损失_tCO2e', '生物碳损失_tCO2e', '总碳损失_tCO2e'],
                aggfunc='sum'
            ).fillna(0)

            # Rename columns for readability
            pivot.columns = [f'{col[1]}_{col[0]}' for col in pivot.columns]
            print(pivot.to_string())

            # Totals
            total_soil_pv = df_s[df_s['能源类型'] == '光伏']['土壤碳损失_tCO2e'].sum()
            total_bio_pv = df_s[df_s['能源类型'] == '光伏']['生物碳损失_tCO2e'].sum()
            total_pv = df_s[df_s['能源类型'] == '光伏']['总碳损失_tCO2e'].sum()

            total_soil_wind = df_s[df_s['能源类型'] == '风电']['土壤碳损失_tCO2e'].sum()
            total_bio_wind = df_s[df_s['能源类型'] == '风电']['生物碳损失_tCO2e'].sum()
            total_wind = df_s[df_s['能源类型'] == '风电']['总碳损失_tCO2e'].sum()

            print(f"\n  Solar: soil carbon loss={total_soil_pv/1e6:.4f} Mt, biomass carbon loss={total_bio_pv/1e6:.4f} Mt, total={total_pv/1e6:.4f} MtCO2e")
            print(f"  Wind: soil carbon loss={total_soil_wind/1e6:.4f} Mt, biomass carbon loss={total_bio_wind/1e6:.4f} Mt, total={total_wind/1e6:.4f} MtCO2e")
            print(f"  Combined: {(total_pv + total_wind)/1e6:.4f} MtCO2e")

        # Output per-scenario CSVs
        for scenario in SCENARIOS:
            df_s = df_all[df_all['场景'] == scenario]
            if len(df_s) > 0:
                scenario_csv = os.path.join(OUTPUT_DIR, f"碳损失按土地覆盖类型分解_{scenario}.csv")
                df_s.to_csv(scenario_csv, index=False, encoding='utf-8-sig')
                print(f"\n>>> {scenario} result saved: {scenario_csv}")

    else:
        print("\nWarning: no data found, please check whether the input paths are correct.")

    print("\n>>> Processing completed!")

if __name__ == "__main__":
    main()
