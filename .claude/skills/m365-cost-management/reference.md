# M365 Cost Management Advanced Reference

This document contains detailed technical information about Microsoft Graph API integration, database schema, troubleshooting, and advanced usage patterns.

## Microsoft Graph API

### Authentication Flow

#### MSAL Client Credentials Flow
```python
from msal import ConfidentialClientApplication
import os

# Initialize MSAL app
tenant_id = os.getenv('TENANT_ID')
client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')

app = ConfidentialClientApplication(
    client_id,
    authority=f"https://login.microsoftonline.com/{tenant_id}",
    client_credential=client_secret
)

# Acquire token
result = app.acquire_token_for_client(
    scopes=["https://graph.microsoft.com/.default"]
)

if "access_token" in result:
    access_token = result["access_token"]
else:
    error = result.get("error")
    error_description = result.get("error_description")
    print(f"Authentication failed: {error} - {error_description}")
```

#### Token Caching
```python
# MSAL automatically caches tokens
# Token is valid for 1 hour
# MSAL will refresh automatically on next call

# Check token expiration
import time
expires_in = result.get('expires_in', 3600)
token_expires_at = time.time() + expires_in
print(f"Token expires in {expires_in} seconds")
```

### Graph API Endpoints

#### Get Subscribed SKUs
```python
import requests

headers = {
    'Authorization': f'Bearer {access_token}',
    'Content-Type': 'application/json'
}

# Get all subscribed SKUs
response = requests.get(
    'https://graph.microsoft.com/v1.0/subscribedSkus',
    headers=headers
)

if response.status_code == 200:
    skus = response.json()['value']
    for sku in skus:
        print(f"SKU: {sku['skuPartNumber']}")
        print(f"  Total: {sku['prepaidUnits']['enabled']}")
        print(f"  Consumed: {sku['consumedUnits']}")
        print(f"  Available: {sku['prepaidUnits']['enabled'] - sku['consumedUnits']}")
```

#### Get User Sign-In Activity
```python
# Requires Azure AD Premium P1/P2 license
# signInActivity is only available with specific permissions

response = requests.get(
    'https://graph.microsoft.com/v1.0/users',
    headers=headers,
    params={
        '$select': 'userPrincipalName,signInActivity',
        '$top': 999  # Max per page
    }
)

if response.status_code == 200:
    users = response.json()['value']
    for user in users:
        upn = user['userPrincipalName']
        sign_in = user.get('signInActivity', {})
        last_sign_in = sign_in.get('lastSignInDateTime')
        print(f"{upn}: {last_sign_in or 'Never'}")
```

#### Get User License Assignments
```python
# Get specific user's licenses
user_upn = "user@contoso.com"

response = requests.get(
    f'https://graph.microsoft.com/v1.0/users/{user_upn}/licenseDetails',
    headers=headers
)

if response.status_code == 200:
    licenses = response.json()['value']
    for license in licenses:
        print(f"License: {license['skuPartNumber']}")
        print(f"SKU ID: {license['skuId']}")
```

#### Pagination Handling
```python
def get_all_users(access_token):
    """Fetch all users with pagination."""
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    all_users = []
    url = 'https://graph.microsoft.com/v1.0/users'
    params = {'$select': 'userPrincipalName,signInActivity', '$top': 999}

    while url:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()

        data = response.json()
        all_users.extend(data['value'])

        # Get next page URL
        url = data.get('@odata.nextLink')
        params = None  # nextLink includes all params

    return all_users
```

### Rate Limiting

Graph API enforces throttling limits:

**Limits**:
- Service level: 10,000 requests per 10 minutes per app per tenant
- User level: Varies by endpoint (typically 2,000-10,000 requests per 10 minutes)

