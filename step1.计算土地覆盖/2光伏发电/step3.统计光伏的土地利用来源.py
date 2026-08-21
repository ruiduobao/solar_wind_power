import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# ================= Configuration =================
# Input file: points to the Merged.csv you just generated
INPUT_FILE = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\数据\土地覆盖数据\光伏发电\土地覆盖合并统计\Solar_Analysis_Decoded_Merged.csv"

# Output image save path
OUTPUT_DIR = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\数据\土地覆盖数据\光伏发电\图表"

# Set plotting style (common style for academic papers)
sns.set_theme(style="whitegrid", font_scale=1.2)
plt.rcParams['font.family'] = 'Arial'  # Common font for papers

# ================= Core analysis logic =================

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    print("Reading data...")
    df = pd.read_csv(INPUT_FILE)
    
    # 1. Data cleaning: remove invalid areas
    df = df[df['total_area_m2'] > 0].copy()
    total_records = len(df)
    print(f"Number of valid solar sites: {total_records}")

    # 2. Calculate total area by land cover type (unit: square kilometers km2)
    # Your preprocessing only extracted 4 types; we need to calculate 'Others' (including Bare, Water, Snow, Built, etc.)
    # Others = Total - (Trees + Grass + Shrub + Crops)
    
    total_area_sum = df['total_area_m2'].sum()
    
    sums = {
        'Trees': df['pre_Trees'].sum(),
        'Grassland': df['pre_Grass'].sum(),
        'Shrubland': df['pre_Shrub'].sum(),
        'Cropland': df['pre_Crops'].sum()
    }
    
    # Calculate the remaining part (mainly bare land, water, etc.)
    known_sum = sum(sums.values())
    sums['Others (Bare/Water)'] = total_area_sum - known_sum
    
    # Convert to DataFrame for plotting
    plot_data = pd.DataFrame(list(sums.items()), columns=['Land Cover', 'Area_m2'])
    
    # Calculate percentages
    plot_data['Percentage'] = (plot_data['Area_m2'] / total_area_sum) * 100
    plot_data['Area_km2'] = plot_data['Area_m2'] / 1e6
    
    # Sort: by area from largest to smallest
    plot_data = plot_data.sort_values('Percentage', ascending=False)
    
    print("\n========== Global land source statistics for solar energy ==========")
    print(plot_data.to_string(index=False))
    print("============================================")
    
    # 3. Check the key critical point (Forest percentage)
    forest_pct = plot_data.loc[plot_data['Land Cover'] == 'Trees', 'Percentage'].values[0]
    if forest_pct > 10:
        print(f"\n[!] Key finding: forest share is {forest_pct:.2f}% (>10%).")
        print("    Conclusion: this is a strong argument proving that solar expansion is encroaching on ecologically sensitive areas.")
    else:
        print(f"\n[-] Forest share is {forest_pct:.2f}%. Within the expected range.")

    # ================= Plotting (Horizontal Bar Chart) =================
    # This chart type is more suitable than pie charts for academic publication, as it clearly compares magnitudes
    
    plt.figure(figsize=(10, 6))
    
    # Define color mapping (Dynamic World style)
    colors = {
        'Trees': '#397d49',      # green
        'Grassland': '#88b053',  # grass green
        'Shrubland': '#dfc35a',  # shrub yellow
        'Cropland': '#e49635',   # cropland orange
        'Others (Bare/Water)': '#a59b8f' # gray
    }
    
    barplot = sns.barplot(
        data=plot_data, 
        x='Percentage', 
        y='Land Cover', 
        palette=colors,
        edgecolor='black'
    )
    
    # Add value labels
    for i, p in enumerate(barplot.patches):
        width = p.get_width()
        plt.text(
            width + 0.5,       # x coordinate
            p.get_y() + p.get_height()/2, # y coordinate
            f'{width:.1f}%',   # text
            va='center', 
            fontsize=12,
            fontweight='bold'
        )

    plt.title('Global Land Sources for Solar Energy Expansion (2015-2024)', fontsize=14, pad=20)
    plt.xlabel('Percentage of Total Buffered Area (%)', fontsize=12)
    plt.ylabel('')
    plt.xlim(0, max(plot_data['Percentage']) + 10) # leave space for labels
    
    # Save the figure
    out_png = os.path.join(OUTPUT_DIR, 'Solar_Global_Land_Source.png')
    out_pdf = os.path.join(OUTPUT_DIR, 'Solar_Global_Land_Source.pdf')
    plt.tight_layout()
    plt.savefig(out_png, dpi=300)
    plt.savefig(out_pdf)
    
    print(f"\nFigure saved to: {out_png}")
    plt.show()

if __name__ == "__main__":
    main()
