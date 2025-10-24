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
    """Get comprehensive metadata about the collection run."""
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
        'records_collected': row[2] if row[2] else 0,
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

    # Count total users collected
    cursor.execute("""
        SELECT COUNT(*) FROM user_activity
        WHERE collection_run_id = ?
    """, (run_id,))
    metadata['total_users'] = cursor.fetchone()[0]

    # Count total licenses collected
    cursor.execute("""
        SELECT COUNT(*) FROM licenses
        WHERE collection_run_id = ?
    """, (run_id,))
    metadata['total_licenses'] = cursor.fetchone()[0]

    return metadata


def get_checkpoint_info(conn: sqlite3.Connection, run_id: int) -> list[dict]:
    """Get checkpoint information for the collection run."""
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            timestamp,
            phase,
            progress,
            total,
            details
        FROM collection_checkpoints
        WHERE collection_run_id = ?
        ORDER BY id DESC
        LIMIT 10
    """, (run_id,))

    checkpoints = []
    for row in cursor.fetchall():
        checkpoints.append({
            'timestamp': row[0],
            'phase': row[1],
            'progress': row[2],
            'total': row[3],
            'details': row[4]
        })

    return checkpoints


def get_retry_info(conn: sqlite3.Connection, run_id: int) -> dict:
    """Get retry/rate limiting information for the collection run."""
    cursor = conn.cursor()

    # Get total retry count
    cursor.execute("""
        SELECT COUNT(*) FROM retry_log
        WHERE collection_run_id = ?
    """, (run_id,))
    total_retries = cursor.fetchone()[0]

    # Get recent retries
    cursor.execute("""
        SELECT
            timestamp,
            endpoint,
            attempt,
            delay,
            reason
        FROM retry_log
        WHERE collection_run_id = ?
        ORDER BY id DESC
        LIMIT 10
    """, (run_id,))

    retries = []
    for row in cursor.fetchall():
        retries.append({
            'timestamp': row[0],
            'endpoint': row[1],
            'attempt': row[2],
            'delay': row[3],
            'reason': row[4]
        })

    return {
        'total_retries': total_retries,
        'recent_retries': retries
    }


def get_pricing_data(db_path: str) -> list[dict]:
    """Get all pricing data from the database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            sku_id,
            sku_name,
            monthly_cost
        FROM price_lookup
        ORDER BY sku_name ASC
    """)

    pricing = []
    for row in cursor.fetchall():
        pricing.append({
            'sku_id': row[0],
            'sku_name': row[1],
            'monthly_cost': row[2]
        })

    conn.close()
    return pricing


def generate_pricing_update_sql(changes: list[dict]) -> str:
    """
    Generate SQL UPDATE statements for pricing changes.

    Args:
        changes: List of dicts with sku_id, sku_name, monthly_cost

    Returns:
        SQL statements as a string
    """
    if not changes:
        return "-- No pricing changes to apply\n"

    sql_lines = []
    sql_lines.append("-- Pricing updates generated by M365 Cost Management Dashboard")
    sql_lines.append("-- Run these statements to update the database")
    sql_lines.append("")

    for change in changes:
        sku_id = change['sku_id']
        sku_name = change['sku_name']
        monthly_cost = change['monthly_cost']

        sql_lines.append(f"-- Update pricing for {sku_name}")
        sql_lines.append(f"UPDATE price_lookup")
        sql_lines.append(f"SET monthly_cost = {monthly_cost}")
        sql_lines.append(f"WHERE sku_id = '{sku_id}';")
        sql_lines.append("")

    return "\n".join(sql_lines)


def get_dashboard_data(db_path: str, inactive_days: int = 90) -> Dict:
    """Fetch all data needed for dashboard."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    run_id, is_complete = get_latest_run_id(conn)
    metadata = get_collection_metadata(conn, run_id)
    checkpoints = get_checkpoint_info(conn, run_id)
    retry_info = get_retry_info(conn, run_id)
    pricing = get_pricing_data(db_path)

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
    costs_row = cursor.fetchone()
    costs = dict(costs_row) if costs_row else {
        'total_monthly': 0,
        'total_licenses': 0,
        'assigned_licenses': 0,
        'available_licenses': 0
    }

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
        'checkpoints': checkpoints,
        'retry_info': retry_info,
        'pricing': pricing,
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
            margin-bottom: 1rem;
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

        h4 {{
            font-weight: 400;
            font-size: 1rem;
            margin: 1.5rem 0 0.5rem 0;
            color: #4C566A;
        }}

        p {{
            line-height: 1.6;
            color: #4C566A;
        }}

        .status-banner {{
            padding: 1rem 1.5rem;
            margin-bottom: 2rem;
            border-radius: 4px;
            border-left: 4px solid;
        }}

        .status-banner.warning {{
            background: #EBCB8B20;
            border-color: #EBCB8B;
            color: #5E4F21;
        }}

        .status-banner.error {{
            background: #BF616A20;
            border-color: #BF616A;
            color: #6B1A22;
        }}

        .status-banner.success {{
            background: #A3BE8C20;
            border-color: #A3BE8C;
            color: #2F4F21;
        }}

        .status-banner h3 {{
            margin: 0 0 0.5rem 0;
            font-size: 1rem;
            font-weight: 600;
        }}

        .status-banner p {{
            margin: 0;
            font-size: 0.9rem;
        }}

        .tabs {{
            display: flex;
            gap: 0;
            border-bottom: 1px solid #D8DEE9;
            margin-bottom: 2rem;
        }}

        .tab {{
            padding: 1rem 2rem;
            background: none;
            border: none;
            color: #4C566A;
            font-size: 0.95rem;
            font-weight: 400;
            cursor: pointer;
            border-bottom: 3px solid transparent;
            transition: all 0.2s;
        }}

        .tab:hover {{
            color: #2E3440;
            background: #F5F7FA;
        }}

        .tab.active {{
            color: #5E81AC;
            border-bottom-color: #5E81AC;
        }}

        .page {{
            display: none;
        }}

        .page.active {{
            display: block;
        }}

        .hero-metric {{
            text-align: center;
            padding: 3rem 0;
            border-bottom: 1px solid #ECEFF4;
            margin-bottom: 3rem;
        }}

        .hero-value {{
            font-size: 5rem;
            font-weight: 100;
            color: #5E81AC;
            line-height: 1;
        }}

        .hero-label {{
            font-size: 1.2rem;
            color: #4C566A;
            margin-top: 0.5rem;
            font-weight: 300;
        }}

        .hero-sublabel {{
            font-size: 0.95rem;
            color: #4C566A;
            margin-top: 0.5rem;
        }}

        .chart-container {{
            position: relative;
            height: 400px;
            margin: 2rem 0;
        }}

        .caption {{
            text-align: center;
            color: #4C566A;
            font-size: 0.9rem;
            margin-top: 1rem;
        }}

        .download-btn {{
            display: inline-block;
            margin: 2rem 0;
            padding: 0.75rem 2rem;
            background: #5E81AC;
            color: white;
            text-decoration: none;
            border-radius: 4px;
            font-size: 0.95rem;
            transition: background 0.2s;
        }}

        .download-btn:hover {{
            background: #4C6A94;
        }}

        .actions-list {{
            list-style: none;
            margin: 2rem 0;
        }}

        .actions-list li {{
            padding: 1.5rem;
            border-left: 3px solid #5E81AC;
            margin-bottom: 1rem;
            background: #F9FAFB;
        }}

        .actions-list .action-title {{
            font-weight: 500;
            font-size: 1.1rem;
            color: #2E3440;
            margin-bottom: 0.5rem;
        }}

        .actions-list .action-impact {{
            color: #5E81AC;
            font-weight: 400;
            margin-bottom: 0.5rem;
        }}

        .actions-list .action-desc {{
            color: #4C566A;
            line-height: 1.6;
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

        .meta-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin: 2rem 0;
        }}

        .meta-card {{
            padding: 1.5rem;
            background: #F9FAFB;
            border-radius: 4px;
            border-left: 3px solid #5E81AC;
        }}

        .meta-label {{
            font-size: 0.85rem;
            color: #4C566A;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 0.5rem;
        }}

        .meta-value {{
            font-size: 1.5rem;
            font-weight: 300;
            color: #2E3440;
        }}

        .checkpoint-list {{
            list-style: none;
            margin: 1rem 0;
        }}

        .checkpoint-list li {{
            padding: 0.75rem 1rem;
            background: #F9FAFB;
            margin-bottom: 0.5rem;
            border-radius: 4px;
            font-family: 'Monaco', 'Courier New', monospace;
            font-size: 0.85rem;
            color: #4C566A;
        }}

        .checkpoint-phase {{
            color: #5E81AC;
            font-weight: 600;
        }}

        .retry-list {{
            list-style: none;
            margin: 1rem 0;
        }}

        .retry-list li {{
            padding: 0.75rem 1rem;
            background: #EBCB8B20;
            margin-bottom: 0.5rem;
            border-radius: 4px;
            border-left: 3px solid #EBCB8B;
            font-size: 0.85rem;
            color: #4C566A;
        }}

        .retry-endpoint {{
            color: #5E81AC;
            font-weight: 600;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Microsoft 365 Cost Management</h1>

        <div id="statusBanner"></div>

        <div class="tabs">
            <button class="tab active" onclick="showPage('overview')">Overview</button>
            <button class="tab" onclick="showPage('inactive')">Inactive Users</button>
            <button class="tab" onclick="showPage('utilization')">License Utilization</button>
            <button class="tab" onclick="showPage('actions')">Actions</button>
            <button class="tab" onclick="showPage('pricing')">Pricing</button>
            <button class="tab" onclick="showPage('collection')">Collection Info</button>
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

        <div id="pricing" class="page">
            <!-- Pricing page content will be inserted by JavaScript -->
        </div>

        <div id="collection" class="page">
            <!-- Collection info page content will be inserted by JavaScript -->
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
            lightGray: '#D8DEE9',
            warning: '#EBCB8B',
            error: '#BF616A',
            success: '#A3BE8C'
        }};

        // Helper functions
        function formatCurrency(value) {{
            return new Intl.NumberFormat('en-US', {{
                style: 'currency',
                currency: 'USD',
                minimumFractionDigits: 2
            }}).format(value);
        }}

        function formatDateTime(isoString) {{
            if (!isoString) return 'N/A';
            const date = new Date(isoString);
            return date.toLocaleString('en-US', {{
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            }});
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

            // Mark tab as active
            event.target.classList.add('active');
        }}

        // Render status banner
        function renderStatusBanner() {{
            const status = data.metadata.status;
            const isComplete = data.is_complete;

            let bannerHtml = '';

            if (!isComplete) {{
                if (status === 'running') {{
                    bannerHtml = `
                        <div class="status-banner warning">
                            <h3>⚠️ Collection In Progress</h3>
                            <p>Data collection is currently running. Dashboard shows partial data. Refresh after collection completes.</p>
                        </div>
                    `;
                }} else if (status === 'failed') {{
                    bannerHtml = `
                        <div class="status-banner error">
                            <h3>❌ Collection Failed</h3>
                            <p>The last data collection failed. Dashboard shows partial data from the incomplete run. Check Collection Info tab for details.</p>
                        </div>
                    `;
                }}
            }} else {{
                bannerHtml = `
                    <div class="status-banner success">
                        <h3>✓ Complete Data</h3>
                        <p>Dashboard shows data from completed collection run #${{data.metadata.run_id}} on ${{formatDateTime(data.metadata.timestamp)}}.</p>
                    </div>
                `;
            }}

            document.getElementById('statusBanner').innerHTML = bannerHtml;
        }}

        // Calculate total savings
        const totalInactiveCost = data.inactive_summary.reduce((sum, item) => sum + item.total_monthly_cost, 0);
        const totalUnassignedCost = data.costs_by_sku
            .filter(item => item.available_licenses > 0)
            .reduce((sum, item) => sum + (item.available_licenses * item.monthly_cost), 0);
        const totalSavings = totalInactiveCost + totalUnassignedCost;
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
                    waste_monthly: item.available_licenses * item.monthly_cost
                }}))
                .sort((a, b) => b.waste_monthly - a.waste_monthly);

            const totalWaste = underutilized.reduce((sum, item) => sum + item.waste_monthly, 0);

            const html = `
                <h3>License Utilization</h3>
                <p style="color: #4C566A; margin-bottom: 2rem;">Unassigned licenses costing money</p>

                <div class="hero-metric">
                    <div class="hero-value">${{formatCurrency(totalWaste)}}</div>
                    <div class="hero-label">monthly waste</div>
                    <div class="hero-sublabel">${{formatCurrency(totalWaste * 12)}}/year from unassigned licenses</div>
                </div>

                <h3>Unassigned Licenses by Type</h3>
                <table>
                    <thead>
                        <tr>
                            <th>License Type</th>
                            <th style="text-align: right;">Unassigned</th>
                            <th style="text-align: right;">Total</th>
                            <th style="text-align: right;">Utilization</th>
                            <th style="text-align: right;">Monthly Waste</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${{underutilized.map(item => `
                            <tr>
                                <td>${{item.sku_name}}</td>
                                <td style="text-align: right;">${{item.available_licenses}}</td>
                                <td style="text-align: right;">${{item.total_licenses}}</td>
                                <td style="text-align: right;">${{item.utilization_pct}}%</td>
                                <td style="text-align: right;">${{formatCurrency(item.waste_monthly)}}</td>
                            </tr>
                        `).join('')}}
                    </tbody>
                </table>
            `;

            document.getElementById('utilization').innerHTML = html;
        }}

        // Render Actions page
        function renderActions() {{
            const actions = [];

            // Inactive users action
            const totalInactive = data.inactive_summary.reduce((sum, item) => sum + item.inactive_count, 0);
            const inactiveCost = data.inactive_summary.reduce((sum, item) => sum + item.total_monthly_cost, 0);

            if (totalInactive > 0) {{
                actions.push({{
                    title: 'Remove licenses from inactive users',
                    impact: formatCurrency(inactiveCost * 12) + '/year',
                    description: `${{totalInactive}} users haven't signed in for ${{data.inactive_days}}+ days. Cross-reference with HR termination records before removing licenses.`
                }});
            }}

            // Unassigned licenses action
            const underutilized = data.costs_by_sku.filter(item => item.available_licenses > 0);
            const unassignedCost = underutilized.reduce((sum, item) => sum + (item.available_licenses * item.monthly_cost), 0);

            if (underutilized.length > 0) {{
                actions.push({{
                    title: 'Cancel unassigned licenses',
                    impact: formatCurrency(unassignedCost * 12) + '/year',
                    description: `${{underutilized.reduce((sum, item) => sum + item.available_licenses, 0)}} licenses are purchased but not assigned. Consider canceling during next renewal.`
                }});
            }}

            // Low utilization action
            const lowUtil = data.costs_by_sku.filter(item =>
                item.utilization_pct < 80 &&
                item.total_licenses > 5 &&
                item.available_licenses > 0
            );

            if (lowUtil.length > 0) {{
                const lowUtilCost = lowUtil.reduce((sum, item) => sum + (item.available_licenses * item.monthly_cost), 0);
                actions.push({{
                    title: 'Review low-utilization license types',
                    impact: formatCurrency(lowUtilCost * 12) + '/year potential',
                    description: `${{lowUtil.length}} license types have <80% utilization. Review if full allocation is still needed.`
                }});
            }}

            const html = `
                <h3>Recommended Actions</h3>
                <p style="color: #4C566A; margin-bottom: 2rem;">Prioritized by annual savings potential</p>

                <ul class="actions-list">
                    ${{actions.map(action => `
                        <li>
                            <div class="action-title">${{action.title}}</div>
                            <div class="action-impact">💰 ${{action.impact}}</div>
                            <div class="action-desc">${{action.description}}</div>
                        </li>
                    `).join('')}}
                </ul>

                <h3>Before Removing Licenses</h3>
                <ul style="margin: 1rem 0; padding-left: 2rem; color: #4C566A; line-height: 1.8;">
                    <li>Cross-reference with HR termination records</li>
                    <li>Check for extended leave (medical, parental, sabbatical)</li>
                    <li>Exclude service accounts and automation users</li>
                    <li>Obtain IT leadership approval</li>
                    <li>Document all removals for audit trail</li>
                </ul>

                <h3>Ongoing Process</h3>
                <p style="color: #4C566A; line-height: 1.8; margin-top: 1rem;">
                    Run monthly audits to catch license drift. Set calendar reminders to regenerate this dashboard
                    before each billing cycle. Review inactive users quarterly with department managers.
                </p>
            `;

            document.getElementById('actions').innerHTML = html;
        }}

        // Render Collection Info page
        function renderCollection() {{
            const meta = data.metadata;
            const statusClass = meta.status === 'completed' ? 'success' : (meta.status === 'failed' ? 'error' : 'warning');
            const statusEmoji = meta.status === 'completed' ? '✓' : (meta.status === 'failed' ? '❌' : '⏳');

            let html = `
                <h3>Collection Run Information</h3>

                <div class="meta-grid">
                    <div class="meta-card">
                        <div class="meta-label">Status</div>
                        <div class="meta-value">${{statusEmoji}} ${{meta.status}}</div>
                    </div>
                    <div class="meta-card">
                        <div class="meta-label">Run ID</div>
                        <div class="meta-value">#${{meta.run_id}}</div>
                    </div>
                    <div class="meta-card">
                        <div class="meta-label">Timestamp</div>
                        <div class="meta-value" style="font-size: 1.1rem;">${{formatDateTime(meta.timestamp)}}</div>
                    </div>
                    <div class="meta-card">
                        <div class="meta-label">Users Collected</div>
                        <div class="meta-value">${{meta.total_users.toLocaleString()}}</div>
                    </div>
                    <div class="meta-card">
                        <div class="meta-label">Licenses Collected</div>
                        <div class="meta-value">${{meta.total_licenses}}</div>
                    </div>
                    <div class="meta-card">
                        <div class="meta-label">Dashboard Generated</div>
                        <div class="meta-value" style="font-size: 1.1rem;">${{formatDateTime(data.generated_at)}}</div>
                    </div>
                </div>
            `;

            // Show progress if available
            if (meta.progress !== undefined) {{
                const progressPct = meta.progress_pct.toFixed(1);
                html += `
                    <h3>Collection Progress</h3>
                    <div class="meta-grid">
                        <div class="meta-card">
                            <div class="meta-label">Last Phase</div>
                            <div class="meta-value" style="font-size: 1.1rem;">${{meta.last_phase}}</div>
                        </div>
                        <div class="meta-card">
                            <div class="meta-label">Progress</div>
                            <div class="meta-value">${{meta.progress}} / ${{meta.total}}</div>
                        </div>
                        <div class="meta-card">
                            <div class="meta-label">Percentage</div>
                            <div class="meta-value">${{progressPct}}%</div>
                        </div>
                    </div>
                `;

                if (meta.progress_message) {{
                    html += `<p style="color: #4C566A; margin-top: 1rem;">${{meta.progress_message}}</p>`;
                }}
            }}

            // Show error message if available
            if (meta.error_message) {{
                html += `
                    <h3>Error Details</h3>
                    <div class="status-banner error">
                        <p>${{meta.error_message}}</p>
                    </div>
                `;
            }}

            // Show checkpoints
            if (data.checkpoints && data.checkpoints.length > 0) {{
                html += `
                    <h3>Recent Checkpoints</h3>
                    <p style="color: #4C566A; margin-bottom: 1rem;">Last 10 checkpoints from collection run</p>
                    <ul class="checkpoint-list">
                        ${{data.checkpoints.map(cp => `
                            <li>
                                <span class="checkpoint-phase">${{cp.phase}}</span>
                                ${{cp.progress}}/${{cp.total}}
                                at ${{formatDateTime(cp.timestamp)}}
                                ${{cp.details ? ' — ' + cp.details : ''}}
                            </li>
                        `).join('')}}
                    </ul>
                `;
            }}

            // Show retry information
            if (data.retry_info && data.retry_info.total_retries > 0) {{
                html += `
                    <h3>Rate Limiting & Retries</h3>
                    <div class="meta-grid">
                        <div class="meta-card">
                            <div class="meta-label">Total Retries</div>
                            <div class="meta-value">${{data.retry_info.total_retries}}</div>
                        </div>
                    </div>
                `;

                if (data.retry_info.recent_retries && data.retry_info.recent_retries.length > 0) {{
                    html += `
                        <p style="color: #4C566A; margin: 1rem 0;">Recent retry attempts (last 10)</p>
                        <ul class="retry-list">
                            ${{data.retry_info.recent_retries.map(retry => `
                                <li>
                                    <span class="retry-endpoint">${{retry.endpoint}}</span>
                                    — attempt #${{retry.attempt}}, delay ${{retry.delay}}s
                                    at ${{formatDateTime(retry.timestamp)}}
                                    <br><small>${{retry.reason}}</small>
                                </li>
                            `).join('')}}
                        </ul>
                    `;
                }}
            }}

            document.getElementById('collection').innerHTML = html;
        }}

        // Download inactive users as CSV
        function downloadInactiveUsers() {{
            const csv = [
                ['User Principal Name', 'License Type', 'Monthly Cost', 'Last Sign-In', 'Days Inactive'],
                ...data.inactive_users.map(user => [
                    user.user_principal_name,
                    user.sku_name,
                    user.monthly_cost,
                    user.last_sign_in_date || 'Never',
                    user.days_inactive === 9999 ? 'Never' : user.days_inactive
                ])
            ].map(row => row.join(',')).join('\\n');

            const blob = new Blob([csv], {{ type: 'text/csv' }});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'inactive_users.csv';
            a.click();
            URL.revokeObjectURL(url);
        }}

        // Pricing management
        let pricingEdits = {{}};
        let isEditingPricing = false;

        function renderPricing() {{
            const html = `
                <h3>License Pricing</h3>
                <p style="color: #4C566A; margin-bottom: 2rem;">Manage monthly costs for each SKU</p>

                <div style="margin-bottom: 2rem;">
                    <button id="editPricingBtn" class="download-btn" onclick="togglePricingEdit()">
                        Edit Prices
                    </button>
                    <button id="resetPricingBtn" class="download-btn" onclick="resetPricing()" style="display: none; background: #D08770; margin-left: 1rem;">
                        Reset Changes
                    </button>
                    <button id="exportSqlBtn" class="download-btn" onclick="exportPricingSQL()" style="display: none; background: #A3BE8C; margin-left: 1rem;">
                        Export SQL
                    </button>
                    <a href="#" class="download-btn" onclick="downloadPricingCSV(); return false;" style="margin-left: 1rem;">
                        Download CSV
                    </a>
                </div>

                <table id="pricingTable">
                    <thead>
                        <tr>
                            <th>SKU Name</th>
                            <th>SKU ID</th>
                            <th style="text-align: right;">Monthly Cost</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${{data.pricing.map(item => `
                            <tr data-sku-id="${{item.sku_id}}">
                                <td>${{item.sku_name}}</td>
                                <td style="font-family: 'Monaco', 'Courier New', monospace; font-size: 0.9em; color: #4C566A;">${{item.sku_id}}</td>
                                <td style="text-align: right;">
                                    <span class="price-display">${{formatCurrency(item.monthly_cost)}}</span>
                                    <input
                                        type="number"
                                        step="0.01"
                                        min="0"
                                        class="price-input"
                                        value="${{item.monthly_cost}}"
                                        data-sku-id="${{item.sku_id}}"
                                        data-sku-name="${{item.sku_name}}"
                                        data-original="${{item.monthly_cost}}"
                                        style="display: none; width: 100px; padding: 0.5rem; border: 1px solid #D8DEE9; border-radius: 4px;"
                                    />
                                </td>
                            </tr>
                        `).join('')}}
                    </tbody>
                </table>

                <div id="pricingChangeSummary" style="display: none; margin-top: 2rem; padding: 1.5rem; background: #EBCB8B20; border-left: 3px solid #EBCB8B; border-radius: 4px;">
                    <h4 style="margin-bottom: 1rem;">Pending Changes</h4>
                    <ul id="changesList" style="list-style: none; margin: 0;"></ul>
                </div>
            `;

            document.getElementById('pricing').innerHTML = html;
        }}

        function togglePricingEdit() {{
            isEditingPricing = !isEditingPricing;
            const editBtn = document.getElementById('editPricingBtn');
            const resetBtn = document.getElementById('resetPricingBtn');
            const exportBtn = document.getElementById('exportSqlBtn');
            const displays = document.querySelectorAll('.price-display');
            const inputs = document.querySelectorAll('.price-input');

            if (isEditingPricing) {{
                editBtn.textContent = 'Save Changes';
                editBtn.style.background = '#A3BE8C';
                resetBtn.style.display = 'inline-block';
                displays.forEach(d => d.style.display = 'none');
                inputs.forEach(i => {{
                    i.style.display = 'inline-block';
                    i.addEventListener('input', trackPricingChange);
                }});
            }} else {{
                editBtn.textContent = 'Edit Prices';
                editBtn.style.background = '#5E81AC';
                resetBtn.style.display = 'none';
                if (Object.keys(pricingEdits).length > 0) {{
                    exportBtn.style.display = 'inline-block';
                }}
                displays.forEach(d => d.style.display = 'inline');
                inputs.forEach(i => i.style.display = 'none');
                updatePricingDisplays();
            }}
        }}

        function trackPricingChange(event) {{
            const input = event.target;
            const skuId = input.dataset.skuId;
            const skuName = input.dataset.skuName;
            const originalPrice = parseFloat(input.dataset.original);
            const newPrice = parseFloat(input.value);

            if (newPrice !== originalPrice) {{
                pricingEdits[skuId] = {{
                    sku_id: skuId,
                    sku_name: skuName,
                    monthly_cost: newPrice,
                    original_cost: originalPrice
                }};
            }} else {{
                delete pricingEdits[skuId];
            }}

            updateChangeSummary();
        }}

        function updateChangeSummary() {{
            const summary = document.getElementById('pricingChangeSummary');
            const changesList = document.getElementById('changesList');
            const changes = Object.values(pricingEdits);

            if (changes.length === 0) {{
                summary.style.display = 'none';
                return;
            }}

            summary.style.display = 'block';
            changesList.innerHTML = changes.map(change => `
                <li style="padding: 0.5rem 0; color: #4C566A;">
                    <strong>${{change.sku_name}}</strong>:
                    ${{formatCurrency(change.original_cost)}} → ${{formatCurrency(change.monthly_cost)}}
                </li>
            `).join('');
        }}

        function updatePricingDisplays() {{
            Object.values(pricingEdits).forEach(edit => {{
                const row = document.querySelector(`tr[data-sku-id="${{edit.sku_id}}"]`);
                if (row) {{
                    const display = row.querySelector('.price-display');
                    display.textContent = formatCurrency(edit.monthly_cost);
                    display.style.color = '#5E81AC';
                    display.style.fontWeight = '600';
                }}
            }});
        }}

        function resetPricing() {{
            if (!confirm('Discard all pricing changes?')) return;

            pricingEdits = {{}};
            isEditingPricing = false;
            document.getElementById('exportSqlBtn').style.display = 'none';
            renderPricing();
        }}

        function exportPricingSQL() {{
            const changes = Object.values(pricingEdits);
            if (changes.length === 0) {{
                alert('No pricing changes to export.');
                return;
            }}

            let sql = '-- Pricing updates generated by M365 Cost Management Dashboard\\n';
            sql += '-- Run these statements to update the database\\n\\n';

            changes.forEach(change => {{
                sql += `-- Update pricing for ${{change.sku_name}}\\n`;
                sql += `UPDATE price_lookup\\n`;
                sql += `SET monthly_cost = ${{change.monthly_cost}}\\n`;
                sql += `WHERE sku_id = '${{change.sku_id}}';\\n\\n`;
            }});

            const blob = new Blob([sql], {{ type: 'text/plain' }});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'm365_pricing_updates.sql';
            a.click();
            URL.revokeObjectURL(url);
        }}

        function downloadPricingCSV() {{
            // Use current pricing including any edits
            const currentPricing = data.pricing.map(item => {{
                const edit = pricingEdits[item.sku_id];
                return {{
                    sku_id: item.sku_id,
                    sku_name: item.sku_name,
                    monthly_cost: edit ? edit.monthly_cost : item.monthly_cost
                }};
            }});

            const csv = [
                ['SKU Name', 'SKU ID', 'Monthly Cost'],
                ...currentPricing.map(item => [
                    item.sku_name,
                    item.sku_id,
                    item.monthly_cost
                ])
            ].map(row => row.join(',')).join('\\n');

            const blob = new Blob([csv], {{ type: 'text/csv' }});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'm365_pricing.csv';
            a.click();
            URL.revokeObjectURL(url);
        }}

        // Initialize dashboard
        renderStatusBanner();
        renderOverview();
        renderInactive();
        renderUtilization();
        renderActions();
        renderPricing();
        renderCollection();
    </script>
</body>
</html>
"""

    with open(output_path, 'w') as f:
        f.write(html)

    print(f"Dashboard generated: {output_path}")


def main():
    load_dotenv()

    db_path = os.getenv('DATABASE_PATH', './data/m365_costs.db')
    output_path = os.getenv('DASHBOARD_OUTPUT', './m365_dashboard.html')
    inactive_days = int(os.getenv('INACTIVE_DAYS', '90'))

    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        print("Run collect_m365_data.py first to collect data.")
        sys.exit(1)

    print(f"Generating dashboard from {db_path}...")
    data = get_dashboard_data(db_path, inactive_days)
    generate_html(data, output_path)


if __name__ == '__main__':
    main()
