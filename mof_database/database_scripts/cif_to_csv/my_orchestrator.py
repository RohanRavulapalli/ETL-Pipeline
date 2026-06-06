#!/usr/bin/env python3
'''
This file will extract all required file names from the MOF database,
retrieve all file data, and then call a script to append all of the 
data into CSV files.

Requirements:
- updated_mof_cif_to_csv_simple.py must be in the same directory as this script
- Output CSV files (atom_sites.csv, bonds.csv) will be created in current working directory

Usage:
    python orchestrator.py <csv_file> <database_folder> [--column COLUMN]
    
    csv_file: Path to CSV file (can be relative or absolute)
    database_folder: Full path to folder containing CIF files
    --column: Column name containing filenames (default: "filename")
'''
import pandas as pd
from pathlib import Path
import subprocess
import argparse

def read_filenames(csv_path: str, column: str) -> list[str]:
    '''
    this function takes a given CSV file, assumed to contain
    a column of cif filenames, and converts it into a list
    of relevant filenames.

    csv_path: full path to the CSV file

    column: name of the column containing cif filenames (should be a string)

    NOTE: filenames listed in the specified column of the CSV file are expected to be
    similar to the following format: str_m5_o16_o16_sra_sym.55
    '''
    try:
        csv_data = pd.read_csv(csv_path) # reads CSV file into a pandas dataframe 

        if column not in csv_data.columns:
            print(f"[WARN] Column '{column}' not found in {csv_path}")
            print(f"Available columns: {list(csv_data.columns)}")
            return []

        list_of_filenames = (csv_data[column].dropna()
                                         .apply(lambda x: x + '.cif') # adds cif file extension
                                         .tolist()) # convert to list
        
        if not list_of_filenames:
            print(f"[WARN] No valid filenames found in column '{column}' of {csv_path}")
        else:
            print(f"Found {len(list_of_filenames)} target filenames in CSV")
    
        return list_of_filenames
    
    except Exception as e:
    
        print(f"[WARN] Could not read {csv_path}: {e}")

        return []

def locate_all_files (cif_filenames: list[str], db_folder_path: str) -> list[str]:
    '''
    takes in a list of cif filenames and extracts
    the relevant cif file paths from a specified folder

    example filename list: ['str_m5_o16_o16_sra_sym.77.cif', 'str_m5_o16_o16_sra_sym.55.cif',....,]

    this function can only take lists containing filenames of this format.

    cif_filenames: list of filenames of specified format

    db_folder_path: the path to a folder assumed to contain various cif files
    
    this function will return a list of cif file paths
    '''
    matching_files = []

    for cif_file in Path(db_folder_path).glob("*.cif"):
        if cif_file.name in cif_filenames:
            matching_files.append(str(cif_file)) # appending path string

    print(f"{len(matching_files)} found in MOF database")

    return matching_files

def main():
    '''
    Should call the imported python script on all relevant file paths to append the data of the 
    cif files to the relevant locations 
    '''

    parser = argparse.ArgumentParser(description="Extract MOF data from matching CIF files")
    parser.add_argument("csv_file", help="CSV file containing target filenames")
    parser.add_argument("database_folder", help="Folder containing CIF files")  
    parser.add_argument("--column", default="filename", help="Column name containing filenames (default: filename)") 
    '''
    running this through command line should feature 3 arguments: csv_File, database_folder, --column

    example cmd run of this program:

        python my_orchestrator.py targets.csv /database --column filename    
    '''

    args = parser.parse_args()

    try:
        target_filenames = read_filenames(args.csv_file, args.column)

        if not target_filenames:
            print("Exiting due to no target filenames")
            return

        matching_files = locate_all_files(target_filenames, args.database_folder)

        if matching_files:
            import updated_mof_cif_to_csv_simple
            updated_mof_cif_to_csv_simple.process_file_list(matching_files)
            # note that due to window cmd character limits, we are going to directly process the files
            # using the mof_cif_to_csv script rather than making use of command line
            print(f"Successfully processed {len(matching_files)} files!")
        else:
            print("No matching files found")
            
    except Exception as e:
           print(f"Error: {e}")

if __name__ == "__main__":
    main()




    


