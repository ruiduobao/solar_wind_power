
import pandas as pd

solar_lc_path = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\figure4_全球碳回本\匹配风机光伏的各类地物的碳汇本时间\SOLAR_FROM_2017_2024_LandCover_Summary.csv"
wind_lc_path = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\制图\figure4_全球碳回本\匹配风机光伏的各类地物的碳汇本时间\WIND_FROM_2017_2024_LandCover_Summary.csv"

def check_classes(path, label):
    df = pd.read_csv(path)
    print(f"Unique classes in {label}: {df['class_name'].unique()}")

try:
    check_classes(solar_lc_path, "Solar")
    check_classes(wind_lc_path, "Wind")
except Exception as e:
    print(e)
