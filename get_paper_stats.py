import pandas as pd
import os

# Paths
base_dir = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\代码\结果数据"

files = {
    "solar_land": os.path.join(base_dir, r"1.土地来源分析\SOLAR_FROM_2017_LandCover_Summary.csv"),
    "wind_land": os.path.join(base_dir, r"1.土地来源分析\FROM_2017_LandCover_Summary.csv"),
    "solar_cpt": os.path.join(base_dir, r"5.1.光伏碳回本周期\Solar_Carbon_Payback_Time.csv"),
    "wind_cpt": os.path.join(base_dir, r"5.2.风机碳回本周期\Wind_Carbon_Payback_Time.csv")
}

def get_land_stats(filepath, name):
    print(f"--- Processing {name} Land Cover ---")
    try:
        # Use chunks to handle large files
        chunksize = 100000
        total_area = 0
        class_areas = {}
        
        for chunk in pd.read_csv(filepath, chunksize=chunksize):
            # Group by class_name and sum area
            grouped = chunk.groupby('class_name')['area_sqm'].sum()
            for cls, area in grouped.items():
                class_areas[cls] = class_areas.get(cls, 0) + area
                total_area += area
                
        # Calculate percentages
        print(f"Total Area (sqm): {total_area:,.2f}")
        results = []
        for cls, area in class_areas.items():
            pct = (area / total_area) * 100
            results.append((cls, area, pct))
            
        # Sort by percentage
        results.sort(key=lambda x: x[2], reverse=True)
        
        for cls, area, pct in results:
            print(f"{cls}: {pct:.2f}% ({area/1e6:.2f} km2)")
            
    except Exception as e:
        print(f"Error reading {name}: {e}")

def get_cpt_stats(filepath, name):
    print(f"\n--- Processing {name} CPT ---")
    try:
        df = pd.read_csv(filepath)
        # Filter positive CPT
        valid_cpt = df[df['CPT_Years'] > 0]['CPT_Years']
        
        print(f"Valid Records: {len(valid_cpt)}")
        print(f"Mean CPT: {valid_cpt.mean():.2f} years")
        print(f"Median CPT: {valid_cpt.median():.2f} years")
        print(f"Min CPT: {valid_cpt.min():.2f} years")
        print(f"Max CPT: {valid_cpt.max():.2f} years")
        print(f"10th Percentile: {valid_cpt.quantile(0.1):.2f} years")
        print(f"90th Percentile: {valid_cpt.quantile(0.9):.2f} years")
        
    except Exception as e:
        print(f"Error reading {name}: {e}")

if __name__ == "__main__":
    get_land_stats(files["solar_land"], "Solar")
    get_land_stats(files["wind_land"], "Wind")
    get_cpt_stats(files["solar_cpt"], "Solar")
    get_cpt_stats(files["wind_cpt"], "Wind")
