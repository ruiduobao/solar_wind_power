import pandas as pd

file_path = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\数据\土地覆盖数据\GEE_Wind_Analysis_2017\WIND_FROM_2017_WithRing_Batch_56.csv"
df = pd.read_csv(file_path)

# Find rows with FID 1-31
target_rows = df[df['fid'].isin(range(1, 32))]

print(f"Found {len(target_rows)} rows")
for _, row in target_rows.iterrows():
    print(f"\nFID: {row['fid']}")
    print(f"Stats JSON: {row['stats_json']}")
    print(f"Ring JSON: {row['ring_stats_json']}")
