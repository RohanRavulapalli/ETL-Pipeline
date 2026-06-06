#!/usr/bin/env python3
"""
Merge multiple carbon data JSON files from different team members
into a single combined dataset

Usage:
    python3 merge_team_data.py --inputs alice_carbon.json bob_carbon.json --output team.json
"""

import json
import argparse
from datetime import datetime
from collections import defaultdict


def merge_carbon_data(input_files):
    """
    Merge multiple JSON files from different users into one combined dataset
    """
    all_jobs = []
    
    for input_file in input_files:
        try:
            with open(input_file, 'r') as f:
                data = json.load(f)
                
                # carbon_dashboard.py outputs: {'user': 'username', 'jobs': [...], 'generated': '...'}
                if 'jobs' in data:
                    all_jobs.extend(data['jobs'])
                
        except FileNotFoundError:
            print(f"Warning: File not found: {input_file}")
            continue
        except json.JSONDecodeError:
            print(f"Warning: Invalid JSON in file: {input_file}")
            continue
    
    if not all_jobs:
        print("Error: No valid job data found in any input files")
        return None
    
    # Remove duplicates based on job_id and user
    seen_jobs = set()
    unique_jobs = []
    
    for job in all_jobs:
        job_key = (job.get('job_id'), job.get('user'))
        if job_key not in seen_jobs:
            seen_jobs.add(job_key)
            unique_jobs.append(job)
    
    print(f"Loaded {len(all_jobs)} jobs, {len(unique_jobs)} unique jobs from {len(input_files)} files")
    
    # Aggregate by user
    user_stats = defaultdict(lambda: {
        'total_jobs': 0,
        'cpu_jobs': 0,
        'gpu_jobs': 0,
        'total_cpu_hours': 0,
        'total_gpu_hours': 0,
        'total_energy_kwh': 0,
        'total_carbon_kg': 0,
        'gpu_breakdown': defaultdict(float)
    })
    
    for job in unique_jobs:
        user = job['user']
        user_stats[user]['total_jobs'] += 1
        user_stats[user]['total_cpu_hours'] += job['duration_hours'] * job['cpu_count']
        user_stats[user]['total_gpu_hours'] += job['duration_hours'] * job.get('gpu_count', 0)
        user_stats[user]['total_energy_kwh'] += job['energy_kwh']
        user_stats[user]['total_carbon_kg'] += job['carbon_kg']
        
        if job.get('gpu_count', 0) > 0:
            user_stats[user]['gpu_jobs'] += 1
            gpu_type = job.get('gpu_type', 'unknown')
            user_stats[user]['gpu_breakdown'][gpu_type] += job['duration_hours'] * job['gpu_count']
        else:
            user_stats[user]['cpu_jobs'] += 1
    
    # Convert to regular dict
    by_user = {}
    for user, stats in user_stats.items():
        by_user[user] = {
            'total_jobs': stats['total_jobs'],
            'cpu_jobs': stats['cpu_jobs'],
            'gpu_jobs': stats['gpu_jobs'],
            'total_cpu_hours': round(stats['total_cpu_hours'], 2),
            'total_gpu_hours': round(stats['total_gpu_hours'], 2),
            'total_energy_kwh': round(stats['total_energy_kwh'], 2),
            'total_carbon_kg': round(stats['total_carbon_kg'], 3),
            'gpu_breakdown': dict(stats['gpu_breakdown'])
        }
    
    # Calculate totals
    total_carbon = sum(j['carbon_kg'] for j in unique_jobs)
    total_energy = sum(j['energy_kwh'] for j in unique_jobs)
    total_cpu_hours = sum(j['duration_hours'] * j['cpu_count'] for j in unique_jobs)
    total_gpu_hours = sum(j['duration_hours'] * j.get('gpu_count', 0) for j in unique_jobs)
    cpu_jobs = len([j for j in unique_jobs if j.get('job_type') == 'CPU'])
    gpu_jobs = len([j for j in unique_jobs if j.get('job_type') == 'GPU'])
    
    # Find earliest date from jobs
    earliest_date = None
    for job in unique_jobs:
        job_date = job.get('end_time', '')
        if job_date:
            if earliest_date is None or job_date < earliest_date:
                earliest_date = job_date
    
    # Create merged dataset
    merged_data = {
        'metadata': {
            'collection_date': datetime.now().isoformat(),
            'start_date': earliest_date.split()[0] if earliest_date else 'unknown',
            'account': 'merged_team_data',
            'total_jobs': len(unique_jobs),
            'cpu_jobs': cpu_jobs,
            'gpu_jobs': gpu_jobs,
            'carbon_intensity_g_per_kwh': 340,
            'pue': 1.2,
            'cpu_power_per_core_watts': 15,
            'sources': f"{len(input_files)} team member files merged",
            'unique_users': len(by_user)
        },
        'summary': {
            'total_carbon_kg': round(total_carbon, 3),
            'total_energy_kwh': round(total_energy, 2),
            'total_cpu_hours': round(total_cpu_hours, 2),
            'total_gpu_hours': round(total_gpu_hours, 2),
            'unique_users': len(by_user)
        },
        'by_user': by_user,
        'jobs': sorted(unique_jobs, key=lambda x: x.get('end_time', ''), reverse=True)
    }
    
    return merged_data


def main():
    parser = argparse.ArgumentParser(
        description='Merge multiple team member carbon data JSON files'
    )
    parser.add_argument(
        '--inputs',
        nargs='+',
        required=True,
        help='Input JSON files from team members (space-separated)'
    )
    parser.add_argument(
        '--output',
        default='team_combined.json',
        help='Output merged JSON file (default: team_combined.json)'
    )
    
    args = parser.parse_args()
    
    print(f"Merging {len(args.inputs)} input files...")
    
    # Merge data
    merged_data = merge_carbon_data(args.inputs)
    
    if merged_data is None:
        print("Error: Failed to merge data")
        return
    
    # Write output
    with open(args.output, 'w') as f:
        json.dump(merged_data, f, indent=2)
    
    print(f"\n[SUCCESS] Team data merged successfully!")
    print(f"\nSummary:")
    print(f"  Total Team Members: {merged_data['summary']['unique_users']}")
    print(f"  Total Jobs: {merged_data['metadata']['total_jobs']} ({merged_data['metadata']['cpu_jobs']} CPU, {merged_data['metadata']['gpu_jobs']} GPU)")
    print(f"  Total CPU Hours: {merged_data['summary']['total_cpu_hours']:,.2f}")
    print(f"  Total GPU Hours: {merged_data['summary']['total_gpu_hours']:,.2f}")
    print(f"  Total Energy: {merged_data['summary']['total_energy_kwh']:,.2f} kWh")
    print(f"  Total Carbon: {merged_data['summary']['total_carbon_kg']:,.3f} kg CO2")
    print(f"\nMerged data saved to: {args.output}")
    print(f"\nNext step:")
    print(f"  python3 generate_team_report.py --input {args.output} --output team_report.html")


if __name__ == '__main__':
    main()
