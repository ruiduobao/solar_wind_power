# -*- coding: utf-8 -*-
"""
Wind CPT comparison analysis: with vs without grid emission factor
Author: 锐多宝 (Trae AI)
Date: 2026-01-28

Features:
1. Read the CPT results under the two scenarios.
2. Merge the data and compute the difference.
3. Generate comparison charts.

Input:
- With emission factor: Wind_Carbon_Payback_Time.csv
- Without emission factor: Wind_CPT_No_Grid_EF.csv

Output:
- Statistical charts (.png)
- Difference data (.csv)
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.colors import Normalize

# ================= Configuration =================

# Input files
FILE_WITH_EF = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\5.2.风机碳回本周期\Wind_Carbon_Payback_Time.csv"
FILE_NO_EF = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\6.2.风机碳回本周期(不考虑排放因子)\Wind_CPT_No_Grid_EF.csv"

# Output directory
OUTPUT_DIR = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\7.2对比风机_有无排放因子"

# Global average (for reference line)
GLOBAL_AVG_EF = 0.475

# Plotting style
sns.set_theme(style="ticks", font="Arial", context="paper")
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['axes.grid'] = True
plt.rcParams['grid.alpha'] = 0.3
plt.rcParams['font.sans-serif'] = ['Arial', 'SimHei'] 
plt.rcParams['axes.unicode_minus'] = False

# ================= Utility functions =================

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

# ================= Plotting functions =================

def plot_comparison_scatter(df):
    """Scatter plot comparison: Local EF vs Global Avg EF"""
    plt.figure(figsize=(10, 8))
    
    # Wind payback is fast, filter out the very few outliers (e.g. > 5 years)
    plot_df = df[(df['CPT_Years'] <= 5) & (df['CPT_Years_NoEF'] <= 5)].copy()
    
    # Draw the 1:1 line
    max_val = max(plot_df['CPT_Years'].max(), plot_df['CPT_Years_NoEF'].max())
    plt.plot([0, max_val], [0, max_val], 'r--', label='1:1 Line (No Difference)')
    
    # Scatter
    sc = plt.scatter(
        plot_df['CPT_Years_NoEF'], 
        plot_df['CPT_Years'], 
        c=plot_df['grid_ef'], 
        cmap='viridis', 
        s=10, 
        alpha=0.6,
        edgecolors='none'
    )
    
    plt.colorbar(sc, label='Grid Emission Factor (tCO2/MWh)')
    
    plt.xlabel("CPT using Global Avg EF (0.475) [Years]", fontsize=12)
    plt.ylabel("CPT using Local Grid EF [Years]", fontsize=12)
    plt.title("Wind CPT Comparison: Local vs Global Emission Factors", fontsize=16, fontweight='bold')
    plt.legend()
    
    out_file = os.path.join(OUTPUT_DIR, "1_Scatter_Comparison.png")
    plt.savefig(out_file)
    plt.close()

    csv_file = os.path.join(OUTPUT_DIR, "1_Scatter_Comparison.csv")
    plot_df.to_csv(csv_file, index=False, encoding='utf-8-sig')
    print(f"Generated: {out_file} and {csv_file}")

def plot_diff_histogram(df):
    """Difference histogram"""
    plt.figure(figsize=(10, 6))
    
    sns.histplot(df['CPT_Diff'], bins=100, kde=True, color='dodgerblue')
    
    plt.axvline(0, color='k', linestyle='-')
    
    plt.xlabel("Difference in CPT (Local EF - Global Avg EF) [Years]", fontsize=12)
    plt.ylabel("Count of Sites", fontsize=12)
    plt.title("Distribution of Wind CPT Discrepancy", fontsize=16, fontweight='bold')
    
    out_file = os.path.join(OUTPUT_DIR, "2_Hist_Difference.png")
    plt.savefig(out_file)
    plt.close()

    csv_file = os.path.join(OUTPUT_DIR, "2_Hist_Difference.csv")
    df[['fid', 'CPT_Diff']].to_csv(csv_file, index=False, encoding='utf-8-sig')
    print(f"Generated: {out_file} and {csv_file}")

def plot_diff_vs_ef(df):
    """Difference vs emission factor"""
    plt.figure(figsize=(10, 6))
    
    plot_df = df[df['CPT_Diff'].abs() < 2].copy() # wind differences are usually small
    
    plt.scatter(plot_df['grid_ef'], plot_df['CPT_Diff'], alpha=0.5, s=5, c='darkblue')
    
    plt.axvline(GLOBAL_AVG_EF, color='r', linestyle='--', label=f'Global Avg EF ({GLOBAL_AVG_EF})')
    plt.axhline(0, color='k', linestyle='-')
    
    plt.xlabel("Local Grid Emission Factor (tCO2/MWh)", fontsize=12)
    plt.ylabel("CPT Difference (Local - Global) [Years]", fontsize=12)
    plt.title("Impact of Grid Cleanliness on Wind CPT Bias", fontsize=16, fontweight='bold')
    plt.legend()
    
    out_file = os.path.join(OUTPUT_DIR, "3_Scatter_Diff_vs_EF.png")
    plt.savefig(out_file)
    plt.close()

    csv_file = os.path.join(OUTPUT_DIR, "3_Scatter_Diff_vs_EF.csv")
    plot_df.to_csv(csv_file, index=False, encoding='utf-8-sig')
    print(f"Generated: {out_file} and {csv_file}")

def plot_country_diff(df):
    """Country average difference ranking"""
    cnt_counts = df['country_final'].value_counts()
    valid_countries = cnt_counts[cnt_counts >= 50].index
    
    sub_df = df[df['country_final'].isin(valid_countries)]
    
    stats = sub_df.groupby('country_final')['CPT_Diff'].mean().sort_values()
    
    top_dirty = stats.head(15)
    top_clean = stats.tail(15)
    
    plot_data = pd.concat([top_dirty, top_clean])
    
    plt.figure(figsize=(12, 10))
    colors = ['green' if x < 0 else 'red' for x in plot_data.values]
    sns.barplot(x=plot_data.values, y=plot_data.index, palette=colors)
    
    plt.axvline(0, color='k', linestyle='-')
    plt.xlabel("Average CPT Difference (Local - Global) [Years]", fontsize=12)
    plt.title("Bias by Country: Where does Grid EF matter most? (Wind)", fontsize=16, fontweight='bold')
    
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='green', label='Local CPT < Global (Dirty Grid)'),
        Patch(facecolor='red', label='Local CPT > Global (Clean Grid)')
    ]
    plt.legend(handles=legend_elements, loc='lower right')
    
    out_file = os.path.join(OUTPUT_DIR, "4_Bar_Country_Bias.png")
    plt.savefig(out_file)
    plt.close()

    csv_file = os.path.join(OUTPUT_DIR, "4_Bar_Country_Bias.csv")
    plot_data.to_csv(csv_file, header=['Avg_CPT_Diff'], encoding='utf-8-sig')
    print(f"Generated: {out_file} and {csv_file}")

# ================= Main program =================

def main():
    ensure_dir(OUTPUT_DIR)
    
    print(">>> Loading Data...")
    if not os.path.exists(FILE_WITH_EF) or not os.path.exists(FILE_NO_EF):
        print("Error: Input files not found.")
        return
        
    df_ef = pd.read_csv(FILE_WITH_EF)
    df_no_ef = pd.read_csv(FILE_NO_EF)
    
    cols_ef = ['fid', 'country_final', 'grid_ef', 'CPT_Years']
    cols_no_ef = ['fid', 'CPT_Years_NoEF']
    
    df_merge = pd.merge(df_ef[cols_ef], df_no_ef[cols_no_ef], on='fid', how='inner')
    
    df_merge = df_merge.dropna(subset=['CPT_Years', 'CPT_Years_NoEF', 'grid_ef'])
    df_merge = df_merge[(df_merge['CPT_Years'] > 0) & (df_merge['CPT_Years_NoEF'] > 0)]
    
    df_merge['CPT_Diff'] = df_merge['CPT_Years'] - df_merge['CPT_Years_NoEF']
    
    print(f"Merged Data: {len(df_merge)} records")
    
    plot_comparison_scatter(df_merge)
    plot_diff_histogram(df_merge)
    plot_diff_vs_ef(df_merge)
    plot_country_diff(df_merge)
    
    out_csv = os.path.join(OUTPUT_DIR, "Wind_CPT_Comparison_Result.csv")
    df_merge.to_csv(out_csv, index=False, encoding='utf-8-sig')
    print(f"Saved comparison data to {out_csv}")

if __name__ == "__main__":
    main()
