# Carbon Dashboard



Real-time tracking and visualization of computational research carbon emissions on HPC clusters.



## Overview



This dashboard aggregates GPU/CPU usage metrics from Slurm workloads on Virginia Tech's ARC computing clusters and calculates associated carbon emissions based on the local power grid's carbon intensity.



## What It Does



Tracks carbon footprint of computational research by:



- Querying Slurm job accounting data (sacct) from HPC compute nodes

- Calculating energy consumption (GPU hours, CPU hours)

- Converting to CO2 emissions using regional grid carbon intensity

- Generating individual and team carbon reports

- Producing HTML dashboards and JSON data exports for analysis



## Technologies



Python, Slurm, HTML/CSS visualization, JSON data export



## Key Features



- Automated Slurm job parsing and metrics extraction

- Carbon intensity calculations (configurable by region)

- Individual researcher dashboards

- Team-level aggregation and reporting

- HTML export for easy sharing

- JSON export for downstream analysis



## How It Works



### 1. carbon_dashboard.py



Main script that:

- Connects to Slurm on HPC cluster (ARC at VT)

- Queries job accounting data via `sacct` command

- Extracts GPU/CPU hours, job duration, compute nodes

- Calculates energy usage and CO2 emissions

- Generates HTML dashboard and JSON data export



Usage:

```bash

ssh yourpid@tinkercliffs1.arc.vt.edu

cd CarbonQapture/carbon_dashboard

python3 carbon_dashboard.py

```



Output:

- `yourpid_dashboard.html` - Interactive HTML dashboard

- `yourpid_carbon.json` - JSON data export



### 2. generate_team_report.py



Aggregates individual carbon data into team-level reports:

- Combines multiple researcher JSON files

- Calculates team totals and averages

- Identifies high-usage contributors

- Generates summary statistics



### 3. merge_team_data.py



Utility for merging and processing multiple carbon datasets:

- Combines weekly/monthly data

- Data cleaning and validation

- Prepares data for reporting



## Example Output



HTML Dashboard shows:

- Total carbon emitted (in kg CO2)

- Breakdown by job type (GPU vs CPU)

- Timeline of emissions over time

- Energy consumption metrics

- Power grid carbon intensity used



## Data Source



Carbon intensity values based on:

- Virginia power grid: ~340g CO2 per kWh (regional mix)

- Customizable for other regions/grids



## System Requirements



- SSH access to HPC cluster

- Slurm command-line tools (sacct)

- Python 3.7+

- Standard library dependencies



## Usage Workflow



1. SSH to HPC cluster

2. Run carbon_dashboard.py

3. Download dashboard: `scp yourpid@owl1.arc.vt.edu:CarbonQapture/carbon_dashboard/yourpid_dashboard.html .`

4. Open HTML file in browser to view dashboard

5. Share JSON file with team for aggregation



## Why This Matters



Computational research has significant energy costs and carbon footprint. This dashboard provides visibility into:

- Which research projects consume most energy

- Opportunities for optimization

- Environmental impact of computational work

- Accountability and awareness in HPC usage



## Example Metrics



From CarbonQapture deployment:

- 36 GPU jobs analyzed

- 269 kWh total energy consumption

- 91.5 kg CO2 emitted

- Average: 7.5 kWh per job



## Contact



For questions or contributions:

Rohan Ravulapalli

rravulapalli6@gmail.com

