# -*- coding: utf-8 -*-
"""
Custom plotting script for Figure 4a/5a: The Grid Decarbonization Paradox scatter plot
Function: draw a Hexbin plot with a logarithmic color mapping, hyperbolic curve fitting and academic annotations (fixing coverage, fonts and grid)
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
from scipy.optimize import curve_fit

# ================= 1. Configure paths =================
# Replace this with the actual folder path that stores 3_Scatter_CPT_vs_GridEF.csv
WORK_DIR = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\5.1.光伏碳回本周期\标准场景"
INPUT_CSV = os.path.join(WORK_DIR, "3_Scatter_CPT_vs_GridEF.csv")
OUTPUT_PNG = os.path.join(WORK_DIR, "Figure_4a_Grid_Paradox.png")

# ================= 2. Global plot style settings =================
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
# Change point 1: enable Times New Roman
plt.rcParams['font.family'] = 'Times New Roman' 
# Make the mathematical symbols in the figure (such as superscripts/subscripts) match the Times-like serif style
plt.rcParams['mathtext.fontset'] = 'stix' 

# Hyperbolic fitting function
def hyperbolic_func(x, a, b):
    return a / x + b

def plot_paradox_scatter():
    print(f"Reading data: {INPUT_CSV}")
    if not os.path.exists(INPUT_CSV):
        print("Error: input file not found. Please check the path.")
        return

    # Read the data
    df = pd.read_csv(INPUT_CSV)
    
    # Clean the data: exclude Grid EF values of 0 or extremely small values to avoid division-by-zero errors during fitting
    col_x = 'grid_ef'
    col_y = 'CPT_Years'
    
    df_valid = df[(df[col_x] > 0.01) & (df[col_y] > 0) & (df[col_y] * 365.25 <= 20 * 365.25)].copy()
    
    x_data = df_valid[col_x].values
    y_data = df_valid[col_y].values * 365.25

    print(f"Number of valid data points: {len(x_data)}")

    # ================= 3. Start plotting =================
    fig, ax = plt.subplots(figsize=(9, 6), constrained_layout=True)

    # Use bins='log' to solve the invisible long tail at low density, and set zorder=2 so it is above the grid lines
    hb = ax.hexbin(x_data, y_data, gridsize=40, cmap='Blues', mincnt=1, bins='log', zorder=2)
    
    # Add the colorbar, indicating this is a logarithmic distribution
    cb = fig.colorbar(hb, ax=ax, pad=0.02)
    cb.set_label('Count ', fontsize=14)
    cb.ax.tick_params(labelsize=12) 

    # Fit the hyperbola and draw it (fit in years first, then convert to days)
    try:
        # Temporarily convert y_data back to years for fitting
        y_data_years = y_data / 365.25
        popt, pcov = curve_fit(hyperbolic_func, x_data, y_data_years, maxfev=10000)
        a_years, b_years = popt
        
        # Convert the fitted parameters to days
        a = a_years * 365.25
        b = b_years * 365.25
        
        # Compute R² (using the day-based data)
        y_pred = a / x_data + b
        ss_res = np.sum((y_data - y_pred) ** 2)
        ss_tot = np.sum((y_data - np.mean(y_data)) ** 2)
        r_squared = 1 - (ss_res / ss_tot)
        
        # Print the fitting results
        print("\n" + "="*60)
        print("Hyperbolic fitting result (CPBT = a / EF_grid + b):")
        print("="*60)
        print(f"Parameter a = {a:.4f}")
        print(f"Parameter b = {b:.4f}")
        print(f"R² = {r_squared:.4f}")
        print("\nModel interpretation:")
        print(f"  - When EF_grid -> inf, CPBT -> {b:.4f} days (asymptote)")
        print(f"  - When EF_grid = 0.5 tCO2e/MWh, CPBT ≈ {a/0.5 + b:.2f} days")
        print(f"  - When EF_grid = 1.0 tCO2e/MWh, CPBT ≈ {a/1.0 + b:.2f} days")
        print("\nPhysical meaning:")
        print("  - a represents the sensitivity of the carbon payback time to the grid emission factor")
        print("  - b represents the theoretical minimum carbon payback time when the grid is extremely clean")
        print("  - This model embodies the 'grid decarbonization paradox': the cleaner the grid, the longer the solar carbon payback time")
        print("="*60 + "\n")
        
        x_fit = np.linspace(min(x_data), max(x_data), 500)
        y_fit = a / x_fit + b
        
        # Draw the fitted line; zorder=4 ensures it is above the data points
        ax.plot(x_fit, y_fit, color='#d7191c', linewidth=3, linestyle='-', 
                 zorder=4)
    except Exception as e:
        print(f"Hyperbolic fitting failed; the fitted line will be skipped. Error message: {e}")
        a, b, r_squared = np.nan, np.nan, np.nan

    # ================== Change point 2 & 3: adjust annotation positions to fix coverage and out-of-frame issues ==================
    # Annotate the top-left (penalty zone)
    # Move the text box downward (near y=9×365.25=3287.25 days), with the arrow pointing upward (y=14×365.25=5113.5 days), perfectly avoiding the legend in the top-right corner without exceeding the frame
    ax.annotate('Decarbonization penalty\n(e.g., Norway, Switzerland)', 
                xy=(0.08, 14*365.25), xycoords='data',
                xytext=(0.25, 12*365.25), textcoords='data',
                arrowprops=dict(facecolor='black', shrink=0.05, width=1.5, headwidth=6, zorder=5),
                fontsize=13, fontweight='bold', color='#2b83ba', zorder=5,
                bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="gray", alpha=0.9))

    # Annotate the bottom-right (benefit zone)
    ax.annotate('High substitution benefit\n(e.g., Iraq, South Africa)', 
                xy=(0.92, 1.2*365.25), xycoords='data',
                xytext=(0.55, 4*365.25), textcoords='data',
                arrowprops=dict(facecolor='black', shrink=0.05, width=1.5, headwidth=6, zorder=5),
                fontsize=13, fontweight='bold', color='#d7191c', zorder=5,
                bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="gray", alpha=0.9))

    # ================= 4. Detail refinements =================
    # Normalize the axis labels
    # ax.set_title("Solar CPBT vs. Grid emission factor", fontsize=18, fontweight='bold', pad=15)
    ax.set_xlabel("Grid emission factor ($tCO_2e/MWh$)", fontsize=14)
    ax.set_ylabel("Carbon payback time (days)", fontsize=14)
    
    # Change point 4: control the density of the vertical axis grid ticks
    ax.yaxis.set_major_locator(MultipleLocator(1826.25)) # Set the Y-axis tick step to 5 years × 365.25 = 1826.25 days
    ax.xaxis.set_major_locator(MultipleLocator(0.2)) # Set the X-axis tick step to 0.2
    
    # Lock the axis ranges for a cleaner chart edge
    ax.set_xlim(-0.02, 1.1)
    ax.set_ylim(-182.625, 20*365.25)
    
    # Optimize the grid lines: zorder=1 keeps them at the bottom layer
    ax.grid(True, linestyle='--', alpha=0.6, color='gray', zorder=1)
    ax.set_axisbelow(True) # Keep the grid lines below the scatter plot
    
    ax.tick_params(axis='both', which='major', labelsize=12)

    handles, labels = ax.get_legend_handles_labels()
    if handles:
        legend = ax.legend(loc='upper right', fontsize=13, framealpha=1)
        legend.set_zorder(5)
    
    # Add the fitted-parameter text box (shown only when fitting succeeds)
    if not np.isnan(a):
        params_text = f'$CPBT = {a:.2f}/EF_{{grid}}  {b:.2f}$\n$R^2 = {r_squared:.2f}$'
        ax.text(0.05, 0.88, params_text, transform=ax.transAxes, 
                fontsize=11, fontfamily='Times New Roman')

    # Save the figure, using bbox_inches='tight' to ensure all content stays inside the frame
    plt.savefig(OUTPUT_PNG, bbox_inches='tight')
    print(f"Plotting successful! Saved to: {OUTPUT_PNG}")
    
    plt.show()

if __name__ == "__main__":
    plot_paradox_scatter()
