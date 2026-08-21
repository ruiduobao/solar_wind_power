import pandas as pd
import json
import os

# 模拟 parse_single_file 函数的核心逻辑
def test_parse(file_path, is_2017_correction=False):
    print(f"Testing file: {file_path}")
    IMPERVIOUS_CODE_FROM = 80
    
    cols = ['fid', 'stats_json']
    if is_2017_correction:
        cols.append('ring_stats_json')
        
    df = pd.read_csv(file_path, usecols=cols)
    print(f"Loaded {len(df)} rows")
    
    parsed_data = []
    
    # 过滤出 FID 1-31
    target_fids = set(range(1, 32))
    df_target = df[df['fid'].isin(target_fids)]
    print(f"Found {len(df_target)} target rows (FID 1-31)")
    
    if len(df_target) == 0:
        return []

    for _, row in df_target.iterrows():
        fid = row['fid']
        json_str = row['stats_json']
        
        print(f"\nProcessing FID: {fid}")
        
        if pd.isna(json_str) or json_str == "":
            print("  Skipping: Empty json_str")
            continue
            
        try:
            stats_list = json.loads(json_str)
            replaced = False
            
            if is_2017_correction:
                ring_json_str = row.get('ring_stats_json')
                
                if not pd.isna(ring_json_str) and ring_json_str != "":
                    try:
                        inner_total_area = 0
                        inner_impervious_area = 0
                        
                        for item in stats_list:
                            code = item.get('code')
                            area = item.get('sum', [0, 0])[1]
                            inner_total_area += area
                            if code == IMPERVIOUS_CODE_FROM:
                                inner_impervious_area += area
                        
                        print(f"  Inner Area: {inner_total_area}, Impervious: {inner_impervious_area}")
                        
                        if inner_total_area > 0:
                            inner_imp_ratio = inner_impervious_area / inner_total_area
                            print(f"  Inner Ratio: {inner_imp_ratio}")
                            
                            if inner_imp_ratio > 0.05:
                                print("  > Threshold 0.05, checking ring...")
                                ring_stats_list = json.loads(ring_json_str)
                                ring_total_area = 0
                                ring_impervious_area = 0
                                
                                for item in ring_stats_list:
                                    code = item.get('code')
                                    area = item.get('sum', [0, 0])[1]
                                    ring_total_area += area
                                    if code == IMPERVIOUS_CODE_FROM:
                                        ring_impervious_area += area
                                        
                                if ring_total_area > 0:
                                    ring_imp_ratio = ring_impervious_area / ring_total_area
                                    print(f"  Ring Ratio: {ring_imp_ratio}")
                                    
                                    if ring_imp_ratio < inner_imp_ratio:
                                        print("  !!! REPLACING !!!")
                                        # logic to replace...
                                        replaced = True
                    except Exception as e:
                        print(f"  Error in ring logic: {e}")
            
            # Output logic
            for item in stats_list:
                parsed_data.append({
                    'fid': fid,
                    'code': item.get('code'),
                    'replaced': replaced
                })
                
        except Exception as e:
            print(f"  Error parsing json: {e}")
            
    return parsed_data

if __name__ == "__main__":
    # 使用之前找到的包含 FID 1-31 的文件
    file_2017 = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\数据\土地覆盖数据\GEE_Wind_Analysis_2017\WIND_FROM_2017_WithRing_Batch_56.csv"
    file_2018 = r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\数据\土地覆盖数据\GEE_Wind_Analysis_2018_2024\FROM_2017_Stats_For2018_2024_Batch_199.csv"
    
    print("=== Testing 2017 File ===")
    results_2017 = test_parse(file_2017, is_2017_correction=True)
    print(f"Parsed {len(results_2017)} records from 2017 file")
    
    print("\n=== Testing 2018-2024 File ===")
    results_2018 = test_parse(file_2018, is_2017_correction=False)
    print(f"Parsed {len(results_2018)} records from 2018 file")
