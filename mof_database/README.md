# carbon_db - Metal-Organic Framework Database

## Overview

**carbon_db** is a MotherDuck database containing crystallographic and screening data for 324,426 hypothetical Metal-Organic Frameworks (MOFs) evaluated for wet flue gas CO2 capture applications. The database stores atomic coordinates, bond connectivity, unit cell parameters, and comprehensive CO2 adsorption screening results.

### Database Platform
- **Platform**: MotherDuck (cloud-hosted DuckDB)
- **Database Name**: `carbon_db`
- **Schema**: `main`

---

## Data Source

All data originates from the Materials Cloud MOF database:
- **Source**: [https://www.materialscloud.org/discover/mofs/](https://www.materialscloud.org/discover/mofs/)
- **DOI**: [10.24435/materialscloud:2018.0016/v3](https://doi.org/10.24435/materialscloud:2018.0016/v3)
- **Total Structures**: 324,426 hypothetical MOFs
- **Refined Structures**: 8,000+ MOFs with REPEAT charge calculations

### Citation
```
Boyd, P. G., Chidambaram, A., García-Díez, E., Ireland, C. P., Daff, T. D., 
Bounds, R., Gładysiak, A., Schouwink, P., Moosavi, S. M., Maroto-Valer, M. M., 
Reimer, J. A., Navarro, J. A. R., Woo, T. K., Garcia, S., Stylianou, K. C., & 
Smit, B. (2019). Data-driven design of metal-organic frameworks for wet flue 
gas CO2 capture. Materials Cloud Archive, 10.24435/materialscloud:2018.0016/v3
```

### Screening Methodology
- **Charge Method**: MEPO-QEq for all structures; REPEAT method for top 8,000+ structures
- **Simulation Conditions**:
  - Post-combustion flue gas: 298K/313K at 0.15 bar CO2
  - Mixture adsorption: 298K with 0.15:0.85 CO2/N2 at 1 bar total pressure
- **Desorption Conditions**:
  - Vacuum swing: 0.1 bar CO2 at 363K
  - Temperature swing: 0.7 bar CO2 at 413K
- **Additional Analysis**: Adsorbaphore identification (CO2 binding site patterns)

---

## Database Schema

The database contains **5 tables** organized into two categories:

### Comprehensive Tables (All 324,426 MOFs)
1. **atom_sites_comprehensive** - Atomic positions and unit cell parameters
2. **bonds_comprehensive** - Bond connectivity information

### Top MOF Tables (Refined subset of 8,000+ MOFs)
3. **top_mof_atom_sites** - Atomic positions for top-performing MOFs
4. **top_mof_bonds** - Bond connectivity for top-performing MOFs  
5. **top_mof_screening_data** - Detailed CO2 screening results with REPEAT charges

---

## Table Definitions

### 1. atom_sites_comprehensive

Stores atomic positions in both fractional and Cartesian coordinates for all MOF structures.

**Schema:**
```sql
CREATE TABLE carbon_db.atom_sites_comprehensive (
    file               VARCHAR NOT NULL,     -- CIF filename
    atom_label         VARCHAR NOT NULL,     -- Unique atom identifier within file
    element            VARCHAR,              -- Element symbol (e.g., 'C', 'N', 'Zn')
    description        VARCHAR,              -- Atom type description
    fract_x            DOUBLE,               -- Fractional x-coordinate
    fract_y            DOUBLE,               -- Fractional y-coordinate
    fract_z            DOUBLE,               -- Fractional z-coordinate
    partial_charge     DOUBLE,               -- Atom partial charge (MEPO-QEq method)
    length_a           DOUBLE,               -- Unit cell length a (Angstroms)
    length_b           DOUBLE,               -- Unit cell length b (Angstroms)
    length_c           DOUBLE,               -- Unit cell length c (Angstroms)
    alpha              DOUBLE,               -- Unit cell angle α (degrees)
    beta               DOUBLE,               -- Unit cell angle β (degrees)
    gamma              DOUBLE,               -- Unit cell angle γ (degrees)
    cart_x             DOUBLE,               -- Cartesian x-coordinate (Angstroms)
    cart_y             DOUBLE,               -- Cartesian y-coordinate (Angstroms)
    cart_z             DOUBLE,               -- Cartesian z-coordinate (Angstroms)
    PRIMARY KEY (file, atom_label)
);
```

**Key Points:**
- Each row represents one atom site in a MOF structure
- Multiple atoms per file means **duplicate filenames** across rows
- Cartesian coordinates are computed from fractional coordinates using unit cell parameters
- Primary key ensures no duplicate atom labels within the same file

**Row Count Behavior:**
```sql
-- Total atom sites across all structures (millions of rows)
SELECT COUNT(*) FROM carbon_db.atom_sites_comprehensive;

-- Number of unique MOF structures (should be ~324,426)
SELECT COUNT(DISTINCT file) FROM carbon_db.atom_sites_comprehensive;

-- Average atoms per structure
SELECT COUNT(*) / COUNT(DISTINCT file) AS avg_atoms_per_structure
FROM carbon_db.atom_sites_comprehensive;
```

---

### 2. bonds_comprehensive

Stores bond connectivity between atoms for all MOF structures.

**Schema:**
```sql
CREATE TABLE carbon_db.bonds_comprehensive (
    file            VARCHAR,              -- CIF filename
    atom1_label     VARCHAR,              -- First atom label
    atom2_label     VARCHAR,              -- Second atom label
    bond_type       VARCHAR,              -- Bond type (e.g., 'S', 'D', 'T' for single/double/triple)
    PRIMARY KEY (file, atom1_label, atom2_label, bond_type)
);
```

**Key Points:**
- Each row represents one bond between two atoms
- Multiple bonds per file means **duplicate filenames** across rows
- Primary key prevents duplicate bond entries

**Row Count Behavior:**
```sql
-- Total bonds across all structures
SELECT COUNT(*) FROM carbon_db.bonds_comprehensive;

-- Number of unique MOF structures with bond data
SELECT COUNT(DISTINCT file) FROM carbon_db.bonds_comprehensive;

-- Average bonds per structure
SELECT COUNT(*) / COUNT(DISTINCT file) AS avg_bonds_per_structure
FROM carbon_db.bonds_comprehensive;
```

---

### 3. top_mof_atom_sites

Identical structure to `atom_sites_comprehensive` but contains only the 8,000+ top-performing MOFs with refined REPEAT charge calculations.

**Schema:**
```sql
CREATE TABLE carbon_db.top_mof_atom_sites (
    file               VARCHAR NOT NULL,
    atom_label         VARCHAR NOT NULL,
    element            VARCHAR,
    description        VARCHAR,
    fract_x            DOUBLE,
    fract_y            DOUBLE,
    fract_z            DOUBLE,
    partial_charge     DOUBLE,              -- Refined with REPEAT method
    length_a           DOUBLE,
    length_b           DOUBLE,
    length_c           DOUBLE,
    alpha              DOUBLE,
    beta               DOUBLE,
    gamma              DOUBLE,
    cart_x             DOUBLE,
    cart_y             DOUBLE,
    cart_z             DOUBLE,
    PRIMARY KEY (file, atom_label)
);
```

**Usage:**
```sql
-- Count top MOF structures
SELECT COUNT(DISTINCT file) FROM carbon_db.top_mof_atom_sites;
```

---

### 4. top_mof_bonds

Identical structure to `bonds_comprehensive` but contains only the top-performing MOFs.

**Schema:**
```sql
CREATE TABLE carbon_db.top_mof_bonds (
    file            VARCHAR,
    atom1_label     VARCHAR,
    atom2_label     VARCHAR,
    bond_type       VARCHAR,
    PRIMARY KEY (file, atom1_label, atom2_label, bond_type)
);
```

---

### 5. top_mof_screening_data

Comprehensive CO2 adsorption screening results for the top-performing MOFs. Contains **66 columns** of screening data.

**Schema (grouped by category):**

**File Identifier:**
```sql
File VARCHAR  -- CIF filename
```

**CO2 Uptake (Pure Gas @ 298K, 0.15 bar):**
```sql
CO2_uptake_P0.15bar_T298K [mmol/g]                    DOUBLE
CO2_uptake_error_P0.15bar_T298K [mmol/g]             DOUBLE
heat_adsorption_CO2_P0.15bar_T298K [kcal/mol]        DOUBLE
heat_adsorption_error_CO2_P0.15bar_T298K [kcal/mol]  DOUBLE
excess_CO2_uptake_P0.15bar_T298K [mmol/g]            DOUBLE
```

**CO2 Uptake (Pure Gas @ 363K, 0.10 bar - Vacuum Swing):**
```sql
CO2_uptake_P0.10bar_T363K [mmol/g]                    DOUBLE
CO2_uptake_error_P0.10bar_T363K [mmol/g]             DOUBLE
heat_adsorption_CO2_P0.10bar_T363K [kcal/mol]        DOUBLE
heat_adsorption_error_CO2_P0.10bar_T363K [kcal/mol]  DOUBLE
excess_CO2_uptake_P0.10bar_T363K [mmol/g]            DOUBLE
```

**CO2 Uptake (Pure Gas @ 413K, 0.70 bar - Temperature Swing):**
```sql
CO2_uptake_P0.70bar_T413K [mmol/g]                    DOUBLE
CO2_uptake_error_P0.70bar_T413K [mmol/g]             DOUBLE
heat_adsorption_CO2_P0.70bar_T413K [kcal/mol]        DOUBLE
heat_adsorption_error_CO2_P0.70bar_T413K [kcal/mol]  DOUBLE
excess_CO2_uptake_P0.70bar_T413K [mmol/g]            DOUBLE
```

**Working Capacities:**
```sql
working_capacity_vacuum_swing [mmol/g]          DOUBLE
working_capacity_temperature_swing [mmol/g]     DOUBLE
```

**Binary Mixture (CO2/N2 @ 298K, 0.15:0.85 ratio):**
```sql
CO2_binary_uptake_P0.15bar_T298K [mmol/g]                    DOUBLE
CO2_binary_uptake_error_P0.15bar_T298K [mmol/g]             DOUBLE
heat_adsorption_CO2_binary_P0.15bar_T298K [kcal/mol]        DOUBLE
heat_adsorption_error_CO2_binary_P0.15bar_T298K [kcal/mol]  DOUBLE
excess_CO2_binary_uptake_P0.15bar_T298K [mmol/g]            DOUBLE

N2_binary_uptake_P0.85bar_T298K [mmol/g]                     DOUBLE
N2_binary_uptake_error_P0.85bar_T298K [mmol/g]              DOUBLE
heat_adsorption_N2_binary_P0.85bar_T298K [kcal/mol]         DOUBLE
heat_adsorption_error_N2_binary_P0.85bar_T298K [kcal/mol]   DOUBLE
excess_N2_binary_uptake_P0.85bar_T298K [mmol/g]             DOUBLE

CO2/N2_selectivity                                           DOUBLE
```

**Structural Properties:**
```sql
volume [A^3]                                             DOUBLE
weight [u]                                               DOUBLE
surface_area [m^2/g]                                     DOUBLE
void_fraction                                            DOUBLE
void_volume [cm^3/g]                                     DOUBLE
largest_free_sphere_diameter [A]                         DOUBLE
largest_included_sphere_along_free_sphere_path_diameter [A]  DOUBLE
largest_included_sphere_diameter [A]                     DOUBLE
```

**Composition:**
```sql
functional_groups    VARCHAR
metal_linker         BIGINT
organic_linker1      BIGINT
organic_linker2      BIGINT
topology             VARCHAR
```

**REPEAT Charge Recalculations:**
```sql
CO2_uptake_REPEAT_chg_P0.15bar_T298K [mmol/g]                          DOUBLE
CO2_uptake_error_REPEAT_chg_P0.15bar_T313K [mmol/g]                   DOUBLE
heat_adsorption_CO2_REPEAT_chg_P0.15bar_T298K [kcal/mol]              DOUBLE
heat_adsorption_error_CO2_REPEAT_chg_P0.15bar_T298K [kcal/mol]        DOUBLE

CO2_uptake_REPEAT_chg_P0.15bar_T313K [mmol/g]                          DOUBLE
heat_adsorption_CO2_REPEAT_chg_P0.15bar_T313K [kcal/mol]              DOUBLE
heat_adsorption_error_CO2_REPEAT_chg_P0.15bar_T313K [kcal/mol]        DOUBLE

CO2_uptake_REPEAT_chg_P0.10bar_T363K [mmol/g]                          DOUBLE
heat_adsorption_CO2_REPEAT_chg_P0.10bar_T363K [kcal/mol]              DOUBLE
heat_adsorption_error_CO2_REPEAT_chg_P0.10bar_T363K [kcal/mol]        DOUBLE

CO2_uptake_REPEAT_chg_P0.70bar_T413K [mmol/g]                          DOUBLE
heat_adsorption_CO2_REPEAT_chg_P0.70bar_T413K [kcal/mol]              DOUBLE
heat_adsorption_error_CO2_REPEAT_chg_P0.70bar_T413K [kcal/mol]        DOUBLE

CO2/N2_selectivity_REPEAT_chg                                          DOUBLE
working_capacity_vacuum_swing_REPEAT_chg [mmol/g]                      DOUBLE
working_capacity_temperature_swing_REPEAT_chg [mmol/g]                 DOUBLE

CO2/N2_selectivity_REPEAT_chg_T313K_adsorption                         DOUBLE
working_capacity_vacuum_swing_REPEAT_chg_T313K_adsorption [mmol/g]     DOUBLE
working_capacity_temperature_swing_REPEAT_chg_T313K_adsorption [mmol/g] DOUBLE
```

**Henry Coefficients:**
```sql
henry_coefficient_CO2_298K [mol/kg/bar]    DOUBLE
henry_coefficient_N2_298K [mol/kg/bar]     DOUBLE
henry_coefficient_H2O_298K [mol/kg/bar]    DOUBLE
```

**Adsorbaphore Analysis:**
```sql
clique_density [mmol/cm^3]    DOUBLE
adsorbaphore_label            VARCHAR
```

**Key Points:**
- One row per MOF structure (no duplicate filenames)
- Contains refined REPEAT charge calculations
- Includes working capacities for both vacuum and temperature swing processes
- Adsorbaphore data identifies common CO2 binding site patterns

---

## Custom SQL Macros

The database includes custom DuckDB macros for coordinate transformations, defined in `conversion_macros.sql`.

### degree_to_radians
Converts angles from degrees to radians.

```sql
CREATE MACRO carbon_db.degree_to_radians(angle, angle_in_degrees := True)
```

**Usage:**
```sql
SELECT carbon_db.degree_to_radians(90.0);  -- Returns π/2
```

### fractional_to_cartesian_matrix
Builds the 3×3 transformation matrix for converting fractional to Cartesian coordinates.

```sql
CREATE MACRO carbon_db.fractional_to_cartesian_matrix(
    a, b, c,              -- Unit cell lengths
    alpha, beta, gamma,   -- Unit cell angles
    angle_in_degrees := True
) AS TABLE
```

**Returns:** Table with columns `col1`, `col2`, `col3`, `corresponding_coordinate`

### fract_to_cart
Converts fractional coordinates to Cartesian coordinates using unit cell parameters.

```sql
CREATE MACRO carbon_db.fract_to_cart(
    a, b, c,              -- Unit cell lengths (Angstroms)
    alpha, beta, gamma,   -- Unit cell angles (degrees)
    fract_x, fract_y, fract_z,  -- Fractional coordinates
    angle_in_degrees := True
) AS TABLE
```

**Returns:** Table with columns `cart_x`, `cart_y`, `cart_z`

**Example:**
```sql
-- Convert fractional (0.5, 0.5, 0.5) to Cartesian
SELECT * 
FROM carbon_db.fract_to_cart(
    10.0, 10.0, 10.0,     -- Unit cell: 10Å × 10Å × 10Å
    90.0, 90.0, 90.0,     -- Orthogonal cell
    0.5, 0.5, 0.5         -- Center of unit cell
);
-- Returns: cart_x=5.0, cart_y=5.0, cart_z=5.0
```

---

## Common Queries

### Count Structures

**Understanding Counts:**
Due to the nature of CIF (Crystallographic Information File) format, each MOF structure contains multiple atoms and bonds. Therefore:
- `COUNT(*)` returns the number of **rows** (atoms or bonds)
- `COUNT(DISTINCT file)` returns the number of **unique structures**

```sql
-- Total unique MOF structures (should return ~324,426)
SELECT COUNT(DISTINCT file) AS total_structures
FROM carbon_db.atom_sites_comprehensive;

-- Total atom sites across all structures
SELECT COUNT(*) AS total_atoms
FROM carbon_db.atom_sites_comprehensive;

-- Total bonds across all structures
SELECT COUNT(*) AS total_bonds
FROM carbon_db.bonds_comprehensive;

-- Top MOF structures (should return ~8,000+)
SELECT COUNT(DISTINCT file) AS top_structures
FROM carbon_db.top_mof_atom_sites;
```

### Retrieve MOF Structure Data

```sql
-- Get all atoms for a specific MOF
SELECT 
    atom_label,
    element,
    fract_x, fract_y, fract_z,
    cart_x, cart_y, cart_z,
    partial_charge
FROM carbon_db.atom_sites_comprehensive
WHERE file = 'str_m5_o16_o22_sra_sym.59.cif';

-- Get unit cell parameters for a MOF
SELECT DISTINCT
    file,
    length_a, length_b, length_c,
    alpha, beta, gamma
FROM carbon_db.atom_sites_comprehensive
WHERE file = 'str_m5_o16_o22_sra_sym.59.cif';

-- Get bond connectivity for a MOF
SELECT 
    atom1_label,
    atom2_label,
    bond_type
FROM carbon_db.bonds_comprehensive
WHERE file = 'str_m5_o16_o22_sra_sym.59.cif';
```

### Element Analysis

```sql
-- Count atoms by element across all structures
SELECT 
    element,
    COUNT(*) AS atom_count,
    COUNT(DISTINCT file) AS structures_with_element
FROM carbon_db.atom_sites_comprehensive
GROUP BY element
ORDER BY atom_count DESC;

-- Average composition per structure
SELECT 
    element,
    AVG(atom_count) AS avg_per_structure
FROM (
    SELECT file, element, COUNT(*) AS atom_count
    FROM carbon_db.atom_sites_comprehensive
    GROUP BY file, element
)
GROUP BY element
ORDER BY avg_per_structure DESC;
```

### Screening Data Analysis

```sql
-- Top 10 MOFs by CO2 uptake
SELECT 
    File,
    "CO2_uptake_P0.15bar_T298K [mmol/g]" AS co2_uptake,
    "surface_area [m^2/g]" AS surface_area,
    void_fraction
FROM carbon_db.top_mof_screening_data
ORDER BY "CO2_uptake_P0.15bar_T298K [mmol/g]" DESC
LIMIT 10;

-- MOFs with best working capacity (vacuum swing)
SELECT 
    File,
    "working_capacity_vacuum_swing [mmol/g]" AS vacuum_swing_capacity,
    "CO2/N2_selectivity" AS selectivity
FROM carbon_db.top_mof_screening_data
ORDER BY "working_capacity_vacuum_swing [mmol/g]" DESC
LIMIT 10;

-- Filter by CO2/N2 selectivity threshold
SELECT 
    File,
    "CO2/N2_selectivity" AS selectivity,
    "CO2_uptake_P0.15bar_T298K [mmol/g]" AS co2_uptake
FROM carbon_db.top_mof_screening_data
WHERE "CO2/N2_selectivity" > 100
ORDER BY "CO2_uptake_P0.15bar_T298K [mmol/g]" DESC;
```

### Join Operations

```sql
-- Combine structural and screening data
SELECT 
    s.File,
    COUNT(DISTINCT a.atom_label) AS num_atoms,
    s."CO2_uptake_P0.15bar_T298K [mmol/g]" AS co2_uptake,
    s."surface_area [m^2/g]" AS surface_area
FROM carbon_db.top_mof_screening_data s
LEFT JOIN carbon_db.top_mof_atom_sites a ON s.File = a.file
GROUP BY s.File, s."CO2_uptake_P0.15bar_T298K [mmol/g]", s."surface_area [m^2/g]"
ORDER BY co2_uptake DESC
LIMIT 10;

-- Analyze atom types in top performers
SELECT 
    a.element,
    AVG(s."CO2_uptake_P0.15bar_T298K [mmol/g]") AS avg_co2_uptake
FROM carbon_db.top_mof_atom_sites a
JOIN carbon_db.top_mof_screening_data s ON a.file = s.File
GROUP BY a.element
HAVING COUNT(DISTINCT a.file) > 100  -- Elements in 100+ structures
ORDER BY avg_co2_uptake DESC;
```

### Coordinate Transformation Examples

```sql
-- Verify Cartesian coordinate calculations
SELECT 
    file,
    atom_label,
    fract_x, fract_y, fract_z,
    cart_x, cart_y, cart_z,
    -- Recalculate using macro
    (SELECT c.cart_x FROM carbon_db.fract_to_cart(
        a.length_a, a.length_b, a.length_c,
        a.alpha, a.beta, a.gamma,
        a.fract_x, a.fract_y, a.fract_z
    ) c) AS recalc_cart_x
FROM carbon_db.atom_sites_comprehensive a
WHERE file = 'str_m5_o16_o22_sra_sym.59.cif'
LIMIT 5;
```

---

## Data Pipelines

Two primary workflows exist for loading data into the database:

### 1. Direct Upload Pipeline (mof_to_sql.py)

Processes CIF files and uploads directly to MotherDuck.

**Process Flow:**
1. Parse CIF files using pymatgen library
2. Extract atom sites and bonds into pandas DataFrames
3. Transform fractional to Cartesian coordinates using SQL macros
4. Insert data into `atom_sites_comprehensive` and `bonds_comprehensive` tables
5. Handle conflicts with `ON CONFLICT DO UPDATE/NOTHING` clauses

**Usage:**
```bash
python mof_to_sql.py /path/to/cif/folder
```

**Requirements:**
- MotherDuck token in environment variable `motherduck_token`
- Python libraries: duckdb, pandas, pymatgen, joblib

**Performance:**
- Parallel processing using joblib
- Batch inserts with configurable memory limits
- Transaction-based loading

### 2. CSV Export Pipeline (my_orchestrator.py + updated_mof_cif_to_csv_simple.py)

Processes targeted MOF files and exports to CSV format.

**Process Flow:**
1. Read target filenames from CSV (e.g., `targets.csv`)
2. Locate matching CIF files in database folder
3. Parse CIF files and extract data
4. Generate Cartesian coordinates using numpy
5. Export to `atom_sites.csv` and `bonds.csv`

**Usage:**
```bash
python my_orchestrator.py targets.csv /path/to/database --column filename
```

**Output Files:**
- `atom_sites.csv` - Atomic positions and unit cell data
- `bonds.csv` - Bond connectivity data

---

## File Formats

### CIF (Crystallographic Information File)

Input files follow the standard CIF format with MOF-specific fields:

**Key Fields:**
- `_atom_site_label` - Unique atom identifier
- `_atom_site_type_symbol` - Element symbol
- `_atom_site_fract_x/y/z` - Fractional coordinates
- `_atom_type_partial_charge` - Partial charge (MEPO-QEq or REPEAT method)
- `_cell_length_a/b/c` - Unit cell dimensions
- `_cell_angle_alpha/beta/gamma` - Unit cell angles
- `_geom_bond_atom_site_label_1/2` - Bonded atoms
- `_ccdc_geom_bond_type` - Bond type

**Example CIF Structure:**
```
data_MOF_structure
_cell_length_a    10.000
_cell_length_b    10.000
_cell_length_c    10.000
_cell_angle_alpha 90.000
_cell_angle_beta  90.000
_cell_angle_gamma 90.000

loop_
_atom_site_label
_atom_site_type_symbol
_atom_site_fract_x
_atom_site_fract_y
_atom_site_fract_z
_atom_type_partial_charge
C1  C  0.500  0.500  0.500  -0.123
Zn1 Zn 0.000  0.000  0.000   1.234

loop_
_geom_bond_atom_site_label_1
_geom_bond_atom_site_label_2
_ccdc_geom_bond_type
C1  Zn1  S
```

### Field Mapping (cif_fields.py)

CIF field names are mapped to database column names:

```python
cif_fields = {
    "_atom_site_label": "atom_label",
    "_atom_site_type_symbol": "element",
    "_atom_type_description": "description",
    "_atom_site_fract_x": "fract_x",
    "_atom_site_fract_y": "fract_y",
    "_atom_site_fract_z": "fract_z",
    "_cell_length_a": "length_a",
    "_cell_length_b": "length_b",
    "_cell_length_c": "length_c",
    "_cell_angle_alpha": "alpha",
    "_cell_angle_beta": "beta",
    "_cell_angle_gamma": "gamma",
    "_atom_type_partial_charge": "partial_charge",
    "_geom_bond_atom_site_label_1": "atom1_label",
    "_geom_bond_atom_site_label_2": "atom2_label",
    "_ccdc_geom_bond_type": "bond_type"
}
```

---

## Important Notes

### Duplicate Filenames in Tables

Due to CIF file structure, **duplicate filenames are expected** in `atom_sites_comprehensive` and `bonds_comprehensive`:

- Each CIF file contains **multiple atoms** → many rows per file in atom_sites table
- Each CIF file contains **multiple bonds** → many rows per file in bonds table
- Use `COUNT(DISTINCT file)` to count unique structures
- Use `COUNT(*)` to count total atoms or bonds

**Example:**
```sql
-- This returns total rows (e.g., 50 million atoms)
SELECT COUNT(*) FROM carbon_db.atom_sites_comprehensive;

-- This returns unique structures (e.g., 324,426 MOFs)
SELECT COUNT(DISTINCT file) FROM carbon_db.atom_sites_comprehensive;
```

### Primary Keys

Primary keys prevent duplicate entries:

- **atom_sites_comprehensive**: `PRIMARY KEY (file, atom_label)`
  - Ensures each atom label is unique within a file
- **bonds_comprehensive**: `PRIMARY KEY (file, atom1_label, atom2_label, bond_type)`
  - Prevents duplicate bond entries

### Coordinate Systems

- **Fractional coordinates**: Relative to unit cell axes (0 to 1)
- **Cartesian coordinates**: Absolute position in Angstroms
- Conversion uses unit cell parameters (lengths and angles)
- All Cartesian coordinates are pre-computed and stored

---

## Connection Instructions

### Python (DuckDB)

```python
import duckdb

# Connect to MotherDuck database
conn = duckdb.connect("md:carbon_db")

# Query example
result = conn.execute("""
    SELECT COUNT(DISTINCT file) AS total_structures
    FROM carbon_db.atom_sites_comprehensive
""").fetchall()

print(f"Total MOF structures: {result[0][0]}")

conn.close()
```

### Environment Setup

Set MotherDuck token as environment variable:

**Linux/Mac:**
```bash
export MOTHERDUCK_TOKEN="your_token_here"
```

**Windows:**
```cmd
set motherduck_token=your_token_here
```

---

## System Requirements

### For Data Loading (mof_to_sql.py)
- Python 3.8+
- Libraries: duckdb, pandas, pymatgen, joblib
- MotherDuck account and token
- Minimum 8GB RAM recommended (100GB+ for full dataset)

### For CSV Export (orchestrator pipeline)
- Python 3.8+
- Libraries: pathlib, argparse, csv, shlex, numpy
- Sufficient disk space for output CSVs

---

## Performance Considerations

### Memory Settings

The `mof_to_sql.py` script configures DuckDB memory limits:

```sql
SET max_memory = '100GB';
SET memory_limit = '156GB';
```

Adjust based on your system's available memory.

### Batch Processing

Both pipelines use batch processing:
- **mof_to_sql.py**: Parallel file parsing with joblib
- **orchestrator**: Processes files in batches to avoid command line length limits

### Indexing

Primary keys automatically create indexes on:
- `(file, atom_label)` in atom_sites tables
- `(file, atom1_label, atom2_label, bond_type)` in bonds tables

---

## Known Issues

### Catalog Errors

When running `create_bonds_comprehensive.sql`, you may encounter catalog errors about table prefixes. Workarounds:
- Use MotherDuck web IDE with `main.` prefix
- Use DuckDB CLI without prefix
- Ensure correct schema context before CREATE TABLE

---

## References

**Original Dataset:**
- Materials Cloud: https://www.materialscloud.org/discover/mofs/
- DOI: 10.24435/materialscloud:2018.0016/v3

**Related Publications:**
- See DOI link above for journal references

**Coordinate Transformation:**
- Based on crystallographic conventions for fractional-to-Cartesian conversion
- Implementation in `frac_cart.py` mirrors SQL macros in `conversion_macros.sql`

---

## Version History

- **v3** (October 2019) - Materials Cloud dataset version
- Current database implementation - 2024-2025

---

## Support

For questions about:
- **Database structure**: Refer to this README
- **Original dataset**: See Materials Cloud documentation
- **CIF format**: See International Union of Crystallography (IUCr) standards

---

**Last Updated**: February 2026