**Handling throttling**:
```python
import time

def make_graph_request(url, headers, max_retries=3):
    """Make Graph API request with retry logic."""
    for attempt in range(max_retries):
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            return response.json()

        elif response.status_code == 429:
            # Rate limited
            retry_after = int(response.headers.get('Retry-After', 60))
            print(f"Rate limited. Retrying after {retry_after} seconds...")
            time.sleep(retry_after)

        elif response.status_code >= 500:
            # Server error - retry with backoff
            wait = 2 ** attempt
            print(f"Server error. Retrying in {wait} seconds...")
            time.sleep(wait)

        else:
            # Other error - raise
            response.raise_for_status()

    raise Exception(f"Failed after {max_retries} retries")
```

## Price Lookup Data

### Manual Price Table

Microsoft doesn't provide a public API for license pricing. Prices must be maintained manually.

**Create price lookup table**:
```sql
CREATE TABLE IF NOT EXISTS price_lookup (
    sku_id TEXT PRIMARY KEY,
    sku_name TEXT NOT NULL,
    monthly_cost REAL NOT NULL,
    last_updated TEXT NOT NULL
);

-- Insert sample prices (update with your actual pricing)
INSERT OR REPLACE INTO price_lookup VALUES
('6fd2c87f-b296-42f0-b197-1e91e994b900', 'Office 365 E3', 23.00, '2024-01-01'),
('c7df2760-2c81-4ef7-b578-5b5392b571df', 'Office 365 E5', 38.00, '2024-01-01'),
('18181a46-0d4e-45cd-891e-60aabd171b4e', 'Microsoft 365 E3', 36.00, '2024-01-01'),
('26d45bd9-adf1-46cd-a9e1-51e9a5524128', 'Power BI Pro', 9.99, '2024-01-01'),
('f30db892-07e9-47e9-837c-80727f46fd3d', 'Microsoft Flow Free', 0.00, '2024-01-01');
```

### Automated Price Updates

**Option 1: Web Scraping** (requires maintenance)
```python
# Scrape Microsoft pricing pages
# WARNING: Fragile - Microsoft changes page structure frequently
import requests
from bs4 import BeautifulSoup

def scrape_m365_pricing():
    """
    Scrape pricing from Microsoft's official pricing page.
    Note: This is brittle and will break when Microsoft changes their site.
    """
    url = "https://www.microsoft.com/en-us/microsoft-365/enterprise/office-365-pricing"
    # Implementation depends on current page structure
    pass
```

**Option 2: Azure Cost Management API** (requires Azure subscription)
```python
# Use Azure Cost Management API to get actual costs
# Requires Azure subscription and cost data
```

**Option 3: Manual CSV Import**
```python
import csv
import sqlite3

def import_pricing_csv(csv_path, db_path):
    """Import pricing from CSV file."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            cursor.execute("""
                INSERT OR REPLACE INTO price_lookup
                (sku_id, sku_name, monthly_cost, last_updated)
                VALUES (?, ?, ?, datetime('now'))
            """, (row['sku_id'], row['sku_name'], float(row['monthly_cost'])))

    conn.commit()
    conn.close()
```

## Database Schema Details

### Complete Schema with Indexes

