# Microsoft 365 Cost Management Skill

Analyze M365 license costs, identify savings opportunities, and generate actionable recommendations.

## Features

- **License Analysis**: Track all M365 SKUs and their costs
- **Inactive User Detection**: Find users with 90+ days no sign-in
- **Utilization Tracking**: Identify unassigned licenses
- **Cost Projections**: Calculate monthly and annual savings potential
- **ADP Integration**: Cross-reference M365 users with HR data to identify orphaned licenses
- **Interactive Dashboard**: Beautiful HTML dashboard with visualizations
- **CSV Export**: Download user lists for review
- **Recommendations**: Prioritized action items with dollar impact

## Installation

### Prerequisites

- Python 3.10+
- uv package manager
- Microsoft 365 tenant admin access
- Azure AD app registration (for data collection)

### Install Dependencies

```bash
cd ~/.claude/skills/m365-cost-management
uv sync
```

### Azure AD Setup (Required for Data Collection)

1. **Register Azure AD Application**:
   - Go to [Azure Portal](https://portal.azure.com)
   - Navigate to Azure Active Directory → App registrations
   - Click "New registration"
   - Name: "M365 Cost Management"
   - Supported account types: "Accounts in this organizational directory only"
   - Click "Register"

2. **Configure API Permissions**:
   - In your app, go to "API permissions"
   - Add permissions:
     - `Organization.Read.All` (Application)
     - `User.Read.All` (Application)
     - `Directory.Read.All` (Application)
   - Click "Grant admin consent"

3. **Create Client Secret**:
   - Go to "Certificates & secrets"
   - Click "New client secret"
   - Description: "M365 Cost Tool"
   - Expires: Choose appropriate duration
   - Copy the secret value (you won't see it again)

4. **Configure .env File**:
```bash
# Create .env in skill directory
cat > .env <<EOF
TENANT_ID=your-tenant-id-here
CLIENT_ID=your-app-client-id-here
CLIENT_SECRET=your-client-secret-here
DATABASE_PATH=./data/m365_costs.db
DASHBOARD_OUTPUT=./m365_dashboard.html
INACTIVE_DAYS=90
EOF
```

Find your tenant ID and client ID in the Azure AD app overview page.

## Quick Start

### 1. Collect Data

```bash
uv run python scripts/collect_m365_data.py
```

This will:
- Authenticate to Microsoft Graph API
- Fetch all subscribed SKUs and license assignments
- Collect user sign-in activity incrementally (written to DB during fetch)
- Create checkpoints for resumability
- Handle rate limiting automatically
- Store everything in SQLite database

**For large tenants (1000+ users):**
- Users are written to database immediately as fetched (no memory accumulation)
- Creates checkpoints after each page (Graph API page size: 999 users)
- Constant memory usage regardless of tenant size
- Can resume if interrupted
- Handles rate limiting with exponential backoff

### 2. Update Pricing (First Time Only)

After first data collection, update the price_lookup table with correct SKU IDs and pricing:

```bash
uv run python scripts/update_pricing.py
```

This script:
- Syncs price_lookup table with actual SKUs from licenses table
- Sets monthly costs based on Microsoft's published pricing
- Handles 40+ common Microsoft 365 SKUs
- Sets unknown SKUs to $0 (update manually via dashboard Pricing tab)

**Note**: Only needed once after initial data collection or when new SKUs appear.

### 3. Import ADP Data (Optional but Recommended)

Cross-reference M365 licenses with HR employee data to identify orphaned licenses:

```bash
uv run python scripts/import_adp_data.py "/path/to/adp_export.xlsx"
```

This will:
- Import employee data from ADP Excel export
- Cross-reference with M365 user data
- Identify orphaned licenses (M365 users not in ADP)
- Find terminated employees with active M365 licenses
- Detect active employees inactive for 90+ days

**Expected ADP Excel columns:**
- Work Contact: Work Email (required)
- Legal Name
- Position Status
- Job Title Description
- Location Description
- Hire Date

**Analysis results shown:**
- Orphaned licenses: M365 users not found in ADP
- Terminated with licenses: Ex-employees still with M365 access
- Inactive active employees: Active employees with no M365 activity

### 4. Generate Dashboard

```bash
uv run python scripts/generate_dashboard.py
```

Creates `m365_dashboard.html` with:
- **Status Banner**: Shows collection completion status (complete/running/failed)
- **Overview**: Total costs and savings potential
- **Inactive Users**: Users with 90+ days no sign-in
- **License Utilization**: Unassigned licenses
- **Actions**: Prioritized recommendations
- **Pricing**: Editable SKU pricing with SQL export
- **Collection Info**: Comprehensive collection metadata, checkpoints, and retry logs
- **ADP Cross-Reference**: Orphaned licenses and HR data comparison (if ADP data imported)

### 5. Review Dashboard

```bash
open m365_dashboard.html
```

Navigate through seven tabs (ADP tab appears only if ADP data imported):
- **Overview**: Hero metric showing potential cost reduction %
- **Inactive Users**: Download CSV of users to review
- **Utilization**: See which licenses are unused
- **Actions**: Specific next steps with savings impact
- **Pricing**: Edit SKU prices, export SQL updates, download pricing CSV
- **Collection Info**: View collection status, progress, checkpoints, and rate limiting details
- **ADP Cross-Reference**: Orphaned licenses, terminated employees with licenses, inactive active employees

## Configuration

All settings use environment variables (or `.env` file):

| Variable | Default | Description |
|----------|---------|-------------|
| `TENANT_ID` | (required) | Azure AD tenant ID |
| `CLIENT_ID` | (required) | App registration client ID |
| `CLIENT_SECRET` | (required) | App client secret |
| `DATABASE_PATH` | `./data/m365_costs.db` | SQLite database location |
| `DASHBOARD_OUTPUT` | `./m365_dashboard.html` | Dashboard output path |
| `INACTIVE_DAYS` | `90` | Days threshold for inactive users |

**Note**: `BATCH_SIZE` is no longer used. The script now uses Graph API's maximum page size (999 users) and writes to database incrementally during fetch with constant memory usage.

## Incremental Collection & Recovery

### How It Works

The data collection process is designed for resilience with large tenants:

1. **Incremental Writes**: Users are written to database immediately as pages are fetched
2. **Constant Memory**: No accumulation in memory - processes Graph API pages (999 users) one at a time
3. **Checkpoints**: After each page, progress is saved to database for resumability
4. **Rate Limiting**: Automatically detects and handles 429 responses with exponential backoff
5. **Progress Tracking**: Real-time status updates throughout collection

### Recovery from Interruptions

If collection is interrupted (Ctrl+C, network issue, rate limit), simply re-run:

```bash
uv run python scripts/collect_m365_data.py
```

The script will:
- Detect the incomplete run
- Resume from the last checkpoint
- Continue where it left off
- Complete the collection

### Monitoring Progress

Check collection status in the database:

```sql
-- View latest collection run
SELECT * FROM collection_runs ORDER BY id DESC LIMIT 1;

-- View progress checkpoints
SELECT * FROM collection_checkpoints
WHERE collection_run_id = (SELECT MAX(id) FROM collection_runs);

-- View retry attempts (rate limiting)
SELECT * FROM retry_log
WHERE collection_run_id = (SELECT MAX(id) FROM collection_runs);
```

### Handling Rate Limits

If you hit rate limits frequently:

1. **Automatic Retry**: Script automatically retries with exponential backoff (1s, 2s, 4s, 8s, 16s)
2. **Respects Retry-After**: Uses Retry-After header from Graph API when available
3. **All Retries Logged**: Check retry_log table to monitor rate limiting patterns
4. **Checkpoints Preserve Progress**: Resume from last successful page after interruption

## Tools

### collect_m365_data.py

Collects data from Microsoft Graph API.

**Endpoints used**:
- `/subscribedSkus` - License inventory
- `/users?$select=signInActivity` - User activity
- Price lookup from configuration

**Output**: SQLite database with schema:
- `collection_runs` - Run metadata
- `licenses` - License inventory
- `price_lookup` - SKU pricing
- `user_licenses` - User assignments
- `user_activity` - Sign-in dates

### update_pricing.py

Syncs price_lookup table with actual SKU IDs and sets correct monthly costs.

**Purpose**:
- Fixes SKU ID mismatches between licenses and price_lookup tables
- Applies Microsoft's published pricing to 40+ common SKUs
- Required after initial data collection

**Pricing includes**:
- Microsoft 365 Enterprise (E3, E5, F3)
- Microsoft 365 Business (Basic, Standard, Premium)
- Exchange, SharePoint, Teams plans
- Power Platform (Power BI, Power Automate, Power Apps)
- Project, Visio, Dynamics 365
- Security & Compliance (Azure AD, Intune, EMS)
- Microsoft 365 Copilot

**Unknown SKUs**: Set to $0.00 (update manually via dashboard Pricing tab)

### import_adp_data.py

Imports ADP employee data and cross-references with M365 licenses.

**Purpose**:
- Import employee data from ADP Excel export
- Cross-reference with M365 user data
- Identify orphaned licenses (M365 users not in ADP)
- Find terminated employees with active M365 licenses
- Detect active employees with no M365 activity

**Expected Excel columns**:
- Work Contact: Work Email (required for matching)
- Legal Name
- Position Status (Active/Terminated)
- Job Title Description
- Location Description
- Hire Date

**Matching logic**:
- Compares ADP work_email with M365 user_principal_name (case-insensitive)
- TODO: Enhance to check M365 email aliases/proxyAddresses

**Output**:
- Populates `adp_employees` table in database
- Displays cross-reference summary in console
- Shows in ADP Cross-Reference tab in dashboard

### generate_dashboard.py

Creates static HTML dashboard from database.

**Design principles**:
- Jony Ive minimalism
- Edward Tufte data density
- Nord frost color palette
- Self-contained (no external dependencies)

**Features**:
- **Status Banner**: Displays collection status (complete/running/failed) with color-coded warnings
- **Pricing Tab**: Editable license pricing management
  - View all SKUs with current monthly costs
  - In-browser editing of prices
  - Real-time change tracking with summary
  - Export SQL UPDATE statements for database
  - Download pricing as CSV
  - Reset/discard changes before export
- **Collection Info Tab**: Shows comprehensive metadata including:
  - Collection run ID, timestamp, and status
  - Total users and licenses collected
  - Progress tracking (phase, progress, percentage)
  - Recent checkpoints (last 10)
  - Rate limiting and retry attempts
  - Error messages if collection failed
- **Cost Analysis**: Overview, inactive users, and utilization tabs with interactive charts
- **CSV Export**: Download inactive user lists and pricing data for review

## Database Schema

### collection_runs
- `id` (INTEGER PRIMARY KEY)
- `timestamp` (TEXT)
- `status` (TEXT: 'completed', 'running', 'failed')
- `records_collected` (INTEGER)
- `error_message` (TEXT)

### collection_checkpoints
- `id` (INTEGER PRIMARY KEY)
- `collection_run_id` (INTEGER)
- `timestamp` (TEXT)
- `phase` (TEXT: 'user_activity', 'licenses', etc.)
- `progress` (INTEGER)
- `total` (INTEGER)
- `details` (TEXT)

### collection_progress
- `id` (INTEGER PRIMARY KEY)
- `collection_run_id` (INTEGER)
- `timestamp` (TEXT)
- `phase` (TEXT)
- `progress` (INTEGER)
- `total` (INTEGER)
- `message` (TEXT)

### retry_log
- `id` (INTEGER PRIMARY KEY)
- `collection_run_id` (INTEGER)
- `timestamp` (TEXT)
- `endpoint` (TEXT)
- `attempt` (INTEGER)
- `delay` (INTEGER)
- `reason` (TEXT)

### licenses
- `collection_run_id` (INTEGER)
- `sku_id` (TEXT)
- `sku_name` (TEXT)
- `total_licenses` (INTEGER)
- `assigned_licenses` (INTEGER)
- `available_licenses` (INTEGER)

### price_lookup
- `sku_id` (TEXT PRIMARY KEY)
- `sku_name` (TEXT)
- `monthly_cost` (REAL)

### user_licenses
- `collection_run_id` (INTEGER)
- `user_principal_name` (TEXT)
- `sku_id` (TEXT)

### user_activity
- `collection_run_id` (INTEGER)
- `user_principal_name` (TEXT PRIMARY KEY)
- `last_sign_in_date` (TEXT)

### adp_employees
- `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
- `import_timestamp` (TEXT)
- `legal_name` (TEXT)
- `preferred_first_name` (TEXT)
- `preferred_last_name` (TEXT)
- `position_id` (TEXT)
- `hire_date` (TEXT)
- `job_title` (TEXT)
- `position_start_date` (TEXT)
- `position_status` (TEXT: 'Active', 'Terminated', etc.)
- `location` (TEXT)
- `work_email` (TEXT NOT NULL)

## Dependencies

| Library | Purpose |
|---------|---------|
| `msal` | Microsoft Authentication Library (Graph API auth) |
| `requests` | HTTP client for Graph API calls |
| `python-dotenv` | Load environment variables from .env |
| `openpyxl` | Read ADP Excel exports |
| `pdfplumber` | Extract text from invoice PDFs |
| `sqlite3` | Database (built-in to Python) |

## Common Tasks

### Monthly License Audit
```bash
# Collect latest data
uv run python tools/collect_m365_data.py

# Generate report
uv run python tools/generate_dashboard.py

# Review unassigned licenses in Utilization tab
open m365_dashboard.html
```

### Quarterly Cost Review
```bash
# Generate dashboard
uv run python tools/generate_dashboard.py

# Open Actions tab for executive summary
open m365_dashboard.html

# Download inactive user CSV for HR review
# (Click download button in Inactive Users tab)
```

### Custom Inactivity Threshold
```bash
# Check 60-day inactive instead of 90
export INACTIVE_DAYS=60
uv run python tools/generate_dashboard.py
```

## Testing

TODO: Test suite to be implemented following TDD practices.

```bash
uv run python -m pytest tests/ -v
```

## Documentation

- **[SKILL.md](SKILL.md)** - Quick reference and usage
- **[examples.md](examples.md)** - Practical workflows
- **[reference.md](reference.md)** - Graph API details and troubleshooting

## Troubleshooting

### Authentication Errors

**Error**: `AADSTS700016: Application not found`
- Verify `CLIENT_ID` matches your Azure AD app
- Check app exists in correct tenant

**Error**: `AADSTS7000215: Invalid client secret`
- Client secret may have expired
- Generate new secret in Azure Portal
- Update `.env` file

### Permission Errors

**Error**: `Insufficient privileges to complete the operation`
- Ensure API permissions are granted
- Click "Grant admin consent" in Azure Portal
- Wait 5-10 minutes for permissions to propagate

### Data Collection Issues

**No data collected**:
- Check Graph API endpoints are accessible
- Verify tenant has active subscriptions
- Review logs for specific error messages

## Cost Savings Checklist

Before removing licenses:
- [ ] Cross-reference with HR termination records
- [ ] Check for extended leave (medical, parental, sabbatical)
- [ ] Exclude service accounts and automation users
- [ ] Obtain IT leadership approval
- [ ] Document all removals for audit trail

## License

Part of Michelle's dotfiles. See [LICENSE](../../../../LICENSE) if applicable.
