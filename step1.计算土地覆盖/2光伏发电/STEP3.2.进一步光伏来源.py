import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os

# ================= Configuration =================
INPUT_FILE = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\数据\土地覆盖数据\光伏发电\土地覆盖合并统计\Solar_Analysis_Decoded_Merged.csv"
OUTPUT_DIR = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\数据\土地覆盖数据\光伏发电\图表"

# Plot style
sns.set_theme(style="whitegrid", font_scale=1.2)
plt.rcParams['font.family'] = 'Arial'

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    print("Reading data...")
    df = pd.read_csv(INPUT_FILE)
    
    # -------------------------------------------------------
    # 1. Prepare the data
    # -------------------------------------------------------
    categories = ['Trees', 'Grass', 'Shrub', 'Crops']
    
    matrix_data = []
    
    for cat in categories:
        pre_col = f'pre_{cat}'
        loss_col = f'loss_{cat}_to_Built'
        
        total_pre_area = df[pre_col].sum() / 1e6 # km2
        total_loss_area = df[loss_col].sum() / 1e6 # km2
        
        matrix_data.append({
            'Source Type': cat,
            'Total Buffered Area (km²)': total_pre_area,
            'Converted to Built (km²)': total_loss_area
        })
    
    matrix_df = pd.DataFrame(matrix_data)
    print("\nGenerated statistics (km²):")
    print(matrix_df)

    # -------------------------------------------------------
    # Chart 1: Impact intensity (unchanged)
    # -------------------------------------------------------
    matrix_df['Conversion Rate (%)'] = (matrix_df['Converted to Built (km²)'] / matrix_df['Total Buffered Area (km²)']) * 100
    
    plt.figure(figsize=(10, 6))
    colors = {'Trees': '#397d49', 'Grass': '#88b053', 'Shrub': '#dfc35a', 'Crops': '#e49635'}
    ax = sns.barplot(x='Source Type', y='Conversion Rate (%)', data=matrix_df, palette=colors, edgecolor='black')
    
    for i, p in enumerate(ax.patches):
        height = p.get_height()
        ax.text(p.get_x() + p.get_width()/2., height + 0.05,
                f'{height:.2f}%',
                ha="center", va="bottom", fontsize=12, fontweight='bold')
    
    plt.title('Impact Intensity: Percentage of Land Converted to Impervious Surfaces\n(Inside Solar Site Boundary)', fontsize=14, pad=20)
    plt.ylabel('Conversion Rate to Built Area (%)', fontsize=12)
    plt.xlabel('Original Land Cover Type', fontsize=12)
    plt.ylim(0, max(matrix_df['Conversion Rate (%)']) * 1.3 if not matrix_df['Conversion Rate (%)'].empty and max(matrix_df['Conversion Rate (%)']) > 0 else 10)
    
    out_path_1 = os.path.join(OUTPUT_DIR, 'Solar_Impact_Intensity.png')
    plt.tight_layout()
    plt.savefig(out_path_1, dpi=300)
    print(f"Impact intensity chart saved: {out_path_1}")
    plt.close() # Close the figure to free memory

    # -------------------------------------------------------
    # Chart 2: Absolute area comparison (Log Scale Grouped Bar Chart) - replacing the heatmap
    # -------------------------------------------------------
    # Data transformation: Melt
    plot_df = matrix_df.melt(id_vars='Source Type', 
                             value_vars=['Total Buffered Area (km²)', 'Converted to Built (km²)'],
                             var_name='Metric', value_name='Area (km²)')
    
    plt.figure(figsize=(10, 7))
    
    # Use a Log Scale to show the huge total areas and the relatively small converted areas at the same time
    # Custom colors: light color for Total, dark red to emphasize Converted
    palette = {'Total Buffered Area (km²)': '#b0c4de', 'Converted to Built (km²)': '#d62728'}
    
    ax2 = sns.barplot(x='Source Type', y='Area (km²)', hue='Metric', data=plot_df, 
                      palette=palette, edgecolor='black')
    
    # Set the log scale
    ax2.set_yscale('log')
    
    # Add value labels (adaptive positions)
    for p in ax2.patches:
        height = p.get_height()
        if height > 0:
            ax2.text(p.get_x() + p.get_width()/2., height * 1.1, # Slightly higher
                    f'{height:.1f}',
                    ha="center", va="bottom", fontsize=10, color='black')

    plt.title('Scale of Impact: Total Affected Area vs. Converted Area (Log Scale)\n(Solar Energy)', fontsize=14, pad=20)
    plt.ylabel('Area (km²) - Log Scale', fontsize=12)
    plt.xlabel('Original Land Cover Type', fontsize=12)
    plt.legend(title='', loc='upper right')
    
    out_path_2 = os.path.join(OUTPUT_DIR, 'Solar_Area_Comparison_Log.png')
    plt.tight_layout()
    plt.savefig(out_path_2, dpi=300)
    print(f"Area comparison chart (replacing heatmap) saved: {out_path_2}")
    plt.show()

if __name__ == "__main__":
    main()