```sql
-- Collection runs
CREATE TABLE IF NOT EXISTS collection_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL DEFAULT (datetime('now')),
    status TEXT NOT NULL CHECK(status IN ('completed', 'failed', 'running')),
    error_message TEXT,
    records_collected INTEGER
);

CREATE INDEX idx_collection_runs_timestamp ON collection_runs(timestamp DESC);
CREATE INDEX idx_collection_runs_status ON collection_runs(status);

-- Licenses
CREATE TABLE IF NOT EXISTS licenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    collection_run_id INTEGER NOT NULL,
    sku_id TEXT NOT NULL,
    sku_name TEXT NOT NULL,
    total_licenses INTEGER NOT NULL,
    assigned_licenses INTEGER NOT NULL,
    available_licenses INTEGER NOT NULL,
    FOREIGN KEY (collection_run_id) REFERENCES collection_runs(id)
);

CREATE INDEX idx_licenses_run ON licenses(collection_run_id);
CREATE INDEX idx_licenses_sku ON licenses(sku_id);

-- Price lookup
CREATE TABLE IF NOT EXISTS price_lookup (
    sku_id TEXT PRIMARY KEY,
    sku_name TEXT NOT NULL,
    monthly_cost REAL NOT NULL CHECK(monthly_cost >= 0),
    last_updated TEXT NOT NULL DEFAULT (datetime('now'))
);

-- User licenses
CREATE TABLE IF NOT EXISTS user_licenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    collection_run_id INTEGER NOT NULL,
    user_principal_name TEXT NOT NULL,
    sku_id TEXT NOT NULL,
    FOREIGN KEY (collection_run_id) REFERENCES collection_runs(id),
    UNIQUE(collection_run_id, user_principal_name, sku_id)
);

CREATE INDEX idx_user_licenses_run ON user_licenses(collection_run_id);
CREATE INDEX idx_user_licenses_user ON user_licenses(user_principal_name);
CREATE INDEX idx_user_licenses_sku ON user_licenses(sku_id);

-- User activity
CREATE TABLE IF NOT EXISTS user_activity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    collection_run_id INTEGER NOT NULL,
    user_principal_name TEXT NOT NULL,
    last_sign_in_date TEXT,
    FOREIGN KEY (collection_run_id) REFERENCES collection_runs(id),
    UNIQUE(collection_run_id, user_principal_name)
);

CREATE INDEX idx_user_activity_run ON user_activity(collection_run_id);
CREATE INDEX idx_user_activity_user ON user_activity(user_principal_name);
CREATE INDEX idx_user_activity_date ON user_activity(last_sign_in_date);
```

### Advanced Queries

#### Cost Trend Analysis
```sql
-- Compare costs across multiple collection runs
SELECT
    cr.timestamp,
    SUM(l.assigned_licenses * p.monthly_cost) as total_monthly_cost,
    COUNT(DISTINCT l.sku_id) as unique_skus,
    SUM(l.total_licenses) as total_licenses
FROM collection_runs cr
INNER JOIN licenses l ON cr.id = l.collection_run_id
INNER JOIN price_lookup p ON l.sku_id = p.sku_id
WHERE cr.status = 'completed'
GROUP BY cr.id, cr.timestamp
ORDER BY cr.timestamp DESC;
```

#### User License Stacking
```sql
-- Find users with multiple licenses
SELECT
    ul.user_principal_name,
    GROUP_CONCAT(p.sku_name, ', ') as licenses,
    COUNT(*) as license_count,
    SUM(p.monthly_cost) as total_monthly_cost
FROM user_licenses ul
INNER JOIN price_lookup p ON ul.sku_id = p.sku_id
WHERE ul.collection_run_id = (
    SELECT id FROM collection_runs
    WHERE status = 'completed'
    ORDER BY timestamp DESC
    LIMIT 1
)
GROUP BY ul.user_principal_name
HAVING COUNT(*) > 1
ORDER BY total_monthly_cost DESC;
```

#### License Utilization Over Time
```sql
-- Track utilization changes
SELECT
    cr.timestamp,
    l.sku_name,
    l.total_licenses,
    l.assigned_licenses,
    l.available_licenses,
    ROUND(100.0 * l.assigned_licenses / l.total_licenses, 1) as utilization_pct
FROM collection_runs cr
INNER JOIN licenses l ON cr.id = l.collection_run_id
WHERE l.sku_id = 'TARGET_SKU_ID'
  AND cr.status = 'completed'
ORDER BY cr.timestamp DESC;
```

## Error Handling

### Common Errors

#### Authentication Errors

**AADSTS700016**: Application not found
```
Cause: CLIENT_ID doesn't exist or is from wrong tenant
Fix: Verify CLIENT_ID in Azure Portal → App registrations
```

**AADSTS7000215**: Invalid client secret
```
Cause: Client secret expired or incorrect
Fix: Generate new secret in Azure Portal
     Update .env file with new secret
```

**AADSTS650057**: Invalid resource
```
Cause: Incorrect scope in token request
Fix: Use scope "https://graph.microsoft.com/.default"
```

#### Permission Errors

