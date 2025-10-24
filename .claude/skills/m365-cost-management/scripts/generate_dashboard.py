#!/usr/bin/env python3
"""
Generate static HTML dashboard from M365 cost data.

Creates a single HTML file with embedded data and Chart.js visualizations.
Follows Jony Ive and Edward Tufte design principles with Nord frost colors.
"""

import os
import sys
import json
import sqlite3
from datetime import datetime
from typing import Dict, List
from dotenv import load_dotenv


def get_latest_run_id(conn: sqlite3.Connection) -> tuple[int, bool]:
    """
    Get the most recent collection run and check if complete.

    Returns:
        Tuple of (run_id, is_complete)
    """
    cursor = conn.cursor()

    # Try to get completed run first
    cursor.execute("""
        SELECT id, status FROM collection_runs
        WHERE status = 'completed'
        ORDER BY timestamp DESC
        LIMIT 1
    """)
    result = cursor.fetchone()

    if result:
        return result[0], True

    # Check for running or failed runs with data
    cursor.execute("""
        SELECT id, status FROM collection_runs
        WHERE status IN ('running', 'failed')
        ORDER BY timestamp DESC
        LIMIT 1
    """)
    result = cursor.fetchone()

    if result:
        run_id, status = result
        print(f"Warning: Using data from {status} collection run {run_id}")
        print("Data may be incomplete. Re-run collect_m365_data.py to complete.")
        return run_id, False

    print("No data collection found. Run collect_m365_data.py first.")
    sys.exit(1)


def get_collection_metadata(conn: sqlite3.Connection, run_id: int) -> dict:
    """Get metadata about the collection run."""
    cursor = conn.cursor()

    # Get run info
    cursor.execute("""
        SELECT
            timestamp,
            status,
            records_collected,
            error_message
        FROM collection_runs
        WHERE id = ?
    """, (run_id,))
    row = cursor.fetchone()

    if not row:
        return {}

    metadata = {
        'run_id': run_id,
        'timestamp': row[0],
        'status': row[1],
        'records_collected': row[2],
        'error_message': row[3]
    }

    # Get latest progress if available
    cursor.execute("""
        SELECT phase, progress, total, message
        FROM collection_progress
        WHERE collection_run_id = ?
        ORDER BY id DESC
        LIMIT 1
    """, (run_id,))
    progress_row = cursor.fetchone()

    if progress_row:
        metadata['last_phase'] = progress_row[0]
        metadata['progress'] = progress_row[1]
        metadata['total'] = progress_row[2]
        metadata['progress_pct'] = (progress_row[1] / progress_row[2] * 100) if progress_row[2] > 0 else 0
        metadata['progress_message'] = progress_row[3]

    return metadata


