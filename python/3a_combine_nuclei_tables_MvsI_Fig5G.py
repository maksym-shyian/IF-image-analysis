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

# ---------------------------------------------------------
# save filtered file with mitotic cells selected
# rules:
# Area > 4000
# ---------------------------------------------------------

'''
filtered_df = combined_df.copy()

filtered_df = filtered_df[
    filtered_df["Area_w1405-0001"] > 4000
]

# Output filename_2 = current folder name + suffix
output_name_2 = (
    f"{root.name}__Results_nuclei_summary_transposed_combined_filtered.csv"
)
output_path_2 = root / output_name_2

filtered_df.to_csv(output_path_2, index=False)

print(f"\nFiltered file saved as: {output_path_2}")

'''

# ---------------------------------------------------------
# Additional analysis
# ---------------------------------------------------------

analysis_df = combined_df.copy()
analysis_df = analysis_df[
    analysis_df["Area_w1405-0001"] > 4000
]

# 1. Create ratio_RNAPII_to_DNA
analysis_df["ratio_RNAPII_to_DNA"] = (
    analysis_df["Mean_normalized_w1405-0002"] /
    analysis_df["Mean_normalized_w1405-0001"]
)

# 2. Create cell_cycle column
analysis_df["cell_cycle"] = analysis_df["Kurt_w1405-0001"].apply(
    lambda x: "M" if x <= -0.9 else "I"
)

# 3. Calculate average ratio for Interphase cells ("I")
mean_ratio_I = analysis_df.loc[
    analysis_df["cell_cycle"] == "I",
    "ratio_RNAPII_to_DNA"
].mean()


mean_I_abs = analysis_df.loc[
    analysis_df["cell_cycle"] == "I",
    "Mean_normalized_w1405-0002"
].mean()

print(f"\nAverage ratio_RNAPII_to_DNA for I cells: {mean_ratio_I}")

# 4. Create normalized MvsI ratio column
analysis_df["ratio_RNAPII_to_DNA_MvsI"] = (
    analysis_df["ratio_RNAPII_to_DNA"] / mean_ratio_I
)



analysis_df["RNAPII_abs_MvsI"] = (
    analysis_df["Mean_normalized_w1405-0002"] / mean_I_abs
)




# Sort so that M cells appear first
analysis_df = analysis_df.sort_values(
    by="cell_cycle",
    ascending=False
)

# Save final output
output_name_3 = (
    f"{root.name}__Results_nuclei_summary_transposed_combined_MvsI.csv"
)
output_path_3 = root / output_name_3

analysis_df.to_csv(output_path_3, index=False)

print(f"\nMvsI analysis file saved as: {output_path_3}")