# M365 Cost Management Examples

## Quick Start

### Run Complete Analysis
```bash
# 1. Collect data from M365 tenant
uv run python scripts/collect_m365_data.py

# 2. Generate dashboard
uv run python scripts/generate_dashboard.py

# 3. Open in browser
open m365_dashboard.html
```

## Common Workflows

### Quarterly Cost Review
```bash
# Collect latest data
uv run python scripts/collect_m365_data.py

# Generate dashboard
uv run python scripts/generate_dashboard.py

# Review dashboard in browser
open m365_dashboard.html

# Download inactive users CSV
# (Click "Download user list" button in Inactive Users tab)

# Present findings to leadership
# - Open Actions tab for talking points
# - Note percentage savings opportunity
# - Use specific recommendations with dollar amounts
```

### Budget Reduction Initiative
```bash
# Set custom inactivity threshold (default 90 days)
export INACTIVE_DAYS=60
uv run python scripts/generate_dashboard.py

# Review more aggressive targets
open m365_dashboard.html

# Export specific user list for review
# Use downloaded CSV to coordinate with HR
```

### Monthly License Audit
```bash
# Check for new unassigned licenses
uv run python scripts/collect_m365_data.py
uv run python scripts/generate_dashboard.py

# Open Utilization tab
# - Review unassigned licenses
# - Calculate monthly waste
# - Reduce license counts in M365 admin center
```

## Data Collection

### Basic Collection
```python
# scripts/collect_m365_data.py
"""
Collect M365 license and usage data via Graph API.

Requires .env file:
TENANT_ID=your-tenant-id
CLIENT_ID=your-app-client-id
CLIENT_SECRET=your-app-secret
DATABASE_PATH=./data/m365_costs.db
"""

# Expected workflow:
# 1. Authenticate to Graph API
# 2. Fetch license data (/subscribedSkus endpoint)
# 3. Fetch user activity (/users?$select=signInActivity)
# 4. Look up pricing data
# 5. Store in SQLite database
```

### Authentication Setup
```python
# Example Graph API authentication (MSAL)
from msal import ConfidentialClientApplication
import os

tenant_id = os.getenv('TENANT_ID')
client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')

app = ConfidentialClientApplication(
    client_id,
    authority=f"https://login.microsoftonline.com/{tenant_id}",
    client_credential=client_secret
)

# Get access token
result = app.acquire_token_for_client(
    scopes=["https://graph.microsoft.com/.default"]
)

if "access_token" in result:
    token = result["access_token"]
    # Use token for Graph API requests
```

## Dashboard Customization

### Custom Inactivity Threshold
```bash
# Check 60-day inactive users instead of 90
export INACTIVE_DAYS=60
uv run python scripts/generate_dashboard.py
```

### Custom Database Location
```bash
# Use different database
export DATABASE_PATH=/path/to/m365_data.db
uv run python scripts/generate_dashboard.py
```

### Custom Output Path
```bash
# Save dashboard to specific location
export DASHBOARD_OUTPUT=/path/to/output/dashboard.html
uv run python scripts/generate_dashboard.py
```

## Database Queries

### Check Latest Collection
```bash
sqlite3 data/m365_costs.db "
SELECT
    id,
    timestamp,
    status
FROM collection_runs
ORDER BY timestamp DESC
LIMIT 5
"
```

### Top 10 Costliest Licenses
```bash
sqlite3 data/m365_costs.db "
SELECT
    l.sku_name,
    l.total_licenses,
    p.monthly_cost,
    (l.assigned_licenses * p.monthly_cost) as total_cost
FROM licenses l
INNER JOIN price_lookup p ON l.sku_id = p.sku_id
WHERE l.collection_run_id = (
    SELECT id FROM collection_runs
    WHERE status = 'completed'
    ORDER BY timestamp DESC
    LIMIT 1
)
ORDER BY total_cost DESC
LIMIT 10
"
```