def get_dashboard_data(db_path: str, inactive_days: int = 90) -> Dict:
    """Fetch all data needed for dashboard."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    run_id, is_complete = get_latest_run_id(conn)
    metadata = get_collection_metadata(conn, run_id)

    # Total costs
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            SUM(l.assigned_licenses * p.monthly_cost) as total_monthly,
            SUM(l.total_licenses) as total_licenses,
            SUM(l.assigned_licenses) as assigned_licenses,
            SUM(l.available_licenses) as available_licenses
        FROM licenses l
        INNER JOIN price_lookup p ON l.sku_id = p.sku_id
        WHERE l.collection_run_id = ?
    """, (run_id,))
    costs = dict(cursor.fetchone())

    # Costs by SKU
    cursor.execute("""
        SELECT
            l.sku_name,
            l.total_licenses,
            l.assigned_licenses,
            l.available_licenses,
            p.monthly_cost,
            (l.assigned_licenses * p.monthly_cost) as total_monthly_cost,
            ROUND(100.0 * l.assigned_licenses / NULLIF(l.total_licenses, 0), 1) as utilization_pct
        FROM licenses l
        INNER JOIN price_lookup p ON l.sku_id = p.sku_id
        WHERE l.collection_run_id = ?
        ORDER BY total_monthly_cost DESC
    """, (run_id,))
    costs_by_sku = [dict(row) for row in cursor.fetchall()]

    # Inactive users summary
    cursor.execute("""
        SELECT
            p.sku_name,
            COUNT(DISTINCT ul.user_principal_name) as inactive_count,
            p.monthly_cost,
            (COUNT(DISTINCT ul.user_principal_name) * p.monthly_cost) as total_monthly_cost
        FROM user_licenses ul
        INNER JOIN user_activity ua ON ul.user_principal_name = ua.user_principal_name
            AND ul.collection_run_id = ua.collection_run_id
        INNER JOIN price_lookup p ON ul.sku_id = p.sku_id
        WHERE ul.collection_run_id = ?
            AND (ua.last_sign_in_date IS NULL
                OR ua.last_sign_in_date < datetime('now', '-{} days'))
        GROUP BY p.sku_name, p.monthly_cost
        ORDER BY total_monthly_cost DESC
    """.format(inactive_days), (run_id,))
    inactive_summary = [dict(row) for row in cursor.fetchall()]

    # Inactive users detail
    cursor.execute("""
        SELECT
            ul.user_principal_name,
            p.sku_name,
            p.monthly_cost,
            ua.last_sign_in_date,
            CASE
                WHEN ua.last_sign_in_date IS NULL THEN 9999
                ELSE CAST((julianday('now') - julianday(ua.last_sign_in_date)) AS INTEGER)
            END as days_inactive
        FROM user_licenses ul
        INNER JOIN user_activity ua ON ul.user_principal_name = ua.user_principal_name
            AND ul.collection_run_id = ua.collection_run_id
        INNER JOIN price_lookup p ON ul.sku_id = p.sku_id
        WHERE ul.collection_run_id = ?
            AND (ua.last_sign_in_date IS NULL
                OR ua.last_sign_in_date < datetime('now', '-{} days'))
        ORDER BY p.monthly_cost DESC, days_inactive DESC
    """.format(inactive_days), (run_id,))
    inactive_users = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return {
        'costs': costs,
        'costs_by_sku': costs_by_sku,
        'inactive_summary': inactive_summary,
        'inactive_users': inactive_users,
        'inactive_days': inactive_days,
        'generated_at': datetime.now().isoformat(),
        'metadata': metadata,
        'is_complete': is_complete
    }


