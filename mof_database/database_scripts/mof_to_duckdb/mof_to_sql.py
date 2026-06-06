'''
Given a folder of CIF files, this program should parse each file and its
given attributes into two tables:

    - one table for storing the attributes of the file's atom sites 

    - one table for storing the attributes of the file's bonds

Then, these two tables are appended to existing comprehensive 
database tables for atom sites and bonds stored in a duckdb database hosted on MotherDuck 

SYSTEM REQUIREMENTS:

    - you must know the path to the folder containing the CIF files you wish to process

    - you must have a valid motherduck token saved as PERMANENT 
      environment variable under the name motherduck_token (or MOTHERDUCK_TOKEN
      if using linux since linux is case-sensitive)

    - the python libraries imported below should be installed

    - the file cif_fields.py, containing a dictionary mapping raw CIF attribute names to preferred CIF attribute names
      should be in the same working directory as this file.

NOTE: this script still needs lots of changes in regards to edge cases, logging,
      error handling and query optimization against CIF data.
'''
import duckdb 
import pandas as pd
import sys
import os 
from pymatgen.io.cif import *
from pathlib import Path
import time
from joblib import Parallel, delayed
import warnings
from cif_fields import cif_fields # dictionary for renaming attributes of CIFs
warnings.filterwarnings("ignore")
os.environ['PYTHONWARNINGS'] = "ignore"

def return_attributes(file:str, contains_none:bool) -> dict:

    
    '''
    Given a CIF file (full path), this function returns a dictionary containing the attributes of the CIF file.

    We use the CifBlock object located in the pymatgen library.

    A CifBlock is an object that stores data for a CIF.

    It contains three attributes:

        data: a dictionary that stores the attributes of CIF (e.g. partial charge, cell lengths, atom sites).
                keys = attributes, values = values of the attributes 

        loops – list of lists of keys, grouped by which loop they should appear in

        header – string representing the cif header 

    the .from_str method takes in a string representation of a CIF, and returns a CifBlock.
    '''

    with open(file, 'r') as f:

        try:     

            text = f.read()

            block = CifBlock.from_str(text)

        except Exception as e:

            print(f"Warning: failed to process {file}")

            contains_none = True

            return None

        cif_attributes = block.data

        cif_attributes['file'] = file.name
       
        return cif_attributes

def get_connection(db_name="carbon_db"):
    return duckdb.connect(f"md:{db_name}")

def extract_cif_data(cif_file_list: list, n_jobs = -1, print_time_stats=True) -> dict():
    '''
    Given a list of cif file directories (each element = address of a cif file),
    this function calls return_attributes() returns a list of dictonaries, 
    where each dictionary represents a cif file and its parsed attributes.

    This function makes use of parallel processing through the use of the joblib library.
    n_jobs specifies the number of workers that will be used to process all the files.

    Specifying n_jobs = -1 (default value) means that joblib.Parallel will use the maximum
    number of workers (cores) available on your computer.

    The print_time_stats argument, if True, will print the time it took to process all of the files in the file list
    '''

    contains_none = False

    starttime = time.time()
    
    cif_file_data = Parallel(n_jobs=n_jobs)(delayed(return_attributes)(file, contains_none) for file in cif_file_list)
                # specifying -1 means maximum number of workers will be used.
                # Parallel() by default returns a list, so we 
                # end up with a list of dictionaries where each dict contains the attributes of a given cif file

    endtime = time.time()

    total_time = endtime - starttime

    if contains_none: 
        
       cif_file_data = [cf for cf in cif_file_data if cf is not None]

    print("File Processing Stats: \n")

    print(f"    {len(cif_file_data)} of {len(cif_file_list)} CIF files were successfully processed\n")

    if print_time_stats:

        if total_time <= 60:

            print(f"    CIF file processing took {total_time} seconds\n")

        else:
            
            print(f"    CIF file processing and parsing took {total_time / 60.0} minutes\n")

    return cif_file_data

