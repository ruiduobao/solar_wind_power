import glob
import os

INPUT_DIR_2017 = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\数据\土地覆盖数据\2017_2024的数据在2017年的土地覆盖上\GEE_solar_Analysis_2017"
name_prefix = "SOLAR_ESRI_2017_Stats"
search_pattern = os.path.join(INPUT_DIR_2017, f"{name_prefix}*.csv")

print(f"Pattern: {search_pattern}")
files = glob.glob(search_pattern)
print(f"Found {len(files)} files")
if len(files) > 0:
    print(files[0])
else:
    print("Listing dir content:")
    try:
        print(os.listdir(INPUT_DIR_2017)[:5])
    except Exception as e:
        print(e)