### Inactive Users by License Type
```bash
sqlite3 data/m365_costs.db "
SELECT
    p.sku_name,
    COUNT(DISTINCT ul.user_principal_name) as inactive_count,
    (COUNT(DISTINCT ul.user_principal_name) * p.monthly_cost) as monthly_cost
FROM user_licenses ul
INNER JOIN user_activity ua
    ON ul.user_principal_name = ua.user_principal_name
INNER JOIN price_lookup p ON ul.sku_id = p.sku_id
WHERE ua.last_sign_in_date < datetime('now', '-90 days')
   OR ua.last_sign_in_date IS NULL
GROUP BY p.sku_name, p.monthly_cost
ORDER BY monthly_cost DESC
"
```

## Programmatic Dashboard Access

### Extract Savings Data
```python
import json
from bs4 import BeautifulSoup

# Read generated dashboard
with open('m365_dashboard.html', 'r') as f:
    html = f.read()

# Extract embedded data
soup = BeautifulSoup(html, 'html.parser')
script = soup.find('script', text=lambda t: 'const data =' in t if t else False)

# Parse data object (between 'const data = ' and ';')
data_json = script.string.split('const data = ')[1].split(';')[0]
data = json.loads(data_json)

# Access insights
print(f"Total monthly cost: ${data['costs']['total_monthly']:,.2f}")
print(f"Total licenses: {data['costs']['total_licenses']}")
print(f"Inactive users: {len(data['inactive_users'])}")

# Calculate potential savings
inactive_savings = sum(item['total_monthly_cost'] for item in data['inactive_summary'])
print(f"Potential monthly savings: ${inactive_savings:,.2f}")
```

## Integration Examples

### Slack Notification
```python
import requests
import json

# After generating dashboard, extract key metrics
with open('m365_dashboard.html', 'r') as f:
    html = f.read()

# Extract data (as shown above)
# ...

# Post to Slack
webhook_url = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
message = {
    "text": f"M365 Cost Analysis Complete",
    "blocks": [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*M365 License Analysis*\n\n"
                       f"• Monthly spend: ${data['costs']['total_monthly']:,.2f}\n"
                       f"• Inactive users: {len(data['inactive_users'])}\n"
                       f"• Potential savings: {savings_pct}%"
            }
        }
    ]
}

requests.post(webhook_url, json=message)
```

### CSV Export for Leadership
```python
import pandas as pd
import sqlite3

# Connect to database
conn = sqlite3.connect('data/m365_costs.db')

# Get latest run
cursor = conn.cursor()
cursor.execute("""
    SELECT id FROM collection_runs
    WHERE status = 'completed'
    ORDER BY timestamp DESC
    LIMIT 1
""")
run_id = cursor.fetchone()[0]

# Export summary for executives
query = f"""
SELECT
    l.sku_name as "License Type",
    l.total_licenses as "Total Purchased",
    l.assigned_licenses as "Assigned",
    l.available_licenses as "Unassigned",
    p.monthly_cost as "Cost per License",
    (l.assigned_licenses * p.monthly_cost) as "Monthly Cost",
    ROUND(100.0 * l.assigned_licenses / l.total_licenses, 1) as "Utilization %"
FROM licenses l
INNER JOIN price_lookup p ON l.sku_id = p.sku_id
WHERE l.collection_run_id = {run_id}
ORDER BY (l.assigned_licenses * p.monthly_cost) DESC
"""

df = pd.read_sql_query(query, conn)
df.to_excel('m365_executive_summary.xlsx', index=False)
conn.close()

print("Executive summary exported to m365_executive_summary.xlsx")
```

## Error Handling

### Handle Missing Data
```python
import os
import sys

db_path = os.getenv("DATABASE_PATH", "./data/m365_costs.db")

if not os.path.exists(db_path):
    print(f"Error: Database not found at {db_path}")
    print("Run collect_m365_data.py first to collect data.")
    sys.exit(1)

# Check for completed runs
import sqlite3
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM collection_runs WHERE status = 'completed'")
count = cursor.fetchone()[0]

if count == 0:
    print("No completed data collection found.")
    print("Run collect_m365_data.py and ensure it completes successfully.")
    sys.exit(1)
```

## See Also

- [SKILL.md](SKILL.md) - Complete skill reference
- [README.md](README.md) - Installation and setup
- [reference.md](reference.md) - Graph API details and troubleshooting
