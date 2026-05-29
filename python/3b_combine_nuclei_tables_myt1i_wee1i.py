import pandas as pd
from pathlib import Path

# Get current folder (where script is executed)
root = Path.cwd()

# Find all matching CSV files in subfolders
files = list(root.rglob("*_Results_nuclei_summary_transposed.csv"))

if not files:
    print("No matching files found.")
    exit()

print(f"Found {len(files)} files.")

# Read and combine
dfs = []
for f in files:
    print(f"Reading: {f}")
    df = pd.read_csv(f)
    dfs.append(df)

combined_df = pd.concat(dfs, ignore_index=True)

# Output filename = current folder name + suffix
output_name = f"{root.name}__Results_nuclei_summary_transposed_combined.csv"
output_path = root / output_name

combined_df.to_csv(output_path, index=False)

print(f"\nCombined file saved as: {output_path}")

# save filtered file with mitotic cells selected

# rules: 
# Skew (of CENPC) > 3
# Mean_normalized_w1405-0001    < 200 (Hoechst)
# Area > 4000

filtered_df = combined_df.copy()
filtered_df = filtered_df[filtered_df["Skew_w1405-0004"] > 3]                   # CENCP Skew
#filtered_df = filtered_df[filtered_df["Mean_normalized_w1405-0001"] < 200]      # hoecsht signal
filtered_df = filtered_df[filtered_df["Area_w1405-0001"] > 4000]                # any Area

# Output filename_22 = current folder name + suffix
output_name_2 = f"{root.name}__Results_nuclei_summary_transposed_combined_filtered.csv"
output_path_2 = root / output_name_2

filtered_df.to_csv(output_path_2, index=False)

print(f"\nFiltered file saved as: {output_path_2}")








