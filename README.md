# ETL Pipeline: Metal-Organic Framework Database

Large-scale ETL pipeline for processing and analyzing 324,426+ crystallographic structures for CO2 capture research using Metal-Organic Frameworks (MOFs).

## Overview

This project demonstrates full-stack data engineering:

- 324K+ files processed in parallel using Python
- Normalized DuckDB database with 5 interconnected tables
- SQL macros for crystallographic coordinate transformations
- Carbon emissions dashboard for research team tracking
- Scalable architecture handling 50M+ atomic records

## Project Structure

```
├── mof_database/          Database schema, ETL scripts, SQL macros
└── carbon_dashboard/      Emissions tracking and reporting utilities
```

## Key Technologies

**Data Processing:** Python, pandas, joblib, pymatgen
**Database:** DuckDB, MotherDuck (cloud-hosted)
**Queries:** SQL with custom transformation macros
**Parallel Processing:** joblib for distributed file parsing

## What This Does

### MOF Database (mof_database/)

Processes crystallographic CIF files and loads into a cloud-hosted DuckDB database:

- Input: 324,426 CIF files (324K+ atoms, bonds, properties)
- Output: 5 normalized tables with 66 columns of screening data
- Pipeline: Parse → Transform → Load (ETL)
- Performance: Parallel processing with configurable batch sizes and memory limits

**Tables:**

- atom_sites_comprehensive - Atomic positions in fractional and Cartesian coordinates
- bonds_comprehensive - Bond connectivity between atoms
- top_mof_atom_sites - Top-performing MOFs with refined charges
- top_mof_bonds - Bond data for top MOFs
- top_mof_screening_data - CO2 adsorption properties (66 columns)

**SQL Features:**

- Macros for fractional-to-Cartesian coordinate conversion
- Primary keys for data integrity
- Optimized queries for large-scale analysis

### Carbon Dashboard (carbon_dashboard/)

Real-time tracking of computational research carbon emissions:

- Aggregates GPU/CPU usage from Slurm workloads on HPC clusters
- Generates individual and team carbon reports
- Calculates emissions based on local power grid carbon intensity
- Produces HTML dashboards and JSON data exports

## Sample Queries

```sql
-- Count unique MOF structures
SELECT COUNT(DISTINCT file) FROM carbon_db.atom_sites_comprehensive;

-- Get atoms for a specific MOF
SELECT * FROM carbon_db.atom_sites_comprehensive 
WHERE file = 'str_m3_o10_o12_pcu_sym.54.cif';

-- Find high-performing MOFs by CO2 uptake
SELECT file, CO2_uptake_P0.15bar_T298K 
FROM carbon_db.top_mof_screening_data 
ORDER BY CO2_uptake_P0.15bar_T298K DESC 
LIMIT 10;
```

## How It Works

### ETL Pipeline

1. Extract: Parse CIF files using pymatgen
2. Transform: Extract atomic/bond data, compute Cartesian coordinates
3. Load: Batch insert into DuckDB with parallel processing

```bash
python mof_database/database_scripts/mof_to_duckdb/mof_to_sql.py <path_to_cif_files>
```

### Dashboard

```bash
python carbon_dashboard/carbon_dashboard.py
# Outputs: yourname_dashboard.html, yourname_carbon.json
```

## Data Source

All crystallographic data originates from the Materials Cloud MOF database:

- Source: https://www.materialscloud.org/discover/mofs/
- DOI: 10.24435/materialscloud:2018.0016/v3
- Structures: 324,426 hypothetical MOFs
- Refined subset: 8,000+ with REPEAT charge calculations

## Technical Highlights

✓ Scalability: Handles 50M+ atomic records
✓ Performance: Parallel file processing with joblib
✓ Database Design: Normalized schema with primary keys
✓ Automation: Batch processing with configurable memory limits
✓ Coordinate Math: SQL macros for crystallographic transformations
✓ Cloud Integration: MotherDuck for distributed database access

## System Requirements

- Python 3.8+
- DuckDB + MotherDuck (cloud database)
- Libraries: pandas, pymatgen, joblib, duckdb
- For full dataset: 100GB+ storage, 8GB+ RAM

## Usage

See detailed documentation in:

- mof_database/README.md - Database schema and queries
- carbon_dashboard/README.md - Dashboard setup

## Contact

Rohan Ravulapalli
rravulapalli6@gmail.com
