#!/usr/bin/env python3

import sys

# Check if pandas is installed
try:
    import pandas as pd
except ModuleNotFoundError:
    print("ERROR: pandas is not installed. Install it with:")
    print("    python3 -m pip install pandas")
    sys.exit(1)

from pathlib import Path

def find_file(folder, suffix):
    """Find exactly one file in folder ending with suffix."""
    files = list(folder.glob(f"*{suffix}"))
    if len(files) != 1:
        raise RuntimeError(f"Expected exactly one file ending with {suffix}, found {len(files)}")
    return files[0]

def main(folder_path="."):
    folder = Path(folder_path)

    # Find input files
    bg_file = find_file(folder, "_Results_background.csv")
    nuc_file = find_file(folder, "_Results_nuclei.csv")

    print(f"Background file: {bg_file.name}")
    print(f"Nuclei file:     {nuc_file.name}")

    # Load data
    bg = pd.read_csv(bg_file)
    nuc = pd.read_csv(nuc_file)

    if "Label" not in bg.columns or "Label" not in nuc.columns:
        raise RuntimeError("Both CSV files must contain a 'Label' column")

    # Identify numeric columns to normalize
    numeric_cols = nuc.select_dtypes(include="number").columns.tolist()
    if not numeric_cols:
        # Try converting text numbers to float
        for col in nuc.columns:
            if col != "Label":
                nuc[col] = pd.to_numeric(nuc[col], errors='coerce')
        numeric_cols = nuc.select_dtypes(include="number").columns.tolist()
        if not numeric_cols:
            raise RuntimeError("No numeric columns found to normalize")

    # Prepare background lookup by background ID
    background_ids = [
        "_w1405-0001:",
        "_w1405-0002:",
        "_w1405-0003:",
    ]

    bg_lookup = {}

    for bg_id in background_ids:
        matches = bg[bg["Label"].str.contains(bg_id, regex=False, na=False)]
        if len(matches) != 1:
            raise RuntimeError(
                f"Expected exactly one background row for {bg_id}, found {len(matches)}"
            )
        # Explicitly cast to float
        bg_lookup[bg_id] = matches.iloc[0][numeric_cols].astype(float)

    # Normalize nuclei
    nuc_norm = nuc.copy()

    for bg_id, bg_values in bg_lookup.items():
        mask = nuc_norm["Label"].str.contains(bg_id, regex=False, na=False)
        nuc_norm.loc[mask, numeric_cols] = (
            nuc_norm.loc[mask, numeric_cols].astype(float) - bg_values.values
        )

    # Round numeric columns to 4 decimals
    nuc_norm[numeric_cols] = nuc_norm[numeric_cols].round(4)

    # --- Save full normalized file ---
    output_full = nuc_file.with_name(
        nuc_file.stem.replace("_Results_nuclei", "_Results_nuclei_normalized") + ".csv"
    )
    nuc_norm.to_csv(output_full, index=False, float_format="%.4f")
    print(f"Full normalized file written to: {output_full.name}")

    # --- Prepare summary smaller file ---
    required_columns = ["Mean", "Median", "Area", "Skew", "Kurt"]
    missing_cols = [c for c in required_columns if c not in nuc_norm.columns]
    if missing_cols:
        raise RuntimeError(f"Cannot create summary file, missing columns: {missing_cols}")

    summary = pd.DataFrame()
    summary["Mean_normalized"] = nuc_norm["Mean"]
    summary["Median_normalized"] = nuc_norm["Median"]
    summary["Area"] = nuc["Area"].astype(float)  # original Area
    summary["total_intensity"] = (summary["Area"] * summary["Mean_normalized"]).round(4)
    summary["Label"] = nuc["Label"]
    summary["Skew"] = nuc["Skew"]
    summary["Kurt"] = nuc["Kurt"]


    # Reorder columns: first column is 1..N (no name), then Label, then numeric columns
    summary = summary[["Label", "Mean_normalized", "Median_normalized", "Area", "total_intensity", "Skew", "Kurt"]]
    summary.insert(0, "", range(1, len(summary) + 1))

    # Save summary file
    output_summary = nuc_file.with_name(
        nuc_file.stem.replace("_Results_nuclei", "_Results_nuclei_summary") + ".csv"
    )
    summary.to_csv(output_summary, index=False, float_format="%.4f")
    print(f"Summary file written to: {output_summary.name}")


    # ==========================================================
    # --- Create TRANSPOSED (wide) summary: one row per nucleus
    # ==========================================================

    # --------------------------------------------------
    # Remove mask rows (binary mask ROIs)
    # Masks have Mean/Median equal to 0 or 255
    # --------------------------------------------------

    mask_rows = (
        summary["Mean_normalized"].isin([0, 255]) &
        summary["Median_normalized"].isin([0, 255])
    )

    n_removed = mask_rows.sum()
    if n_removed > 0:
        print(f"Removing {n_removed} mask rows before transposing")

    summary = summary.loc[~mask_rows].reset_index(drop=True)

    

    # Work from the summary dataframe you already created
    summary_long = summary.copy()

    # Extract channel ID (e.g. w1405-0001) from Label
    summary_long["channel"] = summary_long["Label"].str.extract(r"(w1405-\d{4})")

    # Extract nucleus ID by removing channel suffix
    summary_long["nucleus_id"] = summary_long["Label"].str.replace(
        r"_w1405-\d{4}:?", "", regex=True
    )

    value_cols = ["Mean_normalized", "Median_normalized", "Area", "total_intensity", "Skew", "Kurt"]

    # Pivot to wide format
    summary_wide = summary_long.pivot(
        index="nucleus_id",
        columns="channel",
        values=value_cols
    )

    # Flatten MultiIndex columns
    summary_wide.columns = [
        f"{metric}_{channel}" for metric, channel in summary_wide.columns
    ]

    summary_wide = summary_wide.reset_index()

    # Save transposed summary
    output_transposed = nuc_file.with_name(
        nuc_file.stem.replace("_Results_nuclei", "_Results_nuclei_summary_transposed") + ".csv"
    )

    summary_wide.to_csv(output_transposed, index=False, float_format="%.4f")

    print(f"Transposed summary file written to: {output_transposed.name}")



if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        main()




