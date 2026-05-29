# Microscopy Image Analysis Pipeline

Analysis scripts for IF microscopy quantification.

## Requirements
- Fiji/ImageJ 2.x
- Python 3.11

## Python packages: installed when running the python files

## Workflow

1. Group files with raw microscopy images into subfolders:
   Copy the '0_organize_files.py' file to the root folder.
   Run it in Python through terminal:

      for d in */; do
       echo "Organizing files in $d"
       (cd "$d" && python3 ../0_organize_files.py)
      done

2. Move to the folder with a given sample. Copy scripts there:
   1_fiji_macro_segment_cells_quantify_signal.ijm
   2_normalization.py

3. To segment cells, quantify signal intensities, run Fiji macro in Fiji:
   1_fiji_macro_segment_cells_quantify_signal.ijm

4. To normalize signal on chromosomes to background, run in Python: 
   2_normalization.py

   in terminal:

      for d in */; do
          if ls "$d"/*_Results_nuclei.csv >/dev/null 2>&1; then
              echo "Running normalization in $d"
              python3 2_normalization.py "$d"
          else
              echo "Skipping $d (no nuclei CSV)"
          fi
      done

5. Move to the root folder again. Copy and run the code to combine per-sample outputs in Python:
   3a_combine_nuclei_tables_MvsI_Fig5G.py

   in terminal:

   for d in */; do
      echo "Combining_nuclei_tables in d"
      (cd "$d" && python3 ../3a_combine_nuclei_tables_MvsI_Fig5G.py)
   done


## Output
- normalized intensity tables with Mitotic and Interphase cell-cycle classification (+intermediate caculations:
- 'Results_nuclei_summary_transposed_combined_MvsI.csv'