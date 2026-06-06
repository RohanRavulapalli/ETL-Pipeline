#!/usr/bin/env python3
"""
VT ARC Carbon Dashboard - All-in-One
Collects your data and generates your dashboard in one command

Usage:
    python3 carbon_dashboard.py
"""

import subprocess
import json
import sys
from datetime import datetime, timedelta
from collections import defaultdict
import re

# GPU Power Consumption (Watts - TDP)
GPU_POWER = {
    'a100': 400,
    'a100-40': 300,
    'h200': 700,
    'l40s': 350,
    'a30': 165,
    'v100': 300,
    't4': 70,
    'p100': 250,
}

CPU_POWER_PER_CORE = 15
CARBON_INTENSITY_VA = 340
PUE = 1.2


def run_sacct(days=365):
    """Run sacct to get job data"""
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    
    cmd = [
        'sacct',
        '--format=JobID,User,Partition,AllocTRES,AllocCPUS,Elapsed,Start,End,State',
        f'--starttime={start_date}',
        '--parsable2',
        '--noheader',
        '--allocations',
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running sacct: {e}")
        return None


def parse_tres(tres_string):
    """Parse GPU info from TRES field"""
    gpu_type = None
    gpu_count = 0
    
    if not tres_string or tres_string == '':
        return gpu_type, gpu_count
    
    gpu_pattern = r'gres/gpu:(\w+)=(\d+)'
    match = re.search(gpu_pattern, tres_string)
    
    if match:
        gpu_type = match.group(1).lower()
        gpu_count = int(match.group(2))
    elif 'gres/gpu=' in tres_string:
        gpu_match = re.search(r'gres/gpu=(\d+)', tres_string)
        if gpu_match:
            gpu_count = int(gpu_match.group(1))
            gpu_type = 'unknown'
    
    return gpu_type, gpu_count


def parse_elapsed_time(elapsed_str):
    """Convert elapsed time to hours"""
    if not elapsed_str or elapsed_str == '':
        return 0.0
    
    parts = elapsed_str.split('-')
    if len(parts) == 2:
        days = int(parts[0])
        time_parts = parts[1].split(':')
    else:
        days = 0
        time_parts = elapsed_str.split(':')
    
    if len(time_parts) == 3:
        hours, minutes, seconds = map(int, time_parts)
    elif len(time_parts) == 2:
        hours = 0
        minutes, seconds = map(int, time_parts)
    else:
        return 0.0
    
    total_hours = days * 24 + hours + minutes / 60 + seconds / 3600
    return total_hours


def calculate_energy_and_carbon(gpu_type, gpu_count, cpu_count, hours):
    """Calculate energy and carbon"""
    total_power_watts = 0
    
    if gpu_type and gpu_count > 0:
        gpu_power = GPU_POWER.get(gpu_type, 300)
        total_power_watts += gpu_power * gpu_count
    
    if cpu_count > 0:
        total_power_watts += CPU_POWER_PER_CORE * cpu_count
    
    if total_power_watts == 0 or hours == 0:
        return 0.0, 0.0
    
    energy_kwh = (total_power_watts / 1000) * hours * PUE
    carbon_kg = (energy_kwh * CARBON_INTENSITY_VA) / 1000
    
    return energy_kwh, carbon_kg


def process_sacct_output(output):
    """Process sacct output"""
    if not output:
        return []
    
    jobs = []
    lines = output.strip().split('\n')
    
    for line in lines:
        if not line:
            continue
        
        fields = line.split('|')
        if len(fields) < 9:
            continue
        
        job_id, user, partition, tres, alloc_cpus, elapsed, start, end, state = fields
        
        if state not in ['COMPLETED', 'TIMEOUT', 'OUT_OF_MEMORY', 'FAILED']:
            continue
        
        gpu_type, gpu_count = parse_tres(tres)
        
        try:
            cpu_count = int(alloc_cpus) if alloc_cpus else 0
        except ValueError:
            cpu_count = 0
        
        if gpu_count == 0 and cpu_count == 0:
            continue
        
        hours = parse_elapsed_time(elapsed)
        energy_kwh, carbon_kg = calculate_energy_and_carbon(gpu_type, gpu_count, cpu_count, hours)
        
        if gpu_count > 0:
            job_type = 'GPU'
        else:
            job_type = 'CPU'
        
        job_data = {
            'job_id': job_id,
            'user': user,
            'job_type': job_type,
            'gpu_type': gpu_type or 'none',
            'gpu_count': gpu_count,
            'cpu_count': cpu_count,
            'duration_hours': round(hours, 2),
            'energy_kwh': round(energy_kwh, 2),
            'carbon_kg': round(carbon_kg, 3),
            'end_time': end,
        }
        
        jobs.append(job_data)
    
    return jobs


def generate_simple_html(jobs, username):
    """Generate a simple HTML dashboard"""
    
    if not jobs:
        total_carbon = 0
        total_energy = 0
        total_cpu_hours = 0
        total_gpu_hours = 0
        cpu_jobs = 0
        gpu_jobs = 0
    else:
        total_carbon = sum(j['carbon_kg'] for j in jobs)
        total_energy = sum(j['energy_kwh'] for j in jobs)
        total_cpu_hours = sum(j['duration_hours'] * j['cpu_count'] for j in jobs)
        total_gpu_hours = sum(j['duration_hours'] * j['gpu_count'] for j in jobs)
        cpu_jobs = len([j for j in jobs if j['job_type'] == 'CPU'])
        gpu_jobs = len([j for j in jobs if j['job_type'] == 'GPU'])
    
    # Generate job rows
    job_rows = ""
    for job in jobs[:20]:  # Show last 20 jobs
        job_rows += f"""
        <tr>
            <td>{job['job_id']}</td>
            <td>{job['job_type']}</td>
            <td>{job['cpu_count']} cores</td>
            <td>{job['duration_hours']:.1f} hrs</td>
            <td>{job['energy_kwh']:.2f} kWh</td>
            <td>{job['carbon_kg']:.3f} kg</td>
        </tr>
        """
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>My Carbon Dashboard</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: Arial, sans-serif; background: #f5f5f5; padding: 20px; }}
        .container {{ max-width: 1000px; margin: 0 auto; }}
        h1 {{ color: #2c3e50; margin-bottom: 30px; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .stat-card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .stat-value {{ font-size: 2em; font-weight: bold; color: #27ae60; }}
        .stat-label {{ color: #7f8c8d; margin-top: 5px; }}
        table {{ width: 100%; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        th {{ background: #34495e; color: white; padding: 15px; text-align: left; }}
        td {{ padding: 12px 15px; border-bottom: 1px solid #ecf0f1; }}
        tr:hover {{ background: #f8f9fa; }}
        .info {{ background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Carbon Dashboard - {username}</h1>
        
        <div class="info">
            <strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M')} | 
            <strong>Jobs tracked:</strong> {len(jobs)} ({cpu_jobs} CPU, {gpu_jobs} GPU)
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-value">{total_carbon:.1f}</div>
                <div class="stat-label">kg CO2</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{total_energy:.1f}</div>
                <div class="stat-label">kWh Energy</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{int(total_cpu_hours)}</div>
                <div class="stat-label">CPU Hours</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{int(total_gpu_hours)}</div>
                <div class="stat-label">GPU Hours</div>
            </div>
        </div>
        
        <h2 style="margin: 30px 0 15px 0; color: #2c3e50;">Recent Jobs</h2>
        <table>
            <thead>
                <tr>
                    <th>Job ID</th>
                    <th>Type</th>
                    <th>Resources</th>
                    <th>Duration</th>
                    <th>Energy</th>
                    <th>CO2</th>
                </tr>
            </thead>
            <tbody>
                {job_rows}
            </tbody>
        </table>
    </div>
</body>
</html>"""
    
    return html


def main():
    print("VT ARC Carbon Dashboard")
    print("=" * 50)
    print()
    
    # Get username
    import os
    username = os.environ.get('USER', 'user')
    
    print(f"Collecting data for {username}...")
    
    # Collect data
    output = run_sacct(days=365)
    
    if not output:
        print("No data retrieved from sacct")
        sys.exit(1)
    
    # Process jobs
    jobs = process_sacct_output(output)
    
    if not jobs:
        print("No completed jobs found")
        sys.exit(1)
    
    cpu_jobs = len([j for j in jobs if j['job_type'] == 'CPU'])
    gpu_jobs = len([j for j in jobs if j['job_type'] == 'GPU'])
    total_carbon = sum(j['carbon_kg'] for j in jobs)
    
    print(f"Found {len(jobs)} jobs ({cpu_jobs} CPU, {gpu_jobs} GPU)")
    print(f"Total carbon: {total_carbon:.2f} kg CO2")
    print()
    
    # Save JSON for team merge
    json_filename = f"{username}_carbon.json"
    json_data = {
        'user': username,
        'jobs': jobs,
        'generated': datetime.now().isoformat()
    }
    
    with open(json_filename, 'w') as f:
        json.dump(json_data, f, indent=2)
    
    print(f"[SUCCESS] Saved data: {json_filename}")
    
    # Generate HTML
    html_filename = f"{username}_dashboard.html"
    html = generate_simple_html(jobs, username)
    
    with open(html_filename, 'w') as f:
        f.write(html)
    
    print(f"[SUCCESS] Generated dashboard: {html_filename}")
    print()
    print("Next steps:")
    print(f"  1. Download {html_filename} to view your dashboard")
    print(f"  2. Send {json_filename} to Rohan for team dashboard")
    print()
    print("Download command (run on your computer):")
    print(f"  scp {username}@owl1.arc.vt.edu:CarbonQapture/carbon_dashboard/{html_filename} .")


if __name__ == '__main__':
    main()