def generate_html(data: Dict, output_path: str):
    """Generate static HTML dashboard."""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>M365 Cost Management</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            font-weight: 300;
            color: #2E3440;
            background: #ECEFF4;
            padding: 2rem;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: #fff;
            padding: 3rem;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(46, 52, 64, 0.1);
        }}

        h1 {{
            font-weight: 300;
            font-size: 2.5rem;
            margin-bottom: 3rem;
            color: #2E3440;
        }}

        h2 {{
            font-weight: 300;
            font-size: 1.8rem;
            margin: 3rem 0 1.5rem 0;
            color: #2E3440;
        }}

        h3 {{
            font-weight: 400;
            font-size: 1.2rem;
            margin: 2rem 0 1rem 0;
            color: #2E3440;
        }}

        .tabs {{
            display: flex;
            gap: 0;
            margin-bottom: 3rem;
            border-bottom: 1px solid #D8DEE9;
        }}

        .tab {{
            padding: 1rem 2rem;
            background: none;
            border: none;
            cursor: pointer;
            font-size: 1rem;
            font-weight: 400;
            color: #4C566A;
            transition: all 0.2s;
            border-bottom: 2px solid transparent;
        }}

        .tab:hover {{
            color: #2E3440;
        }}

        .tab.active {{
            color: #5E81AC;
            border-bottom: 2px solid #5E81AC;
        }}

        .page {{
            display: none;
        }}

        .page.active {{
            display: block;
        }}

        .hero-metric {{
            text-align: center;
            margin: 4rem 0;
        }}

        .hero-value {{
            font-size: 4rem;
            font-weight: 200;
            color: #5E81AC;
        }}

        .hero-label {{
            font-size: 1rem;
            color: #4C566A;
            margin-top: 1rem;
        }}

        .hero-sublabel {{
            font-size: 0.9rem;
            color: #D8DEE9;
            margin-top: 0.5rem;
        }}

        .chart-container {{
            margin: 2rem 0;
            padding: 1rem 0;
        }}

        canvas {{
            max-height: 500px;
        }}

        .caption {{
            font-size: 0.9rem;
            color: #4C566A;
            margin-top: 1rem;
            text-align: center;
        }}

        .action-list {{
            list-style: none;
            margin: 2rem 0;
        }}

        .action-item {{
            padding: 1.5rem 0;
            border-bottom: 1px solid #ECEFF4;
        }}

        .action-item:last-child {{
            border-bottom: none;
        }}

        .action-title {{
            font-weight: 400;
            font-size: 1.1rem;
            color: #2E3440;
            margin-bottom: 0.5rem;
        }}

        .action-detail {{
            color: #4C566A;
            font-size: 0.9rem;
        }}

        .checklist {{
            margin: 2rem 0;
            padding: 1.5rem;
            background: #ECEFF4;
            border-radius: 4px;
        }}

        .checklist ul {{
            list-style: none;
            margin-top: 1rem;
        }}

        .checklist li {{
            padding: 0.5rem 0;
            color: #4C566A;
        }}

        .checklist li:before {{
            content: "—";
            margin-right: 0.5rem;
            color: #5E81AC;
        }}

        .download-btn {{
            display: inline-block;
            padding: 0.75rem 1.5rem;
            background: #5E81AC;
            color: white;
            text-decoration: none;
            border-radius: 4px;
            font-weight: 400;
            margin-top: 1rem;
            transition: background 0.2s;
        }}

        .download-btn:hover {{
            background: #81A1C1;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 2rem 0;
        }}

        th, td {{
            text-align: left;
            padding: 1rem;
            border-bottom: 1px solid #ECEFF4;
        }}

        th {{
            font-weight: 400;
            color: #4C566A;
            font-size: 0.9rem;
        }}

        td {{
            color: #2E3440;
        }}

        tr:hover {{
            background: #ECEFF4;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Microsoft 365 Cost Management</h1>

        <div class="tabs">
            <button class="tab active" onclick="showPage('overview')">Overview</button>
            <button class="tab" onclick="showPage('inactive')">Inactive Users</button>
            <button class="tab" onclick="showPage('utilization')">License Utilization</button>
            <button class="tab" onclick="showPage('actions')">Actions</button>
        </div>

        <div id="overview" class="page active">
            <!-- Overview page content will be inserted by JavaScript -->
        </div>

        <div id="inactive" class="page">
            <!-- Inactive users page content will be inserted by JavaScript -->
        </div>

        <div id="utilization" class="page">
            <!-- Utilization page content will be inserted by JavaScript -->
        </div>

        <div id="actions" class="page">
            <!-- Actions page content will be inserted by JavaScript -->
        </div>
    </div>

    <script>
        // Embedded data
        const data = {json.dumps(data, indent=8)};

        // Nord frost colors
        const colors = {{
            frost1: '#8FBCBB',
            frost2: '#88C0D0',
            frost3: '#81A1C1',
            frost4: '#5E81AC',
            dark: '#2E3440',
            gray: '#4C566A',
            lightGray: '#D8DEE9'
        }};

        // Helper functions
        function formatCurrency(value) {{
            return new Intl.NumberFormat('en-US', {{
                style: 'currency',
                currency: 'USD',
                minimumFractionDigits: 2
            }}).format(value);
        }}

        function showPage(pageId) {{
            // Hide all pages
            document.querySelectorAll('.page').forEach(page => {{
                page.classList.remove('active');
            }});

            // Remove active from all tabs
            document.querySelectorAll('.tab').forEach(tab => {{
                tab.classList.remove('active');
            }});

            // Show selected page
            document.getElementById(pageId).classList.add('active');

            // Activate clicked tab
            event.target.classList.add('active');
        }}

        // Calculate savings
        const inactiveMonthly = data.inactive_summary.reduce((sum, item) => sum + item.total_monthly_cost, 0);
        const unassignedMonthly = data.costs_by_sku.reduce((sum, item) => sum + (item.available_licenses * item.monthly_cost), 0);
        const totalSavings = inactiveMonthly + unassignedMonthly;
        const savingsPct = (totalSavings / data.costs.total_monthly * 100).toFixed(1);

        // Render Overview page
        function renderOverview() {{
            const top8 = data.costs_by_sku.slice(0, 8);

            const html = `
                <div class="hero-metric">
                    <div class="hero-value">${{savingsPct}}%</div>
                    <div class="hero-label">potential cost reduction</div>
                    <div class="hero-sublabel">${{formatCurrency(totalSavings)}}/month · ${{formatCurrency(totalSavings * 12)}}/year</div>
                </div>

                <h3>Current Spending</h3>
                <div class="chart-container">
                    <canvas id="overviewChart"></canvas>
                </div>
                <div class="caption">Total monthly cost: ${{formatCurrency(data.costs.total_monthly)}} across ${{data.costs_by_sku.length}} license types</div>
            `;

            document.getElementById('overview').innerHTML = html;

            // Create chart
            const ctx = document.getElementById('overviewChart').getContext('2d');
            new Chart(ctx, {{
                type: 'bar',
                data: {{
                    labels: top8.map(item => item.sku_name),
                    datasets: [{{
                        data: top8.map(item => item.total_monthly_cost),
                        backgroundColor: colors.frost4,
                        borderWidth: 0
                    }}]
                }},
                options: {{
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        legend: {{
                            display: false
                        }},
                        tooltip: {{
                            callbacks: {{
                                label: function(context) {{
                                    return formatCurrency(context.parsed.x) + '/month';
                                }}
                            }}
                        }}
                    }},
                    scales: {{
                        x: {{
                            display: false,
                            grid: {{
                                display: false
                            }}
                        }},
                        y: {{
                            grid: {{
                                display: false
                            }},
                            ticks: {{
                                font: {{
                                    size: 12
                                }}
                            }}
                        }}
                    }}
                }}
            }});
        }}

        // Render Inactive Users page
        function renderInactive() {{
            const totalInactive = data.inactive_summary.reduce((sum, item) => sum + item.inactive_count, 0);
            const totalCost = data.inactive_summary.reduce((sum, item) => sum + item.total_monthly_cost, 0);

            const html = `
                <h3>Inactive Users</h3>
                <p style="color: #4C566A; margin-bottom: 2rem;">${{data.inactive_days}}+ days without sign-in</p>

                <div class="hero-metric">
                    <div class="hero-value">${{totalInactive.toLocaleString()}}</div>
                    <div class="hero-label">inactive users</div>
                    <div class="hero-sublabel">${{formatCurrency(totalCost)}}/month · ${{formatCurrency(totalCost * 12)}}/year</div>
                </div>

                <h3>By License Type</h3>
                <div class="chart-container">
                    <canvas id="inactiveChart"></canvas>
                </div>

                <a href="#" class="download-btn" onclick="downloadInactiveUsers(); return false;">Download user list</a>
            `;

            document.getElementById('inactive').innerHTML = html;

            // Create chart
            const sorted = [...data.inactive_summary].reverse();
            const ctx = document.getElementById('inactiveChart').getContext('2d');
            new Chart(ctx, {{
                type: 'bar',
                data: {{
                    labels: sorted.map(item => item.sku_name),
                    datasets: [{{
                        data: sorted.map(item => item.inactive_count),
                        backgroundColor: colors.frost3,
                        borderWidth: 0
                    }}]
                }},
                options: {{
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        legend: {{
                            display: false
                        }},
                        tooltip: {{
                            callbacks: {{
                                label: function(context) {{
                                    const index = context.dataIndex;
                                    const users = sorted[index].inactive_count;
                                    const cost = sorted[index].total_monthly_cost;
                                    return users + ' users · ' + formatCurrency(cost) + '/mo';
                                }}
                            }}
                        }}
                    }},
                    scales: {{
                        x: {{
                            display: false,
                            grid: {{
                                display: false
                            }}
                        }},
                        y: {{
                            grid: {{
                                display: false
                            }},
                            ticks: {{
                                font: {{
                                    size: 12
                                }}
                            }}
                        }}
                    }}
                }}
            }});
        }}

        // Render Utilization page
        function renderUtilization() {{
            const underutilized = data.costs_by_sku
                .filter(item => item.available_licenses > 0)
                .map(item => ({{
                    ...item,
                    waste: item.available_licenses * item.monthly_cost
                }}))
                .sort((a, b) => a.waste - b.waste);

            const totalWaste = underutilized.reduce((sum, item) => sum + item.waste, 0);

            if (underutilized.length === 0) {{
                document.getElementById('utilization').innerHTML = '<p style="color: #4C566A;">All licenses are fully utilized.</p>';
                return;
            }}

            let tableRows = '';
            underutilized.forEach(item => {{
                tableRows += `
                    <tr>
                        <td>${{item.sku_name}}</td>
                        <td>${{item.available_licenses}}</td>
                        <td>${{formatCurrency(item.monthly_cost)}}</td>
                        <td>${{formatCurrency(item.waste)}}</td>
                    </tr>
                `;
            }});

            const html = `
                <h3>License Utilization</h3>

                <div class="hero-metric">
                    <div class="hero-value">${{formatCurrency(totalWaste)}}</div>
                    <div class="hero-label">wasted on unassigned licenses</div>
                    <div class="hero-sublabel">${{formatCurrency(totalWaste * 12)}}/year</div>
                </div>

                <h3>Unassigned Licenses</h3>
                <div class="chart-container">
                    <canvas id="utilizationChart"></canvas>
                </div>

                <h3>Details</h3>
                <table>
                    <thead>
                        <tr>
                            <th>License Type</th>
                            <th>Unassigned</th>
                            <th>Cost per License</th>
                            <th>Monthly Waste</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${{tableRows}}
                    </tbody>
                </table>
            `;

            document.getElementById('utilization').innerHTML = html;

            // Create chart
            const ctx = document.getElementById('utilizationChart').getContext('2d');
            new Chart(ctx, {{
                type: 'bar',
                data: {{
                    labels: underutilized.map(item => item.sku_name),
                    datasets: [{{
                        data: underutilized.map(item => item.available_licenses),
                        backgroundColor: colors.frost2,
                        borderWidth: 0
                    }}]
                }},
                options: {{
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        legend: {{
                            display: false
                        }},
                        tooltip: {{
                            callbacks: {{
                                label: function(context) {{
                                    const index = context.dataIndex;
                                    const licenses = underutilized[index].available_licenses;
                                    const waste = underutilized[index].waste;
                                    return licenses + ' licenses · ' + formatCurrency(waste) + '/mo';
                                }}
                            }}
                        }}
                    }},
                    scales: {{
                        x: {{
                            display: false,
                            grid: {{
                                display: false
                            }}
                        }},
                        y: {{
                            grid: {{
                                display: false
                            }},
                            ticks: {{
                                font: {{
                                    size: 12
                                }}
                            }}
                        }}
                    }}
                }}
            }});
        }}

        // Render Actions page
        function renderActions() {{
            const actions = [];

            // Add inactive user actions
            data.inactive_summary.slice(0, 5).forEach(item => {{
                actions.push({{
                    action: `Review ${{item.inactive_count}} inactive ${{item.sku_name}} users`,
                    savings: item.total_monthly_cost,
                    note: `${{data.inactive_days}}+ days without sign-in`
                }});
            }});

            // Add unassigned license actions
            const unassigned = data.costs_by_sku
                .filter(item => item.available_licenses > 0)
                .map(item => ({{
                    ...item,
                    potential_savings: item.available_licenses * item.monthly_cost
                }}))
                .sort((a, b) => b.potential_savings - a.potential_savings)
                .slice(0, 5);

            unassigned.forEach(item => {{
                actions.push({{
                    action: `Remove ${{item.available_licenses}} unassigned ${{item.sku_name}} licenses`,
                    savings: item.potential_savings,
                    note: 'Currently unused'
                }});
            }});

            // Sort by savings
            actions.sort((a, b) => b.savings - a.savings);

            let actionItems = '';
            actions.forEach((item, index) => {{
                actionItems += `
                    <li class="action-item">
                        <div class="action-title">${{index + 1}}. ${{item.action}}</div>
                        <div class="action-detail">${{formatCurrency(item.savings)}}/month · ${{item.note}}</div>
                    </li>
                `;
            }});

            const html = `
                <h3>Actions</h3>

                <div class="hero-metric">
                    <div class="hero-value">${{formatCurrency(totalSavings)}}</div>
                    <div class="hero-label">potential monthly savings</div>
                </div>

                <h3>Recommended Steps</h3>
                <ul class="action-list">
                    ${{actionItems}}
                </ul>

                <div class="checklist">
                    <h3 style="margin: 0 0 1rem 0;">Before Taking Action</h3>
                    <p style="color: #4C566A; margin-bottom: 1rem;">Verify each user or license before removal:</p>
                    <ul>
                        <li>Cross-reference with HR termination records</li>
                        <li>Check for extended leave (medical, parental, sabbatical)</li>
                        <li>Exclude service accounts and special cases</li>
                        <li>Obtain IT leadership approval</li>
                    </ul>
                </div>

                <div class="checklist">
                    <h3 style="margin: 0 0 1rem 0;">Ongoing Process</h3>
                    <p style="color: #4C566A; margin-bottom: 1rem;">Establish regular review cycle:</p>
                    <ul>
                        <li>Monthly: Review unassigned licenses</li>
                        <li>Quarterly: Analyze inactive users</li>
                        <li>Annually: Audit all license assignments</li>
                    </ul>
                </div>
            `;

            document.getElementById('actions').innerHTML = html;
        }}

        // Download inactive users as CSV
        function downloadInactiveUsers() {{
            const csvContent = [
                ['User Principal Name', 'License Type', 'Monthly Cost', 'Last Sign In', 'Days Inactive'].join(','),
                ...data.inactive_users.map(user => [
                    user.user_principal_name,
                    user.sku_name,
                    user.monthly_cost,
                    user.last_sign_in_date || 'Never',
                    user.days_inactive === 9999 ? 'Never' : user.days_inactive
                ].join(','))
            ].join('\\n');

            const blob = new Blob([csvContent], {{ type: 'text/csv' }});
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `inactive_users_${{new Date().toISOString().split('T')[0]}}.csv`;
            a.click();
            window.URL.revokeObjectURL(url);
        }}

        // Initialize dashboard
        renderOverview();
        renderInactive();
        renderUtilization();
        renderActions();
    </script>
</body>
</html>
"""

    with open(output_path, 'w') as f:
        f.write(html)

    print(f"Dashboard generated: {output_path}")


def main():
    """Main entry point."""
    load_dotenv()

    db_path = os.getenv("DATABASE_PATH", "./data/m365_costs.db")
    output_path = os.getenv("DASHBOARD_OUTPUT", "./m365_dashboard.html")

    if not os.path.exists(db_path):
        print(f"Database not found: {db_path}")
        print("Run collect_m365_data.py first to collect data.")
        sys.exit(1)

    print("Fetching data from database...")
    data = get_dashboard_data(db_path)

    print("Generating HTML dashboard...")
    generate_html(data, output_path)

    print(f"\nDashboard ready! Open {output_path} in your browser.")


if __name__ == "__main__":
    main()
