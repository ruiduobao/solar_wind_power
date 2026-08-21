# -*- coding: utf-8 -*-
"""
Create a donut chart of land cover composition for each country
Author: 锐多宝
Date: 2026-02-02
Description:
    Based on the given CSV data, draw a land cover share donut chart for each country.
    Requirements:
    1. Show the country name in the center.
    2. Show the shares of the top three land cover types in the ring.
    3. Use Times New Roman font.
    4. Custom colors.
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from io import StringIO

# ================= Configuration =================

# 25: "Country_Analysis_FROM-GLC.csv" (assuming this file contains raw area data rather than percentages; if it contains percentages, accurate sorting is impossible)
# The previous script generated "Country_Analysis_FROM-GLC.csv" storing percentages.
# If we need to sort by total area, we need the raw area data.
# Assume INPUT_FILE contains percentage data (inferred from the previous step),
# but the user now asks to sort by total area.
# Let us first check the content of INPUT_FILE to see whether it is percentages or areas.
# If it is percentages, we cannot know the total area; we can only assume the user wants the order
# as in the file (usually already sorted) or we cannot re-sort.
# The CSV generated in the previous step plot_country_analysis is pivot_pct (percentages).
# To sort by total area, we would need the area summary from plot_country_analysis,
# or the user-provided CSV is already the top N sorted by area.

# Assume the row order in the CSV is already sorted by total area (plot_country_analysis usually
# sorts by total area and keeps the top N).
# So we only need to use the row index in the loop.

# Input file path
INPUT_FILE = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\figure2_全球光伏风电土地利用\子图\Wind_Country_Analysis_FROM-GLC.csv"

# Output directory
OUTPUT_DIR = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\figure2_全球光伏风电土地利用\子图\风机各个国家环形图_FROM-GLC"

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# Color mapping (based on user input)
# 10: "Cropland", 20: "Forest", 30: "Grass", 40: "Shrub", 60: "Water",
# 80: "Impervious", 90: "Bareland", 100: "Snow/Ice", 120: "Cloud"
# 0: "Background" (ignored or black)

# Color definitions (FROM-GLC standard colors)
# Convert (R, G, B, A) to Hex format
def rgba_to_hex(r, g, b, a):
    return f"#{r:02X}{g:02X}{b:02X}"

COLORS = {
    "Background": rgba_to_hex(0, 0, 0, 0),          # 0
    "Cropland": rgba_to_hex(163, 255, 115, 255),    # 10
    "Forest": rgba_to_hex(38, 115, 0, 255),         # 20
    "Grass": rgba_to_hex(76, 230, 0, 255),          # 30
    "Shrub": rgba_to_hex(112, 168, 0, 255),         # 40
    "Water": rgba_to_hex(0, 92, 255, 255),          # 60
    "Impervious": rgba_to_hex(197, 0, 255, 255),    # 80
    "Bareland": rgba_to_hex(255, 170, 0, 255),      # 90
    "Snow/Ice": rgba_to_hex(0, 255, 197, 255),      # 100
    "Cloud": rgba_to_hex(255, 255, 255, 255),       # 120
    "Unknown": "#000000"                            # Unknown
}

# Font settings
plt.rcParams['font.family'] = 'Times New Roman'
plt.rcParams['font.size'] = 18

# ================= Data preparation (create the file if it does not exist) =================
# The user provided the data content; to make sure the script can run, create it if the file is missing
if not os.path.exists(INPUT_FILE):
    print(f"Input file does not exist; creating sample data at: {INPUT_FILE}")
    csv_content = """COUNTRY,Bareland,Cropland,Forest,Grass,Impervious,Shrub,Snow/Ice,Unknown,Water
China,50.21735440931748,21.162586255679745,1.9649413769894444,16.553795595072526,4.811510816409434,0.208237602238501,2.651822090407136e-05,0.30492376292754253,4.776623663144414
United States,18.462298179412517,28.29741265345882,10.296885790969391,34.49088785102505,2.609266335128746,5.6076830380264555,0.00022888744072233598,0.08154005404547375,0.15379721049282497
India,45.50376235985971,25.176191636975936,0.385128570061962,25.52044107268136,1.9715442838995307,0.9514043616391293,0.0,0.018405718237660396,0.4731219966447065
Spain,18.724672577312347,67.25235588326065,0.17979456687199694,4.656729813458432,8.45209206223757,0.6521110580745365,0.0,0.0008265829073732711,0.08141745587710049
Brazil,0.14727371134773995,12.632793282360524,2.6857205470105727,42.830986075527605,0.8607573177497009,40.6959598778547,0.0,0.03906586079007359,0.10744332735907397
México,31.927794309909856,25.3492423720158,1.1301979138537392,24.67396411665897,0.6470352701043071,16.143743495578587,0.0,0.030558733638082022,0.0974637882406481
Japan,3.962038613520253,24.094130198679533,38.30163942944307,12.205214651290943,19.716266749047374,0.12921990795926555,0.038918305954959355,0.014916227647845693,1.537655916456766
Australia,5.930608287861925,17.067885126205955,1.108090990861186,65.23853701096716,0.539588610866304,10.09431910318716,0.0,0.009335490852539392,0.011635379197739548
Chile,72.9462840891938,7.133866464171554,1.0007672246264643,13.312885984329585,0.6339989953967659,4.944580683005159,0.0,6.0681914690104235e-05,0.027555877361971366
Vietnam,2.0900801784507563,57.1048034243712,9.23639526734478,17.46305032526797,6.00948002189375,0.4772623306686812,0.0,0.1132699397378183,7.505658512265061