def main():

    if len(sys.argv) < 2:

        print(f"command line usage: mof_sql.py <insert path of folder containing CIF files>")

        return None
    
    path = sys.argv[1]

    try: 

        file_directory_list = list(Path(path).glob('*.cif'))

    except Exception: 

        print(f"Error: failed to read CIF directory path {path}")

    num_files_found = len(file_directory_list)

    if (num_files_found == 0):

        print("No CIF files found in the specified directory.")
        
        return None

    print(f"\n{num_files_found} CIF Files Found in Specified Directory\n")


    cif_file_data = extract_cif_data(file_directory_list)     

    start = time.time()
    
    cif_table = (pd.DataFrame.from_records(cif_file_data)
                             .rename(columns = cif_fields))

    end = time.time()
    
    print("\nEntering Data Loading Stage:\n")

    print("    Entering Checkpoint 1: create temporary tables of CIF data\n")

    with get_connection('carbon_db') as conn:
        
        start = time.time()

        conn.sql("SET max_memory = '100GB';")

        conn.sql("SET memory_limit = '156GB';")

        conn.sql('''
                 SET VARIABLE ATOM_SITES_COLS = (
                 SELECT LIST(column_name)
                 FROM (DESCRIBE carbon_db.atom_sites_comprehensive));
                 '''
         )
        
        atom_sites_data = '''   
            CREATE TEMP TABLE atom_sites_data_temp AS (
            WITH required_attributes AS (
                SELECT  a.file,
                        CAST(b.partial_charge AS float) partial_charge,
                        b.atom_label,
                        b.element,
                        b.description,
                        CAST(b.fract_x AS float) fract_x,
                        CAST(b.fract_y AS float) fract_y,
                        CAST(b.fract_z AS float) fract_z,
                        CAST(a.length_a AS float) length_a,
                        CAST(a.length_b AS float) length_b,
                        CAST(a.length_c AS float) length_c,
                        CAST(a.alpha AS float) alpha,
                        CAST(a.beta AS float) beta,
                        CAST(a.gamma AS float) gamma
                FROM cif_table a
                        LEFT JOIN LATERAL (
                            SELECT  UNNEST(atom_label), 
                                    UNNEST(element),
                                    UNNEST(description),
                                    UNNEST(fract_x), 
                                    UNNEST(fract_y), 
                                    UNNEST(fract_z),
                                    UNNEST(partial_charge)
                        ) b(atom_label, 
                            element, 
                            description, 
                            fract_x, 
                            fract_y, 
                            fract_z,
                            partial_charge) ON TRUE
                )
                SELECT COLUMNS(col -> col in GETVARIABLE('ATOM_SITES_COLS')) 
                FROM required_attributes r
                        LEFT JOIN LATERAL (
                        SELECT b.cart_x, b.cart_y, b.cart_z
                        FROM carbon_db.fract_to_cart(r.length_a, 
                                                        r.length_b, 
                                                        r.length_C, 
                                                        r.alpha, 
                                                        r.beta, 
                                                        r.gamma,
                                                        r.fract_x,
                                                        r.fract_y,
                                                        r.fract_z) b
                    ) c ON TRUE
            );
        '''

        conn.sql(atom_sites_data)

        print(f"        successfully created temporary table for atom sites data\n")

        bonds_data = '''
                    CREATE TEMP TABLE bonds_data_temp AS (
                    SELECT 
                        DISTINCT
                        a.file, 
                        b.atom1_label, 
                        b.atom2_label,
                        b.bond_type
                    FROM cif_table a
                        LEFT JOIN LATERAL (
                            SELECT UNNEST(atom1_label), 
                                   UNNEST(atom2_label),
                                   UNNEST(bond_type)
                        ) b(atom1_label, 
                            atom2_label, 
                            bond_type) ON TRUE)
        '''

        conn.sql(bonds_data)

        print(f"        successfully created temporary table for bonds data\n")

        end = time.time()

        total = end - start 

        if (total >= 60):

            print(f"    Checkpoint 1 Time Taken: {total / 60.0} Minutes\n")

        else: 

            print(f"    Checkpoint 1 Time Taken: {total} Seconds\n")

        # batch processing data into target tables

        print("    Entering Checkpoint 2: loading data into target tables\n")
        
        start = time.time()

        print(f"        loading atom sites data:\n")

        as_loading_start = time.time()

        conn.sql(
            '''
            BEGIN TRANSACTION;
            
            INSERT INTO carbon_db.atom_sites_comprehensive BY NAME
                SELECT *
                FROM atom_sites_data_temp
                     ON CONFLICT 
                         DO UPDATE SET cart_x = EXCLUDED.cart_x,
                                       cart_y = EXCLUDED.cart_y,
                                       cart_z = EXCLUDED.cart_z;
            COMMIT;
            '''
        )

        as_loading_end = time.time()

        as_total_time = as_loading_end - as_loading_start

        print(f"            successfully loaded data into carbon_db.atom_sites_comprehensive:\n")

        if (as_total_time >= 60):

             print(f"             Time Taken To Load Atom Sites Data: {as_total_time / 60.0} Minutes\n")

        else: 

             print(f"             Time Taken To Load Atom Sites Data: {as_total_time} Seconds\n")

        print(f"        loading bonds data:\n")

        bds_loading_start = time.time()
        
        # Simple batch approach
        batch_size = 50000
        offset = 0
        
        conn.sql(
            '''
            BEGIN TRANSACTION;
            
            INSERT INTO carbon_db.bonds_comprehensive BY NAME
                SELECT *
                FROM bonds_data_temp
                     ON CONFLICT 
                         DO NOTHING;
            COMMIT;
            '''
        )

        bds_loading_end = time.time()

        bds_total_time = bds_loading_end - bds_loading_start

        print(f"            successfully loaded data into carbon_db.bonds_comprehensive:\n")

        if (bds_total_time >= 60):

             print(f"             Time Taken To Load Bonds Data: {bds_total_time / 60.0} Minutes\n")

        else: 

             print(f"             Time Taken To Load Bonds Data: {bds_total_time} Seconds\n")

        end = time.time()

        total = end - start 

        if (total >= 60):

            print(f"    Checkpoint 2 Time Taken: {total / 60.0} Minutes\n")

        else: 

            print(f"    Checkpoint 2 Time Taken: {total} Seconds\n")

if __name__ == "__main__":
    
    main()
