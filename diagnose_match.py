
import geopandas as gpd
import pandas as pd
import os

# Paths
WORLD_SHP = r"z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\代码\结果数据\3.1光伏发电潜力计算\ne_110m_admin_0_countries\ne_110m_admin_0_countries.shp"
CSV_PATH = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\4.4.1光伏碳债务合并损失\标准场景\Solar_Total_Carbon_Debt_Result.csv"

try:
    print("Loading Shapefile...")
    gdf = gpd.read_file(WORLD_SHP)
    print("Shapefile Columns:", gdf.columns.tolist())
    print("Shapefile Sample (ADMIN, ISO_A3, ADM0_A3):")
    cols_to_show = [c for c in ['ADMIN', 'ISO_A3', 'ADM0_A3', 'NAME'] if c in gdf.columns]
    print(gdf[cols_to_show].head())
    
    print("\nLoading CSV...")
    df = pd.read_csv(CSV_PATH)
    csv_countries = df['country_final'].unique()
    print(f"CSV Countries count: {len(csv_countries)}")
    
    # Check matching
    shp_countries = gdf['ADMIN'].unique()
    
    matched = [c for c in csv_countries if c in shp_countries]
    unmatched = [c for c in csv_countries if c not in shp_countries]
    
    print(f"\nMatched: {len(matched)}")
    print(f"Unmatched: {len(unmatched)}")
    print("\nUnmatched Countries in CSV (Top 20):")
    print(unmatched[:20])
    
    print("\nCheck specific potential matches in Shapefile:")
    for c in unmatched[:10]:
        # Simple fuzzy search
        print(f"Looking for match for '{c}':")
        possible = gdf[gdf['ADMIN'].str.contains(c[:4], case=False, na=False)]['ADMIN'].tolist()
        print(f"  Possible matches in SHP: {possible}")

    # Check pycountry
    try:
        import pycountry
        print("\npycountry is available.")
    except ImportError:
        print("\npycountry is NOT available.")

except Exception as e:
    print(f"Error: {e}")
