#!/usr/bin/env python3
"""
Generate a comprehensive team carbon emissions report
Includes analytics, trends, comparisons, and recommendations

Usage:
    python3 generate_team_report.py --input team_data.json --output team_report.html
"""

import json
import argparse
from datetime import datetime, timedelta
from collections import defaultdict

def analyze_data(data):
    """
    Perform comprehensive analysis on the team data
    """
    jobs = data.get('jobs', [])
    by_user = data.get('by_user', {})
    
    analysis = {
        'top_emitters': [],
        'efficiency_leaders': [],
        'resource_usage': {},
        'time_trends': {},
        'job_patterns': {},
        'recommendations': []
    }
    
    # Top emitters
    user_emissions = [(user, stats['total_carbon_kg']) for user, stats in by_user.items()]
    analysis['top_emitters'] = sorted(user_emissions, key=lambda x: x[1], reverse=True)[:10]
    
    # Efficiency (carbon per compute hour)
    efficiency = []
    for user, stats in by_user.items():
        total_hours = stats['total_cpu_hours'] + stats['total_gpu_hours']
        if total_hours > 0:
            efficiency_score = stats['total_carbon_kg'] / total_hours
            efficiency.append((user, efficiency_score, total_hours))
    analysis['efficiency_leaders'] = sorted(efficiency, key=lambda x: x[1])[:10]
    
    # Resource usage breakdown
    cpu_jobs = sum(1 for j in jobs if j.get('job_type') == 'CPU')
    gpu_jobs = sum(1 for j in jobs if j.get('job_type') == 'GPU')
    
    analysis['resource_usage'] = {
        'cpu_jobs': cpu_jobs,
        'gpu_jobs': gpu_jobs,
        'cpu_percentage': (cpu_jobs / len(jobs) * 100) if jobs else 0,
        'gpu_percentage': (gpu_jobs / len(jobs) * 100) if jobs else 0
    }
    
    # Time trends (daily)
    daily_emissions = defaultdict(float)
    daily_jobs = defaultdict(int)
    for job in jobs:
        date = job.get('end_time', '').split('T')[0]
        if date:
            daily_emissions[date] += job['carbon_kg']
            daily_jobs[date] += 1
    
    analysis['time_trends'] = {
        'daily_emissions': dict(daily_emissions),
        'daily_jobs': dict(daily_jobs)
    }
    
    # Job patterns
    job_durations = [j['duration_hours'] for j in jobs]
    if job_durations:
        analysis['job_patterns'] = {
            'avg_duration': sum(job_durations) / len(job_durations),
            'min_duration': min(job_durations),
            'max_duration': max(job_durations),
            'short_jobs': sum(1 for d in job_durations if d < 1),
            'medium_jobs': sum(1 for d in job_durations if 1 <= d < 8),
            'long_jobs': sum(1 for d in job_durations if d >= 8)
        }
    
    # Generate recommendations
    recommendations = []
    
    # Check for inefficient resource usage
    if analysis['resource_usage']['cpu_percentage'] < 20 and gpu_jobs > 0:
        recommendations.append({
            'type': 'warning',
            'title': 'Heavy GPU Usage',
            'message': f"Team is using GPUs for {analysis['resource_usage']['gpu_percentage']:.0f}% of jobs. Consider if all GPU jobs truly need GPU resources.",
            'impact': 'high'
        })
    
    # Check for very short jobs
    if analysis['job_patterns'].get('short_jobs', 0) > len(jobs) * 0.3:
        recommendations.append({
            'type': 'info',
            'title': 'Many Short Jobs',
            'message': f"{analysis['job_patterns']['short_jobs']} jobs under 1 hour. Consider batching small jobs to reduce overhead.",
            'impact': 'medium'
        })
    
    # Check for efficiency outliers
    if len(efficiency) > 2:
        avg_efficiency = sum(e[1] for e in efficiency) / len(efficiency)
        inefficient = [e for e in efficiency if e[1] > avg_efficiency * 2]
        if inefficient:
            recommendations.append({
                'type': 'warning',
                'title': 'Efficiency Gap',
                'message': f"Some users have 2x higher carbon per compute hour than team average. Review job configurations.",
                'impact': 'high'
            })
    
    # Check total team impact
    total_carbon = data['summary']['total_carbon_kg']
    if total_carbon > 100:
        trees = total_carbon / 21  # Average tree absorbs ~21kg CO2/year
        recommendations.append({
            'type': 'success',
            'title': 'Environmental Context',
            'message': f"Team's {total_carbon:.1f} kg CO₂ would require {trees:.1f} trees one year to offset.",
            'impact': 'info'
        })
    
    analysis['recommendations'] = recommendations
    
    return analysis


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Team Carbon Report - VT ARC</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600;700&family=Work+Sans:wght@400;600;700;800&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        :root {
            --forest: #0d3b2e;
            --moss: #1a5c47;
            --sage: #4a7c59;
            --mint: #7fb069;
            --cream: #f4f1de;
            --carbon: #2a2a2a;
            --ash: #5a5a5a;
            --smoke: #e8e8e8;
            --alert: #d62828;
            --warning: #f77f00;
            --info: #0077b6;
            --success: #2a9d8f;
        }
        
        body {
            font-family: 'IBM Plex Mono', monospace;
            background: var(--cream);
            color: var(--carbon);
            line-height: 1.6;
        }
        
        .cover-page {
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            background: linear-gradient(135deg, var(--forest) 0%, var(--moss) 100%);
            color: var(--cream);
            text-align: center;
            padding: 3rem;
            position: relative;
            overflow: hidden;
        }
        
        .cover-page::before {
            content: 'CO₂';
            position: absolute;
            font-size: 400px;
            font-family: 'Work Sans', sans-serif;
            font-weight: 800;
            opacity: 0.05;
            z-index: 0;
        }
        
        .cover-content {
            position: relative;
            z-index: 1;
        }
        
        .cover-title {
            font-family: 'Work Sans', sans-serif;
            font-size: 4rem;
            font-weight: 800;
            margin-bottom: 1rem;
            letter-spacing: -0.03em;
        }
        
        .cover-subtitle {
            font-size: 1.5rem;
            opacity: 0.9;
            margin-bottom: 3rem;
        }
        
        .cover-stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 2rem;
            margin-top: 3rem;
            max-width: 800px;
        }
        
        .cover-stat {
            text-align: center;
        }
        
        .cover-stat-value {
            font-family: 'Work Sans', sans-serif;
            font-size: 3rem;
            font-weight: 700;
            display: block;
        }
        
        .cover-stat-label {
            font-size: 0.9rem;
            opacity: 0.8;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .report-content {
            max-width: 1400px;
            margin: 0 auto;
            padding: 3rem;
        }
        
        .section {
            background: white;
            padding: 2.5rem;
            border-radius: 16px;
            margin-bottom: 2rem;
            box-shadow: 0 2px 12px rgba(0,0,0,0.06);
        }
        
        .section-title {
            font-family: 'Work Sans', sans-serif;
            font-size: 2rem;
            font-weight: 700;
            color: var(--forest);
            margin-bottom: 1.5rem;
            padding-bottom: 1rem;
            border-bottom: 3px solid var(--mint);
        }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }
        
        .metric-card {
            background: var(--smoke);
            padding: 1.5rem;
            border-radius: 12px;
            border-left: 4px solid var(--mint);
        }
        
        .metric-label {
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            color: var(--ash);
            margin-bottom: 0.5rem;
            font-weight: 600;
        }
        
        .metric-value {
            font-family: 'Work Sans', sans-serif;
            font-size: 2.5rem;
            font-weight: 700;
            color: var(--forest);
        }
        
        .metric-unit {
            font-size: 1rem;
            color: var(--ash);
        }
        
        .leaderboard {
            margin: 2rem 0;
        }
        
        .leaderboard-item {
            display: grid;
            grid-template-columns: 60px 1fr auto;
            align-items: center;
            padding: 1rem;
            margin-bottom: 0.5rem;
            background: var(--smoke);
            border-radius: 8px;
            transition: all 0.3s ease;
        }
        
        .leaderboard-item:hover {
            background: white;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }
        
        .rank {
            font-family: 'Work Sans', sans-serif;
            font-size: 2rem;
            font-weight: 700;
            color: var(--ash);
        }
        
        .rank-1 { color: #FFD700; }
        .rank-2 { color: #C0C0C0; }
        .rank-3 { color: #CD7F32; }
        
        .user-name {
            font-weight: 600;
            color: var(--forest);
        }
        
        .user-stat {
            font-family: 'Work Sans', sans-serif;
            font-size: 1.2rem;
            font-weight: 700;
            color: var(--moss);
        }
        
        .recommendations {
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }
        
        .recommendation {
            padding: 1.5rem;
            border-radius: 12px;
            border-left: 4px solid;
        }
        
        .recommendation.warning {
            background: #fff3cd;
            border-color: var(--warning);
        }
        
        .recommendation.info {
            background: #d1ecf1;
            border-color: var(--info);
        }
        
        .recommendation.success {
            background: #d4edda;
            border-color: var(--success);
        }
        
        .recommendation-title {
            font-weight: 700;
            margin-bottom: 0.5rem;
            font-size: 1.1rem;
        }
        
        .chart-container {
            margin: 2rem 0;
            background: white;
            padding: 1.5rem;
            border-radius: 12px;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 1rem 0;
        }
        
        th {
            background: var(--forest);
            color: var(--cream);
            padding: 1rem;
            text-align: left;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.85rem;
            letter-spacing: 0.5px;
        }
        
        td {
            padding: 1rem;
            border-bottom: 1px solid var(--smoke);
        }
        
        tr:hover {
            background: var(--smoke);
        }
        
        .badge {
            display: inline-block;
            padding: 0.3rem 0.8rem;
            border-radius: 6px;
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
        }
        
        .badge-cpu {
            background: var(--sage);
            color: white;
        }
        
        .badge-gpu {
            background: var(--moss);
            color: white;
        }
        
        .page-break {
            page-break-after: always;
        }
        
        @media print {
            .cover-page {
                page-break-after: always;
            }
            .section {
                page-break-inside: avoid;
            }
        }
        
        footer {
            text-align: center;
            padding: 3rem 2rem;
            color: var(--ash);
            font-size: 0.9rem;
        }
    </style>
</head>
<body>
    <div class="cover-page">
        <div class="cover-content">
            <h1 class="cover-title">Team Carbon Report</h1>
            <p class="cover-subtitle">Virginia Tech Advanced Research Computing</p>
            <div class="cover-stats">
                <div class="cover-stat">
                    <span class="cover-stat-value">__TOTAL_CARBON__</span>
                    <span class="cover-stat-label">kg CO₂</span>
                </div>
                <div class="cover-stat">
                    <span class="cover-stat-value">__TOTAL_ENERGY__</span>
                    <span class="cover-stat-label">kWh Energy</span>
                </div>
                <div class="cover-stat">
                    <span class="cover-stat-value">__TOTAL_USERS__</span>
                    <span class="cover-stat-label">Team Members</span>
                </div>
                <div class="cover-stat">
                    <span class="cover-stat-value">__TOTAL_JOBS__</span>
                    <span class="cover-stat-label">Jobs Tracked</span>
                </div>
            </div>
            <p style="margin-top: 3rem; opacity: 0.7;">Report Generated: __REPORT_DATE__</p>
        </div>
    </div>
    
    <div class="report-content">
        <div class="section">
            <h2 class="section-title">Executive Summary</h2>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-label">Total Emissions</div>
                    <div class="metric-value">__TOTAL_CARBON__ <span class="metric-unit">kg CO₂</span></div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Energy Consumed</div>
                    <div class="metric-value">__TOTAL_ENERGY__ <span class="metric-unit">kWh</span></div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Compute Hours</div>
                    <div class="metric-value">__TOTAL_HOURS__ <span class="metric-unit">hrs</span></div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Team Members</div>
                    <div class="metric-value">__TOTAL_USERS__</div>
                </div>
            </div>
            <p style="margin-top: 1rem; color: var(--ash);">
                <strong>Reporting Period:</strong> __START_DATE__ to __END_DATE__<br>
                <strong>Jobs Analyzed:</strong> __CPU_JOBS__ CPU jobs, __GPU_JOBS__ GPU jobs
            </p>
        </div>
        
        <div class="section">
            <h2 class="section-title">__EMITTERS_TITLE__</h2>
            <div class="leaderboard">
                __TOP_EMITTERS__
            </div>
        </div>
        
        <div class="section">
            <h2 class="section-title">__EFFICIENCY_TITLE__</h2>
            __EFFICIENCY_DESCRIPTION__
            <div class="leaderboard">
                __EFFICIENCY_LEADERS__
            </div>
        </div>
        
        <div class="section">
            <h2 class="section-title">Trends & Patterns</h2>
            <div class="chart-container">
                <h3 style="margin-bottom: 1rem;">Daily Carbon Emissions</h3>
                <canvas id="dailyChart"></canvas>
            </div>
            <div class="metrics-grid" style="margin-top: 2rem;">
                <div class="metric-card">
                    <div class="metric-label">Average Job Duration</div>
                    <div class="metric-value">__AVG_DURATION__ <span class="metric-unit">hrs</span></div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Short Jobs (&lt;1hr)</div>
                    <div class="metric-value">__SHORT_JOBS__</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Medium Jobs (1-8hrs)</div>
                    <div class="metric-value">__MEDIUM_JOBS__</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Long Jobs (8+hrs)</div>
                    <div class="metric-value">__LONG_JOBS__</div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2 class="section-title">Resource Usage Breakdown</h2>
            <div class="chart-container">
                <canvas id="resourceChart"></canvas>
            </div>
            <p style="margin-top: 1rem; color: var(--ash); text-align: center;">
                <strong>CPU Jobs:</strong> __CPU_PERCENTAGE__% (__CPU_JOBS__ jobs) • 
                <strong>GPU Jobs:</strong> __GPU_PERCENTAGE__% (__GPU_JOBS__ jobs)
            </p>
        </div>
        
        <div class="section">
            <h2 class="section-title">Recommendations</h2>
            <div class="recommendations">
                __RECOMMENDATIONS__
            </div>
        </div>
        
        <div class="section">
            <h2 class="section-title">Detailed User Breakdown</h2>
            <table>
                <thead>
                    <tr>
                        <th>User</th>
                        <th>Jobs</th>
                        <th>CPU Hours</th>
                        <th>GPU Hours</th>
                        <th>Energy (kWh)</th>
                        <th>CO₂ (kg)</th>
                        <th>Efficiency</th>
                    </tr>
                </thead>
                <tbody>
                    __USER_TABLE__
                </tbody>
            </table>
        </div>
    </div>
    
    <footer>
        <strong>VT ARC Carbon Emissions Report</strong><br>
        Generated __REPORT_DATE__<br>
        Data Period: __START_DATE__ to __END_DATE__
    </footer>
    
    <script>
        const dailyData = __DAILY_DATA__;
        const resourceData = __RESOURCE_DATA__;
        
        // Daily emissions chart
        const dailyCtx = document.getElementById('dailyChart').getContext('2d');
        new Chart(dailyCtx, {
            type: 'bar',
            data: {
                labels: dailyData.labels,
                datasets: [{
                    label: 'CO₂ Emissions (kg)',
                    data: dailyData.values,
                    backgroundColor: '#4a7c59',
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });
        
        // Resource usage chart
        const resourceCtx = document.getElementById('resourceChart').getContext('2d');
        new Chart(resourceCtx, {
            type: 'doughnut',
            data: {
                labels: resourceData.labels,
                datasets: [{
                    data: resourceData.values,
                    backgroundColor: ['#0d3b2e', '#1a5c47', '#4a7c59', '#7fb069', '#f77f00'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { position: 'bottom' }
                }
            }
        });
    </script>
</body>
</html>"""


def generate_report(input_file, output_file):
    """
    Generate comprehensive team report
    """
    # Load data
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    # Analyze data
    analysis = analyze_data(data)
    
    # Generate HTML components
    num_users = len(analysis['top_emitters'])
    show_rankings = num_users > 1
    
    top_emitters_html = ""
    for i, (user, carbon) in enumerate(analysis['top_emitters'][:10], 1):
        rank_class = f"rank-{i}" if i <= 3 else ""
        if show_rankings:
            top_emitters_html += f"""
            <div class="leaderboard-item">
                <div class="rank {rank_class}">#{i}</div>
                <div class="user-name">{user}</div>
                <div class="user-stat">{carbon:.2f} kg CO₂</div>
            </div>
            """
        else:
            top_emitters_html += f"""
            <div class="leaderboard-item">
                <div class="user-name">{user}</div>
                <div class="user-stat">{carbon:.2f} kg CO₂</div>
            </div>
            """
    
    efficiency_html = ""
    for i, (user, efficiency, hours) in enumerate(analysis['efficiency_leaders'][:10], 1):
        rank_class = f"rank-{i}" if i <= 3 else ""
        if show_rankings:
            efficiency_html += f"""
            <div class="leaderboard-item">
                <div class="rank {rank_class}">#{i}</div>
                <div class="user-name">{user}</div>
                <div class="user-stat">{efficiency:.3f} kg/hr</div>
            </div>
            """
        else:
            efficiency_html += f"""
            <div class="leaderboard-item">
                <div class="user-name">{user}</div>
                <div class="user-stat">{efficiency:.3f} kg/hr</div>
            </div>
            """
    
    recommendations_html = ""
    for rec in analysis['recommendations']:
        recommendations_html += f"""
        <div class="recommendation {rec['type']}">
            <div class="recommendation-title">{rec['title']}</div>
            <div>{rec['message']}</div>
        </div>
        """
    
    if not recommendations_html:
        recommendations_html = """
        <div class="recommendation success">
            <div class="recommendation-title">[SUCCESS] Great Job!</div>
            <div>Team is using resources efficiently. Keep up the good work!</div>
        </div>
        """
    
    # User table
    user_table_html = ""
    for user, stats in sorted(data['by_user'].items(), key=lambda x: x[1]['total_carbon_kg'], reverse=True):
        total_hours = stats['total_cpu_hours'] + stats['total_gpu_hours']
        efficiency = stats['total_carbon_kg'] / total_hours if total_hours > 0 else 0
        user_table_html += f"""
        <tr>
            <td><strong>{user}</strong></td>
            <td>{stats['total_jobs']}</td>
            <td>{stats['total_cpu_hours']:.1f}</td>
            <td>{stats['total_gpu_hours']:.1f}</td>
            <td>{stats['total_energy_kwh']:.2f}</td>
            <td>{stats['total_carbon_kg']:.3f}</td>
            <td>{efficiency:.4f} kg/hr</td>
        </tr>
        """
    
    # Chart data
    daily_labels = sorted(analysis['time_trends']['daily_emissions'].keys())
    daily_values = [analysis['time_trends']['daily_emissions'][d] for d in daily_labels]
    daily_data_json = json.dumps({
        'labels': daily_labels,
        'values': daily_values
    })
    
    # Resource breakdown
    resource_labels = []
    resource_values = []
    for user, stats in data['by_user'].items():
        if stats.get('gpu_breakdown'):
            for gpu, hours in stats['gpu_breakdown'].items():
                if gpu in resource_labels:
                    idx = resource_labels.index(gpu)
                    resource_values[idx] += hours
                else:
                    resource_labels.append(gpu.upper())
                    resource_values.append(hours)
    
    # Add CPU if significant
    total_cpu = sum(stats['total_cpu_hours'] for stats in data['by_user'].values())
    if total_cpu > 0:
        resource_labels.append('CPU')
        resource_values.append(total_cpu)
    
    resource_data_json = json.dumps({
        'labels': resource_labels,
        'values': resource_values
    })
    
    # Replacements
    replacements = {
        '__TOTAL_CARBON__': f"{data['summary']['total_carbon_kg']:.1f}",
        '__TOTAL_ENERGY__': f"{data['summary']['total_energy_kwh']:.1f}",
        '__TOTAL_USERS__': str(data['summary']['unique_users']),
        '__TOTAL_JOBS__': str(data['metadata']['total_jobs']),
        '__TOTAL_HOURS__': f"{data['summary']['total_cpu_hours'] + data['summary']['total_gpu_hours']:.0f}",
        '__CPU_JOBS__': str(data['metadata']['cpu_jobs']),
        '__GPU_JOBS__': str(data['metadata']['gpu_jobs']),
        '__CPU_PERCENTAGE__': f"{analysis['resource_usage']['cpu_percentage']:.0f}",
        '__GPU_PERCENTAGE__': f"{analysis['resource_usage']['gpu_percentage']:.0f}",
        '__REPORT_DATE__': datetime.now().strftime('%B %d, %Y'),
        '__START_DATE__': data['metadata']['start_date'],
        '__END_DATE__': datetime.now().strftime('%Y-%m-%d'),
        '__AVG_DURATION__': f"{analysis['job_patterns'].get('avg_duration', 0):.1f}",
        '__SHORT_JOBS__': str(analysis['job_patterns'].get('short_jobs', 0)),
        '__MEDIUM_JOBS__': str(analysis['job_patterns'].get('medium_jobs', 0)),
        '__LONG_JOBS__': str(analysis['job_patterns'].get('long_jobs', 0)),
        '__TOP_EMITTERS__': top_emitters_html,
        '__EFFICIENCY_LEADERS__': efficiency_html,
        '__RECOMMENDATIONS__': recommendations_html,
        '__USER_TABLE__': user_table_html,
        '__DAILY_DATA__': daily_data_json,
        '__RESOURCE_DATA__': resource_data_json,
        '__EMITTERS_TITLE__': 'Top Carbon Emitters' if show_rankings else 'Carbon Usage',
        '__EFFICIENCY_TITLE__': 'Efficiency Leaders' if show_rankings else 'Efficiency Metrics',
        '__EFFICIENCY_DESCRIPTION__': '<p style="margin-bottom: 1rem; color: var(--ash);">Users with the lowest carbon emissions per compute hour</p>' if show_rankings else ''
    }
    
    # Generate HTML
    html = HTML_TEMPLATE
    for key, value in replacements.items():
        html = html.replace(key, str(value))
    
    # Write output
    with open(output_file, 'w') as f:
        f.write(html)
    
    print(f"[SUCCESS] Comprehensive team report generated: {output_file}")
    print(f"\nReport Highlights:")
    print(f"  Team Members: {data['summary']['unique_users']}")
    print(f"  Total Jobs: {data['metadata']['total_jobs']}")
    print(f"  Total Carbon: {data['summary']['total_carbon_kg']:.2f} kg CO2")
    print(f"  Top Emitter: {analysis['top_emitters'][0][0]} ({analysis['top_emitters'][0][1]:.2f} kg)")
    print(f"  Most Efficient: {analysis['efficiency_leaders'][0][0]} ({analysis['efficiency_leaders'][0][1]:.4f} kg/hr)")
    print(f"\n  {len(analysis['recommendations'])} recommendations generated")


def main():
    parser = argparse.ArgumentParser(
        description='Generate comprehensive team carbon emissions report'
    )
    parser.add_argument(
        '--input',
        required=True,
        help='Input JSON file (from collect_arc_data.py or merge_team_data.py)'
    )
    parser.add_argument(
        '--output',
        default='team_report.html',
        help='Output HTML report filename (default: team_report.html)'
    )
    
    args = parser.parse_args()
    
    generate_report(args.input, args.output)


if __name__ == '__main__':
    main()
