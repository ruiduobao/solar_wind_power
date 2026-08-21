import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import numpy as np

# ================= Configuration =================
WIND_FILE = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\数据\土地覆盖数据\风力发电\土地覆盖合并统计\Wind_Analysis_Decoded_Merged.csv"
SOLAR_FILE = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\数据\土地覆盖数据\光伏发电\土地覆盖合并统计\Solar_Analysis_Decoded_Merged.csv"
OUTPUT_DIR = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\数据\土地覆盖数据\对比分析"

# Plot style
sns.set_theme(style="whitegrid", font_scale=1.2)
plt.rcParams['font.family'] = 'Arial'

def process_data(file_path, energy_type):
    if not os.path.exists(file_path):
        print(f"Warning: file does not exist {file_path}")
        return None, None

    df = pd.read_csv(file_path)
    df = df[df['total_area_m2'] > 0].copy()
    
    total_area_sum = df['total_area_m2'].sum()
    
    # 1. Source composition
    sums = {
        'Trees': df['pre_Trees'].sum(),
        'Grassland': df['pre_Grass'].sum(),
        'Shrubland': df['pre_Shrub'].sum(),
        'Cropland': df['pre_Crops'].sum()
    }
    known_sum = sum(sums.values())
    sums['Others'] = total_area_sum - known_sum
    
    composition_df = pd.DataFrame(list(sums.items()), columns=['Land Cover', 'Area_m2'])
    composition_df['Percentage'] = (composition_df['Area_m2'] / total_area_sum) * 100
    composition_df['Energy Type'] = energy_type
    
    # 2. Impact intensity
    # Compute the conversion rate for each type
    intensity_data = []
    categories = ['Trees', 'Grass', 'Shrub', 'Crops']
    mapping = {'Trees': 'Trees', 'Grass': 'Grassland', 'Shrub': 'Shrubland', 'Crops': 'Cropland'}
    
    for cat in categories:
        pre_col = f'pre_{cat}'
        loss_col = f'loss_{cat}_to_Built'
        
        total_pre = df[pre_col].sum()
        total_loss = df[loss_col].sum()
        
        rate = (total_loss / total_pre * 100) if total_pre > 0 else 0
        
        intensity_data.append({
            'Land Cover': mapping[cat],
            'Conversion Rate (%)': rate,
            'Energy Type': energy_type
        })
        
    intensity_df = pd.DataFrame(intensity_data)
    
    return composition_df, intensity_df

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    print("Starting comparison analysis...")
    
    # Process the data
    wind_comp, wind_int = process_data(WIND_FILE, 'Wind')
    solar_comp, solar_int = process_data(SOLAR_FILE, 'Solar')
    
    if wind_comp is None or solar_comp is None:
        print("Data is missing, comparison cannot be performed.")
        return

    # Merge the data
    comp_all = pd.concat([wind_comp, solar_comp])
    int_all = pd.concat([wind_int, solar_int])

    # ================= Chart 1: Land cover composition comparison =================
    plt.figure(figsize=(12, 6))
    
    # Color mapping
    colors = {
        'Trees': '#397d49',
        'Grassland': '#88b053',
        'Shrubland': '#dfc35a',
        'Cropland': '#e49635',
        'Others': '#a59b8f'
    }
    
    # Use pivot so the structure fits stacked charts or grouped bar charts better
    # Here a grouped bar chart is more intuitive
    sns.barplot(x='Land Cover', y='Percentage', hue='Energy Type', data=comp_all, 
                palette={'Wind': '#1f77b4', 'Solar': '#ff7f0e'}, edgecolor='black')
    
    plt.title('Land Cover Composition: Wind vs Solar', fontsize=16)
    plt.ylabel('Percentage of Total Area (%)')
    plt.ylim(0, 100)
    
    out_path_1 = os.path.join(OUTPUT_DIR, 'Comparison_Composition.png')
    plt.savefig(out_path_1, dpi=300)
    print(f"Composition comparison chart saved: {out_path_1}")
    
    # ================= Chart 2: Impact intensity comparison =================
    plt.figure(figsize=(12, 6))
    
    sns.barplot(x='Land Cover', y='Conversion Rate (%)', hue='Energy Type', data=int_all,
                palette={'Wind': '#1f77b4', 'Solar': '#ff7f0e'}, edgecolor='black')
    
    plt.title('Impact Intensity: Conversion to Built-up Area', fontsize=16)
    plt.ylabel('Conversion Rate (%) \n(Percentage of specific land cover converted to built)', fontsize=12)
    
    out_path_2 = os.path.join(OUTPUT_DIR, 'Comparison_Intensity.png')
    plt.savefig(out_path_2, dpi=300)
    print(f"Intensity comparison chart saved: {out_path_2}")
    
    # ================= Generate the report text =================
    report_path = os.path.join(OUTPUT_DIR, 'Comparison_Report.txt')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("========== Land Use Comparison Report: Wind vs Solar ==========\n\n")
        
        f.write("1. Land cover composition (Percentage):\n")
        f.write(comp_all.pivot(index='Land Cover', columns='Energy Type', values='Percentage').to_string())
        f.write("\n\n")
        
        f.write("2. Impact intensity (Conversion Rate %):\n")
        f.write(int_all.pivot(index='Land Cover', columns='Energy Type', values='Conversion Rate (%)').to_string())
        f.write("\n\n")
        
        f.write("3. Key findings:\n")
        # Automatically generate some simple conclusions
        wind_tree = comp_all[(comp_all['Energy Type']=='Wind') & (comp_all['Land Cover']=='Trees')]['Percentage'].values[0]
        solar_tree = comp_all[(comp_all['Energy Type']=='Solar') & (comp_all['Land Cover']=='Trees')]['Percentage'].values[0]
        
        if solar_tree > wind_tree:
            f.write(f"- Solar occupies a higher share of forest ({solar_tree:.2f}%) than wind ({wind_tree:.2f}%).\n")
        else:
            f.write(f"- Wind occupies a higher share of forest ({wind_tree:.2f}%) than solar ({solar_tree:.2f}%).\n")
            
    print(f"Report generated: {report_path}")

if __name__ == "__main__":
    main()