"""
    
    # Ensure the storage directory exists
    input_dir = os.path.dirname(INPUT_FILE)
    if not os.path.exists(input_dir):
        os.makedirs(input_dir)
        
    with open(INPUT_FILE, "w", encoding='utf-8') as f:
        f.write(csv_content)

# ================= Plotting functions =================

def draw_donut_chart(country_name, data_series, rank):
    """
    Draw a donut chart for a single country
    """
    # 1. Data preprocessing
    # Drop zero values
    data = data_series[data_series > 0].sort_values(ascending=False)
    
    # Normalize (ensure the sum is 100)
    data = data / data.sum() * 100
    
    # Get the top 3
    top3_indices = data.head(3).index.tolist()
    
    # Prepare colors
    colors = [COLORS.get(idx, "#333333") for idx in data.index]
    
    # 2. Plot
    fig, ax = plt.subplots(figsize=(6, 6))
    
    # Draw the donut chart (pie chart with hole)
    # wedgeprops width controls the ring width
    # Increase the width to reduce the hole size (0.3 -> 0.5)
    ring_width = 0.5
    wedges, texts = ax.pie(
        data, 
        startangle=90, 
        colors=colors,
        wedgeprops=dict(width=ring_width, edgecolor='white', linewidth=1),
        counterclock=False # clockwise arrangement
    )
    
    # 3. Add labels inside the ring (top 3 shares)
    # Compute the center angle of each wedge to place the text
    # Only label the top 3
    
    total = sum(data)
    cumulative = 0
    for i, (p, label) in enumerate(zip(wedges, data.index)):
        val = data[label]
        
        # Only annotate the top 3
        if label in top3_indices:
            # Compute the angle
            ang = (p.theta2 - p.theta1) / 2. + p.theta1
            y = np.sin(np.deg2rad(ang))
            x = np.cos(np.deg2rad(ang))
            
            # Radial position: middle of the ring (1 - width/2)
            # width=0.5, so the ring spans from 0.5 to 1.0
            # The middle position is 0.75
            r = 1 - ring_width / 2
            
            # Compute the text rotation angle so it follows the ring (tangential direction)
            # matplotlib angles start at the 3 o'clock position and increase counterclockwise
            # ang here is already the standard angle
            
            # Normalize the angle to 0-360
            ang_norm = ang % 360
            
            # The tangential direction is usually ang - 90
            # To keep the text readable (not upside down), adjust by angle
            # Upper half (0-180): text direction ang - 90
            # Lower half (180-360): text direction ang + 90
            
            if 0 <= ang_norm <= 180:
                rotation = ang_norm - 90
            else:
                rotation = ang_norm + 90
            
            # Font color: white on dark backgrounds, black on light backgrounds
            # For simplicity, use white with a slightly larger font size
            ax.text(
                x * r, y * r, 
                f"{val:.1f}", 
                ha='center', va='center', 
                color='white', 
                fontsize=30, # increased font size
                fontweight='bold',
                rotation=rotation, # set rotation
                rotation_mode='anchor'
            )
            
    # 4. Add the country name in the center
    ax.text(
        0, 0, 
        country_name, 
        ha='center', va='center', 
        fontsize=28, # increased font size
        fontweight='bold',
        color='black'
    )
    
    # Save - add the rank to the filename
    out_path = os.path.join(OUTPUT_DIR, f"{rank}.{country_name}_Donut.png")
    # Trim white margins
    plt.tight_layout()
    plt.savefig(out_path, dpi=300, transparent=True)
    plt.close()
    print(f"Saved: {out_path}")

# ================= Main program =================

def main():
    print(f"Reading data: {INPUT_FILE}")
    df = pd.read_csv(INPUT_FILE)
    
    # Assume the input file is already sorted by total area (as analysis scripts usually do)
    # If not sorted, we cannot re-sort here because the input is percentage data and the total
    # area information is lost. We simply use the row number as the rank.
    
    # Iterate over each country
    for index, row in df.iterrows():
        country = row['COUNTRY']
        rank = index + 1 # rank starts at 1
        
        # Extract data columns (exclude the COUNTRY column)
        series = row.drop('COUNTRY')
        # Convert to numeric (just in case)
        series = pd.to_numeric(series, errors='coerce').fillna(0)
        
        print(f"Drawing: {rank}. {country}")
        draw_donut_chart(country, series, rank)
        
    print("All charts have been drawn!")

if __name__ == "__main__":
    main()
