import pandas as pd
import glob
import os

def find_fid_sources(target_fids):
    input_dirs = [
        (r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\数据\土地覆盖数据\GEE_Wind_Analysis_2017", "WIND_FROM_2017_WithRing*.csv"),
        (r"Z:\Mywork\论文\全球绿色能源生态评估_2025.12.24\数据\土地覆盖数据\GEE_Wind_Analysis_2018_2024", "FROM_2017_Stats_For2018_2024*.csv")
    ]

    results = {}
    
    print(f"Searching for FIDs: {target_fids}")
    
    for dir_path, pattern in input_dirs:
        search_pattern = os.path.join(dir_path, pattern)
        files = glob.glob(search_pattern)
        print(f"Scanning {len(files)} files in {os.path.basename(dir_path)}...")
        
        for file_path in files:
            try:
                df = pd.read_csv(file_path, usecols=['fid'])
                found = df[df['fid'].isin(target_fids)]
                
                for fid in found['fid']:
                    results[fid] = os.path.basename(file_path)
                    
            except Exception as e:
                print(f"Error reading {os.path.basename(file_path)}: {e}")

    # Print results sorted by FID
    print("\n" + "="*50)
    print(f"{'FID':<10} | {'Filename'}")
    print("-" * 50)
    
    found_fids = sorted(results.keys())
    for fid in range(min(target_fids), max(target_fids)+1):
        if fid in results:
            print(f"{fid:<10} | {results[fid]}")
        else:
            print(f"{fid:<10} | NOT FOUND")
            
    print("="*50)

if __name__ == "__main__":
    find_fid_sources(range(1, 32))