**Insufficient privileges**
```
Cause: Missing API permissions or admin consent not granted
Fix: 1. Go to Azure Portal → App registrations → Your app
     2. API permissions → Add required permissions
     3. Click "Grant admin consent for [Tenant]"
     4. Wait 5-10 minutes for propagation
```

**Required permissions**:
- `Organization.Read.All` (Application)
- `User.Read.All` (Application)
- `Directory.Read.All` (Application)

#### Graph API Errors

**404 Not Found**
```python
# User doesn't exist or not accessible
try:
    response = requests.get(f'https://graph.microsoft.com/v1.0/users/{upn}', headers=headers)
    response.raise_for_status()
except requests.HTTPError as e:
    if e.response.status_code == 404:
        print(f"User {upn} not found or not accessible")
```

**429 Too Many Requests**
```python
# Rate limited - implement exponential backoff
retry_after = int(response.headers.get('Retry-After', 60))
time.sleep(retry_after)
```

### Database Errors

**Database locked**
```python
# SQLite can't handle concurrent writes
# Use transaction and immediate lock
import sqlite3

conn = sqlite3.connect('data/m365_costs.db', timeout=30.0)
conn.execute('BEGIN IMMEDIATE')
try:
    # Your database operations
    conn.commit()
except Exception:
    conn.rollback()
    raise
finally:
    conn.close()
```

**Foreign key constraint failed**
```sql
-- Ensure foreign keys are enabled
PRAGMA foreign_keys = ON;

-- Check orphaned records
SELECT * FROM licenses
WHERE collection_run_id NOT IN (SELECT id FROM collection_runs);
```

## Performance Optimization

### Batch Inserts
```python
def bulk_insert_user_licenses(conn, run_id, user_licenses):
    """Efficiently insert thousands of user license records."""
    cursor = conn.cursor()

    # Prepare data
    data = [
        (run_id, user_upn, sku_id)
        for user_upn, sku_id in user_licenses
    ]

    # Batch insert
    cursor.executemany("""
        INSERT OR IGNORE INTO user_licenses
        (collection_run_id, user_principal_name, sku_id)
        VALUES (?, ?, ?)
    """, data)

    conn.commit()
```

### Query Optimization
```sql
-- Use EXPLAIN QUERY PLAN to analyze queries
EXPLAIN QUERY PLAN
SELECT
    ul.user_principal_name,
    COUNT(*) as license_count
FROM user_licenses ul
WHERE ul.collection_run_id = 123
GROUP BY ul.user_principal_name;

-- Add covering index if needed
CREATE INDEX idx_user_licenses_covering
ON user_licenses(collection_run_id, user_principal_name);
```

## Troubleshooting

### Sign-In Activity Not Available

**Issue**: `signInActivity` returns null for all users

**Causes**:
1. Tenant doesn't have Azure AD Premium P1/P2
2. Feature not enabled in tenant
3. Insufficient permissions

**Workaround**: Use last mailbox activity from Exchange
```python
# Alternative: Get last email activity
response = requests.get(
    f'https://graph.microsoft.com/v1.0/reports/getEmailActivityUserDetail(period=\'D90\')',
    headers=headers
)
```

### Missing Price Data

**Issue**: SKUs without pricing in price_lookup table

**Solution**: Find unpriced SKUs
```sql
SELECT DISTINCT l.sku_id, l.sku_name
FROM licenses l
LEFT JOIN price_lookup p ON l.sku_id = p.sku_id
WHERE p.sku_id IS NULL;
```

Then manually add pricing or set to 0:
```sql
INSERT INTO price_lookup (sku_id, sku_name, monthly_cost)
VALUES ('unknown-sku-id', 'Unknown License', 0.00);
```

## See Also

- [SKILL.md](SKILL.md) - Quick reference
- [examples.md](examples.md) - Usage examples
- [README.md](README.md) - Installation guide
- [Microsoft Graph API Documentation](https://learn.microsoft.com/en-us/graph/)
- [MSAL Python Documentation](https://msal-python.readthedocs.io/)
